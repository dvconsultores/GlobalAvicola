#!/usr/bin/env bash
# =============================================================================
# GA-REM-013 — Verificación de calidad reproducible
#
#   Ejecuta localmente las MISMAS comprobaciones que el CI, para que la
#   disciplina no dependa de un pipeline.
#
#   LIMITACIÓN ACEPTADA (EX-01):
#   Este comando NO impide el despliegue. El despliegue automático se mantiene
#   por decisión del propietario. La señal es informativa, no bloqueante.
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT="$(cd .. && pwd)"

# Resolución de node: algunos entornos usan nvm y node no está en el PATH base.
if ! command -v node >/dev/null 2>&1; then
  for d in "$HOME"/.nvm/versions/node/*/bin; do
    [ -x "$d/node" ] && export PATH="$d:$PATH" && break
  done
fi

FAIL=0
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
bad()  { printf "  \033[31m✗\033[0m %s\n" "$1"; FAIL=1; }
step() { printf "\n\033[1m── %s\033[0m\n" "$1"; }

step "1/8 · Backend · compilación"
.venv/bin/python -m compileall -q app seeds tests >/dev/null 2>&1 \
  && ok "compileall backend" || bad "compileall backend"

step "2/8 · Backend · integridad de la cadena Alembic"
.venv/bin/python - <<'PY' && ok "Alembic: 1 head, 1 base" || bad "Alembic: cadena rota"
import sys
from alembic.config import Config
from alembic.script import ScriptDirectory
sd = ScriptDirectory.from_config(Config("alembic.ini"))
heads, bases = sd.get_heads(), sd.get_bases()
n = len(list(sd.walk_revisions()))
print(f"     heads={heads} bases={bases} revisiones={n}")
sys.exit(0 if len(heads) == 1 and len(bases) == 1 else 1)
PY

step "3/8 · Backend · deriva entre modelos ORM y migraciones"
.venv/bin/python - <<'PY' && ok "0 deriva de esquema" || bad "deriva de esquema detectada"
import ast, glob, sys
from app.database import Base
import app.auth.models, app.masters.models, app.operations.models, app.lots.models
import app.review.models, app.corrections.models, app.audit.models, app.integrations.sap.models
model = {t.name: {c.name for c in t.columns} for t in Base.metadata.sorted_tables}
mig = {}
for f in sorted(glob.glob("alembic/versions/*.py")):
    tree = ast.parse(open(f).read())
    for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "upgrade"]:
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                a = node.func.attr
                if a == "create_table" and node.args:
                    t = getattr(node.args[0], "value", None)
                    if isinstance(t, str):
                        cols = {getattr(x.args[0], "value", None) for x in node.args[1:]
                                if isinstance(x, ast.Call) and getattr(x.func, "attr", None) == "Column" and x.args}
                        mig.setdefault(t, set()).update(c for c in cols if isinstance(c, str))
                elif a == "add_column" and len(node.args) >= 2:
                    t = getattr(node.args[0], "value", None); c = node.args[1]
                    if isinstance(t, str) and isinstance(c, ast.Call) and c.args:
                        cn = getattr(c.args[0], "value", None)
                        if isinstance(cn, str): mig.setdefault(t, set()).add(cn)
                elif a == "drop_column" and len(node.args) >= 2:
                    t = getattr(node.args[0], "value", None); cn = getattr(node.args[1], "value", None)
                    if isinstance(t, str) and isinstance(cn, str): mig.get(t, set()).discard(cn)
                elif a == "drop_table" and node.args:
                    t = getattr(node.args[0], "value", None)
                    if isinstance(t, str): mig.pop(t, None)
drift = (set(model) ^ set(mig)) or {t for t in set(model) & set(mig) if model[t] ^ mig[t]}

# Deriva de tipos enumerados. La comprobacion de tablas y columnas no la veia: el valor
# EGG_RECEPTION_CLASSIFICATION llevaba desde junio en el enum de Python y ausente del
# tipo eventtype de PostgreSQL, y cualquier intento de usarlo daba 500 (R-40).
import re
enum_py = {}
for _t in Base.metadata.sorted_tables:
    for _c in _t.columns:
        _cls = getattr(_c.type, "enum_class", None)
        if _cls is not None:
            enum_py[getattr(_c.type, "name", None) or _cls.__name__.lower()] = {m.name for m in _cls}
enum_mig = {}
for f in sorted(glob.glob("alembic/versions/*.py")):
    texto = open(f).read()
    for m_ in re.finditer(r"sa\.Enum\((.*?)name=[\'\"](\w+)[\'\"]", texto, re.S):
        vals = set(re.findall(r"[\'\"]([A-Z_][A-Z0-9_]*)[\'\"]", m_.group(1)))
        if vals:
            enum_mig.setdefault(m_.group(2), set()).update(vals)
    for m_ in re.finditer(r"ALTER TYPE (\w+) ADD VALUE(?: IF NOT EXISTS)? \'([^\']+)\'", texto):
        enum_mig.setdefault(m_.group(1), set()).add(m_.group(2))
enum_drift = {n: sorted(enum_py[n] - enum_mig.get(n, set()))
              for n in enum_py if enum_py[n] - enum_mig.get(n, set())}
print(f"     tablas modelo={len(model)} migraciones={len(mig)} deriva={len(drift)}")
print(f"     enums={len(enum_py)} con valores sin migracion={len(enum_drift)}"
      + (f" -> {enum_drift}" if enum_drift else ""))
sys.exit(0 if not drift and not enum_drift else 1)
PY

step "4/8 · Backend · guarda del entorno de pruebas"
GA_TEST_ENV=1 ENVIRONMENT=test \
GA_TEST_DATABASE_URL="postgresql+asyncpg://u:p@127.0.0.1:5432/test_verify" \
  .venv/bin/python -m pytest tests/test_environment_guard.py -q >/dev/null 2>&1 \
  && ok "guarda fail-closed (25 tests)" || bad "guarda fail-closed"

step "5/8 · Backend · ausencia de credenciales literales en seeds"
if grep -rqE '"password":\s*"[^"]' seeds/*.py 2>/dev/null; then
  bad "hay contraseñas literales en seeds/"
else
  ok "sin contraseñas literales en seeds/ (GA-REM-004)"
fi

step "6/8 · Frontend · typecheck"
( cd "$ROOT/frontend" && ./node_modules/.bin/tsc -b --noEmit >/dev/null 2>&1 ) \
  && ok "tsc" || bad "tsc"

step "7/8 · Frontend · tests unitarios"
( cd "$ROOT/frontend" && ./node_modules/.bin/vitest run >/dev/null 2>&1 ) \
  && ok "vitest" || bad "vitest"

step "8/8 · Frontend · paridad i18n"
( cd "$ROOT/frontend" && node -e '
const fs=require("fs");
const flat=(o,p="")=>Object.entries(o).reduce((r,[k,v])=>{const key=p?p+"."+k:k;
  return v&&typeof v==="object"&&!Array.isArray(v)?{...r,...flat(v,key)}:{...r,[key]:v}},{});
const es=flat(JSON.parse(fs.readFileSync("public/locales/es/translation.json","utf8")));
const en=flat(JSON.parse(fs.readFileSync("public/locales/en/translation.json","utf8")));
const a=Object.keys(es).filter(k=>!(k in en)), b=Object.keys(en).filter(k=>!(k in es));
console.log(`     ES=${Object.keys(es).length} EN=${Object.keys(en).length} faltantes=${a.length+b.length}`);
process.exit(a.length+b.length===0?0:1)' ) && ok "paridad i18n" || bad "paridad i18n"

printf "\n══════════════════════════════════════════════════════════════\n"
if [ $FAIL -eq 0 ]; then
  printf "  \033[32mVERIFICACIÓN COMPLETA: TODO EN VERDE\033[0m\n"
else
  printf "  \033[31mVERIFICACIÓN COMPLETA: HAY FALLOS\033[0m\n"
fi
printf "══════════════════════════════════════════════════════════════\n"
printf "  KNOWN_ACCEPTED_LIMITATION (EX-01):\n"
printf "  Este resultado NO impide el despliegue automático.\n"
printf "  Decisión del propietario. Fuera del alcance del programa.\n"
printf "══════════════════════════════════════════════════════════════\n"
exit $FAIL

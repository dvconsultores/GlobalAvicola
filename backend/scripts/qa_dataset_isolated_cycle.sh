#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Ciclo de certificación AISLADA del dataset QA (SPEC 007).
#
# Ejercita el seed `QA-DEMO-V1` completo sobre una base de datos desechable, sin tocar
# el entorno de desarrollo ni SAP, y demuestra las cuatro propiedades exigidas:
# idempotente, removible, aislado y fail-closed.
#
# Secuencia: alembic head → baseline → inventory (vacío) → apply #1 → verify #1 →
#            apply #2 (idempotencia) → verify #2 → cleanup sin --confirm-target
#            (debe ABORTAR) → cleanup --dry-run → cleanup real → baseline intacto
#            → apply #3 (recreación) → verify #3 → entorno prohibido (debe ABORTAR).
#
# Uso (desde backend/):
#   bash scripts/qa_dataset_isolated_cycle.sh \
#     > ../audit/qa-integral-dataset/evidence/06_isolated_cycle.log 2>&1
#
# Los directorios de subidas y de exportaciones SAP van a un `mktemp -d` que se borra
# al salir: el ciclo no deja rastro fuera de su propia bitácora.
# ─────────────────────────────────────────────────────────────────────────────
set -u
BACKEND="$(cd "$(dirname "$0")/.." && pwd)"; cd "$BACKEND"
E="$(cd "$(dirname "$0")/../.." && pwd)/audit/qa-integral-dataset/evidence"
F() { grep -v "^INFO  \[alembic\|bcrypt\|passlib\|__about__\|^Traceback (most\|^    version = \|^    \^\|AttributeError: module 'bcrypt'" ; }
URL="$(.venv/bin/python -m scripts.test_db start)"; URL="$(.venv/bin/python -m scripts.test_db reset)"
export GA_TEST_ENV=1 ENVIRONMENT=test DEBUG=false DATABASE_URL="$URL"
export JWT_SECRET_KEY="$(.venv/bin/python -c 'import secrets;print(secrets.token_hex(32))')"
MEDIA="$(mktemp -d -t ga-qa-media-XXXXXX)"; export MEDIA_DIR="$MEDIA" SAP_EXPORT_DIR="$MEDIA/sap_exports"; mkdir -p "$SAP_EXPORT_DIR"; trap 'rm -rf "$MEDIA"' EXIT
export GA_QA_SEED_PASSWORD="$(.venv/bin/python -c 'import secrets;print(secrets.token_urlsafe(14))')"
export GA_BASELINE_ADMIN_PASSWORD="$(.venv/bin/python -c 'import secrets;print(secrets.token_urlsafe(14))')"
RUN_ID="QA-DEMO-V1-ISOLATED-$(date +%Y%m%d)"
echo "== $(date -u +%FT%TZ) alembic upgrade head =="; .venv/bin/python -m alembic upgrade head 2>&1 | tail -1
echo "== baseline =="; .venv/bin/python - <<'PY' 2>&1 | F | tail -3
import asyncio
from app.database import async_session
from seeds.baseline_seeds import sembrar_baseline
async def m():
    async with async_session() as s: print("BASELINE", await sembrar_baseline(s))
asyncio.run(m())
PY
echo "== 1 inventory (vacío) =="; .venv/bin/python -m seeds.qa_integral_dataset --inventory 2>&1 | F
echo "== 2 apply #1 $(date -u +%FT%TZ) =="; T0=$SECONDS; .venv/bin/python -m seeds.qa_integral_dataset --apply --confirm-target global_avicola_test --run-id "$RUN_ID" --fixtures-dir $E/../fixtures --manifest $E/manifest_isolated.json 2>&1 | F; echo "APPLY1_SECONDS=$((SECONDS-T0))"
echo "== 3 verify #1 =="; .venv/bin/python -m seeds.qa_integral_dataset --verify 2>&1 | F
echo "== 4 apply #2 (idempotencia) =="; .venv/bin/python -m seeds.qa_integral_dataset --apply --confirm-target global_avicola_test --run-id "$RUN_ID" 2>&1 | F | grep -v "created=0 "
echo "== 5 verify #2 =="; .venv/bin/python -m seeds.qa_integral_dataset --verify 2>&1 | F | tail -1
echo "== 6 cleanup sin confirm-target (debe abortar) =="; .venv/bin/python -m seeds.qa_integral_dataset --cleanup 2>&1 | F
echo "== 7 cleanup --dry-run =="; .venv/bin/python -m seeds.qa_integral_dataset --cleanup --dry-run 2>&1 | F
echo "== 8 inventory tras dry-run (sin cambios) =="; .venv/bin/python -m seeds.qa_integral_dataset --inventory 2>&1 | F
echo "== 9 cleanup real =="; .venv/bin/python -m seeds.qa_integral_dataset --cleanup --confirm-target global_avicola_test 2>&1 | F
echo "== 10 inventory tras cleanup =="; .venv/bin/python -m seeds.qa_integral_dataset --inventory 2>&1 | F
echo "== 11 baseline intacto =="; .venv/bin/python - <<'PY' 2>&1 | F
import asyncio
from sqlalchemy import text
from app.database import async_session
async def m():
    async with async_session() as s:
        for q in ["select count(*) from users where username like 'qa.%'","select count(*) from lots where lot_code like 'QA-%'","select count(*) from companies where tax_id like 'QA-DEMO-V1%'","select count(*) from sap_references where sap_code like 'QA%'","select count(*) from operational_events","select count(*) from companies","select count(*) from roles","select count(*) from users where username='admin'","select count(*) from productive_phases","select count(*) from business_units","select count(*) from permissions"]:
            print(f"{q:<70} -> {(await s.execute(text(q))).scalar()}")
asyncio.run(m())
PY
echo "== 12 apply #3 (recreación) =="; .venv/bin/python -m seeds.qa_integral_dataset --apply --confirm-target global_avicola_test --run-id "$RUN_ID" 2>&1 | F | grep "CREATED\|EXISTING\|UPDATED\|SKIPPED\|fase"
echo "== 13 verify #3 =="; .venv/bin/python -m seeds.qa_integral_dataset --verify 2>&1 | F
echo "== 14 entorno prohibido (ENVIRONMENT=production) =="; ENVIRONMENT=production .venv/bin/python -m seeds.qa_integral_dataset --inventory 2>&1 | F
echo "== $(date -u +%FT%TZ) FIN =="

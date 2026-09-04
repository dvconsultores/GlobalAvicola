#!/usr/bin/env bash
# ============================================================
# WAVE 2.75 — CERTIFICACION DEL ARRANQUE REAL (GA-REM-024)
#
#   MIGRATION EXISTS  !=  MIGRATION DEPLOYED
#   CODE PASS         !=  RUNTIME STARTUP PASS
#
# Este script NO ejecuta `alembic` por su cuenta. Invoca el **entrypoint real de la
# imagen** —`backend/docker-entrypoint.sh`, el mismo fichero que el Dockerfile copia— y
# comprueba lo que hace: si migra antes de ceder el control, si se detiene cuando la
# migracion falla, y si arrancar dos veces deja el mismo estado.
#
# Limitacion declarada: esta maquina no tiene Docker, de modo que se ejercita el
# entrypoint y no la capa de imagen (COPY, wiring de ENTRYPOINT, permisos de USER). Lo que
# se certifica es el comportamiento del script; lo que queda pendiente de un entorno con
# Docker esta anotado en el informe de la Wave.
#
# Escenarios:
#   1  fresh          base vacia            -> el arranque debe crear el esquema
#   2  upgrade        estado pre-Wave-2     -> el arranque debe migrar y reconciliar
#   3  restart        base ya en head       -> el arranque debe ser idempotente
#   4  failure        migracion imposible   -> el arranque NO debe ceder el control
# ============================================================
set -uo pipefail
cd "$(dirname "$0")/.."
PY=".venv/bin/python"
ENTRYPOINT="./docker-entrypoint.sh"
HEAD_PREVIO="i9j0k1l2m3n4"

#: Marca que deja el "servidor" simulado. Su existencia demuestra que el entrypoint cedio
#: el control; su ausencia, que se detuvo antes.
MARCA="$(mktemp -u -t ga-arranque-XXXXXX)"

verde() { printf '  \033[32m✓\033[0m %s\n' "$1"; }
rojo()  { printf '  \033[31m✗\033[0m %s\n' "$1"; FALLOS=$((FALLOS+1)); }
FALLOS=0

# El "servidor": no levanta uvicorn —no hace falta para demostrar el orden— sino que deja
# constancia de haber sido alcanzado. Es exactamente lo que hay que medir.
cat > /tmp/ga-fake-server.sh <<'SRV'
#!/bin/sh
echo "[servidor] arrancado con: $*"
touch "$GA_MARCA_ARRANQUE"
SRV
chmod +x /tmp/ga-fake-server.sh

preparar_entorno() {
  local db="$1"
  export GA_TEST_ENV=1 ENVIRONMENT=test DEBUG=false
  export GA_TEST_DATABASE_URL="$db"
  export DATABASE_URL="$db"
  export JWT_SECRET_KEY="${JWT_SECRET_KEY:-$($PY -c 'import secrets;print(secrets.token_hex(32))')}"
  export GA_UPGRADE_TEST_PASSWORD="${GA_UPGRADE_TEST_PASSWORD:-$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')}"
  export GA_MARCA_ARRANQUE="$MARCA"
  export PATH="$PWD/.venv/bin:$PATH"
}

revision_actual() {
  $PY - <<'PYEOF2' 2>/dev/null
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
async def main():
    e = create_async_engine(os.environ["DATABASE_URL"])
    try:
        async with e.connect() as c:
            print((await c.execute(text("SELECT version_num FROM alembic_version"))).scalar() or "—")
    except Exception:
        print("sin-esquema")
    await e.dispose()
asyncio.run(main())
PYEOF2
}

ejecutar_arranque() {
  rm -f "$MARCA"
  set +e
  $ENTRYPOINT /tmp/ga-fake-server.sh uvicorn app.main:app > /tmp/ga-arranque.log 2>&1
  CODIGO=$?
  set -e
  return $CODIGO
}

echo "══════════════════════════════════════════════════════════════"
echo "  WAVE 2.75 — ARRANQUE REAL · entrypoint de la imagen"
echo "══════════════════════════════════════════════════════════════"
$PY scripts/test_db.py start >/dev/null

# ── 1 · Instalacion nueva ────────────────────────────────────────────────────
echo
echo "── 1/4 · FRESH INSTALL · base vacia ──"
DSN_FRESH="$($PY scripts/test_db.py reset)"
preparar_entorno "$DSN_FRESH"
echo "   revision antes: $(revision_actual)"
if ejecutar_arranque; then
  DESPUES="$(revision_actual)"
  echo "   revision despues: $DESPUES"
  [ -f "$MARCA" ] && verde "el entrypoint cedio el control al servidor" || rojo "el servidor no arranco"
  [ "$DESPUES" != "sin-esquema" ] && verde "esquema creado por el arranque, no a mano" || rojo "no se creo el esquema"
  grep -q "Starting database migrations" /tmp/ga-arranque.log && verde "registra el inicio de la migracion" || rojo "sin registro de migracion"
  grep -q "Migration completed" /tmp/ga-arranque.log && verde "registra la migracion completada" || rojo "sin registro de finalizacion"
else
  rojo "el arranque fallo (codigo $CODIGO)"; sed 's/^/     /' /tmp/ga-arranque.log | tail -5
fi

# ── 2 · Actualizacion de instalacion existente ───────────────────────────────
echo
echo "── 2/4 · EXISTING UPGRADE · estado anterior a la Wave 2 ──"
DSN_UP="$($PY scripts/test_db.py reset upgrade)"
preparar_entorno "$DSN_UP"
$PY -m alembic upgrade "$HEAD_PREVIO" >/dev/null 2>&1
$PY -m seeds.legacy_state_seeds >/dev/null 2>&1
ANTES="$(revision_actual)"
PERM_ANTES="$($PY -c "
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
async def m():
    e = create_async_engine(os.environ['DATABASE_URL'])
    async with e.connect() as c:
        print((await c.execute(text('SELECT count(*) FROM permissions'))).scalar())
    await e.dispose()
asyncio.run(m())")"
echo "   antes: revision=$ANTES permisos=$PERM_ANTES"
echo "   (no se ejecuta alembic a mano: debe hacerlo el arranque)"
if ejecutar_arranque; then
  DESPUES="$(revision_actual)"
  PERM_DESPUES="$($PY -c "
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
async def m():
    e = create_async_engine(os.environ['DATABASE_URL'])
    async with e.connect() as c:
        print((await c.execute(text('SELECT count(*) FROM permissions'))).scalar())
    await e.dispose()
asyncio.run(m())")"
  echo "   despues: revision=$DESPUES permisos=$PERM_DESPUES"
  [ "$ANTES" != "$DESPUES" ] && verde "el arranque migro la base ($ANTES -> $DESPUES)" || rojo "la revision no avanzo"
  [ "$PERM_DESPUES" -gt "$PERM_ANTES" ] && verde "el arranque reconcilio permisos ($PERM_ANTES -> $PERM_DESPUES)" || rojo "no hubo reconciliacion"
  [ -f "$MARCA" ] && verde "el servidor arranco despues de migrar" || rojo "el servidor no arranco"
else
  rojo "el arranque fallo (codigo $CODIGO)"; sed 's/^/     /' /tmp/ga-arranque.log | tail -5
fi

# ── 3 · Reinicio con la base ya al dia ───────────────────────────────────────
echo
echo "── 3/4 · RESTART AT HEAD · idempotencia (escenario Watchtower) ──"
PERM_1="$($PY -c "
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
async def m():
    e = create_async_engine(os.environ['DATABASE_URL'])
    async with e.connect() as c:
        print((await c.execute(text('SELECT count(*) FROM permissions'))).scalar())
    await e.dispose()
asyncio.run(m())")"
if ejecutar_arranque; then
  PERM_2="$($PY -c "
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
async def m():
    e = create_async_engine(os.environ['DATABASE_URL'])
    async with e.connect() as c:
        dup = (await c.execute(text('SELECT count(*) FROM (SELECT role_id, module, action FROM permissions GROUP BY 1,2,3 HAVING count(*)>1) d'))).scalar()
        n = (await c.execute(text('SELECT count(*) FROM permissions'))).scalar()
        print(f'{n} {dup}')
    await e.dispose()
asyncio.run(m())")"
  N2="${PERM_2% *}"; DUP="${PERM_2#* }"
  [ "$PERM_1" = "$N2" ] && verde "segundo arranque: mismo numero de permisos ($N2)" || rojo "el recuento cambio: $PERM_1 -> $N2"
  [ "$DUP" = "0" ] && verde "sin asociaciones duplicadas" || rojo "$DUP asociaciones duplicadas"
  [ -f "$MARCA" ] && verde "el servidor arranco de nuevo" || rojo "el servidor no arranco"
else
  rojo "el reinicio fallo (codigo $CODIGO)"
fi

# ── 4 · Fallo de migracion ───────────────────────────────────────────────────
echo
echo "── 4/4 · MIGRATION FAILURE · fail-closed ──"
preparar_entorno "postgresql+asyncpg://nadie:nada@/base_que_no_existe_test?host=/tmp"
if ejecutar_arranque; then
  rojo "GRAVE: el arranque continuo pese a fallar la migracion"
else
  verde "el arranque termino con codigo $CODIGO"
  [ ! -f "$MARCA" ] && verde "el servidor NO arranco: fail-closed correcto" || rojo "GRAVE: el servidor arranco con la migracion fallida"
  grep -q "Starting application" /tmp/ga-arranque.log && rojo "se alcanzo el mensaje de arranque de la aplicacion" || verde "no se alcanzo el punto de cesion del control"
fi

# ── 5 · Sin filtracion de secretos ───────────────────────────────────────────
echo
echo "── Registro del arranque ──"
preparar_entorno "$DSN_UP"
ejecutar_arranque >/dev/null 2>&1 || true
if grep -qE "password|@/.*:.*@|$(echo "${JWT_SECRET_KEY:-nada}" | cut -c1-16)" /tmp/ga-arranque.log; then
  rojo "el registro contiene material sensible"
else
  verde "el registro no filtra credenciales"
fi
sed 's/^/     /' /tmp/ga-arranque.log | head -5

rm -f "$MARCA" /tmp/ga-fake-server.sh
echo
echo "══════════════════════════════════════════════════════════════"
if [ "$FALLOS" -eq 0 ]; then
  echo "  ARRANQUE CERTIFICADO — 0 fallos"
else
  echo "  ARRANQUE CON $FALLOS FALLOS"
fi
echo "══════════════════════════════════════════════════════════════"
exit "$FALLOS"

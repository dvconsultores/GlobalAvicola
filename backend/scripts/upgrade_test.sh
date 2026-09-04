#!/usr/bin/env bash
# ============================================================
# PATH B — CERTIFICACION DEL CAMINO DE ACTUALIZACION (Wave 2.5)
#
# Una base recien creada no demuestra que produccion pueda actualizarse. Este script
# reconstruye el estado de una instalacion EXISTENTE anterior a la Wave 2 y le aplica el
# camino completo de actualizacion:
#
#   base vacia
#     -> alembic upgrade i9j0k1l2m3n4      (head anterior a la Wave 2)
#     -> estado heredado: permisos historicos, usuarios, datos, enums con deriva
#     -> alembic upgrade head              (R-40, R-41, R-44)
#     -> verificacion
#
# Opera sobre `global_avicola_upgrade_test`, distinta de la base de instalacion nueva.
# Produccion no se toca: la guarda de entorno lo impide.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/.."
PY=".venv/bin/python"

#: Ultimo head anterior a la Wave 2. Una instalacion desplegada antes de esa Wave esta aqui.
HEAD_PREVIO="i9j0k1l2m3n4"

echo "── 1/6 · Instancia de pruebas ──"
$PY scripts/test_db.py start >/dev/null
DSN="$($PY scripts/test_db.py reset upgrade)"
echo "   base de actualizacion recreada"

export GA_TEST_ENV=1
export ENVIRONMENT=test
export DEBUG=false
export GA_TEST_DATABASE_URL="$DSN"
export DATABASE_URL="$DSN"
export JWT_SECRET_KEY="$($PY -c 'import secrets;print(secrets.token_hex(32))')"
export GA_UPGRADE_TEST_PASSWORD="$($PY -c 'import secrets;print(secrets.token_urlsafe(18))')"
GA_TEST_MEDIA_DIR="$(mktemp -d -t ga-upgrade-media-XXXXXX)"
export MEDIA_DIR="$GA_TEST_MEDIA_DIR"
export SAP_EXPORT_DIR="$GA_TEST_MEDIA_DIR/sap_exports"
mkdir -p "$SAP_EXPORT_DIR"
trap 'rm -rf "$GA_TEST_MEDIA_DIR"' EXIT

echo "── 2/6 · Esquema anterior a la Wave 2 ($HEAD_PREVIO) ──"
$PY -m alembic upgrade "$HEAD_PREVIO" >/dev/null 2>&1
echo "   migrado hasta $HEAD_PREVIO"

echo "── 3/6 · Estado heredado (permisos historicos, usuarios, datos, enums con deriva) ──"
$PY -m seeds.legacy_state_seeds

echo "── 4/6 · Estado ANTES de actualizar ──"
$PY - <<'PYEOF2'
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    e = create_async_engine(os.environ["DATABASE_URL"])
    async with e.connect() as c:
        n = (await c.execute(text("SELECT count(*) FROM permissions"))).scalar()
        head = (await c.execute(text("SELECT version_num FROM alembic_version"))).scalar()
        ev = (await c.execute(text(
            "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid=e.enumtypid "
            "WHERE t.typname='eventtype'"))).scalar()
    await e.dispose()
    print(f"   head={head} · permisos={n} · valores de eventtype={ev}")
asyncio.run(main())
PYEOF2

echo "── 5/6 · ACTUALIZACION: alembic upgrade head ──"
$PY -m alembic upgrade head 2>&1 | grep -E "Running upgrade|R-44" | sed 's/^/   /'

echo "── 6/6 · Estado DESPUES de actualizar ──"
$PY - <<'PYEOF3'
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    e = create_async_engine(os.environ["DATABASE_URL"])
    async with e.connect() as c:
        n = (await c.execute(text("SELECT count(*) FROM permissions"))).scalar()
        head = (await c.execute(text("SELECT version_num FROM alembic_version"))).scalar()
        ev = (await c.execute(text(
            "SELECT count(*) FROM pg_enum e JOIN pg_type t ON t.oid=e.enumtypid "
            "WHERE t.typname='eventtype'"))).scalar()
        bt = sorted((await c.execute(text(
            "SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON t.oid=e.enumtypid "
            "WHERE t.typname='birdtypeenum'"))).scalars().all())
        usuarios = (await c.execute(text("SELECT count(*) FROM users"))).scalar()
    await e.dispose()
    print(f"   head={head} · permisos={n} · valores de eventtype={ev}")
    print(f"   birdtypeenum={bt}")
    print(f"   usuarios conservados={usuarios}")
asyncio.run(main())
PYEOF3

echo
echo "── Pruebas de actualizacion ──"
$PY -m pytest "${@:-tests/test_upgrade_path.py}" -q

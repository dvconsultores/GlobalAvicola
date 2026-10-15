#!/usr/bin/env bash
# SPEC 006 · verificación de la migración e0f1a2b3c4d5 sobre la base de pruebas aislada (pgserver).
# upgrade fresh → recuentos → downgrade -1 → recuentos → upgrade sobre esquema existente → ORM vs BD.
# El DSN efímero no se imprime (solo se exporta al entorno de los subprocesos).
set -uo pipefail
cd "$(dirname "$0")/../../../../backend"
PY=.venv/bin/python
export GA_TEST_ENV=1 ENVIRONMENT=test
export GA_TEST_DATABASE_URL="$($PY -m scripts.test_db start >/dev/null; $PY -m scripts.test_db reset)"
export DATABASE_URL="$GA_TEST_DATABASE_URL"
echo "INICIO $(date '+%F %T') · verificación de migración e0f1a2b3c4d5 sobre la base de pruebas (pgserver, espacio de usuario)"
echo "head en código: $($PY -m alembic heads 2>/dev/null | tail -1)"

inspeccion() {
$PY - <<'EOF'
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
async def main():
    eng = create_async_engine(os.environ["DATABASE_URL"])
    async with eng.connect() as c:
        n = (await c.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'"))).scalar()
        head = (await c.execute(text("SELECT version_num FROM alembic_version"))).scalar()
        ho = (await c.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_name='hatchery_openings'"))).scalar()
        cols = set((await c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='opening_balances'"))).scalars().all())
        idx = (await c.execute(text("SELECT indexname FROM pg_indexes WHERE tablename='hatchery_openings' ORDER BY 1"))).scalars().all()
        enums = (await c.execute(text("SELECT count(*) FROM pg_type WHERE typtype='e' AND typname LIKE '%hatchery%'"))).scalar()
    await eng.dispose()
    nuevas = {"initial_mixed_count","accumulated_mortality_mixed","accumulated_culls_mixed","placed_male_count","placed_female_count",
              "placed_mixed_count","accumulated_outbound_birds","placed_status","weight_status","eggs_to_hatchery_status","outbound_status",
              "age_status","initial_mixed_status","template_version"}
    print(f"   head en BD: {head} · tablas: {n} · hatchery_openings presente: {bool(ho)} · columnas v2 en opening_balances: {len(nuevas & cols)}/{len(nuevas)}")
    print(f"   índices hatchery_openings: {', '.join(idx) if idx else '-'} · enums nuevos (esperado 0): {enums}")
asyncio.run(main())
EOF
}

echo "-- 1. upgrade head sobre base vacía (fresh) --"
$PY -m alembic upgrade head 2>&1 | grep -E "e0f1a2b3c4d5" | sed 's/^/   /'
inspeccion
echo "-- 2. downgrade -1 --"
$PY -m alembic downgrade -1 2>&1 | grep -E "e0f1a2b3c4d5" | sed 's/^/   /'
inspeccion
echo "-- 3. upgrade head sobre esquema existente --"
$PY -m alembic upgrade head 2>&1 | grep -E "e0f1a2b3c4d5" | sed 's/^/   /'
inspeccion
echo "-- 4. metadata ORM vs esquema --"
$PY - <<'EOF'
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.cutover.models import HatcheryOpening
from app.lots.models import OpeningBalance
async def main():
    eng = create_async_engine(os.environ["DATABASE_URL"])
    async with eng.connect() as c:
        for modelo in (HatcheryOpening, OpeningBalance):
            bd = set((await c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name=:t"), {"t": modelo.__tablename__})).scalars().all())
            orm = {col.name for col in modelo.__table__.columns}
            print(f"   {modelo.__tablename__}: columnas distintas ORM/BD = {sorted(orm ^ bd)}")
    await eng.dispose()
asyncio.run(main())
EOF
echo "FIN $(date '+%F %T')"

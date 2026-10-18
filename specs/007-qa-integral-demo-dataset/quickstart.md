# Quickstart — seed `QA-DEMO-V1`

Todo desde `backend/`, con el `.venv` del proyecto y el `DATABASE_URL` del entorno destino. Nunca en `production/prod/staging/pre/preprod`.

```bash
# 0 · ¿qué hay?
.venv/bin/python -m seeds.qa_integral_dataset --inventory

# 1 · aplicar (idempotente). La contraseña viene del entorno o se genera en un archivo 0600 fuera del repo.
GA_QA_SEED_PASSWORD='<temporal>' .venv/bin/python -m seeds.qa_integral_dataset --apply --confirm-target <nombre_bd> \
    --run-id QA-DEMO-V1-$(date +%Y%m%d) --manifest ../audit/qa-integral-dataset/QA_DATA_MANIFEST.json
#   sin GA_QA_SEED_PASSWORD ⇒ /tmp/global_avicola_qa_credentials.txt (0600); --credentials-file para otra ruta;
#   --reset-passwords vuelve a aplicar la contraseña a usuarios qa.* existentes.

# 2 · verificar (lista §49; termina con QA_DATA_VERIFY = PASS|FAIL)
.venv/bin/python -m seeds.qa_integral_dataset --verify

# 3 · volver a aplicar: debe reportar CREATED = 0
GA_QA_SEED_PASSWORD='<temporal>' .venv/bin/python -m seeds.qa_integral_dataset --apply --confirm-target <nombre_bd>

# 4 · limpieza (NO ejecutar en el runtime compartido sin decisión Owner)
.venv/bin/python -m seeds.qa_integral_dataset --cleanup --dry-run
.venv/bin/python -m seeds.qa_integral_dataset --cleanup --confirm-target <nombre_bd>
```

Prerrequisito: roles canónicos, fases y catálogo de BU presentes (`baseline_seeds.sembrar_baseline` en una base nueva; el runtime ya los tiene).

## Ensayo aislado (arnés)

```bash
URL="$(.venv/bin/python -m scripts.test_db start)"; URL="$(.venv/bin/python -m scripts.test_db reset)"
export GA_TEST_ENV=1 ENVIRONMENT=test DATABASE_URL="$URL" JWT_SECRET_KEY="$(openssl rand -hex 32)" MEDIA_DIR=/tmp/ga-media
.venv/bin/python -m alembic upgrade head
GA_BASELINE_ADMIN_PASSWORD='<tmp>' .venv/bin/python -c 'import asyncio; from app.database import async_session; from seeds.baseline_seeds import sembrar_baseline
async def m():
    async with async_session() as s: print(await sembrar_baseline(s))
asyncio.run(m())'
GA_QA_SEED_PASSWORD='<tmp>' .venv/bin/python -m seeds.qa_integral_dataset --apply --confirm-target global_avicola_test
.venv/bin/python -m seeds.qa_integral_dataset --verify
```

## Salidas

- Contadores `CREATED/EXISTING/UPDATED/SKIPPED` por entidad.
- `--manifest`: JSON con versión, marcador, run_id, SHA, inventario, contadores, lotes y referencias SAP.
- Fixtures XLSX de cutover por BU en `--fixtures-dir` (por defecto `audit/qa-integral-dataset/fixtures/`).

## Ciclo de certificación aislada

```bash
cd backend && bash scripts/qa_dataset_isolated_cycle.sh > ../audit/qa-integral-dataset/evidence/06_isolated_cycle.log 2>&1
```

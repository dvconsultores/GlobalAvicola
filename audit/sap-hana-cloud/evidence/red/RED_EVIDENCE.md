# SPEC 005 · RED evidence

Fecha: 2026-10-06 · Base: `cf991b4` (antes de implementar) · Comando: `backend/scripts/run_tests.sh` (PostgreSQL de pruebas en espacio de usuario) · 0 llamadas a SAP

## 1 · Suite de la spec — `red_suite_collection.log`

```text
./scripts/run_tests.sh tests/test_sap_hana_guard.py tests/test_sap_hana_client.py \
  tests/test_sap_hana_sync.py tests/test_sap_hana_promotion.py tests/test_sap_hana_routes.py -q
→ 5 errors during collection · exit=2
  ModuleNotFoundError: No module named 'app.integrations.sap.inbound'
```

Las 118 funciones de prueba (más sus casos parametrizados) no pueden ejecutarse: el paquete inbound no existe.

## 2 · Sonda conductual sobre HEAD — `red_behavioral_probe_head.log`

El error de importación solo prueba que falta el paquete. Esta sonda temporal (no versionada como prueba; su código va abajo) observa lo que el producto hace hoy por las superficies que **ya existen**:

| Caso | Esperado tras la spec | Observado en HEAD |
|---|---|---|
| `Settings` declara `SAP_HANA_*` y `SAP_OUTBOUND_ENABLED` | sí | `AssertionError: falta SAP_HANA_HOST` |
| `POST /sap/export` | 409 `SAP_OUTBOUND_DISABLED_READ_ONLY_PHASE` | **400** |
| `POST /sap/retry` | 409 | **200** (ejecuta el reintento) |
| `GET /sap/inbound/readiness` | 200 | **404** |
| `GET /sap/connection-check` distingue `inbound_hana` / `outbound` | sí | solo `adapter, connected, delivers_to_sap, mode` |

Resultado: `5 failed · exit=1`.

```python
from app.config import Settings


def test_red_settings_sin_variables_hana():
    for n in ("SAP_HANA_HOST", "SAP_HANA_ENCRYPT", "SAP_OUTBOUND_ENABLED", "SAP_HANA_SYNC_ENABLED"):
        assert n in Settings.model_fields, f"falta {n}"


async def test_red_export_no_esta_deshabilitado(client, auth_headers):
    r = await client.post("/api/v1/sap/export", headers=auth_headers, json={})
    assert r.status_code == 409, f"HEAD responde {r.status_code}"


async def test_red_retry_no_esta_deshabilitado(client, auth_headers):
    r = await client.post("/api/v1/sap/retry", headers=auth_headers, json={})
    assert r.status_code == 409, f"HEAD responde {r.status_code}"


async def test_red_readiness_no_existe(client, auth_headers):
    r = await client.get("/api/v1/sap/inbound/readiness", headers=auth_headers)
    assert r.status_code == 200, f"HEAD responde {r.status_code}"


async def test_red_connection_check_no_distingue_inbound(client, auth_headers):
    r = await client.get("/api/v1/sap/connection-check", headers=auth_headers)
    assert "inbound_hana" in r.json() and "outbound" in r.json(), sorted(r.json())
```

## 3 · Saneado

Los logs no contienen DSN, contraseñas ni secretos (el arnés genera credenciales efímeras por ejecución y no las imprime en estas corridas).

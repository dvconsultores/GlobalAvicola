"""GA-REQ-061 · T14 · C2 — ciclo crear→subir→validar (staging) (RED).

Rojo en HEAD (`cf03253`): no existen las rutas `/cutover-batches` (404). La
Implementación añade: creación de batch (DRAFT), upload Excel→staging (jamás a
tablas operacionales, AC43/44), parser `openpyxl` con `template_version`
validada (CUT-RED-19), errores estructurados con `error_code`/`received_value`
(AC46) y re-upload idempotente por checksum (AC50, sin duplicar filas).
"""
import io

import pytest


def _xlsx(filas: list[list], *, template_version: str = "v1", business_unit: str = "broiler") -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    meta = wb.active
    meta.title = "Meta"
    meta.append(["key", "value"])
    meta.append(["template_version", template_version])
    meta.append(["business_unit", business_unit])
    datos = wb.create_sheet("Datos")
    datos.append(["legacy_lot_code", "real_start_date", "live_males", "live_females",
                  "historical_mortality_males", "historical_mortality_females", "farm_code", "notes"])
    for f in filas:
        datos.append(f)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


FILAS = [
    ["CUT-BR-001", "2026-08-15", 5000, 5000, 300, 200, None, ""],
    ["CUT-BR-002", "2026-09-01", 2000, 2000, None, None, None, "mortalidad histórica desconocida"],
    ["CUT-BR-003", "2026-09-05", 1000, 1000, 50, 40, "F-999", ""],
]


async def _crear_batch(client, headers, cutover: str = "2026-10-01T00:00:00+00:00") -> int:
    r = await client.post("/api/v1/cutover-batches", headers=headers, json={
        "business_unit": "broiler",
        "cutover_datetime": cutover,
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _subir(files_ok: bytes):
    return {"file": ("corte.xlsx", files_ok,
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}


@pytest.mark.asyncio
async def test_c2_crear_batch_draft(auth_headers, client, seeded_ids):
    """POST /cutover-batches nace en DRAFT con actor y empresa efectiva."""
    r = await client.post("/api/v1/cutover-batches", headers=auth_headers, json={
        "business_unit": "broiler",
        "cutover_datetime": "2026-10-01T00:00:00+00:00",
    })
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert cuerpo["status"] == "draft"
    assert cuerpo["business_unit"] == "broiler"
    assert cuerpo["company_id"] == seeded_ids["company_id"]
    assert cuerpo["total_rows"] == 0


@pytest.mark.asyncio
async def test_c2_upload_validar_preview(auth_headers, http_client, seeded_ids):
    """Upload → staging + validación sin efectos: 3 leídas / 2 válidas / 1 con error estructurado."""
    batch_id = await _crear_batch(http_client, auth_headers)
    r = await http_client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                               headers=auth_headers, files=_subir(_xlsx(FILAS)))
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert (cuerpo["total_rows"], cuerpo["valid_rows"], cuerpo["invalid_rows"]) == (3, 2, 1), cuerpo
    assert cuerpo["status"] == "validating"

    # Preview (validación) con error estructurado: fila 4 (encabezado=1) · farm_code F-999 no existe.
    v = await http_client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=auth_headers)
    assert v.status_code == 200, v.text
    errores = v.json()["errors"]
    assert len(errores) == 1
    err = errores[0]
    assert err["row_number"] == 4
    assert err["error_code"] == "MASTER_NOT_FOUND"
    assert err["field"] == "farm_code"
    assert err["received_value"] == "F-999"

    # Nada fué aplicado: sin lotes creados, sin errores de staging duplicado.
    listado = await http_client.get(
        f"/api/v1/cutover-batches/{batch_id}/items", headers=auth_headers)
    assert listado.status_code == 200, listado.text
    items = listado.json()["items"]
    assert len(items) == 3
    assert {it["validation_status"] for it in items} == {"valid", "invalid"}


@pytest.mark.asyncio
async def test_c2_template_version_no_soportada(auth_headers, http_client):
    """CUT-RED-19: versión de plantilla no soportada ⇒ error determinista, 0 aplicados."""
    batch_id = await _crear_batch(http_client, auth_headers)
    r = await http_client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                               headers=auth_headers, files=_subir(_xlsx(FILAS, template_version="v99")))
    assert r.status_code in (400, 422), r.text
    assert "TEMPLATE_VERSION_UNSUPPORTED" in r.text
    # El batch sigue sin filas de staging y en DRAFT.
    v = await http_client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=auth_headers)
    assert v.json()["total_rows"] == 0


@pytest.mark.asyncio
async def test_c2_mismo_checksum_no_duplica(auth_headers, http_client):
    """AC50/CUT-RED-08 (misma carga): re-subir el MISMO archivo no duplica filas."""
    batch_id = await _crear_batch(http_client, auth_headers)
    contenido = _xlsx(FILAS)
    r1 = await http_client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                                headers=auth_headers, files=_subir(contenido))
    assert r1.status_code == 200, r1.text
    r2 = await http_client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                                headers=auth_headers, files=_subir(contenido))
    assert r2.status_code == 200, r2.text
    assert r2.json()["total_rows"] == 3  # no 6
    listado = await http_client.get(f"/api/v1/cutover-batches/{batch_id}/items", headers=auth_headers)
    assert len(listado.json()["items"]) == 3


@pytest.mark.asyncio
async def test_c2_plantilla_descargable_y_cargable(auth_headers, http_client):
    """`GET /cutover-templates/{bu}`: plantilla versionada descargable; el propio archivo re-cargado vale."""
    from openpyxl import load_workbook

    for bu in ("grandparent", "breeder", "hatchery", "broiler"):
        r = await http_client.get(f"/api/v1/cutover-templates/{bu}", headers=auth_headers)
        assert r.status_code == 200, r.text
        assert "spreadsheetml" in r.headers["content-type"]
        wb = load_workbook(io.BytesIO(r.content))
        assert {"Instrucciones", "Meta", "Datos"} <= set(wb.sheetnames)
        meta = {fila[0].value: fila[1].value for fila in wb["Meta"].iter_rows(min_row=2)}
        assert meta["template_version"] == "v1"
        assert meta["business_unit"] == bu

    # La plantilla broiler descargada se puede subir tal cual (0 filas, sin efectos).
    r = await http_client.get("/api/v1/cutover-templates/broiler", headers=auth_headers)
    batch_id = await _crear_batch(http_client, auth_headers)
    subida = await http_client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                                    headers=auth_headers, files={"file": ("plantilla.xlsx", r.content,
                                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert subida.status_code == 200, subida.text
    assert subida.json()["total_rows"] == 0

    # Unidad inexistente ⇒ 422 determinista.
    r = await http_client.get("/api/v1/cutover-templates/aves", headers=auth_headers)
    assert r.status_code == 422
    assert "BUSINESS_UNIT_INVALID" in r.text

"""SPEC 018 §7 · OD-HATCH-V4-01 RATIFIED 2026-11-21 — `fertile_eggs_to_pit` es POST-CARGA.

Decisión Owner: los huevos fértiles a fosa son huevos **ya cargados** retirados del proceso
durante la incubación/ovoscopia (antes de nacedora). Consecuencias certificadas aquí:

- **D-12** `eggs_in_process` V4 = `eggs_set − eggs_transferred − fertile_eggs_to_pit` solo si los
  tres son KNOWN (un UNKNOWN nunca se toma por 0: jamás 1000 con `pit` UNKNOWN).
- **D-13** validación: `pit ≤ set` y `transferred + pit ≤ set` (sin doble error); sin `set` KNOWN
  solo queda la cota derivada `pit ≤ received` (`pit ⊆ set ⊆ received`).
- **D-14** BR-03 no cambia: el saldo disponible para cargar NO resta la fosa (es post-carga).
- **D-15** V3 histórica intacta: `eggs_in_process = set − transferred − eggs_discarded`.

Casos obligatorios del mandato: H4-FOSA-01..07. La cabecera V4 y los helpers se reutilizan de
`test_cutover_hatchery_v4`/`cutover_v2_fixtures` (sin duplicar infraestructura).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import select

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import (  # noqa: E402
    aplicar, aprobar, corte, crear_batch, fila_incubadora,
    headers_aprobador, items_por_referencia, preparar, subir, xlsx_v2,
)

EMPRESA = 1

_CAMPOS_APERTURA = (
    "eggs_received", "eggs_received_status", "eggs_set", "eggs_set_status",
    "eggs_transferred", "eggs_transferred_status",
    "fertile_eggs_to_pit", "fertile_eggs_to_pit_status",
    "eggs_discarded", "eggs_discarded_status",
)


async def _apertura(lot_id: int) -> dict:
    """Valores y estados físicos de `hatchery_openings` para un lote (lectura ORM)."""
    from app.cutover.models import HatcheryOpening

    async with database.async_session() as s:
        ho = (await s.execute(select(HatcheryOpening).where(HatcheryOpening.lot_id == lot_id))).scalar_one()
        return {campo: getattr(ho, campo) for campo in _CAMPOS_APERTURA}


async def _subir_para_validar(client, headers, filas: list, dias: int) -> int:
    batch_id = await crear_batch(client, headers, "hatchery", corte(dias))
    r = await subir(client, headers, batch_id, xlsx_v2("hatchery", filas, company_id=EMPRESA))
    assert r.status_code == 200, r.text
    return batch_id


async def _errores(client, headers, filas: list, dias: int) -> tuple[dict, list[tuple]]:
    batch_id = await _subir_para_validar(client, headers, filas, dias)
    v = (await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=headers)).json()
    return v, sorted((e["row_number"], e["field"], e["error_code"]) for e in v["errors"])


async def _aplicar_batch(client, headers, headers_apr, filas: list, dias: int) -> int:
    """Pipeline completo staging → validate → preview → approve → apply."""
    batch_id = await _subir_para_validar(client, headers, filas, dias)
    v = (await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=headers)).json()
    assert v["invalid_rows"] == 0, v["errors"]
    await aprobar(client, headers, headers_apr, batch_id)
    r = await aplicar(client, headers, batch_id)
    assert r.status_code == 200, r.text
    return batch_id


async def _preview(client, headers, batch_id: int) -> dict[str, dict]:
    r = await client.get(f"/api/v1/cutover-batches/{batch_id}/preview", headers=headers)
    assert r.status_code == 200, r.text
    return {f["legacy_lot_code"]: f for f in r.json()["rows"]}


async def _reconciliacion(client, headers, batch_id: int) -> dict[str, dict]:
    r = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=headers)
    assert r.status_code == 200, r.text
    return {f["legacy_lot_code"]: f for f in r.json()["lots"]}


# ── H4-FOSA-01 · fosa > 0 resta del proceso ─────────────────────────────────

@pytest.mark.asyncio
async def test_h4_fosa_01_en_proceso_resta_la_fosa(auth_headers, http_client, seeded_ids):
    """received 10000, set 9000, transferred 8000, pit 100 ⇒ válido y en proceso 900 (D-12/AC-V4-17)."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        fila_incubadora("H4-FOSA-01", eggs_received=10000, eggs_set=9000, eggs_transferred=8000,
                        fertile_eggs_to_pit=100),
    ], 90)

    preview = await _preview(http_client, auth_headers, batch_id)
    assert preview["H4-FOSA-01"]["values"]["fertile_eggs_to_pit"] == {"value": 100, "status": "KNOWN"}
    assert preview["H4-FOSA-01"]["derived"]["eggs_in_process"] == 900

    rec = await _reconciliacion(http_client, auth_headers, batch_id)
    apertura = rec["H4-FOSA-01"]["opening"]["hatchery"]
    assert apertura["eggs_in_process"] == 900                     # 9000 − 8000 − 100
    assert (apertura["fertile_eggs_to_pit_status"], apertura["eggs_transferred_status"]) == ("KNOWN", "KNOWN")
    assert rec["H4-FOSA-01"]["current"]["eggs_in_process"] == 900  # sin eventos post-corte

    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    ho = await _apertura(lotes["H4-FOSA-01"])
    assert (ho["fertile_eggs_to_pit"], ho["fertile_eggs_to_pit_status"]) == (100, "KNOWN")


# ── H4-FOSA-02 · transferidos + fosa = set ──────────────────────────────────

@pytest.mark.asyncio
async def test_h4_fosa_02_transferidos_mas_fosa_igual_a_cargados(auth_headers, http_client, seeded_ids):
    """set 9000, transferred 8000, pit 1000 ⇒ válido (igualdad, no exceso) y en proceso 0 (AC-V4-16)."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        fila_incubadora("H4-FOSA-02", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=1000),
    ], 91)

    preview = await _preview(http_client, auth_headers, batch_id)
    assert preview["H4-FOSA-02"]["derived"]["eggs_in_process"] == 0
    rec = await _reconciliacion(http_client, auth_headers, batch_id)
    assert rec["H4-FOSA-02"]["opening"]["hatchery"]["eggs_in_process"] == 0


# ── H4-FOSA-03 · transferidos + fosa > set ⇒ DENY ───────────────────────────

@pytest.mark.asyncio
async def test_h4_fosa_03_transferidos_mas_fosa_excede_los_cargados(auth_headers, http_client, seeded_ids):
    """set 9000, transferred 8000, pit 1001 ⇒ CONSISTENCY_MISMATCH en `fertile_eggs_to_pit` (AC-V4-16)."""
    await preparar(seeded_ids)
    filas = [fila_incubadora("H4-FOSA-03", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=1001)]
    batch_id = await _subir_para_validar(http_client, auth_headers, filas, 92)
    v = (await http_client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=auth_headers)).json()
    assert sorted((e["row_number"], e["field"], e["error_code"]) for e in v["errors"]) == [
        (2, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH")]
    assert (v["valid_rows"], v["invalid_rows"]) == (0, 1)

    # Un batch con una fila inválida no se envía a aprobación (BATCH_STATE_INVALID).
    r = await http_client.post(f"/api/v1/cutover-batches/{batch_id}/submit", headers=auth_headers)
    assert r.status_code == 409 and "BATCH_STATE_INVALID" in r.json()["detail"], r.text


# ── H4-FOSA-04 · fosa > set ⇒ DENY (aunque transferidos sea UNKNOWN) ────────

@pytest.mark.asyncio
async def test_h4_fosa_04_fosa_mayor_que_cargados(auth_headers, http_client, seeded_ids):
    """set 9000, transferred UNKNOWN, pit 9001 ⇒ CONSISTENCY_MISMATCH; pit 9000 es válido con en proceso UNKNOWN."""
    await preparar(seeded_ids)
    cuerpo, errores = await _errores(http_client, auth_headers, [
        fila_incubadora("H4-FOSA-04A", eggs_set=9000, eggs_transferred=None, fertile_eggs_to_pit=9001),
        fila_incubadora("H4-FOSA-04B", eggs_set=9000, eggs_transferred=None, fertile_eggs_to_pit=9000),
    ], 93)
    assert errores == [(2, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH")]
    assert (cuerpo["valid_rows"], cuerpo["invalid_rows"]) == (1, 1)

    # `transferred` UNKNOWN ⇒ `eggs_in_process` UNKNOWN (nunca se toma por 0), preview y derivados.
    assert cuerpo["valid_rows"] == 1
    batch_id = await _subir_para_validar(http_client, auth_headers, [
        fila_incubadora("H4-FOSA-04B", eggs_set=9000, eggs_transferred=None, fertile_eggs_to_pit=9000),
    ], 93)
    preview = await _preview(http_client, auth_headers, batch_id)
    assert preview["H4-FOSA-04B"]["derived"]["eggs_in_process"] is None


# ── H4-FOSA-05 · fosa UNKNOWN ⇒ en proceso UNKNOWN ──────────────────────────

@pytest.mark.asyncio
async def test_h4_fosa_05_fosa_unknown_no_inventa_en_proceso(auth_headers, http_client, seeded_ids):
    """set 9000, transferred 8000, pit UNKNOWN ⇒ válido y `eggs_in_process` None (no 1000) (AC-V4-17)."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        fila_incubadora("H4-FOSA-05", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=None),
    ], 94)

    preview = await _preview(http_client, auth_headers, batch_id)
    assert preview["H4-FOSA-05"]["values"]["fertile_eggs_to_pit"] == {"value": None, "status": "UNKNOWN"}
    assert preview["H4-FOSA-05"]["derived"]["eggs_in_process"] is None

    rec = await _reconciliacion(http_client, auth_headers, batch_id)
    apertura = rec["H4-FOSA-05"]["opening"]["hatchery"]
    assert apertura["fertile_eggs_to_pit_status"] == "UNKNOWN"
    assert apertura["eggs_in_process"] is None
    assert rec["H4-FOSA-05"]["current"]["eggs_in_process"] is None

    # Con `set` o `transferred` UNKNOWN el derivado también es UNKNOWN (nivel derivados, sin BD).
    from datetime import date

    from app.cutover.contracts import contrato
    from app.cutover.validation import ValidadorDeDominio

    validador = ValidadorDeDominio(None, company_id=EMPRESA, contrato=contrato("hatchery"),
                                   cutover_date=date(2026, 11, 21))  # type: ignore[arg-type]

    def _celda(valor, estado: str) -> dict:
        return {"value": valor, "status": estado}

    for pit, pit_estado in ((None, "UNKNOWN"), (0, "KNOWN"), (100, "KNOWN")):
        for set_, transf in ((None, 8000), (9000, None), (None, None)):
            fila = {"normalized": {
                "eggs_set": _celda(set_, "KNOWN" if set_ is not None else "UNKNOWN"),
                "eggs_transferred": _celda(transf, "KNOWN" if transf is not None else "UNKNOWN"),
                "fertile_eggs_to_pit": _celda(pit, pit_estado),
            }, "_derived": {}}
            validador._derivados(fila)
            assert fila["_derived"]["eggs_in_process"] is None, (set_, transf, pit, pit_estado)
    # Control positivo del helper: los tres KNOWN sí derivan el número.
    fila = {"normalized": {"eggs_set": _celda(9000, "KNOWN"), "eggs_transferred": _celda(8000, "KNOWN"),
                           "fertile_eggs_to_pit": _celda(100, "KNOWN")}, "_derived": {}}
    validador._derivados(fila)
    assert fila["_derived"]["eggs_in_process"] == 900


# ── H4-FOSA-06 · pit = 0 conocido ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_h4_fosa_06_pit_cero_conocido(auth_headers, http_client, seeded_ids):
    """`pit = 0` KNOWN ⇒ en proceso = set − transferred (9000 − 8000 = 1000) y estado KNOWN en la fosa."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        fila_incubadora("H4-FOSA-06", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=0),
    ], 95)

    preview = await _preview(http_client, auth_headers, batch_id)
    assert preview["H4-FOSA-06"]["values"]["fertile_eggs_to_pit"] == {"value": 0, "status": "KNOWN"}
    assert preview["H4-FOSA-06"]["derived"]["eggs_in_process"] == 1000

    rec = await _reconciliacion(http_client, auth_headers, batch_id)
    apertura = rec["H4-FOSA-06"]["opening"]["hatchery"]
    assert (apertura["fertile_eggs_to_pit"], apertura["fertile_eggs_to_pit_status"]) == (0, "KNOWN")
    assert apertura["eggs_in_process"] == 1000

    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    ho = await _apertura(lotes["H4-FOSA-06"])
    assert (ho["fertile_eggs_to_pit"], ho["fertile_eggs_to_pit_status"]) == (0, "KNOWN")


# ── H4-FOSA-07 · no doble conteo (no incubables + fosa) ─────────────────────

@pytest.mark.asyncio
async def test_h4_fosa_07_sin_doble_conteo_entre_no_incubables_y_fosa(auth_headers, http_client, seeded_ids):
    """AC-V4-18: received 10000, no incubables 1000, set 9000, pit 100, transferred 8000.

    Disponible para cargar (BR-03) = 0 y en proceso = 900 (ni −100 ni 800): la fosa es POST-CARGA y
    BR-03 NO la resta (D-14). Se contrasta con un lote equivalente con `pit = 0` (mismo saldo).
    """
    await preparar(seeded_ids)
    from app.operations.validators import get_hatchery_egg_balance

    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        fila_incubadora("H4-FOSA-07", eggs_received=10000, eggs_set=9000, eggs_transferred=8000,
                        fertile_eggs_to_pit=100),
        fila_incubadora("H4-FOSA-07B", eggs_received=10000, eggs_set=9000, eggs_transferred=8000,
                        fertile_eggs_to_pit=0),
    ], 96)
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)

    async with database.async_session() as s:
        # BR-03: 10000 − 9000 − 1000 (no incubables) = 0; la fosa (post-carga) no interviene.
        assert await get_hatchery_egg_balance(s, lotes["H4-FOSA-07"]) == 0
        assert await get_hatchery_egg_balance(s, lotes["H4-FOSA-07B"]) == 0  # mismo saldo con pit 0

    rec = await _reconciliacion(http_client, auth_headers, batch_id)
    con_fosa = rec["H4-FOSA-07"]
    assert con_fosa["opening"]["hatchery"]["eggs_non_incubable_total"] == 1000
    assert con_fosa["opening"]["hatchery"]["eggs_in_process"] == 900     # ni −100 ni 800
    assert con_fosa["current"]["eggs_available_hatchery"] == 0
    assert rec["H4-FOSA-07B"]["opening"]["hatchery"]["eggs_in_process"] == 1000
    assert rec["H4-FOSA-07B"]["current"]["eggs_available_hatchery"] == 0


# ── V3 histórica intacta (D-15/AC-V4-19) ────────────────────────────────────

@pytest.mark.asyncio
async def test_h4_fosa_v3_historica_no_cambia(auth_headers, http_client, seeded_ids):
    """V3 histórica (como AC-V4-11): `eggs_in_process = set − transferred − eggs_discarded`, sin fosa."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids),
                                    [fila_incubadora("H4-FOSA-V3", eggs_transferred=8000, fertile_eggs_to_pit=None)],
                                    97)
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)

    from app.cutover.models import CutoverBatch, HatcheryOpening

    async with database.async_session() as s:
        ho = (await s.execute(select(HatcheryOpening).where(HatcheryOpening.lot_id == lotes["H4-FOSA-V3"]))).scalar_one()
        ho.eggs_discarded, ho.eggs_discarded_status = 100, "KNOWN"
        ho.fertile_eggs_to_pit, ho.fertile_eggs_to_pit_status = None, "UNKNOWN"
        batch = (await s.execute(select(CutoverBatch).where(CutoverBatch.id == batch_id))).scalar_one()
        batch.template_version = "v3"
        await s.commit()

    h = (await _reconciliacion(http_client, auth_headers, batch_id))["H4-FOSA-V3"]
    assert h["opening"]["hatchery"]["eggs_discarded_status"] == "KNOWN"
    assert h["opening"]["hatchery"]["eggs_in_process"] == 9000 - 8000 - 100  # fórmula V3, sin fosa


# ── fosa con `eggs_received` UNKNOWN (reglas independientes de received) ────

@pytest.mark.asyncio
async def test_h4_fosa_08_reglas_de_fosa_sin_eggs_received(auth_headers, http_client, seeded_ids):
    """Las reglas (a)/(b) de D-13 no dependen de `eggs_received`: se evalúan igual con received vacío.

    `eggs_received` es obligatorio, así que el vacío añade `REQUIRED_FIELD_MISSING` en esa columna,
    pero el exceso de fosa sobre los cargados sigue saliendo como `CONSISTENCY_MISMATCH`.
    """
    await preparar(seeded_ids)
    cuerpo, errores = await _errores(http_client, auth_headers, [
        fila_incubadora("H4-FOSA-NORCV", eggs_received=None, eggs_set=9000, eggs_transferred=8000,
                        fertile_eggs_to_pit=9001),
        fila_incubadora("H4-FOSA-NORCV-B", eggs_received=None, eggs_set=9000, eggs_transferred=8000,
                        fertile_eggs_to_pit=100),
    ], 98)
    assert errores == [(2, "eggs_received", "REQUIRED_FIELD_MISSING"),
                       (2, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH"),
                       (3, "eggs_received", "REQUIRED_FIELD_MISSING")]
    assert (cuerpo["valid_rows"], cuerpo["invalid_rows"]) == (0, 2)


# ── fosa ≤ received cuando `eggs_set` es UNKNOWN (cota derivada) ────────────

@pytest.mark.asyncio
async def test_h4_fosa_09_cota_derivada_cuando_set_es_unknown(auth_headers, http_client, seeded_ids):
    """Sin `eggs_set` KNOWN solo queda `pit ≤ received` (pit ⊆ set ⊆ received), no `pit ≤ set`."""
    await preparar(seeded_ids)
    cuerpo, errores = await _errores(http_client, auth_headers, [
        fila_incubadora("H4-FOSA-SETUNK", eggs_set=None, fertile_eggs_to_pit=10001),   # > received ⇒ error
        fila_incubadora("H4-FOSA-SETUNK-B", eggs_set=None, fertile_eggs_to_pit=9000),  # ≤ received ⇒ válida
    ], 99)
    assert errores == [(2, "eggs_set", "REQUIRED_FIELD_MISSING"),
                       (2, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH"),
                       (3, "eggs_set", "REQUIRED_FIELD_MISSING")]
    assert (cuerpo["valid_rows"], cuerpo["invalid_rows"]) == (0, 2)

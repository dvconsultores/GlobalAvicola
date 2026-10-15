"""SPEC 006 · Cutover v2 — apply por BU con destino por campo (`10_APPLY_DESTINATION_MATRIX`).

Cada BU demuestra: SOURCE FILE FIELD → RAW → NORMALIZED → STAGING → DOMAIN ENTITY → DOMAIN FIELD.
Además: idempotencia (mismo checksum), doble apply, segregación, multiempresa, BU
deshabilitada / sin concesión y la guarda defensiva de duplicados en el apply.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import select

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import (  # noqa: E402
    LINEA, RAZA, aplicar, aprobar, corte, crear_batch, fila_engorde, fila_incubadora, fila_reproductoras,
    headers_aprobador, items_por_referencia, preparar, subir, xlsx_v2,
)
from time_reference import days_ago, iso_days_ago  # noqa: E402


async def _aplicado(client, headers, seeded_ids, bu: str, filas: list, dias: int) -> tuple[int, dict[str, int]]:
    batch_id = await crear_batch(client, headers, bu, corte(dias))
    r = await subir(client, headers, batch_id, xlsx_v2(bu, filas, company_id=seeded_ids["company_id"]))
    assert r.status_code == 200 and r.json()["status"] == "validated", r.text
    await aprobar(client, headers, headers_aprobador(seeded_ids), batch_id)
    r = await aplicar(client, headers, batch_id)
    assert r.status_code == 200, r.text
    return batch_id, await items_por_referencia(client, headers, batch_id)


async def _lote_opening_fase(lot_id: int):
    from app.lots.models import LotPhase, OpeningBalance
    from app.masters.models import Lot

    async with database.async_session() as s:
        lote = (await s.execute(select(Lot).where(Lot.id == lot_id))).scalar_one()
        ob = (await s.execute(select(OpeningBalance).where(OpeningBalance.lot_id == lot_id))).scalar_one()
        fases = (await s.execute(select(LotPhase).where(LotPhase.lot_id == lot_id))).scalars().all()
    return lote, ob, fases


@pytest.mark.asyncio
async def test_apply_grandparent_destino_por_campo(auth_headers, http_client, seeded_ids):
    ids = await preparar(seeded_ids)
    filas = [fila_reproductoras("grandparent", "GP-APP-1", fase="PROD", genetic_line_code=LINEA, breed_name=None,
                                birds_placed_males=1050, birds_placed_females=9450, area_code="CUT2-AREA", sex="mixed",
                                phase_start_date=iso_days_ago(100))]
    _, por_ref = await _aplicado(http_client, auth_headers, seeded_ids, "grandparent", filas, 80)
    lote, ob, fases = await _lote_opening_fase(por_ref["GP-APP-1"])
    assert (lote.bird_type.value, lote.origin, lote.legacy_lot_code, lote.lot_code) == ("grandparent", "MIGRATED", "GP-APP-1", "GP-APP-1")
    assert (lote.farm_id, lote.house_id, lote.area_id, lote.genetic_line_id) == (ids["farm_id"], ids["house_id"], ids["area_id"], ids["genetic_line_id"])
    assert lote.sex.value == "mixed" and lote.source_system == "LEGACY" and lote.source_reference == "REF-GP-APP-1"
    assert lote.start_date.date() == days_ago(200) and lote.activation_type == "normal" and lote.status.value == "active"
    assert (ob.initial_male_count, ob.initial_female_count, ob.initial_mixed_count) == (1000, 9000, 0)
    assert (ob.placed_male_count, ob.placed_female_count, ob.placed_status) == (1050, 9450, "KNOWN")
    assert (ob.accumulated_mortality_male, ob.accumulated_mortality_female, ob.mortality_status) == (50, 450, "KNOWN")
    assert (ob.accumulated_culls_male, ob.accumulated_culls_female, ob.culls_status) == (0, 0, "KNOWN")
    assert (ob.accumulated_feed_kg, ob.feed_status) == (120000.5, "KNOWN")
    assert (ob.current_avg_weight, ob.weight_status) == (3200, "KNOWN")
    assert (ob.accumulated_egg_production, ob.egg_production_status) == (180000, "KNOWN")
    assert (ob.accumulated_eggs_to_hatchery, ob.eggs_to_hatchery_status) == (150000, "KNOWN")
    assert ob.chicks_hatched_status == ob.broiler_received_status == ob.outbound_status == "NOT_APPLICABLE"
    assert (ob.age_days, ob.age_status) == (200 - 80, "KNOWN")
    assert ob.phase_at_activation_id == ids["PROD"] and ob.activation_date == days_ago(80)
    assert ob.template_version == "v2" and ob.cutover_datetime is not None and ob.is_manual_activation is False
    assert (ob.source_system, ob.source_reference, ob.legacy_lot_code) == ("LEGACY", "REF-GP-APP-1", "GP-APP-1")
    assert len(fases) == 1 and fases[0].phase_id == ids["PROD"] and fases[0].start_date == days_ago(100)
    assert (fases[0].start_population_male, fases[0].start_population_female, fases[0].start_weight_avg) == (1000, 9000, 3200)
    assert fases[0].is_active


@pytest.mark.asyncio
async def test_apply_breeder_cria_y_produccion(auth_headers, http_client, seeded_ids):
    ids = await preparar(seeded_ids)
    filas = [
        fila_reproductoras("breeder", "BR-CRIA", fase="CRIA", real_start_date=iso_days_ago(120), phase_start_date=None,
                           accumulated_egg_production="N/A", accumulated_eggs_to_hatchery="N/A",
                           genetic_line_code=LINEA, breed_name=RAZA, historical_culls_males=None, historical_culls_females=None),
        fila_reproductoras("breeder", "BR-PROD", fase="PROD", genetic_line_code=LINEA, breed_name=RAZA),
    ]
    _, por_ref = await _aplicado(http_client, auth_headers, seeded_ids, "breeder", filas, 81)
    cria, ob_c, fases_c = await _lote_opening_fase(por_ref["BR-CRIA"])
    prod, ob_p, fases_p = await _lote_opening_fase(por_ref["BR-PROD"])
    assert cria.bird_type.value == prod.bird_type.value == "breeder"
    assert cria.breed_id == ids["breed_id"] and cria.genetic_line_id == ids["genetic_line_id"]
    assert ob_c.phase_at_activation_id == ids["CRIA"] and fases_c[0].phase_id == ids["CRIA"]
    assert fases_c[0].start_date == days_ago(120), "sin phase_start_date la fase empieza con el lote"
    assert ob_c.egg_production_status == ob_c.eggs_to_hatchery_status == "NOT_APPLICABLE"
    assert ob_c.accumulated_egg_production is None and ob_c.accumulated_eggs_to_hatchery is None
    assert ob_c.culls_status == "UNKNOWN" and (ob_c.accumulated_culls_male, ob_c.accumulated_culls_female) == (0, 0)
    assert ob_c.age_days == 120 - 81
    assert ob_p.phase_at_activation_id == ids["PROD"] and ob_p.egg_production_status == "KNOWN"
    assert ob_p.accumulated_egg_production == 180000
    assert cria.sex is None and prod.sex is None, "sin declarar: no se inventa el sexo de reproductoras"


@pytest.mark.asyncio
async def test_apply_broiler_mixto(auth_headers, http_client, seeded_ids):
    ids = await preparar(seeded_ids)
    filas = [fila_engorde("ENG-APP-1"),
             fila_engorde("ENG-APP-2", age_days=None, real_start_date=iso_days_ago(110), historical_mortality=None,
                          partial_outbound_birds="N/A", accumulated_birds_received=None)]
    _, por_ref = await _aplicado(http_client, auth_headers, seeded_ids, "broiler", filas, 82)
    lote, ob, fases = await _lote_opening_fase(por_ref["ENG-APP-1"])
    assert lote.bird_type.value == "broiler" and lote.sex.value == "mixed" and lote.origin == "MIGRATED"
    assert (ob.initial_male_count, ob.initial_female_count, ob.initial_mixed_count, ob.initial_mixed_status) == (0, 0, 10000, "KNOWN")
    assert (ob.accumulated_broiler_received, ob.broiler_received_status) == (10500, "KNOWN")
    assert (ob.accumulated_mortality_mixed, ob.mortality_status) == (300, "KNOWN")
    assert (ob.accumulated_culls_mixed, ob.culls_status) == (200, "KNOWN")
    assert (ob.accumulated_outbound_birds, ob.outbound_status) == (0, "KNOWN")
    assert (ob.accumulated_feed_kg, ob.current_avg_weight) == (15000, 900)
    assert (ob.age_days, ob.age_status) == (20, "KNOWN")
    assert ob.egg_production_status == ob.eggs_to_hatchery_status == ob.chicks_hatched_status == ob.placed_status == "NOT_APPLICABLE"
    assert ob.phase_at_activation_id == ids["ENGORDE"] and fases[0].phase_id == ids["ENGORDE"]
    _, ob2, _ = await _lote_opening_fase(por_ref["ENG-APP-2"])
    assert (ob2.age_days, ob2.age_status) == (110 - 82, "KNOWN"), "edad derivada de la fecha de inicio cuando no se declara"
    assert ob2.mortality_status == "UNKNOWN" and ob2.accumulated_mortality_mixed == 0
    assert ob2.outbound_status == "NOT_APPLICABLE" and ob2.accumulated_outbound_birds is None
    assert ob2.broiler_received_status == "UNKNOWN" and ob2.accumulated_broiler_received is None


@pytest.mark.asyncio
async def test_apply_hatchery_con_lote_fuente_y_na(auth_headers, http_client, seeded_ids):
    ids = await preparar(seeded_ids)
    empresa = seeded_ids["company_id"]
    from app.masters.models import BirdTypeEnum, Lot, LotStatus

    async with database.async_session() as s:
        if (await s.execute(select(Lot).where(Lot.lot_code == "CUT2-FUENTE-BR"))).scalars().first() is None:
            s.add(Lot(company_id=empresa, lot_code="CUT2-FUENTE-BR", origin="NATIVE", bird_type=BirdTypeEnum.BREEDER,
                      status=LotStatus.ACTIVE, activation_type="normal"))
            await s.commit()
        fuente = (await s.execute(select(Lot).where(Lot.lot_code == "CUT2-FUENTE-BR"))).scalar_one()
    filas = [fila_incubadora("INC-APP-1", source_lot_code="CUT2-FUENTE-BR", generation="breeder", set_date="N/A",
                             expected_hatch_date=None, eggs_set=0, eggs_transferred="N/A", eggs_discarded=None,
                             chicks_hatched="N/A", chicks_available="N/A")]
    _, por_ref = await _aplicado(http_client, auth_headers, seeded_ids, "hatchery", filas, 83)
    lote, ob, fases = await _lote_opening_fase(por_ref["INC-APP-1"])
    from app.cutover.models import HatcheryOpening

    async with database.async_session() as s:
        ho = (await s.execute(select(HatcheryOpening).where(HatcheryOpening.lot_id == lote.id))).scalar_one()
    assert lote.bird_type.value == "hatchery" and lote.hatchery_purpose == "breeder" and lote.sex.value == "mixed"
    assert lote.start_date.date() == days_ago(120)
    assert (ho.hatchery_id, ho.incubator_id, ho.hatcher_id) == (ids["hatchery_id"], ids["incubator_id"], ids["hatcher_id"])
    assert (ho.source_lot_id, ho.source_lot_reference, ho.generation) == (fuente.id, "CUT2-FUENTE-BR", "breeder")
    assert ho.reception_date == days_ago(120)
    assert (ho.set_date, ho.set_date_status) == (None, "NOT_APPLICABLE")
    assert (ho.expected_hatch_date, ho.expected_hatch_date_status) == (None, "UNKNOWN")
    assert (ho.eggs_received, ho.eggs_received_status, ho.eggs_set, ho.eggs_set_status) == (10000, "KNOWN", 0, "KNOWN")
    assert (ho.eggs_transferred, ho.eggs_transferred_status) == (None, "NOT_APPLICABLE")
    assert (ho.eggs_discarded, ho.eggs_discarded_status) == (None, "UNKNOWN")
    assert (ob.accumulated_chicks_hatched, ob.chicks_hatched_status) == (None, "NOT_APPLICABLE")
    assert (ob.initial_mixed_count, ob.initial_mixed_status) == (0, "NOT_APPLICABLE")
    assert ob.feed_status == ob.weight_status == ob.mortality_status == "NOT_APPLICABLE"
    assert ob.phase_at_activation_id == ids["INCUB"] and fases[0].phase_id == ids["INCUB"] and fases[0].start_date == days_ago(120)
    assert (ob.age_days, ob.age_status) == (120 - 83, "KNOWN")


@pytest.mark.asyncio
async def test_reuso_explicito_de_lote_existente(auth_headers, http_client, seeded_ids):
    ids = await preparar(seeded_ids)
    empresa = seeded_ids["company_id"]
    from app.masters.models import BirdTypeEnum, Lot, LotStatus

    async with database.async_session() as s:
        if (await s.execute(select(Lot).where(Lot.lot_code == "CUT2-REUSE-GP"))).scalars().first() is None:
            s.add(Lot(company_id=empresa, lot_code="CUT2-REUSE-GP", origin="NATIVE", bird_type=BirdTypeEnum.GRANDPARENT,
                      status=LotStatus.ACTIVE, activation_type="normal", start_date=None))
            await s.commit()
    filas = [fila_reproductoras("grandparent", "LEG-REUSE-GP", existing_lot_code="CUT2-REUSE-GP", fase="PROD")]
    _, por_ref = await _aplicado(http_client, auth_headers, seeded_ids, "grandparent", filas, 84)
    lote, ob, fases = await _lote_opening_fase(por_ref["LEG-REUSE-GP"])
    assert lote.lot_code == "CUT2-REUSE-GP" and lote.origin == "NATIVE", "el lote existente no se duplica ni se reescribe su origen"
    assert lote.legacy_lot_code == "LEG-REUSE-GP" and lote.farm_id == ids["farm_id"] and lote.house_id == ids["house_id"]
    assert lote.start_date.date() == days_ago(200), "solo se completa lo que faltaba"
    assert ob.legacy_lot_code == "LEG-REUSE-GP" and len(fases) == 1


@pytest.mark.asyncio
async def test_idempotencia_doble_apply_y_segregacion(auth_headers, http_client, seeded_ids):
    await preparar(seeded_ids)
    empresa = seeded_ids["company_id"]
    contenido = xlsx_v2("breeder", [fila_reproductoras("breeder", "BR-IDEM")], company_id=empresa)
    b1 = await crear_batch(http_client, auth_headers, "breeder", corte(85))
    assert (await subir(http_client, auth_headers, b1, contenido)).status_code == 200
    # S10: re-subir el mismo archivo no duplica filas; el mismo checksum en otro batch del mismo corte ⇒ 409.
    r = await subir(http_client, auth_headers, b1, contenido)
    assert r.status_code == 200 and r.json()["total_rows"] == 1
    b2 = await crear_batch(http_client, auth_headers, "breeder", corte(85))
    r = await subir(http_client, auth_headers, b2, contenido)
    assert r.status_code == 409 and "DUPLICATE_UPLOAD" in r.text
    # Segregación: el creador no aprueba su propio batch.
    assert (await http_client.post(f"/api/v1/cutover-batches/{b1}/submit", headers=auth_headers)).status_code == 200
    r = await http_client.post(f"/api/v1/cutover-batches/{b1}/approve", headers=auth_headers)
    assert r.status_code == 403 and "SEGREGATION_VIOLATION" in r.text
    assert (await http_client.post(f"/api/v1/cutover-batches/{b1}/approve", headers=headers_aprobador(seeded_ids))).status_code == 200
    # S5: doble apply ⇒ 409 determinista; un VALIDATED tampoco se aplica.
    assert (await aplicar(http_client, auth_headers, b1)).status_code == 200
    r = await aplicar(http_client, auth_headers, b1)
    assert r.status_code == 409 and "BATCH_STATE_INVALID" in r.text


@pytest.mark.asyncio
async def test_multiempresa_bu_deshabilitada_y_sin_concesion(auth_headers, http_client, seeded_ids):
    """S3/S4: la empresa B no ve ni aplica lo de A; BU apagada ⇒ 403 aun para actor global; sin grant ⇒ 403."""
    from datetime import datetime, timezone

    from app.auth.security import create_access_token
    from app.business_units.models import BusinessUnit as UnidadDeNegocio
    from app.business_units.models import CompanyBusinessUnit, UserBusinessUnit
    from test_ga_req_061_cutover_c3_lifecycle import _otorgar
    from test_ga_req_061_cutover_c7_matrix import _headers_ajenos, _rol_de

    await preparar(seeded_ids)
    empresa = seeded_ids["company_id"]
    b = await crear_batch(http_client, auth_headers, "hatchery", corte(86))
    assert (await subir(http_client, auth_headers, b, xlsx_v2("hatchery", [fila_incubadora("INC-MULTI")], company_id=empresa))).status_code == 200
    await aprobar(http_client, auth_headers, headers_aprobador(seeded_ids), b)

    ajenos = await _headers_ajenos(seeded_ids)
    await _otorgar(await _rol_de(seeded_ids["user_other_company_id"]), ("cutover", "create"))
    for ruta in ("", "/preview", "/errors", "/items", "/reconciliation"):
        assert (await http_client.get(f"/api/v1/cutover-batches/{b}{ruta}", headers=ajenos)).status_code == 404, ruta
    assert (await http_client.post(f"/api/v1/cutover-batches/{b}/apply", headers=ajenos)).status_code == 404
    assert (await http_client.get(f"/api/v1/cutover-templates/hatchery?batch_id={b}", headers=ajenos)).status_code == 404
    listado = (await http_client.get("/api/v1/cutover-batches", headers=ajenos)).json()
    assert all(item["id"] != b for item in listado["items"])

    async with database.async_session() as s:
        unidad = (await s.execute(select(UnidadDeNegocio).where(UnidadDeNegocio.code == "hatchery"))).scalars().first()
        habilitacion = (await s.execute(select(CompanyBusinessUnit).where(
            CompanyBusinessUnit.company_id == empresa, CompanyBusinessUnit.business_unit_id == unidad.id))).scalars().first()
        habilitacion.is_enabled = False
        await s.commit()
    try:
        r = await aplicar(http_client, auth_headers, b)
        assert r.status_code == 403 and "BU_DISABLED" in r.text
    finally:
        async with database.async_session() as s:
            fila = (await s.execute(select(CompanyBusinessUnit).where(CompanyBusinessUnit.id == habilitacion.id))).scalar_one()
            fila.is_enabled = True
            await s.commit()

    await _otorgar(await _rol_de(seeded_ids["user_operator_id"]), ("cutover", "apply"))
    async with database.async_session() as s:
        concesion = (await s.execute(select(UserBusinessUnit).where(
            UserBusinessUnit.user_id == seeded_ids["user_operator_id"],
            UserBusinessUnit.company_business_unit_id == habilitacion.id, UserBusinessUnit.revoked_at.is_(None)))).scalars().first()
        if concesion is not None:
            concesion.revoked_at = datetime.now(timezone.utc)
            await s.commit()
    operador = {"Authorization": "Bearer " + create_access_token(data={"sub": str(seeded_ids["user_operator_id"]), "role": "operator"})}
    try:
        r = await aplicar(http_client, operador, b)
        assert r.status_code == 403 and "BU_NOT_GRANTED" in r.text
    finally:
        async with database.async_session() as s:
            if concesion is not None:
                fila = (await s.execute(select(UserBusinessUnit).where(UserBusinessUnit.id == concesion.id))).scalar_one()
                fila.revoked_at = None
                await s.commit()
    assert (await aplicar(http_client, auth_headers, b)).status_code == 200


@pytest.mark.asyncio
async def test_guarda_defensiva_de_duplicados_en_el_apply():
    """La detección vive en el staging; el apply conserva la guarda (defensa en profundidad)."""
    from app.cutover.contracts import contrato
    from app.cutover.service import CutoverApplyError, CutoverService

    servicio = CutoverService(db=None, current_user={"id": 1, "company_id": 1})

    class _Item:
        id = 1
        source_row_number = 2

    with pytest.raises(CutoverApplyError) as exc:
        await servicio._lote(batch=None, item=_Item(), c=contrato("breeder"),
                             estado={"legacy_lot_code": {"value": "X", "status": "KNOWN"}}, refs={}, vistos={"X"})
    assert exc.value.code == "LOT_DUPLICATE"


@pytest.mark.asyncio
async def test_listado_detalle_errores_y_preview(auth_headers, http_client, seeded_ids):
    await preparar(seeded_ids)
    empresa = seeded_ids["company_id"]
    b = await crear_batch(http_client, auth_headers, "broiler", corte(87))
    filas = [fila_engorde("ENG-LIST-1"), fila_engorde("ENG-LIST-2", farm_code="NOPE", live_birds=-1)]
    r = await subir(http_client, auth_headers, b, xlsx_v2("broiler", filas, company_id=empresa))
    assert r.status_code == 200 and r.json()["status"] == "validating"
    detalle = (await http_client.get(f"/api/v1/cutover-batches/{b}", headers=auth_headers)).json()
    assert detalle["source_type"] == "XLSX" and detalle["template_version"] == "v2" and detalle["created_at"]
    listado = (await http_client.get("/api/v1/cutover-batches?business_unit=broiler&status=validating", headers=auth_headers)).json()
    assert any(item["id"] == b for item in listado["items"]) and listado["total"] >= 1
    xlsx = await http_client.get(f"/api/v1/cutover-batches/{b}/errors?format=xlsx", headers=auth_headers)
    assert xlsx.status_code == 200 and xlsx.content.startswith(b"PK")
    csv_ = await http_client.get(f"/api/v1/cutover-batches/{b}/errors", headers=auth_headers)
    lineas = csv_.content.decode("utf-8-sig").splitlines()
    assert lineas[0].startswith("row_number;field;error_code;message;received_value")
    assert any("NEGATIVE_VALUE" in l for l in lineas) and any("MASTER_NOT_FOUND" in l for l in lineas)
    preview = (await http_client.get(f"/api/v1/cutover-batches/{b}/preview", headers=auth_headers)).json()
    assert preview["business_unit"] == "broiler" and preview["schema_id"] == "CUTOVER_BROILER_V2"
    assert (preview["summary"]["lots"], preview["summary"]["valid_rows"], preview["summary"]["invalid_rows"]) == (2, 1, 1)
    assert preview["summary"]["live_birds"] == 10000, "solo las filas válidas suman"
    assert "live_birds" in preview["highlight"] and set(preview["highlight"]) <= set(preview["columns"])
    assert preview["rows"][1]["errors"] == 2 and preview["rows"][0]["values"]["live_birds"] == {"value": 10000, "status": "KNOWN"}

"""SPEC 005 · Sincronización inbound: RAW, validación, mapping, staging, idempotencia, watermark.

`AC-HANA-13…31`, `39`. Cubre el recorrido

    HANA (fake) → RAW → VALIDATION → MAPPING → STAGING → PROMOTION

a nivel de servicio, contra PostgreSQL real y sin SAP. Las cifras salen del dataset
determinista de `FakeHana` (`fake_hana.default_dataset`).
"""
from __future__ import annotations

import copy

import pytest
from fastapi import HTTPException

from app.integrations.sap.inbound.errors import ErrorCode
from app.integrations.sap.inbound.fake_hana import FakeHana, FakeHanaError
from app.integrations.sap.inbound.registry import HanaObject
from tests.time_reference import iso_days_ago
from tests.sap_hana_fixtures import (  # noqa: F401  (`esc` es una fixture)
    SECRETO,
    cfg_de_prueba,
    esc,
    escalar,
    filas,
    referencias,
    registros,
    sincronizar,
    ventana_amplia,
)

pytestmark = pytest.mark.asyncio

VENTANA = ventana_amplia()
# Ventana cerrada de 30 días, relativa al reloj de la suite (sin literales que caducan, R-28).
DESDE, HASTA = iso_days_ago(40), iso_days_ago(10)
DESDE_SAP, HASTA_SAP = DESDE.replace("-", ""), HASTA.replace("-", "")


def _uno(jobs, objeto):
    encontrados = [j for j in jobs if j.object_type == objeto]
    assert len(encontrados) == 1, f"un job por objeto: {[j.object_type for j in jobs]}"
    return encontrados[0]


async def _sync_ok(esc, objeto: HanaObject, **kw):
    jobs, fake = await sincronizar(esc, objetos=[objeto], **kw)
    job = _uno(jobs, objeto.value)
    assert job.status == "completed", (job.status, job.error_code, job.error_message)
    assert job.query_id.startswith(objeto.value + ".")
    assert job.rows_read == job.rows_raw + job.rows_noop + job.rows_rejected
    return job, fake


# ── Un objeto, una ruta de adaptador (`AC-HANA-13…24`) ───────────────────────

async def test_sync_company(esc):
    job, _ = await _sync_ok(esc, HanaObject.COMPANY)
    r = await registros(esc, "company")
    assert [x["source_key"] for x in r] == [f"{esc['client']}|1000"], "solo la sociedad de A"
    assert r[0]["company_code"] == "1000" and r[0]["client"] == esc["client"]
    assert (r[0]["validation_status"], r[0]["mapping_status"]) == ("VALID", "MAPPED")
    assert r[0]["promotion_status"] == "STAGED_ONLY", "sin tipo de referencia: se queda en staging"
    assert r[0]["staged_json"]["company_code"] == "1000"
    assert r[0]["staged_json"]["name"] and r[0]["staged_json"]["currency"]
    assert len(r[0]["payload_hash"]) == 64 and r[0]["payload_json"]["BUKRS"] == "1000"
    assert job.rows_raw == 1


async def test_sync_plant(esc):
    await _sync_ok(esc, HanaObject.PLANT)
    r = {x["plant_code"]: x for x in await registros(esc, "plant")}
    assert set(r) == {"1100", "1200"}, "los centros de la sociedad 1000, no los de la 2000"
    assert r["1100"]["promotion_status"] == "PROMOTED"
    assert r["1200"]["mapping_status"] == "PENDING_MAPPING"
    refs = await referencias(esc, "PLANT")
    assert [x["sap_code"] for x in refs] == ["1100"], "solo se promueve el centro mapeado"
    assert refs[0]["extra_data"]["source"] == "SAP_HANA_CLOUD"
    assert refs[0]["extra_data"]["company_code"] == "1000"
    assert refs[0]["id"] == r["1100"]["promoted_reference_id"]


async def test_sync_storage_location(esc):
    await _sync_ok(esc, HanaObject.STORAGE_LOCATION)
    r = await registros(esc, "storage_location")
    assert {x["source_key"] for x in r} >= {f"{esc['client']}|1100|A001", f"{esc['client']}|1200|I001"}
    refs = await referencias(esc, "STORAGE_LOCATION")
    assert refs and all(x["sap_code"].startswith("1100-") for x in refs)
    assert all("house_id" not in (x["extra_data"] or {}) for x in refs), "LGORT no es un galpón"


async def test_sync_vendor(esc):
    await _sync_ok(esc, HanaObject.VENDOR)
    r = await registros(esc, "vendor")
    assert r and all(x["company_code"] == "1000" for x in r)
    refs = await referencias(esc, "VENDOR")
    assert len(refs) == len(r) and all(x["description"] for x in refs)
    assert refs[0]["sap_code"] == r[0]["payload_json"]["LIFNR"], "el código SAP se conserva tal cual"


async def test_sync_material(esc):
    await _sync_ok(esc, HanaObject.MATERIAL)
    r = await registros(esc, "material")
    refs = await referencias(esc, "MATERIAL")
    assert r and len(refs) == len(r)
    assert all(len(x["sap_code"]) == 18 for x in refs), "MATNR con sus ceros significativos"
    assert all(x["unit"] for x in refs) and all(x["description"] for x in refs)


async def test_sync_batch(esc):
    await _sync_ok(esc, HanaObject.BATCH)
    r = await registros(esc, "batch")
    assert r
    refs = await referencias(esc, "SAP_BATCH")
    promovidos = [x for x in r if x["promotion_status"] == "PROMOTED"]
    assert promovidos and len(refs) == len(promovidos)
    assert all(x["plant_code"] == "1100" for x in promovidos)


async def test_sync_movement_type(esc):
    await _sync_ok(esc, HanaObject.MOVEMENT_TYPE)
    r = await registros(esc, "movement_type")
    assert r and all(x["promotion_status"] == "STAGED_ONLY" for x in r)
    assert all(x["staged_json"]["description"] for x in r)
    assert await referencias(esc, "OTHER") == [], "nada se cuela en OTHER"


async def test_sync_purchase_order(esc):
    """Cabecera, posiciones e historial van juntos: una OC sin posiciones no tiene cantidad."""
    jobs, _ = await sincronizar(esc, objetos=[HanaObject.PURCHASE_ORDER], **VENTANA)
    assert {j.object_type for j in jobs} == {
        "purchase_order", "purchase_order_item", "purchase_order_history"}
    assert all(j.status == "completed" for j in jobs), [(j.object_type, j.error_message) for j in jobs]

    cabeceras = {x["payload_json"]["EBELN"]: x for x in await registros(esc, "purchase_order")}
    assert set(cabeceras) == {esc["oc"], esc["oc_alimento"]}, "las OC de la sociedad de A"
    assert cabeceras[esc["oc"]]["promotion_status"] == "PROMOTED"
    assert cabeceras[esc["oc"]]["staged_json"]["vendor"]
    assert cabeceras[esc["oc"]]["staged_json"]["document_date"]

    posiciones = [x for x in await registros(esc, "purchase_order_item")
                  if x["payload_json"]["EBELN"] == esc["oc"]]
    assert len(posiciones) == 2, "cabecera y posiciones no se colapsan"
    assert {x["source_key"].split("|")[-1] for x in posiciones} == {"00010", "00020"}


async def test_sync_purchase_order_history(esc):
    await sincronizar(esc, objetos=[HanaObject.PURCHASE_ORDER_HISTORY], **VENTANA)
    r = await registros(esc, "purchase_order_history")
    assert r and all(x["promotion_status"] == "STAGED_ONLY" for x in r)
    assert all(x["staged_json"]["debit_credit"] in ("S", "H") for x in r)
    assert any(x["staged_json"]["debit_credit"] == "H" for x in r), "el reverso se conserva"
    assert all(len(x["source_key"].split("|")) == 8 for x in r), "clave completa de EKBE"


async def test_sync_production_order(esc):
    await _sync_ok(esc, HanaObject.PRODUCTION_ORDER, **VENTANA)
    r = await registros(esc, "production_order")
    assert r
    s = r[0]["staged_json"]
    for campo in ("order_number", "plant", "material", "planned_quantity", "unit", "status",
                  "start_date"):
        assert s.get(campo) not in (None, ""), campo
    assert await referencias(esc, "OTHER") == []


async def test_sync_transfer_order(esc):
    await _sync_ok(esc, HanaObject.TRANSFER_ORDER, **VENTANA)
    r = await registros(esc, "transfer_order")
    assert r
    s = r[0]["staged_json"]
    assert s["source_plant"] and s["destination_plant"] and s["source_plant"] != s["destination_plant"]
    assert s["material"] and s["quantity"] > 0 and s["unit"]


async def test_sync_outbound_order(esc):
    await _sync_ok(esc, HanaObject.OUTBOUND_ORDER, **VENTANA)
    r = await registros(esc, "outbound_order")
    assert r and all(x["object_type"] == "outbound_order" for x in r)
    s = r[0]["staged_json"]
    assert s["order_number"] and s["item"] and s["material"] and s["quantity"] > 0
    assert await registros(esc, "material_movement") == [], (
        "una orden de salida no es un documento de material: no se mezclan")


async def test_sync_material_movement(esc):
    await _sync_ok(esc, HanaObject.MATERIAL_MOVEMENT, **VENTANA)
    r = await registros(esc, "material_movement")
    assert r and all(x["promotion_status"] in ("STAGED_ONLY", "PENDING") for x in r)
    s = next(x["staged_json"] for x in r if x["mapping_status"] == "MAPPED")
    for campo in ("material_document", "year", "item", "movement_type", "material", "plant",
                  "quantity", "unit", "debit_credit", "posting_date", "company_code"):
        assert s.get(campo) not in (None, ""), campo
    assert any(x["staged_json"].get("reversal_reference") for x in r), "los reversos no se ignoran"


async def test_sync_all_objects_in_one_request(esc):
    jobs, _ = await sincronizar(esc, **VENTANA)
    assert {j.object_type for j in jobs} == {o.value for o in HanaObject}
    assert all(j.status == "completed" for j in jobs), [
        (j.object_type, j.status, j.error_message) for j in jobs if j.status != "completed"]
    assert len({j.sync_request_id for j in jobs}) == 1


# ── Ventana y paginación (`§17`) ─────────────────────────────────────────────

async def test_sync_window_is_bound_and_bounded(esc):
    _, fake = await sincronizar(esc, objetos=[HanaObject.MATERIAL_MOVEMENT],
                                date_from=DESDE, date_to=HASTA)
    sql, params = next(e for e in fake.executed if "MATDOC" in e[0])
    assert params["date_from"] == DESDE_SAP and params["date_to"] == HASTA_SAP
    assert DESDE_SAP not in sql

    with pytest.raises(HTTPException) as exc:
        await sincronizar(esc, objetos=[HanaObject.MATERIAL_MOVEMENT],
                          date_from=iso_days_ago(800), date_to=iso_days_ago(0))
    assert exc.value.status_code == 422, "una ventana de años es un scan encubierto"
    with pytest.raises(HTTPException):
        await sincronizar(esc, objetos=[HanaObject.MATERIAL_MOVEMENT],
                          date_from=iso_days_ago(1), date_to=iso_days_ago(30))


async def test_sync_default_window_uses_lookback(esc):
    """Sin fechas, la ventana es `hoy − lookback … hoy`: nunca abierta."""
    job, fake = await _sync_ok(esc, HanaObject.MATERIAL_MOVEMENT)
    _, params = next(e for e in fake.executed if "MATDOC" in e[0])
    assert len(params["date_from"]) == 8 and len(params["date_to"]) == 8
    assert params["date_from"] < params["date_to"]
    assert job.watermark_from == params["date_from"] and job.watermark_to == params["date_to"]


async def test_sync_paginates_with_stable_order(esc):
    cfg = cfg_de_prueba(esc["client"], page_size=2)
    jobs, fake = await sincronizar(esc, objetos=[HanaObject.MATERIAL], cfg=cfg)
    paginas = [p for sql, p in fake.executed if "MARA" in sql]
    assert len(paginas) >= 2, "con página de 2 hacen falta varias lecturas"
    assert [p["page_offset"] for p in paginas] == [2 * i for i in range(len(paginas))]
    assert all(p["page_limit"] == 2 for p in paginas)
    total = len(await registros(esc, "material"))
    assert _uno(jobs, "material").rows_read == total, "ni filas perdidas ni repetidas"


async def test_sync_max_rows_cap_marks_partial_and_keeps_watermark(esc):
    cfg = cfg_de_prueba(esc["client"], page_size=2, max_rows=2)
    jobs, _ = await sincronizar(esc, objetos=[HanaObject.MATERIAL], cfg=cfg)
    job = _uno(jobs, "material")
    assert job.status == "partial" and job.rows_read == 2
    assert await escalar(esc, "SELECT count(*) FROM sap_inbound_watermarks WHERE company_id = :c "
                              "AND object_type = 'material'", c=esc["a"]) == 0


# ── Idempotencia (`AC-HANA-29`) ──────────────────────────────────────────────

async def test_sync_duplicate_same_hash_noop(esc):
    primero, _ = await _sync_ok(esc, HanaObject.PLANT)
    antes = await registros(esc, "plant", solo_vigentes=False)
    segundo, _ = await _sync_ok(esc, HanaObject.PLANT)
    despues = await registros(esc, "plant", solo_vigentes=False)

    assert primero.rows_raw == 2 and primero.rows_noop == 0
    assert segundo.rows_raw == 0 and segundo.rows_noop == 2
    assert [(x["id"], x["version"], x["updated_at"]) for x in antes] == [
        (x["id"], x["version"], x["updated_at"]) for x in despues], "no-op: ni fila ni actualización"
    assert len(await referencias(esc, "PLANT")) == 1


async def test_sync_same_page_twice_no_duplicate(esc):
    """La misma fila dos veces en una respuesta no produce dos registros."""
    datos = copy.deepcopy(esc["datos"])
    datos["plant"] = datos["plant"] + [copy.deepcopy(f) for f in datos["plant"]]
    job, _ = await _sync_ok(esc, HanaObject.PLANT, fake=FakeHana(datos))
    assert len(await registros(esc, "plant", solo_vigentes=False)) == 2
    assert job.rows_raw == 2 and job.rows_noop == 2


async def test_sync_changed_hash_versioned(esc):
    await _sync_ok(esc, HanaObject.PLANT)
    datos = copy.deepcopy(esc["datos"])
    next(f for f in datos["plant"] if f["WERKS"] == "1100")["NAME1"] = "Granja Renombrada"
    job, _ = await _sync_ok(esc, HanaObject.PLANT, fake=FakeHana(datos))

    versiones = [x for x in await registros(esc, "plant", solo_vigentes=False)
                 if x["plant_code"] == "1100"]
    assert [(x["version"], x["is_current"]) for x in versiones] == [(1, False), (2, True)]
    assert versiones[0]["promotion_status"] == "SUPERSEDED"
    assert versiones[0]["payload_json"]["NAME1"] != "Granja Renombrada", "el RAW previo es inmutable"
    assert versiones[0]["payload_hash"] != versiones[1]["payload_hash"]
    assert job.rows_raw == 1 and job.rows_noop == 1

    refs = await referencias(esc, "PLANT")
    assert len(refs) == 1 and refs[0]["description"] == "Granja Renombrada", "upsert, no duplicado"
    assert refs[0]["id"] == versiones[1]["promoted_reference_id"]


# ── Watermark (`AC-HANA-30`) ─────────────────────────────────────────────────

async def test_sync_watermark_advances_after_success(esc):
    job, _ = await _sync_ok(esc, HanaObject.MATERIAL_MOVEMENT, date_from=DESDE, date_to=HASTA)
    marcas = await filas(esc, "SELECT * FROM sap_inbound_watermarks WHERE company_id = :c "
                              "AND object_type = 'material_movement'", c=esc["a"])
    assert len(marcas) == 1
    assert marcas[0]["watermark_value"] == HASTA_SAP == job.watermark_to
    assert marcas[0]["scope_key"] == f"client:{esc['client']}|bukrs:1000"
    assert marcas[0]["last_record_count"] == job.rows_read and marcas[0]["last_success_at"]


async def test_sync_failed_batch_does_not_advance_watermark(esc):
    await _sync_ok(esc, HanaObject.PLANT)
    marca = await filas(esc, "SELECT watermark_value, last_success_at FROM sap_inbound_watermarks "
                             "WHERE company_id = :c AND object_type = 'plant'", c=esc["a"])
    n_antes = len(await registros(esc, "plant", solo_vigentes=False))

    datos = copy.deepcopy(esc["datos"])
    for i in range(5):
        datos["plant"].append({**datos["plant"][0], "WERKS": f"13{i:02d}", "NAME1": f"Nueva {i}"})
    fake = FakeHana(datos)
    fake.fail_query_at["plant.v1"] = (2, FakeHanaError(613, "statement timeout"))  # falla la 2.ª página
    cfg = cfg_de_prueba(esc["client"], page_size=2)
    jobs, _ = await sincronizar(esc, objetos=[HanaObject.PLANT], fake=fake, cfg=cfg)

    job = _uno(jobs, "plant")
    assert job.status == "failed" and job.error_code == ErrorCode.SAP_QUERY_TIMEOUT.value
    assert job.completed_at is not None
    assert await filas(esc, "SELECT watermark_value, last_success_at FROM sap_inbound_watermarks "
                            "WHERE company_id = :c AND object_type = 'plant'", c=esc["a"]) == marca
    assert len(await registros(esc, "plant", solo_vigentes=False)) == n_antes, (
        "el batch es atómico: la primera página no queda a medias")
    assert await escalar(esc, "SELECT count(*) FROM sap_inbound_sync_jobs WHERE id = :j",
                         j=job.id) == 1, "el job fallido sí queda registrado"


async def test_sync_one_object_failing_does_not_block_the_rest(esc):
    fake = FakeHana(esc["datos"])
    fake.fail_query["vendor.v1"] = FakeHanaError(259, "invalid table name")
    jobs, _ = await sincronizar(esc, objetos=[HanaObject.VENDOR, HanaObject.MATERIAL], fake=fake)
    assert _uno(jobs, "vendor").status == "failed"
    assert _uno(jobs, "vendor").error_code == ErrorCode.SAP_OBJECT_NOT_FOUND.value
    assert _uno(jobs, "material").status == "completed"
    assert await referencias(esc, "MATERIAL")


# ── Mapping fail-closed (`AC-HANA-27`) ───────────────────────────────────────

async def test_unknown_company_pending_mapping(esc):
    """Una fila con una sociedad sin mapping se retiene: ni se promueve ni se atribuye."""
    datos = copy.deepcopy(esc["datos"])
    intrusa = {**datos["plant"][0], "WERKS": "9100", "BUKRS": "9000", "NAME1": "Centro Ajeno"}
    fake = FakeHana(datos)
    fake.inject["plant.v1"] = [intrusa]            # el origen la devuelve pese al filtro
    job, _ = await _sync_ok(esc, HanaObject.PLANT, fake=fake)

    r = {x["plant_code"]: x for x in await registros(esc, "plant")}
    assert r["9100"]["mapping_status"] == "PENDING_MAPPING"
    assert r["9100"]["error_code"] == ErrorCode.SAP_MAPPING_PENDING.value
    assert r["9100"]["promoted_reference_id"] is None
    assert "9100" not in [x["sap_code"] for x in await referencias(esc, "PLANT")]
    assert job.rows_pending_mapping >= 1

    # Y con un objeto que no depende de ningún centro: aquí la sociedad es la única barrera,
    # de modo que si dejara de comprobarse la fila se promovería.
    ajeno = {**datos["vendor"][0], "LIFNR": "0000999999", "BUKRS": "9000", "NAME1": "Proveedor Ajeno"}
    fake = FakeHana(datos)
    fake.inject["vendor.v1"] = [ajeno]
    await _sync_ok(esc, HanaObject.VENDOR, fake=fake)
    v = next(x for x in await registros(esc, "vendor") if x["payload_json"]["LIFNR"] == "0000999999")
    assert v["mapping_status"] == "PENDING_MAPPING" and v["promotion_status"] == "PENDING"
    assert v["error_code"] == ErrorCode.SAP_MAPPING_PENDING.value
    assert v["promoted_reference_id"] is None
    assert "0000999999" not in [x["sap_code"] for x in await referencias(esc, "VENDOR")]


async def test_unknown_plant_pending_mapping(esc):
    await _sync_ok(esc, HanaObject.PLANT)
    await _sync_ok(esc, HanaObject.MATERIAL_MOVEMENT, **VENTANA)
    pendientes = [x for x in await registros(esc, "material_movement")
                  if x["plant_code"] == "1200"]
    assert pendientes, "el dataset trae movimientos del centro sin mapear"
    assert all(x["mapping_status"] == "PENDING_MAPPING" for x in pendientes)
    assert all(x["promotion_status"] == "PENDING" for x in pendientes)
    assert all(x["error_code"] == ErrorCode.SAP_MAPPING_PENDING.value for x in pendientes)


async def test_mapping_added_later_releases_pending_records(esc):
    """El mapping se resuelve en la siguiente pasada aunque el hash no haya cambiado."""
    from tests.sap_hana_fixtures import mapear

    await _sync_ok(esc, HanaObject.PLANT)
    async with esc["fabrica"]() as s:
        await mapear(s, client=esc["client"], company_id=esc["a"], entity_type="PLANT",
                     sap_key="1200", parent="1000")
        await s.commit()
    job, _ = await _sync_ok(esc, HanaObject.PLANT)
    assert job.rows_noop == 2 and job.rows_promoted == 1
    assert [x["sap_code"] for x in await referencias(esc, "PLANT")] == ["1100", "1200"]


async def test_row_of_another_ga_company_is_not_persisted(esc):
    """`Q6`. Una fila cuya sociedad es de otra empresa GA no entra en el RAW de esta."""
    datos = copy.deepcopy(esc["datos"])
    de_b = next(f for f in datos["plant"] if f["BUKRS"] == "2000")
    fake = FakeHana(datos)
    fake.inject["plant.v1"] = [copy.deepcopy(de_b)]
    job, _ = await _sync_ok(esc, HanaObject.PLANT, fake=fake)

    assert job.rows_rejected == 1
    assert de_b["WERKS"] not in [x["plant_code"] for x in await registros(esc, "plant")]
    assert await registros(esc, "plant", empresa="b") == [], "y tampoco aparece en B por arte de magia"


async def test_sync_is_scoped_to_the_effective_company(esc):
    _, fake = await sincronizar(esc, objetos=[HanaObject.PLANT], actor="actor_b")
    assert {p["bukrs"] for _, p in fake.executed} == {"2000"}
    assert [x["plant_code"] for x in await registros(esc, "plant", empresa="b")] == ["2100"]
    assert await registros(esc, "plant", empresa="a") == []


async def test_company_without_mapping_makes_no_hana_call(esc):
    async with esc["fabrica"]() as s:
        from sqlalchemy import text
        await s.execute(text("DELETE FROM sap_entity_mappings WHERE company_id = :c"), {"c": esc["a"]})
        await s.commit()
    jobs, fake = await sincronizar(esc, objetos=[HanaObject.PLANT])
    job = _uno(jobs, "plant")
    assert job.status == "failed" and job.error_code == ErrorCode.SAP_MAPPING_PENDING.value
    assert fake.connections_opened == 0, "sin sociedad mapeada no hay nada que preguntarle a SAP"


async def test_company_code_outside_allowlist_is_not_queried(esc):
    cfg = cfg_de_prueba(esc["client"], company_codes=("7777",))
    jobs, fake = await sincronizar(esc, objetos=[HanaObject.PLANT], cfg=cfg)
    assert _uno(jobs, "plant").error_code == ErrorCode.SAP_MAPPING_PENDING.value
    assert fake.connections_opened == 0


# ── Contexto y configuración (`AC-HANA-39`, `34`) ────────────────────────────

async def test_sync_without_company_context_fails_closed(esc):
    fake = FakeHana(esc["datos"])
    with pytest.raises(HTTPException) as exc:
        await sincronizar(esc, actor="actor_global_sin_contexto", fake=fake)
    assert exc.value.status_code == 400
    assert fake.connections_opened == 0
    assert await escalar(esc, "SELECT count(*) FROM sap_inbound_sync_jobs WHERE company_id IN (:a, :b)",
                         a=esc["a"], b=esc["b"]) == 0


async def test_sync_not_configured_reports_and_makes_no_hana_call(esc):
    from app.integrations.sap.inbound.settings import HanaSettings

    fake = FakeHana(esc["datos"])
    jobs, _ = await sincronizar(esc, objetos=[HanaObject.PLANT], fake=fake,
                                cfg=HanaSettings(environment="test"))
    job = _uno(jobs, "plant")
    assert job.status == "failed" and job.error_code == ErrorCode.SAP_CONFIG_MISSING.value
    assert fake.connections_opened == 0
    assert "SAP_HANA_PASSWORD" in job.error_message, "dice qué falta, por su nombre"


# ── Validación y errores (`AC-HANA-26`) ──────────────────────────────────────

async def test_invalid_row_is_kept_visible_and_not_promoted(esc):
    datos = copy.deepcopy(esc["datos"])
    datos["material"][0]["MEINS"] = ""             # unidad base obligatoria
    job, _ = await _sync_ok(esc, HanaObject.MATERIAL, fake=FakeHana(datos))
    malo = next(x for x in await registros(esc, "material")
                if x["payload_json"]["MATNR"] == datos["material"][0]["MATNR"])
    assert malo["validation_status"] == "INVALID"
    assert malo["error_code"] == ErrorCode.SAP_VALIDATION_ERROR.value and "MEINS" in malo["error_message"]
    assert malo["promoted_reference_id"] is None and job.rows_invalid == 1
    assert datos["material"][0]["MATNR"] not in [x["sap_code"] for x in await referencias(esc, "MATERIAL")]


async def test_schema_mismatch_fails_the_job_without_null_filling(esc):
    fake = FakeHana(esc["datos"])
    fake.drop_columns["material.v1"] = {"MEINS"}
    jobs, _ = await sincronizar(esc, objetos=[HanaObject.MATERIAL], fake=fake)
    job = _uno(jobs, "material")
    assert job.status == "failed" and job.error_code == ErrorCode.SAP_SCHEMA_MISMATCH.value
    assert await registros(esc, "material") == []


async def test_job_error_message_is_sanitized(esc):
    fake = FakeHana(esc["datos"])
    fake.fail_connect = FakeHanaError(10, f"authentication failed user=GA_RO_TEST password={SECRETO}")
    jobs, _ = await sincronizar(esc, objetos=[HanaObject.PLANT], fake=fake)
    job = _uno(jobs, "plant")
    assert job.error_code == ErrorCode.SAP_AUTH_ERROR.value
    assert SECRETO not in (job.error_message or "")
    assert SECRETO not in str(await filas(
        esc, "SELECT * FROM sap_inbound_sync_jobs WHERE id = :j", j=job.id))


# ── Auditoría (`§42`) ────────────────────────────────────────────────────────

async def test_sync_is_reconstructible(esc):
    job, _ = await _sync_ok(esc, HanaObject.MATERIAL_MOVEMENT, date_from=DESDE, date_to=HASTA)
    assert job.company_id == esc["a"] and job.initiated_by_id == esc["ids"]["analista_a"]
    assert job.trigger == "manual" and job.source_system == "SAP_HANA_CLOUD"
    assert job.filters["date_from"] == DESDE_SAP and job.filters["company_codes"] == ["1000"]
    assert SECRETO not in str(job.filters)
    assert job.started_at and job.completed_at and job.completed_at >= job.started_at
    for contador in ("rows_read", "rows_raw", "rows_noop", "rows_valid", "rows_invalid",
                     "rows_pending_mapping", "rows_promoted", "rows_rejected"):
        assert getattr(job, contador) is not None, contador

    rastro = await filas(esc, "SELECT action::text AS accion, entity_type FROM audit_logs "
                              "WHERE company_id = :c AND entity_type = 'sap_inbound_sync'", c=esc["a"])
    assert rastro, "el sync deja rastro de auditoría"


# ── Scheduler (`§40`) ────────────────────────────────────────────────────────

async def test_scheduler_does_nothing_when_not_configured(esc):
    from app.integrations.sap.inbound.scheduler import run_scheduled_sync
    from app.integrations.sap.inbound.settings import HanaSettings

    fake = FakeHana(esc["datos"])
    resumen = await run_scheduled_sync(
        esc["fabrica"], cfg=HanaSettings(environment="test"), adapter_factory=lambda c: None)
    assert resumen["ran"] is False and resumen["reason"] == "PENDING_CREDENTIALS"
    assert fake.connections_opened == 0
    assert await escalar(esc, "SELECT count(*) FROM sap_inbound_sync_jobs WHERE company_id = :c",
                         c=esc["a"]) == 0, "sin credenciales no deja ni jobs fallidos en bucle"


async def test_scheduler_syncs_only_mapped_companies_without_actor(esc):
    from app.integrations.sap.inbound.scheduler import run_scheduled_sync
    from tests.sap_hana_fixtures import adaptador_de_prueba

    fake = FakeHana(esc["datos"])
    resumen = await run_scheduled_sync(
        esc["fabrica"], cfg=esc["cfg"], adapter_factory=lambda c: adaptador_de_prueba(fake, c),
        company_ids=[esc["a"], esc["b"]])
    assert resumen["ran"] is True and set(resumen["companies"]) == {esc["a"], esc["b"]}
    jobs = await filas(esc, "SELECT * FROM sap_inbound_sync_jobs WHERE company_id IN (:a, :b)",
                       a=esc["a"], b=esc["b"])
    assert jobs and all(j["trigger"] == "scheduled" and j["initiated_by_id"] is None for j in jobs)
    assert [x["plant_code"] for x in await registros(esc, "plant", empresa="b")] == ["2100"]

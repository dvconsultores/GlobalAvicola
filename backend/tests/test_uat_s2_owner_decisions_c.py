"""`GA-UAT-BREEDER-CRIA-S2` · `spec 020 §6` — semana derivada (`RR-30`) y alimento con tipo y fase (`RR-33`/`RR-34`).

`OD-S2-04`: la «Semana N» es la **edad productiva del lote** (`(fecha_evento − inicio_del_lote).days // 7 + 1`),
no la semana ISO del reloj, y la deriva el servidor: el cliente no la escribe. `OD-S2-07`: el consumo de
alimento nombra su tipo (dato del operador) y su fase se deriva de la fase vigente del lote.

Casos: `OD04-01..07`, `OD07-01..06`. Las fechas se expresan en **días de vida del lote** para no depender del
reloj; las pruebas puras de frontera usan fechas fijas porque no pasan por `BR-19` ni por el reloj.
"""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.operations.semana import semana_productiva
from tests.test_uat_s2_owner_decisions_a import (
    _corregir, _detalle, _evento_historico, _id_de_la_desconocida, _lista, _tipo_de_correccion,
)
from tests.time_reference import days_ago, iso_days_ago

FARM = 1
HOUSE = 1
DIAS_DEL_LOTE = 30          # el lote nace hace 30 días: todos los eventos caen dentro del período abierto


# ── Datos ─────────────────────────────────────────────────────────────────────

async def _lote_propio(client, headers, aves: int = 200) -> int:
    """Lote reproductor con inicio hace `DIAS_DEL_LOTE` días y aves recibidas ese día."""
    r = await client.post("/api/v1/lots", headers=headers, json={
        "farm_id": FARM, "house_id": HOUSE, "lot_code": f"OD4-{uuid.uuid4().hex[:8].upper()}",
        "bird_type": "breeder", "sex": "mixed", "start_date": iso_days_ago(DIAS_DEL_LOTE),
    })
    assert r.status_code == 201, r.text
    lote = r.json()["id"]
    rec = await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lote, "farm_id": FARM, "house_id": HOUSE, "event_type": "bird_reception",
        "event_date": iso_days_ago(DIAS_DEL_LOTE), "received_total": aves, "dead_on_arrival": 0,
        "rejected_on_arrival": 0, "bird_movements": [{"sex": "mixed", "quantity": aves}],
    })
    assert rec.status_code == 201, rec.text
    return lote


def _fecha(dia_de_vida: int) -> str:
    """Fecha del día `dia_de_vida` del lote (día 0 = inicio)."""
    return iso_days_ago(DIAS_DEL_LOTE - dia_de_vida)


async def _fases(client, headers, cuantas: int = 2) -> list[int]:
    """Ids de `cuantas` fases productivas distintas (se crean las que falten)."""
    ids = [f["id"] for f in await _lista(client, headers, "productive-phases")][:cuantas]
    while len(ids) < cuantas:
        r = await client.post("/api/v1/masters/productive-phases", headers=headers, json={
            "name": f"Fase OD {uuid.uuid4().hex[:6]}", "code": f"OD{uuid.uuid4().hex[:6].upper()}",
            "order": 90 + len(ids)})
        assert r.status_code == 201, r.text
        ids.append(r.json()["id"])
    return ids


async def _poner_fase(client, headers, lote: int, fase: int, dia_de_vida: int):
    return await client.post(f"/api/v1/lots/{lote}/phases", headers=headers, json={
        "lot_id": lote, "phase_id": fase, "start_date": _fecha(dia_de_vida)})


async def _tipo_de_alimento(client, headers) -> int:
    items = await _lista(client, headers, "feed-types")
    if items:
        return items[0]["id"]
    r = await client.post("/api/v1/masters/feed-types", headers=headers,
                          json={"name": f"Alimento OD {uuid.uuid4().hex[:6]}", "code": f"AL{uuid.uuid4().hex[:6].upper()}"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _pesaje(client, headers, lote: int, dia_de_vida: int, **extra):
    return await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lote, "event_type": "weight_recording", "event_date": _fecha(dia_de_vida),
        "bird_movements": [{"sex": "mixed", "quantity": 0, "avg_weight": 1500.0, **extra}]})


def _semana_de(detalle: dict) -> set:
    filas = detalle["bird_movements"] + detalle["feed_movements"]
    return {f["week_number"] for f in filas}


# ══════════════════════════════════════════════════════════════════════════════
#  OD04 · `RR-30` — la semana es derivada
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("dia,semana", [(0, 1), (6, 1), (7, 2), (13, 2), (14, 3), (20, 3), (21, 4)])
@pytest.mark.asyncio
async def test_od04_01_la_semana_sale_de_la_edad_del_lote(auth_headers, client, dia, semana):
    """`OD04-01`: semana 1 = días 0–6 de vida; el día 7 abre la semana 2."""
    lote = await _lote_propio(client, auth_headers)
    r = await _pesaje(client, auth_headers, lote, dia)
    assert r.status_code == 201, r.text
    assert _semana_de(await _detalle(client, auth_headers, r.json()["id"])) == {semana}


@pytest.mark.asyncio
async def test_od04_01b_los_cuatro_eventos_derivan_la_misma_semana(auth_headers, client):
    """`OD04-01`: pesaje, mortalidad, descarte y alimento comparten la función canónica (día 15 ⇒ semana 3)."""
    lote = await _lote_propio(client, auth_headers)
    fase = (await _fases(client, auth_headers, 1))[0]
    assert (await _poner_fase(client, auth_headers, lote, fase, 0)).status_code == 201
    tipo_alimento = await _tipo_de_alimento(client, auth_headers)
    mort = await _id_de_la_desconocida(client, auth_headers, "mortality-causes")
    desc = await _id_de_la_desconocida(client, auth_headers, "cull-causes")
    cuerpos = [
        {"event_type": "weight_recording", "bird_movements": [{"sex": "mixed", "quantity": 0, "avg_weight": 1500.0}]},
        {"event_type": "mortality_recording", "cause_id": mort, "bird_movements": [{"sex": "mixed", "quantity": 1}]},
        {"event_type": "cull_recording", "cull_cause_id": desc, "bird_movements": [{"sex": "mixed", "quantity": 1}]},
        {"event_type": "feed_registration", "feed_movements": [{"feed_type_id": tipo_alimento, "quantity_kg": 5.0}]},
    ]
    for cuerpo in cuerpos:
        r = await client.post("/api/v1/operations", headers=auth_headers,
                              json={"lot_id": lote, "event_date": _fecha(15), **cuerpo})
        assert r.status_code == 201, (cuerpo["event_type"], r.text)
        assert _semana_de(await _detalle(client, auth_headers, r.json()["id"])) == {3}, cuerpo["event_type"]


@pytest.mark.asyncio
async def test_od04_01c_la_semana_que_manda_el_cliente_se_ignora(auth_headers, client):
    """`OD04-01`: no se tapa la derivación escribiendo un número a mano."""
    lote = await _lote_propio(client, auth_headers)
    r = await _pesaje(client, auth_headers, lote, 15, week_number=99)
    assert r.status_code == 201, r.text
    assert _semana_de(await _detalle(client, auth_headers, r.json()["id"])) == {3}


@pytest.mark.asyncio
async def test_od04_02_cambiar_la_fecha_recalcula_la_semana(auth_headers, client):
    """`OD04-02`: por edición (`PUT`) y por corrección auditada la semana sigue a la fecha."""
    lote = await _lote_propio(client, auth_headers)
    alta = await _pesaje(client, auth_headers, lote, 6)
    assert alta.status_code == 201, alta.text
    event_id = alta.json()["id"]
    assert _semana_de(await _detalle(client, auth_headers, event_id)) == {1}

    put = await client.put(f"/api/v1/operations/{event_id}", headers=auth_headers,
                           json={"event_date": _fecha(7)})
    assert put.status_code == 200, put.text
    assert _semana_de(await _detalle(client, auth_headers, event_id)) == {2}

    tipo = await _tipo_de_correccion(client, auth_headers)
    cor = await _corregir(client, auth_headers, event_id, "event_date", _fecha(14), tipo=tipo)
    assert cor.status_code == 201, cor.text
    assert _semana_de(await _detalle(client, auth_headers, event_id)) == {3}


@pytest.mark.asyncio
async def test_od04_03_sin_fecha_base_no_se_inventa_la_semana(auth_headers, client, seeded_ids, test_database_url):
    """`OD04-03`: un lote sin fecha de inicio no admite eventos con semana derivada (`LOT_DATE_INCOMPLETE`)."""
    import app.masters.models  # noqa: F401
    from app.masters.models import BirdTypeEnum, Lot

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as sesion:
            lote = Lot(company_id=seeded_ids["company_id"], lot_code=f"OD4-SIN-{uuid.uuid4().hex[:6].upper()}",
                       bird_type=BirdTypeEnum.BREEDER, status="active", activation_type="normal", start_date=None)
            sesion.add(lote)
            await sesion.commit()
            lote_id = lote.id
    finally:
        await motor.dispose()

    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote_id, "event_type": "weight_recording", "event_date": iso_days_ago(3),
        "bird_movements": [{"sex": "mixed", "quantity": 0, "avg_weight": 1500.0}]})
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-30", r.json()
    assert "LOT_DATE_INCOMPLETE" in r.json()["detail"], r.json()


@pytest.mark.parametrize("inicio,evento,esperada", [
    (date(2025, 12, 29), date(2026, 1, 4), 1),      # cambio de año, día 6
    (date(2025, 12, 29), date(2026, 1, 5), 2),      # cambio de año, día 7
    (date(2025, 12, 28), date(2026, 1, 11), 3),     # domingo (ISO 52) → día 14
    (date(2026, 11, 25), date(2026, 12, 1), 1),     # cambia la semana ISO (48→49) y no la productiva
    (date(2026, 12, 31), date(2027, 1, 7), 2),      # ISO 53 → ISO 1, día 7
    (date(2026, 2, 28), date(2026, 3, 1), 1),       # fin de mes de febrero
])
def test_od04_04_cambio_de_anio_y_de_semana_iso_no_alteran_la_semana_productiva(inicio, evento, esperada):
    """`OD04-04` / `OD04-05`: función pura, fechas fijas, sin reloj: la semana es edad del lote, no ISO."""
    assert semana_productiva(inicio, evento) == esperada


def test_od04_05_sin_base_o_con_evento_anterior_la_funcion_no_inventa():
    """`OD04-03`: la función nunca devuelve una semana sin fecha base o con un evento anterior al inicio."""
    with pytest.raises(ValueError):
        semana_productiva(None, date(2026, 1, 1))
    with pytest.raises(ValueError):
        semana_productiva(date(2026, 1, 10), date(2026, 1, 9))


@pytest.mark.asyncio
async def test_od04_06_la_semana_deja_de_ser_corregible(auth_headers, client):
    """`OD04-06`: la semana no se corrige a mano; solo cambia con la fecha."""
    lote = await _lote_propio(client, auth_headers)
    alta = await _pesaje(client, auth_headers, lote, 15)
    assert alta.status_code == 201, alta.text
    event_id = alta.json()["id"]
    campos = await client.get(f"/api/v1/corrections/events/{event_id}/correctable-fields", headers=auth_headers)
    assert campos.status_code == 200, campos.text
    assert not [c for c in campos.json() if c["field_name"].endswith(".week_number")], campos.json()

    # El detalle no publica el id de la fila; el selector de corrección sí lo ofrece (`row_id`).
    filas = [c["row_id"] for c in campos.json()
             if c["row_id"] is not None and c["field_name"].startswith("bird_movements[")]
    assert filas, campos.json()
    fila = filas[0]
    tipo = await _tipo_de_correccion(client, auth_headers)
    r = await _corregir(client, auth_headers, event_id, f"bird_movements[{fila}].week_number", "9", tipo=tipo)
    assert r.status_code == 400, r.text
    assert _semana_de(await _detalle(client, auth_headers, event_id)) == {3}


@pytest.mark.asyncio
async def test_od04_07_el_historico_conserva_su_semana_y_se_lee(auth_headers, client, seeded_ids, test_database_url):
    """`OD04-07`: una fila anterior a la derivación se lee tal cual (sin *backfill*)."""
    from app.operations.models import BirdMovement, EventStatus, EventType

    event_id = await _evento_historico(
        test_database_url, company_id=seeded_ids["company_id"], lot_id=2, event_type=EventType.WEIGHT_RECORDING,
        event_date=days_ago(7), status=EventStatus.REGISTERED, version=1,
        registered_by_id=seeded_ids["user_admin_id"])
    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as sesion:
            sesion.add(BirdMovement(event_id=event_id, sex="mixed", quantity=0, avg_weight=1400.0, week_number=77))
            await sesion.commit()
    finally:
        await motor.dispose()
    assert _semana_de(await _detalle(client, auth_headers, event_id)) == {77}


# ══════════════════════════════════════════════════════════════════════════════
#  OD07 · `RR-33` / `RR-34` — el alimento nombra su tipo y su fase se deriva
# ══════════════════════════════════════════════════════════════════════════════

async def _alimento(client, headers, lote: int, dia_de_vida: int, **fila):
    return await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lote, "event_type": "feed_registration", "event_date": _fecha(dia_de_vida),
        "feed_movements": [{"quantity_kg": 5.0, **fila}]})


@pytest.mark.asyncio
async def test_od07_01_alimento_sin_tipo_es_400(auth_headers, client):
    """`OD07-01` · `RR-33`: cantidad sin tipo de alimento no es trazable."""
    lote = await _lote_propio(client, auth_headers)
    fase = (await _fases(client, auth_headers, 1))[0]
    assert (await _poner_fase(client, auth_headers, lote, fase, 0)).status_code == 201
    r = await _alimento(client, auth_headers, lote, 15)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Seleccione el tipo de alimento", r.json()
    assert r.json()["rule"] == "RR-33", r.json()


@pytest.mark.asyncio
async def test_od07_02_y_03_tipo_y_cantidad_validos_derivan_la_fase_del_lote(auth_headers, client):
    """`OD07-02` / `OD07-03`: el alta es 201 y la fase guardada es la vigente del lote, no un dato del cliente."""
    lote = await _lote_propio(client, auth_headers)
    fase = (await _fases(client, auth_headers, 1))[0]
    assert (await _poner_fase(client, auth_headers, lote, fase, 0)).status_code == 201
    tipo = await _tipo_de_alimento(client, auth_headers)
    r = await _alimento(client, auth_headers, lote, 15, feed_type_id=tipo, phase_id=999999)
    assert r.status_code == 201, r.text
    fila = (await _detalle(client, auth_headers, r.json()["id"]))["feed_movements"][0]
    assert fila["phase_id"] == fase and fila["week_number"] == 3, fila


@pytest.mark.asyncio
async def test_od07_04_si_la_fase_del_lote_cambia_el_evento_nuevo_usa_la_nueva(auth_headers, client):
    """`OD07-04`: antes de la transición rige la fase A; después, la B."""
    lote = await _lote_propio(client, auth_headers)
    fase_a, fase_b = await _fases(client, auth_headers, 2)
    assert (await _poner_fase(client, auth_headers, lote, fase_a, 0)).status_code == 201
    assert (await _poner_fase(client, auth_headers, lote, fase_b, 20)).status_code == 201
    tipo = await _tipo_de_alimento(client, auth_headers)

    antes = await _alimento(client, auth_headers, lote, 15, feed_type_id=tipo)
    despues = await _alimento(client, auth_headers, lote, 25, feed_type_id=tipo)
    assert antes.status_code == 201 and despues.status_code == 201, (antes.text, despues.text)
    assert (await _detalle(client, auth_headers, antes.json()["id"]))["feed_movements"][0]["phase_id"] == fase_a
    assert (await _detalle(client, auth_headers, despues.json()["id"]))["feed_movements"][0]["phase_id"] == fase_b

    # y la fecha manda también al editar: llevar el evento nuevo al período A cambia su fase
    put = await client.put(f"/api/v1/operations/{despues.json()['id']}", headers=auth_headers,
                           json={"event_date": _fecha(10)})
    assert put.status_code == 200, put.text
    assert (await _detalle(client, auth_headers, despues.json()["id"]))["feed_movements"][0]["phase_id"] == fase_a


@pytest.mark.asyncio
async def test_od07_05_sin_fase_vigente_no_se_inventa(auth_headers, client):
    """`OD07-05`: un lote sin fase vigente rechaza el alimento (`LOT_PHASE_INCOMPLETE`), no inventa una."""
    lote = await _lote_propio(client, auth_headers)
    tipo = await _tipo_de_alimento(client, auth_headers)
    r = await _alimento(client, auth_headers, lote, 15, feed_type_id=tipo)
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == "RR-34", r.json()
    assert "LOT_PHASE_INCOMPLETE" in r.json()["detail"], r.json()

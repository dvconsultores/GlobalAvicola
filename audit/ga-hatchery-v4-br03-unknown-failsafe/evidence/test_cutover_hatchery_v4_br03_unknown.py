"""SPEC 018 §10 · BR-03 UNKNOWN FAIL-SAFE — el saldo para cargar es exacto o no autoriza nada.

`UNKNOWN ≠ 0` y `UNKNOWN ≠ seguro de ignorar`: con un componente pre-carga UNKNOWN la suma conocida es
una cota superior, no un saldo. BR-03 deniega toda carga positiva (`CUTOVER_BALANCE_INCOMPLETE`) hasta que
la corrección gobernada de la apertura complete el dato; entonces el saldo vuelve a ser exacto.

Casos del mandato: BR03-U01..U07, más la guarda de retiro de entrada y V3 histórica.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import select

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import headers_aprobador, items_por_referencia, preparar  # noqa: E402
from tests.test_cutover_hatchery_v4_od02 import (  # noqa: E402
    _aplicar_batch, _errores, _fila, _filas, _preview, _reconciliacion, _saldos_br03,
)
from tests.time_reference import recent_event_date  # noqa: E402

INCOMPLETO = "CUTOVER_BALANCE_INCOMPLETE"
#: Caso del mandato con `dirty` como parámetro (None = UNKNOWN).
BASE = dict(eggs_received=10000, eggs_set=8500, eggs_non_incubable_oversized=200,
            eggs_non_incubable_dirty=200, eggs_non_incubable_broken=100, fertile_eggs_to_pit=200)


def _caso(ref: str, **cambios) -> list:
    return _fila(ref, **{**BASE, **cambios})


async def _cargar(client, headers, lot_id: int, cantidad: int):
    return await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lot_id, "event_type": "incubation_load", "event_date": recent_event_date(),
        "hatchery_params": [{"quantity_loaded": cantidad}],
    })


async def _corregir(client, headers, opening_id: int, campo: str, valor: int, motivo="Completar dato de la carga inicial"):
    return await client.post(f"/api/v1/opening-balances/{opening_id}/corrections", headers=headers,
                             json={"field": campo, "new_value": valor, "reason": motivo})


def _sin_tecnicismos(detalle: str) -> None:
    for prohibido in ("None", "null", "UNKNOWN", INCOMPLETO, "_status", "eggs_"):
        assert prohibido not in detalle, f"el mensaje expone '{prohibido}': {detalle}"


# ── BR03-U01 · un no incubable UNKNOWN deja el saldo UNKNOWN y bloquea la carga ──

@pytest.mark.asyncio
async def test_br03_u01_dirty_unknown_saldo_unknown_y_carga_denegada(auth_headers, http_client, seeded_ids):
    """AC-V4-30: preview, reconciliación y BR-03 comparten el UNKNOWN; 1 huevo ⇒ 400 funcional."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids),
                                    [_caso("BR03-U01", eggs_non_incubable_dirty=None)], 80)
    assert _filas(await _preview(http_client, auth_headers, batch_id))["BR03-U01"]["derived"]["eggs_available_to_set"] is None
    rec = (await _reconciliacion(http_client, auth_headers, batch_id))["BR03-U01"]
    assert rec["current"]["eggs_available_hatchery"] is None
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    assert (await _saldos_br03(lotes))["BR03-U01"] is None             # nunca 1000 (la cota superior)

    r = await _cargar(http_client, auth_headers, lotes["BR03-U01"], 1)
    assert r.status_code == 400, r.text
    assert r.json()["rule"] == INCOMPLETO
    assert "No se puede determinar el saldo disponible para cargar" in r.json()["detail"]
    _sin_tecnicismos(r.json()["detail"])


# ── BR03-U02 · corregir dirty = 700 ⇒ saldo 300 exacto ──────────────────────

@pytest.mark.asyncio
async def test_br03_u02_corregir_dirty_700_da_saldo_300(auth_headers, http_client, seeded_ids):
    """AC-V4-31: la corrección gobernada completa el dato; 300 entra y 1 más ya no (BR-03)."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids),
                                    [_caso("BR03-U02", eggs_non_incubable_dirty=None)], 81)
    rec = (await _reconciliacion(http_client, auth_headers, batch_id))["BR03-U02"]
    opening_id = rec["opening_id"]
    assert isinstance(opening_id, int)

    c = await _corregir(http_client, auth_headers, opening_id, "eggs_non_incubable_dirty", 700)
    assert c.status_code == 201, c.text
    correccion = c.json()
    assert (correccion["old_value"], correccion["new_value"], correccion["delta"]) == (None, "700", None)

    rec = (await _reconciliacion(http_client, auth_headers, batch_id))["BR03-U02"]
    assert rec["opening"]["hatchery"]["eggs_non_incubable_dirty"] == 700
    assert rec["opening"]["hatchery"]["eggs_non_incubable_dirty_status"] == "KNOWN"
    assert rec["current"]["eggs_available_hatchery"] == 300
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    assert (await _saldos_br03(lotes))["BR03-U02"] == 300

    assert (await _cargar(http_client, auth_headers, lotes["BR03-U02"], 300)).status_code == 201
    r = await _cargar(http_client, auth_headers, lotes["BR03-U02"], 1)
    assert r.status_code == 400 and r.json()["rule"] == "BR-03", r.text

    historial = await http_client.get(f"/api/v1/opening-balances/{opening_id}/corrections", headers=auth_headers)
    assert historial.status_code == 200
    assert [(i["field"], i["old_value"], i["new_value"]) for i in historial.json()["items"]] == \
        [("eggs_non_incubable_dirty", None, "700")]


# ── BR03-U03 · cero conocido no es UNKNOWN ──────────────────────────────────

@pytest.mark.asyncio
async def test_br03_u03_cero_conocido_calcula_y_autoriza(auth_headers, http_client, seeded_ids):
    """AC-V4-32: `dirty = 0` conocido ⇒ saldo 1000 y se cargan 1000 (directo o tras corregir el UNKNOWN a 0)."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        _caso("BR03-U03A", eggs_non_incubable_dirty=0),
        _caso("BR03-U03B", eggs_non_incubable_dirty=None),
    ], 82)
    rec = await _reconciliacion(http_client, auth_headers, batch_id)
    assert rec["BR03-U03A"]["current"]["eggs_available_hatchery"] == 1000
    assert (await _corregir(http_client, auth_headers, rec["BR03-U03B"]["opening_id"],
                            "eggs_non_incubable_dirty", 0)).status_code == 201
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    saldos = await _saldos_br03(lotes)
    assert saldos == {"BR03-U03A": 1000, "BR03-U03B": 1000}
    for ref in ("BR03-U03A", "BR03-U03B"):
        assert (await _cargar(http_client, auth_headers, lotes[ref], 1000)).status_code == 201
        r = await _cargar(http_client, auth_headers, lotes[ref], 1)
        assert r.status_code == 400 and r.json()["rule"] == "BR-03", r.text


# ── BR03-U04 · la suma conocida que ya excede se rechaza sin esperar al UNKNOWN ──

@pytest.mark.asyncio
async def test_br03_u04_suma_conocida_excedida_se_rechaza(auth_headers, http_client, seeded_ids):
    """AC-V4-33: en la carga (validación) y en la corrección (422) la cota conocida sí se aplica."""
    await preparar(seeded_ids)
    # Validación: `dirty` UNKNOWN y 9000 + 500 + 200 + 400 = 10100 > 10000 ⇒ fila rechazada.
    cuerpo, errores = await _errores(http_client, auth_headers, [
        _caso("BR03-U04A", eggs_set=9000, eggs_non_incubable_oversized=500, eggs_non_incubable_dirty=None,
              eggs_non_incubable_broken=200, fertile_eggs_to_pit=400),
    ], 83)
    assert errores == [(2, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH")]
    assert cuerpo["invalid_rows"] == 1

    # Corrección: completar `dirty` con 1001 dejaría 9000 + 1001 > 10000 ⇒ 422; con 1000 cuadra (saldo 0).
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids),
                                    [_caso("BR03-U04B", eggs_non_incubable_dirty=None)], 84)
    opening_id = (await _reconciliacion(http_client, auth_headers, batch_id))["BR03-U04B"]["opening_id"]
    r = await _corregir(http_client, auth_headers, opening_id, "eggs_non_incubable_dirty", 1001)
    assert r.status_code == 422, r.text
    assert (await _reconciliacion(http_client, auth_headers, batch_id))["BR03-U04B"]["current"]["eggs_available_hatchery"] is None
    assert (await _corregir(http_client, auth_headers, opening_id, "eggs_non_incubable_dirty", 1000)).status_code == 201
    assert (await _reconciliacion(http_client, auth_headers, batch_id))["BR03-U04B"]["current"]["eggs_available_hatchery"] == 0


# ── BR03-U05 / U06 · cualquier componente UNKNOWN bloquea, sin trato especial ──

@pytest.mark.asyncio
@pytest.mark.parametrize("campo,dias", [
    ("fertile_eggs_to_pit", 85),            # U05
    ("eggs_non_incubable_oversized", 86),   # U06
    ("eggs_non_incubable_dirty", 87),       # U06
    ("eggs_non_incubable_broken", 88),      # U06
])
async def test_br03_u05_u06_cualquier_componente_unknown_bloquea(auth_headers, http_client, seeded_ids, campo, dias):
    """AC-V4-34: UNKNOWN en la fosa o en cualquiera de los tres no incubables ⇒ misma denegación."""
    await preparar(seeded_ids)
    ref = f"BR03-U56-{dias}"
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids),
                                    [_caso(ref, **{campo: None})], dias)
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    assert (await _saldos_br03(lotes))[ref] is None
    r = await _cargar(http_client, auth_headers, lotes[ref], 1)
    assert r.status_code == 400 and r.json()["rule"] == INCOMPLETO, r.text


# ── BR03-U07 · todo conocido: 800 exacto ────────────────────────────────────

@pytest.mark.asyncio
async def test_br03_u07_todo_conocido_saldo_800(auth_headers, http_client, seeded_ids):
    """AC-V4-35: escenario ya certificado — 801 ⇒ 400 BR-03; 800 ⇒ 201."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [_caso("BR03-U07")], 89)
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    assert (await _saldos_br03(lotes))["BR03-U07"] == 800
    r = await _cargar(http_client, auth_headers, lotes["BR03-U07"], 801)
    assert r.status_code == 400 and r.json()["rule"] == "BR-03", r.text
    assert (await _cargar(http_client, auth_headers, lotes["BR03-U07"], 800)).status_code == 201


# ── retiro de entrada con saldo inicial UNKNOWN ─────────────────────────────

@pytest.mark.asyncio
async def test_br03_retiro_de_recepcion_con_saldo_unknown_se_deniega(auth_headers, http_client, seeded_ids):
    """AC-V4-36: anular/reasignar una recepción en incubadora exige demostrar saldo `≥ 0` ⇒ con UNKNOWN, 400."""
    await preparar(seeded_ids)
    from app.operations.models import EventType
    from app.operations.validators import BusinessRuleViolation, validate_retiro_de_entrada

    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids),
                                    [_caso("BR03-RET", fertile_eggs_to_pit=None)], 90)
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    evento = SimpleNamespace(lot_id=lotes["BR03-RET"], event_type=EventType.EGG_RECEPTION_HATCHERY)
    async with database.async_session() as s:
        with pytest.raises(BusinessRuleViolation) as error:
            await validate_retiro_de_entrada(s, evento, 1, "La anulación")
    assert error.value.rule_id == INCOMPLETO


# ── V3 histórica: su saldo no depende de componentes que no existían ────────

@pytest.mark.asyncio
async def test_br03_v3_historica_no_se_bloquea(auth_headers, http_client, seeded_ids):
    """V3: saldo `received − set` aunque los componentes V4 estén UNKNOWN (no formaban parte del contrato)."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids),
                                    [_caso("BR03-V3", eggs_non_incubable_dirty=None)], 91)
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    from app.cutover.models import CutoverBatch

    async with database.async_session() as s:
        batch = (await s.execute(select(CutoverBatch).where(CutoverBatch.id == batch_id))).scalar_one()
        batch.template_version = "v3"
        await s.commit()
    assert (await _saldos_br03(lotes))["BR03-V3"] == 10000 - 8500
    assert (await _reconciliacion(http_client, auth_headers, batch_id))["BR03-V3"]["current"]["eggs_available_hatchery"] == 1500
    opening_id = (await _reconciliacion(http_client, auth_headers, batch_id))["BR03-V3"]["opening_id"]
    r = await _corregir(http_client, auth_headers, opening_id, "eggs_non_incubable_dirty", 0)
    assert r.status_code == 422, r.text                     # la corrección de componentes es solo V4

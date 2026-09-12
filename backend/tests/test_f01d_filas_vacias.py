"""`R-189` · `F-01d` — filas vacías de alimento/incubadora y lectura tolerante del detalle.

Contrato del anexo `GA_F01D_SUBSANACION_ANNEX.md`:

* la UI nunca envía `[{}]` en `feed_movements`/`hatchery_params` (serializadores F-01d);
* un cliente que envíe una fila vacía recibe **422** y no se persiste ninguna fila;
* una fila válida (`quantity_kg > 0`) se conserva y el detalle la muestra;
* el detalle de eventos **históricos** con `quantity_kg = 0.0` vuelve a leerse (200): la lectura
  no impone las restricciones de escritura.

Reutiliza el escenario `AUTOLOTE-` (empresa con grandparent/breeder, operador, OC) de la suite R-153.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.test_r153_import_lot_auto import (  # noqa: F401
    _cuenta,
    _importacion,
    _post,
    _sql,
    _token,
    esc,
)

pytestmark = pytest.mark.asyncio


async def _ejecutar(esc, sql, **params):
    """Sentencia de escritura comprometida (el helper `_sql` es de solo lectura)."""
    motor = create_async_engine(esc["url"])
    try:
        async with motor.begin() as conn:
            await conn.execute(text(sql), params)
    finally:
        await motor.dispose()


async def test_f01d_01_escritura_feed_fila_vacia_422_sin_persistir(http_client, esc):
    r = await _post(http_client, esc, "operador", _importacion(esc, feed_movements=[{}]))
    assert r.status_code == 422, r.text
    filas = await _cuenta(
        esc,
        "SELECT count(*) FROM feed_movements fm JOIN operational_events e ON e.id = fm.event_id "
        "JOIN companies c ON c.id = e.company_id WHERE c.name LIKE :p",
        p="AUTOLOTE-%",
    )
    assert filas == 0, "una fila vacía no puede dejar rastro"


async def test_f01d_02_escritura_hatchery_fila_vacia_422(http_client, esc):
    r = await _post(http_client, esc, "operador", _importacion(esc, hatchery_params=[{}]))
    assert r.status_code == 422, r.text


async def test_f01d_03_fila_valida_conservada_y_visible(http_client, esc):
    r = await _post(http_client, esc, "operador", _importacion(esc, feed_movements=[{"quantity_kg": 5.0}]))
    assert r.status_code == 201, r.text
    eid = r.json()["id"]
    g = await http_client.get(f"/api/v1/operations/{eid}", headers=_token(esc["operador"], esc["a"]))
    assert g.status_code == 200, g.text
    assert [f["quantity_kg"] for f in g.json()["feed_movements"]] == [5.0]


async def test_f01d_04_lectura_tolerante_de_fila_historica(http_client, esc):
    """Una fila como las que dejaba la versión anterior (`{}` ⇒ `quantity_kg = 0.0`)."""
    r = await _post(http_client, esc, "operador", _importacion(esc))
    assert r.status_code == 201, r.text
    eid = r.json()["id"]
    await _ejecutar(esc, "INSERT INTO feed_movements (event_id, quantity_kg) VALUES (:e, 0.0)", e=eid)

    g = await http_client.get(f"/api/v1/operations/{eid}", headers=_token(esc["operador"], esc["a"]))
    assert g.status_code == 200, g.text  # antes del anexo: 500 (`gt=0` en lectura)
    assert [f["quantity_kg"] for f in g.json()["feed_movements"]] == [0.0]


async def test_f01d_05_detalle_canonico_sin_500(http_client, esc):
    """El síntoma de la nube: detalle 500 con listas canónicas `[]` en alimento e incubadora."""
    r = await _post(http_client, esc, "operador", _importacion(esc, feed_movements=[], hatchery_params=[]))
    assert r.status_code == 201, r.text
    g = await http_client.get(f"/api/v1/operations/{r.json()['id']}",
                              headers=_token(esc["operador"], esc["a"]))
    assert g.status_code == 200, g.text
    assert g.json()["feed_movements"] == []
    assert g.json()["hatchery_params"] == []

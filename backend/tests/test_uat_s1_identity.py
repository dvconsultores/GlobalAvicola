"""UAT `GA-UAT-BREEDER-CRIA-S1` — identidad de granja y nave en la API.

Guion de aceptación del capítulo S1: quien opera en campo debe poder reconocer
**dónde** ocurrió un evento sin traducir identificadores. El detalle del lote y el
del evento tienen que traer el nombre de la granja y el de la nave; los listados
tienen que poder filtrarse por el código de lote tal como se teclea (parcial y sin
distinguir mayúsculas) sin que un comodín de SQL devuelva el universo completo; y el
reporte del lote tiene que conservar el tipo de ave, la fecha de fin y el estado
canónico —no traducido— para que lo que ve campo y lo que ve gerencia sea lo mismo.

Trazabilidad: `spec 015 §6 (AC-S1-I01, I02, R02, B01)`.

Las fechas se derivan de `tests/time_reference.py`: nunca literales, porque `BR-19`
rechaza eventos con más de 90 días de antigüedad y una fecha fija caducaría sola.
"""

from __future__ import annotations

import pytest

from tests.time_reference import recent_event_date

# Lote sembrado por la suite: gallina reproductora con granja y nave asignadas.
LOTE_ID = 2

# Tipos de ave canónicos del dominio, para construir el filtro negativo.
OTROS_TIPOS_DE_AVE = ["grandparent", "breeder", "broiler", "hatchery"]

ESTADOS_CANONICOS = {"active", "closed", "cancelled"}


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _lote(client, headers):
    """Detalle del lote de pruebas tal como lo devuelve la API."""
    r = await client.get(f"/api/v1/lots/{LOTE_ID}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


async def _vacunacion(client, headers, lote):
    """Una vacunación reciente sobre el lote de pruebas, con su ubicación."""
    cuerpo = {
        "lot_id": LOTE_ID,
        "event_type": "vaccination",
        "event_date": recent_event_date(),
        "vaccine_id": 1,
        "vaccination_route": "water",
    }
    if lote.get("farm_id") is not None:
        cuerpo["farm_id"] = lote["farm_id"]
    if lote.get("house_id") is not None:
        cuerpo["house_id"] = lote["house_id"]

    r = await client.post("/api/v1/operations", headers=headers, json=cuerpo)
    assert r.status_code == 201, r.text
    return r.json()


def _ids(lista):
    return {x["id"] for x in lista}


# ── AC-S1-I01 · el detalle del lote se reconoce sin diccionario ──────────────

@pytest.mark.asyncio
async def test_detalle_de_lote_trae_nombres(auth_headers, client):
    """Un `farm_id` y un `house_id` sueltos obligan a campo a llevar su propia tabla."""
    lote = await _lote(client, auth_headers)

    if lote.get("farm_id"):
        assert lote.get("farm_name"), "el detalle del lote debe traer el nombre de la granja"
    if lote.get("house_id"):
        assert lote.get("house_name"), "el detalle del lote debe traer el nombre de la nave"


# ── AC-S1-I02 · el detalle del evento dice dónde pasó ────────────────────────

@pytest.mark.asyncio
async def test_detalle_de_evento_trae_codigo_granja_y_nave(auth_headers, client):
    lote = await _lote(client, auth_headers)
    evento = await _vacunacion(client, auth_headers, lote)

    r = await client.get(f"/api/v1/operations/{evento['id']}", headers=auth_headers)
    assert r.status_code == 200, r.text
    detalle = r.json()

    assert detalle["lot_code"] == lote["lot_code"]
    if lote.get("farm_id"):
        assert detalle.get("farm_name"), "el evento debe traer el nombre de la granja"
    if lote.get("house_id"):
        assert detalle.get("house_name"), "el evento debe traer el nombre de la nave"


# ── AC-S1-R02 · buscar por el código que se teclea ───────────────────────────

@pytest.mark.asyncio
async def test_filtro_por_codigo_de_lote_parcial_e_insensible(auth_headers, client):
    """Quien busca teclea un trozo del código, y no en mayúsculas."""
    lote = await _lote(client, auth_headers)
    evento = await _vacunacion(client, auth_headers, lote)

    codigo = lote["lot_code"]
    trozo = codigo[:max(3, len(codigo) // 2)].lower()

    r = await client.get("/api/v1/operations", headers=auth_headers,
                         params={"lot_code": trozo, "limit": 100})
    assert r.status_code == 200, r.text
    assert evento["id"] in _ids(r.json()), (
        f"el filtro parcial '{trozo}' debe encontrar el evento del lote '{codigo}'")
    assert int(r.headers["x-total-count"]) >= 1


@pytest.mark.asyncio
async def test_filtro_por_codigo_inexistente_devuelve_vacio(auth_headers, client):
    r = await client.get("/api/v1/operations", headers=auth_headers,
                         params={"lot_code": "ZZZ-NO-EXISTE", "limit": 100})
    assert r.status_code == 200, r.text
    assert r.json() == []
    assert r.headers["x-total-count"] == "0"


@pytest.mark.asyncio
async def test_comodin_porcentaje_no_devuelve_todo(auth_headers, client):
    """`%` es comodín de SQL: si llega al `LIKE` sin escapar, el filtro deja de filtrar."""
    r = await client.get("/api/v1/operations", headers=auth_headers,
                         params={"lot_code": "%", "limit": 100})
    assert r.status_code == 200, r.text
    assert r.json() == [], (
        "el '%' debe tratarse como carácter literal: ningún código de lote lo contiene, "
        f"pero el filtro devolvió {len(r.json())} eventos")


# ── AC-S1-B01 · el filtro por tipo de ave acota de verdad ────────────────────

@pytest.mark.asyncio
async def test_lotes_filtran_por_tipo_de_ave(auth_headers, client):
    lote = await _lote(client, auth_headers)
    tipo = lote.get("bird_type")
    if not tipo:
        pytest.skip("el lote de pruebas no tiene bird_type: el filtro no es evaluable")

    r = await client.get("/api/v1/lots", headers=auth_headers,
                         params={"bird_type": tipo, "limit": 100})
    assert r.status_code == 200, r.text
    assert LOTE_ID in _ids(r.json()), f"el filtro por su propio tipo '{tipo}' debe incluir el lote"

    otro = next(t for t in OTROS_TIPOS_DE_AVE if t != tipo)
    r_otro = await client.get("/api/v1/lots", headers=auth_headers,
                              params={"bird_type": otro, "limit": 100})
    assert r_otro.status_code == 200, r_otro.text
    assert LOTE_ID not in _ids(r_otro.json()), (
        f"un lote de tipo '{tipo}' no puede aparecer al filtrar por '{otro}'")

    r_invalido = await client.get("/api/v1/lots", headers=auth_headers,
                                  params={"bird_type": "zzz"})
    assert r_invalido.status_code == 400, (
        f"un tipo de ave fuera del dominio debe rechazarse, no ignorarse: {r_invalido.text}")


# ── Trazabilidad del reporte ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reporte_de_lote_trae_tipo_fin_granja_y_nave(auth_headers, client):
    """El reporte alimenta decisiones: tiene que hablar el idioma canónico, sin traducir."""
    lote = await _lote(client, auth_headers)

    r = await client.get(f"/api/v1/reports/lot/{LOTE_ID}", headers=auth_headers)
    assert r.status_code == 200, r.text
    reporte = r.json()["lot"]

    for clave in ("bird_type", "end_date", "farm_name", "house_name"):
        assert clave in reporte, f"el reporte del lote debe incluir '{clave}'"

    if lote.get("farm_id"):
        assert reporte["farm_name"], "el reporte debe traer el nombre de la granja"

    assert reporte["bird_type"] == lote.get("bird_type")
    assert reporte["status"] in ESTADOS_CANONICOS, (
        f"el estado debe ser el canónico, no una traducción: {reporte['status']!r}")

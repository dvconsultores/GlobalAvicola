"""`R-28` — determinismo temporal de la suite y cobertura de `BR-19`.

Dos cosas distintas se verifican aquí:

1. Que la suite no dependa del calendario real (`T-028-04`, `T-028-05`).
2. Que `BR-19` —el período cerrado a 90 días— quede cubierta en sus tres regiones
   (`T-028-01` … `T-028-03`), cobertura que la suite no tenía.

`BR-19` pertenece al dominio y no se toca: lo que se corrige es la dependencia de los
tests respecto del reloj.
"""

from __future__ import annotations

import pathlib
import re

import pytest

from tests.time_reference import (
    CLOSED_PERIOD_DAYS,
    at_open_period_boundary,
    beyond_open_period,
    inside_open_period,
    recent_event_date,
    reference_today,
)

# Un evento cualquiera que no dependa de catálogos ausentes en las semillas.
def _payload(event_date: str) -> dict:
    return {
        "lot_id": 2,
        "event_type": "feed_registration",
        "event_date": event_date,
        "feed_movements": [{"quantity_kg": 10.0}],
    }


# ── T-028-01 … 03 · BR-19 en sus tres regiones ────────────────────────────────

@pytest.mark.asyncio
async def test_t028_01_br19_antes_del_limite_se_acepta(auth_headers, client):
    """Día 89: dentro del período abierto, el evento debe registrarse."""
    r = await client.post("/api/v1/operations", headers=auth_headers,
                          json=_payload(inside_open_period()))
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_t028_02_br19_en_el_limite_exacto_se_acepta(auth_headers, client):
    """Día 90: `validate_period_open` compara con `> 90`, así que el límite entra.

    Si producción cambiara el umbral, este test y `CLOSED_PERIOD_DAYS` dejarían de
    coincidir y el fallo obligaría a actualizar la constante de forma consciente.
    """
    r = await client.post("/api/v1/operations", headers=auth_headers,
                          json=_payload(at_open_period_boundary()))
    assert r.status_code == 201, (
        f"El límite exacto de {CLOSED_PERIOD_DAYS} días debe aceptarse: {r.text}")


@pytest.mark.asyncio
async def test_t028_03a_br19_pasado_el_limite_no_persiste(auth_headers, http_client):
    """Día 91: la regla se aplica — el evento no llega a crearse."""
    antes = await http_client.get("/api/v1/operations?limit=200", headers=auth_headers)
    n_antes = len(antes.json())

    await http_client.post("/api/v1/operations", headers=auth_headers,
                           json=_payload(beyond_open_period()))

    despues = await http_client.get("/api/v1/operations?limit=200", headers=auth_headers)
    assert len(despues.json()) == n_antes, (
        "Un evento con fecha en período cerrado no debe persistirse")


@pytest.mark.asyncio
async def test_t028_03b_br19_pasado_el_limite_responde_400(auth_headers, http_client):
    """Día 91: la regla debe **comunicarse** como 400, no como 500.

    Hoy falla: `validate_period_open` se invoca fuera del `try/except` de
    `_apply_business_rules` y la violación escapa sin manejar. Es el defecto `R-26`,
    que se corrige en el Stage 2 de la Wave 2. El test se escribe ahora, con la
    aserción correcta, para que Stage 2 tenga un criterio objetivo que satisfacer.
    """
    r = await http_client.post("/api/v1/operations", headers=auth_headers,
                               json=_payload(beyond_open_period()))
    assert r.status_code == 400, (
        f"BR-19 debe responder 400, no {r.status_code} (R-26). Cuerpo: {r.text[:200]}")
    assert "período cerrado" in r.text or "BR-19" in r.text


# ── T-028-04 · sin fechas literales en el árbol de tests ──────────────────────

@pytest.mark.asyncio
async def test_t028_04_sin_fechas_literales_en_los_tests():
    """Ninguna fecha ISO literal en `tests/` ni en las semillas de prueba.

    Una fecha escrita a mano caduca sola por `BR-19`. Este test impide que vuelvan a
    entrar.
    """
    raiz = pathlib.Path(__file__).resolve().parent.parent
    patron = re.compile(r"\b20\d\d-[01]\d-[0-3]\d\b")
    objetivos = list((raiz / "tests").glob("*.py")) + [raiz / "seeds" / "test_seeds.py"]

    infractores = []
    for fichero in objetivos:
        if fichero.name in {"time_reference.py", "test_time_determinism.py"}:
            continue  # definen y verifican la política; documentan formatos
        for numero, linea in enumerate(fichero.read_text(encoding="utf-8").splitlines(), 1):
            if patron.search(linea):
                infractores.append(f"{fichero.relative_to(raiz)}:{numero}: {linea.strip()}")

    assert not infractores, (
        "Fechas literales encontradas; use `tests.time_reference`:\n  "
        + "\n  ".join(infractores))


# ── T-028-05 · el resultado no depende de la fecha de referencia ──────────────

@pytest.mark.asyncio
async def test_t028_05_las_fechas_derivan_de_la_referencia():
    """Todas las fechas con nombre se mueven con la referencia y conservan su orden."""
    from datetime import date as _d

    hoy = reference_today()
    reciente = _d.fromisoformat(recent_event_date())
    dentro = _d.fromisoformat(inside_open_period())
    limite = _d.fromisoformat(at_open_period_boundary())
    fuera = _d.fromisoformat(beyond_open_period())

    assert fuera < limite < dentro < reciente < hoy
    assert (hoy - limite).days == CLOSED_PERIOD_DAYS
    assert (hoy - fuera).days == CLOSED_PERIOD_DAYS + 1


# ── T-028-06 · la simulación del calendario funciona de verdad ────────────────

@pytest.mark.asyncio
async def test_t028_06_la_simulacion_alcanza_a_la_aplicacion():
    """El reloj simulado debe verlo también la aplicación, no solo los tests.

    Si la simulación solo moviera el lado del test, la comparación de `BR-19` seguiría
    haciéndose contra el día real y la prueba de que la suite ya no caduca no valdría
    nada. Aquí se comprueba que `datetime.date.today()` —lo que `validate_period_open`
    resuelve en el momento de la llamada— responde al calendario simulado.
    """
    import datetime

    from tests.simulated_clock import simulating

    antes = datetime.date.today()
    futuro = datetime.date(antes.year + 3, 1, 15)

    with simulating(futuro):
        assert datetime.date.today() == futuro, (
            "La aplicación seguiría midiendo contra el día real")
        assert reference_today() == futuro

    assert datetime.date.today() == antes, (
        "El bloque debe restaurar el reloj anterior, no el real: si hay una simulación "
        "externa activa, restaurar el real contaminaría los tests siguientes")


# ── R-30 · BR-19 tampoco admite el futuro ─────────────────────────────────────

@pytest.mark.asyncio
async def test_r30_una_fecha_futura_se_rechaza(auth_headers, client):
    """`days_ago` negativo pasaba la comparación `> 90`: se admitía el futuro.

    Un evento operativo que aún no ha ocurrido no puede registrarse.
    """
    from tests.time_reference import iso_days_ago

    r = await client.post("/api/v1/operations", headers=auth_headers,
                          json=_payload(iso_days_ago(-10)))
    assert r.status_code == 400, f"Una fecha futura debe rechazarse: {r.status_code}"
    assert "futura" in r.text.lower()
    assert r.json().get("rule") == "BR-19"


@pytest.mark.asyncio
async def test_r30_un_dia_de_holgura_por_zona_horaria(auth_headers, client):
    """El servidor mide en su zona: un operador al este puede vivir ya el día siguiente."""
    from tests.time_reference import iso_days_ago

    r = await client.post("/api/v1/operations", headers=auth_headers,
                          json=_payload(iso_days_ago(-1)))
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_r26_el_error_de_regla_cita_la_regla(auth_headers, http_client):
    """`R-26`: contrato único de error — `400`, mensaje y `rule`."""
    r = await http_client.post("/api/v1/operations", headers=auth_headers,
                               json=_payload(beyond_open_period()))
    assert r.status_code == 400
    cuerpo = r.json()
    assert isinstance(cuerpo["detail"], str), "`detail` debe seguir siendo texto"
    assert cuerpo["rule"] == "BR-19", "La respuesta debe identificar la regla"

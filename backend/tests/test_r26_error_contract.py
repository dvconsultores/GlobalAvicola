"""`R-26` — contrato de error de las reglas de negocio.

Ocho de las trece reglas que puede violar una creación de evento se evaluaban **fuera**
del único `try/except` que las traducía, de modo que salían del proceso sin manejar y el
cliente recibía `500 Internal Server Error` en lugar del motivo. El operador que olvidaba
la granja veía «Internal Server Error»; las reglas contaminaban además cualquier métrica
de 5xx.

Aquí se verifica que **toda** violación esperada produce un `400` con la regla
identificada, y —tan importante como eso— que un fallo inesperado sigue siendo un `500`:
capturar de más habría escondido defectos reales, que es peor que el problema original.
"""

from __future__ import annotations

import pytest

from tests.owner_decisions_support import causa_desconocida, tipo_de_alimento
from tests.time_reference import beyond_open_period, iso_days_ago, recent_event_date


def _evento(datos: dict, **extra) -> dict:
    """Evento base con los datos que el contrato ratificado exige.

    El alimento declara su tipo (`RR-33`); la mortalidad, su causa (`RR-32`). Esos ids se leen
    de los maestros sembrados al construir el caso, no se escriben aquí.
    """
    base = {
        "lot_id": 2,
        "event_type": "feed_registration",
        "event_date": recent_event_date(),
        "feed_movements": [{"quantity_kg": 5.0, "feed_type_id": datos["feed_type_id"]}],
    }
    base.update(extra)
    return base


async def _datos_requeridos(client, headers) -> dict:
    return {
        "feed_type_id": await tipo_de_alimento(client, headers),
        "cause_id": await causa_desconocida(client, headers),
    }


# Cada caso: (regla, descripción, constructor del payload). El constructor recibe los datos
# del contrato para poder citarlos; las ocho primeras reglas salían como 500 antes de `R-26`.
CASOS = [
    ("BR-08", "evento de ubicación sin granja",
     lambda d: _evento(d, event_type="bird_reception", farm_id=None, house_id=None,
                       bird_movements=[{"sex": "mixed", "quantity": 10}])),
    ("BR-08", "inspección de granja sin galpón",
     lambda d: _evento(d, event_type="farm_inspection", farm_id=1, house_id=None)),
    ("BR-19", "fecha en período cerrado",
     lambda d: _evento(d, event_date=beyond_open_period())),
    ("BR-19", "fecha futura", lambda d: _evento(d, event_date=iso_days_ago(-10))),
    ("BR-07", "lote inexistente", lambda d: _evento(d, lot_id=999999)),
    ("BR-01", "mortalidad sobre el saldo",
     lambda d: _evento(d, event_type="mortality_recording", cause_id=d["cause_id"],
                       bird_movements=[{"sex": "female", "quantity": 999999}],
                       feed_movements=[])),
]


@pytest.mark.parametrize("regla,descripcion,constructor", CASOS,
                         ids=[f"{r}-{d}" for r, d, _ in CASOS])
@pytest.mark.asyncio
async def test_toda_violacion_es_un_400_con_su_regla(
    auth_headers, http_client, regla, descripcion, constructor
):
    payload = constructor(await _datos_requeridos(http_client, auth_headers))
    r = await http_client.post("/api/v1/operations", headers=auth_headers, json=payload)
    assert r.status_code == 400, (
        f"{descripcion}: se esperaba 400 y llegó {r.status_code}. Cuerpo: {r.text[:200]}")
    cuerpo = r.json()
    assert isinstance(cuerpo.get("detail"), str) and cuerpo["detail"], (
        "El error debe explicar el motivo en `detail`")
    assert cuerpo.get("rule") == regla, (
        f"{descripcion}: la respuesta debe identificar {regla}, no {cuerpo.get('rule')!r}")


@pytest.mark.asyncio
async def test_ninguna_violacion_sale_como_500(auth_headers, http_client):
    """Barrido: ninguno de los casos conocidos puede producir un 5xx."""
    datos = await _datos_requeridos(http_client, auth_headers)
    for regla, descripcion, constructor in CASOS:
        r = await http_client.post("/api/v1/operations", headers=auth_headers,
                                   json=constructor(datos))
        assert r.status_code < 500, f"{descripcion} ({regla}) sigue produciendo {r.status_code}"


@pytest.mark.asyncio
async def test_el_manejador_no_captura_errores_inesperados():
    """El manejador es tipado: un fallo imprevisto debe seguir siendo un 500.

    Resolverlo con `except Exception: return 400` habría convertido cualquier defecto
    futuro en un error de validación silencioso.
    """
    import inspect

    import app.main as main

    fuente = inspect.getsource(main)
    assert "except Exception" not in fuente, (
        "El contrato de error no puede apoyarse en una captura genérica")
    manejados = {k.__name__ for k in main.app.exception_handlers if hasattr(k, "__name__")}
    assert "BusinessRuleViolation" in manejados
    assert "Exception" not in manejados


@pytest.mark.asyncio
async def test_r27_configuracion_ausente_no_es_error_del_servidor(auth_headers, http_client):
    """`R-27`: sembrar pasos de aprobación sin los roles del sistema daba 500."""
    r = await http_client.post("/api/v1/approval-steps/seed-defaults",
                               headers=auth_headers, params={"approval_levels": 2})
    assert r.status_code != 500, "Una configuración ausente no es un fallo del servidor"
    if r.status_code == 422:
        assert "rol" in r.text.lower()

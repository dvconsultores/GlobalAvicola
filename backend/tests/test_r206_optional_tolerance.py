"""`R-206` · RED/control — tolerancia de `''` en los **opcionales** de `PlanDeImportacion`.

El asistente normaliza (C-02 = A, defensa en profundidad): un campo opcional con cadena
vacía se comporta como ausente (`None`) — nunca «Input should be a valid date». Los
requeridos no se relajan (control).

RED esperado en HEAD: los vacíos en opcionales lanzan `ValidationError`.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.operations.schemas import PlanDeImportacion
from tests.time_reference import iso_days_ago

BASE: dict = {
    "origin_country": "Francia",
    "purchased_total": 110,
    "shipped_total": 105,
    "received_total": 100,
    "transit_mortality": 5,
    "departure_date": iso_days_ago(40),
    "arrival_date": iso_days_ago(33),
}


@pytest.mark.parametrize("campo", [
    "quarantine_end_date",
    "reception_condition",
    "initial_health_inspection",
    "quarantine_days",
])
def test_r206_01_cadena_vacia_en_opcionales_se_tolera(campo):
    try:
        plan = PlanDeImportacion(**BASE, **{campo: ""})
    except ValidationError as exc:  # pragma: no cover - RED en HEAD
        pytest.fail(f"'{campo}' con '' debe tolerarse como ausente: {exc}")
    assert getattr(plan, campo) is None


def test_r206_02_control_fecha_valida_pasa():
    plan = PlanDeImportacion(**BASE, quarantine_end_date=iso_days_ago(-10))
    assert plan.quarantine_end_date is not None


def test_r206_03_control_requerido_no_se_relaja():
    with pytest.raises(ValidationError):
        PlanDeImportacion(**{**BASE, "origin_country": ""})

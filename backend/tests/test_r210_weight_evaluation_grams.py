"""`R-210` · control (verde en HEAD) — la evaluación de peso opera en **gramos**.

La curva genética, la evaluación y las alertas están en gramos (captura canónica del
asistente). Este control fija la semántica de `evaluar` con pesos de orden real (~2150 g)
y los límites **inclusivos**: el margen lo deciden `min_weight`/`max_weight` de la tabla,
sin tolerancias inventadas.
"""
from __future__ import annotations

from types import SimpleNamespace

from app.operations.weight_curve import WeightStatus, evaluar

#: Curva sintética en gramos (dos puntos, interpolación entre ambos).
PUNTOS = [
    SimpleNamespace(age_days=7, min_weight=1800.0, target_weight=2100.0, max_weight=2400.0),
    SimpleNamespace(age_days=14, min_weight=2600.0, target_weight=3000.0, max_weight=3400.0),
]


def test_r210_01_peso_en_grama_dentro_de_banda():
    ev = evaluar(PUNTOS, 10, 2150.0)
    assert ev.status == WeightStatus.WITHIN_STANDARD
    assert ev.rango is not None and ev.rango.min_weight <= 2150.0 <= ev.rango.max_weight


def test_r210_02_bordes_inclusivos():
    ev_min = evaluar(PUNTOS, 7, 1800.0)
    ev_max = evaluar(PUNTOS, 7, 2400.0)
    assert ev_min.status == WeightStatus.WITHIN_STANDARD
    assert ev_max.status == WeightStatus.WITHIN_STANDARD


def test_r210_03_fuera_de_banda_alerta():
    assert evaluar(PUNTOS, 10, 1500.0).status == WeightStatus.BELOW_STANDARD
    assert evaluar(PUNTOS, 10, 4000.0).status == WeightStatus.ABOVE_STANDARD


def test_r210_04_sin_peso_es_no_reference():
    assert evaluar(PUNTOS, 10, None).status == WeightStatus.NO_REFERENCE

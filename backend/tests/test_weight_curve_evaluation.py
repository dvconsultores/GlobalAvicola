"""Motor de evaluación de peso — `GA-REM-037`, `AC11`…`AC19`.

Curvas ficticias y deterministas: son **fixtures**, no datos de negocio. Los pesos reales de
Cobb, Ross o Hubbard los carga el administrador y no se inventan aquí.

    día 10  ·  mín  90  ·  objetivo 100  ·  máx 110
    día 20  ·  mín 180  ·  objetivo 200  ·  máx 220

Elegida para que la interpolación en el día 15 dé números exactos y comprobables a mano:
mínimo 135, objetivo 150, máximo 165.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest

from app.operations.weight_curve import WeightStatus, evaluar, rango_esperado


@dataclass(frozen=True)
class Punto:
    age_days: int
    min_weight: float
    max_weight: float
    target_weight: Optional[float] = None


CURVA = [
    Punto(age_days=10, min_weight=90.0, max_weight=110.0, target_weight=100.0),
    Punto(age_days=20, min_weight=180.0, max_weight=220.0, target_weight=200.0),
]


# ── AC11 · el punto exacto ────────────────────────────────────────────────────

def test_t_037_01_el_dia_exacto_usa_su_punto():
    """`AC11` · con un punto para esa edad no se interpola."""
    r = rango_esperado(CURVA, 10)
    assert r is not None
    assert (r.min_weight, r.target_weight, r.max_weight) == (90.0, 100.0, 110.0)
    assert r.interpolado is False


# ── AC12 · la interpolación ───────────────────────────────────────────────────

def test_t_037_02_el_dia_intermedio_se_interpola_linealmente():
    """`AC12` · día 15, a mitad de camino entre el 10 y el 20.

    Los tres valores se interpolan **por separado**: describen curvas distintas y mezclarlos
    daría un rango que no está en ninguna tabla.
    """
    r = rango_esperado(CURVA, 15)
    assert r is not None
    assert r.min_weight == pytest.approx(135.0), r
    assert r.target_weight == pytest.approx(150.0), r
    assert r.max_weight == pytest.approx(165.0), r
    assert r.interpolado is True


def test_t_037_03_la_interpolacion_no_es_el_punto_inferior():
    """`AC12` · si devolviera el punto anterior, el día 15 daría 90 en vez de 135."""
    assert rango_esperado(CURVA, 15).min_weight != CURVA[0].min_weight
    assert rango_esperado(CURVA, 12).min_weight == pytest.approx(108.0)


# ── AC13 · AC14 · AC15 · AC16 · la clasificación y sus bordes ─────────────────

@pytest.mark.parametrize("peso,esperado", [
    (85.0, WeightStatus.BELOW_STANDARD),    # `AC13`
    (90.0, WeightStatus.WITHIN_STANDARD),   # `AC16` · el mínimo, inclusive
    (100.0, WeightStatus.WITHIN_STANDARD),  # `AC14`
    (110.0, WeightStatus.WITHIN_STANDARD),  # `AC16` · el máximo, inclusive
    (120.0, WeightStatus.ABOVE_STANDARD),   # `AC15`
])
def test_t_037_04_clasificacion_y_bordes(peso, esperado):
    """`AC13`…`AC16`.

    Los dos casos de borde impiden un `<=` mal puesto: con `peso <= min` como criterio de
    «por debajo», el peso de 90 saldría fuera de norma sin estarlo.
    """
    assert evaluar(CURVA, 10, peso).status is esperado


# ── AC17 · sin tolerancia global ──────────────────────────────────────────────

def test_t_037_05_el_rango_sale_de_la_tabla_y_de_ningun_otro_sitio():
    """`AC17` · 89 está a poco más del 1 % del mínimo y aun así queda fuera.

    Si el motor aplicara un margen del 5 % —o de cualquier otro valor no documentado—, este
    peso saldría dentro de norma.
    """
    assert evaluar(CURVA, 10, 89.0).status is WeightStatus.BELOW_STANDARD
    assert evaluar(CURVA, 10, 111.0).status is WeightStatus.ABOVE_STANDARD


# ── AC18 · fuera del rango de la tabla ────────────────────────────────────────

@pytest.mark.parametrize("edad", [0, 9, 21, 100])
def test_t_037_06_fuera_del_rango_no_se_extrapola(edad):
    """`AC18` · prolongar la recta más allá de los datos sería inventar la curva."""
    assert rango_esperado(CURVA, edad) is None
    assert evaluar(CURVA, edad, 150.0).status is WeightStatus.NO_REFERENCE


def test_t_037_07_sin_referencia_no_es_dentro_de_norma():
    """`AC18`/`AC19` · no tener norma no es estar dentro de norma.

    Confundirlos produciría un «todo correcto» sin fundamento, que es peor que no evaluar.
    """
    for caso in (evaluar([], 10, 100.0), evaluar(CURVA, 50, 100.0), evaluar(CURVA, 10, None)):
        assert caso.status is WeightStatus.NO_REFERENCE
        assert caso.status is not WeightStatus.WITHIN_STANDARD
        assert caso.fuera_de_norma is False, "tampoco se emite alerta sin base"

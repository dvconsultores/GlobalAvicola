"""Evaluación del peso contra la curva estándar de la línea genética.

`GA-REM-037` / `GA-REQ-037` / `spec.md §4.5` — «alertas por desviaciones (peso fuera de curva
estándar)». `OD-06` fijó de dónde sale esa curva: una tabla por línea genética, versionada, que
el administrador carga.

**Una sola función decide**, y vive en el backend. El frontend puede mostrar el resultado, no
calcularlo: duplicar la interpolación en dos lenguajes es garantizar que diverjan.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence


class WeightStatus(str, Enum):
    """Resultado de comparar un peso real con el rango esperado a su edad."""

    BELOW_STANDARD = "below_standard"
    WITHIN_STANDARD = "within_standard"
    ABOVE_STANDARD = "above_standard"
    #: Sin línea genética, sin curva asignada, o con una edad fuera del rango de la tabla.
    #: **Nunca** se degrada a `WITHIN_STANDARD`: no tener norma contra la que comparar no es
    #: estar dentro de norma, y confundirlos produciría un «todo correcto» sin fundamento.
    NO_REFERENCE = "no_reference"


@dataclass(frozen=True)
class RangoEsperado:
    """El rango a una edad concreta, ya interpolado si hizo falta."""

    age_days: int
    min_weight: float
    max_weight: float
    target_weight: Optional[float]
    interpolado: bool


@dataclass(frozen=True)
class Evaluacion:
    status: WeightStatus
    rango: Optional[RangoEsperado]
    peso: Optional[float]

    @property
    def fuera_de_norma(self) -> bool:
        return self.status in (WeightStatus.BELOW_STANDARD, WeightStatus.ABOVE_STANDARD)


def _interpolar(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
    """Valor de `y` en `x`, sobre la recta que une dos puntos vecinos."""
    if x2 == x1:
        return y1
    return y1 + (x - x1) / (x2 - x1) * (y2 - y1)


def rango_esperado(puntos: Sequence, age_days: int) -> Optional[RangoEsperado]:
    """Rango esperado a `age_days`, o `None` si la tabla no lo cubre.

    Con un punto exacto para esa edad se usa **ese punto**: no se interpola sin necesidad.
    Entre dos puntos se interpola **linealmente** cada valor por separado — mínimo, máximo y
    objetivo—, porque los tres describen curvas distintas y mezclarlos daría un rango que no
    está en ninguna tabla.

    Fuera del rango de edades **no se extrapola**. Ninguna fuente lo autoriza, y prolongar la
    recta más allá de los datos sería inventar la curva donde no la hay: se devuelve `None`,
    que el llamante traduce a `NO_REFERENCE`.
    """
    if not puntos:
        return None

    ordenados = sorted(puntos, key=lambda p: p.age_days)

    for p in ordenados:
        if p.age_days == age_days:
            return RangoEsperado(
                age_days=age_days, min_weight=p.min_weight, max_weight=p.max_weight,
                target_weight=p.target_weight, interpolado=False,
            )

    if age_days < ordenados[0].age_days or age_days > ordenados[-1].age_days:
        return None

    anterior = max((p for p in ordenados if p.age_days < age_days), key=lambda p: p.age_days)
    siguiente = min((p for p in ordenados if p.age_days > age_days), key=lambda p: p.age_days)

    objetivo = None
    if anterior.target_weight is not None and siguiente.target_weight is not None:
        objetivo = _interpolar(age_days, anterior.age_days, anterior.target_weight,
                               siguiente.age_days, siguiente.target_weight)

    return RangoEsperado(
        age_days=age_days,
        min_weight=_interpolar(age_days, anterior.age_days, anterior.min_weight,
                               siguiente.age_days, siguiente.min_weight),
        max_weight=_interpolar(age_days, anterior.age_days, anterior.max_weight,
                               siguiente.age_days, siguiente.max_weight),
        target_weight=objetivo,
        interpolado=True,
    )


def evaluar(puntos: Sequence, age_days: int, peso: Optional[float]) -> Evaluacion:
    """Clasifica un peso real contra la curva.

    Los límites son **inclusivos**: un peso exactamente igual al mínimo —o al máximo— está
    dentro de norma. La alerta la deciden `min_weight` y `max_weight`; `target_weight` es
    referencia y no interviene, de modo que no se introduce ninguna tolerancia porcentual que
    la tabla no traiga.
    """
    if peso is None:
        return Evaluacion(WeightStatus.NO_REFERENCE, None, peso)

    rango = rango_esperado(puntos, age_days)
    if rango is None:
        return Evaluacion(WeightStatus.NO_REFERENCE, None, peso)

    if peso < rango.min_weight:
        return Evaluacion(WeightStatus.BELOW_STANDARD, rango, peso)
    if peso > rango.max_weight:
        return Evaluacion(WeightStatus.ABOVE_STANDARD, rango, peso)
    return Evaluacion(WeightStatus.WITHIN_STANDARD, rango, peso)

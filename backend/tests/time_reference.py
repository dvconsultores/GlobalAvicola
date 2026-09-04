"""Reloj de referencia de la suite — `GA-REM-015` addendum `R-28`.

La suite no debe depender del calendario real. `BR-19` (`validate_period_open`,
`app/operations/validators.py:332-347`) rechaza los eventos con más de 90 días de
antigüedad, de modo que una fecha literal escrita hoy caduca sola dentro de tres meses.

Todas las fechas de los tests se derivan de `reference_today()`. Los tests expresan la
regla —«dentro del período abierto», «un día pasado el límite»— y no una fecha histórica.

La referencia es siempre `date.today()`. **No se expone un override que solo afecte a
los tests**: `BR-19` se evalúa contra el reloj real del proceso, de modo que desplazar la
referencia sin desplazar también el reloj de producción produciría ejecuciones engañosas.

Para demostrar que la suite es inmune al avance del calendario existe
`GA_TEST_SIMULATED_TODAY`, que adelanta el reloj **de todo el proceso** —aplicación
incluida— desde `tests/simulated_clock.py`. Esa es la simulación honesta: si el resultado
no cambia al situarse un año en el futuro, el problema del calendario está resuelto.
"""

from __future__ import annotations

import datetime as _dt

# ── Umbral del período abierto ────────────────────────────────────────────────
# Debe coincidir con el literal de `validate_period_open`. Si producción lo cambia,
# `T-028-02` y `T-028-03` fallan y obligan a actualizar esta constante de forma
# consciente. No se importa desde `app/` a propósito: el test no debe heredar el
# mismo número que pretende verificar.
CLOSED_PERIOD_DAYS = 90


def reference_today() -> _dt.date:
    """Fecha de referencia de la suite: siempre el día en curso del proceso.

    Se accede a través de esta función y no de `date.today()` directamente para que
    exista un único punto por el que pasa toda la suite.
    """
    return _dt.date.today()


def days_ago(n: int) -> _dt.date:
    """Fecha `n` días antes de la referencia."""
    return reference_today() - _dt.timedelta(days=n)


def iso_days_ago(n: int) -> str:
    """Igual que `days_ago`, en el formato que aceptan los endpoints."""
    return days_ago(n).isoformat()


# ── Fechas con nombre, por intención ──────────────────────────────────────────

def recent_event_date() -> str:
    """Fecha de un evento operativo reciente: holgadamente dentro del período abierto.

    Siete días atrás: lo bastante en el pasado para ser plausible como registro de
    campo, y lo bastante lejos del límite de 90 días para que ningún desfase de zona
    horaria la acerque a la frontera.
    """
    return iso_days_ago(7)


def earlier_event_date() -> str:
    """Un evento anterior al de `recent_event_date`, útil cuando el orden importa."""
    return iso_days_ago(14)


def inside_open_period() -> str:
    """Último día que `BR-19` debe aceptar sin discusión (límite − 1)."""
    return iso_days_ago(CLOSED_PERIOD_DAYS - 1)


def at_open_period_boundary() -> str:
    """El límite exacto. `BR-19` compara con `> 90`, así que debe aceptarse."""
    return iso_days_ago(CLOSED_PERIOD_DAYS)


def beyond_open_period() -> str:
    """Primer día que `BR-19` debe rechazar (límite + 1)."""
    return iso_days_ago(CLOSED_PERIOD_DAYS + 1)


def lot_start_date() -> _dt.datetime:
    """Inicio del lote sembrado: anterior a cualquier fecha que la suite genere.

    `BR-06` exige que el evento no preceda a la activación del lote. Se sitúa un año
    antes del límite del período abierto para que ninguna fecha de test lo viole.
    """
    return _dt.datetime.combine(days_ago(CLOSED_PERIOD_DAYS + 365), _dt.time.min)

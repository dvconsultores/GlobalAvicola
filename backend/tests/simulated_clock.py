"""Simulación del avance del calendario — `R-28` / `T-028-05`.

`BR-19` cierra los períodos a 90 días contra `date.today()`. Demostrar que la suite ya no
caduca exige *adelantar el calendario*, no solo desplazar las fechas que los tests
escriben: si únicamente se moviera el lado del test, la aplicación seguiría midiendo
contra el día real y la comprobación no probaría nada.

Con `GA_TEST_SIMULATED_TODAY=YYYY-MM-DD` se sustituye `datetime.date` en todo el proceso
por una subclase cuyo `today()` devuelve esa fecha. La aplicación —que hace
`from datetime import date` dentro de `validate_period_open`— la resuelve en el momento de
la llamada y ve el mismo calendario que los tests.

Es una utilidad exclusiva de pruebas. No se importa desde `app/` y no altera nada cuando
la variable no está definida.
"""

from __future__ import annotations

import contextlib
import datetime as _datetime
import os

SIMULATED_TODAY_ENV = "GA_TEST_SIMULATED_TODAY"

_real_date = _datetime.date


def _build_frozen_date(simulated: _datetime.date):
    class _FrozenDate(_real_date):
        @classmethod
        def today(cls):  # noqa: D102 - reemplaza a date.today
            return cls(simulated.year, simulated.month, simulated.day)

    return _FrozenDate


def install() -> _datetime.date | None:
    """Adelanta el reloj del proceso si la variable está definida.

    Devuelve la fecha simulada, o `None` si no se ha pedido simulación.
    """
    raw = os.environ.get(SIMULATED_TODAY_ENV, "").strip()
    if not raw:
        return None
    return _set_clock(_real_date.fromisoformat(raw))


def _set_clock(simulated: _datetime.date) -> _datetime.date:
    _datetime.date = _build_frozen_date(simulated)
    return simulated


@contextlib.contextmanager
def simulating(simulated: _datetime.date):
    """Adelanta el reloj dentro del bloque y **restaura lo que hubiera antes**.

    Restaurar el reloj *real* en lugar del anterior descartaría una simulación externa
    —la que instala `pytest_configure`— y contaminaría los tests que vinieran después.
    """
    previo = _datetime.date
    _set_clock(simulated)
    try:
        yield simulated
    finally:
        _datetime.date = previo


def uninstall() -> None:
    """Restaura el reloj real. Uso excepcional: prefiera `simulating`."""
    _datetime.date = _real_date

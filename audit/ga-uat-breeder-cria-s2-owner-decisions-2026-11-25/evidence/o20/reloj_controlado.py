"""O-20 · plugin de pytest: reloj controlado para los tests.

Con `GA_RELOJ_CONTROLADO=<AAAA-MM-DD>` fija `tests.time_reference.reference_today()` en ese día,
de modo que todas las fechas derivadas (`days_ago`, …) se calculan como si la suite corriera
ese día. Solo afecta a los tests; el producto sigue usando su reloj real. Se carga con
`-p reloj_controlado` y `PYTHONPATH` apuntando a este directorio.
"""
import datetime as _dt
import os


def pytest_configure(config):
    hoy = os.environ.get("GA_RELOJ_CONTROLADO")
    if not hoy:
        return
    import importlib
    import sys
    from pathlib import Path

    # Los tests importan el módulo con DOS nombres: `tests.time_reference` y `time_reference`
    # (con `tests/` en `sys.path`). Son objetos de módulo distintos: se fijan los dos.
    carpeta_tests = str(Path(str(config.rootpath)) / "tests")
    if carpeta_tests not in sys.path:
        sys.path.insert(0, carpeta_tests)
    fijo = _dt.date.fromisoformat(hoy)
    for nombre in ("tests.time_reference", "time_reference"):
        importlib.import_module(nombre).reference_today = lambda: fijo
    config._ga_reloj_controlado = fijo


def pytest_report_header(config):
    fijo = getattr(config, "_ga_reloj_controlado", None)
    return f"GA reloj controlado: {fijo.isoformat()} ({fijo.strftime('%A')})" if fijo else None

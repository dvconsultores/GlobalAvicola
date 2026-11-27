"""Semana productiva del lote — la única función canónica (`SPEC 020 §6` · `RR-30`).

La «Semana N» avícola es la **edad productiva del lote**, no la semana ISO del calendario:

```
semana 1  =  días 0 a 6 de vida del lote       (fecha_evento − inicio_del_lote)
semana n  =  (fecha_evento − inicio_del_lote).days // 7 + 1
```

La fecha base es `lots.start_date`, la misma con la que el sistema calcula la edad del lote
(curva de peso, índice productivo). Pesaje, mortalidad, descarte y alimento derivan su semana de
aquí; ningún otro código calcula una semana por su cuenta. La tendencia del panel
(`/dashboard/admin`) agrega por semana ISO de **calendario** a través de lotes: es otro concepto y
conserva su propia semántica.
"""

from __future__ import annotations

from datetime import date, datetime

#: Eventos cuya `week_number` (en cada fila de aves o de alimento) es derivada y de solo lectura.
TIPOS_CON_SEMANA_DERIVADA = frozenset({
    "mortality_recording", "cull_recording", "weight_recording", "feed_registration",
})

#: Eventos cuya fase productiva (`feed_movements.phase_id`) es derivada del lote (`RR-34`).
TIPOS_CON_FASE_DERIVADA = frozenset({"feed_registration"})


def _dia(valor):
    """Día del calendario de un valor que puede venir como fecha o como instante."""
    return valor.date() if isinstance(valor, datetime) else valor


def semana_productiva(inicio_lote: date | datetime | None, fecha_evento: date | datetime | None) -> int:
    """Semana productiva de un evento. `ValueError` si falta la fecha base o el evento es anterior.

    Nunca inventa una semana: quien llama traduce el error a `LOT_DATE_INCOMPLETE`.
    """
    inicio, fecha = _dia(inicio_lote), _dia(fecha_evento)
    if inicio is None or fecha is None:
        raise ValueError("sin fecha base para derivar la semana")
    dias = (fecha - inicio).days
    if dias < 0:
        raise ValueError("el evento es anterior al inicio del lote")
    return dias // 7 + 1

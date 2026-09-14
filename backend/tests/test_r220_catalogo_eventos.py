"""R-220 · Lote A (A-14) — el catálogo de tipos de evento expone `water_consumption`.

RED en HEAD: `ALL_EVENT_TYPES` no incluye el tipo informativo `water_consumption`
(B-24) y el cliente no puede rotularlo.
"""
from __future__ import annotations


def test_water_consumption_en_catalogo():
    from app.operations.schemas import ALL_EVENT_TYPES

    tipos = {item["type"] for item in ALL_EVENT_TYPES}
    assert "water_consumption" in tipos, sorted(tipos)
    etiqueta = next(i["label"] for i in ALL_EVENT_TYPES if i["type"] == "water_consumption")
    assert etiqueta, "sin etiqueta"

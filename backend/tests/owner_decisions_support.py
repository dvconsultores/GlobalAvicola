"""Datos válidos para las reglas ratificadas el 25-11-2026 (`SPEC 020 §6`).

Un test que registra una mortalidad, un descarte, una vacunación, un consumo de alimento o una
corrección debe declarar lo que el contrato ya exige: causa (`RR-32`), lote de vacuna (`RR-31`), tipo de
alimento (`RR-33`) y fase vigente del lote (`RR-34`), tipo de corrección (`RR-27`). Estas funciones
construyen ese dato **válido**; nunca debilitan una regla ni rellenan por el cliente lo que el servidor
rechaza.
"""

from __future__ import annotations

import uuid

#: `vaccine_lot_number` válido para un alta de vacunación.
LOTE_DE_VACUNA = "TEST-VAC-001"


async def _lista(client, headers, recurso: str, **params) -> list[dict]:
    r = await client.get(f"/api/v1/masters/{recurso}", headers=headers, params={"limit": 100, **params})
    assert r.status_code == 200, r.text
    datos = r.json()
    return datos["items"] if isinstance(datos, dict) else datos


async def causa_desconocida(client, headers, recurso: str = "mortality-causes") -> int:
    """Id de la causa compartida «Desconocida» (`mortality-causes` o `cull-causes`)."""
    filas = [f for f in await _lista(client, headers, recurso, search="Desconocida") if f["name"] == "Desconocida"]
    assert len(filas) == 1, f"«Desconocida» debe existir una vez en {recurso}: {filas}"
    return filas[0]["id"]


async def tipo_de_correccion(client, headers) -> int:
    """Id de un tipo de corrección de la empresa (se crea uno si no hay)."""
    filas = await _lista(client, headers, "correction-types")
    if filas:
        return filas[0]["id"]
    r = await client.post("/api/v1/masters/correction-types", headers=headers,
                          json={"name": f"Tipo de prueba {uuid.uuid4().hex[:8]}"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def tipo_de_alimento(client, headers) -> int:
    """Id de un tipo de alimento de la empresa (se crea uno si no hay)."""
    filas = await _lista(client, headers, "feed-types")
    if filas:
        return filas[0]["id"]
    r = await client.post("/api/v1/masters/feed-types", headers=headers,
                          json={"name": f"Alimento de prueba {uuid.uuid4().hex[:8]}",
                                "code": f"AP{uuid.uuid4().hex[:6].upper()}"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def fase_vigente_del_lote(client, headers, lote_id: int, start_date: str) -> int:
    """Asegura que el lote tenga una fase productiva vigente desde `start_date` (`RR-34`) y devuelve su id.

    Si el lote ya tiene una fase activa que cubre esa fecha, no crea otra.
    """
    r = await client.get(f"/api/v1/lots/{lote_id}/phases", headers=headers)
    assert r.status_code == 200, r.text
    for fase in r.json():
        if fase["start_date"] <= start_date and (fase.get("end_date") is None or fase["end_date"] >= start_date):
            return fase["phase_id"]
    fases = await _lista(client, headers, "productive-phases")
    if not fases:
        c = await client.post("/api/v1/masters/productive-phases", headers=headers,
                              json={"name": f"Fase de prueba {uuid.uuid4().hex[:6]}",
                                    "code": f"FP{uuid.uuid4().hex[:6].upper()}", "order": 1})
        assert c.status_code == 201, c.text
        fases = [c.json()]
    c = await client.post(f"/api/v1/lots/{lote_id}/phases", headers=headers, json={
        "lot_id": lote_id, "phase_id": fases[0]["id"], "start_date": start_date})
    assert c.status_code == 201, c.text
    return fases[0]["id"]

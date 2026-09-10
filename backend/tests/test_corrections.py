"""`GA-REM-006` / `P0-2` — la corrección debe corregir el dato.

Se creaba el `CorrectionLog`, se cambiaba el estado a `CORRECTED` y **no se escribía
nada**: el dato erróneo era el que se aprobaba, el que alimentaba los KPI y el que se
consolidaba hacia SAP. El sistema quedaba con dos verdades divergentes y la auditoría
respaldaba la que no era.

Regla vigente `RR-01` (Wave 1.5): la corrección escribe el valor en el acto, conserva el
original en el registro de corrección y deja el evento pendiente de aprobación.
"""

from __future__ import annotations

import pytest

from tests.time_reference import iso_days_ago, recent_event_date


async def _evento(client, headers, **extra):
    cuerpo = {
        "lot_id": 2, "event_type": "vaccination", "event_date": recent_event_date(),
        "vaccine_id": 1, "vaccination_route": "water", "treatment_days": 3,
        "observations": "original",
    }
    cuerpo.update(extra)
    r = await client.post("/api/v1/operations", headers=headers, json=cuerpo)
    assert r.status_code == 201, r.text
    return r.json()


async def _corregir(client, headers, event_id, campo, valor, motivo="Error de digitación"):
    return await client.post("/api/v1/corrections", headers=headers, json={
        "event_id": event_id, "field_name": campo,
        "corrected_value": valor, "reason": motivo,
    })


# ── P0-2 · el valor se aplica ─────────────────────────────────────────────────

@pytest.mark.parametrize("campo,valor,esperado", [
    ("observations", "corregido", "corregido"),
    ("vaccination_route", "ocular", "ocular"),
    ("treatment_days", "7", 7),
    ("vaccine_id", "1", 1),
    ("dosage_per_bird", "0.5", 0.5),
])
@pytest.mark.asyncio
async def test_la_correccion_escribe_el_valor(auth_headers, client, campo, valor, esperado):
    evento = await _evento(client, auth_headers)
    r = await _corregir(client, auth_headers, evento["id"], campo, valor)
    assert r.status_code == 201, r.text

    leido = await client.get(f"/api/v1/operations/{evento['id']}", headers=auth_headers)
    assert leido.json()[campo] == esperado, (
        f"'{campo}' debe quedar corregido en el dato, no solo en el registro de corrección")


@pytest.mark.asyncio
async def test_el_registro_conserva_el_valor_original(auth_headers, client):
    """`BR-09`: valor original y corregido, ambos visibles."""
    evento = await _evento(client, auth_headers, observations="valor de partida")
    r = await _corregir(client, auth_headers, evento["id"], "observations", "valor corregido")
    assert r.status_code == 201, r.text

    correcciones = await client.get(f"/api/v1/corrections/event/{evento['id']}",
                                    headers=auth_headers)
    assert correcciones.status_code == 200
    registro = correcciones.json()[0]
    assert registro["original_value"] == "valor de partida"
    assert registro["corrected_value"] == "valor corregido"
    assert registro["reason"]


@pytest.mark.asyncio
async def test_el_original_lo_lee_el_servidor_no_el_cliente(auth_headers, client):
    """Si el valor original lo aporta quien corrige, la auditoría deja de ser evidencia."""
    evento = await _evento(client, auth_headers, observations="lo que realmente había")
    r = await client.post("/api/v1/corrections", headers=auth_headers, json={
        "event_id": evento["id"], "field_name": "observations",
        "original_value": "una versión conveniente",   # mentira deliberada
        "corrected_value": "nuevo", "reason": "prueba de integridad",
    })
    assert r.status_code == 201, r.text
    assert r.json()["original_value"] == "lo que realmente había", (
        "El registro debe guardar lo que había en el dato, no lo que declare el cliente")


# ── El evento sigue requiriendo aprobación (RR-01) ────────────────────────────

@pytest.mark.asyncio
async def test_el_evento_corregido_no_queda_aprobado(auth_headers, client):
    evento = await _evento(client, auth_headers)
    await _corregir(client, auth_headers, evento["id"], "observations", "x")

    leido = await client.get(f"/api/v1/operations/{evento['id']}", headers=auth_headers)
    assert leido.json()["status"] == "corrected"
    assert leido.json()["approved_by_id"] is None, (
        "Corregir no es aprobar: el registro sigue necesitando aprobación (RR-01)")


@pytest.mark.asyncio
async def test_la_version_del_evento_avanza(auth_headers, client):
    evento = await _evento(client, auth_headers)
    assert evento["version"] == 1
    await _corregir(client, auth_headers, evento["id"], "observations", "x")
    leido = await client.get(f"/api/v1/operations/{evento['id']}", headers=auth_headers)
    assert leido.json()["version"] == 2, "Una corrección produce una versión nueva"


# ── Lista blanca de campos corregibles ────────────────────────────────────────

@pytest.mark.parametrize("campo", ["status", "company_id", "registered_by_id",
                                   "approved_by_id", "id", "event_type"])
@pytest.mark.asyncio
async def test_no_se_puede_corregir_lo_que_no_es_un_dato_operativo(
    auth_headers, client, campo
):
    """Sin lista blanca, una corrección sería la misma escalada que `R-32`.

    `field_name` lo elige el cliente: aplicar `setattr` sobre lo que llegue permitiría
    aprobar un evento, cambiarlo de compañía o reasignar quién lo registró.
    """
    evento = await _evento(client, auth_headers)
    r = await _corregir(client, auth_headers, evento["id"], campo, "1")
    assert r.status_code == 400, f"'{campo}' no puede corregirse: {r.status_code}"

    leido = await client.get(f"/api/v1/operations/{evento['id']}", headers=auth_headers)
    assert leido.json()["status"] == "registered", "El evento no puede haber cambiado"


@pytest.mark.asyncio
async def test_un_valor_del_tipo_equivocado_da_400_no_500(auth_headers, http_client):
    evento = await _evento(http_client, auth_headers)
    r = await http_client.post("/api/v1/corrections", headers=auth_headers, json={
        "event_id": evento["id"], "field_name": "treatment_days",
        "corrected_value": "no es un número", "reason": "prueba de tipos",
    })
    assert r.status_code == 400, f"Debe explicarse, no romperse: {r.status_code}"
    assert "treatment_days" in r.text


# ── Estados no corregibles (BR-15, BR-16, RR-01) ──────────────────────────────

@pytest.mark.asyncio
async def test_no_se_corrige_un_evento_cancelado(auth_headers, client):
    evento = await _evento(client, auth_headers)
    await client.post(f"/api/v1/operations/{evento['id']}/cancel", headers=auth_headers)

    r = await _corregir(client, auth_headers, evento["id"], "observations", "x")
    assert r.status_code == 400
    assert "no se puede corregir" in r.text.lower()


@pytest.mark.asyncio
async def test_la_fecha_corregida_sigue_sujeta_a_las_reglas(auth_headers, client):
    """Corregir no es una puerta trasera: `BR-19` sigue aplicándose después.

    `R-45` (Wave 2): la corrección escribía la fecha sin revalidarla y podía dejar el evento en
    período cerrado; la aserción admitía ambos comportamientos. `GA-REM-023-B` (`R-176`, WAVE B
    tranche 11) hace pasar la corrección por la guarda de edición: ahora se exige el `400` y la
    fecha intacta (`AC-R176-05`).
    """
    evento = await _evento(client, auth_headers)
    r = await _corregir(client, auth_headers, evento["id"], "event_date", iso_days_ago(400))
    leido = await client.get(f"/api/v1/operations/{evento['id']}", headers=auth_headers)
    assert (r.status_code, leido.json()["event_date"]) == (400, evento["event_date"]), (r.status_code, r.text)
    assert r.json().get("rule") == "BR-19"

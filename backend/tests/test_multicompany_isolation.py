"""Wave 2.75 — aislamiento multiempresa e IDOR.

`R-48` cambió cómo se resuelve el contexto de compañía, y eso obliga a una regresión
transversal: si el contexto se puede desplazar, hay que demostrar que **solo** puede
desplazarlo quien tiene derecho, y que ningún identificador ajeno es alcanzable.

No se confía en los filtros del frontend. Se prueba contra el API.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from app.auth.security import create_access_token
from tests.time_reference import iso_days_ago, recent_event_date

pytestmark = pytest.mark.asyncio


def _token(user_id: int, **extra) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id), **extra})}"}


# ── §20 · una única regla de resolución del contexto ─────────────────────────

async def test_la_fuente_del_contexto_es_una_sola_y_esta_documentada():
    """`get_current_user` resuelve la compañía efectiva. Nadie más.

    Para un usuario normal manda la base: un token no puede reclamar una compañía ajena.
    Para el Super Admin —que no pertenece a ninguna y puede operar sobre todas— se honra
    el claim que `switch-company` emitió.
    """
    import inspect

    from app.auth.security import get_current_user
    from app.tenancy import resolver_empresa_efectiva

    # `GA-REM-040` fase 2 / `OD-11`: la regla se movió a `app/tenancy.py` para que un
    # servicio o una tarea de fondo puedan invocarla. La propiedad que esta prueba defiende
    # no cambia —una sola fuente de contexto— y se comprueba en los dos extremos: que la
    # petición **delega** y que no conserva una segunda copia de la regla.
    peticion = inspect.getsource(get_current_user)
    assert "resolver_empresa_efectiva" in peticion, (
        "La petición debe delegar en el resolutor único")
    assert "company_id = user.company_id" not in peticion, (
        "No puede quedar una segunda copia de la regla en la capa de petición")

    regla = inspect.getsource(resolver_empresa_efectiva)
    assert "persistida" in regla, "El valor por defecto debe venir de la base"
    assert "if not puede_cambiar:" in regla, (
        "La excepción debe estar acotada a quien está autorizado a cambiar de empresa")


async def test_un_usuario_normal_no_desplaza_su_contexto(http_client, seeded_ids):
    """El claim de un usuario normal se ignora: la base es la autoridad."""
    r = await http_client.get(
        "/api/v1/operations?limit=100",
        headers=_token(seeded_ids["user_operator_id"], company_id=seeded_ids["company_id_2"]))
    assert r.status_code == 200, r.text
    ajenas = {e["company_id"] for e in r.json()} - {seeded_ids["company_id"]}
    assert not ajenas, f"Un usuario normal alcanzó datos de {ajenas} reclamándolo en el token"


async def test_un_usuario_normal_no_puede_cambiar_de_empresa(http_client, seeded_ids):
    r = await http_client.post("/api/v1/switch-company",
                               headers=_token(seeded_ids["user_operator_id"]),
                               json={"company_id": seeded_ids["company_id_2"]})
    assert r.status_code == 403, f"Solo el Super Admin puede cambiar de empresa: {r.status_code}"


async def test_el_super_admin_no_puede_situarse_en_una_empresa_inexistente(
    http_client, seeded_ids
):
    r = await http_client.post("/api/v1/switch-company",
                               headers=_token(seeded_ids["user_admin_id"]),
                               json={"company_id": 999999})
    assert r.status_code == 404, f"Una empresa inexistente debe rechazarse: {r.status_code}"


# ── §21 · la matriz de `switch-company` ──────────────────────────────────────

async def test_el_contexto_del_super_admin_determina_la_propiedad(http_client, seeded_ids):
    """Un lote creado tras el cambio pertenece a la empresa seleccionada."""
    cambio = await http_client.post("/api/v1/switch-company",
                                    headers=_token(seeded_ids["user_admin_id"]),
                                    json={"company_id": seeded_ids["company_id_2"]})
    assert cambio.status_code == 200, cambio.text
    cabecera = {"Authorization": f"Bearer {cambio.json()['access_token']}"}

    granja = await http_client.post("/api/v1/masters/farms", headers=cabecera,
                                    json={"name": "Granja B", "code": f"ISO-FARM-B-{__import__('uuid').uuid4().hex[:6]}",
                                          "company_id": seeded_ids["company_id_2"]})
    assert granja.status_code == 201, granja.text
    assert granja.json()["company_id"] == seeded_ids["company_id_2"], (
        "El maestro creado debe pertenecer a la empresa del contexto")

    lote = await http_client.post("/api/v1/lots", headers=cabecera, json={
        "lot_code": f"ISO-LOT-B-{__import__('uuid').uuid4().hex[:6]}", "farm_id": granja.json()["id"],
        "bird_type": "broiler", "sex": "mixed"})
    assert lote.status_code in (200, 201), lote.text
    assert lote.json()["company_id"] == seeded_ids["company_id_2"]


async def test_el_contexto_sobrevive_a_la_renovacion(http_client, seeded_ids):
    """Renovar no puede devolver al Super Admin a su compañía de origen sin avisar."""
    cambio = await http_client.post("/api/v1/switch-company",
                                    headers=_token(seeded_ids["user_admin_id"]),
                                    json={"company_id": seeded_ids["company_id_2"]})
    renovado = await http_client.post(
        "/api/v1/refresh", json={"refresh_token": cambio.json()["refresh_token"]})
    assert renovado.status_code == 200, renovado.text

    import base64
    import json

    carga = renovado.json()["access_token"].split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(carga + "=" * (-len(carga) % 4)))
    # El claim viaja como cadena: `create_access_token` serializa los numéricos, y el
    # frontend hace `Number(claims.company_id)` (`auth.store.ts:77`).
    assert str(claims.get("company_id")) == str(seeded_ids["company_id_2"]), (
        f"El contexto desplazado debe sobrevivir a la renovación; quedó en "
        f"{claims.get('company_id')} (`R-54`)")


# ── §23 · IDOR entre compañías ───────────────────────────────────────────────

@pytest_asyncio.fixture
async def recurso_ajeno(http_client, seeded_ids):
    """Crea, desde la compañía B, un lote y una operación que la compañía A no debe ver."""
    cambio = await http_client.post("/api/v1/switch-company",
                                    headers=_token(seeded_ids["user_admin_id"]),
                                    json={"company_id": seeded_ids["company_id_2"]})
    cabecera = {"Authorization": f"Bearer {cambio.json()['access_token']}"}

    # Códigos únicos por invocación: el fixture es de función y se ejecuta una vez por
    # test, de modo que reutilizar el mismo código chocaría con la unicidad.
    import uuid

    sufijo = uuid.uuid4().hex[:8]
    granja = await http_client.post("/api/v1/masters/farms", headers=cabecera,
                                    json={"name": f"Granja ajena {sufijo}",
                                          "code": f"IDOR-FARM-{sufijo}",
                                          "company_id": seeded_ids["company_id_2"]})
    assert granja.status_code == 201, granja.text
    lote = await http_client.post("/api/v1/lots", headers=cabecera, json={
        "lot_code": f"IDOR-LOT-{sufijo}", "farm_id": granja.json()["id"],
        "bird_type": "broiler", "sex": "mixed"})
    assert lote.status_code in (200, 201), lote.text
    operacion = await http_client.post("/api/v1/operations", headers=cabecera, json={
        "lot_id": lote.json()["id"], "event_type": "feed_registration",
        "event_date": iso_days_ago(0), "feed_movements": [{"quantity_kg": 5.0}]})
    return {
        "farm_id": granja.json()["id"],
        "lot_id": lote.json()["id"],
        "event_id": operacion.json()["id"] if operacion.status_code == 201 else None,
    }


@pytest.mark.parametrize("recurso,plantilla", [
    ("lot_id", "/api/v1/lots/{}"),
    ("event_id", "/api/v1/operations/{}"),
    ("farm_id", "/api/v1/masters/farms/{}"),
])
async def test_idor_lectura_de_un_recurso_ajeno(
    http_client, seeded_ids, recurso_ajeno, recurso, plantilla
):
    """Compañía A pide por id un recurso de la compañía B."""
    ident = recurso_ajeno[recurso]
    if ident is None:
        pytest.skip(f"no se pudo preparar {recurso}")
    r = await http_client.get(plantilla.format(ident),
                              headers=_token(seeded_ids["user_operator_id"]))
    assert r.status_code in (403, 404), (
        f"Un recurso de otra compañía no puede leerse: {r.status_code} en {plantilla}")


async def test_idor_escritura_sobre_un_recurso_ajeno(http_client, seeded_ids, recurso_ajeno):
    """Compañía A intenta modificar un lote de la compañía B."""
    r = await http_client.put(f"/api/v1/lots/{recurso_ajeno['lot_id']}",
                              headers=_token(seeded_ids["user_operator_id"]),
                              json={"lot_code": "SECUESTRADO"})
    assert r.status_code in (403, 404), f"No debe poder modificarse: {r.status_code}"


async def test_idor_no_se_puede_registrar_contra_un_lote_ajeno(
    http_client, seeded_ids, recurso_ajeno
):
    """El caso más peligroso: escribir datos operativos en el lote de otra empresa."""
    r = await http_client.post("/api/v1/operations",
                               headers=_token(seeded_ids["user_operator_id"]), json={
                                   "lot_id": recurso_ajeno["lot_id"],
                                   "event_type": "feed_registration",
                                   "event_date": iso_days_ago(0),
                                   "feed_movements": [{"quantity_kg": 1.0}]})
    assert r.status_code >= 400, (
        f"No debe poder registrarse contra un lote ajeno: {r.status_code}")


async def test_los_listados_no_filtran_entre_companias(http_client, seeded_ids, recurso_ajeno):
    """Barrido sobre los listados que devuelven datos de negocio."""
    cabecera = _token(seeded_ids["user_operator_id"])
    for ruta in ("/api/v1/operations?limit=100", "/api/v1/lots?limit=100",
                 "/api/v1/masters/farms?limit=100"):
        r = await http_client.get(ruta, headers=cabecera)
        if r.status_code != 200:
            continue
        cuerpo = r.json()
        elementos = cuerpo if isinstance(cuerpo, list) else cuerpo.get("items", [])
        ajenos = [e for e in elementos if isinstance(e, dict)
                  and e.get("company_id") not in (None, seeded_ids["company_id"])]
        assert not ajenos, f"{ruta} devolvió {len(ajenos)} elementos de otra compañía"

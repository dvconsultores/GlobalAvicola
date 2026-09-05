"""Pertenencia en los vínculos de trazabilidad — `GA-REM-030`, hallazgo `R-60`.

Cubre `AC01`…`AC06`.

`POST /lots/egg-batches` y `/chick-batches` construían la entidad directamente desde el
cuerpo (`EggBatch(**data.model_dump())`), sin comprobar pertenencia ni existencia.

`EggBatch` y `ChickBatch` **no declaran `company_id`**: su dueño es derivado de los lotes que
enlazan. Un vínculo entre compañías produce un registro sin dueño posible, y hace
insatisfacible `GA-REM-008 AC06` —certificado— que promete que un usuario nunca obtiene un
lote de trazabilidad que referencie lotes de otra compañía.

Fechas relativas al reloj (`R-28`). Contexto de empresa por el token activo, nunca por `/me`
(`R-66`).
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import Lot
from tests.time_reference import iso_days_ago

PREFIJO = "TO-TEST-"


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.lots.models import ChickBatch, EggBatch, LotPhase, OpeningBalance

    async with e.begin() as c:
        ids = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if ids:
            await c.execute(delete(ChickBatch).where(
                ChickBatch.hatchery_lot_id.in_(ids) | ChickBatch.destination_lot_id.in_(ids)))
            await c.execute(delete(EggBatch).where(
                EggBatch.source_lot_id.in_(ids) | EggBatch.hatchery_lot_id.in_(ids)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
    await e.dispose()


# ── utilidades ────────────────────────────────────────────────────────────────

async def _lote(client, cabecera, company_id, farm_id, house_id, tipo="breeder"):
    r = await client.post("/api/v1/lots", headers=cabecera, json={
        "company_id": company_id, "farm_id": farm_id, "house_id": house_id,
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": tipo, "sex": "mixed",
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _maestros_en(client, cabecera, company_id, sufijo):
    """Granja y galpón de una compañía concreta."""
    g = await client.post("/api/v1/masters/farms", headers=cabecera, json={
        "company_id": company_id, "name": f"{PREFIJO}granja-{sufijo}", "code": f"TOG{sufijo}"})
    assert g.status_code in (200, 201), g.text
    h = await client.post("/api/v1/masters/houses", headers=cabecera, json={
        "farm_id": g.json()["id"], "name": f"{PREFIJO}galpon-{sufijo}", "code": f"TOH{sufijo}"})
    assert h.status_code in (200, 201), h.text
    return g.json()["id"], h.json()["id"]


async def _en_empresa(client, cabecera, company_id):
    """Token del mismo usuario con el contexto puesto en otra empresa."""
    r = await client.post("/api/v1/switch-company", headers=cabecera,
                          json={"company_id": company_id})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _huevo(origen, destino):
    return {"source_lot_id": origen, "hatchery_lot_id": destino,
            "quantity_dispatched": 1000, "dispatch_date": iso_days_ago(1)}


def _pollito(origen, destino):
    return {"hatchery_lot_id": origen, "destination_lot_id": destino,
            "quantity_dispatched": 900, "dispatch_date": iso_days_ago(1)}


async def _super_admin_sin_contexto(client, auth_headers, sufijo):
    """Super Admin **sin empresa** (`company_id = None`), creado por la API.

    `docs/02 §76` lo contempla: «cada usuario pertenece a una compañía, **excepto Super
    Admin**». Un rol con `module="*"` y `scope_type="all"` es lo que
    `auth/security.py:118` reconoce como tal.

    Hace falta este sujeto y no vale el administrador de pruebas: aquél tiene empresa, de
    modo que la pertenencia del actor rechazaría antes y las reglas de coherencia y de
    existencia quedarían sin prueba que las aislara. La puerta de sensibilidad lo demostró.
    """
    rol = await client.post("/api/v1/roles", headers=auth_headers, json={
        "name": f"TO-TEST Super {sufijo}", "description": "Super Admin sin contexto",
        "permissions": [{"module": "*", "action": "create", "scope_type": "all"},
                        {"module": "*", "action": "read", "scope_type": "all"}],
    })
    assert rol.status_code in (200, 201), rol.text
    clave = f"Su-{uuid.uuid4().hex[:12]}!"
    u = await client.post("/api/v1/users", headers=auth_headers, json={
        "username": f"to_super_{sufijo}", "email": f"to_super_{sufijo}@example.com",
        "password": clave, "first_name": "Super", "last_name": "SinEmpresa",
        "company_id": None, "role_id": rol.json()["id"], "view_type": "web",
    })
    assert u.status_code in (200, 201), u.text
    e = await client.post("/api/v1/login",
                          json={"username": f"to_super_{sufijo}", "password": clave})
    assert e.status_code == 200, e.text
    return {"Authorization": f"Bearer {e.json()['access_token']}"}


async def _sujeto_con_permiso(client, auth_headers, company_id, sufijo):
    """Usuario de `company_id` **con `lots:create`**, que no es Super Admin.

    Sin ese permiso el 403 llegaría antes que la pertenencia y la prueba no mediría nada.
    """
    rol = await client.post("/api/v1/roles", headers=auth_headers, json={
        "name": f"TO-TEST Enlace {sufijo}", "description": "Sujeto de GA-REM-030",
        "permissions": [{"module": "lots", "action": "create"},
                        {"module": "lots", "action": "read"},
                        {"module": "masters", "action": "read"}],
    })
    assert rol.status_code in (200, 201), rol.text
    clave = f"To-{uuid.uuid4().hex[:12]}!"
    u = await client.post("/api/v1/users", headers=auth_headers, json={
        "username": f"to_test_{sufijo}", "email": f"to_test_{sufijo}@example.com",
        "password": clave, "first_name": "Enlace", "last_name": "Sujeto",
        "company_id": company_id, "role_id": rol.json()["id"], "view_type": "web",
    })
    assert u.status_code in (200, 201), u.text
    e = await client.post("/api/v1/login",
                          json={"username": f"to_test_{sufijo}", "password": clave})
    assert e.status_code == 200, e.text
    return {"Authorization": f"Bearer {e.json()['access_token']}"}


@pytest_asyncio.fixture
async def escenario(client, auth_headers, seeded_ids):
    """Dos lotes en la empresa 1 y uno en la empresa 2, con sus maestros propios."""
    s = uuid.uuid4().hex[:8]
    c1, c2 = seeded_ids["company_id"], seeded_ids["company_id_2"]

    propio_a = await _lote(client, auth_headers, c1,
                           seeded_ids["farm_id"], seeded_ids["house_id"])
    propio_b = await _lote(client, auth_headers, c1,
                           seeded_ids["farm_id"], seeded_ids["house_id"], "hatchery")

    admin_2 = await _en_empresa(client, auth_headers, c2)
    granja_2, galpon_2 = await _maestros_en(client, admin_2, c2, s)
    ajeno = await _lote(client, admin_2, c2, granja_2, galpon_2, "hatchery")
    ajeno_b = await _lote(client, admin_2, c2, granja_2, galpon_2, "broiler")

    return {"s": s, "c1": c1, "c2": c2, "propio_a": propio_a, "propio_b": propio_b,
            "ajeno": ajeno, "ajeno_b": ajeno_b, "admin_2": admin_2}


async def _vinculos(motor, lot_id):
    from app.lots.models import ChickBatch, EggBatch
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        huevos = (await s.execute(select(EggBatch).where(
            (EggBatch.source_lot_id == lot_id) | (EggBatch.hatchery_lot_id == lot_id)
        ))).scalars().all()
        pollitos = (await s.execute(select(ChickBatch).where(
            (ChickBatch.hatchery_lot_id == lot_id) | (ChickBatch.destination_lot_id == lot_id)
        ))).scalars().all()
    return len(huevos) + len(pollitos)


# ── AC01 · el actor no alcanza lotes ajenos ───────────────────────────────────

@pytest.mark.parametrize("ruta,cuerpo", [("egg-batches", _huevo), ("chick-batches", _pollito)])
async def test_t_060_01_el_actor_no_enlaza_lotes_ajenos(
    client, http_client, auth_headers, seeded_ids, escenario, motor, ruta, cuerpo
):
    """`AC01` y `AC06` · con permiso, pero sin derecho sobre el lote ajeno.

    CONTROL y TRATAMIENTO comparten sujeto, permiso y forma de la petición. Lo único que
    cambia es de quién es el lote: si el rechazo llegara por otra causa, el CONTROL fallaría.
    """
    sujeto = await _sujeto_con_permiso(
        client, auth_headers, escenario["c1"], f"{escenario['s']}{ruta[:3]}")

    # CONTROL · dos lotes suyos.
    ok = await http_client.post(f"/api/v1/lots/{ruta}", headers=sujeto,
                                json=cuerpo(escenario["propio_a"], escenario["propio_b"]))
    assert ok.status_code == 201, (
        f"CONTROL falló: el sujeto no puede enlazar ni lotes propios, "
        f"así que un rechazo posterior no probaría pertenencia: {ok.text}"
    )

    # TRATAMIENTO · el destino es de otra compañía.
    cruzado = await http_client.post(f"/api/v1/lots/{ruta}", headers=sujeto,
                                     json=cuerpo(escenario["propio_a"], escenario["ajeno"]))
    assert cruzado.status_code == 400, (
        f"se enlazó un lote de otra compañía: {cruzado.status_code} {cruzado.text}"
    )
    assert cruzado.json().get("rule") == "BR-07", cruzado.json()

    # `AC04` · y no quedó nada.
    assert await _vinculos(motor, escenario["ajeno"]) == 0, (
        "el intento rechazado dejó un vínculo sobre el lote ajeno"
    )


# ── AC02 · el par es coherente incluso para el Super Admin ────────────────────

@pytest.mark.parametrize("ruta,cuerpo", [("egg-batches", _huevo), ("chick-batches", _pollito)])
async def test_t_060_02_el_super_admin_sin_contexto_no_cruza_companias(
    client, auth_headers, escenario, motor, ruta, cuerpo
):
    """`AC02` · autoridad global no es licencia para crear un registro sin dueño.

    El sujeto es un Super Admin **sin empresa** (`company_id = None`), y esa elección es lo
    que da valor a la prueba: para él la pertenencia del actor se abstiene por diseño
    —`verificar_pertenencia` no filtra sin contexto—, de modo que **solo** la coherencia del
    par puede rechazarlo. Con un administrador que sí tiene empresa, la regla `A` lo
    rechazaría antes y esta comprobación no mediría lo que dice medir.

    El vínculo no tiene `company_id` propio: uniendo dos compañías queda sin dueño posible y
    hace insatisfacible `GA-REM-008 AC06`.
    """
    sujeto = await _super_admin_sin_contexto(
        client, auth_headers, f"{escenario['s']}{ruta[:3]}")

    # CONTROL · el mismo Super Admin sin contexto, dentro de una sola compañía: se acepta.
    # Es lo que prueba que la guarda no le recortó la autoridad legítima.
    ok = await client.post(f"/api/v1/lots/{ruta}", headers=sujeto,
                           json=cuerpo(escenario["propio_a"], escenario["propio_b"]))
    assert ok.status_code == 201, f"CONTROL falló: {ok.text}"

    # TRATAMIENTO · el mismo sujeto, la misma llamada, cruzando compañías.
    cruzado = await client.post(f"/api/v1/lots/{ruta}", headers=sujeto,
                                json=cuerpo(escenario["propio_a"], escenario["ajeno"]))
    assert cruzado.status_code == 400, (
        f"el Super Admin creó un vínculo entre compañías: {cruzado.status_code} {cruzado.text}"
    )
    assert await _vinculos(motor, escenario["ajeno"]) == 0


# ── AC03 · un lote inexistente se rechaza por contrato ────────────────────────

@pytest.mark.parametrize("ruta,cuerpo", [("egg-batches", _huevo), ("chick-batches", _pollito)])
async def test_t_060_03_lote_inexistente_da_400_y_no_500(
    client, auth_headers, escenario, ruta, cuerpo
):
    """`AC03` · sin la guarda esto revienta con 500 por violación de clave foránea.

    También aquí el sujeto es el Super Admin **sin contexto**: con empresa, la pertenencia
    del actor ya descartaría el identificador inventado y la comprobación de existencia
    podría desaparecer sin que ninguna prueba lo notara.
    """
    sujeto = await _super_admin_sin_contexto(
        client, auth_headers, f"{escenario['s']}x{ruta[:3]}")
    r = await client.post(f"/api/v1/lots/{ruta}", headers=sujeto,
                          json=cuerpo(escenario["propio_a"], 99_999_999))
    assert r.status_code == 400, f"esperado 400 por contrato, no {r.status_code}: {r.text}"
    assert r.json().get("rule") == "BR-07", r.json()


# ── AC05 · el enlace legítimo sigue funcionando ───────────────────────────────

async def test_t_060_04_el_enlace_legitimo_sigue_vivo(
    client, auth_headers, escenario, motor
):
    """`AC05` · regresión de `GA-REM-008 AC07`: el vínculo válido se crea y se ve."""
    r = await client.post("/api/v1/lots/egg-batches", headers=auth_headers,
                          json=_huevo(escenario["propio_a"], escenario["propio_b"]))
    assert r.status_code == 201, r.text

    # `R-68` · lectura inmediata, sin esperas.
    arbol = await client.get(f"/api/v1/lots/{escenario['propio_a']}/traceability",
                             headers=auth_headers)
    assert arbol.status_code == 200, arbol.text
    enviados = arbol.json()["egg_batches_sent"]
    assert any(b["hatchery_lot_id"] == escenario["propio_b"] for b in enviados), enviados


# ── AC02 · el Super Admin sí puede operar dentro de otra compañía ─────────────

async def test_t_060_05_el_super_admin_opera_dentro_de_otra_compania(
    client, auth_headers, escenario, motor
):
    """`AC02`, cara complementaria · la guarda **no** recorta la autoridad legítima.

    Sin esta comprobación, la corrección podría haber convertido «no cruzar compañías» en
    «el Super Admin no sale de la suya», que sería un cambio de RBAC que nadie pidió.
    """
    admin_2 = escenario["admin_2"]
    s = escenario["s"]
    granja, galpon = await _maestros_en(client, admin_2, escenario["c2"], f"b{s}")
    otro = await _lote(client, admin_2, escenario["c2"], granja, galpon, "broiler")

    r = await client.post("/api/v1/lots/chick-batches", headers=admin_2,
                          json=_pollito(escenario["ajeno"], otro))
    assert r.status_code == 201, (
        f"el Super Admin perdió la capacidad de operar dentro de la compañía 2: {r.text}"
    )


# ── AC01 · la pertenencia del actor hace trabajo propio ───────────────────────

async def test_t_060_06_dos_lotes_ajenos_coherentes_entre_si_tambien_se_rechazan(
    client, http_client, auth_headers, seeded_ids, escenario, motor
):
    """`AC01` aislado de `AC02` · el par es coherente y aun así no es suyo.

    Las dos reglas se solapan cuando el vínculo cruza compañías, de modo que un rechazo allí
    no dice cuál actuó. Aquí **los dos lotes son de la compañía 2**: la coherencia del par se
    cumple, así que solo la pertenencia del actor puede rechazarlo. Sin este caso, la regla
    `A` podría desaparecer sin que ninguna prueba lo notara.
    """
    sujeto = await _sujeto_con_permiso(
        client, auth_headers, escenario["c1"], f"{escenario['s']}sol")

    r = await http_client.post("/api/v1/lots/egg-batches", headers=sujeto,
                               json=_huevo(escenario["ajeno"], escenario["ajeno_b"]))
    assert r.status_code == 400, (
        f"un usuario de la compañía 1 enlazó dos lotes de la compañía 2: {r.text}"
    )
    assert r.json().get("rule") == "BR-07", r.json()
    assert await _vinculos(motor, escenario["ajeno"]) == 0

"""Destinatarios de las notificaciones internas — `GA-REM-038` enmienda A, decisión `OD-08`.

Cubre `AC-R01`…`AC-R11` y `AC-T01`…`AC-T04`.

`OD-08` nombra **funciones** —quien cargó el dato, administradores, contraloría, gerente del
área, supervisor— y esta suite las comprueba contra los roles que existen de verdad. El gerente
del área no se prueba porque no hay áreas ni rol de gerencia: se declara en
`P14_OD08_ROLE_MAPPING_MATRIX.md §5` y no se fabrica un test que no mediría nada.

La regla es una **unión que no resta**: «notificar al operador» y «Notificar al rol Analista
SAP» siguen exigidos por sus fuentes y se suman a los términos nuevos. Y deduplica: quien
cumple varias condiciones recibe un aviso, no uno por motivo.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import Lot
from tests.time_reference import iso_days_ago, recent_event_date

PREFIJO = "NR-TEST-"

#: Los nombres reales del catálogo, no inventados. `P14_OD08_ROLE_MAPPING_MATRIX.md §2`.
ROL_ADMIN = "Administrador de Empresa"      # `docs/02 §6.1`, normativo
ROL_CONTRALOR = "Contralor Avícola"         # `seeds/integration_seeds.py:137`
ROL_SUPERVISOR = "Supervisor Avícola"       # `docs/02 §6.1` + migración `l2m3n4o5p6q7`
#: `GA-REM-039`. No existe en el catálogo y **no se siembra**: `GA-REM-034` permite que la
#: empresa lo cree. El resolutor lo reconoce por el nombre, como a los demás.
ROL_GERENTE = "Gerente de Área"


def _cabecera(user_id: int) -> dict:
    from app.auth.security import create_access_token
    return {"Authorization": "Bearer " + create_access_token(data={"sub": str(user_id)})}


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    from app.integrations.sap.models import ConsolidatedMovement, SapPayload, SapSyncJob
    async with e.connect() as c:
        marca = {
            "payload": (await c.execute(select(func.max(SapPayload.id)))).scalar() or 0,
            "consolidado": (await c.execute(
                select(func.max(ConsolidatedMovement.id)))).scalar() or 0,
            "job": (await c.execute(select(func.max(SapSyncJob.id)))).scalar() or 0,
        }
    yield e

    from app.audit.models import AuditLog
    from app.auth.models import Permission, Role, User
    from app.operations.models import BirdMovement, OperationalAlert, OperationalEvent
    from app.review.models import ApprovalAction

    async with e.begin() as c:
        usuarios = (await c.execute(
            select(User.id).where(User.username.like(f"{PREFIJO}%")))).scalars().all()
        if usuarios:
            await c.execute(text(
                "DELETE FROM notifications WHERE recipient_user_id = ANY(:ids)"),
                {"ids": usuarios})
        nuevas = (await c.execute(select(SapPayload.id).where(
            SapPayload.id > marca["payload"]))).scalars().all()
        if nuevas:
            await c.execute(text(
                "DELETE FROM notifications WHERE related_entity_type = 'sap_payload' "
                "AND related_entity_id = ANY(:ids)"), {"ids": nuevas})
            await c.execute(text(
                "DELETE FROM sap_responses WHERE payload_id = ANY(:ids)"), {"ids": nuevas})
            await c.execute(delete(SapPayload).where(SapPayload.id.in_(nuevas)))
        await c.execute(delete(ConsolidatedMovement).where(
            ConsolidatedMovement.id > marca["consolidado"]))
        await c.execute(delete(SapSyncJob).where(SapSyncJob.id > marca["job"]))

        lotes = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        eventos = (await c.execute(select(OperationalEvent.id).where(
            OperationalEvent.lot_id.in_(lotes or [-1])))).scalars().all()
        if eventos:
            await c.execute(text(
                "DELETE FROM notifications WHERE related_entity_type = 'operational_event' "
                "AND related_entity_id = ANY(:ids)"), {"ids": eventos})
            await c.execute(delete(ApprovalAction).where(ApprovalAction.event_id.in_(eventos)))
            await c.execute(delete(BirdMovement).where(BirdMovement.event_id.in_(eventos)))
            await c.execute(delete(OperationalAlert).where(
                OperationalAlert.event_id.in_(eventos)))
            await c.execute(delete(AuditLog).where(AuditLog.entity_id.in_(
                [str(i) for i in eventos])))
            await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
        if lotes:
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(lotes)))
            await c.execute(delete(Lot).where(Lot.id.in_(lotes)))
        if usuarios:
            # `GA-REM-040`: las concesiones de unidad referencian al usuario y le impiden
            # ser borrado. Se retiran antes, como ya se hace con el resto de dependencias.
            await c.execute(text(
                "DELETE FROM user_business_units WHERE user_id = ANY(:ids)"),
                {"ids": list(usuarios)})
            await c.execute(delete(User).where(User.id.in_(usuarios)))
        roles = (await c.execute(
            select(Role.id).where(Role.name.like(f"{PREFIJO}%")))).scalars().all()
        if roles:
            await c.execute(delete(Permission).where(Permission.role_id.in_(roles)))
            await c.execute(delete(Role).where(Role.id.in_(roles)))
    await e.dispose()


# ── Utilidades de escenario ───────────────────────────────────────────────────

async def _rol(client, cab, nombre: str, permisos=None) -> int:
    """El rol por su nombre real, creándolo si la siembra no lo trae.

    `docs/02 §6.1` enumera once roles y hay seis sembrados; `GA-REM-034` permite crear los que
    falten. El resolutor debe funcionar con los que existan, así que el test los provee.
    """
    from app.auth.models import Role
    import app.database as database

    async with database.async_session() as s:
        existente = (await s.execute(
            select(Role).where(Role.name == nombre))).scalar_one_or_none()
        if existente is not None:
            return existente.id

    r = await client.post("/api/v1/roles", headers=cab, json={
        "name": nombre, "description": f"Rol normativo: {nombre}",
        "permissions": permisos or [{"module": "operations", "action": "read"}],
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _situado_en(client, cab, company_id):
    """Cabeceras de la autoridad global **situada** en esa empresa. `OD-14.b`.

    Desde `OD-14`, `/users` es superficie de inquilino también para el Super Administrador:
    aprovisionar en la empresa `B` exige estar en `B`. `switch-company` es el mecanismo que el
    propio producto ofrece para eso, y el que un humano usaría.

    El cambio de expectativa es deliberado: esta prueba se apoyaba en que la autoridad global
    atravesaba cualquier inquilino desde cualquier contexto, que era la norma anterior y dejó
    de serlo por decisión de propietario (`R-126`).
    """
    r = await client.post("/api/v1/switch-company", headers=cab,
                          json={"company_id": company_id})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _usuario(client, cab, role_id: int, company_id: int) -> dict:
    """Crea un usuario **en** `company_id`, situándose allí primero. `OD-14.c`.

    Desde `OD-14` el alta es superficie de inquilino también para la autoridad global: la
    empresa sale del contexto, no del cuerpo. Sin situarse, estos usuarios nacían en la
    empresa del administrador y la prueba de fuga los contaba como propios — un defecto de
    fixture que se presentaba como fuga de notificaciones.
    """
    cab = await _situado_en(client, cab, company_id)
    nombre = f"{PREFIJO}{uuid.uuid4().hex[:8]}"
    r = await client.post("/api/v1/users", headers=cab, json={
        "username": nombre, "first_name": "Test", "last_name": nombre,
        "email": f"{nombre}@example.com", "password": uuid.uuid4().hex,
        "role_id": role_id, "company_id": company_id, "view_type": "web",
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _lote(client, cab, seeded_ids, area_id=None) -> dict:
    r = await client.post("/api/v1/lots", headers=cab, json={
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"], "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder", "sex": "mixed", "start_date": iso_days_ago(60),
        "area_id": area_id,
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _evento(client, seeded_ids, lote, tipo="weight_recording", **extra) -> dict:
    """Registrado **por el operador**: es el originador que `OD-08` nombra."""
    operador = _cabecera(seeded_ids["user_operator_id"])
    cuerpo = {
        "lot_id": lote["id"], "farm_id": lote["farm_id"], "house_id": lote["house_id"],
        "event_type": tipo, "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 10, "avg_weight": 1800}],
    }
    cuerpo.update(extra)
    r = await client.post("/api/v1/operations", headers=operador, json=cuerpo)
    assert r.status_code == 201, r.text
    return r.json()


async def _rechazar(client, cab, seeded_ids, event_id):
    operador = _cabecera(seeded_ids["user_operator_id"])
    envio = await client.post(f"/api/v1/operations/{event_id}/submit", headers=operador)
    assert envio.status_code == 200, envio.text
    inicio = await client.post(f"/api/v1/review/start/{event_id}", headers=cab)
    assert inicio.status_code == 200, inicio.text
    return await client.post("/api/v1/approvals/reject", headers=cab,
                             json={"event_id": event_id,
                                   "observations": "Datos incoherentes en el pesaje"})


async def _destinatarios(test_database_url, entity_type: str, entity_id: int) -> set[int]:
    """Quién recibió aviso de ese hecho, leído de la base."""
    e = create_async_engine(test_database_url)
    try:
        async with e.connect() as c:
            filas = (await c.execute(text(
                "SELECT recipient_user_id FROM notifications "
                "WHERE related_entity_type = :t AND related_entity_id = :i"),
                {"t": entity_type, "i": entity_id})).scalars().all()
        return set(filas)
    finally:
        await e.dispose()


async def _cuantas(test_database_url, entity_type, entity_id, user_id) -> int:
    e = create_async_engine(test_database_url)
    try:
        async with e.connect() as c:
            return (await c.execute(text(
                "SELECT count(*) FROM notifications WHERE related_entity_type = :t "
                "AND related_entity_id = :i AND recipient_user_id = :u"),
                {"t": entity_type, "i": entity_id, "u": user_id})).scalar()
    finally:
        await e.dispose()


async def _area(client, cab, company_id):
    r = await client.post("/api/v1/masters/areas", headers=cab, json={
        "company_id": company_id, "name": f"{PREFIJO}{uuid.uuid4().hex[:8]}"})
    assert r.status_code in (200, 201), r.text
    return r.json()


async def _en_area(client, cab, role_id, company_id, area_id) -> dict:
    # `OD-14`: crear y editar ocurren en la empresa efectiva. `_usuario` ya se sitúa; la
    # edición necesita el mismo contexto.
    propio = await _situado_en(client, cab, company_id)
    u = await _usuario(client, cab, role_id, company_id)
    r = await client.put(f"/api/v1/users/{u['id']}", headers=propio,
                         json={"area_id": area_id})
    assert r.status_code == 200, r.text
    assert r.json()["area_id"] == area_id, r.json()
    return r.json()


@pytest_asyncio.fixture
async def elenco(client, auth_headers, seeded_ids, motor):
    """Un usuario por cada función que `OD-08` nombra, con rol real.

    El área entra en el fixture porque `OD-08` dice «el supervisor **correspondiente**», y
    `GA-REM-039` lo hace literal: la capacidad la da el rol y la pertenencia, `area_id`. Un
    supervisor sin área no es supervisor de ninguna, así que el escenario debe tenerla.

    Administración y contraloría **no** llevan área: su alcance es toda la empresa.
    """
    empresa = seeded_ids["company_id"]
    area = await _area(client, auth_headers, empresa)
    return {
        "area": area,
        "admin": await _usuario(client, auth_headers,
                                await _rol(client, auth_headers, ROL_ADMIN), empresa),
        "contralor": await _usuario(client, auth_headers,
                                    await _rol(client, auth_headers, ROL_CONTRALOR), empresa),
        "supervisor": await _en_area(client, auth_headers,
                                     await _rol(client, auth_headers, ROL_SUPERVISOR),
                                     empresa, area["id"]),
    }


# ── AC-R01 · AC-R02 · AC-R03 · AC-R05 · AC-R06 ────────────────────────────────

async def test_t_038_20_el_rechazo_llega_a_las_cinco_funciones(
    client, auth_headers, seeded_ids, motor, elenco, test_database_url
):
    """`AC-R01`…`AC-R03`, `AC-R05` y `AC-R06` · la unión de `OD-08`, sin perder al operador.

    «Registro rechazado (notificar al operador)» es una exigencia previa de `docs/02 §3.14`.
    `OD-08` **amplía**; una decisión que amplía no retira.
    """
    lote = await _lote(client, auth_headers, seeded_ids, elenco["area"]["id"])
    evento = await _evento(client, seeded_ids, lote)
    r = await _rechazar(client, auth_headers, seeded_ids, evento["id"])
    assert r.status_code == 200, r.text

    avisados = await _destinatarios(test_database_url, "operational_event", evento["id"])

    # `AC-R06` · el destinatario que ya exigía la fuente anterior sigue estando.
    assert seeded_ids["user_operator_id"] in avisados, (
        "se perdió al operador, que `docs/02 §3.14` exige explícitamente"
    )
    # `AC-R01`…`AC-R05` · y los que `OD-08` añade.
    for funcion in ("admin", "contralor", "supervisor"):
        assert elenco[funcion]["id"] in avisados, f"falta {funcion}: {avisados}"


async def test_t_038_21_la_mortalidad_sobre_umbral_avisa(
    client, auth_headers, seeded_ids, motor, elenco, test_database_url
):
    """`AC-R01`…`AC-R05` · «Mortalidad > umbral configurable», `docs/02 §3.14`.

    El umbral vive en `settings`, que es lo que hace «configurable» al nombre del evento. Aquí
    se supera con holgura para que la alerta se dispare sin depender del saldo exacto.
    """
    lote = await _lote(client, auth_headers, seeded_ids, elenco["area"]["id"])
    await _evento(client, seeded_ids, lote, tipo="bird_reception",
                  bird_movements=[{"sex": "mixed", "quantity": 1000}],
                  received_total=1000, dead_on_arrival=0, rejected_on_arrival=0)  # `GA-REM-021-B` (`B01`), solo setup
    muerte = await _evento(client, seeded_ids, lote, tipo="mortality_recording",
                           bird_movements=[{"sex": "mixed", "quantity": 200}])

    avisados = await _destinatarios(test_database_url, "operational_event", muerte["id"])
    assert seeded_ids["user_operator_id"] in avisados, "falta quien registró la mortalidad"
    for funcion in ("admin", "contralor", "supervisor"):
        assert elenco[funcion]["id"] in avisados, f"falta {funcion}: {avisados}"


async def test_t_038_22_el_peso_fuera_de_curva_avisa(
    client, auth_headers, seeded_ids, motor, elenco, test_database_url
):
    """`AC-R01`…`AC-R05` · «Peso fuera de estándar», con la curva de `GA-REM-037`."""
    empresa = seeded_ids["company_id"]
    linea = (await client.post("/api/v1/masters/genetic-lines", headers=auth_headers, json={
        "company_id": empresa, "name": f"{PREFIJO}{uuid.uuid4().hex[:8]}"})).json()
    curva = await client.post("/api/v1/masters/weight-curves", headers=auth_headers, json={
        "genetic_line_id": linea["id"], "version_label": "v1", "is_active": True,
        "points": [{"age_days": 10, "min_weight": 90.0, "max_weight": 110.0},
                   {"age_days": 20, "min_weight": 180.0, "max_weight": 220.0}]})
    assert curva.status_code == 201, curva.text

    l = await client.post("/api/v1/lots", headers=auth_headers, json={
        "company_id": empresa, "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
        "genetic_line_id": linea["id"], "start_date": iso_days_ago(22),
        "area_id": elenco["area"]["id"]})
    assert l.status_code == 201, l.text

    # A 15 días la curva interpola a [135, 165]; 100 g queda por debajo.
    pesaje = await _evento(client, seeded_ids, l.json(), event_date=iso_days_ago(7),
                           bird_movements=[{"sex": "mixed", "quantity": 50, "avg_weight": 100}])

    avisados = await _destinatarios(test_database_url, "operational_event", pesaje["id"])
    assert seeded_ids["user_operator_id"] in avisados, "falta quien registró el pesaje"
    for funcion in ("admin", "contralor", "supervisor"):
        assert elenco[funcion]["id"] in avisados, f"falta {funcion}: {avisados}"


async def test_t_038_23_dentro_de_curva_no_avisa(
    client, auth_headers, seeded_ids, motor, elenco, test_database_url
):
    """`GA-REM-037` sigue vigente: dentro de norma **no** hay aviso.

    `OD-08` amplió los destinatarios; no convirtió cada pesaje en una notificación.
    """
    empresa = seeded_ids["company_id"]
    linea = (await client.post("/api/v1/masters/genetic-lines", headers=auth_headers, json={
        "company_id": empresa, "name": f"{PREFIJO}{uuid.uuid4().hex[:8]}"})).json()
    await client.post("/api/v1/masters/weight-curves", headers=auth_headers, json={
        "genetic_line_id": linea["id"], "version_label": "v1", "is_active": True,
        "points": [{"age_days": 10, "min_weight": 90.0, "max_weight": 110.0},
                   {"age_days": 20, "min_weight": 180.0, "max_weight": 220.0}]})
    l = (await client.post("/api/v1/lots", headers=auth_headers, json={
        "company_id": empresa, "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
        "genetic_line_id": linea["id"], "start_date": iso_days_ago(22)})).json()

    dentro = await _evento(client, seeded_ids, l, event_date=iso_days_ago(7),
                           bird_movements=[{"sex": "mixed", "quantity": 50, "avg_weight": 150}])
    assert await _destinatarios(test_database_url, "operational_event", dentro["id"]) == set()


# ── AC-R07 · AC-R09 — deduplicación ───────────────────────────────────────────

async def test_t_038_24_quien_cumple_tres_condiciones_recibe_una(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC-R07` y `AC-R09` · una persona, un aviso.

    El sujeto registra el evento **y** es administrador de la empresa: dos condiciones de
    `OD-08` a la vez. Debe recibir una fila, no dos.
    """
    empresa = seeded_ids["company_id"]
    # Un usuario tiene **un** rol, de modo que la única superposición posible en este modelo
    # es «originador + una función». Para construirla hace falta un rol administrativo que
    # además pueda registrar: se crea uno propio del test, con nombre prefijado para que la
    # limpieza lo retire y que contiene «administrador», que es por lo que el resolutor busca.
    rol = await _rol(client, auth_headers, f"{PREFIJO}Administrador de Planta", permisos=[
        {"module": "operations", "action": "read"},
        {"module": "operations", "action": "create"},
        {"module": "lots", "action": "read"},
    ])
    admin = await _usuario(client, auth_headers, rol, empresa)
    # `GA-REM-040` fase 6: el usuario nace sin cadenas concedidas y no vería ni su propio
    # evento. Se le configura la empresa, como hará un cliente real; lo que esta prueba mide
    # es la deduplicación de destinatarios, no el alcance por cadena.
    from tests.business_unit_fixtures import habilitar_y_conceder_todo

    await habilitar_y_conceder_todo(test_database_url, company_id=empresa,
                                    user_ids=[admin["id"]])

    lote = await _lote(client, auth_headers, seeded_ids)  # sin área: el admin no la usa
    cab_admin = _cabecera(admin["id"])
    r = await client.post("/api/v1/operations", headers=cab_admin, json={
        "lot_id": lote["id"], "farm_id": lote["farm_id"], "house_id": lote["house_id"],
        "event_type": "weight_recording", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 10, "avg_weight": 1800}]})
    assert r.status_code == 201, r.text
    evento = r.json()

    envio = await client.post(f"/api/v1/operations/{evento['id']}/submit", headers=cab_admin)
    assert envio.status_code == 200, envio.text
    await client.post(f"/api/v1/review/start/{evento['id']}", headers=auth_headers)
    rechazo = await client.post("/api/v1/approvals/reject", headers=auth_headers,
                                json={"event_id": evento["id"],
                                      "observations": "Motivo suficientemente largo"})
    assert rechazo.status_code == 200, rechazo.text

    cuantas = await _cuantas(test_database_url, "operational_event", evento["id"], admin["id"])
    assert cuantas == 1, (
        f"quien es originador y administrador a la vez recibió {cuantas} avisos, no 1"
    )


# ── AC-R08 — la empresa acota ─────────────────────────────────────────────────

async def test_t_038_25_las_mismas_funciones_en_otra_empresa_no_reciben(
    client, auth_headers, seeded_ids, motor, elenco, test_database_url
):
    """`AC-R08` · cero filtración.

    `CONTROL` los administradores, contralores y supervisores de la empresa del evento reciben.
    `TRATAMIENTO` los de la otra empresa, que tienen **los mismos roles**, no reciben nada.
    """
    ajena = seeded_ids["company_id_2"]
    forasteros = {
        f: (await _usuario(client, auth_headers,
                           await _rol(client, auth_headers, nombre), ajena))["id"]
        for f, nombre in (("admin", ROL_ADMIN), ("contralor", ROL_CONTRALOR),
                          ("supervisor", ROL_SUPERVISOR))
    }

    lote = await _lote(client, auth_headers, seeded_ids, elenco["area"]["id"])
    evento = await _evento(client, seeded_ids, lote)
    await _rechazar(client, auth_headers, seeded_ids, evento["id"])

    avisados = await _destinatarios(test_database_url, "operational_event", evento["id"])

    # CONTROL
    assert elenco["admin"]["id"] in avisados, "el administrador de la empresa no recibió"
    # TRATAMIENTO
    fugas = [f for f, uid in forasteros.items() if uid in avisados]
    assert fugas == [], f"funciones de otra empresa fueron notificadas: {fugas}"


# ── AC-R06 — el error de SAP conserva a su destinatario explícito ─────────────

async def test_t_038_26_el_error_de_sap_conserva_al_analista(
    client, auth_headers, seeded_ids, motor, elenco, monkeypatch, test_database_url
):
    """`AC-R06` · «Notificar al rol Analista SAP» (`docs/10 §6.2`) sigue vigente, y se suma."""
    from app.integrations.sap.adapter import SapExportResult, SapIntegrationAdapter
    from app.integrations.sap.service import SapService

    analista = await _usuario(client, auth_headers,
                              await _rol(client, auth_headers, "Analista SAP"),
                              seeded_ids["company_id"])

    lote = await _lote(client, auth_headers, seeded_ids, elenco["area"]["id"])
    evento = await _evento(client, seeded_ids, lote)
    operador = _cabecera(seeded_ids["user_operator_id"])
    await client.post(f"/api/v1/operations/{evento['id']}/submit", headers=operador)
    await client.post(f"/api/v1/review/start/{evento['id']}", headers=auth_headers)
    aprobado = await client.post("/api/v1/approvals/approve", headers=auth_headers,
                                 json={"event_id": evento["id"]})
    assert aprobado.status_code == 200, aprobado.text

    class Falla(SapIntegrationAdapter):
        delivers_to_sap = False

        async def export_consolidated(self, payload):
            return SapExportResult(success=False, message="Error simulado", status_code=503)

        async def check_connection(self) -> bool:
            return False

        async def get_adapter_name(self) -> str:
            return "falla"

    monkeypatch.setattr(SapService, "get_adapter", lambda self: Falla())
    await client.post("/api/v1/sap/consolidate", headers=auth_headers, json={})
    salida = await client.post("/api/v1/sap/export", headers=auth_headers, json={})
    assert salida.status_code in (200, 201), salida.text

    e = create_async_engine(test_database_url)
    try:
        async with e.connect() as c:
            avisados = set((await c.execute(text(
                "SELECT recipient_user_id FROM notifications "
                "WHERE notification_type = 'sap_send_failed'"))).scalars().all())
    finally:
        await e.dispose()

    assert analista["id"] in avisados, "se perdió el Analista SAP que `docs/10 §6.2` exige"
    for funcion in ("admin", "contralor", "supervisor"):
        assert elenco[funcion]["id"] in avisados, f"falta {funcion} en el aviso de SAP"


# ── AC-T01 · AC-T02 · AC-T03 · AC-T04 — el aviso de las 24 horas ─────────────

async def test_t_038_27_antes_de_24h_no_hay_aviso(
    client, auth_headers, seeded_ids, motor, elenco, test_database_url
):
    """`AC-T03` · antes del umbral normativo no existe notificación."""
    from app.notifications.sla import evaluar_revisiones_vencidas
    import app.database as database

    lote = await _lote(client, auth_headers, seeded_ids, elenco["area"]["id"])
    evento = await _evento(client, seeded_ids, lote)
    operador = _cabecera(seeded_ids["user_operator_id"])
    await client.post(f"/api/v1/operations/{evento['id']}/submit", headers=operador)

    async with database.async_session() as s:
        await evaluar_revisiones_vencidas(s)
        await s.commit()

    assert await _destinatarios(test_database_url, "operational_event", evento["id"]) == set()


async def test_t_038_28_al_cruzar_24h_se_avisa_una_sola_vez(
    client, auth_headers, seeded_ids, motor, elenco, test_database_url
):
    """`AC-T01`, `AC-T02` y `AC-T04` · el umbral está en el nombre del evento, y no se repite.

    La antigüedad se mide desde la **transición** a `pending_review`, que consta en la
    auditoría. No desde `updated_at`, que cambia con cualquier edición posterior y reiniciaría
    la cuenta.

    La recurrencia no está definida en ninguna fuente: se emite una vez. Reevaluar tres veces
    debe seguir dando una.
    """
    from app.audit.models import AuditLog
    from app.notifications.sla import evaluar_revisiones_vencidas
    import app.database as database

    lote = await _lote(client, auth_headers, seeded_ids, elenco["area"]["id"])
    evento = await _evento(client, seeded_ids, lote)
    operador = _cabecera(seeded_ids["user_operator_id"])
    await client.post(f"/api/v1/operations/{evento['id']}/submit", headers=operador)

    # Se envejece la marca de la transición: 25 h atrás, un lado del umbral.
    async with database.async_session() as s:
        await s.execute(
            AuditLog.__table__.update()
            .where(AuditLog.entity_id == str(evento["id"]),
                   AuditLog.new_state == "pending_review")
            .values(created_at=datetime.now(timezone.utc) - timedelta(hours=25)))
        await s.commit()

    async with database.async_session() as s:
        for _ in range(3):
            await evaluar_revisiones_vencidas(s)
        await s.commit()

    avisados = await _destinatarios(test_database_url, "operational_event", evento["id"])
    assert seeded_ids["user_operator_id"] in avisados, "no se avisó a quien registró"
    for funcion in ("admin", "contralor", "supervisor"):
        assert elenco[funcion]["id"] in avisados, f"falta {funcion}: {avisados}"

    repetidos = await _cuantas(test_database_url, "operational_event", evento["id"],
                               seeded_ids["user_operator_id"])
    assert repetidos == 1, f"reevaluar duplicó el aviso: {repetidos}"


# ── AC-A04 · AC-A05 · AC-A10 — el área acota al gerente y al supervisor ───────

async def test_t_039_10_el_gerente_y_el_supervisor_del_area_reciben(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC-A04`, `AC-A05` y `AC-A10` · el área del **evento**, no otra.

    `CONTROL` gerente y supervisor del área del lote reciben.
    `TRATAMIENTO` los de otra área de la **misma empresa** no reciben nada — que es
    exactamente lo que el modelo de áreas viene a evitar, y lo que ningún filtro de empresa
    habría detectado.
    """
    empresa = seeded_ids["company_id"]
    produccion = await _area(client, auth_headers, empresa)
    comercial = await _area(client, auth_headers, empresa)

    rol_gerente = await _rol(client, auth_headers, ROL_GERENTE)
    rol_supervisor = await _rol(client, auth_headers, ROL_SUPERVISOR)

    gerente_ok = await _en_area(client, auth_headers, rol_gerente, empresa, produccion["id"])
    super_ok = await _en_area(client, auth_headers, rol_supervisor, empresa, produccion["id"])
    gerente_no = await _en_area(client, auth_headers, rol_gerente, empresa, comercial["id"])
    super_no = await _en_area(client, auth_headers, rol_supervisor, empresa, comercial["id"])

    r = await client.post("/api/v1/lots", headers=auth_headers, json={
        "company_id": empresa, "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder", "sex": "mixed", "start_date": iso_days_ago(60),
        "area_id": produccion["id"]})
    assert r.status_code == 201, r.text
    lote = r.json()
    assert lote["area_id"] == produccion["id"], lote

    evento = await _evento(client, seeded_ids, lote)
    await _rechazar(client, auth_headers, seeded_ids, evento["id"])

    avisados = await _destinatarios(test_database_url, "operational_event", evento["id"])

    # CONTROL
    assert gerente_ok["id"] in avisados, "el gerente del área del lote no recibió"
    assert super_ok["id"] in avisados, "el supervisor del área del lote no recibió"
    # TRATAMIENTO
    assert gerente_no["id"] not in avisados, (
        "el gerente de otra área recibió un aviso que no le toca"
    )
    assert super_no["id"] not in avisados, (
        "el supervisor de otra área recibió un aviso que no le toca"
    )


async def test_t_039_11_el_gerente_de_otra_empresa_no_recibe(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC-A06` · aunque su área se llame igual y su rol sea el mismo."""
    empresa = seeded_ids["company_id"]
    ajena = seeded_ids["company_id_2"]

    propia = await _area(client, auth_headers, empresa)
    forastera = await _area(client, auth_headers, ajena)
    rol_gerente = await _rol(client, auth_headers, ROL_GERENTE)

    mio = await _en_area(client, auth_headers, rol_gerente, empresa, propia["id"])
    suyo = await _en_area(client, auth_headers, rol_gerente, ajena, forastera["id"])

    lote = (await client.post("/api/v1/lots", headers=auth_headers, json={
        "company_id": empresa, "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder", "sex": "mixed", "start_date": iso_days_ago(60),
        "area_id": propia["id"]})).json()
    evento = await _evento(client, seeded_ids, lote)
    await _rechazar(client, auth_headers, seeded_ids, evento["id"])

    avisados = await _destinatarios(test_database_url, "operational_event", evento["id"])
    assert mio["id"] in avisados
    assert suyo["id"] not in avisados, "un gerente de otra empresa fue notificado"


async def test_t_039_12_un_gerente_sin_area_no_es_gerente_de_nada(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC-A04` · la capacidad la da el rol; la pertenencia, `area_id`. Hacen falta las dos.

    Sin este filtro, cualquiera con nombre de rol de gerencia recibiría todo lo de la empresa
    y el modelo de áreas no serviría para nada.
    """
    empresa = seeded_ids["company_id"]
    area = await _area(client, auth_headers, empresa)
    rol_gerente = await _rol(client, auth_headers, ROL_GERENTE)

    sin_area = await _usuario(client, auth_headers, rol_gerente, empresa)
    assert sin_area.get("area_id") is None

    lote = (await client.post("/api/v1/lots", headers=auth_headers, json={
        "company_id": empresa, "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder", "sex": "mixed", "start_date": iso_days_ago(60),
        "area_id": area["id"]})).json()
    evento = await _evento(client, seeded_ids, lote)
    await _rechazar(client, auth_headers, seeded_ids, evento["id"])

    avisados = await _destinatarios(test_database_url, "operational_event", evento["id"])
    assert sin_area["id"] not in avisados, (
        "un usuario con rol de gerencia y sin área recibió el aviso de un área"
    )


async def test_t_039_13_un_usuario_inactivo_no_recibe(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC-A07` · quien ya no trabaja aquí no debe seguir recibiendo avisos operativos."""
    empresa = seeded_ids["company_id"]
    area = await _area(client, auth_headers, empresa)
    gerente = await _en_area(client, auth_headers,
                             await _rol(client, auth_headers, ROL_GERENTE), empresa, area["id"])

    baja = await client.put(f"/api/v1/users/{gerente['id']}", headers=auth_headers,
                            json={"is_active": False})
    assert baja.status_code == 200, baja.text

    lote = (await client.post("/api/v1/lots", headers=auth_headers, json={
        "company_id": empresa, "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder", "sex": "mixed", "start_date": iso_days_ago(60),
        "area_id": area["id"]})).json()
    evento = await _evento(client, seeded_ids, lote)
    await _rechazar(client, auth_headers, seeded_ids, evento["id"])

    avisados = await _destinatarios(test_database_url, "operational_event", evento["id"])
    assert gerente["id"] not in avisados, "un usuario inactivo recibió un aviso"


# ── AC-C16 — la edición no reinicia las 24 horas ─────────────────────────────

async def test_t_038_29_editar_el_evento_no_reinicia_la_cuenta(
    client, auth_headers, seeded_ids, motor, elenco, test_database_url
):
    """`AC-C16` · la marca es la de la transición, no `updated_at`.

    Con `updated_at`, un evento editado a las 23 horas volvería a empezar y no avisaría
    **nunca** mientras alguien lo tocara a diario. Aquí se envejece la transición a 25 h y
    después se edita el evento: la cuenta debe seguir valiendo.
    """
    from app.audit.models import AuditLog
    from app.notifications.sla import evaluar_revisiones_vencidas
    import app.database as database

    lote = await _lote(client, auth_headers, seeded_ids, elenco["area"]["id"])
    evento = await _evento(client, seeded_ids, lote)
    operador = _cabecera(seeded_ids["user_operator_id"])
    await client.post(f"/api/v1/operations/{evento['id']}/submit", headers=operador)

    async with database.async_session() as s:
        await s.execute(
            AuditLog.__table__.update()
            .where(AuditLog.entity_id == str(evento["id"]),
                   AuditLog.new_state == "pending_review")
            .values(created_at=datetime.now(timezone.utc) - timedelta(hours=25)))
        await s.commit()

    # Cualquier escritura posterior mueve `updated_at` a ahora mismo. Se hace en la base
    # porque el flujo no permite editar un evento ya en revisión, y lo que importa aquí es el
    # efecto sobre la marca, no el camino que la mueve.
    from app.operations.models import OperationalEvent

    async with database.async_session() as s2:
        await s2.execute(
            OperationalEvent.__table__.update()
            .where(OperationalEvent.id == evento["id"])
            .values(updated_at=datetime.now(timezone.utc)))
        await s2.commit()

    async with database.async_session() as s:
        await evaluar_revisiones_vencidas(s)
        await s.commit()

    avisados = await _destinatarios(test_database_url, "operational_event", evento["id"])
    assert seeded_ids["user_operator_id"] in avisados, (
        "editar el evento reinició la cuenta de las 24 horas"
    )

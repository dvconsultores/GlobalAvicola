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


async def _usuario(client, cab, role_id: int, company_id: int) -> dict:
    nombre = f"{PREFIJO}{uuid.uuid4().hex[:8]}"
    r = await client.post("/api/v1/users", headers=cab, json={
        "username": nombre, "first_name": "Test", "last_name": nombre,
        "email": f"{nombre}@example.com", "password": uuid.uuid4().hex,
        "role_id": role_id, "company_id": company_id, "view_type": "web",
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _lote(client, cab, seeded_ids) -> dict:
    r = await client.post("/api/v1/lots", headers=cab, json={
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"], "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder", "sex": "mixed", "start_date": iso_days_ago(60),
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


@pytest_asyncio.fixture
async def elenco(client, auth_headers, seeded_ids, motor):
    """Un usuario por cada función que `OD-08` nombra y que tiene rol real."""
    empresa = seeded_ids["company_id"]
    return {
        "admin": await _usuario(client, auth_headers,
                                await _rol(client, auth_headers, ROL_ADMIN), empresa),
        "contralor": await _usuario(client, auth_headers,
                                    await _rol(client, auth_headers, ROL_CONTRALOR), empresa),
        "supervisor": await _usuario(client, auth_headers,
                                     await _rol(client, auth_headers, ROL_SUPERVISOR), empresa),
    }


# ── AC-R01 · AC-R02 · AC-R03 · AC-R05 · AC-R06 ────────────────────────────────

async def test_t_038_20_el_rechazo_llega_a_las_cinco_funciones(
    client, auth_headers, seeded_ids, motor, elenco, test_database_url
):
    """`AC-R01`…`AC-R03`, `AC-R05` y `AC-R06` · la unión de `OD-08`, sin perder al operador.

    «Registro rechazado (notificar al operador)» es una exigencia previa de `docs/02 §3.14`.
    `OD-08` **amplía**; una decisión que amplía no retira.
    """
    lote = await _lote(client, auth_headers, seeded_ids)
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
    lote = await _lote(client, auth_headers, seeded_ids)
    await _evento(client, seeded_ids, lote, tipo="bird_reception",
                  bird_movements=[{"sex": "mixed", "quantity": 1000}])
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
        "genetic_line_id": linea["id"], "start_date": iso_days_ago(22)})
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

    lote = await _lote(client, auth_headers, seeded_ids)
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

    lote = await _lote(client, auth_headers, seeded_ids)
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

    lote = await _lote(client, auth_headers, seeded_ids)
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

    lote = await _lote(client, auth_headers, seeded_ids)
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

    lote = await _lote(client, auth_headers, seeded_ids)
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

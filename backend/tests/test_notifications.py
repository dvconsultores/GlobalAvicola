"""Notificaciones internas — `GA-REM-038`, decisión `OD-07`.

Cubre `AC02`…`AC15`.

`docs/02 §3.14` enumera seis tipos de aviso. Dos tienen disparador **y** destinatario escritos
en una fuente normativa; los otros cuatro no dicen a quién avisar, y elegirlo habría sido
inventar requisito (`OD-08`). Aquí se certifican los dos que sí:

    record_rejected   review/service.py · «notificar al operador»          docs/02 §3.14
    sap_send_failed   sap/service.py    · «Notificar al rol Analista SAP»  docs/10 §6.2

La bandeja es **de una persona**. Por eso el aislamiento se comprueba dos veces: contra otro
usuario de la misma empresa y contra otra empresa. Filtrar solo por empresa dejaría a cada
compañero leer los avisos de los demás.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import Lot
from tests.time_reference import iso_days_ago, recent_event_date

PREFIJO = "NOTIF-TEST-"


def _cabecera(user_id: int) -> dict:
    from app.auth.security import create_access_token
    return {"Authorization": "Bearer " + create_access_token(data={"sub": str(user_id)})}


@pytest_asyncio.fixture
async def motor(test_database_url):
    """Limpieza. Habla por SQL con `notifications` porque esta suite se escribió **antes**
    de que la tabla existiera: importar el modelo la habría hecho fallar al recolectarse, y
    un error de importación no es un rojo que demuestre nada."""
    e = create_async_engine(test_database_url)

    # `/sap/consolidate` consolida **todos** los eventos aprobados de la empresa, incluidos
    # los sembrados: no admite acotar. Sin deshacerlo, esta suite dejaba cargas con la misma
    # clave idempotente que `test_sap.py` intenta crear después, y aquélla fallaba por culpa
    # de ésta. Se anota la marca de agua y se retira lo posterior.
    from app.integrations.sap.models import (
        ConsolidatedMovement, SapPayload, SapSyncJob,
    )
    async with e.connect() as c:
        marca = {
            "payload": (await c.execute(select(func.max(SapPayload.id)))).scalar() or 0,
            "consolidado": (await c.execute(
                select(func.max(ConsolidatedMovement.id)))).scalar() or 0,
            "job": (await c.execute(select(func.max(SapSyncJob.id)))).scalar() or 0,
        }

    yield e
    from app.audit.models import AuditLog
    from app.auth.models import User
    from app.operations.models import BirdMovement, OperationalAlert, OperationalEvent

    async with e.begin() as c:
        existe = (await c.execute(text(
            "SELECT to_regclass('public.notifications')"))).scalar()
        if existe:
            await c.execute(text(
                "DELETE FROM notifications WHERE recipient_user_id IN "
                "(SELECT id FROM users WHERE username LIKE :p)"), {"p": f"{PREFIJO}%"})
            await c.execute(text(
                "DELETE FROM notifications WHERE payload::text LIKE :p"), {"p": f"%{PREFIJO}%"})

        lotes = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        eventos = (await c.execute(select(OperationalEvent.id).where(
            OperationalEvent.lot_id.in_(lotes or [-1])))).scalars().all()
        if existe and eventos:
            await c.execute(text(
                "DELETE FROM notifications WHERE related_entity_type = 'operational_event' "
                "AND related_entity_id = ANY(:ids)"), {"ids": eventos})
        # Todo lo que el export creó por encima de la marca de agua, sin importar a qué lote
        # apunte: consolidó también los eventos sembrados.
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

        if eventos:
            from app.review.models import ApprovalAction
            await c.execute(delete(ApprovalAction).where(ApprovalAction.event_id.in_(eventos)))
            await c.execute(delete(BirdMovement).where(BirdMovement.event_id.in_(eventos)))
            await c.execute(delete(OperationalAlert).where(
                OperationalAlert.event_id.in_(eventos)))
            await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
        if lotes:
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(lotes)))
            await c.execute(delete(Lot).where(Lot.id.in_(lotes)))
        await c.execute(delete(User).where(User.username.like(f"{PREFIJO}%")))
    await e.dispose()


async def _lote(client, cab, seeded_ids) -> dict:
    r = await client.post("/api/v1/lots", headers=cab, json={
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"], "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder", "sex": "mixed", "start_date": iso_days_ago(60),
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _evento_del_operador(client, seeded_ids, lote) -> dict:
    """Un evento registrado **por el operador**: es quien debe recibir el aviso."""
    operador = _cabecera(seeded_ids["user_operator_id"])
    r = await client.post("/api/v1/operations", headers=operador, json={
        "lot_id": lote["id"], "farm_id": lote["farm_id"], "house_id": lote["house_id"],
        "event_type": "weight_recording", "event_date": recent_event_date(),
        "bird_movements": [{"sex": "mixed", "quantity": 10, "avg_weight": 1800}],
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _a_revision(client, seeded_ids, event_id):
    """`registered` → `pending_review`. Lo hace el propio operador: es su registro."""
    operador = _cabecera(seeded_ids["user_operator_id"])
    r = await client.post(f"/api/v1/operations/{event_id}/submit", headers=operador)
    assert r.status_code in (200, 201), r.text
    return r


async def _rechazar(client, cab_admin, event_id, motivo="Datos incoherentes en el pesaje"):
    inicio = await client.post(f"/api/v1/review/start/{event_id}", headers=cab_admin)
    assert inicio.status_code in (200, 201), inicio.text
    return await client.post("/api/v1/approvals/reject", headers=cab_admin,
                             json={"event_id": event_id, "observations": motivo})


async def _bandeja(client, cab, **params):
    from urllib.parse import urlencode
    q = f"?{urlencode(params)}" if params else ""
    return await client.get(f"/api/v1/notifications{q}", headers=cab)


# ── AC03 · AC05 · AC09 — el rechazo avisa al operador ─────────────────────────

async def test_t_038_01_rechazar_avisa_a_quien_registro(
    client, auth_headers, seeded_ids, motor
):
    """`AC03`, `AC05` y `AC09` · «Registro rechazado (notificar al operador)», literal.

    El destinatario es `registered_by_id`, no quien rechaza. Se comprueban los dos lados: si
    el destinatario se resolviera mal y llegara al propio actor, avisar al actor pasaría por
    funcionar.
    """
    lote = await _lote(client, auth_headers, seeded_ids)
    evento = await _evento_del_operador(client, seeded_ids, lote)

    await _a_revision(client, seeded_ids, evento["id"])
    r = await _rechazar(client, auth_headers, evento["id"])
    assert r.status_code == 200, r.text

    operador = _cabecera(seeded_ids["user_operator_id"])
    suyas = await _bandeja(client, operador)
    assert suyas.status_code == 200, suyas.text
    mias = [n for n in suyas.json()
            if n["related_entity_id"] == evento["id"]
            and n["related_entity_type"] == "operational_event"]
    assert len(mias) == 1, mias

    aviso = mias[0]
    assert aviso["notification_type"] == "record_rejected", aviso
    assert aviso["read_at"] is None, aviso
    assert aviso["company_id"] == seeded_ids["company_id"], aviso

    # Y quien rechazó no recibe nada: no es el operador.
    del_que_rechaza = await _bandeja(client, auth_headers)
    assert del_que_rechaza.status_code == 200
    ajenas = [n for n in del_que_rechaza.json()
              if n["related_entity_id"] == evento["id"]]
    assert ajenas == [], (
        "el aviso llegó a quien rechazó en lugar de a quien registró"
    )


# ── AC06 — lo que no ocurre no avisa ──────────────────────────────────────────

async def test_t_038_02_un_rechazo_que_falla_no_avisa(
    client, auth_headers, seeded_ids, motor
):
    """`AC06` · una notificación de algo que no llegó a pasar es una mentira.

    Se rechaza un evento que **no está en estado rechazable**: la llamada falla y la bandeja
    del operador queda igual que antes.
    """
    lote = await _lote(client, auth_headers, seeded_ids)
    evento = await _evento_del_operador(client, seeded_ids, lote)
    operador = _cabecera(seeded_ids["user_operator_id"])

    inicial = await _bandeja(client, operador)
    assert inicial.status_code == 200, inicial.text
    antes = len(inicial.json())

    # Sin pasar por `review/start`, el evento sigue en `registered` y no es rechazable.
    fallido = await client.post("/api/v1/approvals/reject", headers=auth_headers,
                                json={"event_id": evento["id"], "observations": "motivo suficientemente largo"})
    assert fallido.status_code == 400, fallido.text

    posterior = await _bandeja(client, operador)
    assert posterior.status_code == 200, posterior.text
    assert len(posterior.json()) == antes, "una operación rechazada dejó notificación"


async def test_t_038_03_consultar_la_bandeja_no_crea_nada(
    client, auth_headers, seeded_ids, motor
):
    """`AC07` · solo los eventos del negocio crean notificaciones."""
    lote = await _lote(client, auth_headers, seeded_ids)
    evento = await _evento_del_operador(client, seeded_ids, lote)
    await _a_revision(client, seeded_ids, evento["id"])
    await _rechazar(client, auth_headers, evento["id"])

    operador = _cabecera(seeded_ids["user_operator_id"])
    inicial = await _bandeja(client, operador, limit=100)
    assert inicial.status_code == 200, inicial.text
    # El aviso del rechazo debe estar: sin él, «no crece» se cumpliría con la bandeja vacía.
    assert any(n["related_entity_id"] == evento["id"] for n in inicial.json()), inicial.json()
    primera = len(inicial.json())

    for _ in range(3):
        await _bandeja(client, operador, limit=100)
    final = await _bandeja(client, operador, limit=100)
    assert final.status_code == 200, final.text
    assert len(final.json()) == primera


# ── AC11 · AC12 · AC13 — leer y marcar ────────────────────────────────────────

async def test_t_038_04_el_contador_de_no_leidas_es_exacto(
    client, auth_headers, seeded_ids, motor
):
    """`AC12` · tres sin leer y dos leídas dan tres. No «al menos una»."""
    operador = _cabecera(seeded_ids["user_operator_id"])
    base = (await client.get("/api/v1/notifications/unread-count",
                             headers=operador)).json()["unread"]

    creadas = []
    for _ in range(5):
        lote = await _lote(client, auth_headers, seeded_ids)
        evento = await _evento_del_operador(client, seeded_ids, lote)
        await _a_revision(client, seeded_ids, evento["id"])
        await _rechazar(client, auth_headers, evento["id"])
        creadas.append(evento["id"])

    hechas = (await _bandeja(client, operador, limit=100)).json()
    mias = [n for n in hechas if n["related_entity_id"] in creadas]
    assert len(mias) == 5, mias

    # Se leen dos.
    for n in mias[:2]:
        marcada = await client.patch(f"/api/v1/notifications/{n['id']}/read",
                                     headers=operador)
        assert marcada.status_code == 200, marcada.text
        assert marcada.json()["read_at"] is not None

    r = await client.get("/api/v1/notifications/unread-count", headers=operador)
    assert r.status_code == 200, r.text
    assert r.json()["unread"] == base + 3, (r.json(), base)


async def test_t_038_05_marcar_leida_dos_veces_deja_el_mismo_estado(
    client, auth_headers, seeded_ids, motor
):
    """`AC13` · repetir la llamada no altera el resultado ni el contador."""
    lote = await _lote(client, auth_headers, seeded_ids)
    evento = await _evento_del_operador(client, seeded_ids, lote)
    await _a_revision(client, seeded_ids, evento["id"])
    await _rechazar(client, auth_headers, evento["id"])

    operador = _cabecera(seeded_ids["user_operator_id"])
    aviso = next(n for n in (await _bandeja(client, operador, limit=100)).json()
                 if n["related_entity_id"] == evento["id"])

    primera = await client.patch(f"/api/v1/notifications/{aviso['id']}/read",
                                 headers=operador)
    assert primera.status_code == 200, primera.text
    momento = primera.json()["read_at"]
    assert momento is not None

    conteo = (await client.get("/api/v1/notifications/unread-count",
                               headers=operador)).json()["unread"]

    segunda = await client.patch(f"/api/v1/notifications/{aviso['id']}/read",
                                 headers=operador)
    assert segunda.status_code == 200, segunda.text
    assert segunda.json()["read_at"] == momento, "la segunda llamada movió la marca de lectura"
    assert (await client.get("/api/v1/notifications/unread-count",
                             headers=operador)).json()["unread"] == conteo


async def test_t_038_06_la_bandeja_pagina_y_da_el_total(
    client, auth_headers, seeded_ids, motor
):
    """`AC11` · el total viaja en cabecera, como en los maestros (`R-89`)."""
    operador = _cabecera(seeded_ids["user_operator_id"])
    for _ in range(3):
        lote = await _lote(client, auth_headers, seeded_ids)
        evento = await _evento_del_operador(client, seeded_ids, lote)
        await _a_revision(client, seeded_ids, evento["id"])
        await _rechazar(client, auth_headers, evento["id"])

    r = await _bandeja(client, operador, limit=2)
    assert r.status_code == 200, r.text
    assert len(r.json()) == 2, "la página no respeta el límite"
    total = r.headers.get("x-total-count")
    assert total is not None, "la bandeja no expone el total"
    assert int(total) >= 3, total


# ── AC14 · AC15 — la bandeja es de una persona ────────────────────────────────

async def test_t_038_07_otro_usuario_de_la_misma_empresa_no_la_lee(
    client, http_client, auth_headers, seeded_ids, motor
):
    """`AC14` · filtrar solo por empresa dejaría leer los avisos de los compañeros.

    `CONTROL` el destinatario la lee. `TRATAMIENTO` un usuario válido de la **misma** empresa,
    no. El sujeto negativo es el aprobador, con empresa propia: el Super Administrador está
    exento de tenencia y haría pasar la prueba sin comprobar nada.
    """
    lote = await _lote(client, auth_headers, seeded_ids)
    evento = await _evento_del_operador(client, seeded_ids, lote)
    await _a_revision(client, seeded_ids, evento["id"])
    await _rechazar(client, auth_headers, evento["id"])

    operador = _cabecera(seeded_ids["user_operator_id"])
    aviso = next(n for n in (await _bandeja(client, operador, limit=100)).json()
                 if n["related_entity_id"] == evento["id"])

    # CONTROL
    propio = await client.get(f"/api/v1/notifications/{aviso['id']}", headers=operador)
    assert propio.status_code == 200, propio.text

    # TRATAMIENTO · mismo tenant, otra persona.
    otro = _cabecera(seeded_ids["user_approver_id"])
    ajeno = await http_client.get(f"/api/v1/notifications/{aviso['id']}", headers=otro)
    assert ajeno.status_code == 404, (
        f"un compañero de empresa leyó la notificación de otro: {ajeno.text}"
    )

    # Y tampoco aparece en su bandeja.
    suya = await http_client.get("/api/v1/notifications?limit=100", headers=otro)
    assert suya.status_code == 200, suya.text
    assert all(n["id"] != aviso["id"] for n in suya.json()), (
        "la notificación ajena aparece en la bandeja de otro usuario"
    )


async def test_t_038_08_otra_empresa_no_ve_nada(
    client, http_client, auth_headers, seeded_ids, motor
):
    """`AC15` · cero filtración entre empresas."""
    lote = await _lote(client, auth_headers, seeded_ids)
    evento = await _evento_del_operador(client, seeded_ids, lote)
    await _a_revision(client, seeded_ids, evento["id"])
    await _rechazar(client, auth_headers, evento["id"])

    operador = _cabecera(seeded_ids["user_operator_id"])
    aviso = next(n for n in (await _bandeja(client, operador, limit=100)).json()
                 if n["related_entity_id"] == evento["id"])

    forastero = _cabecera(seeded_ids["user_other_company_id"])
    directo = await http_client.get(f"/api/v1/notifications/{aviso['id']}",
                                    headers=forastero)
    assert directo.status_code == 404, directo.text

    lista = await http_client.get("/api/v1/notifications?limit=100", headers=forastero)
    assert lista.status_code == 200, lista.text
    assert all(n["id"] != aviso["id"] for n in lista.json())


# ── AC04 · AC10 — el fallo de SAP avisa al Analista SAP ───────────────────────

async def _analista_sap(client, auth_headers, seeded_ids) -> dict:
    """Un usuario con el rol que `docs/10 §6.2` nombra."""
    from app.auth.models import Role
    import app.database as database

    async with database.async_session() as s:
        rol = (await s.execute(
            select(Role).where(Role.name == "Analista SAP"))).scalar_one_or_none()
    assert rol is not None, "la migración `l2m3n4o5p6q7` debe crear el rol «Analista SAP»"

    usuario = f"{PREFIJO}{uuid.uuid4().hex[:8]}"
    r = await client.post("/api/v1/users", headers=auth_headers, json={
        "username": usuario, "first_name": "Analista", "last_name": "SAP",
        "email": f"{usuario}@example.com", "password": uuid.uuid4().hex,
        "role_id": rol.id, "company_id": seeded_ids["company_id"], "view_type": "web",
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _forzar_fallo_sap(client, auth_headers, seeded_ids, monkeypatch):
    """Consolida y exporta con un adaptador que rechaza. El camino de fallo es el real
    (`sap/service.py:367`); lo único forzado es el veredicto del adaptador, que es
    exactamente para lo que existe un adaptador."""
    from app.integrations.sap.adapter import SapExportResult, SapIntegrationAdapter
    from app.integrations.sap.service import SapService

    class AdaptadorQueFalla(SapIntegrationAdapter):
        delivers_to_sap = False

        async def export_consolidated(self, payload):
            return SapExportResult(success=False, message="Error simulado de envío",
                                   status_code=503)

        async def check_connection(self) -> bool:
            return False

        async def get_adapter_name(self) -> str:
            return "falla"

    monkeypatch.setattr(SapService, "get_adapter", lambda self: AdaptadorQueFalla())

    await client.post("/api/v1/sap/consolidate", headers=auth_headers, json={})
    return await client.post("/api/v1/sap/export", headers=auth_headers, json={})


async def test_t_038_09_el_fallo_de_envio_avisa_al_analista_sap(
    client, auth_headers, seeded_ids, motor, monkeypatch
):
    """`AC04` y `AC10` · «Notificar al rol Analista SAP», `docs/10 §6.2` literal.

    Es una regla **por rol**, así que produce una notificación por cada usuario de ese rol:
    la bandeja es personal y una fila compartida no podría marcarse leída por uno sin
    marcarla por todos.
    """
    analista = await _analista_sap(client, auth_headers, seeded_ids)

    # Un evento aprobado que consolidar, para que haya algo que exportar.
    lote = await _lote(client, auth_headers, seeded_ids)
    evento = await _evento_del_operador(client, seeded_ids, lote)
    await _a_revision(client, seeded_ids, evento["id"])
    await client.post(f"/api/v1/review/start/{evento['id']}", headers=auth_headers)
    aprobado = await client.post("/api/v1/approvals/approve", headers=auth_headers,
                                 json={"event_id": evento["id"]})
    assert aprobado.status_code == 200, aprobado.text

    salida = await _forzar_fallo_sap(client, auth_headers, seeded_ids, monkeypatch)
    assert salida.status_code in (200, 201), salida.text

    cab = _cabecera(analista["id"])
    suyas = (await _bandeja(client, cab, limit=100)).json()
    fallos = [n for n in suyas if n["notification_type"] == "sap_send_failed"]
    assert fallos, "el analista SAP no recibió aviso del fallo de envío"
    assert fallos[0]["related_entity_type"] == "sap_payload", fallos[0]
    assert fallos[0]["read_at"] is None


async def test_t_038_10_un_reintento_fallido_no_duplica_el_aviso(
    client, auth_headers, seeded_ids, motor, monkeypatch
):
    """`AC08` · el mismo problema sin leer no se anuncia dos veces.

    El envío reintenta hasta tres veces. Si cada intento dejara su fila, la bandeja acabaría
    contando reintentos en vez de problemas.
    """
    analista = await _analista_sap(client, auth_headers, seeded_ids)
    lote = await _lote(client, auth_headers, seeded_ids)
    evento = await _evento_del_operador(client, seeded_ids, lote)
    await _a_revision(client, seeded_ids, evento["id"])
    await client.post(f"/api/v1/review/start/{evento['id']}", headers=auth_headers)
    await client.post("/api/v1/approvals/approve", headers=auth_headers,
                      json={"event_id": evento["id"]})

    await _forzar_fallo_sap(client, auth_headers, seeded_ids, monkeypatch)
    cab = _cabecera(analista["id"])
    primera = [n for n in (await _bandeja(client, cab, limit=100)).json()
               if n["notification_type"] == "sap_send_failed"]
    assert primera, "no se creó el primer aviso"

    reintento = await client.post("/api/v1/sap/retry", headers=auth_headers, json={})
    assert reintento.status_code in (200, 201), reintento.text

    segunda = [n for n in (await _bandeja(client, cab, limit=100)).json()
               if n["notification_type"] == "sap_send_failed"]
    assert len(segunda) == len(primera), (
        f"el reintento duplicó el aviso: {len(primera)} → {len(segunda)}"
    )


# ── AC02 — ningún canal externo ───────────────────────────────────────────────

def test_t_038_11_no_se_introduce_ningun_canal_externo():
    """`AC02` · `OD-07` deja fuera correo, WhatsApp, SMS y push.

    Se comprueba sobre el esquema y las dependencias declaradas, no sobre la intención: una
    tabla de plantillas, una cola de correo o un cliente SMTP serían la huella inevitable de
    haber empezado por la puerta de atrás.
    """
    import pathlib

    from app.database import Base

    sospechosas = [t for t in Base.metadata.tables if any(
        p in t for p in ("email", "smtp", "sms", "whatsapp", "push", "telegram",
                         "subscription", "delivery_attempt"))]
    assert sospechosas == [], f"canal externo en el esquema: {sospechosas}"

    declaradas = pathlib.Path("pyproject.toml").read_text().lower()
    externas = [p for p in ("aiosmtplib", "sendgrid", "twilio", "firebase",
                            "pywebpush", "python-telegram-bot", "mailgun")
                if p in declaradas]
    assert externas == [], f"dependencia de canal externo declarada: {externas}"

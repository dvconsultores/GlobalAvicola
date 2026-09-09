"""«Lote próximo a cierre» — `GA-REM-038` enmienda B, decisión `OD-08`.

Cubre `AC-C01`…`AC-C14`.

`OD-08` fijó qué significa «próximo»: **faltan 3 días** para la fecha prevista de cierre. Con
eso, el sexto tipo de `docs/02 §3.14` deja de estar bloqueado.

Dos cosas que estas pruebas fijan y conviene no perder:

    planned_close_date   cuándo se PREVÉ cerrar     lo pone quien planifica
    end_date             cuándo se cerró DE VERDAD  lo fija `close_lot`

Y la ventana `0..3` en vez de la igualdad `== 3`: con igualdad, un evaluador que no corriera
exactamente ese día no avisaría nunca.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import Lot
from tests.time_reference import iso_days_ago, reference_today

PREFIJO = "PC-TEST-"


def _en_dias(n: int) -> str:
    """Fecha de negocio a `n` días vista, en el marco que usa el producto.

    `reference_today()` es el día local del servidor, que es lo que `close_lot` llama «hoy».
    La comparación es día contra día: `R-80` —mezclar un instante UTC con un día local— no
    interviene aquí.
    """
    return (reference_today() + timedelta(days=n)).isoformat()


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.auth.models import User
    from app.operations.models import BirdMovement, OperationalAlert, OperationalEvent

    async with e.begin() as c:
        lotes = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if lotes:
            existe = (await c.execute(
                text("SELECT to_regclass('public.notifications')"))).scalar()
            eventos = (await c.execute(select(OperationalEvent.id).where(
                OperationalEvent.lot_id.in_(lotes)))).scalars().all()
            if existe:
                await c.execute(text(
                    "DELETE FROM notifications WHERE related_entity_type = 'lot' "
                    "AND related_entity_id = ANY(:ids)"), {"ids": lotes})
                if eventos:
                    await c.execute(text(
                        "DELETE FROM notifications WHERE "
                        "related_entity_type = 'operational_event' "
                        "AND related_entity_id = ANY(:ids)"), {"ids": eventos})
            if eventos:
                await c.execute(delete(BirdMovement).where(
                    BirdMovement.event_id.in_(eventos)))
                await c.execute(delete(OperationalAlert).where(
                    OperationalAlert.event_id.in_(eventos)))
                await c.execute(delete(OperationalEvent).where(
                    OperationalEvent.id.in_(eventos)))
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(lotes)))
            await c.execute(delete(Lot).where(Lot.id.in_(lotes)))
        # Enmienda H: el usuario de `test_t_038_49` recibe una concesión de unidad; se retira
        # antes que el usuario (clave foránea `user_business_units.user_id`).
        from app.business_units.models import UserBusinessUnit
        usuarios = (await c.execute(
            select(User.id).where(User.username.like(f"{PREFIJO}%")))).scalars().all()
        if usuarios:
            await c.execute(delete(UserBusinessUnit).where(UserBusinessUnit.user_id.in_(usuarios)))
        await c.execute(delete(User).where(User.username.like(f"{PREFIJO}%")))
        from app.auth.models import Permission, Role
        roles = (await c.execute(
            select(Role.id).where(Role.name.like(f"{PREFIJO}%")))).scalars().all()
        if roles:
            await c.execute(delete(Permission).where(Permission.role_id.in_(roles)))
            await c.execute(delete(Role).where(Role.id.in_(roles)))
    await e.dispose()


async def _lote(client, cab, seeded_ids, **extra):
    cuerpo = {
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"], "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder", "sex": "mixed", "start_date": iso_days_ago(60),
    }
    cuerpo.update(extra)
    return await client.post("/api/v1/lots", headers=cab, json=cuerpo)


async def _evaluar(veces: int = 1) -> None:
    """Ejecuta el evaluador periódico, como haría la tarea de fondo."""
    import app.database as database
    from app.notifications.sla import evaluar_lotes_proximos_a_cierre

    async with database.async_session() as s:
        for _ in range(veces):
            await evaluar_lotes_proximos_a_cierre(s)
        await s.commit()


async def _avisos(test_database_url, lot_id: int) -> int:
    e = create_async_engine(test_database_url)
    try:
        async with e.connect() as c:
            return (await c.execute(text(
                "SELECT count(*) FROM notifications WHERE notification_type = 'lot_near_close' "
                "AND related_entity_type = 'lot' AND related_entity_id = :i"),
                {"i": lot_id})).scalar()
    finally:
        await e.dispose()


# ── AC-C01 · AC-C02 · AC-C03 · AC-C04 — el campo ──────────────────────────────

async def test_t_038_40_la_fecha_prevista_se_persiste(
    client, auth_headers, seeded_ids, motor
):
    """`AC-C01` y `AC-C03` · una fecha prevista futura viaja y vuelve.

    Es el patrón de `R-47`: un campo que el cliente envía y el esquema descarta en silencio
    devuelve `201` y no llega a ninguna parte.
    """
    prevista = _en_dias(30)
    r = await _lote(client, auth_headers, seeded_ids, planned_close_date=prevista)
    assert r.status_code == 201, r.text
    assert r.json()["planned_close_date"] is not None, "la fecha prevista se descartó"
    assert r.json()["planned_close_date"].startswith(prevista), r.json()

    leido = await client.get(f"/api/v1/lots/{r.json()['id']}", headers=auth_headers)
    assert leido.status_code == 200, leido.text
    assert leido.json()["planned_close_date"].startswith(prevista)


async def test_t_038_41_los_lotes_sin_fecha_prevista_se_admiten(
    client, auth_headers, seeded_ids, motor
):
    """`AC-C02` · hay lotes anteriores a esta spec. Inventarles una fecha sería fabricar dato."""
    r = await _lote(client, auth_headers, seeded_ids)
    assert r.status_code == 201, r.text
    assert r.json()["planned_close_date"] is None, r.json()


async def test_t_038_42_la_fecha_real_de_cierre_no_es_la_prevista(
    client, auth_headers, seeded_ids, motor
):
    """`AC-C04` · `end_date` conserva su significado. Planificar no cierra nada.

    `R-73` y `R-75` fijaron esa semántica y siguen vigentes: reutilizar `end_date` para
    pronosticar habría avisado de algo que ya ocurrió.
    """
    prevista = _en_dias(10)
    lote = (await _lote(client, auth_headers, seeded_ids,
                        planned_close_date=prevista)).json()

    assert lote["end_date"] is None, "planificar no puede fijar la fecha real de cierre"
    assert lote["status"] == "active"

    leido = (await client.get(f"/api/v1/lots/{lote['id']}", headers=auth_headers)).json()
    assert leido["planned_close_date"].startswith(prevista)
    assert leido["end_date"] is None


# ── AC-C05 · AC-C06 · AC-C07 — la ventana ─────────────────────────────────────

@pytest.mark.parametrize("dias,esperado", [
    (4, 0),   # `AC-C07` · todavía no es «próximo»
    (3, 1),   # `AC-C05` · el umbral exacto que `OD-08` fijó
    (2, 1),   # `AC-C06` · recuperación: el evaluador pudo no haber corrido antes
    (1, 1),
    (0, 1),   # el mismo día previsto sigue siendo «próximo»
])
async def test_t_038_43_la_ventana_es_de_cero_a_tres_dias(
    client, auth_headers, seeded_ids, motor, test_database_url, dias, esperado
):
    """`AC-C05`…`AC-C07` · la condición es una ventana, no una igualdad.

    Con `== 3` el aviso solo saldría si el evaluador corriera exactamente ese día. Si el
    sistema estuvo apagado, no saldría nunca — y un aviso que no sale es un aviso que no
    existe.
    """
    lote = (await _lote(client, auth_headers, seeded_ids,
                        planned_close_date=_en_dias(dias))).json()
    await _evaluar()
    assert await _avisos(test_database_url, lote["id"]) == esperado


# ── AC-C08 · AC-C09 · AC-C10 — cuándo NO se avisa ─────────────────────────────

async def test_t_038_44_pasada_la_fecha_prevista_no_se_avisa(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC-C08` · ya no significa «próximo».

    Un aviso de retraso sería otro evento, con su propia fuente normativa. Aquí no se inventa.
    """
    lote = (await _lote(client, auth_headers, seeded_ids,
                        planned_close_date=_en_dias(-1))).json()
    await _evaluar()
    assert await _avisos(test_database_url, lote["id"]) == 0


async def test_t_038_45_un_lote_cerrado_no_avisa(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC-C09` · avisar de que un lote cerrado va a cerrar no informa a nadie."""
    import app.database as database

    lote = (await _lote(client, auth_headers, seeded_ids,
                        planned_close_date=_en_dias(2))).json()

    # Se cierra por la base y no por `close_lot`: `BR-05` y `R7` exigen pesaje, alimento y
    # aprobaciones, y montarlos aquí probaría el cierre en vez de la exclusión.
    async with database.async_session() as s:
        await s.execute(Lot.__table__.update()
                        .where(Lot.id == lote["id"]).values(status="closed"))
        await s.commit()

    await _evaluar()
    assert await _avisos(test_database_url, lote["id"]) == 0


async def test_t_038_46_sin_fecha_prevista_no_hay_aviso_falso(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC-C10` · sin referencia no se inventa ninguna.

    Es el mismo criterio que `GA-REM-037` aplicó a la curva de peso: la ausencia de dato se
    declara callando, no adivinando.
    """
    lote = (await _lote(client, auth_headers, seeded_ids)).json()
    assert lote["planned_close_date"] is None
    await _evaluar()
    assert await _avisos(test_database_url, lote["id"]) == 0


# ── AC-C11 · AC-C12 — una sola vez ────────────────────────────────────────────

async def test_t_038_47_el_aviso_se_emite_una_sola_vez(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC-C11` y `AC-C12` · el propietario decidió uno al entrar, no uno por día.

    El evaluador corre cada hora: sin idempotencia, un lote a tres días acumularía setenta y
    dos avisos antes de cerrar.
    """
    lote = (await _lote(client, auth_headers, seeded_ids,
                        planned_close_date=_en_dias(2))).json()

    await _evaluar(veces=1)
    primera = await _avisos(test_database_url, lote["id"])
    assert primera >= 1, "no se creó el aviso"

    await _evaluar(veces=5)
    assert await _avisos(test_database_url, lote["id"]) == primera, (
        "reevaluar duplicó el aviso"
    )


async def test_t_038_48_replanificar_vuelve_a_avisar(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC-C11` · la idempotencia se ancla a la **ocurrencia**, no solo al lote.

    Si la fecha prevista cambia de verdad, el lote entra en una ventana distinta: es una
    situación nueva y merece aviso nuevo. Y el aviso viejo **no se borra**: era evidencia de
    lo que se sabía entonces.
    """
    import app.database as database

    lote = (await _lote(client, auth_headers, seeded_ids,
                        planned_close_date=_en_dias(2))).json()
    await _evaluar()
    antes = await _avisos(test_database_url, lote["id"])
    assert antes >= 1

    # Se replanifica a una fecha lejana y luego se vuelve a acercar.
    async with database.async_session() as s:
        await s.execute(Lot.__table__.update().where(Lot.id == lote["id"])
                        .values(planned_close_date=None))
        await s.commit()
    r = await client.put(f"/api/v1/lots/{lote['id']}", headers=auth_headers,
                         json={"planned_close_date": _en_dias(1)})
    assert r.status_code == 200, r.text

    await _evaluar()
    despues = await _avisos(test_database_url, lote["id"])
    assert despues > antes, "una replanificación real no volvió a avisar"


# ── AC-C13 · AC-C14 — destinatarios ───────────────────────────────────────────

async def test_t_038_49_avisa_a_quien_registro_el_lote_y_no_al_evaluador(
    client, auth_headers, seeded_ids, motor, test_database_url
):
    """`AC-C13` y `AC-C14` · el originador sale del dato, no del proceso que evalúa.

    El evaluador corre sin sesión de nadie. Si el destinatario se tomara de «quien ejecuta»,
    no habría a quién avisar — o peor, se avisaría a un usuario de sistema.
    """
    from app.auth.security import create_access_token

    # Ningún rol sembrado tiene `lots:create` —solo el Super Administrador, por comodín—, de
    # modo que se construye el escenario: un usuario que sí puede registrar lotes. Es
    # legítimo, `GA-REM-034` permite crear roles, y es el único modo de tener un originador
    # distinto de quien evalúa.
    rol = await client.post("/api/v1/roles", headers=auth_headers, json={
        "name": f"{PREFIJO}Planificador", "description": "Rol de prueba",
        "permissions": [{"module": "lots", "action": "create"},
                        {"module": "lots", "action": "read"}]})
    assert rol.status_code == 201, rol.text
    nombre = f"{PREFIJO}{uuid.uuid4().hex[:8]}"
    usuario = await client.post("/api/v1/users", headers=auth_headers, json={
        "username": nombre, "first_name": "Test", "last_name": "Planificador",
        "email": f"{nombre}@example.com", "password": uuid.uuid4().hex,
        "role_id": rol.json()["id"], "company_id": seeded_ids["company_id"],
        "view_type": "web"})
    assert usuario.status_code == 201, usuario.text
    # `GA-REM-040` enmienda H (`R-163`): registrar un lote es escritura productiva y exige la
    # unidad efectiva (`OD-09.c`, `AC-C05`). Hasta el tranche 3 de la ola B este montaje creaba
    # el lote con un usuario **sin** ninguna concesión —el defecto que `R-163` cierra— y por
    # eso funcionaba. Solo cambia el montaje: se le concede la unidad como haría la
    # administración de la fase 7; las aserciones sobre el aviso no cambian.
    from tests.business_unit_fixtures import habilitar_y_conceder_todo

    await habilitar_y_conceder_todo(
        test_database_url, company_id=seeded_ids["company_id"],
        user_ids=[usuario.json()["id"]])

    operador = {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(usuario.json()["id"])})}
    r = await client.post("/api/v1/lots", headers=operador, json={
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"], "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder", "sex": "mixed", "start_date": iso_days_ago(60),
        "planned_close_date": _en_dias(3)})
    assert r.status_code == 201, r.text
    lote = r.json()

    await _evaluar()

    e = create_async_engine(test_database_url)
    try:
        async with e.connect() as c:
            avisados = set((await c.execute(text(
                "SELECT recipient_user_id FROM notifications WHERE "
                "notification_type = 'lot_near_close' AND related_entity_id = :i"),
                {"i": lote["id"]})).scalars().all())
    finally:
        await e.dispose()

    assert usuario.json()["id"] in avisados, (
        "no se avisó a quien registró el lote"
    )

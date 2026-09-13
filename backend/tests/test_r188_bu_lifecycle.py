"""R-188 — BU-D10 (OD-23 · B): ciclo apagar/encender una unidad de empresa.

Regla canónica ratificada por el propietario (OD-23; fecha en el registro de decisión):

    APAGAR una unidad de empresa TERMINA la efectividad futura de las concesiones vivas
    de esa unidad en ese ciclo: quedan MARCADAS como historia (revoked_at), nunca borradas.
    RE-ENCENDER no devuelve efectividad a ninguna concesión histórica.
    Cada usuario que deba operar tras la reapertura requiere una CONCESIÓN NUEVA explícita.

Estas pruebas afirman la conducta OD-23. Contra el código previo (conducta provisional A:
`AC-A06` devolvía la efectividad al re-encender) esta suite es RED: falla en las pruebas
de «no devuelve»/«termina». La evidencia RED/GREEN ejecutada vive en `audit/ga-bu-d10/`.

Nota de ejecución: requiere PostgreSQL (suite canónica). En local sin credenciales de
siembra (`GA_TEST_ADMIN_PASSWORD`, vía `test_credentials`) queda `skipped` — declarado,
no fingido; corre en CI con `backend/scripts/run_tests.sh`.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "BU188-"
CODIGO = "broiler"


def _cab(uid: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(uid)})}"}


@pytest_asyncio.fixture
async def esc(test_database_url, test_credentials):
    """Escenario autocontenido: empresa A (con unidad habilitada) · empresa B ajena.

    Actores: `u_admin` (Administrador de Accesos, SIN concesión propia) · `u_op` (recibirá
    concesiones) · `u_zero` (sin concesión) · `u_otra` (empresa B, blanco cross-company).
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.masters.models import Company

    motor = create_async_engine(test_database_url)
    datos: dict = {}
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        unidad = (await s.execute(select(BusinessUnit).where(BusinessUnit.code == CODIGO))).scalar_one()
        hab_a = CompanyBusinessUnit(company_id=a.id, business_unit_id=unidad.id, is_enabled=True)
        s.add(hab_a)
        await s.flush()

        r_admin = Role(name=f"{PREFIJO}ADM-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        r_op = Role(name=f"{PREFIJO}OP-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        r_otra = Role(name=f"{PREFIJO}OTR-{uuid.uuid4().hex[:6]}", company_id=b.id, is_active=True)
        s.add_all([r_admin, r_op, r_otra])
        await s.flush()
        for accion in ("read", "create", "update", "delete"):
            s.add(Permission(role_id=r_admin.id, module="business_units",
                             action=PermissionAction(accion), scope_type="company"))
        s.add(Permission(role_id=r_op.id, module="reports",
                         action=PermissionAction.READ, scope_type="company"))
        await s.flush()

        def _u(company_id: int, marca: str, role_id: int) -> User:
            # GA-GOV-03 (T1): el fixture usa un dominio válido para `EmailStr` — los dominios
            # reservados (`@e.test`) hacían fallar la lectura de `/me` (R-213 es del producto de
            # lectura y se corrige en su propio paquete; aquí solo se corrige el fixture).
            return User(first_name=marca, last_name="Bu188",
                        email=f"{PREFIJO}{marca.lower()}-{uuid.uuid4().hex[:6]}@example.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=company_id,
                        role_id=role_id, is_active=True)

        u_admin = _u(a.id, "ADM", r_admin.id)
        u_op = _u(a.id, "OP", r_op.id)
        u_zero = _u(a.id, "ZERO", r_op.id)
        u_otra = _u(b.id, "OTRA", r_otra.id)
        s.add_all([u_admin, u_op, u_zero, u_otra])
        await s.commit()

        datos = {"a": a.id, "b": b.id, "hab_a": hab_a.id,
                 "u_admin": u_admin.id, "u_op": u_op.id, "u_zero": u_zero.id,
                 "u_otra": u_otra.id}

    yield datos

    # ── Limpieza determinista por prefijo ─────────────────────────────────────
    from app.audit.models import AuditLog
    from app.business_units.models import CompanyBusinessUnit, UserBusinessUnit
    from app.masters.models import Company

    async with motor.begin() as c:
        usuarios = (await c.execute(text(
            "SELECT id FROM users WHERE username LIKE :p"), {"p": f"{PREFIJO}%"})).scalars().all()
        cbus = (await c.execute(
            select(CompanyBusinessUnit.id).where(CompanyBusinessUnit.company_id.in_(
                select(Company.id).where(Company.name.like(f"{PREFIJO}%"))))
        )).scalars().all()
        if usuarios:
            await c.execute(delete(UserBusinessUnit).where(UserBusinessUnit.user_id.in_(usuarios)))
        if cbus:
            await c.execute(delete(UserBusinessUnit).where(
                UserBusinessUnit.company_business_unit_id.in_(cbus)))
            await c.execute(delete(AuditLog).where(
                AuditLog.entity_type == "company_business_unit",
                AuditLog.entity_id.in_([str(i) for i in cbus])))
        if usuarios:
            await c.execute(delete(AuditLog).where(AuditLog.user_id.in_(usuarios)))
        await c.execute(text(
            "DELETE FROM permissions WHERE role_id IN "
            "(SELECT id FROM roles WHERE name LIKE :p)"), {"p": f"{PREFIJO}%"})
        if cbus:
            await c.execute(delete(CompanyBusinessUnit).where(CompanyBusinessUnit.id.in_(cbus)))
        if usuarios:
            await c.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": list(usuarios)})
        await c.execute(text("DELETE FROM roles WHERE name LIKE :p"), {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM companies WHERE name LIKE :p"), {"p": f"{PREFIJO}%"})
    await motor.dispose()


async def _efectivas_y_concedidas(http_client, uid: int) -> tuple[list, list]:
    r = await http_client.get("/api/v1/me", headers=_cab(uid))
    assert r.status_code == 200, r.text
    d = r.json()
    return d["effective_business_units"], d["granted_business_units"]


async def _concesiones(test_database_url, user_id: int):
    from app.business_units.models import UserBusinessUnit

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            filas = (await s.execute(
                select(UserBusinessUnit).where(UserBusinessUnit.user_id == user_id)
                .order_by(UserBusinessUnit.id))).scalars().all()
            return [(f.id, f.revoked_at) for f in filas]
    finally:
        await motor.dispose()


def _url_post(user_id: int) -> str:
    return f"/api/v1/users/{user_id}/business-units"


# ═══════════════════════════════════════════════════════════════════════════
# Núcleo OD-23 · B — apagar TERMINA · encender NO devuelve · concesión nueva SÍ
# ═══════════════════════════════════════════════════════════════════════════

async def test_r188_apagar_termina_las_concesiones_vivas(http_client, test_database_url, esc):
    """Apagar: la concesión queda MARCADA (no borrada) y deja de ser efectiva."""
    r = await http_client.post(_url_post(esc["u_op"]), headers=_cab(esc["u_admin"]),
                               json={"code": CODIGO})
    assert r.status_code == 201, r.text
    ef, gr = await _efectivas_y_concedidas(http_client, esc["u_op"])
    assert ef == [CODIGO] and gr == [CODIGO]

    rd = await http_client.patch(f"/api/v1/business-units/{CODIGO}/disable",
                                 headers=_cab(esc["u_admin"]))
    assert rd.status_code == 200, rd.text

    ef, gr = await _efectivas_y_concedidas(http_client, esc["u_op"])
    assert ef == [] and gr == [], "OD-23: apagar termina la concesión del ciclo"
    filas = await _concesiones(test_database_url, esc["u_op"])
    assert len(filas) == 1 and filas[0][1] is not None, (
        "la fila SE CONSERVA (historia) y queda marcada revoked_at — nunca se borra")


async def test_r188_reactivar_no_devuelve_la_concesion(http_client, esc):
    """OD-23 §2.2: el re-encendido NO devuelve efectividad a ninguna concesión histórica.

    Esta aserción es el núcleo del RED: la conducta provisional (AC-A06) devolvía la
    efectividad aquí, sin ninguna concesión nueva.
    """
    await http_client.post(_url_post(esc["u_op"]), headers=_cab(esc["u_admin"]), json={"code": CODIGO})
    await http_client.patch(f"/api/v1/business-units/{CODIGO}/disable", headers=_cab(esc["u_admin"]))
    await http_client.patch(f"/api/v1/business-units/{CODIGO}/enable", headers=_cab(esc["u_admin"]))

    ef, gr = await _efectivas_y_concedidas(http_client, esc["u_op"])
    assert ef == [], "B: re-encender no resucita accesos — hace falta concesión nueva"
    assert gr == []


async def test_r188_concesion_nueva_restaura_y_conserva_historia(http_client, test_database_url, esc):
    """La re-autorización explícita restaura acceso; la historia queda (2 filas)."""
    await http_client.post(_url_post(esc["u_op"]), headers=_cab(esc["u_admin"]), json={"code": CODIGO})
    await http_client.patch(f"/api/v1/business-units/{CODIGO}/disable", headers=_cab(esc["u_admin"]))
    await http_client.patch(f"/api/v1/business-units/{CODIGO}/enable", headers=_cab(esc["u_admin"]))

    r = await http_client.post(_url_post(esc["u_op"]), headers=_cab(esc["u_admin"]), json={"code": CODIGO})
    assert r.status_code == 201, r.text
    ef, gr = await _efectivas_y_concedidas(http_client, esc["u_op"])
    assert ef == [CODIGO] and gr == [CODIGO]

    filas = await _concesiones(test_database_url, esc["u_op"])
    assert len(filas) == 2, "historia completa: la terminada + la nueva"
    assert filas[0][1] is not None and filas[1][1] is None


async def test_r188_auditoria_de_terminacion_por_ciclo(http_client, test_database_url, esc):
    """§12/§38: cada concesión terminada por el apagado deja evento con causa declarada."""
    from app.audit.models import AuditAction, AuditLog

    r = await http_client.post(_url_post(esc["u_op"]), headers=_cab(esc["u_admin"]), json={"code": CODIGO})
    assert r.status_code == 201, r.text
    filas = await _concesiones(test_database_url, esc["u_op"])
    cid = filas[0][0]

    r = await http_client.patch(f"/api/v1/business-units/{CODIGO}/disable", headers=_cab(esc["u_admin"]))
    assert r.status_code == 200, r.text

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            eventos = (await s.execute(select(AuditLog).where(
                AuditLog.entity_type == "user_business_unit",
                AuditLog.entity_id == str(cid)))).scalars().all()
    finally:
        await motor.dispose()

    tipos = {e.action: e for e in eventos}
    assert AuditAction.PERMISSION_CHANGE in tipos, "terminación auditada individualmente"
    # GA-GOV-03 · TEST_DEFECT 38 (C6): PostgreSQL no garantiza el orden de lectura sin
    # `ORDER BY` — en CI el orden físico invirtió los dos eventos y el dict retenía el
    # de concesión. La terminación se identifica por su semántica (`new_state` «revoked»),
    # no por su posición, y su unicidad queda afirmada.
    terminaciones = [e for e in eventos
                     if e.action == AuditAction.PERMISSION_CHANGE and e.new_state == "revoked"]
    assert len(terminaciones) == 1, "exactamente una terminación auditada por el ciclo"
    term = terminaciones[0]
    assert term.previous_state == "granted" and term.new_state == "revoked"
    assert (term.new_values or {}).get("cause") == "company_business_unit_disabled"
    assert (term.new_values or {}).get("target_user_id") == esc["u_op"]


async def test_r188_apagado_idempotente_normaliza_estado_previo(http_client, test_database_url, esc):
    """Un estado OFF previo con concesión viva (pre-política) se normaliza con un apagado.

    El apagado repetido no duplica configuración y marca las vivas residuales.
    """
    from app.business_units.models import CompanyBusinessUnit, UserBusinessUnit
    from app.business_units.service import conceder_unidad

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            hab = (await s.execute(select(CompanyBusinessUnit)
                                   .where(CompanyBusinessUnit.id == esc["hab_a"]))).scalar_one()
            from app.auth.models import User
            u = (await s.execute(select(User).where(User.id == esc["u_op"]))).scalar_one()
            await conceder_unidad(s, user=u, company_business_unit=hab)
            hab.is_enabled = False          # simula OFF previo a la política, con viva
            await s.commit()
    finally:
        await motor.dispose()

    r = await http_client.patch(f"/api/v1/business-units/{CODIGO}/disable",
                                headers=_cab(esc["u_admin"]))
    assert r.status_code == 200, r.text
    filas = await _concesiones(test_database_url, esc["u_op"])
    assert len(filas) == 1 and filas[0][1] is not None, "normaliza sin duplicar"


# ═══════════════════════════════════════════════════════════════════════════
# Puertas preservadas — conceder no habilita · self-grant · cross-company
# ═══════════════════════════════════════════════════════════════════════════

async def test_r188_conceder_con_unidad_apagada_rechaza(http_client, esc):
    """Conceder no enciende (409): la re-autorización ocurre tras encender."""
    await http_client.patch(f"/api/v1/business-units/{CODIGO}/disable", headers=_cab(esc["u_admin"]))
    r = await http_client.post(_url_post(esc["u_op"]), headers=_cab(esc["u_admin"]), json={"code": CODIGO})
    assert r.status_code == 409, r.text


async def test_r188_self_grant_denegado(http_client, esc):
    """OD-15.a: quien reparte no se sirve a sí mismo (403, primera puerta)."""
    r = await http_client.post(_url_post(esc["u_admin"]), headers=_cab(esc["u_admin"]), json={"code": CODIGO})
    assert r.status_code == 403, r.text


async def test_r188_cross_company_denegado(http_client, esc):
    """Usuario de otra empresa ⇒ 404 anti-enumeración."""
    r = await http_client.post(_url_post(esc["u_otra"]), headers=_cab(esc["u_admin"]), json={"code": CODIGO})
    assert r.status_code == 404, r.text


async def test_r188_zero_bu_sin_dato_productivo(http_client, esc):
    """Sin concesión: /me contesta y no hay efectivas (OD-09.c)."""
    ef, gr = await _efectivas_y_concedidas(http_client, esc["u_zero"])
    assert ef == [] and gr == []


# ═══════════════════════════════════════════════════════════════════════════
# Transferencia de empresa — PRESERVADA (OD-09.e; no es BU-D10)
# ═══════════════════════════════════════════════════════════════════════════

async def test_r188_transferencia_de_empresa_intacta(http_client, test_database_url, esc):
    """Volver a la empresa anterior NO reactiva: hace falta concesión nueva (AC-B12)."""
    from app.auth.models import User
    from app.business_units.service import conceder_unidad, revocar_concesiones

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            from app.business_units.models import CompanyBusinessUnit
            hab = (await s.execute(select(CompanyBusinessUnit)
                                   .where(CompanyBusinessUnit.id == esc["hab_a"]))).scalar_one()
            u = (await s.execute(select(User).where(User.id == esc["u_op"]))).scalar_one()
            await conceder_unidad(s, user=u, company_business_unit=hab)
            await s.commit()
        ef, _ = await _efectivas_y_concedidas(http_client, esc["u_op"])
        assert ef == [CODIGO]

        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            u = (await s.execute(select(User).where(User.id == esc["u_op"]))).scalar_one()
            await revocar_concesiones(s, user=u)      # lo que hace mover de empresa
            u.company_id = esc["b"]
            await s.commit()
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            u = (await s.execute(select(User).where(User.id == esc["u_op"]))).scalar_one()
            u.company_id = esc["a"]                   # vuelve
            await s.commit()
    finally:
        await motor.dispose()

    ef, _ = await _efectivas_y_concedidas(http_client, esc["u_op"])
    assert ef == [], "volver no prueba el mismo cargo (OD-09.e) — sin cambios por OD-23"

"""Aislamiento por fila — `GA-REM-040` fase 3 · `T-040-09`.

La afirmación que esta suite existe para sostener:

    PERTENECER A LA EMPRESA  ES NECESARIO  PERO NO SUFICIENTE

La fase 2 clasificó `/api/v1/lots` como `MULTI_UNIDAD` y dejó dicho, con una prueba dedicada,
que clasificar no es proteger: seguía devolviendo los lotes de todas las cadenas de la empresa.
Aquí se cierra esa fuga.

Se prueba **contra el API**, no contra el servicio: quien llame con `curl` alcanza el endpoint
igual que la interfaz, y un filtro que solo viva en la pantalla no es un filtro.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.auth.security import create_access_token
from tests.time_reference import days_ago, iso_days_ago

pytestmark = pytest.mark.asyncio

PREFIJO = "BUROW-"


def _futuro(dias: int) -> str:
    """`T-028-04`: sin fechas literales. Se calculan desde la referencia del proyecto, de
    modo que la prueba no caduca ni depende del calendario en que se ejecute."""
    import datetime as _dt

    return _dt.datetime.combine(
        days_ago(-dias), _dt.time.min, tzinfo=_dt.timezone.utc).isoformat()


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def escenario(test_database_url):
    """Una empresa con lotes de dos cadenas, y tres usuarios con alcances distintos.

    ```
    Empresa A   Reproductora ON · Incubadora ON
        lote R  breeder      lote H  hatchery
        usuario RE   solo Reproductora
        usuario AMB  Reproductora + Incubadora
        usuario CERO sin ninguna
    Empresa B   Reproductora ON · lote de B, mismo código de unidad
    ```

    `CONTROL` y `TRATAMIENTO` en el mismo escenario: si `AMB` no viera los dos lotes, un
    filtro que lo deniega todo pasaría por seguro (`R-72`).
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import BirdTypeEnum, Company, Lot

    motor = create_async_engine(test_database_url)
    datos: dict = {}
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        habilitaciones = {}
        for empresa, codes in ((a, ("breeder", "hatchery")), (b, ("breeder",))):
            for code in codes:
                fila = CompanyBusinessUnit(company_id=empresa.id,
                                           business_unit_id=unidades[code].id,
                                           is_enabled=True)
                s.add(fila)
                await s.flush()
                habilitaciones[(empresa.id, code)] = fila

        def _lote(company_id, code, tipo):
            return Lot(company_id=company_id, lot_code=f"{PREFIJO}{code}-{uuid.uuid4().hex[:6]}",
                       bird_type=tipo, status="active")

        lote_r = _lote(a.id, "R", BirdTypeEnum.BREEDER)
        lote_h = _lote(a.id, "H", BirdTypeEnum.HATCHERY)
        lote_b = _lote(b.id, "B", BirdTypeEnum.BREEDER)
        # Un lote sin cadena declarada: el campo es nulable y esta suite tiene que decir
        # qué le pasa, en lugar de descubrirlo el día que alguien pregunte.
        lote_sin = _lote(a.id, "SIN", None)
        s.add_all([lote_r, lote_h, lote_b, lote_sin])
        await s.flush()

        rol = Role(name=f"{PREFIJO}Op-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        s.add(rol)
        await s.flush()
        for modulo, accion in (("lots", PermissionAction.READ),
                               ("lots", PermissionAction.UPDATE),
                               ("lots", PermissionAction.CREATE)):
            s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        await s.flush()

        def _usuario(company_id, marca):
            return User(first_name=marca, last_name="Fila",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=company_id,
                        role_id=rol.id, is_active=True)

        re_, amb, cero = _usuario(a.id, "RE"), _usuario(a.id, "AMB"), _usuario(a.id, "CERO")
        s.add_all([re_, amb, cero])
        await s.flush()

        await conceder_unidad(s, user=re_, company_business_unit=habilitaciones[(a.id, "breeder")])
        for code in ("breeder", "hatchery"):
            await conceder_unidad(s, user=amb,
                                  company_business_unit=habilitaciones[(a.id, code)])
        await s.commit()

        # Fase productiva propia: `test_seeds` no las siembra, y depender de que exista
        # una haría que la prueba pasara o fallara por algo ajeno a lo que mide.
        from app.masters.models import ProductivePhase

        fase = (await s.execute(select(ProductivePhase).limit(1))).scalar_one_or_none()
        if fase is None:
            fase = ProductivePhase(name=f"{PREFIJO}Fase", code=f"{PREFIJO[:4]}{uuid.uuid4().hex[:4]}",
                                   order=1, duration_days=10)
            s.add(fase)
            await s.flush()

        datos = {
            "fase_id": fase.id,
            "empresa_a": a.id, "empresa_b": b.id,
            "lote_r": lote_r.id, "lote_h": lote_h.id, "lote_b": lote_b.id,
            "lote_sin": lote_sin.id,
            "codigo_r": lote_r.lot_code, "codigo_h": lote_h.lot_code,
            "user_re": re_.id, "user_amb": amb.id, "user_cero": cero.id,
            "hab_hatchery": habilitaciones[(a.id, "hatchery")].id,
        }

    yield datos

    async with motor.begin() as c:
        await c.execute(text("DELETE FROM user_business_units WHERE user_id IN "
                             "(SELECT id FROM users WHERE username LIKE :p)"),
                        {"p": f"{PREFIJO}%"})
        # La auditoría referencia al usuario y al lote: una escritura con éxito deja
        # rastro, y el rastro es lo que impide borrar la fixture. Se retira primero.
        await c.execute(text("DELETE FROM audit_logs WHERE user_id IN "
                             "(SELECT id FROM users WHERE username LIKE :p)"),
                        {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM audit_logs WHERE entity_type = 'lot' AND entity_id IN "
                             "(SELECT id::text FROM lots WHERE lot_code LIKE :p)"),
                        {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM lots WHERE lot_code LIKE :p"), {"p": f"{PREFIJO}%"})
        await c.execute(text("DELETE FROM company_business_units WHERE company_id IN "
                             "(SELECT id FROM companies WHERE name LIKE :p)"),
                        {"p": f"{PREFIJO}%"})
        from app.auth.models import Permission, Role, User
        from app.masters.models import Company
        ids = (await c.execute(text("SELECT id FROM roles WHERE name LIKE :p"),
                               {"p": f"{PREFIJO}%"})).scalars().all()
        if ids:
            await c.execute(delete(Permission).where(Permission.role_id.in_(ids)))
        await c.execute(delete(User).where(User.username.like(f"{PREFIJO}%")))
        await c.execute(delete(Role).where(Role.name.like(f"{PREFIJO}%")))
        await c.execute(delete(Company).where(Company.name.like(f"{PREFIJO}%")))
    await motor.dispose()


async def _codigos(http_client, user_id, query=""):
    r = await http_client.get(f"/api/v1/lots?limit=100{query}", headers=_token(user_id))
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    filas = cuerpo if isinstance(cuerpo, list) else cuerpo.get("items", [])
    return {f["lot_code"] for f in filas}


# ── El listado · el control y el tratamiento ─────────────────────────────────

async def test_el_usuario_de_dos_cadenas_ve_las_dos(http_client, escenario):
    """`CONTROL`. Sin esta prueba, un filtro que deniegue todo pasaría por seguro."""
    vistos = await _codigos(http_client, escenario["user_amb"])
    assert escenario["codigo_r"] in vistos
    assert escenario["codigo_h"] in vistos


async def test_el_usuario_de_una_cadena_no_ve_la_otra(http_client, escenario):
    """`TRATAMIENTO`. El escenario exacto que la fase 3 debe cerrar.

    Misma empresa, mismo endpoint, mismo permiso `RBAC`. Lo único distinto es la concesión
    de unidad, y eso tiene que bastar para que el lote de incubadora desaparezca.
    """
    vistos = await _codigos(http_client, escenario["user_re"])
    assert escenario["codigo_r"] in vistos, "debe seguir viendo lo suyo"
    assert escenario["codigo_h"] not in vistos, (
        "PERTENECER A LA EMPRESA NO BASTA: el lote de incubadora se ha filtrado")


async def test_el_usuario_sin_unidades_no_ve_ningun_lote(http_client, escenario):
    """`BU-D09` desde el lado del dato: entra, y la operación productiva le queda vacía."""
    vistos = await _codigos(http_client, escenario["user_cero"])
    assert vistos == set()


async def test_no_se_ven_los_lotes_de_otra_empresa(http_client, escenario):
    """El inquilino sigue siendo la primera frontera, y no la única."""
    vistos = await _codigos(http_client, escenario["user_amb"])
    ajenos = {c for c in vistos if c.startswith(f"{PREFIJO}B-")}
    assert not ajenos


async def test_apagar_la_unidad_a_la_empresa_retira_sus_lotes(http_client, escenario,
                                                              test_database_url):
    """La concesión sigue viva; la empresa apagó la cadena. Los lotes desaparecen."""
    from app.business_units.models import CompanyBusinessUnit

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor)() as s:
        hab = await s.get(CompanyBusinessUnit, escenario["hab_hatchery"])
        hab.is_enabled = False
        await s.commit()
    try:
        vistos = await _codigos(http_client, escenario["user_amb"])
        assert escenario["codigo_r"] in vistos
        assert escenario["codigo_h"] not in vistos
    finally:
        async with async_sessionmaker(motor)() as s:
            hab = await s.get(CompanyBusinessUnit, escenario["hab_hatchery"])
            hab.is_enabled = True
            await s.commit()
        await motor.dispose()


async def test_un_lote_sin_cadena_declarada_no_se_muestra(http_client, escenario):
    """`Lot.bird_type` es nulable y de ahí no se puede derivar cadena.

    Se **deniega**, no se abre: `OD-10.c` decidió que lo no clasificable quede pendiente de
    clasificar, visible para quien lo registró y para la administración autorizada. Esa
    bandeja es la fase 6. Hasta entonces el comportamiento seguro es que no aparezca en la
    operación, y queda registrado como dependencia, no como olvido.
    """
    vistos = await _codigos(http_client, escenario["user_amb"])
    sin = {c for c in vistos if c.startswith(f"{PREFIJO}SIN-")}
    assert not sin


# ── El parámetro del cliente no amplía el alcance ────────────────────────────

async def test_pedir_la_otra_cadena_por_parametro_no_la_devuelve(http_client, escenario):
    """Un filtro que el cliente envía puede **reducir** el alcance, nunca ampliarlo."""
    vistos = await _codigos(http_client, escenario["user_re"], "&bird_type=hatchery")
    assert escenario["codigo_h"] not in vistos


# ── El detalle · conocer el identificador no cambia nada ─────────────────────

async def test_el_detalle_de_un_lote_de_otra_cadena_es_inalcanzable(http_client, escenario):
    """Saber el identificador del lote de incubadora no debe cambiar el resultado."""
    r = await http_client.get(f"/api/v1/lots/{escenario['lote_h']}",
                              headers=_token(escenario["user_re"]))
    assert r.status_code == 404, r.text


async def test_el_detalle_del_lote_propio_sigue_funcionando(http_client, escenario):
    r = await http_client.get(f"/api/v1/lots/{escenario['lote_r']}",
                              headers=_token(escenario["user_re"]))
    assert r.status_code == 200, r.text


async def test_el_detalle_de_otra_empresa_sigue_siendo_inalcanzable(http_client, escenario):
    r = await http_client.get(f"/api/v1/lots/{escenario['lote_b']}",
                              headers=_token(escenario["user_amb"]))
    assert r.status_code == 404, r.text


# ── La mutación · y sin efecto lateral ───────────────────────────────────────

async def test_no_se_modifica_un_lote_de_otra_cadena(http_client, escenario,
                                                     test_database_url):
    """Denegar después de haber escrito no es denegar."""
    from app.masters.models import Lot

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor)() as s:
        antes = (await s.execute(
            select(Lot.planned_close_date).where(
                Lot.id == escenario["lote_h"]))).scalar_one_or_none()

    r = await http_client.put(f"/api/v1/lots/{escenario['lote_h']}",
                              headers=_token(escenario["user_re"]),
                              json={"planned_close_date": _futuro(30)})
    assert r.status_code == 404, r.text

    async with async_sessionmaker(motor)() as s:
        despues = (await s.execute(
            select(Lot.planned_close_date).where(
                Lot.id == escenario["lote_h"]))).scalar_one_or_none()
    await motor.dispose()
    assert despues == antes, "la fila no puede haber cambiado"


async def test_si_se_modifica_un_lote_propio(http_client, escenario):
    """El control de la mutación: si nada se pudiera modificar, la prueba anterior no
    demostraría nada."""
    r = await http_client.put(f"/api/v1/lots/{escenario['lote_r']}",
                              headers=_token(escenario["user_re"]),
                              json={"planned_close_date": _futuro(60)})
    assert r.status_code == 200, r.text


# ── El total del listado ─────────────────────────────────────────────────────

async def test_el_total_no_cuenta_lo_que_no_se_ve(http_client, escenario):
    """Un total que cuenta filas ocultas las revela por diferencia: no enseña la fila,
    enseña que existe. Es el mismo principio que la fase 4 aplicará a los `KPI`."""
    r = await http_client.get("/api/v1/lots?limit=100", headers=_token(escenario["user_re"]))
    assert r.status_code == 200
    cuerpo = r.json()
    filas = cuerpo if isinstance(cuerpo, list) else cuerpo.get("items", [])
    total = cuerpo.get("total") if isinstance(cuerpo, dict) else len(filas)
    propios = {f["lot_code"] for f in filas}
    assert escenario["codigo_h"] not in propios
    assert total == len(filas), "el total del listado y sus filas tienen que casar"


async def test_el_alcance_se_aplica_antes_de_paginar(http_client, escenario):
    """Con el filtro después de paginar, la primera página podría venir vacía o incompleta
    mientras existen filas propias. Se pide una página de uno y tiene que traer una fila
    propia, no un hueco donde estaba la ajena."""
    r = await http_client.get("/api/v1/lots?limit=1&skip=0", headers=_token(escenario["user_re"]))
    assert r.status_code == 200
    cuerpo = r.json()
    filas = cuerpo if isinstance(cuerpo, list) else cuerpo.get("items", [])
    assert len(filas) == 1
    assert filas[0]["lot_code"].startswith(f"{PREFIJO}R-")


# ── Los sub-recursos del lote ────────────────────────────────────────────────

async def test_las_fases_de_un_lote_de_otra_cadena_son_inalcanzables(http_client, escenario):
    """Un sub-recurso que no comprueba nada deja el lote abierto por la puerta de al lado.

    Al escribir esta prueba apareció que `/lots/{id}/phases` y `/lots/{id}/opening-balance`
    consultaban por `lot_id` **sin comprobar pertenencia alguna** — ni siquiera de empresa.
    Era un `IDOR` anterior a las unidades de negocio, y se cierra pasando por el mismo
    camino acotado que el detalle.
    """
    r = await http_client.get(f"/api/v1/lots/{escenario['lote_h']}/phases",
                              headers=_token(escenario["user_re"]))
    assert r.status_code == 404, r.text


async def test_las_fases_del_lote_propio_siguen_funcionando(http_client, escenario):
    r = await http_client.get(f"/api/v1/lots/{escenario['lote_r']}/phases",
                              headers=_token(escenario["user_re"]))
    assert r.status_code == 200, r.text


async def test_las_fases_de_otra_empresa_son_inalcanzables(http_client, escenario):
    """El agujero de inquilino que este sub-recurso tenía desde antes de esta capacidad."""
    r = await http_client.get(f"/api/v1/lots/{escenario['lote_b']}/phases",
                              headers=_token(escenario["user_amb"]))
    assert r.status_code == 404, r.text


async def test_el_saldo_de_apertura_de_otra_cadena_es_inalcanzable(http_client, escenario):
    r = await http_client.get(f"/api/v1/lots/{escenario['lote_h']}/opening-balance",
                              headers=_token(escenario["user_re"]))
    assert r.status_code == 404, r.text


async def test_no_se_activa_manualmente_un_lote_de_otra_cadena(http_client, escenario,
                                                               test_database_url):
    """`activate_manual` consulta el lote con un `select` propio, fuera del camino acotado."""
    from app.lots.models import OpeningBalance

    r = await http_client.post("/api/v1/lots/activate-manual",
                               headers=_token(escenario["user_re"]),
                               json={"lot_id": escenario["lote_h"],
                                     "activation_date": iso_days_ago(30),
                                     "phase_at_activation_id": escenario["fase_id"],
                                     "initial_male_count": 50,
                                     "initial_female_count": 50})
    assert r.status_code in (403, 404), r.text

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor)() as s:
        creado = (await s.execute(select(OpeningBalance).where(
            OpeningBalance.lot_id == escenario["lote_h"]))).scalar_one_or_none()
    await motor.dispose()
    assert creado is None, "una activación denegada no puede dejar saldo de apertura"


async def test_no_se_cuelga_una_fase_de_un_lote_de_otra_cadena(http_client, escenario,
                                                               test_database_url):
    """Escribir contra lo ajeno es la misma clase de defecto que leerlo, y era posible."""
    from app.lots.models import LotPhase

    r = await http_client.post(f"/api/v1/lots/{escenario['lote_h']}/phases",
                               headers=_token(escenario["user_re"]),
                               json={"lot_id": escenario["lote_h"], "phase_id": 1,
                                     "start_date": iso_days_ago(30)})
    assert r.status_code == 404, r.text

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor)() as s:
        creada = (await s.execute(select(LotPhase).where(
            LotPhase.lot_id == escenario["lote_h"]))).scalar_one_or_none()
    await motor.dispose()
    assert creada is None, "una fase denegada no puede quedar escrita"


async def test_llamarse_administrador_no_amplia_el_alcance(http_client, escenario,
                                                           test_database_url):
    """El nombre del rol no atraviesa el filtro por fila. `OD-09.a` · `AC-F05`.

    `OD-09.a` da a las funciones de control visibilidad **de lectura** sobre la empresa, y
    esa es otra superficie y otra fase. Un `GET /lots` corriente no se vuelve transversal
    porque quien lo pida se llame de cierta forma, y el nombre de un rol es texto que
    `GA-REM-034` permite editar: si bastara con llamarse «Administrador», la capacidad se
    saltaría desde la pantalla de roles.

    Esta prueba nació de una mutación que **no** rompió nada: el alcance sí estaba bien,
    pero ninguna prueba lo sujetaba por este lado.
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import CompanyBusinessUnit
    from app.business_units.service import conceder_unidad

    motor = create_async_engine(test_database_url)
    creados = []
    try:
        async with async_sessionmaker(motor, expire_on_commit=False)() as s:
            hab = await s.get(CompanyBusinessUnit, escenario["hab_hatchery"])
            breeder = (await s.execute(select(CompanyBusinessUnit).where(
                CompanyBusinessUnit.company_id == escenario["empresa_a"],
                CompanyBusinessUnit.id != hab.id))).scalars().first()
            for nombre in ("Administrador de Empresa", "Contralor Avícola"):
                rol = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}",
                           company_id=escenario["empresa_a"], is_active=True)
                s.add(rol)
                await s.flush()
                s.add(Permission(role_id=rol.id, module="lots",
                                 action=PermissionAction.READ, scope_type="company"))
                u = User(first_name=nombre[:8], last_name="Rol",
                         email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                         username=f"{PREFIJO}{uuid.uuid4().hex[:8]}",
                         hashed_password=hash_password("x"),
                         company_id=escenario["empresa_a"], role_id=rol.id, is_active=True)
                s.add(u)
                await s.flush()
                # Solo Reproductora, igual que el sujeto restringido.
                await conceder_unidad(s, user=u, company_business_unit=breeder)
                creados.append(u.id)
            await s.commit()
    finally:
        await motor.dispose()

    for user_id in creados:
        vistos = await _codigos(http_client, user_id)
        assert escenario["codigo_r"] in vistos, "debe seguir viendo lo suyo"
        assert escenario["codigo_h"] not in vistos, (
            "el nombre del rol no puede ampliar el alcance por fila")

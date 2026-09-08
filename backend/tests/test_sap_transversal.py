"""El contrato SAP atraviesa las cuatro cadenas — `GA-REM-040` flujo 5 · `OD-12` · `BU-D04`.

    TRANSVERSALIDAD SAP  =  CAPACIDAD OPERATIVA EXPLÍCITA, ACOTADA AL CONTRATO SAP

Y en negativo, que es la mitad que evita los abusos:

    NO es todas las concesiones de unidad
    NO es un salto general del alcance por cadena
    NO es el nombre del rol

El sujeto principal tiene **una sola cadena concedida** a propósito. Probar esto con un analista
al que se le conceden las cuatro no probaría nada: demostraría que quien tiene todo ve todo.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.security import create_access_token
from tests.time_reference import days_ago

pytestmark = pytest.mark.asyncio

PREFIJO = "BUSAP-"
CADENAS = ("grandparent", "breeder", "hatchery", "broiler")


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def sap(test_database_url):
    """Un consolidado por cada cadena, y actores con capacidades distintas.

    ```
    Empresa A   las cuatro cadenas habilitadas · un consolidado en cada una
        ANALISTA   solo `breeder` concedida  +  sap:read · sap:send_sap
        OPERARIO   `breeder` + `hatchery`     SIN capacidad SAP
        IMPOSTOR   rol llamado «Analista SAP», SIN el permiso
    Empresa B   un consolidado ajeno
    ```
    """
    from datetime import datetime, time, timezone

    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.integrations.sap.models import ConsolidatedMovement
    from app.masters.models import BirdTypeEnum, Company, Lot

    def _instante(dias):
        return datetime.combine(days_ago(dias), time.min, tzinfo=timezone.utc)

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, codes in ((a, CADENAS), (b, ("breeder",))):
            for code in codes:
                fila = CompanyBusinessUnit(company_id=empresa.id,
                                           business_unit_id=unidades[code].id, is_enabled=True)
                s.add(fila)
                await s.flush()
                hab[(empresa.id, code)] = fila

        def _rol(nombre, company_id):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}",
                     company_id=company_id, is_active=True)
            s.add(r)
            return r

        rol_analista = _rol("AnalistaSAP", a.id)
        rol_operario = _rol("Operario", a.id)
        rol_impostor = _rol("Analista SAP", a.id)   # el nombre, sin el permiso
        rol_b = _rol("AnalistaB", b.id)
        await s.flush()
        for rol, permisos in (
            (rol_analista, [("sap", PermissionAction.READ), ("sap", PermissionAction.SEND_SAP),
                            ("lots", PermissionAction.READ),
                            ("reports", PermissionAction.READ)]),
            (rol_operario, [("lots", PermissionAction.READ),
                            ("reports", PermissionAction.READ)]),
            (rol_impostor, [("lots", PermissionAction.READ)]),
            (rol_b, [("sap", PermissionAction.READ), ("sap", PermissionAction.SEND_SAP)]),
        ):
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion,
                                 scope_type="company"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca[:8], last_name="Sap",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=company_id,
                        role_id=rol.id, is_active=True)

        analista = _usuario(a.id, "ANALISTA", rol_analista)
        operario = _usuario(a.id, "OPERARIO", rol_operario)
        impostor = _usuario(a.id, "IMPOSTOR", rol_impostor)
        analista_b = _usuario(b.id, "ANALISTAB", rol_b)
        s.add_all([analista, operario, impostor, analista_b])
        await s.flush()

        # El analista tiene **una sola** cadena. Es el corazón de la prueba.
        await conceder_unidad(s, user=analista, company_business_unit=hab[(a.id, "breeder")])
        for code in ("breeder", "hatchery"):
            await conceder_unidad(s, user=operario, company_business_unit=hab[(a.id, code)])
        await conceder_unidad(s, user=impostor, company_business_unit=hab[(a.id, "breeder")])
        await conceder_unidad(s, user=analista_b, company_business_unit=hab[(b.id, "breeder")])

        lotes, consolidados = {}, {}
        for code in CADENAS:
            lote = Lot(company_id=a.id, lot_code=f"{PREFIJO}{code[:4]}-{uuid.uuid4().hex[:6]}",
                       bird_type=BirdTypeEnum(code), status="active")
            s.add(lote)
            await s.flush()
            lotes[code] = lote.id
            cm = ConsolidatedMovement(
                company_id=a.id, lot_id=lote.id, event_type="mortality_recording",
                period_start=_instante(30), period_end=_instante(1), event_ids=[],
                total_quantity=float(CADENAS.index(code) + 1) * 10,
                unit="units", consolidated_by_id=analista.id)
            s.add(cm)
            await s.flush()
            consolidados[code] = cm.id

        lote_b = Lot(company_id=b.id, lot_code=f"{PREFIJO}AJENO-{uuid.uuid4().hex[:6]}",
                     bird_type=BirdTypeEnum.BREEDER, status="active")
        s.add(lote_b)
        await s.flush()
        cm_b = ConsolidatedMovement(
            company_id=b.id, lot_id=lote_b.id, event_type="mortality_recording",
            period_start=_instante(30), period_end=_instante(1), event_ids=[],
            total_quantity=999.0, unit="units", consolidated_by_id=analista_b.id)
        s.add(cm_b)
        await s.flush()
        await s.commit()

        datos = {"empresa_a": a.id, "empresa_b": b.id, "lotes": lotes,
                 "consolidados": consolidados, "consolidado_b": cm_b.id,
                 "lote_b": lote_b.id, "analista": analista.id, "operario": operario.id,
                 "impostor": impostor.id, "analista_b": analista_b.id,
                 "hab_breeder": hab[(a.id, "breeder")].id}

    yield datos

    async with motor.begin() as c:
        for sql in (
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM consolidated_movements WHERE lot_id IN "
            "(SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM user_business_units WHERE user_id IN "
            "(SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM company_business_units WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
        ):
            await c.execute(text(sql), {"p": f"{PREFIJO}%"})
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


async def _consolidados(http_client, user_id):
    r = await http_client.get("/api/v1/sap/consolidated?limit=200", headers=_token(user_id))
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    filas = cuerpo if isinstance(cuerpo, list) else (
        cuerpo.get("items") or cuerpo.get("movements") or cuerpo.get("consolidated") or [])
    assert filas or cuerpo, f"no se supo leer la respuesta: {cuerpo}"
    return {f["id"] for f in filas}


# ── `AC-SAP03` · `AC-SAP04` · las cuatro cadenas con una sola concedida ──────

async def test_ac_sap03_el_analista_alcanza_las_cuatro_cadenas(http_client, sap):
    """El corazón de `BU-D04`. **Una sola cadena concedida**, las cuatro alcanzables.

    Si el analista tuviera las cuatro concesiones esta prueba no diría nada: demostraría que
    quien tiene todo ve todo, no que exista una excepción de contrato.
    """
    vistos = await _consolidados(http_client, sap["analista"])
    for code in CADENAS:
        assert sap["consolidados"][code] in vistos, f"falta la cadena {code}"


async def test_ac_sap04_no_hacen_falta_las_cuatro_concesiones(http_client, sap,
                                                               test_database_url):
    """Y se comprueba que efectivamente **no** las tiene."""
    from app.auth.models import User
    from app.business_units.service import unidades_efectivas

    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor)() as s:
            u = (await s.execute(
                select(User).where(User.id == sap["analista"]))).scalar_one()
            assert await unidades_efectivas(s, u) == ["breeder"]
    finally:
        await motor.dispose()


# ── `AC-SAP01` · la capacidad es explícita ──────────────────────────────────

async def test_ac_sap01_sin_capacidad_sap_no_se_opera_el_contrato(http_client, sap):
    """Dos cadenas concedidas y ningún permiso SAP: denegado.

    Las concesiones de unidad **no sustituyen** al permiso.
    """
    r = await http_client.get("/api/v1/sap/consolidated", headers=_token(sap["operario"]))
    assert r.status_code == 403, r.text


async def test_ac_sap12_el_nombre_del_rol_no_abre_el_contrato(http_client, sap):
    """El rol se llama «Analista SAP» y no tiene el permiso. Denegado."""
    r = await http_client.get("/api/v1/sap/consolidated", headers=_token(sap["impostor"]))
    assert r.status_code == 403, r.text


# ── `AC-SAP02` · la empresa sigue siendo la primera frontera ────────────────

async def test_ac_sap02_el_contrato_no_cruza_la_empresa(http_client, sap):
    vistos = await _consolidados(http_client, sap["analista"])
    assert sap["consolidado_b"] not in vistos


async def test_ac_sap02_el_analista_ajeno_no_ve_lo_nuestro(http_client, sap):
    vistos = await _consolidados(http_client, sap["analista_b"])
    for code in CADENAS:
        assert sap["consolidados"][code] not in vistos


# ── `AC-SAP07` · fuera del contrato, el alcance normal ──────────────────────

async def test_ac_sap07_la_capacidad_sap_no_abre_las_superficies_normales(http_client, sap):
    """La prueba que separa una excepción acotada de un salto general.

    El mismo actor que acaba de listar las cuatro cadenas por el contrato SAP pide el detalle
    de un lote de incubadora por la puerta normal, y se le niega.
    """
    assert sap["consolidados"]["hatchery"] in await _consolidados(http_client, sap["analista"])

    r = await http_client.get(f"/api/v1/lots/{sap['lotes']['hatchery']}",
                              headers=_token(sap["analista"]))
    assert r.status_code == 404, r.text

    propio = await http_client.get(f"/api/v1/lots/{sap['lotes']['breeder']}",
                                   headers=_token(sap["analista"]))
    assert propio.status_code == 200, propio.text


async def test_el_identificador_obtenido_por_sap_no_es_una_llave(http_client, sap):
    """`§46`. El `lot_id` viaja en la proyección para trazar, y **no** abre el objeto."""
    r = await http_client.get("/api/v1/sap/consolidated?limit=200",
                              headers=_token(sap["analista"]))
    cuerpo = r.json()
    filas = cuerpo if isinstance(cuerpo, list) else (
        cuerpo.get("items") or cuerpo.get("movements") or cuerpo.get("consolidated") or [])
    ajenos = [f["lot_id"] for f in filas if f["lot_id"] != sap["lotes"]["breeder"]]
    assert ajenos, "la fixture debe traer lotes de otras cadenas"
    for lot_id in ajenos:
        d = await http_client.get(f"/api/v1/lots/{lot_id}", headers=_token(sap["analista"]))
        assert d.status_code == 404, f"lote {lot_id}: {d.status_code}"


async def test_ac_sap07_la_capacidad_sap_no_amplia_los_indicadores(http_client, sap):
    """Regresión de la fase 4: el contrato no ensancha el universo de los `KPI` normales."""
    r = await http_client.get(
        f"/api/v1/reports/kpis/mortality?lot_id={sap['lotes']['hatchery']}",
        headers=_token(sap["analista"]))
    assert r.status_code == 404, r.text


# ── `AC-SAP08` · `AC-SAP09` · la proyección ─────────────────────────────────

async def test_ac_sap09_la_proyeccion_no_lleva_el_objeto_ajeno(http_client, sap):
    """Categoría `C`. La respuesta lleva referencias, no el lote ni sus internos."""
    r = await http_client.get("/api/v1/sap/consolidated?limit=200",
                              headers=_token(sap["analista"]))
    cuerpo = r.json()
    filas = cuerpo if isinstance(cuerpo, list) else (
        cuerpo.get("items") or cuerpo.get("movements") or cuerpo.get("consolidated") or [])
    for f in filas:
        for prohibido in ("lot", "notes", "observations", "bird_type", "farm", "house"):
            assert prohibido not in f, f"la proyección expone {prohibido!r}: {f}"


# ── `AC-SAP05` · `AC-SAP06` · no concede ni habilita ────────────────────────

async def test_ac_sap05_operar_el_contrato_no_concede_ni_habilita(http_client, sap,
                                                                  test_database_url):
    from app.auth.models import User
    from app.business_units.service import unidades_efectivas, unidades_habilitadas

    motor = create_async_engine(test_database_url)
    try:
        async def _estado():
            async with async_sessionmaker(motor)() as s:
                u = (await s.execute(
                    select(User).where(User.id == sap["analista"]))).scalar_one()
                return (await unidades_efectivas(s, u),
                        await unidades_habilitadas(s, sap["empresa_a"]))

        antes = await _estado()
        await _consolidados(http_client, sap["analista"])
        await http_client.post("/api/v1/sap/consolidate", headers=_token(sap["analista"]),
                               json={})
        despues = await _estado()
    finally:
        await motor.dispose()
    assert antes == despues, f"{antes} → {despues}"


# ── `AC-SAP11` · una denegación no deja rastro de éxito ─────────────────────

async def test_ac_sap11_una_operacion_denegada_no_produce_efectos(http_client, sap,
                                                                  test_database_url):
    from app.integrations.sap.models import ConsolidatedMovement, SapPayload

    motor = create_async_engine(test_database_url)
    try:
        async def _conteos():
            async with async_sessionmaker(motor)() as s:
                from sqlalchemy import func
                return (
                    (await s.execute(select(func.count(ConsolidatedMovement.id))
                                     .where(ConsolidatedMovement.company_id ==
                                            sap["empresa_a"]))).scalar_one(),
                    (await s.execute(select(func.count(SapPayload.id)))).scalar_one(),
                )

        antes = await _conteos()
        r = await http_client.post("/api/v1/sap/export", headers=_token(sap["operario"]),
                                   json={})
        assert r.status_code == 403, r.text
        despues = await _conteos()
    finally:
        await motor.dispose()
    assert antes == despues, "una operación denegada modificó el estado"


# ── La excepción está declarada, no es un descuido ──────────────────────────

def test_la_excepcion_sap_esta_declarada_y_no_puede_crecer_en_silencio():
    """`OD-12`. La lista declarada tiene que coincidir con las rutas SAP reales.

    Sin esta prueba, una ruta SAP nueva heredaría la transversalidad por el mismo mecanismo
    que la tenían todas: **por ausencia de filtro**. Con ella, quien la añada tiene que
    decir explícitamente que la quiere dentro de la excepción — o dejarla fuera.

    Es la diferencia entre una excepción y un descuido que funciona.
    """
    from app.authorization_coverage import enumerar_rutas
    from app.business_units.route_scope import Alcance, clasificar
    from app.business_units.sap_contract import SUPERFICIES_TRANSVERSALES
    from app.main import app

    de_sap = {c for c, _, _ in enumerar_rutas(app) if c.startswith("/api/v1/sap/")}
    contrato = {c for c in de_sap if clasificar(c)[0] is Alcance.CONTRATO}

    assert contrato == set(SUPERFICIES_TRANSVERSALES), (
        f"la excepción declarada y las rutas del contrato no coinciden.\n"
        f"  sin declarar: {sorted(contrato - set(SUPERFICIES_TRANSVERSALES))}\n"
        f"  declaradas de más: {sorted(set(SUPERFICIES_TRANSVERSALES) - contrato)}")


def test_las_rutas_de_configuracion_sap_quedan_fuera_de_la_excepcion():
    """Referencias y diagnóstico no tocan filas de producción: no cruzan nada."""
    from app.business_units.sap_contract import es_superficie_transversal

    for camino in ("/api/v1/sap/references", "/api/v1/sap/references/import",
                   "/api/v1/sap/connection-check"):
        assert not es_superficie_transversal(camino), camino


def test_no_existe_una_funcion_generica_de_salto_de_alcance():
    """`§37`. Una excepción reutilizable acaba usándose donde nadie la previó.

    Se comprueba sobre el código real del paquete: ninguna función pública ofrece saltarse
    el alcance por unidad, y la única excepción está tipada a SAP.
    """
    import pathlib

    paquete = pathlib.Path(__file__).resolve().parents[1] / "app" / "business_units"
    sospechosas = ("def bypass", "def saltar_alcance", "def skip_business_unit",
                   "def ignorar_unidades")
    hallazgos = []
    for fichero in paquete.glob("*.py"):
        texto = fichero.read_text(encoding="utf-8")
        hallazgos += [f"{fichero.name}: {s}" for s in sospechosas if s in texto]
    assert not hallazgos, hallazgos

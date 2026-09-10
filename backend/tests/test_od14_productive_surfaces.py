"""`GA-REM-002` enmienda C · `R-139` · `OD-14.c/d` en las ocho superficies de dato productivo.

Ocho superficies sustituían el filtro de empresa por `is_super_admin`. `OD-14.c` las clasifica
`INQUILINO`: la autoridad global sin contexto obtiene cero filas / `404` / `403` según la
convención vigente de cada una, y situada en `A` obtiene solo `A`. Los actores de empresa no
cambian (`OD-14 §6`, `AC-G06`).

    Empresa A   breeder ON · hatchery OFF (control AC-A05) · lote, evento, alerta, evidencia,
                línea genética, granja+galpón, planta+incubadora
    Empresa B   breeder ON · lo mismo
    ACTOR_A     operations:read/delete · lots:create/read · masters:read/create · concesión breeder(A) y hatchery(A)
    ACTOR_B     ídem en B
    SIN_PERM    masters:read solamente, en A                         → control RBAC (AC17.12)
    SIN_EMP     mismos permisos que ACTOR_A, company_id NULL         → R-116 (AC23, AC24, AC25)
    GLOBAL      ("*", …, "all"), company_id NULL; se sitúa por reclamación autorizada (OD-11)
"""
from __future__ import annotations

import os
import pathlib
import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "OD14P-"
CARPETA = pathlib.Path(os.environ.get("MEDIA_DIR", "/tmp")) / "od14p_evidencias"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


def _filas(r) -> list[dict]:
    cuerpo = r.json()
    return cuerpo["items"] if isinstance(cuerpo, dict) else cuerpo


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import (BirdTypeEnum, Company, Farm, FarmType, GeneticLine,
                                    Hatchery, House, Incubator, Lot, ProductivePhase)
    from app.operations.models import (EventStatus, EventType, Evidence, OperationalAlert,
                                       OperationalEvent)

    CARPETA.mkdir(parents=True, exist_ok=True)
    motor = create_async_engine(test_database_url)
    d: dict = {}
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        assert {"breeder", "hatchery"} <= set(unidades), "el catálogo de unidades no está sembrado"
        hab = {}
        for empresa, code, on in ((a, "breeder", True), (a, "hatchery", False), (b, "breeder", True)):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id,
                                       is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        # Precondición explícita: el control de `AC-A05` depende de que hatchery(A) esté apagada.
        assert hab[(a.id, "hatchery")].is_enabled is False
        assert hab[(a.id, "breeder")].is_enabled is True and hab[(b.id, "breeder")].is_enabled is True

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id,
                     is_active=True)
            s.add(r)
            return r, permisos

        completo = [("operations", PermissionAction.READ), ("operations", PermissionAction.DELETE),
                    ("operations", PermissionAction.CREATE),
                    ("lots", PermissionAction.CREATE), ("lots", PermissionAction.READ),
                    ("masters", PermissionAction.READ), ("masters", PermissionAction.CREATE)]
        rol_a, perm_a = _rol("OpA", a.id, completo)
        rol_b, perm_b = _rol("OpB", b.id, completo)
        rol_sin, perm_sin = _rol("SinOps", a.id, [("masters", PermissionAction.READ)])
        rol_global, _ = _rol("Global", None, [])
        await s.flush()
        for rol, permisos in ((rol_a, perm_a), (rol_b, perm_b), (rol_sin, perm_sin)):
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        for accion in PermissionAction:
            s.add(Permission(role_id=rol_global.id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Od14",
                        email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        actor_a = _usuario(a.id, "ACTORA", rol_a)
        actor_b = _usuario(b.id, "ACTORB", rol_b)
        sin_perm = _usuario(a.id, "SINPERM", rol_sin)
        sin_emp = _usuario(None, "SINEMP", rol_a)
        glob = _usuario(None, "GLOBAL", rol_global)
        s.add_all([actor_a, actor_b, sin_perm, sin_emp, glob])
        await s.flush()
        # Precondición explícita (lección de la fase 8): la autoridad global es capacidad
        # real, no nombre de rol.
        comodines = (await s.execute(
            select(Permission).where(Permission.role_id == rol_global.id,
                                     Permission.module == "*", Permission.scope_type == "all")
        )).scalars().all()
        assert len(comodines) == len(list(PermissionAction))

        await conceder_unidad(s, user=actor_a, company_business_unit=hab[(a.id, "breeder")])
        await conceder_unidad(s, user=actor_a, company_business_unit=hab[(a.id, "hatchery")])
        await conceder_unidad(s, user=actor_b, company_business_unit=hab[(b.id, "breeder")])
        await conceder_unidad(s, user=sin_perm, company_business_unit=hab[(a.id, "breeder")])

        fase = (await s.execute(select(ProductivePhase).limit(1))).scalar_one_or_none()
        if fase is None:
            fase = ProductivePhase(name=f"{PREFIJO}Fase", code=f"OD14{uuid.uuid4().hex[:4]}",
                                   order=1, duration_days=10)
            s.add(fase)
            await s.flush()

        def _granja(empresa, marca):
            return Farm(company_id=empresa.id, name=f"{PREFIJO}GRANJA-{marca}",
                        code=f"{PREFIJO}G{marca}-{uuid.uuid4().hex[:4]}",
                        farm_type=FarmType.BREEDING, is_active=True)

        granja_a, granja_b = _granja(a, "A"), _granja(b, "B")
        planta_a = Hatchery(company_id=a.id, name=f"{PREFIJO}PLANTA-A", is_active=True)
        planta_b = Hatchery(company_id=b.id, name=f"{PREFIJO}PLANTA-B", is_active=True)
        linea_a = GeneticLine(company_id=a.id, name=f"{PREFIJO}LINEA-A", is_active=True)
        linea_b = GeneticLine(company_id=b.id, name=f"{PREFIJO}LINEA-B", is_active=True)
        s.add_all([granja_a, granja_b, planta_a, planta_b, linea_a, linea_b])
        await s.flush()
        galpon_a = House(farm_id=granja_a.id, name=f"{PREFIJO}GALPON-A", capacity=1000, is_active=True)
        galpon_b = House(farm_id=granja_b.id, name=f"{PREFIJO}GALPON-B", capacity=1000, is_active=True)
        inc_a = Incubator(hatchery_id=planta_a.id, name=f"{PREFIJO}INC-A", capacity=100, is_active=True)
        inc_b = Incubator(hatchery_id=planta_b.id, name=f"{PREFIJO}INC-B", capacity=100, is_active=True)
        s.add_all([galpon_a, galpon_b, inc_a, inc_b])
        await s.flush()

        def _lote(empresa, marca, tipo):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}",
                       bird_type=tipo, status="active")

        lote_a = _lote(a, "LA", BirdTypeEnum.BREEDER)          # con evento y alerta
        lote_a_h = _lote(a, "LAH", BirdTypeEnum.HATCHERY)      # unidad apagada en A
        lote_b = _lote(b, "LB", BirdTypeEnum.BREEDER)
        lote_a_manual = _lote(a, "LAM", BirdTypeEnum.BREEDER)  # para activate-manual
        lote_b_manual = _lote(b, "LBM", BirdTypeEnum.BREEDER)
        s.add_all([lote_a, lote_a_h, lote_b, lote_a_manual, lote_b_manual])
        await s.flush()

        def _evento(empresa, lote, autor):
            return OperationalEvent(company_id=empresa.id, lot_id=lote.id,
                                    event_type=EventType.FARM_INSPECTION,
                                    event_date=date.today(), status=EventStatus.REGISTERED,
                                    registered_by_id=autor.id, version=1,
                                    observations=f"{PREFIJO}EVENTO-{lote.lot_code}")

        ev_a, ev_a_h, ev_b = _evento(a, lote_a, actor_a), _evento(a, lote_a_h, actor_a), _evento(b, lote_b, actor_b)
        s.add_all([ev_a, ev_a_h, ev_b])
        await s.flush()

        def _alerta(empresa, lote, marca):
            return OperationalAlert(company_id=empresa.id, lot_id=lote.id, alert_type="high_mortality",
                                    severity="warning", message=f"{PREFIJO}ALERTA-{marca}",
                                    is_resolved=False)

        al_a, al_b = _alerta(a, lote_a, "A"), _alerta(b, lote_b, "B")
        s.add_all([al_a, al_b])

        def _evidencia(empresa, evento, autor, marca):
            ruta = CARPETA / f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}.txt"
            ruta.write_text(f"{PREFIJO}CONTENIDO-{marca}")
            return Evidence(event_id=evento.id, company_id=empresa.id, file_name=ruta.name,
                            file_path=str(ruta), file_size=ruta.stat().st_size,
                            mime_type="text/plain", evidence_type="document",
                            uploaded_by_id=autor.id)

        evi_a, evi_b = _evidencia(a, ev_a, actor_a, "A"), _evidencia(b, ev_b, actor_b, "B")
        # Una segunda evidencia de A, para que el borrado legítimo no consuma la que otras
        # pruebas necesitan intacta.
        evi_a2 = _evidencia(a, ev_a, actor_a, "A2")
        s.add_all([evi_a, evi_b, evi_a2])
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "fase": fase.id,
             "actor_a": actor_a.id, "actor_b": actor_b.id, "sin_perm": sin_perm.id,
             "sin_emp": sin_emp.id, "global": glob.id,
             "granja_a": granja_a.id, "granja_b": granja_b.id, "galpon_a": galpon_a.id,
             "planta_a": planta_a.id, "planta_b": planta_b.id, "inc_a": inc_a.id,
             "linea_a": linea_a.id, "linea_b": linea_b.id,
             "lote_a": lote_a.id, "lote_a_h": lote_a_h.id, "lote_b": lote_b.id,
             "lote_a_manual": lote_a_manual.id, "lote_b_manual": lote_b_manual.id,
             "ev_a": ev_a.id, "ev_a_h": ev_a_h.id, "ev_b": ev_b.id,
             "al_a": al_a.id, "al_b": al_b.id,
             "evi_a": evi_a.id, "evi_a2": evi_a2.id, "evi_b": evi_b.id,
             "ruta_evi_b": str(evi_b.file_path), "ruta_evi_a": str(evi_a.file_path)}
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        await c.execute(text("DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)"), p)
        await c.execute(text("DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)"), p)
        await c.execute(text("DELETE FROM opening_balances WHERE lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)"), p)
        await c.execute(text("DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM evidences WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM lots WHERE lot_code LIKE :p"), p)
        await c.execute(text("DELETE FROM productive_phases WHERE name LIKE :p"), p)  # `GA-REM-015-B` (`R-175`): la fase creada por la fixture se retira
        await c.execute(text("DELETE FROM houses WHERE farm_id IN (SELECT id FROM farms WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM farms WHERE name LIKE :p"), p)
        await c.execute(text("DELETE FROM incubators WHERE hatchery_id IN (SELECT id FROM hatcheries WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM hatcheries WHERE name LIKE :p"), p)
        await c.execute(text("DELETE FROM genetic_weight_curve_points WHERE curve_id IN (SELECT id FROM genetic_weight_curves WHERE genetic_line_id IN (SELECT id FROM genetic_lines WHERE name LIKE :p))"), p)
        await c.execute(text("DELETE FROM genetic_weight_curves WHERE genetic_line_id IN (SELECT id FROM genetic_lines WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM genetic_lines WHERE name LIKE :p"), p)
        await c.execute(text("DELETE FROM company_business_units WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)"), p)
        await c.execute(text("DELETE FROM users WHERE username LIKE :p"), p)
        await c.execute(text("DELETE FROM roles WHERE name LIKE :p"), p)
        await c.execute(text("DELETE FROM companies WHERE name LIKE :p"), p)
    for f in CARPETA.glob(f"{PREFIJO}*"):
        try:
            f.unlink()
        except OSError:
            pass
    await motor.dispose()


# ═══════════════════════════════════════════════════════════════════════════
#  S01 · GET /operations/alerts · AC18
# ═══════════════════════════════════════════════════════════════════════════

async def test_s01_control_el_actor_de_empresa_solo_ve_sus_alertas(http_client, esc):
    r = await http_client.get("/api/v1/operations/alerts?limit=50", headers=_token(esc["actor_a"]))
    assert r.status_code == 200, r.text
    ids = {x["id"] for x in _filas(r)}
    assert esc["al_a"] in ids and esc["al_b"] not in ids
    assert f"{PREFIJO}ALERTA-B" not in r.text


async def test_s01_la_autoridad_global_sin_contexto_obtiene_cero_alertas(http_client, esc):
    """`OD-14.c` dato productivo · sin contexto → cero filas. Antes: todas las empresas."""
    r = await http_client.get("/api/v1/operations/alerts?limit=50", headers=_token(esc["global"]))
    assert r.status_code == 200, r.text
    assert _filas(r) == [], f"sin contexto llegó la unión de inquilinos: {[x['id'] for x in _filas(r)]}"


async def test_s01_situada_en_a_solo_ve_a_y_situada_en_b_solo_ve_b(http_client, esc):
    ra = await http_client.get("/api/v1/operations/alerts?limit=50", headers=_token(esc["global"], esc["a"]))
    rb = await http_client.get("/api/v1/operations/alerts?limit=50", headers=_token(esc["global"], esc["b"]))
    assert ra.status_code == 200 and rb.status_code == 200, (ra.text, rb.text)
    assert {x["id"] for x in _filas(ra)} == {esc["al_a"]}, "situada en A vio alertas ajenas"
    assert {x["id"] for x in _filas(rb)} == {esc["al_b"]}, "situada en B vio alertas ajenas"


async def test_s01_rbac_sin_operations_read_es_403(http_client, esc):
    r = await http_client.get("/api/v1/operations/alerts", headers=_token(esc["sin_perm"]))
    assert r.status_code == 403, r.text


# ═══════════════════════════════════════════════════════════════════════════
#  S02 · GET /operations · AC19
# ═══════════════════════════════════════════════════════════════════════════

async def test_s02_control_el_actor_de_empresa_solo_ve_sus_eventos(http_client, esc):
    r = await http_client.get("/api/v1/operations?limit=100", headers=_token(esc["actor_a"]))
    assert r.status_code == 200, r.text
    ids = {x["id"] for x in _filas(r)}
    assert esc["ev_a"] in ids and esc["ev_b"] not in ids


async def test_s02_control_la_unidad_apagada_para_la_empresa_no_se_ve(http_client, esc):
    """`AC-A05` preservado: hatchery está OFF en A aunque el actor tenga concesión."""
    r = await http_client.get("/api/v1/operations?limit=100", headers=_token(esc["actor_a"]))
    assert r.status_code == 200, r.text
    assert esc["ev_a_h"] not in {x["id"] for x in _filas(r)}


async def test_s02_la_autoridad_global_sin_contexto_obtiene_cero_eventos(http_client, esc):
    r = await http_client.get("/api/v1/operations?limit=100", headers=_token(esc["global"]))
    assert r.status_code == 200, r.text
    assert _filas(r) == [], f"sin contexto llegó la unión de inquilinos: {len(_filas(r))} eventos"
    if "x-total-count" in r.headers:
        assert r.headers["x-total-count"] == "0", "el total revela filas ajenas"


async def test_s02_situada_en_a_solo_ve_a_incluidas_todas_sus_unidades(http_client, esc):
    """Situada en A: solo A (`OD-14.c`) — y todas las unidades de A, exención de visibilidad
    certificada en la fase 3 que `R-139` preserva."""
    r = await http_client.get("/api/v1/operations?limit=100", headers=_token(esc["global"], esc["a"]))
    assert r.status_code == 200, r.text
    ids = {x["id"] for x in _filas(r)}
    assert esc["ev_b"] not in ids, "situada en A vio eventos de B"
    assert {esc["ev_a"], esc["ev_a_h"]} <= ids


async def test_s02_situada_en_b_solo_ve_b(http_client, esc):
    r = await http_client.get("/api/v1/operations?limit=100", headers=_token(esc["global"], esc["b"]))
    assert r.status_code == 200, r.text
    ids = {x["id"] for x in _filas(r)}
    assert esc["ev_b"] in ids and esc["ev_a"] not in ids and esc["ev_a_h"] not in ids


async def test_s02_rbac_sin_operations_read_es_403(http_client, esc):
    r = await http_client.get("/api/v1/operations", headers=_token(esc["sin_perm"]))
    assert r.status_code == 403, r.text


# ═══════════════════════════════════════════════════════════════════════════
#  S03 · DELETE evidencia · AC20      S04 · descarga · AC21
# ═══════════════════════════════════════════════════════════════════════════

async def test_s03_control_el_actor_de_empresa_borra_la_propia_y_no_la_ajena(http_client, esc):
    ajena = await http_client.delete(f"/api/v1/operations/{esc['ev_b']}/evidences/{esc['evi_b']}",
                                     headers=_token(esc["actor_a"]))
    assert ajena.status_code == 403, ajena.text
    assert os.path.exists(esc["ruta_evi_b"]), "el fichero ajeno desapareció"
    propia = await http_client.delete(f"/api/v1/operations/{esc['ev_a']}/evidences/{esc['evi_a2']}",
                                      headers=_token(esc["actor_a"]))
    assert propia.status_code == 204, propia.text


async def test_s03_la_autoridad_global_sin_contexto_no_borra_nada(http_client, esc):
    r = await http_client.delete(f"/api/v1/operations/{esc['ev_b']}/evidences/{esc['evi_b']}",
                                 headers=_token(esc["global"]))
    assert r.status_code == 403, r.text
    assert os.path.exists(esc["ruta_evi_b"]), "sin contexto se borró el fichero de B"


async def test_s03_situada_en_a_no_borra_la_de_b(http_client, esc):
    r = await http_client.delete(f"/api/v1/operations/{esc['ev_b']}/evidences/{esc['evi_b']}",
                                 headers=_token(esc["global"], esc["a"]))
    assert r.status_code == 403, r.text
    assert os.path.exists(esc["ruta_evi_b"])


async def test_s04_control_el_actor_de_empresa_descarga_la_propia_y_no_la_ajena(http_client, esc):
    propia = await http_client.get(f"/api/v1/operations/{esc['ev_a']}/evidences/{esc['evi_a']}/download",
                                   headers=_token(esc["actor_a"]))
    assert propia.status_code == 200 and f"{PREFIJO}CONTENIDO-A" in propia.text, propia.text[:200]
    ajena = await http_client.get(f"/api/v1/operations/{esc['ev_b']}/evidences/{esc['evi_b']}/download",
                                  headers=_token(esc["actor_a"]))
    assert ajena.status_code == 403, ajena.text[:200]


async def test_s04_la_autoridad_global_sin_contexto_no_descarga(http_client, esc):
    r = await http_client.get(f"/api/v1/operations/{esc['ev_b']}/evidences/{esc['evi_b']}/download",
                              headers=_token(esc["global"]))
    assert r.status_code == 403, r.text[:200]
    assert f"{PREFIJO}CONTENIDO-B" not in r.text


async def test_s04_situada_en_a_descarga_la_de_a_y_no_la_de_b(http_client, esc):
    ra = await http_client.get(f"/api/v1/operations/{esc['ev_a']}/evidences/{esc['evi_a']}/download",
                               headers=_token(esc["global"], esc["a"]))
    assert ra.status_code == 200 and f"{PREFIJO}CONTENIDO-A" in ra.text
    rb = await http_client.get(f"/api/v1/operations/{esc['ev_b']}/evidences/{esc['evi_b']}/download",
                               headers=_token(esc["global"], esc["a"]))
    assert rb.status_code == 403, rb.text[:200]
    assert f"{PREFIJO}CONTENIDO-B" not in rb.text


# ═══════════════════════════════════════════════════════════════════════════
#  S05 · POST /lots/activate-manual · AC22
# ═══════════════════════════════════════════════════════════════════════════

def _cuerpo(esc, lote):
    return {"lot_id": lote, "activation_date": date.today().isoformat(),
            "phase_at_activation_id": esc["fase"], "age_days": 10,
            "initial_male_count": 100, "initial_female_count": 900}


async def _cuenta_saldos(test_database_url, lote) -> int:
    from app.lots.models import OpeningBalance
    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor)() as s:
            return len((await s.execute(select(OpeningBalance).where(OpeningBalance.lot_id == lote))).scalars().all())
    finally:
        await motor.dispose()


async def test_s05_control_el_actor_de_b_no_activa_el_lote_de_a(http_client, esc, test_database_url):
    r = await http_client.post("/api/v1/lots/activate-manual", headers=_token(esc["actor_b"]),
                               json=_cuerpo(esc, esc["lote_a_manual"]))
    # Convención vigente de la superficie (`AC-R67-11`): lote ajeno → `400 BR-07`.
    assert r.status_code == 400 and r.json().get("rule") == "BR-07", r.text
    assert await _cuenta_saldos(test_database_url, esc["lote_a_manual"]) == 0


async def test_s05_la_autoridad_global_sin_contexto_no_activa_el_lote_de_a(http_client, esc, test_database_url):
    """Escritura: antes creaba el saldo de apertura de un lote de cualquier empresa."""
    r = await http_client.post("/api/v1/lots/activate-manual", headers=_token(esc["global"]),
                               json=_cuerpo(esc, esc["lote_a_manual"]))
    assert r.status_code == 400 and r.json().get("rule") == "BR-07", r.text
    assert await _cuenta_saldos(test_database_url, esc["lote_a_manual"]) == 0, "sin contexto se escribió un saldo ajeno"


async def test_s05_situada_en_b_no_activa_el_lote_de_a(http_client, esc, test_database_url):
    r = await http_client.post("/api/v1/lots/activate-manual", headers=_token(esc["global"], esc["b"]),
                               json=_cuerpo(esc, esc["lote_a_manual"]))
    assert r.status_code == 400 and r.json().get("rule") == "BR-07", r.text
    assert await _cuenta_saldos(test_database_url, esc["lote_a_manual"]) == 0


async def test_s05_situada_en_a_activa_el_lote_de_a_y_el_actor_de_a_el_suyo(http_client, esc, test_database_url):
    r = await http_client.post("/api/v1/lots/activate-manual", headers=_token(esc["global"], esc["a"]),
                               json=_cuerpo(esc, esc["lote_a_manual"]))
    assert r.status_code == 201, r.text
    assert await _cuenta_saldos(test_database_url, esc["lote_a_manual"]) == 1
    # El actor de B activa el suyo: la regla no bloquea lo legítimo.
    r2 = await http_client.post("/api/v1/lots/activate-manual", headers=_token(esc["actor_b"]),
                                json=_cuerpo(esc, esc["lote_b_manual"]))
    assert r2.status_code == 201, r2.text


# ═══════════════════════════════════════════════════════════════════════════
#  S06 · curvas de una línea genética · AC23
# ═══════════════════════════════════════════════════════════════════════════

async def test_s06_control_el_actor_ve_su_linea_y_no_la_ajena(http_client, esc):
    propia = await http_client.get(f"/api/v1/masters/genetic-lines/{esc['linea_a']}/weight-curves",
                                   headers=_token(esc["actor_a"]))
    ajena = await http_client.get(f"/api/v1/masters/genetic-lines/{esc['linea_b']}/weight-curves",
                                  headers=_token(esc["actor_a"]))
    assert propia.status_code == 200 and ajena.status_code == 404, (propia.text, ajena.text)


async def test_s06_la_autoridad_global_sin_contexto_no_alcanza_ninguna_linea(http_client, esc):
    r = await http_client.get(f"/api/v1/masters/genetic-lines/{esc['linea_a']}/weight-curves",
                              headers=_token(esc["global"]))
    assert r.status_code == 404, r.text


async def test_s06_situada_en_a_alcanza_a_y_no_b(http_client, esc):
    ra = await http_client.get(f"/api/v1/masters/genetic-lines/{esc['linea_a']}/weight-curves",
                               headers=_token(esc["global"], esc["a"]))
    rb = await http_client.get(f"/api/v1/masters/genetic-lines/{esc['linea_b']}/weight-curves",
                               headers=_token(esc["global"], esc["a"]))
    assert ra.status_code == 200 and rb.status_code == 404, (ra.text, rb.text)


async def test_s06_el_actor_sin_empresa_no_alcanza_ninguna_linea(http_client, esc):
    """`R-116` en otra piel: `and company_id` dejaba sin filtro al actor sin empresa."""
    r = await http_client.get(f"/api/v1/masters/genetic-lines/{esc['linea_a']}/weight-curves",
                              headers=_token(esc["sin_emp"]))
    assert r.status_code == 404, r.text


async def test_s06_la_autoridad_global_sin_contexto_no_crea_curva_sobre_linea_de_a(http_client, esc):
    r = await http_client.post("/api/v1/masters/weight-curves", headers=_token(esc["global"]), json={
        "genetic_line_id": esc["linea_a"], "version_label": f"{PREFIJO}v1",
        "points": [{"age_days": 7, "min_weight": 100, "max_weight": 200, "target_weight": 150}]})
    assert r.status_code == 404, r.text


# ═══════════════════════════════════════════════════════════════════════════
#  S07 · galpones por granja · AC24      S08 · incubadoras por planta · AC25
# ═══════════════════════════════════════════════════════════════════════════

async def test_s07_control_el_actor_ve_su_granja_y_no_la_ajena(http_client, esc):
    propia = await http_client.get(f"/api/v1/masters/farms/{esc['granja_a']}/houses", headers=_token(esc["actor_a"]))
    ajena = await http_client.get(f"/api/v1/masters/farms/{esc['granja_b']}/houses", headers=_token(esc["actor_a"]))
    assert propia.status_code == 200 and {h["id"] for h in propia.json()} == {esc["galpon_a"]}
    assert ajena.status_code == 404, ajena.text


async def test_s07_la_autoridad_global_sin_contexto_no_lista_galpones(http_client, esc):
    r = await http_client.get(f"/api/v1/masters/farms/{esc['granja_a']}/houses", headers=_token(esc["global"]))
    assert r.status_code == 404, r.text


async def test_s07_situada_en_a_alcanza_a_y_no_b(http_client, esc):
    ra = await http_client.get(f"/api/v1/masters/farms/{esc['granja_a']}/houses", headers=_token(esc["global"], esc["a"]))
    rb = await http_client.get(f"/api/v1/masters/farms/{esc['granja_b']}/houses", headers=_token(esc["global"], esc["a"]))
    assert ra.status_code == 200 and {h["id"] for h in ra.json()} == {esc["galpon_a"]}
    assert rb.status_code == 404, rb.text


async def test_s07_el_actor_sin_empresa_no_lista_galpones(http_client, esc):
    r = await http_client.get(f"/api/v1/masters/farms/{esc['granja_a']}/houses", headers=_token(esc["sin_emp"]))
    assert r.status_code == 404, r.text


async def test_s08_control_el_actor_ve_su_planta_y_no_la_ajena(http_client, esc):
    propia = await http_client.get(f"/api/v1/masters/hatcheries/{esc['planta_a']}/incubators", headers=_token(esc["actor_a"]))
    ajena = await http_client.get(f"/api/v1/masters/hatcheries/{esc['planta_b']}/incubators", headers=_token(esc["actor_a"]))
    assert propia.status_code == 200 and {i["id"] for i in propia.json()} == {esc["inc_a"]}
    assert ajena.status_code == 404, ajena.text


async def test_s08_la_autoridad_global_sin_contexto_no_lista_incubadoras(http_client, esc):
    r = await http_client.get(f"/api/v1/masters/hatcheries/{esc['planta_a']}/incubators", headers=_token(esc["global"]))
    assert r.status_code == 404, r.text


async def test_s08_situada_en_a_alcanza_a_y_no_b(http_client, esc):
    ra = await http_client.get(f"/api/v1/masters/hatcheries/{esc['planta_a']}/incubators", headers=_token(esc["global"], esc["a"]))
    rb = await http_client.get(f"/api/v1/masters/hatcheries/{esc['planta_b']}/incubators", headers=_token(esc["global"], esc["a"]))
    assert ra.status_code == 200 and {i["id"] for i in ra.json()} == {esc["inc_a"]}
    assert rb.status_code == 404, rb.text


async def test_s08_el_actor_sin_empresa_no_lista_incubadoras(http_client, esc):
    r = await http_client.get(f"/api/v1/masters/hatcheries/{esc['planta_a']}/incubators", headers=_token(esc["sin_emp"]))
    assert r.status_code == 404, r.text


# ═══════════════════════════════════════════════════════════════════════════
#  AC26 · el primitivo compartido falla cerrado
# ═══════════════════════════════════════════════════════════════════════════

async def test_ac26_verificar_pertenencia_sin_empresa_falla_cerrado(esc, test_database_url):
    from app.masters.models import Farm
    from app.operations.validators import BusinessRuleViolation
    from app.tenancy import verificar_pertenencia
    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor)() as s:
            with pytest.raises(BusinessRuleViolation):
                await verificar_pertenencia(s, Farm, esc["granja_a"], None, "Granja")
            # Y con empresa: propia pasa, ajena no.
            await verificar_pertenencia(s, Farm, esc["granja_a"], esc["a"], "Granja")
            with pytest.raises(BusinessRuleViolation):
                await verificar_pertenencia(s, Farm, esc["granja_a"], esc["b"], "Granja")
    finally:
        await motor.dispose()


async def test_ac26_la_autoridad_global_sin_contexto_no_crea_galpon_bajo_granja_de_a(http_client, esc, test_database_url):
    """Llamador `masters/service._verificar_padres`: antes creaba el galpón bajo cualquier granja."""
    r = await http_client.post("/api/v1/masters/houses", headers=_token(esc["global"]),
                               json={"farm_id": esc["granja_a"], "name": f"{PREFIJO}GALPON-X", "capacity": 10})
    assert r.status_code == 400 and r.json().get("rule") == "BR-07", r.text
    from app.masters.models import House
    motor = create_async_engine(test_database_url)
    try:
        async with async_sessionmaker(motor)() as s:
            creado = (await s.execute(select(House).where(House.name == f"{PREFIJO}GALPON-X"))).scalar_one_or_none()
    finally:
        await motor.dispose()
    assert creado is None, "sin contexto se creó un galpón bajo una granja ajena"

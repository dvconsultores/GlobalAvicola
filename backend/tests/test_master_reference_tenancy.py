"""`GA-REM-002` enmienda D · `R-179` · las referencias a **catálogos** de un evento son de su empresa (`AC-R179-01…12`).

Regla (ya escrita en el ADDENDUM Wave 3 de `GA-REM-002`): `company_id IS NULL` = catálogo compartido, referenciable desde cualquier
empresa; `company_id` fijado = propio de esa empresa, y el evento solo puede referenciarlo si es la suya. El ajeno se comporta como
**inexistente** (`BR-07`, anti-enumeración).

Escenario (prefijo `MAES-`):
    empresa A (breeder ON) · empresa B (breeder ON) · empresa A: lote, granja, galpón, incubadora
    catálogos por familia: uno de A, uno de B y uno **compartido** (`company_id = NULL`)
    actores: op (A, operations+corrections), actor_b (B), global (comodín sin empresa)
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.security import create_access_token
from tests.time_reference import recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "MAES-"

#: familia → (campo del evento, tipo de evento, carga adicional). Una por catálogo `TENANT_OWNED_NULLABLE`.
FAMILIAS = [
    ("sup", "supplier_id", "bird_reception", {"bird_movements": [{"sex": "mixed", "quantity": 10}],
                                              "received_total": 10, "dead_on_arrival": 0, "rejected_on_arrival": 0}),
    ("tr", "transport_id", "transport_inspection", {"inspection_details": [{"parameter": "Higiene", "value": "ok", "status": "ok"}]}),
    ("mc", "cause_id", "mortality_recording", {"bird_movements": [{"sex": "mixed", "quantity": 1}]}),
    ("cc", "cull_cause_id", "cull_recording", {"bird_movements": [{"sex": "mixed", "quantity": 1}]}),
    ("vac", "vaccine_id", "vaccination", {}),
    ("med", "medication_id", "medication", {}),
    ("plant", "destination_plant_id", "bird_exit", {"bird_movements": [{"sex": "mixed", "quantity": 1}]}),
]


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


def _es_br(r, regla: str) -> bool:
    return r.status_code == 400 and r.json().get("rule") == regla


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import (BirdTypeEnum, Breed, Company, CullCause, Farm, FarmType, FeedType, GeneticLine,
                                    Hatchery, House, Incubator, Lot, LotStatus, Medication, MortalityCause,
                                    ProcessingPlant, Supplier, Transport, Vaccine)

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa in (a, b):
            for code in ("breeder", "hatchery"):
                fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id, is_enabled=True)
                s.add(fila)
                await s.flush()
                hab[(empresa.id, code)] = fila
        PA = PermissionAction
        ops = [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ),
               ("corrections", PA.CORRECT), ("corrections", PA.READ)]
        rol_a = Role(name=f"{PREFIJO}Op-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        rol_b = Role(name=f"{PREFIJO}OpB-{uuid.uuid4().hex[:6]}", company_id=b.id, is_active=True)
        rol_g = Role(name=f"{PREFIJO}Global-{uuid.uuid4().hex[:6]}", company_id=None, is_active=True)
        s.add_all([rol_a, rol_b, rol_g])
        await s.flush()
        for rol in (rol_a, rol_b):
            for modulo, accion in ops:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        for accion in PA:
            s.add(Permission(role_id=rol_g.id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Maes", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        op, actor_b, global_ = _usuario(a.id, "OP", rol_a), _usuario(b.id, "B", rol_b), _usuario(None, "GLOBAL", rol_g)
        s.add_all([op, actor_b, global_])
        await s.flush()
        for code in ("breeder", "hatchery"):
            await conceder_unidad(s, user=op, company_business_unit=hab[(a.id, code)])
            await conceder_unidad(s, user=actor_b, company_business_unit=hab[(b.id, code)])

        granja = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA-A", code=f"{PREFIJO}GA-{uuid.uuid4().hex[:4]}",
                      farm_type=FarmType.BREEDING, is_active=True)
        s.add(granja)
        await s.flush()
        galpon = House(farm_id=granja.id, name=f"{PREFIJO}GALPON-A", capacity=100_000, is_active=True)
        s.add(galpon)
        await s.flush()
        lote = Lot(company_id=a.id, lot_code=f"{PREFIJO}LR-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.BREEDER,
                   status=LotStatus.ACTIVE, farm_id=granja.id, house_id=galpon.id)
        lote_h = Lot(company_id=a.id, lot_code=f"{PREFIJO}LH-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.HATCHERY,
                     status=LotStatus.ACTIVE, farm_id=granja.id, house_id=galpon.id)
        s.add_all([lote, lote_h])

        # Un catálogo por familia y por dueño: A, B y compartido (`company_id = NULL`).
        modelos = {"sup": Supplier, "tr": Transport, "mc": MortalityCause, "cc": CullCause,
                   "vac": Vaccine, "med": Medication, "plant": ProcessingPlant}
        catalogos = {}
        for clave, modelo in modelos.items():
            for marca, cid in (("a", a.id), ("b", b.id), ("shared", None)):
                fila = modelo(company_id=cid, name=f"{PREFIJO}{clave.upper()}-{marca}-{uuid.uuid4().hex[:4]}", is_active=True)
                s.add(fila)
                await s.flush()
                catalogos[f"{clave}_{marca}"] = fila.id
        # submovimientos: alimento (tenant), incubadora (tenant) y sus máquinas (derivadas), raza (global)
        for marca, cid in (("a", a.id), ("b", b.id), ("shared", None)):
            ft = FeedType(company_id=cid, name=f"{PREFIJO}FT-{marca}-{uuid.uuid4().hex[:4]}", is_active=True)
            s.add(ft)
            await s.flush()
            catalogos[f"ft_{marca}"] = ft.id
        for marca, cid in (("a", a.id), ("b", b.id)):
            hc = Hatchery(company_id=cid, name=f"{PREFIJO}INC-{marca}-{uuid.uuid4().hex[:4]}", is_active=True)
            s.add(hc)
            await s.flush()
            catalogos[f"hatch_{marca}"] = hc.id
            maq = Incubator(hatchery_id=hc.id, name=f"{PREFIJO}MAQ-{marca}-{uuid.uuid4().hex[:4]}", is_active=True)
            s.add(maq)
            await s.flush()
            catalogos[f"maq_{marca}"] = maq.id
        linea = GeneticLine(company_id=a.id, name=f"{PREFIJO}LINEA-{uuid.uuid4().hex[:4]}", is_active=True)
        s.add(linea)
        await s.flush()
        raza = Breed(genetic_line_id=linea.id, name=f"{PREFIJO}RAZA-{uuid.uuid4().hex[:4]}", is_active=True)
        s.add(raza)
        await s.flush()
        catalogos["raza"] = raza.id
        await s.commit()
        d = {"url": test_database_url, "a": a.id, "b": b.id, "op": op.id, "actor_b": actor_b.id, "global": global_.id,
             "granja": granja.id, "galpon": galpon.id, "lote": lote.id, "lote_h": lote_h.id}
        d.update(catalogos)
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM notifications WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM approval_actions WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM correction_logs WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM hatchery_params WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM feed_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM inspection_details WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM incubators WHERE name LIKE :p",
            "DELETE FROM hatchers WHERE name LIKE :p",
            "DELETE FROM hatcheries WHERE name LIKE :p",
            "DELETE FROM houses WHERE farm_id IN (SELECT id FROM farms WHERE name LIKE :p)",
            "DELETE FROM farms WHERE name LIKE :p",
            "DELETE FROM breeds WHERE name LIKE :p",
            "DELETE FROM genetic_lines WHERE name LIKE :p",
            "DELETE FROM suppliers WHERE name LIKE :p", "DELETE FROM transports WHERE name LIKE :p",
            "DELETE FROM mortality_causes WHERE name LIKE :p", "DELETE FROM cull_causes WHERE name LIKE :p",
            "DELETE FROM vaccines WHERE name LIKE :p", "DELETE FROM medications WHERE name LIKE :p",
            "DELETE FROM processing_plants WHERE name LIKE :p", "DELETE FROM feed_types WHERE name LIKE :p",
            "DELETE FROM company_business_units WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p", "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


# ── helpers ────────────────────────────────────────────────────────────────

async def _sql(esc, sql, **params):
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return (await s.execute(text(sql), params)).all()
    finally:
        await motor.dispose()


async def _cuenta(esc, sql, **params) -> int:
    return int((await _sql(esc, sql, **params))[0][0] or 0)


async def _eventos(esc) -> int:
    return await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE company_id = :a", a=esc["a"])


async def _auditorias(esc) -> int:
    return await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a AND action::text ILIKE 'created'", a=esc["a"])


def _cuerpo(esc, tipo, extra, campo=None, valor=None, lote="lote"):
    cuerpo = {"lot_id": esc[lote], "event_type": tipo, "event_date": recent_event_date(),
              "farm_id": esc["granja"], "house_id": esc["galpon"], **extra}
    if campo is not None:
        cuerpo[campo] = valor
    return cuerpo


async def _poblar(http_client, esc, n=500):
    """Saldo para que los decrementos (`cull_recording`, `bird_exit`) pasen `BR-01`."""
    r = await http_client.post("/api/v1/operations", headers=_token(esc["op"]),
                               json=_cuerpo(esc, "bird_reception", {"bird_movements": [{"sex": "mixed", "quantity": n}],
                                                                    "received_total": n, "dead_on_arrival": 0, "rejected_on_arrival": 0}))
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _post(http_client, esc, actor, cuerpo, company_id=None):
    return await http_client.post("/api/v1/operations", headers=_token(esc[actor], company_id), json=cuerpo)


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R179-01 — control: el catálogo propio se acepta en las siete familias
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("clave,campo,tipo,extra", FAMILIAS, ids=[f[1] for f in FAMILIAS])
async def test_r179_01_el_catalogo_propio_se_acepta(http_client, esc, clave, campo, tipo, extra):
    await _poblar(http_client, esc)
    r = await _post(http_client, esc, "op", _cuerpo(esc, tipo, extra, campo, esc[f"{clave}_a"]))
    assert r.status_code == 201, (f"AC-R179-01 · {campo} de la propia empresa", r.text)
    assert r.json()[campo] == esc[f"{clave}_a"]


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R179-02 · 05 — el catálogo de otra empresa se deniega en el alta, sin rastro
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("clave,campo,tipo,extra", FAMILIAS, ids=[f[1] for f in FAMILIAS])
async def test_r179_02_05_el_catalogo_ajeno_se_deniega_en_el_alta(http_client, esc, clave, campo, tipo, extra):
    await _poblar(http_client, esc)
    antes, aud = await _eventos(esc), await _auditorias(esc)
    r = await _post(http_client, esc, "op", _cuerpo(esc, tipo, extra, campo, esc[f"{clave}_b"]))
    assert _es_br(r, "BR-07"), (f"AC-R179-02 · {campo} de la empresa B", r.status_code, r.text)
    assert await _eventos(esc) == antes, "AC-R179-05: sin fila"
    assert await _auditorias(esc) == aud, "AC-R179-05: sin auditoría de alta"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R179-03 · 04 — edición y corrección hacia un catálogo ajeno
# ═══════════════════════════════════════════════════════════════════════════

async def test_r179_03_04_la_edicion_y_la_correccion_no_repuntan_a_un_catalogo_ajeno(http_client, esc):
    await _poblar(http_client, esc)
    r = await _post(http_client, esc, "op", _cuerpo(esc, "mortality_recording",
                                                    {"bird_movements": [{"sex": "mixed", "quantity": 1}]}, "cause_id", esc["mc_a"]))
    assert r.status_code == 201, r.text
    evento = r.json()["id"]

    async def _causa():
        return (await _sql(esc, "SELECT cause_id, version FROM operational_events WHERE id = :e", e=evento))[0]

    antes = await _causa()
    r = await http_client.put(f"/api/v1/operations/{evento}", headers=_token(esc["op"]), json={"cause_id": esc["mc_b"]})
    assert _es_br(r, "BR-07"), ("AC-R179-03: PUT hacia la causa de B", r.status_code, r.text)
    assert await _causa() == antes, "AC-R179-05: el evento no cambia"
    r = await http_client.post("/api/v1/corrections", headers=_token(esc["op"]),
                               json={"event_id": evento, "field_name": "cause_id", "corrected_value": str(esc["mc_b"]),
                                     "reason": f"{PREFIJO}corrección de prueba"})
    assert _es_br(r, "BR-07"), ("AC-R179-04: corrección hacia la causa de B", r.status_code, r.text)
    assert await _causa() == antes
    assert await _cuenta(esc, "SELECT count(*) FROM correction_logs WHERE event_id = :e", e=evento) == 0
    # control: hacia una causa propia, ambas superficies funcionan
    r = await http_client.put(f"/api/v1/operations/{evento}", headers=_token(esc["op"]), json={"cause_id": esc["mc_shared"]})
    assert r.status_code == 200, ("AC-R179-06: el catálogo compartido se acepta también al editar", r.text)


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R179-06 — control positivo: el catálogo compartido (company_id NULL) se acepta desde cualquier empresa
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("clave,campo,tipo,extra", FAMILIAS, ids=[f[1] for f in FAMILIAS])
async def test_r179_06_el_catalogo_compartido_se_acepta(http_client, esc, clave, campo, tipo, extra):
    await _poblar(http_client, esc)
    r = await _post(http_client, esc, "op", _cuerpo(esc, tipo, extra, campo, esc[f"{clave}_shared"]))
    assert r.status_code == 201, (f"AC-R179-06 · {campo} compartido (company_id NULL) debe aceptarse", r.status_code, r.text)
    assert r.json()[campo] == esc[f"{clave}_shared"]


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R179-07 · 12 — la empresa la deriva el servidor; la autoridad global sigue el mismo contrato
# ═══════════════════════════════════════════════════════════════════════════

async def test_r179_07_12_la_empresa_la_deriva_el_servidor(http_client, esc):
    await _poblar(http_client, esc)
    cuerpo = _cuerpo(esc, "vaccination", {}, "vaccine_id", esc["vac_b"])
    # el actor de A declara el contexto de B: su empresa efectiva no cambia (OD-11) y el lote sigue siendo de A
    r = await _post(http_client, esc, "op", cuerpo, company_id=esc["b"])
    assert r.status_code in (400, 403, 404), ("AC-R179-07: declarar otra empresa no autoriza el catálogo ajeno", r.status_code, r.text)
    # autoridad global situada en A: mismo contrato que el actor de empresa
    r = await _post(http_client, esc, "global", cuerpo, company_id=esc["a"])
    assert _es_br(r, "BR-07"), ("AC-R179-12: global situada en A con vacuna de B", r.status_code, r.text)
    r = await _post(http_client, esc, "global", _cuerpo(esc, "vaccination", {}, "vaccine_id", esc["vac_a"]), company_id=esc["a"])
    assert r.status_code == 201, ("AC-R179-12: global situada en A con vacuna de A", r.text)


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R179-08 · 09 · 10 — submovimientos: alimento e incubadora ajenos; máquina por su padre; raza global
# ═══════════════════════════════════════════════════════════════════════════

async def test_r179_08_el_alimento_ajeno_se_deniega(http_client, esc):
    antes = await _eventos(esc)
    r = await _post(http_client, esc, "op", _cuerpo(esc, "feed_registration",
                                                    {"feed_movements": [{"quantity_kg": 100.0, "feed_type_id": esc["ft_b"]}]}))
    assert _es_br(r, "BR-07"), ("AC-R179-08: tipo de alimento de la empresa B", r.status_code, r.text)
    assert await _eventos(esc) == antes
    r = await _post(http_client, esc, "op", _cuerpo(esc, "feed_registration",
                                                    {"feed_movements": [{"quantity_kg": 100.0, "feed_type_id": esc["ft_shared"]}]}))
    assert r.status_code == 201, ("AC-R179-06: el alimento compartido se acepta", r.text)


async def test_r179_08_09_la_incubadora_y_su_maquina_ajenas_se_deniegan(http_client, esc):
    base = {"lot_id": esc["lote_h"], "event_type": "incubation_load", "event_date": recent_event_date(),
            "farm_id": esc["granja"], "house_id": esc["galpon"]}
    r = await http_client.post("/api/v1/operations", headers=_token(esc["op"]),
                               json={**base, "egg_movements": [{"egg_type": "fertile", "quantity": 100}],
                                     "event_type": "egg_reception_hatchery"})
    assert r.status_code == 201, r.text
    antes = await _eventos(esc)
    r = await http_client.post("/api/v1/operations", headers=_token(esc["op"]),
                               json={**base, "hatchery_params": [{"quantity_loaded": 10, "hatchery_id": esc["hatch_b"]}]})
    assert _es_br(r, "BR-07"), ("AC-R179-08: incubadora de la empresa B", r.status_code, r.text)
    r = await http_client.post("/api/v1/operations", headers=_token(esc["op"]),
                               json={**base, "hatchery_params": [{"quantity_loaded": 10, "incubator_id": esc["maq_b"]}]})
    assert _es_br(r, "BR-07"), ("AC-R179-09: máquina cuya incubadora es de B", r.status_code, r.text)
    assert await _eventos(esc) == antes
    r = await http_client.post("/api/v1/operations", headers=_token(esc["op"]),
                               json={**base, "hatchery_params": [{"quantity_loaded": 10, "hatchery_id": esc["hatch_a"],
                                                                  "incubator_id": esc["maq_a"]}]})
    assert r.status_code == 201, ("control: incubadora y máquina propias", r.text)


async def test_r179_10_la_raza_global_sigue_aceptandose(http_client, esc):
    """`breeds` no tiene `company_id` (`PLATFORM_GLOBAL`): no se convierte en dato de inquilino."""
    r = await _post(http_client, esc, "op", _cuerpo(esc, "bird_reception",
                                                    {"bird_movements": [{"sex": "mixed", "quantity": 10, "breed_id": esc["raza"]}],
                                                     "received_total": 10, "dead_on_arrival": 0, "rejected_on_arrival": 0}))
    assert r.status_code == 201, ("AC-R179-10: la raza es global", r.text)

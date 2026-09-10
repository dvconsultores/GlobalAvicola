"""`GA-REM-021` enmienda B · `B01` · el cuadre de la recepción de reproductoras (`AC-B01-01…20`).

`Recomendación central §6`: «Que hembras + machos + mortalidad + rechazo cuadren contra recibido».
`recibido = Σ aves alojadas + mortalidad al arribo + rechazo` (`RR-12`, `BR-20`); sin tolerancia;
las alojadas son las entradas del saldo (`R-130`), la mortalidad al arribo y el rechazo no.

Escenario (prefijo `CUADRE-`):
    empresa A   breeder ON · broiler OFF · grandparent ON · hatchery ON
    empresa B   breeder ON · broiler ON
    operador    operations:create/read/update · breeder + broiler (histórica, OFF)
    operador_g  grandparent
    corrector   corrections:correct/read
    sin_perm    operations:read · acceso (Administrador de Accesos) · lectura (control transversal)
    actor_b     empresa B · global (comodín, sin empresa)
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

PREFIJO = "CUADRE-"


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
    from app.integrations.sap.models import SapReference, SapReferenceType
    from app.masters.models import BirdTypeEnum, Company, Farm, FarmType, House, Lot, LotStatus

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, code, on in ((a, "breeder", True), (a, "broiler", False), (a, "grandparent", True), (a, "hatchery", True),
                                  (b, "breeder", True), (b, "broiler", True)):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id, is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        PA = PermissionAction

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos

        ops = [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ)]
        roles = {
            "operador": _rol("Op", a.id, ops),
            "corrector": _rol("Corr", a.id, [("corrections", PA.CORRECT), ("corrections", PA.READ), ("operations", PA.READ)]),
            "sin_perm": _rol("SinPerm", a.id, [("operations", PA.READ)]),
            "lectura": _rol("Lectura", a.id, [("review", PA.READ), ("corrections", PA.READ), ("audit", PA.READ), ("reports", PA.READ), ("operations", PA.READ)]),
            "acceso": _rol("Acceso", a.id, [("business_units", PA.READ), ("business_units", PA.CREATE), ("business_units", PA.UPDATE), ("business_units", PA.DELETE)]),
            "b": _rol("OpB", b.id, ops),
            "global": _rol("Global", None, []),
        }
        await s.flush()
        for rol, permisos in roles.values():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        for accion in PA:
            s.add(Permission(role_id=roles["global"][0].id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Cuadre", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        u = {"operador": _usuario(a.id, "OP", roles["operador"][0]), "operador_g": _usuario(a.id, "OPG", roles["operador"][0]),
             "corrector": _usuario(a.id, "CORR", roles["corrector"][0]), "sin_perm": _usuario(a.id, "SINPERM", roles["sin_perm"][0]),
             "lectura": _usuario(a.id, "LECT", roles["lectura"][0]), "acceso": _usuario(a.id, "ACC", roles["acceso"][0]),
             "actor_b": _usuario(b.id, "B", roles["b"][0]), "global": _usuario(None, "GLOBAL", roles["global"][0])}
        s.add_all(u.values())
        await s.flush()
        for k in ("operador", "corrector", "sin_perm", "lectura"):
            await conceder_unidad(s, user=u[k], company_business_unit=hab[(a.id, "breeder")])
        await conceder_unidad(s, user=u["operador"], company_business_unit=hab[(a.id, "broiler")])
        await conceder_unidad(s, user=u["operador_g"], company_business_unit=hab[(a.id, "grandparent")])
        for code in ("breeder", "broiler"):
            await conceder_unidad(s, user=u["actor_b"], company_business_unit=hab[(b.id, code)])

        granja_a = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA-A", code=f"{PREFIJO}GA-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        granja_b = Farm(company_id=b.id, name=f"{PREFIJO}GRANJA-B", code=f"{PREFIJO}GB-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        s.add_all([granja_a, granja_b])
        await s.flush()
        galpon_a = House(farm_id=granja_a.id, name=f"{PREFIJO}GALPON-A", capacity=10_000, is_active=True)
        galpon_b = House(farm_id=granja_b.id, name=f"{PREFIJO}GALPON-B", capacity=10_000, is_active=True)
        s.add_all([galpon_a, galpon_b])
        await s.flush()

        def _lote(empresa, marca, tipo, estado=LotStatus.ACTIVE):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", bird_type=tipo, status=estado)

        lotes = {"lr": _lote(a, "LR", BirdTypeEnum.BREEDER), "lr2": _lote(a, "LR2", BirdTypeEnum.BREEDER), "lp": _lote(a, "LP", BirdTypeEnum.BROILER),
                 "lg": _lote(a, "LG", BirdTypeEnum.GRANDPARENT), "lh": _lote(a, "LH", BirdTypeEnum.HATCHERY), "ln": _lote(a, "LN", None),
                 "lb": _lote(b, "LB", BirdTypeEnum.BREEDER), "lpb": _lote(b, "LPB", BirdTypeEnum.BROILER)}
        s.add_all(lotes.values())
        oc = SapReference(company_id=a.id, ref_type=SapReferenceType.PURCHASE_ORDER, sap_code=f"{PREFIJO}OC-{uuid.uuid4().hex[:6]}",
                          quantity=250, unit="aves", is_active=True)
        s.add(oc)
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "granja_a": granja_a.id, "galpon_a": galpon_a.id, "granja_b": granja_b.id, "galpon_b": galpon_b.id,
             "oc": oc.sap_code, "url": test_database_url}
        d.update({k: v.id for k, v in u.items()})
        d.update({k: v.id for k, v in lotes.items()})
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
            "DELETE FROM chick_batches WHERE destination_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM sap_references WHERE sap_code LIKE :p",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM houses WHERE farm_id IN (SELECT id FROM farms WHERE name LIKE :p)",
            "DELETE FROM farms WHERE name LIKE :p",
            "DELETE FROM company_business_units WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
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


async def _recepciones(esc, lote) -> int:
    return await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE lot_id = :l AND event_type::text ILIKE 'bird_reception'", l=lote)


async def _saldo(esc, lote) -> int:
    from app.operations.validators import get_current_bird_balance

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return await get_current_bird_balance(s, lote)
    finally:
        await motor.dispose()


def _cuerpo(esc, lote, *, filas=((("female", 50), ("male", 45))), total=100, dead=3, rej=2, fecha=None, granja="granja_a", galpon="galpon_a", **extra):
    cuerpo = {"lot_id": esc[lote], "event_type": "bird_reception", "event_date": fecha or recent_event_date(),
              "farm_id": esc[granja], "house_id": esc[galpon],
              "bird_movements": [{"sex": sexo, "quantity": n, "target_house_id": esc[galpon]} for sexo, n in filas]}
    for clave, valor in (("received_total", total), ("dead_on_arrival", dead), ("rejected_on_arrival", rej)):
        if valor is not None:
            cuerpo[clave] = valor
    cuerpo.update(extra)
    return cuerpo


async def _recibir(http_client, esc, actor, lote, company_id=None, **kw):
    return await http_client.post("/api/v1/operations", headers=_token(esc[actor], company_id), json=_cuerpo(esc, lote, **kw))


# ═══════════════════════════════════════════════════════════════════════════
#  AC-B01-01 · 03 · 05 · 15 — la recepción cuadrada
# ═══════════════════════════════════════════════════════════════════════════

async def test_b01_01_03_05_la_recepcion_cuadrada_se_registra_y_las_alojadas_son_la_suma_de_las_filas(http_client, esc):
    r = await _recibir(http_client, esc, "operador", "lr")  # 100 = 50 + 45 + 3 + 2
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert (cuerpo["received_total"], cuerpo["dead_on_arrival"], cuerpo["rejected_on_arrival"]) == (100, 3, 2), "AC-B01-01: se persisten y se leen"
    fila = (await _sql(esc, "SELECT received_total, dead_on_arrival, rejected_on_arrival FROM operational_events WHERE id = :e", e=cuerpo["id"]))[0]
    assert tuple(fila) == (100, 3, 2)
    assert await _cuenta(esc, "SELECT count(*) FROM bird_movements WHERE event_id = :e", e=cuerpo["id"]) == 2, "AC-B01-03: dos filas ♀/♂"
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE entity_type = 'operational_event' AND entity_id = :e AND action::text ILIKE 'created'", e=str(cuerpo["id"])) == 1, "AC-B01-15"
    # AC-B01-05: identidad exacta con muertas y rechazadas > 0; cuadra con una sola fila también
    r = await _recibir(http_client, esc, "operador", "lr2", filas=(("female", 90),), total=97, dead=5, rej=2)
    assert r.status_code == 201, r.text


async def test_b01_04_06_el_descuadre_se_rechaza_y_no_deja_rastro(http_client, esc):
    antes_audit = await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a", a=esc["a"])
    for total in (101, 99):  # uno de más y uno de menos: distingue == de >= / <=
        r = await _recibir(http_client, esc, "operador", "lr", total=total)
        assert _es_br(r, "BR-20"), ("AC-B01-04", total, r.text)
        detalle = r.json().get("detail") or r.json().get("message") or r.text
        for numero in ("95", str(total), "3", "2"):
            assert numero in str(detalle), ("el mensaje nombra los cuatro números", numero, detalle)
    assert await _recepciones(esc, esc["lr"]) == 0, "AC-B01-06: cero eventos"
    assert await _cuenta(esc, "SELECT count(*) FROM bird_movements bm JOIN operational_events e ON e.id = bm.event_id WHERE e.lot_id = :l", l=esc["lr"]) == 0
    assert await _saldo(esc, esc["lr"]) == 0
    assert await _cuenta(esc, "SELECT count(*) FROM operational_alerts WHERE lot_id = :l", l=esc["lr"]) == 0
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :a", a=esc["a"]) == antes_audit, "AC-B01-15: la denegada no audita"


async def test_b01_02_07_19_dos_entregas_parciales_cuadradas_contra_la_misma_oc_y_el_saldo_son_las_alojadas(http_client, esc):
    # OC de 250 aves: dos entregas de 100 recibidas (95 alojadas cada una) cuadran y se aceptan (OD-04); la tercera excede (BR-18)
    for _ in range(2):
        r = await _recibir(http_client, esc, "operador", "lr", sap_document_ref=esc["oc"])
        assert r.status_code == 201, r.text
    assert await _saldo(esc, esc["lr"]) == 190, "AC-B01-19: el saldo son las alojadas (95 + 95), no las recibidas (100 + 100)"
    r = await _recibir(http_client, esc, "operador", "lr", sap_document_ref=esc["oc"])
    assert _es_br(r, "BR-18"), ("control GA-TD-014: 200 + 100 > 250", r.text)
    # R-130: una salida mayor que el saldo se acota; una igual pasa
    def _mortalidad(n):
        return {"lot_id": esc["lr"], "event_type": "mortality_recording", "event_date": recent_event_date(),
                "farm_id": esc["granja_a"], "house_id": esc["galpon_a"], "bird_movements": [{"sex": "mixed", "quantity": n}]}
    r = await http_client.post("/api/v1/operations", headers=_token(esc["operador"]), json=_mortalidad(191))
    assert r.status_code == 400, r.text
    r = await http_client.post("/api/v1/operations", headers=_token(esc["operador"]), json=_mortalidad(190))
    assert r.status_code == 201, r.text
    assert await _saldo(esc, esc["lr"]) == 0


async def test_b01_08_09_el_total_alojado_nunca_viene_del_cliente(http_client, esc):
    # AC-B01-08: `extra_data` coherente con el total declarado, filas que no cuadran → la identidad se calcula sobre las filas
    r = await _recibir(http_client, esc, "operador", "lr", filas=(("female", 50), ("male", 40)), total=100, dead=3, rej=2,
                       extra_data={"placed_total": 95, "declared_quantity": 100})
    assert _es_br(r, "BR-20"), ("AC-B01-08", r.text)
    # AC-B01-09: company_id / business_unit_id del cuerpo se ignoran
    r = await http_client.post("/api/v1/operations", headers=_token(esc["operador"]), json={**_cuerpo(esc, "lr"), "company_id": esc["b"], "business_unit_id": 999})
    assert r.status_code == 201 and r.json()["company_id"] == esc["a"], r.text


# ═══════════════════════════════════════════════════════════════════════════
#  AC-B01-10 … 14 — cadena de seguridad (misma ruta que B05: una aserción por capa)
# ═══════════════════════════════════════════════════════════════════════════

async def test_b01_10_14_empresa_unidad_concesion_rbac_y_contexto_global(http_client, esc):
    assert _es_br(await _recibir(http_client, esc, "actor_b", "lr", granja="granja_b", galpon="galpon_b"), "BR-07"), "AC-B01-10: otra empresa"
    assert _es_br(await _recibir(http_client, esc, "global", "lr"), "BR-07"), "AC-B01-14: global sin contexto"
    assert _es_br(await _recibir(http_client, esc, "global", "lr", company_id=esc["b"]), "BR-07"), "AC-B01-10: global situada en B"
    r = await _recibir(http_client, esc, "global", "lp", company_id=esc["a"], total=None, dead=0, rej=None)
    assert r.status_code == 403, ("AC-B01-11: la autoridad global no salta la unidad apagada", r.text)
    assert _es_br(await _recibir(http_client, esc, "operador", "lp", total=None, dead=0, rej=None), "BR-07"), "AC-B01-11: concesión histórica sobre unidad apagada"
    assert _es_br(await _recibir(http_client, esc, "operador_g", "lr"), "BR-07"), "AC-B01-12: sin la unidad del lote"
    for actor in ("sin_perm", "acceso", "lectura"):
        assert (await _recibir(http_client, esc, actor, "lr")).status_code == 403, ("AC-B01-13", actor)
    assert await _recepciones(esc, esc["lr"]) == 0 and await _recepciones(esc, esc["lp"]) == 0


# ═══════════════════════════════════════════════════════════════════════════
#  AC-B01-16 · 17 · 20 — obligatoriedad, aplicabilidad por cadena, tipos
# ═══════════════════════════════════════════════════════════════════════════

async def test_b01_16_20_los_tres_datos_son_obligatorios_y_enteros_en_reproductoras(http_client, esc):
    for faltante in ({"total": None}, {"dead": None}, {"rej": None}):
        r = await _recibir(http_client, esc, "operador", "lr", **faltante)
        assert r.status_code == 400, ("AC-B01-16", faltante, r.text)
    r = await _recibir(http_client, esc, "operador", "lr", filas=(("female", 100),), total=100, dead=0, rej=0)
    assert r.status_code == 201, ("AC-B01-16: el 0 explícito vale", r.text)
    for malo in ({"dead": -1}, {"rej": -1}, {"total": 0}, {"dead": 3.5}, {"total": "cien"}):
        r = await _recibir(http_client, esc, "operador", "lr", **malo)
        assert r.status_code == 422, ("AC-B01-20", malo, r.text)


async def test_b01_17_la_identidad_y_sus_campos_solo_viven_en_la_recepcion_de_reproductoras(http_client, esc):
    # engorde: total y rechazo prohibidos; mortalidad inicial opcional (spec.md §4.8) y fuera del saldo
    assert (await _recibir(http_client, esc, "actor_b", "lpb", granja="granja_b", galpon="galpon_b", filas=(("mixed", 100),), total=103, dead=3, rej=None)).status_code == 400
    assert (await _recibir(http_client, esc, "actor_b", "lpb", granja="granja_b", galpon="galpon_b", filas=(("mixed", 100),), total=None, dead=None, rej=0)).status_code == 400
    r = await _recibir(http_client, esc, "actor_b", "lpb", granja="granja_b", galpon="galpon_b", filas=(("mixed", 100),), total=None, dead=3, rej=None)
    assert r.status_code == 201 and r.json()["dead_on_arrival"] == 3, r.text
    assert await _saldo(esc, esc["lpb"]) == 100, "AC-B01-17: la mortalidad al arribo no entra al saldo"
    # otro tipo de evento
    r = await http_client.post("/api/v1/operations", headers=_token(esc["operador"]), json={
        "lot_id": esc["lr"], "event_type": "feed_registration", "event_date": recent_event_date(),
        "feed_movements": [{"quantity_kg": 5.0}], "received_total": 100, "dead_on_arrival": 0, "rejected_on_arrival": 0})
    assert r.status_code == 400, r.text
    # progenitoras, incubadora (global situada en A, unidades habilitadas) y lote sin cadena
    assert (await _recibir(http_client, esc, "operador_g", "lg")).status_code == 400
    assert (await _recibir(http_client, esc, "global", "lh", company_id=esc["a"])).status_code == 400
    assert (await _recibir(http_client, esc, "operador", "ln")).status_code == 400
    for lote in ("lr", "lg", "lh", "ln"):
        assert await _recepciones(esc, esc[lote]) == 0, lote


# ═══════════════════════════════════════════════════════════════════════════
#  AC-B01-18 — edición y corrección
# ═══════════════════════════════════════════════════════════════════════════

async def test_b01_18_la_edicion_revalida_y_la_correccion_uno_a_uno_no_puede_descuadrar(http_client, esc):
    ev = (await _recibir(http_client, esc, "operador", "lr")).json()  # 100 = 95 + 3 + 2
    ruta = f"/api/v1/operations/{ev['id']}"
    r = await http_client.put(ruta, headers=_token(esc["operador"]), json={"received_total": 101})
    assert _es_br(r, "BR-20"), ("edición que descuadra", r.text)
    r = await http_client.put(ruta, headers=_token(esc["operador"]), json={"received_total": 101, "dead_on_arrival": 4})
    assert r.status_code == 200 and (r.json()["received_total"], r.json()["dead_on_arrival"]) == (101, 4), r.text
    # una corrección de un solo sumando siempre descuadra un registro cuadrado: no es corregible uno a uno
    for campo, valor in (("dead_on_arrival", "5"), ("received_total", "102"), ("rejected_on_arrival", "3")):
        r = await http_client.post("/api/v1/corrections", headers=_token(esc["corrector"]),
                                   json={"event_id": ev["id"], "field_name": campo, "corrected_value": valor, "reason": f"{PREFIJO}recuento"})
        assert r.status_code == 400, (campo, r.text)
    fila = (await _sql(esc, "SELECT received_total, dead_on_arrival, rejected_on_arrival FROM operational_events WHERE id = :e", e=ev["id"]))[0]
    assert tuple(fila) == (101, 4, 2), "ninguna vía deja la recepción descuadrada"
    assert await _cuenta(esc, "SELECT count(*) FROM correction_logs WHERE event_id = :e", e=ev["id"]) == 0


async def test_r168_la_muestra_tomada_de_la_recepcion_se_persiste(http_client, esc):
    """`AC-R168-02` (control): el campo de evento `sample_size` («Muestra tomada», Rec. §6) se persiste y se lee."""
    r = await _recibir(http_client, esc, "operador", "lr", sample_size=30)
    assert r.status_code == 201, r.text
    assert r.json()["sample_size"] == 30
    assert (await _sql(esc, "SELECT sample_size FROM operational_events WHERE id = :e", e=r.json()["id"]))[0][0] == 30


# ═══════════════════════════════════════════════════════════════════════════
#  R-167 · reproducción controlada: un hecho de negocio, un efecto productivo
# ═══════════════════════════════════════════════════════════════════════════

async def test_r167_la_mortalidad_al_arribo_afecta_al_saldo_exactamente_cero_veces(http_client, esc):
    """`R-167` (WAVE B tranche 8, pre-flight). Traza observada, no inspeccionada:

    recibidas 100 · muertas al arribo 5 · rechazadas 5 · alojadas 90  →  saldo 90.
    Ni el alta, ni la edición de la tupla, ni la lectura del saldo descuentan `dead_on_arrival`:
    las muertas al arribo nunca entraron a la parvada y el sistema no crea ningún evento de
    mortalidad por ellas. Un evento `mortality_recording` posterior es **otro hecho** (aves
    alojadas que murieron) y descuenta una sola vez.
    """
    r = await _recibir(http_client, esc, "operador", "lr", filas=(("female", 50), ("male", 40)), total=100, dead=5, rej=5)
    assert r.status_code == 201, r.text
    ev = r.json()
    assert await _saldo(esc, esc["lr"]) == 90, "las alojadas entran; muertas al arribo y rechazadas no"
    assert await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE lot_id = :l AND event_type::text ILIKE 'mortality_recording'", l=esc["lr"]) == 0, \
        "el alta no fabrica ningún evento de mortalidad por las muertas al arribo"
    assert await _cuenta(esc, "SELECT count(*) FROM operational_alerts WHERE lot_id = :l", l=esc["lr"]) == 0
    # editar la tupla (5 → 6 muertas, 100 → 101 recibidas) no toca el saldo: las alojadas no cambiaron
    r = await http_client.put(f"/api/v1/operations/{ev['id']}", headers=_token(esc["operador"]), json={"received_total": 101, "dead_on_arrival": 6})
    assert r.status_code == 200, r.text
    assert await _saldo(esc, esc["lr"]) == 90
    # un evento de mortalidad es otro hecho y descuenta exactamente una vez
    r = await http_client.post("/api/v1/operations", headers=_token(esc["operador"]), json={
        "lot_id": esc["lr"], "event_type": "mortality_recording", "event_date": recent_event_date(),
        "farm_id": esc["granja_a"], "house_id": esc["galpon_a"], "bird_movements": [{"sex": "mixed", "quantity": 5}]})
    assert r.status_code == 201, r.text
    assert await _saldo(esc, esc["lr"]) == 85

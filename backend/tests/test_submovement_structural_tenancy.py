"""`GA-REM-002` enmienda E · `R-180` · las referencias **estructurales** de los submovimientos son de la empresa
del evento (`AC-R180-01…14`).

El evento pasa la cadena de inquilino porque **sus propias** columnas se verifican (`verificar_ubicacion`); sus hijos,
no. Un galpón no declara `company_id`: pertenece a la empresa **a través de su granja**, y esa cadena ya la recorre
`tenancy.verificar_pertenencia`. Lo que faltaba era recorrerla también para los hijos.

    UNA CLAVE FORÁNEA VÁLIDA NO PRUEBA QUE EL GALPÓN SEA DE LA EMPRESA DEL EVENTO.

Escenario (prefijo `SUBM-`):
    empresa A (breeder ON · hatchery OFF) · granjas `A1` y `A2` · galpones `A1H` y `A2H` · lote de A
    empresa B (breeder ON) · granja `B1` · galpón `B1H` · lote de B
    op (permisos y unidad correctos) · sin_perm · sin_unidad · actor_b · global
El único elemento ajeno en cada caso es la referencia del hijo: todo lo demás es legítimo.
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
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
from app.auth.security import create_access_token
from tests.time_reference import recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "SUBM-"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


@pytest_asyncio.fixture
async def esc(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import BirdTypeEnum, Company, Farm, FarmType, House, Lot, LotStatus

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, code, on in ((a, "breeder", True), (a, "hatchery", False), (b, "breeder", True)):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id, is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        PA = PermissionAction
        operar = [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE),
                  ("corrections", PA.CREATE), ("corrections", PA.READ), ("lots", PA.READ)]

        def _rol(nombre, company_id, permisos):
            r = Role(name=f"{PREFIJO}{nombre}-{uuid.uuid4().hex[:6]}", company_id=company_id, is_active=True)
            s.add(r)
            return r, permisos

        roles = {"op": _rol("Op", a.id, operar), "sin_unidad": _rol("SinUnidad", a.id, operar),
                 "sin_perm": _rol("SinPerm", a.id, [("operations", PA.READ)]),
                 "actor_b": _rol("OpB", b.id, operar), "global": _rol("Global", None, [])}
        await s.flush()
        for rol, permisos in roles.values():
            for modulo, accion in permisos:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        for accion in PA:
            s.add(Permission(role_id=roles["global"][0].id, module="*", action=accion, scope_type="all"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Subm", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        u = {k: _usuario(a.id, k.upper(), roles[k][0]) for k in ("op", "sin_unidad", "sin_perm")}
        u["actor_b"] = _usuario(b.id, "ACTORB", roles["actor_b"][0])
        u["global"] = _usuario(None, "GLOBAL", roles["global"][0])
        s.add_all(u.values())
        await s.flush()
        for k in ("op", "sin_perm"):  # `sin_unidad` queda deliberadamente sin conceder
            await conceder_unidad(s, user=u[k], company_business_unit=hab[(a.id, "breeder")])
        await conceder_unidad(s, user=u["actor_b"], company_business_unit=hab[(b.id, "breeder")])

        def _granja(empresa, marca):
            return Farm(company_id=empresa.id, name=f"{PREFIJO}{marca}", code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:4]}",
                        farm_type=FarmType.BREEDING, is_active=True)

        f_a1, f_a2, f_b1 = _granja(a, "FA1"), _granja(a, "FA2"), _granja(b, "FB1")
        s.add_all([f_a1, f_a2, f_b1])
        await s.flush()
        h_a1 = House(farm_id=f_a1.id, name=f"{PREFIJO}HA1", capacity=100_000, is_active=True)
        h_a2 = House(farm_id=f_a2.id, name=f"{PREFIJO}HA2", capacity=100_000, is_active=True)
        h_b1 = House(farm_id=f_b1.id, name=f"{PREFIJO}HB1", capacity=100_000, is_active=True)
        s.add_all([h_a1, h_a2, h_b1])
        await s.flush()
        lote = Lot(company_id=a.id, lot_code=f"{PREFIJO}LA-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.BREEDER,
                   status=LotStatus.ACTIVE, farm_id=f_a1.id, house_id=h_a1.id)
        lote_b = Lot(company_id=b.id, lot_code=f"{PREFIJO}LB-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.BREEDER,
                     status=LotStatus.ACTIVE, farm_id=f_b1.id, house_id=h_b1.id)
        lote_h = Lot(company_id=a.id, lot_code=f"{PREFIJO}LH-{uuid.uuid4().hex[:6]}", bird_type=BirdTypeEnum.HATCHERY,
                     status=LotStatus.ACTIVE, farm_id=f_a1.id, house_id=h_a1.id)
        s.add_all([lote, lote_b, lote_h])
        await s.flush()
        await s.commit()
        d = {"url": test_database_url, "a": a.id, "b": b.id, "fa1": f_a1.id, "fa2": f_a2.id, "fb1": f_b1.id,
             "ha1": h_a1.id, "ha2": h_a2.id, "hb1": h_b1.id, "lote": lote.id, "lote_b": lote_b.id, "lote_h": lote_h.id}
        d.update({k: v.id for k, v in u.items()})
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM notifications WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM correction_logs WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM approval_actions WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM inspection_details WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_storage WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM houses WHERE farm_id IN (SELECT id FROM farms WHERE name LIKE :p)",
            "DELETE FROM farms WHERE name LIKE :p",
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


async def _verdad(esc) -> dict:
    """Lo que existe en la base para la empresa A: filas padre, filas hijas y auditoría de éxito."""
    p = {"c": esc["a"]}
    return {
        "eventos": await _cuenta(esc, "SELECT count(*) FROM operational_events WHERE company_id = :c", **p),
        "aves": await _cuenta(esc, "SELECT count(*) FROM bird_movements WHERE event_id IN "
                                   "(SELECT id FROM operational_events WHERE company_id = :c)", **p),
        "inspecciones": await _cuenta(esc, "SELECT count(*) FROM inspection_details WHERE event_id IN "
                                           "(SELECT id FROM operational_events WHERE company_id = :c)", **p),
        "almacenes": await _cuenta(esc, "SELECT count(*) FROM egg_storage WHERE event_id IN "
                                        "(SELECT id FROM operational_events WHERE company_id = :c)", **p),
        "auditoria": await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE company_id = :c AND "
                                        "entity_type = 'operational_event' AND action::text ILIKE 'created'", **p),
        "ajenas": await _cuenta(esc, "SELECT count(*) FROM bird_movements bm JOIN operational_events e ON e.id = bm.event_id "
                                     "LEFT JOIN houses ho ON ho.id = bm.source_house_id LEFT JOIN farms fo ON fo.id = ho.farm_id "
                                     "LEFT JOIN houses hd ON hd.id = bm.target_house_id LEFT JOIN farms fd ON fd.id = hd.farm_id "
                                     "WHERE e.company_id = :c AND (fo.company_id <> :c OR fd.company_id <> :c)", **p),
    }


def _es_br(r, codigo: str) -> bool:
    try:
        return r.json().get("rule") == codigo
    except Exception:
        return False


async def _post(http_client, esc, cuerpo, actor="op", company_id=None):
    return await http_client.post("/api/v1/operations", headers=_token(esc[actor], company_id), json=cuerpo)


def _base(esc, tipo="bird_transfer", lote="lote"):
    return {"lot_id": esc[lote], "event_type": tipo, "event_date": recent_event_date(),
            "farm_id": esc["fa1"], "house_id": esc["ha1"]}


def _aves(origen=None, destino=None, cantidad=10, sexo="mixed"):
    fila = {"sex": sexo, "quantity": cantidad}
    if origen is not None:
        fila["source_house_id"] = origen
    if destino is not None:
        fila["target_house_id"] = destino
    return fila


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R180-01 · 08 — los controles positivos: no sobre-bloquear
# ═══════════════════════════════════════════════════════════════════════════

async def test_r180_01_08_los_galpones_de_la_misma_empresa_se_aceptan(http_client, esc):
    """`AC-R180-01` y `AC-R180-08`: dentro de la empresa se acepta, **también entre granjas distintas**.

    La frontera que `R-180` cierra es la de **empresa**. `House` y `Farm` no declaran unidad de negocio (se deriva
    del lote), de modo que aquí no se inventa ninguna restricción por granja ni por unidad (`OD-10` intacto).
    """
    r = await _post(http_client, esc, {**_base(esc), "bird_movements": [_aves(esc["ha1"], esc["ha2"])]})
    assert r.status_code == 201, ("AC-R180-08: entre granjas de la misma empresa debe aceptarse", r.text)
    movimiento = (await _sql(esc, "SELECT source_house_id, target_house_id FROM bird_movements WHERE event_id = :e",
                             e=r.json()["id"]))[0]
    assert tuple(movimiento) == (esc["ha1"], esc["ha2"])
    r = await _post(http_client, esc, {**_base(esc), "bird_movements": [_aves(esc["ha1"], esc["ha1"])]})
    assert r.status_code == 201, ("AC-R180-01: dentro del mismo galpón", r.text)


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R180-02 · 03 · 04 — origen y destino son dos contratos independientes
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("caso", ["origen", "destino", "ambos"])
async def test_r180_02_04_el_galpon_ajeno_se_deniega(http_client, esc, caso):
    antes = await _verdad(esc)
    origen = esc["hb1"] if caso in ("origen", "ambos") else esc["ha1"]
    destino = esc["hb1"] if caso in ("destino", "ambos") else esc["ha2"]
    r = await _post(http_client, esc, {**_base(esc), "bird_movements": [_aves(origen, destino)]})
    assert r.status_code == 400 and _es_br(r, "BR-07"), (f"AC-R180-02/03/04 · {caso} ajeno", r.status_code, r.text[:160])
    despues = await _verdad(esc)
    assert despues["eventos"] == antes["eventos"], "no se persiste el evento padre"
    assert despues["aves"] == antes["aves"], "no se persiste el movimiento hijo"
    assert despues["auditoria"] == antes["auditoria"], "no se registra auditoría de éxito"
    assert despues["ajenas"] == 0, "ninguna referencia entre empresas queda en la base"


async def test_r180_13_el_galpon_ajeno_se_comporta_como_inexistente(http_client, esc):
    """`AC-R180-13`: la denegación no revela que el galpón existe en otra empresa."""
    r = await _post(http_client, esc, {**_base(esc), "bird_movements": [_aves(esc["ha1"], esc["hb1"])]})
    cuerpo = r.text.lower()
    assert _es_br(r, "BR-07") and "no encontrado" in cuerpo, (r.status_code, r.text[:160])
    for filtrado in ("otra empresa", "company b", str(esc["b"]), "pertenece"):
        assert filtrado not in cuerpo, f"la respuesta filtra información: {filtrado}"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R180-05 · 06 — las otras dos referencias estructurales
# ═══════════════════════════════════════════════════════════════════════════

async def test_r180_05_el_galpon_de_la_inspeccion_ajeno_se_deniega(http_client, esc):
    antes = await _verdad(esc)
    cuerpo = {**_base(esc, "farm_inspection"),
              "inspection_details": [{"house_id": esc["hb1"], "parameter": "temperatura", "value": "30"}]}
    r = await _post(http_client, esc, cuerpo)
    assert r.status_code == 400 and _es_br(r, "BR-07"), ("AC-R180-05", r.status_code, r.text[:160])
    despues = await _verdad(esc)
    assert (despues["eventos"], despues["inspecciones"]) == (antes["eventos"], antes["inspecciones"])
    cuerpo["inspection_details"][0]["house_id"] = esc["ha2"]
    assert (await _post(http_client, esc, cuerpo)).status_code == 201, "el galpón propio sigue aceptándose"


async def test_r180_06_el_lote_del_almacenamiento_ajeno_se_deniega(http_client, esc):
    antes = await _verdad(esc)
    cuerpo = {**_base(esc, "egg_collection"), "egg_movements": [{"egg_type": "fertile", "quantity": 100}],
              "egg_storage_records": [{"lot_id": esc["lote_b"], "arrival_date": recent_event_date(), "eggs_received": 100}]}
    r = await _post(http_client, esc, cuerpo)
    assert r.status_code == 400 and _es_br(r, "BR-07"), ("AC-R180-06", r.status_code, r.text[:160])
    despues = await _verdad(esc)
    assert (despues["eventos"], despues["almacenes"]) == (antes["eventos"], antes["almacenes"])
    cuerpo["egg_storage_records"][0]["lot_id"] = esc["lote"]
    assert (await _post(http_client, esc, cuerpo)).status_code == 201, "el lote propio sigue aceptándose"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R180-07 — atomicidad: nada se persiste parcialmente
# ═══════════════════════════════════════════════════════════════════════════

async def test_r180_07_los_hijos_mixtos_no_persisten_nada(http_client, esc):
    """`AC-R180-07`: con un hijo válido y otro ajeno no queda **nada** — ni el evento, ni el hijo válido."""
    antes = await _verdad(esc)
    cuerpo = {**_base(esc), "bird_movements": [
        _aves(esc["ha1"], esc["ha2"], 5),
        _aves(esc["ha1"], esc["hb1"], 5, "male"),   # el segundo hijo es el ajeno
        _aves(esc["ha1"], esc["ha2"], 5, "female"),
    ]}
    r = await _post(http_client, esc, cuerpo)
    assert r.status_code == 400 and _es_br(r, "BR-07"), ("AC-R180-07", r.status_code, r.text[:160])
    despues = await _verdad(esc)
    assert despues["eventos"] == antes["eventos"], "quedó un evento padre huérfano"
    assert despues["aves"] == antes["aves"], "quedaron hijos válidos de una operación denegada"
    assert despues["ajenas"] == 0


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R180-09 · 10 · 11 · 12 — la empresa la deriva el servidor; el acceso sigue mandando
# ═══════════════════════════════════════════════════════════════════════════

async def test_r180_09_10_el_cliente_no_autoriza_el_galpon_ajeno(http_client, esc):
    """`AC-R180-09`/`10`: declarar otra empresa en el contexto no habilita su galpón; la autoridad global situada en
    A tampoco alcanza un galpón de B, y sin empresa seleccionada falla cerrado."""
    r = await _post(http_client, esc, {**_base(esc), "bird_movements": [_aves(esc["ha1"], esc["hb1"])]},
                    actor="op", company_id=esc["b"])
    assert r.status_code in (400, 403, 404), ("AC-R180-09: contexto declarado por el cliente", r.status_code, r.text[:140])
    r = await _post(http_client, esc, {**_base(esc), "bird_movements": [_aves(esc["ha1"], esc["hb1"])]},
                    actor="global", company_id=esc["a"])
    assert r.status_code == 400 and _es_br(r, "BR-07"), ("AC-R180-10: global situada en A con galpón de B", r.status_code, r.text[:140])
    r = await _post(http_client, esc, {**_base(esc), "bird_movements": [_aves(esc["ha1"], esc["ha2"])]}, actor="global")
    assert r.status_code in (400, 403, 404), ("AC-R180-10: global sin empresa seleccionada falla cerrado", r.status_code)
    r = await _post(http_client, esc, {**_base(esc), "bird_movements": [_aves(esc["ha1"], esc["ha2"])]},
                    actor="global", company_id=esc["a"])
    assert r.status_code == 201, ("AC-R180-10: situada en A y con galpones de A, procede", r.text[:140])


async def test_r180_11_12_el_acceso_manda_antes_que_la_estructura(http_client, esc):
    """`AC-R180-11`/`12`: unidad de empresa apagada, otra empresa, sin permiso y sin unidad concedida."""
    valido = {**_base(esc), "bird_movements": [_aves(esc["ha1"], esc["ha2"])]}
    r = await _post(http_client, esc, {**_base(esc, lote="lote_h"), "bird_movements": [_aves(esc["ha1"], esc["ha2"])]})
    # En el **alta**, el lote de una unidad apagada queda fuera del ámbito y la denegación llega como `BR-07`
    # («lote no encontrado»), no como `403`: la unidad apagada hace invisible el lote antes de discutir permisos.
    assert r.status_code in (400, 403), ("AC-R180-11: unidad de la empresa apagada (OD-16)", r.status_code, r.text[:140])
    assert r.status_code == 403 or _es_br(r, "BR-07"), ("AC-R180-11: denegación con contrato conocido", r.text[:140])
    assert (await _post(http_client, esc, valido, actor="actor_b")).status_code in (400, 403, 404), "AC-R180-12: otra empresa"
    assert (await _post(http_client, esc, valido, actor="sin_perm")).status_code == 403, "AC-R180-12: sin permiso"
    r = await _post(http_client, esc, valido, actor="sin_unidad")
    # Sin unidad concedida el lote también queda fuera de ámbito: el contrato es el mismo que el de la unidad
    # apagada, `BR-07` antes que `403`. Lo que importa aquí es que la validación estructural **no** sustituye
    # al control de acceso: se deniega antes de llegar a ella.
    assert r.status_code in (400, 403) and (r.status_code == 403 or _es_br(r, "BR-07")), \
        ("AC-R180-12: sin unidad concedida", r.status_code, r.text[:140])
    assert (await _verdad(esc))["ajenas"] == 0


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R180-14 — `PUT` y corrección no son superficies escritoras de submovimientos
# ═══════════════════════════════════════════════════════════════════════════

async def test_r180_14_la_edicion_y_la_correccion_no_escriben_submovimientos(http_client, esc):
    """`AC-R180-14`: hoy es cierto por construcción; se versiona para que deje de ser una lectura y pase a ser un
    guardián. Si alguna vez `PUT` o la corrección admitieran submovimientos, esta prueba enrojece y obliga a
    extender la enmienda E a esa superficie."""
    from app.operations.schemas import OperationalEventUpdate, SUBMOVEMENT_FIELDS

    campos = set(OperationalEventUpdate.model_fields)
    assert not (campos & SUBMOVEMENT_FIELDS), ("PUT declara submovimientos: la enmienda E debe cubrir esa superficie",
                                               sorted(campos & SUBMOVEMENT_FIELDS))
    for estructural in ("source_house_id", "target_house_id"):
        assert estructural not in campos, f"PUT declara {estructural}"

    from app.corrections.service import campos_corregibles

    corregibles = campos_corregibles()
    assert not (corregibles & SUBMOVEMENT_FIELDS), ("la corrección alcanza submovimientos", sorted(corregibles & SUBMOVEMENT_FIELDS))

    r = await _post(http_client, esc, {**_base(esc), "bird_movements": [_aves(esc["ha1"], esc["ha2"])]})
    assert r.status_code == 201
    evento = r.json()["id"]
    antes = (await _sql(esc, "SELECT source_house_id, target_house_id FROM bird_movements WHERE event_id = :e", e=evento))[0]
    r = await http_client.put(f"/api/v1/operations/{evento}", headers=_token(esc["op"]),
                              json={"bird_movements": [_aves(esc["ha1"], esc["hb1"])], "observations": f"{PREFIJO}intento"})
    despues = (await _sql(esc, "SELECT source_house_id, target_house_id FROM bird_movements WHERE event_id = :e", e=evento))[0]
    assert tuple(despues) == tuple(antes), ("un PUT cambió el galpón de un submovimiento", r.status_code, tuple(antes), tuple(despues))

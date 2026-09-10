"""`GA-REM-031` enmienda A · `R-178` · el linaje efectivo sigue el estado de sus eventos; la historia se conserva; la reasignación de un evento casado
se deniega (`AC-R178-01…11`).

Escenario (prefijo `LINA-`): empresa A (breeder ON · hatchery ON · broiler OFF) y B · operador con operations + corrections + lots:read/create en
breeder + hatchery · granja_a (lr, lr2 breeder) · planta_a (lh, lh2 hatchery) · granja_c (lr3 breeder: receptor de pollitos) · granja_b (lb) ·
lbo (broiler A, unidad apagada). Cadena: egg_collection en lr → egg_dispatch (destino planta_a) → egg_reception_hatchery en lh → EggBatch;
birth en lh → chick_dispatch (destino granja_c) → bird_reception en lr3 → ChickBatch(egg_batch_id).
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
from tests.time_reference import earlier_event_date, recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "LINA-"


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
    from app.masters.models import BirdTypeEnum, Company, Farm, FarmType, House, Lot, LotStatus

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, code, on in ((a, "breeder", True), (a, "hatchery", True), (a, "broiler", False), (b, "breeder", True), (b, "hatchery", True)):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id, is_enabled=on)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        PA = PermissionAction
        ops = [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ), ("lots", PA.CREATE),
               ("corrections", PA.CORRECT), ("corrections", PA.READ)]
        rol_a = Role(name=f"{PREFIJO}Op-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        rol_b = Role(name=f"{PREFIJO}OpB-{uuid.uuid4().hex[:6]}", company_id=b.id, is_active=True)
        s.add_all([rol_a, rol_b])
        await s.flush()
        for rol in (rol_a, rol_b):
            for modulo, accion in ops:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        await s.flush()

        def _usuario(company_id, marca, rol):
            return User(first_name=marca, last_name="Lina", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                        username=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"),
                        company_id=company_id, role_id=rol.id, is_active=True)

        operador, actor_b = _usuario(a.id, "OP", rol_a), _usuario(b.id, "B", rol_b)
        s.add_all([operador, actor_b])
        await s.flush()
        for code in ("breeder", "hatchery"):
            await conceder_unidad(s, user=operador, company_business_unit=hab[(a.id, code)])
            await conceder_unidad(s, user=actor_b, company_business_unit=hab[(b.id, code)])

        granjas = {k: Farm(company_id=(b if k == "granja_b" else a).id, name=f"{PREFIJO}{k.upper()}", code=f"{PREFIJO}{k[:2].upper()}-{uuid.uuid4().hex[:4]}",
                           farm_type=FarmType.BREEDING, is_active=True) for k in ("granja_a", "planta_a", "granja_c", "granja_b")}
        s.add_all(granjas.values())
        await s.flush()
        galpones = {k: House(farm_id=f.id, name=f"{PREFIJO}G-{k}", capacity=100_000, is_active=True) for k, f in granjas.items()}
        s.add_all(galpones.values())
        await s.flush()

        def _lote(empresa, marca, tipo, granja):
            return Lot(company_id=empresa.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", bird_type=tipo, status=LotStatus.ACTIVE,
                       farm_id=granjas[granja].id, house_id=galpones[granja].id)

        lotes = {"lr": _lote(a, "LR", BirdTypeEnum.BREEDER, "granja_a"), "lr2": _lote(a, "LR2", BirdTypeEnum.BREEDER, "granja_a"),
                 "lh": _lote(a, "LH", BirdTypeEnum.HATCHERY, "planta_a"), "lh2": _lote(a, "LH2", BirdTypeEnum.HATCHERY, "planta_a"),
                 "lr3": _lote(a, "LR3", BirdTypeEnum.BREEDER, "granja_c"), "lbo": _lote(a, "LBO", BirdTypeEnum.BROILER, "granja_a"),
                 "lb": _lote(b, "LB", BirdTypeEnum.BREEDER, "granja_b")}
        s.add_all(lotes.values())
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "operador": operador.id, "actor_b": actor_b.id, "url": test_database_url}
        d.update({k: v.id for k, v in granjas.items()})
        d.update({f"galpon_{k}": v.id for k, v in galpones.items()})
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
            "DELETE FROM chick_batches WHERE hatchery_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p) OR destination_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM egg_batches WHERE source_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p) OR hatchery_lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM hatchery_params WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
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


async def _vinculos_huevo(esc, despacho_id):
    return await _sql(esc, "SELECT id, source_lot_id, hatchery_lot_id, reception_event_id, quantity_dispatched, quantity_received FROM egg_batches "
                           "WHERE dispatch_event_id = :d", d=despacho_id)


async def _saldos(esc, lote):
    from app.operations.validators import get_current_bird_balance, get_egg_balance, get_hatchery_egg_balance, get_viable_chick_balance

    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return {"aves": await get_current_bird_balance(s, lote), "viables": await get_viable_chick_balance(s, lote),
                    "huevos": await get_egg_balance(s, lote), "incubadora": await get_hatchery_egg_balance(s, lote)}
    finally:
        await motor.dispose()


def _ubicacion(lote):
    return {"lr": "granja_a", "lr2": "granja_a", "lh": "planta_a", "lh2": "planta_a", "lr3": "granja_c", "lbo": "granja_a", "lb": "granja_b"}[lote]


def _cuerpo(esc, lote, tipo, n, *, destino=None, fecha=None):
    g = _ubicacion(lote)
    cuerpo = {"lot_id": esc[lote], "event_type": tipo, "event_date": fecha or recent_event_date(), "farm_id": esc[g], "house_id": esc[f"galpon_{g}"]}
    if tipo in ("egg_collection", "egg_dispatch", "egg_reception_hatchery"):
        cuerpo["egg_movements"] = [{"egg_type": "fertile", "quantity": n}]
    else:
        cuerpo["bird_movements"] = [{"sex": "mixed", "quantity": n}]
        if tipo == "birth_registration":
            cuerpo.update({"chicks_healthy": n, "chicks_weak": 0})
        if tipo == "bird_reception":
            cuerpo.update({"received_total": n, "dead_on_arrival": 0, "rejected_on_arrival": 0})
    if destino:
        cuerpo["destination_farm_id"] = esc[destino]
    return cuerpo


async def _alta(http_client, esc, lote, tipo, n, **kw) -> int:
    r = await http_client.post("/api/v1/operations", headers=_token(esc["operador"]), json=_cuerpo(esc, lote, tipo, n, **kw))
    assert r.status_code == 201, (tipo, lote, r.text)
    return r.json()["id"]


async def _arbol(http_client, esc, lote, actor="operador"):
    r = await http_client.get(f"/api/v1/lots/{esc[lote]}/traceability", headers=_token(esc[actor]))
    assert r.status_code == 200, r.text
    return r.json()


async def _put(http_client, esc, event_id, cuerpo, actor="operador"):
    return await http_client.put(f"/api/v1/operations/{event_id}", headers=_token(esc[actor]), json=cuerpo)


async def _corregir(http_client, esc, event_id, campo, valor):
    return await http_client.post("/api/v1/corrections", headers=_token(esc["operador"]),
                                  json={"event_id": event_id, "field_name": campo, "corrected_value": str(valor), "reason": f"{PREFIJO}corrección de prueba"})


async def _cancelar(http_client, esc, event_id):
    return await http_client.post(f"/api/v1/operations/{event_id}/cancel", headers=_token(esc["operador"]))


async def _cadena_huevo(http_client, esc, *, origen="lr", destino_lote="lh", n=100):
    """Recolección en el origen, despacho con destino declarado (planta) y recepción en la incubadora → un EggBatch."""
    await _alta(http_client, esc, origen, "egg_collection", n)
    despacho = await _alta(http_client, esc, origen, "egg_dispatch", n, destino=_ubicacion(destino_lote), fecha=earlier_event_date())
    recepcion = await _alta(http_client, esc, destino_lote, "egg_reception_hatchery", n)
    return despacho, recepcion


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R178-01 — control: el par crea un vínculo orientado y visible desde ambos lotes
# ═══════════════════════════════════════════════════════════════════════════

async def test_r178_01_control_el_par_crea_un_vinculo_orientado_visible_desde_ambos_lotes(http_client, esc):
    despacho, recepcion = await _cadena_huevo(http_client, esc)
    filas = await _vinculos_huevo(esc, despacho)
    assert len(filas) == 1 and filas[0][1] == esc["lr"] and filas[0][2] == esc["lh"] and filas[0][3] == recepcion and filas[0][5] == 100, filas
    a, b = await _arbol(http_client, esc, "lr"), await _arbol(http_client, esc, "lh")
    assert [x["hatchery_lot_id"] for x in a["egg_batches_sent"]] == [esc["lh"]] and a["egg_batches_sent"][0]["quantity_received"] == 100
    assert [x["source_lot_id"] for x in b["egg_batches_received"]] == [esc["lr"]]


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R178-02 · 11 — anular el despacho: el vínculo deja de ser efectivo, la fila y la auditoría permanecen
# ═══════════════════════════════════════════════════════════════════════════

async def test_r178_02_11_anular_el_despacho_retira_el_vinculo_efectivo_y_conserva_la_historia(http_client, esc):
    despacho, recepcion = await _cadena_huevo(http_client, esc)
    assert (await _cancelar(http_client, esc, despacho)).status_code == 200
    a, b = await _arbol(http_client, esc, "lr"), await _arbol(http_client, esc, "lh")
    assert a["egg_batches_sent"] == [], ("AC-R178-02: un traspaso anulado desaparece del lado emisor (OD-10 §2.5)", a["egg_batches_sent"])
    assert b["egg_batches_received"] == [], ("AC-R178-02: y del lado receptor", b["egg_batches_received"])
    assert len(await _vinculos_huevo(esc, despacho)) == 1, "AC-R178-03/11: la historia se conserva (BR-10): la fila no se borra"
    assert await _cuenta(esc, "SELECT count(*) FROM audit_logs WHERE entity_type = 'operational_event' AND entity_id = :e AND action::text ILIKE 'cancelled'", e=str(despacho)) == 1
    assert (await _cancelar(http_client, esc, despacho)).status_code == 400, "AC-R178-11: segunda anulación sin efecto"
    assert (await _arbol(http_client, esc, "lr"))["egg_batches_sent"] == []
    assert (await _saldos(esc, esc["lh"]))["incubadora"] == 100, "la recepción sigue vigente en su saldo (independiente del despacho)"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R178-03 — anular la recepción: el vínculo queda incompleto; una recepción nueva vuelve a casarse
# ═══════════════════════════════════════════════════════════════════════════

async def test_r178_03_anular_la_recepcion_deja_el_vinculo_incompleto_y_una_nueva_recepcion_lo_recasa(http_client, esc):
    despacho, recepcion = await _cadena_huevo(http_client, esc)
    assert (await _cancelar(http_client, esc, recepcion)).status_code == 200
    a, b = await _arbol(http_client, esc, "lr"), await _arbol(http_client, esc, "lh")
    assert len(a["egg_batches_sent"]) == 1 and a["egg_batches_sent"][0]["quantity_received"] is None and a["egg_batches_sent"][0]["reception_date"] is None, \
        ("AC-R178-03: el emisor ve el despacho sin recepción (cadena incompleta, GA-REM-008 AC04)", a["egg_batches_sent"])
    assert b["egg_batches_received"] == [], ("AC-R178-03: el receptor ya no lo recibió", b["egg_batches_received"])
    assert len(await _vinculos_huevo(esc, despacho)) == 1, "la fila se conserva"
    nueva = await _alta(http_client, esc, "lh", "egg_reception_hatchery", 90)
    filas = await _vinculos_huevo(esc, despacho)
    assert len(filas) == 1 and filas[0][3] == nueva and filas[0][5] == 90, ("control: la recepción nueva se casa con el despacho (GA-REM-031)", filas)
    a, b = await _arbol(http_client, esc, "lr"), await _arbol(http_client, esc, "lh")
    assert a["egg_batches_sent"][0]["quantity_received"] == 90 and [x["source_lot_id"] for x in b["egg_batches_received"]] == [esc["lr"]]


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R178-04 · 05 · 06 — un evento casado no se reasigna (lote ni destino declarado); nada cambia
# ═══════════════════════════════════════════════════════════════════════════

async def test_r178_04_05_06_un_evento_casado_no_se_reasigna(http_client, esc):
    despacho, recepcion = await _cadena_huevo(http_client, esc)
    await _alta(http_client, esc, "lr2", "egg_collection", 100)  # lr2 tiene saldo: R-173 dejaría mover el despacho
    fila_antes = await _vinculos_huevo(esc, despacho)
    saldos_antes = {k: await _saldos(esc, esc[k]) for k in ("lr", "lr2", "lh", "lh2")}
    for etiqueta, r in (
        ("AC-R178-04 PUT lot_id del despacho", await _put(http_client, esc, despacho, {"lot_id": esc["lr2"]})),
        ("AC-R178-05 corrección lot_id del despacho", await _corregir(http_client, esc, despacho, "lot_id", esc["lr2"])),
        ("AC-R178-05 PUT destination_farm_id del despacho", await _put(http_client, esc, despacho, {"destination_farm_id": esc["granja_c"]})),
        ("AC-R178-06 PUT lot_id de la recepción", await _put(http_client, esc, recepcion, {"lot_id": esc["lh2"]})),
    ):
        assert r.status_code == 400, (etiqueta, r.status_code, r.text)
    assert await _vinculos_huevo(esc, despacho) == fila_antes, "el vínculo no cambia"
    lotes = await _sql(esc, "SELECT id, lot_id, coalesce(destination_farm_id, 0) FROM operational_events WHERE id IN (:d, :r) ORDER BY id", d=despacho, r=recepcion)
    assert [(l[1], l[2]) for l in lotes] == [(esc["lr"], esc["planta_a"]), (esc["lh"], 0)], "los eventos no cambian"
    assert {k: await _saldos(esc, esc[k]) for k in ("lr", "lr2", "lh", "lh2")} == saldos_antes
    assert await _cuenta(esc, "SELECT count(*) FROM correction_logs WHERE event_id = :e", e=despacho) == 0


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R178-07 — la denegación por inquilino/unidad (R-173) no toca el linaje; ningún vínculo entre empresas
# ═══════════════════════════════════════════════════════════════════════════

async def test_r178_07_la_denegacion_de_inquilino_o_unidad_no_toca_el_linaje(http_client, esc):
    despacho, _ = await _cadena_huevo(http_client, esc)
    fila_antes = await _vinculos_huevo(esc, despacho)
    assert _es_br(await _put(http_client, esc, despacho, {"lot_id": esc["lb"]}), "BR-07"), "otra empresa"
    assert _es_br(await _put(http_client, esc, despacho, {"lot_id": esc["lbo"]}), "BR-07"), "unidad apagada"
    assert await _vinculos_huevo(esc, despacho) == fila_antes
    assert await _cuenta(esc, "SELECT count(*) FROM egg_batches WHERE source_lot_id IN (SELECT id FROM lots WHERE company_id = :b) "
                              "OR hatchery_lot_id IN (SELECT id FROM lots WHERE company_id = :b)", b=esc["b"]) == 0, "ningún vínculo alcanza a B"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R178-08 — cadena de pollitos: ChickBatch con egg_batch_id; mover → 400; anular → desaparece
# ═══════════════════════════════════════════════════════════════════════════

async def test_r178_08_la_cadena_de_pollitos_sigue_el_mismo_contrato(http_client, esc):
    despacho_huevo, _ = await _cadena_huevo(http_client, esc)
    huevo_id = (await _vinculos_huevo(esc, despacho_huevo))[0][0]
    await _alta(http_client, esc, "lh", "birth_registration", 100)
    await _alta(http_client, esc, "lh2", "birth_registration", 100)  # lh2 con viables: R-173 dejaría mover el despacho
    despacho = await _alta(http_client, esc, "lh", "chick_dispatch", 100, destino="granja_c", fecha=earlier_event_date())
    await _alta(http_client, esc, "lr3", "bird_reception", 100)
    filas = await _sql(esc, "SELECT id, hatchery_lot_id, destination_lot_id, egg_batch_id, quantity_received FROM chick_batches WHERE dispatch_event_id = :d", d=despacho)
    assert len(filas) == 1 and filas[0][1] == esc["lh"] and filas[0][2] == esc["lr3"] and filas[0][3] == huevo_id and filas[0][4] == 100, ("AC-R178-01 pollitos", filas)
    assert [x["destination_lot_id"] for x in (await _arbol(http_client, esc, "lh"))["chick_batches_sent"]] == [esc["lr3"]]
    r = await _put(http_client, esc, despacho, {"lot_id": esc["lh2"]})
    assert r.status_code == 400, ("AC-R178-08: el despacho de pollitos casado no se mueve", r.status_code, r.text)
    assert (await _cancelar(http_client, esc, despacho)).status_code == 200
    assert (await _arbol(http_client, esc, "lh"))["chick_batches_sent"] == [], "AC-R178-08: anulado → desaparece"
    assert (await _arbol(http_client, esc, "lr3"))["chick_batches_received"] == []
    assert await _cuenta(esc, "SELECT count(*) FROM chick_batches WHERE dispatch_event_id = :d", d=despacho) == 1, "la fila se conserva"
    assert (await _saldos(esc, esc["lh"]))["viables"] == 100, "R-173: anular la salida restaura los viables"


# ═══════════════════════════════════════════════════════════════════════════
#  AC-R178-09 · 10 — controles: sin vínculo se mueve como hoy; el vínculo manual sigue visible
# ═══════════════════════════════════════════════════════════════════════════

async def test_r178_09_10_controles_sin_vinculo_se_mueve_y_el_enlace_manual_sigue(http_client, esc):
    await _alta(http_client, esc, "lr", "egg_collection", 100)
    await _alta(http_client, esc, "lr2", "egg_collection", 100)
    suelto = await _alta(http_client, esc, "lr", "egg_dispatch", 40, destino="granja_c")  # nadie recibe en granja_c: sin vínculo
    assert await _vinculos_huevo(esc, suelto) == []
    r = await _put(http_client, esc, suelto, {"lot_id": esc["lr2"]})
    assert r.status_code == 200, ("AC-R178-09: sin vínculo, R-173 manda", r.text)
    assert (await _saldos(esc, esc["lr"]))["huevos"] == 100 and (await _saldos(esc, esc["lr2"]))["huevos"] == 60
    r = await http_client.post("/api/v1/lots/egg-batches", headers=_token(esc["operador"]),
                               json={"source_lot_id": esc["lr"], "hatchery_lot_id": esc["lh2"], "quantity_dispatched": 10, "dispatch_date": recent_event_date()})
    assert r.status_code == 201, r.text
    assert [x["hatchery_lot_id"] for x in (await _arbol(http_client, esc, "lr"))["egg_batches_sent"]] == [esc["lh2"]], "AC-R178-10: el enlace manual se lista"

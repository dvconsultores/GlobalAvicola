"""`GA-REM-021` enmienda B · `B02` · `GA-REM-037` enmienda B · los pesos de la recepción de reproductoras contra la curva del lote.

`Recomendación central §6`: «Que los pesos estén dentro de rango esperado». El rango es la curva estándar fijada al lote a la
edad del lote el día de la recepción (`OD-06`, `RR-13`); fuera de rango alerta y no bloquea; sin curva o sin punto para esa edad,
`NO_REFERENCE` declarado.

Curvas de fixture (gramos):  v1: día 0 [38 · 40 · 42] · día 10 [100 · 120 · 140]  →  día 5 interpolado [69 · 80 · 91]
                             v2: día 0 [50 · 55 · 60] · día 10 [110 · 130 · 150]  (se activa después de crear los lotes)
                             c7: día 7 [60 · 70 · 80] · día 14 [90 · 100 · 110]   (sin punto en el día 0)
Lotes (start_date = hace 7 días; la recepción «reciente» cae en el día 0):
    lr0  breeder · v1        lr7  breeder · c7        lrn  breeder · sin línea        lpb  broiler · v1
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

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
from tests.time_reference import days_ago, iso_days_ago, recent_event_date

pytestmark = pytest.mark.asyncio

PREFIJO = "PESO-"
DIAS_INICIO = 7  # el lote empezó el mismo día que `recent_event_date()`


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
    from app.masters.models import (BirdTypeEnum, Company, Farm, FarmType, GeneticLine, GeneticWeightCurve,
                                    GeneticWeightCurvePoint, House, Lot, LotStatus)

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for empresa, code in ((a, "breeder"), (a, "broiler"), (b, "breeder")):
            fila = CompanyBusinessUnit(company_id=empresa.id, business_unit_id=unidades[code].id, is_enabled=True)
            s.add(fila)
            await s.flush()
            hab[(empresa.id, code)] = fila
        PA = PermissionAction
        ops = [("operations", PA.CREATE), ("operations", PA.READ), ("operations", PA.UPDATE), ("lots", PA.READ)]
        rol_a = Role(name=f"{PREFIJO}Op-{uuid.uuid4().hex[:6]}", company_id=a.id, is_active=True)
        rol_b = Role(name=f"{PREFIJO}OpB-{uuid.uuid4().hex[:6]}", company_id=b.id, is_active=True)
        s.add_all([rol_a, rol_b])
        await s.flush()
        for rol in (rol_a, rol_b):
            for modulo, accion in ops:
                s.add(Permission(role_id=rol.id, module=modulo, action=accion, scope_type="company"))
        op = User(first_name="OP", last_name="Peso", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                  username=f"{PREFIJO}OP-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"), company_id=a.id, role_id=rol_a.id, is_active=True)
        ob = User(first_name="B", last_name="Peso", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                  username=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", hashed_password=hash_password("x1234567"), company_id=b.id, role_id=rol_b.id, is_active=True)
        s.add_all([op, ob])
        await s.flush()
        await conceder_unidad(s, user=op, company_business_unit=hab[(a.id, "breeder")])
        await conceder_unidad(s, user=op, company_business_unit=hab[(a.id, "broiler")])
        await conceder_unidad(s, user=ob, company_business_unit=hab[(b.id, "breeder")])

        granja = Farm(company_id=a.id, name=f"{PREFIJO}GRANJA-A", code=f"{PREFIJO}GA-{uuid.uuid4().hex[:4]}", farm_type=FarmType.BREEDING, is_active=True)
        s.add(granja)
        await s.flush()
        galpon = House(farm_id=granja.id, name=f"{PREFIJO}GALPON-A", capacity=10_000, is_active=True)
        s.add(galpon)
        await s.flush()

        def _linea(marca):
            return GeneticLine(company_id=a.id, name=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", code=f"{PREFIJO}{marca}", is_active=True)

        la, lb7 = _linea("LA"), _linea("LB7")
        s.add_all([la, lb7])
        await s.flush()

        def _curva(linea, etiqueta, activa, puntos):
            c = GeneticWeightCurve(genetic_line_id=linea.id, version_label=etiqueta, is_active=activa, source=f"{PREFIJO}fixture")
            s.add(c)
            return c, puntos

        curvas = {"v1": _curva(la, "v1", True, ((0, 38, 40, 42), (10, 100, 120, 140))),
                  "v2": _curva(la, "v2", False, ((0, 50, 55, 60), (10, 110, 130, 150))),
                  "c7": _curva(lb7, "c7", True, ((7, 60, 70, 80), (14, 90, 100, 110)))}
        await s.flush()
        for c, puntos in curvas.values():
            for edad, mn, tg, mx in puntos:
                s.add(GeneticWeightCurvePoint(curve_id=c.id, age_days=edad, min_weight=mn, target_weight=tg, max_weight=mx))
        inicio = datetime.combine(days_ago(DIAS_INICIO), datetime.min.time()).replace(tzinfo=timezone.utc)

        def _lote(marca, tipo, linea=None, curva=None):
            return Lot(company_id=a.id, lot_code=f"{PREFIJO}{marca}-{uuid.uuid4().hex[:6]}", bird_type=tipo, status=LotStatus.ACTIVE,
                       genetic_line_id=linea.id if linea else None, weight_curve_id=curvas[curva][0].id if curva else None,
                       start_date=inicio, farm_id=granja.id, house_id=galpon.id)

        lotes = {"lr0": _lote("LR0", BirdTypeEnum.BREEDER, la, "v1"), "lr5": _lote("LR5", BirdTypeEnum.BREEDER, la, "v1"),
                 "lrv": _lote("LRV", BirdTypeEnum.BREEDER, la, "v1"), "lr7": _lote("LR7", BirdTypeEnum.BREEDER, lb7, "c7"),
                 "lrn": _lote("LRN", BirdTypeEnum.BREEDER), "lpb": _lote("LPB", BirdTypeEnum.BROILER, la, "v1")}
        s.add_all(lotes.values())
        await s.flush()
        await s.commit()
        d = {"a": a.id, "b": b.id, "granja": granja.id, "galpon": galpon.id, "op": op.id, "ob": ob.id, "linea_a": la.id,
             "v1": curvas["v1"][0].id, "v2": curvas["v2"][0].id, "url": test_database_url}
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
            "DELETE FROM operational_alerts WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM bird_movements WHERE event_id IN (SELECT id FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM genetic_weight_curve_points WHERE curve_id IN (SELECT id FROM genetic_weight_curves WHERE genetic_line_id IN (SELECT id FROM genetic_lines WHERE name LIKE :p))",
            "DELETE FROM genetic_weight_curves WHERE genetic_line_id IN (SELECT id FROM genetic_lines WHERE name LIKE :p)",
            "DELETE FROM genetic_lines WHERE name LIKE :p",
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


async def _alertas(esc, lote):
    filas = await _sql(esc, "SELECT alert_type, threshold_value, actual_value, message, company_id, event_id FROM operational_alerts WHERE lot_id = :l ORDER BY id", l=lote)
    return [dict(zip(("tipo", "umbral", "real", "mensaje", "empresa", "evento"), f)) for f in filas]


async def _recibir(http_client, esc, lote, hembras, machos, *, fecha=None, actor="op", breeder=True, **extra):
    cuerpo = {"lot_id": esc[lote], "event_type": "bird_reception", "event_date": fecha or recent_event_date(),
              "farm_id": esc["granja"], "house_id": esc["galpon"],
              "bird_movements": [{"sex": "female", "quantity": 50, "avg_weight": hembras, "target_house_id": esc["galpon"]},
                                 {"sex": "male", "quantity": 45, "avg_weight": machos, "target_house_id": esc["galpon"]}]}
    if breeder:
        cuerpo.update({"received_total": 95, "dead_on_arrival": 0, "rejected_on_arrival": 0})
    cuerpo.update(extra)
    return await http_client.post("/api/v1/operations", headers=_token(esc[actor]), json=cuerpo)


async def _evaluacion(http_client, esc, evento, actor="op"):
    return await http_client.get(f"/api/v1/operations/{evento}/weight-evaluation", headers=_token(esc[actor]))


# ═══════════════════════════════════════════════════════════════════════════

async def test_b02_01_02_04_10_punto_exacto_del_dia_cero_dentro_de_rango(http_client, esc):
    r = await _recibir(http_client, esc, "lr0", 40, 41)
    assert r.status_code == 201, r.text
    ev = r.json()
    pesos = [f[0] for f in await _sql(esc, "SELECT avg_weight FROM bird_movements WHERE event_id = :e ORDER BY id", e=ev["id"])]
    assert pesos == [40, 41], ("AC-B02-01: el peso se persiste", pesos)
    e = (await _evaluacion(http_client, esc, ev["id"])).json()
    assert e["age_days"] == 0 and e["curve_version_label"] == "v1", ("AC-B02-02/03: curva del lote, edad del día", e)
    assert [(f["status"], f["expected_min"], f["expected_target"], f["expected_max"]) for f in e["evaluations"]] == \
        [("within_standard", 38, 40, 42), ("within_standard", 38, 40, 42)], ("AC-B02-04/10", e)
    assert await _alertas(esc, esc["lr0"]) == []


async def test_b02_06_07_los_bordes_son_inclusivos(http_client, esc):
    r = await _recibir(http_client, esc, "lr0", 38, 42)
    assert r.status_code == 201, r.text
    e = (await _evaluacion(http_client, esc, r.json()["id"])).json()
    assert [f["status"] for f in e["evaluations"]] == ["within_standard", "within_standard"], e
    assert await _alertas(esc, esc["lr0"]) == []


async def test_b02_08_09_11_19_20_fuera_de_rango_alerta_y_no_bloquea(http_client, esc):
    r = await _recibir(http_client, esc, "lr0", 30, 50, extra_data={"declared_avg_weight_f": 40, "declared_avg_weight_m": 40})
    assert r.status_code == 201, ("AC-B02-19: fuera de rango no bloquea", r.text)
    ev = r.json()
    e = (await _evaluacion(http_client, esc, ev["id"])).json()
    assert [f["status"] for f in e["evaluations"]] == ["below_standard", "above_standard"], ("AC-B02-08/09/11", e)
    alertas = await _alertas(esc, esc["lr0"])
    assert [(x["tipo"], x["umbral"], x["real"]) for x in alertas] == [("weight_deviation", 38.0, 30.0), ("weight_deviation", 42.0, 50.0)], alertas
    for x in alertas:
        assert "0 días" in x["mensaje"] and "v1" in x["mensaje"] and x["empresa"] == esc["a"] and x["evento"] == ev["id"], ("AC-B02-20", x)
    r = await http_client.post(f"/api/v1/operations/{ev['id']}/submit", headers=_token(esc["op"]))
    assert r.status_code == 200, ("AC-B02-19: puede enviarse a revisión", r.text)


async def test_b02_03_05_la_edad_es_la_del_dia_de_la_recepcion_y_se_interpola(http_client, esc):
    r = await _recibir(http_client, esc, "lr5", 69, 68, fecha=iso_days_ago(DIAS_INICIO - 5))
    assert r.status_code == 201, r.text
    e = (await _evaluacion(http_client, esc, r.json()["id"])).json()
    assert e["age_days"] == 5, ("AC-B02-03", e)
    assert [(f["status"], f["expected_min"], f["expected_target"], f["expected_max"]) for f in e["evaluations"]] == \
        [("within_standard", 69, 80, 91), ("below_standard", 69, 80, 91)], ("AC-B02-05: número exacto interpolado", e)
    alertas = await _alertas(esc, esc["lr5"])
    assert [(x["umbral"], x["real"]) for x in alertas] == [(69.0, 68.0)] and "5 días" in alertas[0]["mensaje"], alertas


async def test_b02_12_sin_referencia_se_declara_y_no_se_inventa(http_client, esc):
    r = await _recibir(http_client, esc, "lrn", 10, 500)
    assert r.status_code == 201, r.text
    e = (await _evaluacion(http_client, esc, r.json()["id"])).json()
    assert e["reason"] == "lot_without_genetic_line" and all(f["status"] == "no_reference" for f in e["evaluations"]), e
    r = await _recibir(http_client, esc, "lr7", 10, 500)  # la tabla empieza en el día 7: el día 0 no se extrapola
    assert r.status_code == 201, r.text
    e = (await _evaluacion(http_client, esc, r.json()["id"])).json()
    assert e["reason"] == "age_outside_curve_table" and e["curve_version_label"] == "c7" and \
        all(f["status"] == "no_reference" and f["expected_min"] is None for f in e["evaluations"]), e
    assert await _alertas(esc, esc["lrn"]) == [] and await _alertas(esc, esc["lr7"]) == []


async def test_b02_18_engorde_no_alerta_por_fuente(http_client, esc):
    r = await _recibir(http_client, esc, "lpb", 30, 50, breeder=False)
    assert r.status_code == 201, r.text
    assert await _alertas(esc, esc["lpb"]) == [], "AC-B02-18: §4.8 no exige alertas por desviación"


async def test_b02_22_la_evaluacion_usa_la_version_fijada_al_lote(http_client, esc):
    motor = create_async_engine(esc["url"])
    async with motor.begin() as c:  # se publica v2 después de crear los lotes
        await c.execute(text("UPDATE genetic_weight_curves SET is_active = false WHERE id = :v1"), {"v1": esc["v1"]})
        await c.execute(text("UPDATE genetic_weight_curves SET is_active = true WHERE id = :v2"), {"v2": esc["v2"]})
    await motor.dispose()
    r = await _recibir(http_client, esc, "lrv", 40, 42)  # dentro de v1 [38-42]; por debajo de v2 [50-60]
    assert r.status_code == 201, r.text
    e = (await _evaluacion(http_client, esc, r.json()["id"])).json()
    assert e["curve_version_label"] == "v1" and [f["status"] for f in e["evaluations"]] == ["within_standard", "within_standard"], e
    assert await _alertas(esc, esc["lrv"]) == []


async def test_b02_13_otra_empresa_no_lee_la_evaluacion(http_client, esc):
    ev = (await _recibir(http_client, esc, "lr0", 40, 41)).json()
    assert (await _evaluacion(http_client, esc, ev["id"], actor="ob")).status_code == 404, "AC-B02-13 (control AC28)"

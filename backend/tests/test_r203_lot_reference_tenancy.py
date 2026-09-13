"""`R-203` · Tenencia estructural en alta y edición de lotes (galpón, línea, curva).

Diseño: `specs/R-203/R-203_RED_E2E_UAT_DESIGN.md §1` y clarificación **C-07**.

En HEAD, `house_id` y `genetic_line_id` de **otra empresa** se aceptaban en el alta
(`201`) y en la edición (`200`); la curva de una línea ajena quedaba aplicada. El
patrón canónico ya existía (`verificar_pertenencia` / `verificar_catalogo_de_empresa`)
y el área lo adoptó en `GA-FE-06-A`; a estos tres campos les faltaba.

Nota de código de estado (**C-07**): el rechazo canónico del repo para la referencia
ajena es `400` con detalle neutro y `rule: "BR-07"` (`app/main.py:88-102`, precedente
certificado en `test_lot_area_ownership.py:105-108`). El «404» del hallazgo describe
la frontera, no el contrato; aquí se fija el contrato real.

```
A: farmA1{farmA2}/houseA1/houseA2 · lineA/curveA(activa) · userA
B: farmB1/houseB1 · lineB/curveB(activa)
```

PREFIJO `R203-`.
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
import app.review.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "R203-"


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def esc203(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import (
        Company, Farm, GeneticLine, GeneticWeightCurve, House,
    )

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        b = Company(name=f"{PREFIJO}B-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add_all([a, b])
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(
            select(BusinessUnit))).scalars()}
        hab_a = CompanyBusinessUnit(company_id=a.id,
                                    business_unit_id=unidades["broiler"].id,
                                    is_enabled=True)
        hab_b = CompanyBusinessUnit(company_id=b.id,
                                    business_unit_id=unidades["broiler"].id,
                                    is_enabled=True)
        s.add_all([hab_a, hab_b])
        await s.flush()

        rol_a = Role(name=f"{PREFIJO}Lotes-{uuid.uuid4().hex[:6]}",
                     company_id=a.id, is_active=True)
        s.add(rol_a)
        await s.flush()
        for accion in (PermissionAction.CREATE, PermissionAction.UPDATE,
                       PermissionAction.READ):
            s.add(Permission(role_id=rol_a.id, module="lots", action=accion,
                             scope_type="company"))
        u_a = User(first_name="R203", last_name="Lotes",
                   email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                   username=f"{PREFIJO}u-{uuid.uuid4().hex[:6]}",
                   hashed_password=hash_password("x"), company_id=a.id,
                   role_id=rol_a.id, is_active=True)
        s.add(u_a)
        await s.flush()
        await conceder_unidad(s, user=u_a, company_business_unit=hab_a)

        farm_a1 = Farm(company_id=a.id, name=f"{PREFIJO}FA1-{uuid.uuid4().hex[:5]}")
        farm_a2 = Farm(company_id=a.id, name=f"{PREFIJO}FA2-{uuid.uuid4().hex[:5]}")
        farm_b1 = Farm(company_id=b.id, name=f"{PREFIJO}FB1-{uuid.uuid4().hex[:5]}")
        s.add_all([farm_a1, farm_a2, farm_b1])
        await s.flush()
        house_a1 = House(farm_id=farm_a1.id, name=f"{PREFIJO}HA1")
        house_a2 = House(farm_id=farm_a2.id, name=f"{PREFIJO}HA2")
        house_b1 = House(farm_id=farm_b1.id, name=f"{PREFIJO}HB1")
        s.add_all([house_a1, house_a2, house_b1])
        await s.flush()

        line_a = GeneticLine(company_id=a.id, name=f"{PREFIJO}LA-{uuid.uuid4().hex[:5]}")
        line_b = GeneticLine(company_id=b.id, name=f"{PREFIJO}LB-{uuid.uuid4().hex[:5]}")
        s.add_all([line_a, line_b])
        await s.flush()
        curve_a = GeneticWeightCurve(genetic_line_id=line_a.id,
                                     version_label=f"{PREFIJO}CA", is_active=True)
        curve_b = GeneticWeightCurve(genetic_line_id=line_b.id,
                                     version_label=f"{PREFIJO}CB", is_active=True)
        s.add_all([curve_a, curve_b])
        await s.flush()
        await s.commit()

        d = {"url": test_database_url, "a": a.id, "b": b.id, "u_a": u_a.id,
             "farm_a1": farm_a1.id, "farm_b1": farm_b1.id,
             "house_a1": house_a1.id, "house_a2": house_a2.id,
             "house_b1": house_b1.id, "line_a": line_a.id, "line_b": line_b.id,
             "curve_a": curve_a.id, "curve_b": curve_b.id}
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            # `audit_logs.lot_id` referencia a `lots`: primero el rastro.
            "DELETE FROM audit_logs WHERE lot_id IN (SELECT id FROM lots WHERE lot_code LIKE :p)",
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM houses WHERE farm_id IN (SELECT id FROM farms WHERE name LIKE :p)",
            "DELETE FROM farms WHERE name LIKE :p",
            "DELETE FROM genetic_weight_curve_points WHERE curve_id IN (SELECT id FROM genetic_weight_curves WHERE version_label LIKE :p)",
            "DELETE FROM genetic_weight_curves WHERE version_label LIKE :p",
            "DELETE FROM genetic_lines WHERE name LIKE :p",
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM company_business_units WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


async def _lote(http_client, esc, **extra):
    cuerpo = {
        "farm_id": esc["farm_a1"], "house_id": esc["house_a1"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "broiler", "sex": "mixed",
    }
    cuerpo.update(extra)
    return await http_client.post("/api/v1/lots", headers=_token(esc["u_a"]),
                                  json=cuerpo)


async def _cuenta_lotes(esc):
    motor = create_async_engine(esc["url"])
    try:
        async with async_sessionmaker(motor)() as s:
            return (await s.execute(text(
                "SELECT count(*) FROM lots WHERE company_id = :a"),
                {"a": esc["a"]})).scalar()
    finally:
        await motor.dispose()


async def test_r203_01_galpon_ajeno_es_rechazo_y_nada_persiste(http_client, esc203):
    """`AC-R203-01`. RED en HEAD: `201` y el lote queda ligado al galpón de B."""
    r = await _lote(http_client, esc203, house_id=esc203["house_b1"])
    assert r.status_code == 400, r.text
    assert r.json().get("detail") == "Galpón no encontrado", r.text
    assert r.json().get("rule") == "BR-07", r.text
    assert await _cuenta_lotes(esc203) == 0, "cero filas creadas"


async def test_r203_02_linea_ajena_se_rechaza_y_nula_es_compartida(http_client, esc203):
    """`AC-R203-02`. RED en HEAD (línea ajena ⇒ 201). La nula es compartida (R-179)."""
    r = await _lote(http_client, esc203, genetic_line_id=esc203["line_b"])
    assert r.status_code == 400, r.text
    assert r.json().get("detail") == "Línea genética no encontrado", r.text
    assert await _cuenta_lotes(esc203) == 0

    r2 = await _lote(http_client, esc203, genetic_line_id=None)
    assert r2.status_code == 201, r2.text


async def test_r203_03_curva_de_linea_ajena_rechazada(http_client, esc203):
    """`AC-R203-03`. RED en HEAD: línea B + curva B ⇒ `201` con curva ajena aplicada."""
    r = await _lote(http_client, esc203, genetic_line_id=esc203["line_b"],
                    weight_curve_id=esc203["curve_b"])
    assert r.status_code in (400, 404), r.text
    assert await _cuenta_lotes(esc203) == 0, "sin curva ajena aplicada"


async def test_r203_04_edicion_por_put_no_cruza(http_client, esc203):
    """`AC-R203-04`. RED en HEAD: `PUT {house_id: B}` ⇒ 200. Propio ⇒ 200 (control)."""
    creado = await _lote(http_client, esc203)
    assert creado.status_code == 201, creado.text
    lote_id = creado.json()["id"]

    ajeno = await http_client.put(f"/api/v1/lots/{lote_id}",
                                  headers=_token(esc203["u_a"]),
                                  json={"house_id": esc203["house_b1"]})
    assert ajeno.status_code == 400, ajeno.text
    assert ajeno.json().get("rule") == "BR-07", ajeno.text

    propio = await http_client.put(f"/api/v1/lots/{lote_id}",
                                   headers=_token(esc203["u_a"]),
                                   json={"house_id": esc203["house_a2"]})
    assert propio.status_code == 200, propio.text


async def test_r203_05_curva_propia_se_aplica(http_client, esc203):
    """Control: el alta con línea propia toma la versión activa de **su** curva."""
    r = await _lote(http_client, esc203, genetic_line_id=esc203["line_a"])
    assert r.status_code == 201, r.text
    assert r.json()["weight_curve_id"] == esc203["curve_a"], r.text


async def test_r203_06_alta_legitima_intacta(http_client, esc203):
    """Control: geometría propia completa ⇒ 201 (regresión del flujo legítimo)."""
    r = await _lote(http_client, esc203, genetic_line_id=esc203["line_a"],
                    weight_curve_id=esc203["curve_a"])
    assert r.status_code == 201, r.text
    assert r.json()["house_id"] == esc203["house_a1"]

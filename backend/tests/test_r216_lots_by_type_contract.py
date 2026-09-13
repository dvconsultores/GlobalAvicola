"""`R-216` · Contrato de `lots_by_type` del panel: claves = **valor** del enum.

`dashboard/service.py:171` construye `{str(row.bird_type): cnt}`; `str()` sobre un
`(str, Enum)` produce `'BirdTypeEnum.BROILER'`. `DashboardPage.tsx` busca
`lotsByType['broiler'|…]` ⇒ las cuatro tarjetas quedan en 0 mientras el subtítulo
(suma) es correcto. La especificación compacta vive en
`specs/R-216/R-216_FINDING_SPEC.md` (AC-R216-01/02/04).

```
A: lotes activos por tipo (grandparent/breeder/hatchery/broiler)
```

PREFIJO `R216-`.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "R216-"
CLAVES_ESPERADAS = {"grandparent", "breeder", "hatchery", "broiler"}


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


@pytest_asyncio.fixture
async def esc216(test_database_url):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import BirdTypeEnum, Company, Lot

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add(a)
        await s.flush()
        # El panel acota por unidades: el actor necesita las cuatro habilitadas y vivas.
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = {}
        for code in ("grandparent", "breeder", "hatchery", "broiler"):
            fila = CompanyBusinessUnit(company_id=a.id,
                                       business_unit_id=unidades[code].id,
                                       is_enabled=True)
            s.add(fila)
            await s.flush()
            hab[code] = fila
        rol = Role(name=f"{PREFIJO}Panel-{uuid.uuid4().hex[:6]}", company_id=a.id,
                   is_active=True)
        s.add(rol)
        await s.flush()
        s.add(Permission(role_id=rol.id, module="dashboard",
                         action=PermissionAction.READ, scope_type="company"))
        u = User(first_name="R216", last_name="Panel",
                 email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                 username=f"{PREFIJO}u-{uuid.uuid4().hex[:6]}",
                 hashed_password=hash_password("x"), company_id=a.id,
                 role_id=rol.id, is_active=True)
        s.add(u)
        await s.flush()
        for fila in hab.values():
            await conceder_unidad(s, user=u, company_business_unit=fila)
        # Un lote activo por cada tipo + un broiler extra para verificar el recuento.
        reparto = {"grandparent": 1, "breeder": 2, "hatchery": 1, "broiler": 3}
        for tipo, cuantos in reparto.items():
            for _ in range(cuantos):
                s.add(Lot(company_id=a.id,
                          lot_code=f"{PREFIJO}{tipo[:4]}-{uuid.uuid4().hex[:8]}",
                          bird_type=BirdTypeEnum(tipo), status="active"))
        await s.flush()
        await s.commit()
        d = {"url": test_database_url, "a": a.id, "u": u.id, "reparto": reparto}
    yield d
    async with motor.begin() as c:
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM lots WHERE lot_code LIKE :p",
            "DELETE FROM user_business_units WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE user_id IN (SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM company_business_units WHERE company_id IN (SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN (SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await motor.dispose()


async def test_r216_01_las_claves_son_los_valores_del_enum(http_client, esc216):
    """`AC-R216-01/04`. RED en HEAD: las claves son `BirdTypeEnum.*`."""
    r = await http_client.get("/api/v1/dashboard/admin", headers=_token(esc216["u"]))
    assert r.status_code == 200, r.text
    lots_by_type = r.json().get("lots_by_type")
    assert isinstance(lots_by_type, dict), r.text
    assert set(lots_by_type) == CLAVES_ESPERADAS, lots_by_type
    for tipo, cuantos in esc216["reparto"].items():
        assert lots_by_type[tipo] == cuantos, (tipo, lots_by_type)


async def test_r216_02_control_la_suma_es_el_total(http_client, esc216):
    """`AC-R216-02` (control, verde antes y después): la suma no cambia."""
    r = await http_client.get("/api/v1/dashboard/admin", headers=_token(esc216["u"]))
    assert r.status_code == 200, r.text
    lots_by_type = r.json().get("lots_by_type") or {}
    assert sum(lots_by_type.values()) == sum(esc216["reparto"].values())

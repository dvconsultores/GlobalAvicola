"""`GA-FE-02-D` · `OD-16` — el borde de LECTURA productiva de la autoridad global.

La regla ratificada por el propietario:

```
CompanyBusinessUnit OFF es absoluta para las operaciones productivas
para TODOS los actores — incluida la autoridad global.
La autoridad global PUEDE saltarse la concesión de usuario (R-139 §6);
NUNCA puede saltarse la habilitación de la empresa.
CONTROL PLANE ≠ PRODUCTIVE DATA READ.
```

Este fichero sucede a la excepción de la fase 3 («certificada en `GA-REM-002`») en LECTURAS
productivas: `unidades_de_alcance_productivo` espeja la semántica que la escritura ya aplica
(`exigir_unidad_operativa`, `R-163`).

Los dos bloques:

    · ruteo del resolutor             — puro, sin base de datos (se ejecuta siempre)
    · frontera de `GET /lots`         — contra el API; requiere la base de pruebas (CI)
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.lots.models  # noqa: F401
from app.auth.security import create_access_token

pytestmark = pytest.mark.asyncio

PREFIJO = "OD16-"


def _token(user_id: int, company_id: int | None = None) -> dict:
    datos: dict = {"sub": str(user_id)}
    if company_id is not None:
        datos["company_id"] = company_id
    return {"Authorization": f"Bearer {create_access_token(data=datos)}"}


# ══════════════════════════════════════════════════════════════════════════════
#  Ruteo del resolutor — puro (sin base de datos)
# ══════════════════════════════════════════════════════════════════════════════

async def test_alcance_productivo_rutea_por_actor(monkeypatch):
    """`GA-FE-02-D`: la autoridad global va por **habilitadas**; el resto, por efectivas."""
    from app.business_units import service as unidades

    llamadas = {"habilitadas": 0, "efectivas": 0}

    async def _habilitadas(db, company_id):
        llamadas["habilitadas"] += 1
        return ["breeder"]

    async def _efectivas(db, *, user_id, company_id):
        llamadas["efectivas"] += 1
        return ["hatchery"]

    monkeypatch.setattr(unidades, "unidades_habilitadas", _habilitadas)
    monkeypatch.setattr(unidades, "unidades_efectivas_por_id", _efectivas)

    auto = await unidades.unidades_de_alcance_productivo(
        object(), current_user={"is_super_admin": True, "id": 1}, company_id=7)
    assert auto == ["breeder"], "la autoridad global debe leer por HABILITADAS"

    normal = await unidades.unidades_de_alcance_productivo(
        object(), current_user={"is_super_admin": False, "id": 2}, company_id=7)
    assert normal == ["hatchery"], "el actor de empresa conserva sus EFECTIVAS"

    assert llamadas == {"habilitadas": 1, "efectivas": 1}


# ══════════════════════════════════════════════════════════════════════════════
#  Frontera productiva contra el API — `GET /lots` (la ruta D-1)
# ══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def escenario_od16(test_database_url):
    """Empresa A con `breeder` y `hatchery` habilitadas; `broiler` sin fila.

    Un lote por cadena + la autoridad global situada en A con su comodín.
    La autoridad global **no** tiene ninguna concesión de usuario (R-139 §6).
    """
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.masters.models import BirdTypeEnum, Company, Lot

    motor = create_async_engine(test_database_url)
    async with async_sessionmaker(motor, expire_on_commit=False)() as s:
        a = Company(name=f"{PREFIJO}A-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add(a)
        await s.flush()

        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab: dict[str, CompanyBusinessUnit] = {}
        for code in ("breeder", "hatchery"):  # broiler: sin fila (nunca configurada)
            fila = CompanyBusinessUnit(company_id=a.id,
                                       business_unit_id=unidades[code].id,
                                       is_enabled=True)
            s.add(fila)
            await s.flush()
            hab[code] = fila

        def _lote(code, tipo):
            return Lot(company_id=a.id, lot_code=f"{PREFIJO}{code}-{uuid.uuid4().hex[:6]}",
                       bird_type=tipo, status="active")

        lote_r = _lote("R", BirdTypeEnum.BREEDER)
        lote_h = _lote("H", BirdTypeEnum.HATCHERY)
        lote_b = _lote("B", BirdTypeEnum.BROILER)
        s.add_all([lote_r, lote_h, lote_b])

        rol = Role(name=f"{PREFIJO}Global-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add(rol)
        await s.flush()
        for accion in PermissionAction:
            s.add(Permission(role_id=rol.id, module="*", action=accion, scope_type="all"))

        superadmin = User(first_name="SUPER", last_name="Od16",
                          email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@globalavicola.com",
                          username=f"{PREFIJO}{uuid.uuid4().hex[:6]}",
                          hashed_password=hash_password("x1234567"),
                          company_id=None, role_id=rol.id, is_active=True)
        s.add(superadmin)
        await s.flush()
        await s.commit()
        return {
            "empresa": a.id, "super": superadmin.id, "hab": hab,
            "codigos": {lote_r.lot_code, lote_h.lot_code, lote_b.lot_code},
            "codigos_hab": {lote_r.lot_code, lote_h.lot_code},
        }


async def _codigos(http_client, escenario):
    r = await http_client.get("/api/v1/lots?limit=100",
                              headers=_token(escenario["super"], escenario["empresa"]))
    assert r.status_code == 200, r.text
    return {fila["lot_code"] for fila in r.json()}


async def test_od16_autoridad_global_lee_solo_las_habilitadas(http_client, escenario_od16):
    """Con la puerta de empresa en pie, el global ve lo habilitado — sin concesiones.

    `broiler` no tiene fila de empresa: su lote **no** puede aparecer, ni siquiera para la
    autoridad global. Antes de `GA-FE-02-D` aparecía (el atajo anulaba todo el predicado).
    """
    vistos = await _codigos(http_client, escenario_od16)
    assert vistos == escenario_od16["codigos_hab"], vistos


async def test_od16_autoridad_global_con_todo_apagado_no_lee_nada(http_client, escenario_od16):
    """`OD-16`: apagada la empresa, cero filas productivas — también para el global.

    Y el plano de control sigue disponible (las 4 unidades del catálogo se listan igual).
    """
    # Apagar por flujo oficial: la propia autoridad global administra el plano de control.
    for code in ("breeder", "hatchery"):
        r = await http_client.patch(
            f"/api/v1/business-units/{code}/disable",
            headers=_token(escenario_od16["super"], escenario_od16["empresa"]))
        assert r.status_code == 200, r.text

    vistos = await _codigos(http_client, escenario_od16)
    assert vistos == set(), f"unidades apagadas ⇒ cero filas productivas: {vistos}"

    r = await http_client.get("/api/v1/business-units",
                              headers=_token(escenario_od16["super"], escenario_od16["empresa"]))
    assert r.status_code == 200, r.text
    assert len(r.json()) == 4, "el plano de control no se apaga con las unidades"

"""Seed **mínimo** de baseline. Entregable de `GA-REM-025`.

Qué siembra, y nada más:

    roles + permisos          no existe API que cree asociaciones rol→permiso
    usuario administrador     sin él nadie puede llamar a ninguna API
    fases productivas         catálogo invariante del dominio, sin `company_id`
    2 empresas de certificación   mínimo exigido por R-42 / R-48 / R-54 / R-59

Qué **no** siembra, deliberadamente (encargo §53 y §60):

    granjas, galpones, lotes, eventos, correcciones, aprobaciones,
    documentos SAP, ni ningún otro maestro de cliente

Todo eso lo crea un usuario por la API —los 19 maestros tienen CRUD completo— o un
fixture de escenario. Inventarlo aquí sería fabricar los datos del futuro cliente.

La matriz de permisos **no se copia**: se importa de la migración `l2m3n4o5p6q7`, que es
su fuente única. Mantener dos copias fue precisamente la causa de `R-44`.
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import secrets

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Todos los módulos de modelos deben importarse antes de usar el ORM: SQLAlchemy
# configura los mappers de golpe y las relaciones cruzadas fallan si falta alguno.
import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.models import Permission, PermissionAction, Role, User
from app.auth.security import hash_password
from app.masters.models import Company, ProductivePhase

# ── Fuente única de la matriz RBAC ────────────────────────────────────────────

def _matriz_de_la_migracion() -> dict[str, list[tuple[str, str]]]:
    """Importa `PERMISOS_POR_ROL` de la migración de reconciliación.

    Se carga por ruta porque el paquete `alembic/versions` no es importable como módulo.
    Si la migración cambia, el seed cambia con ella: es imposible que diverjan.
    """
    ruta = next(
        pathlib.Path(__file__).resolve().parents[1].glob("alembic/versions/l2m3n4o5p6q7*.py")
    )
    spec = importlib.util.spec_from_file_location("_rbac_matrix", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.PERMISOS_POR_ROL


#: Acciones comodín del Super Administrador. No están en la migración porque ésta solo
#: reconcilia roles operativos; aquí sí hacen falta para que exista un administrador.
ACCIONES_COMODIN = [a for a in PermissionAction]

DESCRIPCIONES = {
    "Super Administrador": "Control total del sistema",
    "Operador de Granja": "Registro de operaciones en campo",
    "Supervisor Avícola": "Supervisión operativa de granjas",
    "Aprobador": "Aprobación y rechazo de operaciones",
    "Analista SAP": "Envío y seguimiento de documentos SAP",
    "Auditor": "Consulta de auditoría, solo lectura",
}

#: Empresas de certificación. Los nombres declaran su naturaleza: nadie puede confundirlas
#: con una operación real (encargo §27).
EMPRESAS_CERTIFICACION = [
    {"name": "TEST COMPANY A", "tax_id": "TEST-A-000000001", "country": "Test", "currency": "USD"},
    {"name": "TEST COMPANY B", "tax_id": "TEST-B-000000002", "country": "Test", "currency": "USD"},
]

#: Fases del ciclo productivo avícola. Invariantes del dominio, no del cliente.
FASES = [
    ("Cría", "CRIA", 1, 140, True, False),
    ("Producción", "PROD", 2, 280, False, False),
    ("Incubación", "INCUB", 3, 21, False, False),
    ("Engorde", "ENGORDE", 4, 42, False, True),
]

#: Cuenta administradora del baseline.
ADMIN = {
    "username": "admin",
    "first_name": "Administrador",
    "last_name": "del Sistema",
    # Dominio real y no reservado: `EmailStr` rechaza .test/.example/.local y el
    # usuario resultaría ilegible por la API.
    "email": "admin@globalavicola.com",
    "role_name": "Super Administrador",
    "view_type": "web",
}


def _password_admin() -> str:
    """Contraseña del administrador, del entorno. Nunca literal en el repositorio.

    `GA-REM-004`. Si no se declara, se genera una aleatoria y se imprime **una sola vez**:
    un baseline sin administrador accesible sería un baseline inservible, y una contraseña
    fija en el código sería el defecto que `GA-REM-004` vino a cerrar.
    """
    valor = os.environ.get("GA_BASELINE_ADMIN_PASSWORD")
    if valor:
        return valor
    generada = secrets.token_urlsafe(18)
    print(
        "  ⚠️  GA_BASELINE_ADMIN_PASSWORD no declarada. Se generó una contraseña aleatoria.\n"
        f"      Anótela ahora, no vuelve a mostrarse:  {generada}"
    )
    return generada


# ── Siembra ───────────────────────────────────────────────────────────────────

async def sembrar_roles(session: AsyncSession) -> dict[str, Role]:
    matriz = _matriz_de_la_migracion()
    permisos_por_rol: dict[str, list[tuple[str, PermissionAction]]] = {
        "Super Administrador": [("*", accion) for accion in ACCIONES_COMODIN],
    }
    for nombre, pares in matriz.items():
        permisos_por_rol[nombre] = [(modulo, PermissionAction(accion)) for modulo, accion in pares]

    roles: dict[str, Role] = {}
    for nombre, permisos in permisos_por_rol.items():
        existente = (
            await session.execute(select(Role).where(Role.name == nombre))
        ).scalar_one_or_none()
        if existente is None:
            existente = Role(name=nombre, description=DESCRIPCIONES.get(nombre))
            session.add(existente)
            await session.flush()
            print(f"  ✅ Rol: {nombre}")
        roles[nombre] = existente

        ya = {
            (p.module, p.action)
            for p in (
                await session.execute(select(Permission).where(Permission.role_id == existente.id))
            ).scalars()
        }
        nuevos = 0
        for modulo, accion in permisos:
            if (modulo, accion) not in ya:
                session.add(
                    Permission(role_id=existente.id, module=modulo, action=accion, scope_type="all")
                )
                nuevos += 1
        if nuevos:
            print(f"     └─ {nuevos} permisos añadidos")
    await session.flush()
    return roles


async def sembrar_fases(session: AsyncSession) -> int:
    creadas = 0
    for nombre, code, orden, dias, inicial, final in FASES:
        existe = (
            await session.execute(select(ProductivePhase).where(ProductivePhase.code == code))
        ).scalar_one_or_none()
        if existe is None:
            session.add(
                ProductivePhase(
                    name=nombre, code=code, order=orden,
                    duration_days=dias, is_initial=inicial, is_final=final,
                )
            )
            creadas += 1
    await session.flush()
    if creadas:
        print(f"  ✅ {creadas} fases productivas")
    return creadas


async def sembrar_empresas(session: AsyncSession) -> dict[str, int]:
    resultado: dict[str, int] = {}
    for datos in EMPRESAS_CERTIFICACION:
        empresa = (
            await session.execute(select(Company).where(Company.name == datos["name"]))
        ).scalar_one_or_none()
        if empresa is None:
            empresa = Company(**datos)
            session.add(empresa)
            await session.flush()
            print(f"  ✅ Empresa de certificación: {empresa.name} (id={empresa.id})")
        resultado[empresa.name] = empresa.id
    return resultado


async def sembrar_admin(session: AsyncSession, roles: dict[str, Role]) -> None:
    existe = (
        await session.execute(select(User).where(User.username == ADMIN["username"]))
    ).scalar_one_or_none()
    if existe is not None:
        print(f"  ⏭️  Usuario '{ADMIN['username']}' ya existe")
        return
    session.add(
        User(
            first_name=ADMIN["first_name"],
            last_name=ADMIN["last_name"],
            email=ADMIN["email"],
            username=ADMIN["username"],
            hashed_password=hash_password(_password_admin()),
            role_id=roles[ADMIN["role_name"]].id,
            company_id=None,  # Super Administrador: sin tenant fijo
            view_type=ADMIN["view_type"],
        )
    )
    print(f"  ✅ Usuario administrador: {ADMIN['username']}")


async def sembrar_baseline(session: AsyncSession) -> dict[str, int]:
    """Siembra el baseline completo. Idempotente: repetirla no duplica nada."""
    print("── Baseline mínimo (GA-REM-025) ──")
    roles = await sembrar_roles(session)
    await sembrar_fases(session)
    empresas = await sembrar_empresas(session)
    await sembrar_admin(session, roles)
    await session.commit()

    total_permisos = (await session.execute(select(func.count(Permission.id)))).scalar_one()
    operativos = (
        await session.execute(
            select(func.count(Permission.id))
            .join(Role, Role.id == Permission.role_id)
            .where(Role.name != "Super Administrador")
        )
    ).scalar_one()
    print(
        f"── Baseline listo: {len(roles)} roles · {total_permisos} permisos "
        f"({operativos} operativos) · {len(empresas)} empresas ──"
    )
    return {"roles": len(roles), "permisos": total_permisos, "permisos_operativos": operativos,
            "empresas": len(empresas)}

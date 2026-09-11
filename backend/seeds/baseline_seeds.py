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
su fuente única, y se compone con los deltas de las migraciones de reconciliación posteriores
(`v2w3x4y5z6a7`, `OD-19` Aclaración A · `GA-REM-041-B`). Mantener dos copias fue precisamente
la causa de `R-44`: sigue habiendo una copia de cada hecho.
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
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.integrations.sap.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.auth.models import Permission, PermissionAction, Role, User
from app.auth.security import hash_password
from app.masters.models import Company, GeneticLine, ProductivePhase

# ── Fuente única de la matriz RBAC ────────────────────────────────────────────

#: Migraciones de reconciliación de la matriz RBAC, en orden: la base (`R-44`) y los deltas
#: que decisiones posteriores añadieron sobre ella. Cada una es la fuente única de su hecho.
MIGRACIONES_DE_LA_MATRIZ = (
    ("l2m3n4o5p6q7", "PERMISOS_POR_ROL"),       # base: `docs/12 §3` (46 asociaciones)
    ("v2w3x4y5z6a7", "PERMISOS_ADICIONALES"),   # `OD-19` Aclaración A (+2 al Supervisor Avícola)
)


def _atributo_de_la_migracion(prefijo: str, atributo: str) -> dict[str, list[tuple[str, str]]]:
    """Carga por ruta —el paquete `alembic/versions` no es importable como módulo—."""
    ruta = next(
        pathlib.Path(__file__).resolve().parents[1].glob(f"alembic/versions/{prefijo}*.py")
    )
    spec = importlib.util.spec_from_file_location(f"_rbac_{prefijo}", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return getattr(modulo, atributo)


def _matriz_de_la_migracion() -> dict[str, list[tuple[str, str]]]:
    """Matriz RBAC compuesta: la base de `l2m3n4o5p6q7` más los deltas posteriores.

    Si una migración cambia, el seed cambia con ella: es imposible que diverjan. Los deltas
    solo se aplican a roles que ya están en la base: el baseline **no inventa roles**
    («Contralor Avícola» es figura de `integration_seeds`, `OD-19` Aclaración A).
    """
    base_prefijo, base_atributo = MIGRACIONES_DE_LA_MATRIZ[0]
    matriz = {rol: list(pares) for rol, pares in _atributo_de_la_migracion(base_prefijo, base_atributo).items()}
    for prefijo, atributo in MIGRACIONES_DE_LA_MATRIZ[1:]:
        for rol, pares in _atributo_de_la_migracion(prefijo, atributo).items():
            if rol not in matriz:
                continue
            matriz[rol].extend(par for par in pares if par not in matriz[rol])
    return matriz


#: Acciones comodín del Super Administrador. No están en la migración porque ésta solo
#: reconcilia roles operativos; aquí sí hacen falta para que exista un administrador.
ACCIONES_COMODIN = [a for a in PermissionAction]

#: `OD-15 §6` · `R-113`. La figura que administra el acceso por unidad de negocio.
#:
#: Vive aquí y no en la migración de reconciliación por la misma razón que `ACCIONES_COMODIN`:
#: aquella solo reconcilia **roles operativos**, y éste es plano de control. Añadirlo allí
#: exigiría una migración nueva para sembrar un rol, que no es lo que las migraciones son.
#:
#: **Exactamente cuatro permisos, y ninguno más.** No lleva `users:*` —el conjunto que mantuvo
#: cuatro `P0` latentes— ni comodín, ni ninguna cadena productiva: administrar el acceso no es
#: acceder (`OD-09.b`), y repartirlo no es recibirlo (`OD-15.a`).
PERMISOS_ADMINISTRADOR_DE_ACCESOS = [
    ("business_units", PermissionAction.READ),
    ("business_units", PermissionAction.UPDATE),
    ("business_units", PermissionAction.CREATE),
    ("business_units", PermissionAction.DELETE),
]

ROL_ADMINISTRADOR_DE_ACCESOS = "Administrador de Accesos"

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

#: Las tres líneas genéticas iniciales de `OD-06`. Se siembran **solo los nombres**: la
#: curva estándar de cada una la carga el administrador desde la tabla del proveedor, y
#: inventarle valores aquí sería fabricar la referencia contra la que se juzga un lote.
#: La lista no es un enum — `AC01` exige que se puedan añadir otras por la API.
LINEAS_GENETICAS = [
    ("Cobb 500", "COBB500", "Cobb-Vantress"),
    ("Ross 308", "ROSS308", "Aviagen"),
    ("Hubbard", "HUBBARD", "Hubbard"),
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
        ROL_ADMINISTRADOR_DE_ACCESOS: list(PERMISOS_ADMINISTRADOR_DE_ACCESOS),
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


async def sembrar_lineas_geneticas(session: AsyncSession, empresas: dict[str, int]) -> int:
    """Siembra las tres líneas de `OD-06` en cada empresa. Nombres, nunca curvas.

    Por empresa y no globales porque el filtro de tenencia de maestros compara
    `company_id == user_company_id`: una línea con `company_id = NULL` sería invisible
    para todo usuario con empresa, que son todos menos el Super Administrador.
    """
    creadas = 0
    for company_id in empresas.values():
        for nombre, code, proveedor in LINEAS_GENETICAS:
            existe = (
                await session.execute(
                    select(GeneticLine).where(
                        GeneticLine.company_id == company_id, GeneticLine.name == nombre
                    )
                )
            ).scalar_one_or_none()
            if existe is None:
                session.add(GeneticLine(company_id=company_id, name=nombre,
                                        code=code, supplier=proveedor))
                creadas += 1
    await session.flush()
    if creadas:
        print(f"  ✅ {creadas} líneas genéticas (nombres; sin curvas)")
    return creadas


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


#: Las cuatro cadenas productivas del producto (`GA-REM-040 §2`). Es catálogo de plataforma:
#: ninguna empresa las crea ni las renombra. El nombre visible es una **clave de traducción**,
#: no una traducción — el producto habla dos lenguas y la base no debe elegir una.
#:
#: `bird_type` registra la correspondencia con el enum de dominio. La autoridad de acceso son
#: las tres tablas, nunca el enum.
#:
#: **Fuente única: la migración `y5z6a7b8c9d0`** (`GA-FE-02-C §2`). El catálogo dejó de ser
#: solo-semilla cuando pasó a ser baseline determinista de despliegue: la migración lo crea en
#: instalaciones existentes y este seed **importa el mismo hecho** — imposible que diverjan,
#: igual que con la matriz RBAC. `p6q7r8s9t0u1` advirtió «una migración que inserta catálogo
#: obliga a mantener el dato en dos sitios»; este import es exactamente lo que evita ese
#: segundo sitio.
def _unidades_de_negocio_de_la_migracion() -> tuple[tuple[str, str, str], ...]:
    """Carga por ruta —el paquete `alembic/versions` no es importable como módulo—."""
    return _atributo_de_la_migracion("y5z6a7b8c9d0", "UNIDADES_CANONICAS")


UNIDADES_DE_NEGOCIO = _unidades_de_negocio_de_la_migracion()


async def sembrar_unidades_de_negocio(session: AsyncSession) -> int:
    """Siembra el catálogo de unidades. Idempotente: repetirla no duplica nada.

    **Solo el catálogo.** Ni habilitaciones de empresa ni concesiones de usuario: `GA-REM-040`
    exige que ambas sean explícitas. Encender las cuatro para toda empresa «para que no
    moleste» dejaría la capacidad apagada de hecho el día que se estrene, y conceder todo a
    los usuarios existentes haría lo mismo desde el otro lado.
    """
    from app.business_units.models import BusinessUnit

    creadas = 0
    for code, name_key, bird_type in UNIDADES_DE_NEGOCIO:
        existe = (
            await session.execute(select(BusinessUnit).where(BusinessUnit.code == code))
        ).scalar_one_or_none()
        if existe is None:
            session.add(BusinessUnit(code=code, name_key=name_key, bird_type=bird_type))
            creadas += 1
    await session.flush()
    if creadas:
        print(f"  ✅ {creadas} unidades de negocio (catálogo de producto)")
    return creadas


async def sembrar_baseline(session: AsyncSession) -> dict[str, int]:
    """Siembra el baseline completo. Idempotente: repetirla no duplica nada."""
    print("── Baseline mínimo (GA-REM-025) ──")
    roles = await sembrar_roles(session)
    await sembrar_fases(session)
    await sembrar_unidades_de_negocio(session)
    empresas = await sembrar_empresas(session)
    await sembrar_lineas_geneticas(session, empresas)
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

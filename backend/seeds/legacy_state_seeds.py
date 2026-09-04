"""Estado representativo de una instalación EXISTENTE anterior a la Wave 2.

Reconstruye —sin tocar producción— lo que una instalación desplegada antes de la Wave 2
tendría en su base de datos:

* la **matriz de permisos histórica**, tal como la sembraba `dev_seeds.py` en el commit
  `bfccdfb`: 24 asociaciones rol↔permiso más los 9 comodines del Super Admin;
* usuarios reales asignados a esos roles;
* datos operativos representativos;
* y, sobre todo, el **estado de enums anterior**: `eventtype` sin
  `EGG_RECEPTION_CLASSIFICATION` y `birdtypeenum` con `'hatchery'` en minúsculas.

Ese último punto es el que hace útil este módulo. Una base creada desde cero con las
migraciones actuales **nunca** reproduce el estado que hay que probar: el de una base que
lleva meses en producción con la deriva que la Wave 2 descubrió.

Se aplica sobre `global_avicola_upgrade_test`, después de migrar hasta el *head* anterior
a la Wave 2 (`i9j0k1l2m3n4`) y antes de aplicar las migraciones nuevas.
"""

from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import select, text

# ── Matriz de permisos histórica ──────────────────────────────────────────────
# Copiada literalmente de `git show bfccdfb:backend/seeds/dev_seeds.py`. No se «mejora»:
# el objeto de este módulo es reproducir lo que hay, no lo que debería haber.
PERMISOS_HISTORICOS: dict[str, list[tuple[str, str]]] = {
    "Super Administrador": [
        ("*", a) for a in
        ("READ", "CREATE", "UPDATE", "DELETE", "REVIEW", "CORRECT", "APPROVE", "REJECT", "SEND_SAP")
    ],
    "Supervisor Avícola": [
        ("operations", "READ"), ("lots", "READ"), ("review", "REVIEW"),
        ("review", "CORRECT"), ("approvals", "READ"), ("reports", "READ"),
    ],
    "Operador de Granja": [
        ("operations", "CREATE"), ("operations", "READ"), ("lots", "READ"),
    ],
    "Aprobador": [
        ("operations", "READ"), ("review", "READ"), ("approvals", "APPROVE"),
        ("approvals", "REJECT"), ("approvals", "REVIEW"), ("approvals", "CORRECT"),
        ("reports", "READ"),
    ],
    "Analista SAP": [
        ("sap", "READ"), ("sap", "CREATE"), ("sap", "SEND_SAP"),
        ("operations", "READ"), ("reports", "READ"),
    ],
    "Auditor": [
        ("audit", "READ"), ("reports", "READ"), ("operations", "READ"),
    ],
}

USUARIOS_HISTORICOS = [
    ("legacy_admin", "Super Administrador", None),
    ("legacy_operador", "Operador de Granja", "empresa"),
    ("legacy_supervisor", "Supervisor Avícola", "empresa"),
    ("legacy_aprobador", "Aprobador", "empresa"),
    ("legacy_sap", "Analista SAP", "empresa"),
    ("legacy_auditor", "Auditor", "empresa"),
]

PASSWORD_ENV = "GA_UPGRADE_TEST_PASSWORD"
EMPRESA = "Empresa Heredada"
GRANJA_CODIGO = "LEGACY-FARM-01"
LOTE_CODIGO = "LEGACY-LOT-01"


def _password() -> str:
    valor = os.environ.get(PASSWORD_ENV)
    if not valor:
        raise SystemExit(
            f"{PASSWORD_ENV} no está definida. Use backend/scripts/upgrade_test.sh, "
            "que genera la credencial por ejecución."
        )
    return valor


async def sembrar_estado_heredado() -> dict:
    """Deja la base en el estado de una instalación anterior a la Wave 2."""
    # Todos los módulos de modelos: SQLAlchemy resuelve las relaciones por nombre y
    # necesita el registro completo antes de mapear.
    import app.audit.models  # noqa: F401
    import app.corrections.models  # noqa: F401
    import app.integrations.sap.models  # noqa: F401
    import app.lots.models  # noqa: F401
    import app.operations.models  # noqa: F401
    import app.review.models  # noqa: F401
    from app.auth.models import Role, User
    from app.auth.security import hash_password
    from app.database import async_session
    from app.masters.models import BirdTypeEnum, Company, Farm, House, Lot, LotStatus

    creado: dict[str, int] = {}
    async with async_session() as sesion:
        empresa = (await sesion.execute(
            select(Company).where(Company.name == EMPRESA))).scalar_one_or_none()
        if empresa is None:
            empresa = Company(name=EMPRESA, is_active=True)
            sesion.add(empresa)
            await sesion.flush()
        creado["company_id"] = empresa.id

        roles: dict[str, Role] = {}
        for nombre, permisos in PERMISOS_HISTORICOS.items():
            rol = (await sesion.execute(
                select(Role).where(Role.name == nombre))).scalar_one_or_none()
            if rol is None:
                rol = Role(name=nombre, description=f"Rol heredado: {nombre}", is_active=True)
                sesion.add(rol)
                await sesion.flush()
                for modulo, accion in permisos:
                    # SQL directo: los enums de Python pueden haber cambiado desde
                    # entonces, y aquí interesa escribir exactamente lo que había.
                    await sesion.execute(
                        text(
                            "INSERT INTO permissions (role_id, module, action, scope_type) "
                            "VALUES (:rid, :m, CAST(:a AS permissionaction), 'all')"
                        ),
                        {"rid": rol.id, "m": modulo, "a": accion},
                    )
            roles[nombre] = rol
        await sesion.flush()

        clave = hash_password(_password())
        for usuario, nombre_rol, ambito in USUARIOS_HISTORICOS:
            existente = (await sesion.execute(
                select(User).where(User.username == usuario))).scalar_one_or_none()
            if existente is None:
                sesion.add(User(
                    company_id=empresa.id if ambito == "empresa" else None,
                    first_name="Legacy", last_name=usuario,
                    email=f"{usuario}@example.com", username=usuario,
                    hashed_password=clave, role_id=roles[nombre_rol].id,
                    view_type="web", is_active=True,
                ))
        await sesion.flush()

        granja = (await sesion.execute(
            select(Farm).where(Farm.code == GRANJA_CODIGO))).scalar_one_or_none()
        if granja is None:
            granja = Farm(company_id=empresa.id, name="Granja heredada",
                          code=GRANJA_CODIGO, location="Estado previo", is_active=True)
            sesion.add(granja)
            await sesion.flush()
        creado["farm_id"] = granja.id

        galpon = (await sesion.execute(
            select(House).where(House.name == "Galpon heredado"))).scalar_one_or_none()
        if galpon is None:
            galpon = House(farm_id=granja.id, name="Galpon heredado",
                           capacity=10_000, is_active=True)
            sesion.add(galpon)
            await sesion.flush()
        creado["house_id"] = galpon.id

        lote = (await sesion.execute(
            select(Lot).where(Lot.lot_code == LOTE_CODIGO))).scalar_one_or_none()
        if lote is None:
            from tests.time_reference import lot_start_date

            lote = Lot(company_id=empresa.id, lot_code=LOTE_CODIGO, farm_id=granja.id,
                       house_id=galpon.id, bird_type=BirdTypeEnum.BROILER, sex="mixed",
                       status=LotStatus.ACTIVE, activation_type="normal",
                       start_date=lot_start_date())
            sesion.add(lote)
            await sesion.flush()
        creado["lot_id"] = lote.id

        await sesion.commit()

    return creado


async def revertir_enums_al_estado_previo() -> None:
    """Devuelve los tipos enumerados al estado que tenía una instalación anterior.

    `alembic upgrade i9j0k1l2m3n4` deja `birdtypeenum` con `'hatchery'` en minúsculas
    —así lo escribió la migración `a1b2c3d4e5f6`— y `eventtype` sin
    `EGG_RECEPTION_CLASSIFICATION`, porque ninguna migración lo añadía. Es decir: el estado
    previo se obtiene solo, sin trucos.

    Esta función se limita a **comprobarlo**, porque asumirlo sería exactamente el error
    que la Wave 2.5 investiga.
    """
    from app.database import engine

    async with engine.connect() as conexion:
        etiquetas = {
            (fila[0], fila[1])
            for fila in (await conexion.execute(text(
                "SELECT t.typname, e.enumlabel FROM pg_type t "
                "JOIN pg_enum e ON e.enumtypid = t.oid "
                "WHERE t.typname IN ('eventtype','birdtypeenum')"
            ))).all()
        }

    assert ("eventtype", "EGG_RECEPTION_CLASSIFICATION") not in etiquetas, (
        "El estado previo NO debería contener EGG_RECEPTION_CLASSIFICATION: "
        "la reconstrucción no es representativa")
    assert ("birdtypeenum", "hatchery") in etiquetas, (
        "El estado previo debería contener 'hatchery' en minúsculas")
    assert ("birdtypeenum", "HATCHERY") not in etiquetas, (
        "El estado previo NO debería contener 'HATCHERY'")
    print("[legacy] estado de enums previo verificado: "
          "eventtype sin el 25.º valor · birdtypeenum con 'hatchery' minúscula")


def main() -> None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tests.environment_guard import require_safe_test_environment

    decision = require_safe_test_environment()
    os.environ["DATABASE_URL"] = decision.database_url or ""
    print(f"[legacy_state_seeds] {decision.reason}")

    async def _todo() -> dict:
        # Un solo `asyncio.run`: el motor del módulo queda ligado al bucle que lo abre,
        # y abrir dos bucles distintos produce el clásico «Future attached to a
        # different loop».
        await revertir_enums_al_estado_previo()
        return await sembrar_estado_heredado()

    creado = asyncio.run(_todo())
    print(f"[legacy_state_seeds] estado heredado sembrado: {creado}")


if __name__ == "__main__":
    main()

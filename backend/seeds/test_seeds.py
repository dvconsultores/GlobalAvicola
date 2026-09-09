"""
Seeds deterministas para el entorno de pruebas aislado.

GA-REM-014 — Entorno de test aislado.
GA-REM-004 — Sin contraseñas literales en el código versionado.

Diferencias con `dev_seeds.py` e `integration_seeds.py`:

  * Las contraseñas se leen del entorno; **nunca** hay literales aquí.
  * El conjunto de datos es mínimo y determinista: lo justo para que la suite
    sea reproducible, sin datos de demostración.
  * Solo se ejecuta contra la base validada por `tests/environment_guard.py`.
"""
from __future__ import annotations

import asyncio
import os
import sys
from tests.time_reference import lot_start_date

# ── Identidades de prueba ─────────────────────────────────────────────────────
TEST_COMPANY_2_NAME = "TEST Compania 2"
TEST_OTHER_COMPANY_USERNAME = "test_otra_empresa"
TEST_ADMIN_USERNAME = "test_admin"
TEST_ADMIN_PASSWORD_ENV = "GA_TEST_ADMIN_PASSWORD"

TEST_OPERATOR_USERNAME = "test_operator"
TEST_OPERATOR_PASSWORD_ENV = "GA_TEST_OPERATOR_PASSWORD"

TEST_APPROVER_USERNAME = "test_approver"
TEST_APPROVER_PASSWORD_ENV = "GA_TEST_APPROVER_PASSWORD"

#: Identificadores estables que las fixtures pueden referenciar por código,
#: nunca por número mágico.
TEST_COMPANY_NAME = "TEST Compañía Avícola"
TEST_FARM_DEST_CODE = "TEST-FARM-DEST"
TEST_FARM_CODE = "TEST-GRANJA-01"
TEST_HOUSE_2_NAME = "TEST Galpon 02"
TEST_HOUSE_NAME = "TEST-GALPON-01"
TEST_LOT_CODE = "TEST-LOTE-BROILER-01"
TEST_LOT_CODE_2 = "TEST-LOTE-BROILER-02"

#: La suite heredada (`test_operations.py`, `test_full_workflow_audit.py`)
#: referencia identificadores fijos: farm_id=1, house_id=1, lot_id=2.
#: Se siembran en ese orden para que existan. Migrar esos tests a los
#: identificadores expuestos por estas constantes queda en el backlog.
LEGACY_LOT_ID = 2


def _password(env_var: str) -> str:
    value = os.environ.get(env_var)
    if not value:
        raise SystemExit(
            f"[test_seeds] {env_var} no está definida. "
            "Ejecute la suite mediante backend/scripts/run_tests.sh, "
            "que genera las credenciales de prueba."
        )
    return value


async def seed_test_data() -> dict[str, int]:
    """Siembra el conjunto mínimo determinista. Devuelve los ids creados."""
    # Import diferido: la guarda ya validó el destino antes de llegar aquí.
    from sqlalchemy import select

    # Todos los módulos de modelos deben cargarse para que el registro de
    # SQLAlchemy pueda resolver las relaciones entre dominios (p. ej.
    # Lot -> LotPhase, definidos en módulos distintos).
    import app.audit.models  # noqa: F401
    import app.corrections.models  # noqa: F401
    import app.integrations.sap.models  # noqa: F401
    import app.lots.models  # noqa: F401
    import app.operations.models  # noqa: F401
    import app.review.models  # noqa: F401

    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import hash_password
    from app.database import async_session
    from app.masters.models import (
        BirdTypeEnum,
        Company,
        CullCause,
        Farm,
        FeedType,
        House,
        HouseType,
        Lot,
        LotStatus,
        Medication,
        MortalityCause,
        ProcessingPlant,
        Supplier,
        Transport,
        Vaccine,
    )

    created: dict[str, int] = {}

    async with async_session() as session:
        # ── Compañía ──────────────────────────────────────────────────────────
        company = (
            await session.execute(select(Company).where(Company.name == TEST_COMPANY_NAME))
        ).scalar_one_or_none()
        if company is None:
            company = Company(name=TEST_COMPANY_NAME, approval_levels=1, is_active=True)
            session.add(company)
            await session.flush()
        created["company_id"] = company.id

        # Segunda compañía: el aislamiento multiempresa no se puede verificar con una
        # sola. Los tests heredados asumían que el usuario 3 pertenecía a la compañía 2
        # sin que nadie la hubiera creado.
        company_2 = (
            await session.execute(select(Company).where(Company.name == TEST_COMPANY_2_NAME))
        ).scalar_one_or_none()
        if company_2 is None:
            company_2 = Company(name=TEST_COMPANY_2_NAME, is_active=True)
            session.add(company_2)
            await session.flush()
        created["company_id_2"] = company_2.id

        # ── Roles y permisos ──────────────────────────────────────────────────
        roles_def = {
            "TEST Super Admin": [("*", a) for a in PermissionAction],
            # Mismos criterios que la reconciliación de producción
            # (`l2m3n4o5p6q7`): si el catálogo real se completó, el de pruebas debe
            # reflejarlo o los tests estarían midiendo un sistema distinto.
            "TEST Operador": [
                ("operations", PermissionAction.CREATE),
                ("operations", PermissionAction.READ),
                ("operations", PermissionAction.UPDATE),
                ("lots", PermissionAction.READ),
                ("masters", PermissionAction.READ),
                ("dashboard", PermissionAction.READ),
            ],
            "TEST Aprobador": [
                ("operations", PermissionAction.READ),
                ("review", PermissionAction.REVIEW),
                ("approvals", PermissionAction.APPROVE),
                ("approvals", PermissionAction.REJECT),
            ],
            # Roles del flujo de aprobación con sus nombres canónicos: `seed-defaults`
            # los busca por nombre exacto (`review/service.py:471,481,489`) y sin ellos
            # el endpoint no puede sembrar los pasos.
            "Supervisor Avícola": [
                ("operations", PermissionAction.READ),
                ("review", PermissionAction.REVIEW),
                # `OD-19` Aclaración A · `GA-REM-041-A` (mismo catálogo que producción).
                ("reversals", PermissionAction.CREATE),
                ("reversals", PermissionAction.READ),
            ],
            "Aprobador": [
                ("operations", PermissionAction.READ),
                ("approvals", PermissionAction.APPROVE),
            ],
            "Analista SAP": [
                ("operations", PermissionAction.READ),
                ("sap", PermissionAction.SEND_SAP),
            ],
            # La suite heredada comprueba que existan al menos 5 roles.
            "TEST Supervisor": [
                ("operations", PermissionAction.READ),
                ("review", PermissionAction.REVIEW),
                ("review", PermissionAction.CORRECT),
            ],
            "TEST Analista SAP": [
                ("sap", PermissionAction.READ),
                ("sap", PermissionAction.SEND_SAP),
                ("operations", PermissionAction.READ),
            ],
        }
        roles: dict[str, Role] = {}
        for name, perms in roles_def.items():
            role = (
                await session.execute(select(Role).where(Role.name == name))
            ).scalar_one_or_none()
            if role is None:
                role = Role(name=name, description=f"Rol de pruebas: {name}", is_active=True)
                session.add(role)
                await session.flush()
                for module, action in perms:
                    session.add(
                        Permission(
                            role_id=role.id, module=module, action=action, scope_type="all"
                        )
                    )
            roles[name] = role
        created["role_admin_id"] = roles["TEST Super Admin"].id
        created["role_operator_id"] = roles["TEST Operador"].id
        created["role_approver_id"] = roles["TEST Aprobador"].id

        # ── Usuarios ──────────────────────────────────────────────────────────
        users_def = [
            (TEST_ADMIN_USERNAME, TEST_ADMIN_PASSWORD_ENV, "TEST Super Admin", "web"),
            (TEST_OPERATOR_USERNAME, TEST_OPERATOR_PASSWORD_ENV, "TEST Operador", "mobile"),
            (TEST_APPROVER_USERNAME, TEST_APPROVER_PASSWORD_ENV, "TEST Aprobador", "web"),
        ]
        # El usuario de la segunda compañía comparte contraseña con el operador: no se
        # introduce una variable de entorno nueva para una identidad de solo lectura.
        users_def.append(
            (TEST_OTHER_COMPANY_USERNAME, TEST_OPERATOR_PASSWORD_ENV, "TEST Operador", "web")
        )
        for username, pwd_env, role_name, view_type in users_def:
            user = (
                await session.execute(select(User).where(User.username == username))
            ).scalar_one_or_none()
            password = _password(pwd_env)
            empresa = company_2 if username == TEST_OTHER_COMPANY_USERNAME else company
            if user is None:
                session.add(
                    User(
                        company_id=empresa.id,
                        first_name="Test",
                        last_name=username,
                        # EmailStr rechaza los TLD reservados (.invalid, .test): se usa example.com,
                        # reservado por la RFC 2606 para documentación y pruebas.
                        email=f"{username}@example.com",
                        username=username,
                        hashed_password=hash_password(password),
                        role_id=roles[role_name].id,
                        view_type=view_type,
                        is_active=True,
                    )
                )
            else:
                user.hashed_password = hash_password(password)
                user.role_id = roles[role_name].id
                user.company_id = company.id
                user.is_active = True
        await session.flush()

        # ── Granja, galpón y lote ─────────────────────────────────────────────
        farm = (
            await session.execute(select(Farm).where(Farm.code == TEST_FARM_CODE))
        ).scalar_one_or_none()
        if farm is None:
            farm = Farm(
                company_id=company.id,
                name="TEST Granja",
                code=TEST_FARM_CODE,
                location="Entorno de pruebas",
                is_active=True,
            )
            session.add(farm)
            await session.flush()
        created["farm_id"] = farm.id

        # Segunda granja: destino de las salidas de aves y despachos de huevo. Sin ella
        # no se puede verificar `destination_farm_id`, que es clave foránea real.
        farm_destino = (
            await session.execute(select(Farm).where(Farm.code == TEST_FARM_DEST_CODE))
        ).scalar_one_or_none()
        if farm_destino is None:
            farm_destino = Farm(
                company_id=company.id,
                name="TEST Granja destino",
                code=TEST_FARM_DEST_CODE,
                location="Entorno de pruebas",
                is_active=True,
            )
            session.add(farm_destino)
            await session.flush()
        created["farm_dest_id"] = farm_destino.id

        house = (
            await session.execute(select(House).where(House.name == TEST_HOUSE_NAME))
        ).scalar_one_or_none()
        if house is None:
            # House no declara company_id: pertenece a la compañía vía su granja.
            house = House(
                farm_id=farm.id,
                name=TEST_HOUSE_NAME,
                capacity=10_000,
                is_active=True,
            )
            session.add(house)
            await session.flush()
        created["house_id"] = house.id

        # Segundo galpón: `inspection_details` los referencia por clave foránea y la
        # inspección de granja se registra por galpón.
        house_2 = (
            await session.execute(select(House).where(House.name == TEST_HOUSE_2_NAME))
        ).scalar_one_or_none()
        if house_2 is None:
            house_2 = House(
                farm_id=farm.id,
                name=TEST_HOUSE_2_NAME,
                capacity=10000,
                house_type=HouseType.CLOSED,
                is_active=True,
            )
            session.add(house_2)
            await session.flush()
        created["house_id_2"] = house_2.id

        # ── Catálogos maestros ────────────────────────────────────────────────
        # Los campos operativos del evento (`cause_id`, `vaccine_id`, `transport_id`…)
        # son claves foráneas reales. Sin referentes no se puede verificar que se
        # persistan, que es justamente lo que `P0-14` dejó de hacer durante meses.
        catalogos = (
            (Supplier, {"name": "TEST Proveedor", "supplier_type": "genetica"}),
            (FeedType, {"name": "TEST Iniciador", "code": "TST-INI"}),
            (Vaccine, {"name": "TEST Vacuna Newcastle", "application_route": "water"}),
            (Medication, {"name": "TEST Antibiotico"}),
            (MortalityCause, {"name": "TEST Causa de mortalidad", "category": "sanitaria"}),
            (CullCause, {"name": "TEST Causa de descarte", "category": "productiva"}),
            (Transport, {"name": "TEST Transporte", "plate": "TST-000"}),
            (ProcessingPlant, {"name": "TEST Planta de beneficio"}),
        )
        for modelo, campos in catalogos:
            existente = (
                await session.execute(select(modelo).where(modelo.name == campos["name"]))
            ).scalar_one_or_none()
            if existente is None:
                session.add(modelo(company_id=company.id, is_active=True, **campos))
        await session.flush()
        for modelo in (Supplier, FeedType, Vaccine, Medication,
                       MortalityCause, CullCause, Transport, ProcessingPlant):
            primero = (
                await session.execute(select(modelo).order_by(modelo.id))
            ).scalars().first()
            created[f"{modelo.__tablename__}_id"] = primero.id if primero else None

        # Dos lotes: la suite heredada referencia lot_id=2.
        for codigo in (TEST_LOT_CODE, TEST_LOT_CODE_2):
            existente = (
                await session.execute(select(Lot).where(Lot.lot_code == codigo))
            ).scalar_one_or_none()
            if existente is None:
                session.add(
                    Lot(
                        company_id=company.id,
                        lot_code=codigo,
                        farm_id=farm.id,
                        house_id=house.id,
                        bird_type=BirdTypeEnum.BROILER,
                        sex="mixed",
                        status=LotStatus.ACTIVE,
                        activation_type="normal",
                        start_date=lot_start_date(),
                    )
                )
        await session.flush()
        lots = (await session.execute(select(Lot).order_by(Lot.id))).scalars().all()
        created["lot_id"] = lots[0].id
        created["lot_id_2"] = lots[1].id if len(lots) > 1 else lots[0].id

        usuarios = {
            u.username: u.id
            for u in (await session.execute(select(User))).scalars().all()
        }
        created["user_admin_id"] = usuarios.get(TEST_ADMIN_USERNAME)
        created["user_operator_id"] = usuarios.get(TEST_OPERATOR_USERNAME)
        created["user_approver_id"] = usuarios.get(TEST_APPROVER_USERNAME)
        created["user_other_company_id"] = usuarios.get(TEST_OTHER_COMPANY_USERNAME)

        # El catálogo de unidades de negocio es dato de referencia del producto: sin él,
        # ninguna base es utilizable para nada que toque `GA-REM-040`. Se reutiliza la misma
        # función que el baseline en lugar de copiarla, para que las dos no discrepen.
        #
        # **Solo el catálogo.** Ni habilitaciones de empresa ni concesiones de usuario: las
        # pruebas que las necesitan las crean explícitamente, que es también lo que tendrá
        # que hacer un cliente real.
        from seeds.baseline_seeds import sembrar_unidades_de_negocio

        created["business_units"] = await sembrar_unidades_de_negocio(session)

        # `GA-REM-040` fase 6: desde que el acceso se acota por cadena productiva, un usuario
        # sin concesiones no ve dato productivo — ni siquiera el suyo. Las semillas
        # **configuran la empresa**, que es lo que hará un cliente real en su alta: habilitan
        # las cuatro cadenas y se las conceden a los usuarios sembrados.
        #
        # No es un rodeo al control. La alternativa —que la ausencia de concesión signifique
        # acceso total— es exactamente el `fail open` que esta capacidad existe para impedir.
        # Las suites que **miden** el aislamiento por cadena crean sus propios usuarios y
        # conceden a mano, unidad por unidad, porque allí la concesión es el objeto de estudio.
        from app.business_units.models import BusinessUnit, CompanyBusinessUnit
        from app.business_units.service import conceder_unidad

        unidades = (await session.execute(select(BusinessUnit))).scalars().all()
        usuarios_por_empresa: dict[int, list] = {}
        for u in (await session.execute(select(User))).scalars().all():
            if u.company_id is not None:
                usuarios_por_empresa.setdefault(u.company_id, []).append(u)

        concedidas = 0
        for company_id, usuarios_empresa in usuarios_por_empresa.items():
            habilitaciones = []
            for unidad in unidades:
                fila = (await session.execute(select(CompanyBusinessUnit).where(
                    CompanyBusinessUnit.company_id == company_id,
                    CompanyBusinessUnit.business_unit_id == unidad.id))).scalar_one_or_none()
                if fila is None:
                    fila = CompanyBusinessUnit(company_id=company_id,
                                               business_unit_id=unidad.id, is_enabled=True)
                    session.add(fila)
                    await session.flush()
                habilitaciones.append(fila)
            from app.business_units.models import UserBusinessUnit

            for usuario in usuarios_empresa:
                for fila in habilitaciones:
                    ya = (await session.execute(select(UserBusinessUnit).where(
                        UserBusinessUnit.user_id == usuario.id,
                        UserBusinessUnit.company_business_unit_id == fila.id,
                        UserBusinessUnit.revoked_at.is_(None)))).scalar_one_or_none()
                    if ya is None:
                        await conceder_unidad(session, user=usuario,
                                              company_business_unit=fila)
                        concedidas += 1
        created["business_unit_grants"] = concedidas

        await session.commit()

    return created


def main() -> None:
    # La guarda es obligatoria también aquí: los seeds escriben.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tests.environment_guard import require_safe_test_environment

    decision = require_safe_test_environment()
    os.environ["DATABASE_URL"] = decision.database_url or ""
    print(f"[test_seeds] {decision.reason}")
    ids = asyncio.run(seed_test_data())
    for key, value in sorted(ids.items()):
        print(f"[test_seeds]   {key} = {value}")
    print("[test_seeds] Datos de prueba sembrados.")


if __name__ == "__main__":
    main()

"""
Development seeds for Global Avícola.
Creates initial roles, permissions, and a super admin user.
"""
import asyncio
from asyncio import run as asyncio_run

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Permission, PermissionAction, Role, User
from app.auth.security import hash_password
from app.database import async_session


async def seed_roles(session: AsyncSession) -> dict[str, Role]:
    roles_data = [
        {
            "name": "Super Administrador",
            "description": "Control total del sistema",
            "permissions": [
                {"module": "*", "action": PermissionAction.READ},
                {"module": "*", "action": PermissionAction.CREATE},
                {"module": "*", "action": PermissionAction.UPDATE},
                {"module": "*", "action": PermissionAction.DELETE},
                {"module": "*", "action": PermissionAction.REVIEW},
                {"module": "*", "action": PermissionAction.CORRECT},
                {"module": "*", "action": PermissionAction.APPROVE},
                {"module": "*", "action": PermissionAction.REJECT},
                {"module": "*", "action": PermissionAction.SEND_SAP},
            ],
        },
        {
            "name": "Supervisor Avícola",
            "description": "Supervisión operativa de granjas",
            "permissions": [
                {"module": "operations", "action": PermissionAction.READ},
                {"module": "lots", "action": PermissionAction.READ},
                {"module": "review", "action": PermissionAction.REVIEW},
                {"module": "review", "action": PermissionAction.CORRECT},
                {"module": "approvals", "action": PermissionAction.READ},
                {"module": "reports", "action": PermissionAction.READ},
            ],
        },
        {
            "name": "Operador de Granja",
            "description": "Registro operativo en campo",
            "permissions": [
                {"module": "operations", "action": PermissionAction.CREATE},
                {"module": "operations", "action": PermissionAction.READ},
                {"module": "lots", "action": PermissionAction.READ},
            ],
        },
        {
            "name": "Aprobador",
            "description": "Aprobación de registros operativos",
            "permissions": [
                {"module": "operations", "action": PermissionAction.READ},
                {"module": "review", "action": PermissionAction.READ},
                {"module": "approvals", "action": PermissionAction.APPROVE},
                {"module": "approvals", "action": PermissionAction.REJECT},
                {"module": "approvals", "action": PermissionAction.REVIEW},
                {"module": "approvals", "action": PermissionAction.CORRECT},
                {"module": "reports", "action": PermissionAction.READ},
            ],
        },
        {
            "name": "Analista SAP",
            "description": "Gestión de integración SAP",
            "permissions": [
                {"module": "sap", "action": PermissionAction.READ},
                {"module": "sap", "action": PermissionAction.CREATE},
                {"module": "sap", "action": PermissionAction.SEND_SAP},
                {"module": "operations", "action": PermissionAction.READ},
                {"module": "reports", "action": PermissionAction.READ},
            ],
        },
        {
            "name": "Auditor",
            "description": "Consulta de auditoría",
            "permissions": [
                {"module": "audit", "action": PermissionAction.READ},
                {"module": "reports", "action": PermissionAction.READ},
                {"module": "operations", "action": PermissionAction.READ},
            ],
        },
    ]

    created_roles = {}
    for role_data in roles_data:
        # Check if role already exists
        existing = await session.execute(select(Role).where(Role.name == role_data["name"]))
        if existing.scalar_one_or_none():
            continue

        role = Role(name=role_data["name"], description=role_data["description"])
        session.add(role)
        await session.flush()

        for perm_data in role_data["permissions"]:
            perm = Permission(
                role_id=role.id,
                module=perm_data["module"],
                action=perm_data["action"],
                scope_type="all",
            )
            session.add(perm)

        created_roles[role_data["name"]] = role
        print(f"  ✅ Rol: {role.name} ({len(role_data['permissions'])} permisos)")

    return created_roles


async def seed_users(session: AsyncSession, roles: dict[str, Role]):
    users_data = [
        {
            "first_name": "Admin",
            "last_name": "Sistema",
            "email": "admin@globalavicola.com",
            "username": "admin",
            "password": "admin123",
            "role_name": "Super Administrador",
        },
        {
            "first_name": "María",
            "last_name": "Supervisora",
            "email": "supervisora@globalavicola.com",
            "username": "supervisora",
            "password": "super123",
            "role_name": "Supervisor Avícola",
        },
        {
            "first_name": "Juan",
            "last_name": "Operador",
            "email": "operador@globalavicola.com",
            "username": "operador",
            "password": "oper123",
            "role_name": "Operador de Granja",
        },
        {
            "first_name": "Carlos",
            "last_name": "Aprobador",
            "email": "aprobador@globalavicola.com",
            "username": "aprobador",
            "password": "aprob123",
            "role_name": "Aprobador",
        },
        {
            "first_name": "Ana",
            "last_name": "SAP",
            "email": "sap@globalavicola.com",
            "username": "sap_analyst",
            "password": "sap123",
            "role_name": "Analista SAP",
        },
        {
            "first_name": "Auditor",
            "last_name": "Interno",
            "email": "auditor@globalavicola.com",
            "username": "auditor",
            "password": "audit123",
            "role_name": "Auditor",
        },
        {
            "first_name": "Operador",
            "last_name": "Móvil",
            "email": "operador.mobile@globalavicola.com",
            "username": "operador.mobile",
            "password": "mobile123456",
            "role_name": "Operador de Granja",
            "view_type": "mobile",
        },
    ]

    for user_data in users_data:
        existing = await session.execute(select(User).where(User.username == user_data["username"]))
        existing_user = existing.scalar_one_or_none()
        if existing_user:
            desired_view = user_data.get("view_type", "web")
            if existing_user.view_type != desired_view:
                existing_user.view_type = desired_view
                session.add(existing_user)
                print(f"  🔄 Usuario '{user_data['username']}' ya existe, view_type actualizado a '{desired_view}'")
            else:
                print(f"  ⏭️  Usuario '{user_data['username']}' ya existe, saltando...")
            continue

        role = roles.get(user_data["role_name"])
        user = User(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            username=user_data["username"],
            phone=None,
            hashed_password=hash_password(user_data["password"]),
            role_id=role.id if role else None,
            view_type=user_data.get("view_type", "web"),
        )
        session.add(user)
        print(f"  ✅ Usuario: {user.username} ({user_data['role_name']}) [vista: {user.view_type}]")


async def main():
    print("🌱 Sembrando datos de desarrollo...")
    print()

    async with async_session() as session:
        print("📋 Creando roles y permisos...")
        roles = await seed_roles(session)

        print()
        print("👤 Creando usuarios...")
        await seed_users(session, roles)

        await session.commit()

    print()
    print("✅ Seeds completados!")
    print()
    print("   Usuarios de prueba:")
    print("   ┌──────────────────┬─────────────────┐")
    print("   │ admin            │ admin123        │")
    print("   │ supervisora      │ super123        │")
    print("   │ operador         │ oper123         │")
    print("   │ operador.mobile  │ mobile123456    │")
    print("   │ aprobador        │ aprob123        │")
    print("   │ sap_analyst      │ sap123          │")
    print("   │ auditor          │ audit123        │")
    print("   └──────────────────┴─────────────────┘")


if __name__ == "__main__":
    asyncio_run(main())

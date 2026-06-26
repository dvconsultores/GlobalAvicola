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
from app.masters.models import (
    Breed, CullCause, Farm, FarmType, FeedType, Hatcher, Hatchery,
    House, HouseType, Incubator, Medication, MortalityCause,
    ProcessingPlant, Supplier, Transport, Vaccine,
)
import app.lots.models  # noqa: F401 — register LotPhase/OpeningBalance mappers


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


async def seed_catalogs(session: AsyncSession, company_id: int) -> None:
    """Seed all master catalog tables needed by operation forms."""

    # ── Helper: skip if already seeded ───────────────────────────────
    async def already_seeded(model) -> bool:
        r = await session.execute(select(model).limit(1))
        return r.first() is not None

    # ── Farms & Houses ────────────────────────────────────────────────
    if not await already_seeded(Farm):
        farms_data = [
            Farm(company_id=company_id, name="Granja Norte",   code="GN-01", farm_type=FarmType.BREEDING,    location="Zona Norte"),
            Farm(company_id=company_id, name="Granja Sur",     code="GS-01", farm_type=FarmType.PRODUCTION,  location="Zona Sur"),
            Farm(company_id=company_id, name="Granja Engorde", code="GE-01", farm_type=FarmType.FATTENING,   location="Zona Este"),
        ]
        session.add_all(farms_data)
        await session.flush()  # get IDs

        houses_data = []
        for farm in farms_data:
            for i in range(1, 5):
                houses_data.append(House(
                    farm_id=farm.id, name=f"Galpón {i}",
                    capacity=5000, house_type=HouseType.OPEN,
                ))
        session.add_all(houses_data)
        print("  ✅ Granjas (3) y Galpones (12)")

    # ── Hatchery / Incubators / Hatchers ─────────────────────────────
    if not await already_seeded(Hatchery):
        hatchery = Hatchery(company_id=company_id, name="Incubadora Central", code="INC-01", location="Planta Principal")
        session.add(hatchery)
        await session.flush()
        session.add_all([
            Incubator(hatchery_id=hatchery.id, name="Incubadora 1", capacity=28800),
            Incubator(hatchery_id=hatchery.id, name="Incubadora 2", capacity=28800),
            Incubator(hatchery_id=hatchery.id, name="Incubadora 3", capacity=28800),
            Incubator(hatchery_id=hatchery.id, name="Incubadora 4", capacity=28800),
            Hatcher(hatchery_id=hatchery.id,   name="Nacedora 1",   capacity=9600),
            Hatcher(hatchery_id=hatchery.id,   name="Nacedora 2",   capacity=9600),
        ])
        print("  ✅ Incubadora (1) · Incubadoras (4) · Nacedoras (2)")

    # ── Processing Plants ─────────────────────────────────────────────
    if not await already_seeded(ProcessingPlant):
        session.add_all([
            ProcessingPlant(company_id=company_id, name="Planta de Procesamiento Central", location="Zona Industrial Norte"),
            ProcessingPlant(company_id=company_id, name="Planta Frigorífico Sur",          location="Zona Industrial Sur"),
        ])
        print("  ✅ Plantas procesadoras (2)")

    # ── Suppliers ─────────────────────────────────────────────────────
    if not await already_seeded(Supplier):
        session.add_all([
            Supplier(company_id=company_id, name="Cobb-Vantress",       sap_code="PROV-001", country="USA",       supplier_type="genetica"),
            Supplier(company_id=company_id, name="Aviagen (Ross)",       sap_code="PROV-002", country="USA",       supplier_type="genetica"),
            Supplier(company_id=company_id, name="Hendrix Genetics",     sap_code="PROV-003", country="Holanda",   supplier_type="genetica"),
            Supplier(company_id=company_id, name="Lohmann Tierzucht",    sap_code="PROV-004", country="Alemania",  supplier_type="genetica"),
            Supplier(company_id=company_id, name="Proveedor Local 1",    sap_code="PROV-005", country="Venezuela", supplier_type="insumos"),
        ])
        print("  ✅ Proveedores (5)")

    # ── Breeds ────────────────────────────────────────────────────────
    if not await already_seeded(Breed):
        session.add_all([
            Breed(name="Ross 308",         bird_type="breeder",     description="Línea de engorde Ross"),
            Breed(name="Cobb 500",         bird_type="breeder",     description="Línea de engorde Cobb"),
            Breed(name="Arbor Acres Plus", bird_type="breeder",     description="Línea de engorde Aviagen"),
            Breed(name="Hy-Line Brown",    bird_type="grandparent", description="Línea ponedora café"),
            Breed(name="Hy-Line W-36",     bird_type="grandparent", description="Línea ponedora blanca"),
            Breed(name="Lohmann Brown",    bird_type="grandparent", description="Línea ponedora café"),
        ])
        print("  ✅ Líneas/Razas (6)")

    # ── Transports ────────────────────────────────────────────────────
    if not await already_seeded(Transport):
        session.add_all([
            Transport(company_id=company_id, name="Camión Avícola 1",  plate="ABC-123", transport_type="camion_aves",   capacity=10000),
            Transport(company_id=company_id, name="Camión Avícola 2",  plate="DEF-456", transport_type="camion_aves",   capacity=10000),
            Transport(company_id=company_id, name="Camión Huevos 1",   plate="GHI-789", transport_type="camion_huevos", capacity=50000),
            Transport(company_id=company_id, name="Camioneta Logística",plate="JKL-012", transport_type="camioneta",     capacity=2000),
        ])
        print("  ✅ Transportes (4)")

    # ── Feed Types ────────────────────────────────────────────────────
    if not await already_seeded(FeedType):
        session.add_all([
            FeedType(company_id=company_id, name="Pre-iniciación",   code="PI",  presentation="Migaja"),
            FeedType(company_id=company_id, name="Iniciación",       code="INI", presentation="Migaja"),
            FeedType(company_id=company_id, name="Crecimiento",      code="CRE", presentation="Pellet"),
            FeedType(company_id=company_id, name="Desarrollo",       code="DES", presentation="Pellet"),
            FeedType(company_id=company_id, name="Prepostura",       code="PRE", presentation="Harina"),
            FeedType(company_id=company_id, name="Postura",          code="POS", presentation="Harina"),
            FeedType(company_id=company_id, name="Engorde Fase 1",   code="ENG1",presentation="Pellet"),
            FeedType(company_id=company_id, name="Engorde Fase 2",   code="ENG2",presentation="Pellet"),
            FeedType(company_id=company_id, name="Finalizador",      code="FIN", presentation="Pellet"),
        ])
        print("  ✅ Tipos de alimento (9)")

    # ── Vaccines ──────────────────────────────────────────────────────
    if not await already_seeded(Vaccine):
        session.add_all([
            Vaccine(company_id=company_id, name="Newcastle (IB King)",       laboratory="Zoetis",     vaccine_type="viral",      application_route="water"),
            Vaccine(company_id=company_id, name="Gumboro (IBD)",             laboratory="MSD Animal", vaccine_type="viral",      application_route="water"),
            Vaccine(company_id=company_id, name="Bronquitis Infecciosa H120",laboratory="Ceva",       vaccine_type="viral",      application_route="spray"),
            Vaccine(company_id=company_id, name="Marek HVT+SB1",            laboratory="Merck",      vaccine_type="viral",      application_route="injection"),
            Vaccine(company_id=company_id, name="Viruela Aviar (FP)",        laboratory="Ceva",       vaccine_type="viral",      application_route="wing_stab"),
            Vaccine(company_id=company_id, name="Laringotraqueitis (ILT)",   laboratory="Zoetis",     vaccine_type="viral",      application_route="eye"),
            Vaccine(company_id=company_id, name="Encefalomielitis Aviar",    laboratory="MSD Animal", vaccine_type="viral",      application_route="wing_stab"),
            Vaccine(company_id=company_id, name="Salmonella (AviPro)",       laboratory="Elanco",     vaccine_type="bacteriana", application_route="spray"),
            Vaccine(company_id=company_id, name="Coriza Infecciosa",         laboratory="Hipra",      vaccine_type="bacteriana", application_route="injection"),
            Vaccine(company_id=company_id, name="Pasteurella (Cólera)",      laboratory="Ceva",       vaccine_type="bacteriana", application_route="injection"),
        ])
        print("  ✅ Vacunas (10)")

    # ── Medications ───────────────────────────────────────────────────
    if not await already_seeded(Medication):
        session.add_all([
            Medication(company_id=company_id, name="Amoxicilina 50%",       laboratory="Vetanco",  presentation="Polvo soluble"),
            Medication(company_id=company_id, name="Enrofloxacina 10%",     laboratory="Bayer",    presentation="Solución oral"),
            Medication(company_id=company_id, name="Tilosina 20%",          laboratory="Elanco",   presentation="Polvo soluble"),
            Medication(company_id=company_id, name="Sulfametoxazol+TMP",    laboratory="Vetanco",  presentation="Polvo soluble"),
            Medication(company_id=company_id, name="Oxitetraciclina 20%",   laboratory="Pfizer",   presentation="Polvo soluble"),
            Medication(company_id=company_id, name="Lincomicina+Espectino",  laboratory="Pharmaq", presentation="Polvo soluble"),
            Medication(company_id=company_id, name="Vitaminas ADE",         laboratory="Ceva",     presentation="Solución oral"),
            Medication(company_id=company_id, name="Electrolitos+Glucosa",  laboratory="Vetanco",  presentation="Polvo soluble"),
            Medication(company_id=company_id, name="Ácido Cítrico 50%",     laboratory="Biovet",   presentation="Polvo soluble"),
            Medication(company_id=company_id, name="Amprolium 20%",         laboratory="MSD",      presentation="Polvo soluble"),
        ])
        print("  ✅ Medicamentos (10)")

    # ── Mortality Causes ──────────────────────────────────────────────
    if not await already_seeded(MortalityCause):
        session.add_all([
            MortalityCause(company_id=company_id, name="Newcastle",                 category="enfermedades_virales"),
            MortalityCause(company_id=company_id, name="Gumboro (IBD)",             category="enfermedades_virales"),
            MortalityCause(company_id=company_id, name="Bronquitis Infecciosa",     category="enfermedades_virales"),
            MortalityCause(company_id=company_id, name="Marek",                     category="enfermedades_virales"),
            MortalityCause(company_id=company_id, name="Micoplasmosis",             category="enfermedades_bacterianas"),
            MortalityCause(company_id=company_id, name="Salmonelosis",              category="enfermedades_bacterianas"),
            MortalityCause(company_id=company_id, name="Cólera Aviar",              category="enfermedades_bacterianas"),
            MortalityCause(company_id=company_id, name="Ascitis (Síndrome Hídrico)",category="metabolicas"),
            MortalityCause(company_id=company_id, name="Muerte Súbita",             category="metabolicas"),
            MortalityCause(company_id=company_id, name="Trauma / Aplaste",          category="accidentes"),
            MortalityCause(company_id=company_id, name="Estrés Calórico",           category="ambiental"),
            MortalityCause(company_id=company_id, name="Causa Indeterminada",       category="otros"),
        ])
        print("  ✅ Causas de mortalidad (12)")

    # ── Cull Causes ───────────────────────────────────────────────────
    if not await already_seeded(CullCause):
        session.add_all([
            CullCause(company_id=company_id, name="Raquitismo",              category="desarrollo"),
            CullCause(company_id=company_id, name="Mal conformados",         category="desarrollo"),
            CullCause(company_id=company_id, name="Ceguera / Lesión ocular", category="lesiones"),
            CullCause(company_id=company_id, name="Lesión de pata",          category="lesiones"),
            CullCause(company_id=company_id, name="Descarte por peso bajo",  category="productividad"),
            CullCause(company_id=company_id, name="Descarte fin de ciclo",   category="productividad"),
            CullCause(company_id=company_id, name="Prolapso",                category="reproductivo"),
            CullCause(company_id=company_id, name="Bajo rendimiento postura",category="reproductivo"),
        ])
        print("  ✅ Causas de descarte (8)")


async def main():
    print("🌱 Sembrando datos de desarrollo...")
    print()

    async with async_session() as session:
        print("📋 Creando roles y permisos...")
        roles = await seed_roles(session)

        print()
        print("👤 Creando usuarios...")
        await seed_users(session, roles)

        print()
        print("📦 Creando catálogos maestros...")
        await seed_catalogs(session, company_id=1)

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

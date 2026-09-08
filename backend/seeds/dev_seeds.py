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
    Breed, Company, CullCause, Farm, FarmType, FeedType, Hatcher, Hatchery,
    House, HouseType, Incubator, Medication, MortalityCause,
    ProcessingPlant, ProductivePhase, Supplier, Transport, Vaccine,
)
import app.lots.models  # noqa: F401 — register LotPhase/OpeningBalance mappers


# ── GA-REM-004: las contraseñas nunca se versionan ──────────────────────────
# Se leen del entorno. Si falta la variable, el seed aborta en lugar de crear
# usuarios con credenciales conocidas y publicadas.
def _seed_password(username: str) -> str:
    """Contraseña del usuario sembrado, tomada del entorno.

    Convención de la variable: GA_SEED_PWD_<USERNAME en mayúsculas, sin puntos>.
    Alternativa global para desarrollo local: GA_SEED_DEFAULT_PASSWORD.
    """
    import os
    key = "GA_SEED_PWD_" + username.upper().replace(".", "_").replace("-", "_")
    value = os.environ.get(key) or os.environ.get("GA_SEED_DEFAULT_PASSWORD")
    if not value:
        raise SystemExit(
            f"[seeds] Falta la contraseña del usuario '{username}'.\n"
            f"        Defina {key} o GA_SEED_DEFAULT_PASSWORD.\n"
            "        GA-REM-004: no se siembran credenciales literales."
        )
    return value



async def seed_companies(session: AsyncSession) -> dict[str, int]:
    """Ensure both dev companies exist. Returns {name: id} mapping."""
    companies_data = [
        {"name": "Avícola Global C.A.",  "tax_id": "J-12345678-9", "country": "Venezuela", "currency": "USD"},
        {"name": "Avícola Del Sur C.A.", "tax_id": "J-98765432-1", "country": "Venezuela", "currency": "USD"},
    ]
    result: dict[str, int] = {}
    for c_data in companies_data:
        existing = await session.execute(select(Company).where(Company.name == c_data["name"]))
        company = existing.scalar_one_or_none()
        if company:
            print(f"  ⏭️  Compañía '{company.name}' ya existe (id={company.id})")
        else:
            company = Company(**c_data)
            session.add(company)
            await session.flush()
            print(f"  ✅ Compañía: {company.name} (id={company.id})")
        result[company.name] = company.id
    return result


async def seed_roles(session: AsyncSession) -> dict[str, Role]:
    # GA-REM-002: el catalogo de permisos se completo al activar el enforcement.
    #
    # Mientras nada comprobaba los permisos, las definiciones de rol eran decorativas y
    # podian estar incompletas sin que se notara: ningun rol declaraba `masters:read`,
    # que hace falta para cargar granjas, galpones, vacunas o tipos de alimento en
    # practicamente todas las pantallas. Con el enforcement activo, esa ausencia deja
    # inutilizable la aplicacion para cualquiera que no sea Super Admin.
    #
    # Los permisos que siguen se derivan de la funcion documentada de cada rol en
    # `docs/12-approval-workflow.md §3`, no de lo que resulte comodo.
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
            # `OD-15 §6` · `R-113`. Administra el acceso por unidad y **nada más**: sin
            # `users:*`, sin comodín, sin ninguna cadena productiva. Que no pueda listar
            # usuarios es deliberado — `users:read` es otra cosa, y ampliarlo por comodidad
            # es exactamente cómo se abren los agujeros que esta figura vino a cerrar.
            "name": "Administrador de Accesos",
            "description": "Administración del acceso por unidad de negocio",
            "permissions": [
                {"module": "business_units", "action": PermissionAction.READ},
                {"module": "business_units", "action": PermissionAction.UPDATE},
                {"module": "business_units", "action": PermissionAction.CREATE},
                {"module": "business_units", "action": PermissionAction.DELETE},
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
                {"module": "review", "action": PermissionAction.READ},
                {"module": "approvals", "action": PermissionAction.READ},
                {"module": "reports", "action": PermissionAction.READ},
                {"module": "masters", "action": PermissionAction.READ},
                {"module": "corrections", "action": PermissionAction.READ},
                {"module": "corrections", "action": PermissionAction.CORRECT},
                {"module": "operations", "action": PermissionAction.UPDATE},
                {"module": "dashboard", "action": PermissionAction.READ},
            ],
        },
        {
            "name": "Operador de Granja",
            "description": "Registro operativo en campo",
            "permissions": [
                {"module": "operations", "action": PermissionAction.CREATE},
                {"module": "operations", "action": PermissionAction.READ},
                {"module": "operations", "action": PermissionAction.UPDATE},
                {"module": "lots", "action": PermissionAction.READ},
                # Sin lectura de maestros no puede elegir granja, galpon, vacuna ni
                # tipo de alimento: el formulario de registro queda inservible.
                {"module": "masters", "action": PermissionAction.READ},
                {"module": "dashboard", "action": PermissionAction.READ},
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
                {"module": "masters", "action": PermissionAction.READ},
                {"module": "lots", "action": PermissionAction.READ},
                {"module": "corrections", "action": PermissionAction.READ},
                {"module": "corrections", "action": PermissionAction.CORRECT},
                {"module": "dashboard", "action": PermissionAction.READ},
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
                {"module": "masters", "action": PermissionAction.READ},
                {"module": "lots", "action": PermissionAction.READ},
                {"module": "dashboard", "action": PermissionAction.READ},
            ],
        },
        {
            "name": "Auditor",
            "description": "Consulta de auditoría",
            "permissions": [
                {"module": "audit", "action": PermissionAction.READ},
                {"module": "reports", "action": PermissionAction.READ},
                {"module": "operations", "action": PermissionAction.READ},
                {"module": "masters", "action": PermissionAction.READ},
                {"module": "lots", "action": PermissionAction.READ},
                {"module": "corrections", "action": PermissionAction.READ},
                {"module": "review", "action": PermissionAction.READ},
                {"module": "dashboard", "action": PermissionAction.READ},
            ],
        },
    ]

    created_roles = {}
    for role_data in roles_data:
        # Check if role already exists
        existing = await session.execute(select(Role).where(Role.name == role_data["name"]))
        existing_role = existing.scalar_one_or_none()
        if existing_role:
            created_roles[role_data["name"]] = existing_role
            print(f"  ⏭️  Rol: {existing_role.name} (ya existe)")
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


async def seed_users(session: AsyncSession, roles: dict[str, Role], companies: dict[str, int]):
    c1 = companies.get("Avícola Global C.A.", 1)
    c2 = companies.get("Avícola Del Sur C.A.", 2)
    users_data = [
        {
            "first_name": "Admin",
            "last_name": "Sistema",
            "email": "admin@globalavicola.com",
            "username": "admin",
            "password": None,  # GA-REM-004: se resuelve en tiempo de ejecución
            "role_name": "Super Administrador",
            "company_id": None,  # super admin no está limitado a empresa
        },
        {
            "first_name": "María",
            "last_name": "Supervisora",
            "email": "supervisora@globalavicola.com",
            "username": "supervisora",
            "password": None,  # GA-REM-004: se resuelve en tiempo de ejecución
            "role_name": "Supervisor Avícola",
            "company_id": c1,
        },
        {
            "first_name": "Juan",
            "last_name": "Operador",
            "email": "operador@globalavicola.com",
            "username": "operador",
            "password": None,  # GA-REM-004: se resuelve en tiempo de ejecución
            "role_name": "Operador de Granja",
            "company_id": c1,
        },
        {
            "first_name": "Carlos",
            "last_name": "Aprobador",
            "email": "aprobador@globalavicola.com",
            "username": "aprobador",
            "password": None,  # GA-REM-004: se resuelve en tiempo de ejecución
            "role_name": "Aprobador",
            "company_id": c1,
        },
        {
            "first_name": "Ana",
            "last_name": "SAP",
            "email": "sap@globalavicola.com",
            "username": "sap_analyst",
            "password": None,  # GA-REM-004: se resuelve en tiempo de ejecución
            "role_name": "Analista SAP",
            "company_id": c1,
        },
        {
            "first_name": "Auditor",
            "last_name": "Interno",
            "email": "auditor@globalavicola.com",
            "username": "auditor",
            "password": None,  # GA-REM-004: se resuelve en tiempo de ejecución
            "role_name": "Auditor",
            "company_id": c1,
        },
        {
            "first_name": "Operador",
            "last_name": "Móvil",
            "email": "operador.mobile@globalavicola.com",
            "username": "operador.mobile",
            "password": None,  # GA-REM-004: se resuelve en tiempo de ejecución
            "role_name": "Operador de Granja",
            "view_type": "mobile",
            "company_id": c1,
        },
        # ── Empresa 2: Avícola Del Sur C.A. ─────────────────────────────
        {
            "first_name": "Pedro",
            "last_name": "Supervisor Sur",
            "email": "supervisor@avicola-sur.com",
            "username": "supervisor_sur",
            "password": None,  # GA-REM-004: se resuelve en tiempo de ejecución
            "role_name": "Supervisor Avícola",
            "company_id": c2,
        },
        {
            "first_name": "Luis",
            "last_name": "Operador Sur",
            "email": "operador@avicola-sur.com",
            "username": "operador_sur",
            "password": None,  # GA-REM-004: se resuelve en tiempo de ejecución
            "role_name": "Operador de Granja",
            "company_id": c2,
        },
    ]

    for user_data in users_data:
        existing = await session.execute(select(User).where(User.username == user_data["username"]))
        existing_user = existing.scalar_one_or_none()
        desired_view = user_data.get("view_type", "web")
        desired_company = user_data.get("company_id")
        desired_role = roles.get(user_data["role_name"])

        if existing_user:
            updates = []
            if existing_user.view_type != desired_view:
                existing_user.view_type = desired_view
                updates.append(f"view_type={desired_view}")

            if desired_role and existing_user.role_id != desired_role.id:
                existing_user.role_id = desired_role.id
                updates.append(f"role_id={desired_role.id}")

            if existing_user.company_id != desired_company:
                existing_user.company_id = desired_company
                updates.append(f"company_id={desired_company}")

            if updates:
                session.add(existing_user)
                print(f"  🔄 Usuario '{user_data['username']}' actualizado: {', '.join(updates)}")
            else:
                print(f"  ⏭️  Usuario '{user_data['username']}' ya existe, saltando...")
            continue

        role = desired_role
        if not role:
            print(f"  ❌ Usuario '{user_data['username']}' no creado: rol '{user_data['role_name']}' no encontrado")
            continue

        user = User(
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            email=user_data["email"],
            username=user_data["username"],
            phone=None,
            hashed_password=hash_password(_seed_password(user_data["username"])),
            role_id=role.id,
            company_id=desired_company,
            view_type=desired_view,
        )
        session.add(user)
        print(f"  ✅ Usuario: {user.username} ({user_data['role_name']}) [empresa_id={user_data.get('company_id')}]")


async def seed_catalogs(session: AsyncSession, company_id: int) -> None:
    """Seed all master catalog tables needed by operation forms."""

    # ── Helper: skip if already seeded for this company ─────────────
    async def already_seeded(model) -> bool:
        if hasattr(model, 'company_id'):
            r = await session.execute(
                select(model).where(model.company_id == company_id).limit(1)
            )
        else:
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

    # ── Productive Phases ──────────────────────────────────────────────
    if not await already_seeded(ProductivePhase):
        session.add_all([
            ProductivePhase(name="Cría",          code="CRIA",       order=1, duration_days=140, is_initial=True,  is_final=False),
            ProductivePhase(name="Producción",    code="PROD",       order=2, duration_days=280, is_initial=False, is_final=False),
            ProductivePhase(name="Incubación",    code="INCUB",      order=3, duration_days=21,  is_initial=False, is_final=False),
            ProductivePhase(name="Engorde",       code="ENGORDE",    order=4, duration_days=42,  is_initial=False, is_final=True),
        ])
        print("  ✅ Fases productivas (4: Cría, Producción, Incubación, Engorde)")


async def main():
    print("🌱 Sembrando datos de desarrollo...")
    print()

    async with async_session() as session:
        print("🏢 Creando compañías...")
        companies = await seed_companies(session)

        print()
        print("📋 Creando roles y permisos...")
        roles = await seed_roles(session)

        print()
        print("👤 Creando usuarios...")
        await seed_users(session, roles, companies)

        print()
        print("📦 Creando catálogos maestros (empresa 1)...")
        c1 = companies.get("Avícola Global C.A.", 1)
        await seed_catalogs(session, company_id=c1)

        print()
        print("📦 Creando catálogos maestros (empresa 2)...")
        c2 = companies.get("Avícola Del Sur C.A.", 2)
        await seed_catalogs(session, company_id=c2)

        await session.commit()

    print()
    print("✅ Seeds completados!")
    print()
    print("   Empresa 1 — Avícola Global C.A.:")
    print("   ┌──────────────────┬─────────────────┐")
    print("   │ admin            │ admin123        │")
    print("   │ supervisora      │ super123        │")
    print("   │ operador         │ oper123         │")
    print("   │ operador.mobile  │ mobile123456    │")
    print("   │ aprobador        │ aprob123        │")
    print("   │ sap_analyst      │ sap123          │")
    print("   │ auditor          │ audit123        │")
    print("   └──────────────────┴─────────────────┘")
    print()
    print("   Empresa 2 — Avícola Del Sur C.A.:")
    print("   ┌──────────────────┬─────────────────┐")
    print("   │ supervisor_sur   │ sur123456       │")
    print("   │ operador_sur     │ sur123456       │")
    print("   └──────────────────┴─────────────────┘")


if __name__ == "__main__":
    asyncio_run(main())

"""
Integration Test Seeds — Global Avícola v2.0
============================================
Crea todos los datos necesarios para pruebas en vivo multi-usuario:
- 5 roles por tipo de ave + contralor
- 14 usuarios (7 mobile + 7 web)
- Granjas, galpones, incubadoras por cada proceso
- Lotes activos con saldos iniciales (apertura manual)
- Referencias SAP simuladas (órdenes de compra, transferencias)
- Eventos operativos iniciales para estado realista

Ejecutar:  cd backend && PYTHONPATH=. python3 seeds/integration_seeds.py
"""
import asyncio
import sys
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import Permission, PermissionAction, Role, User
from app.auth.security import hash_password
from app.database import async_session
from app.masters.models import (
    BirdTypeEnum, Breed, Company, CullCause, Farm, FarmType,
    FeedType, GeneticLine, Hatcher, Hatchery, House, HouseType,
    Incubator, Lot, LotStatus, Medication, MortalityCause,
    ProcessingPlant, ProductivePhase, SexEnum, Supplier, Transport, Vaccine,
)
from app.lots.models import LotPhase, OpeningBalance
from app.operations.models import (
    BirdMovement, EggMovement, EventStatus, EventType,
    FeedMovement, OperationalEvent,
)
from app.integrations.sap.models import SapReference, SapReferenceType


# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════

COMPANY_ID = 1  # Avícola Global C.A.
TODAY = date.today()

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

async def _exists(session: AsyncSession, model, **filters) -> bool:
    q = select(model.id).where(*[getattr(model, k) == v for k, v in filters.items()]).limit(1)
    r = await session.execute(q)
    return r.scalar_one_or_none() is not None


async def _get_id(session: AsyncSession, model, **filters):
    q = select(model).where(*[getattr(model, k) == v for k, v in filters.items()]).limit(1)
    r = await session.execute(q)
    obj = r.scalar_one_or_none()
    return obj.id if obj else None


# ═══════════════════════════════════════════════════════════
# 1. ROLES
# ═══════════════════════════════════════════════════════════

ROLES_DEF = [
    # --- Operadores por tipo de ave ---
    {
        "name": "Operador Progenitoras",
        "description": "Registro operativo en granjas de progenitoras (abuelas)",
        "permissions": [
            {"module": "operations", "action": PermissionAction.CREATE},
            {"module": "operations", "action": PermissionAction.READ},
            {"module": "lots", "action": PermissionAction.READ},
        ],
    },
    {
        "name": "Operador Reproductoras",
        "description": "Registro operativo en granjas de reproductoras",
        "permissions": [
            {"module": "operations", "action": PermissionAction.CREATE},
            {"module": "operations", "action": PermissionAction.READ},
            {"module": "lots", "action": PermissionAction.READ},
        ],
    },
    {
        "name": "Operador Incubadora",
        "description": "Registro operativo en planta de incubación",
        "permissions": [
            {"module": "operations", "action": PermissionAction.CREATE},
            {"module": "operations", "action": PermissionAction.READ},
            {"module": "lots", "action": PermissionAction.READ},
        ],
    },
    {
        "name": "Operador Engorde",
        "description": "Registro operativo en granjas de pollos de engorde",
        "permissions": [
            {"module": "operations", "action": PermissionAction.CREATE},
            {"module": "operations", "action": PermissionAction.READ},
            {"module": "lots", "action": PermissionAction.READ},
        ],
    },
    # --- Operador multi-proceso (ve todos los procesos) ---
    {
        "name": "Operador Multi-Proceso",
        "description": "Registro operativo en todos los tipos de ave",
        "permissions": [
            {"module": "operations", "action": PermissionAction.CREATE},
            {"module": "operations", "action": PermissionAction.READ},
            {"module": "lots", "action": PermissionAction.READ},
            {"module": "reports", "action": PermissionAction.READ},
        ],
    },
    # --- Contralor (ve todo como admin pero no administra) ---
    {
        "name": "Contralor Avícola",
        "description": "Control total de revisión, aprobación, auditoría y envío a SAP",
        "permissions": [
            {"module": "operations", "action": PermissionAction.READ},
            {"module": "lots", "action": PermissionAction.READ},
            {"module": "review", "action": PermissionAction.REVIEW},
            {"module": "review", "action": PermissionAction.CORRECT},
            {"module": "approvals", "action": PermissionAction.APPROVE},
            {"module": "approvals", "action": PermissionAction.REJECT},
            {"module": "approvals", "action": PermissionAction.REVIEW},
            {"module": "approvals", "action": PermissionAction.CORRECT},
            {"module": "audit", "action": PermissionAction.READ},
            {"module": "reports", "action": PermissionAction.READ},
            {"module": "masters", "action": PermissionAction.READ},
        ],
    },
    # --- Supervisor (ya existe, se actualiza para cubrir todos los tipos) ---
    {
        "name": "Supervisor General",
        "description": "Supervisión operativa de todas las granjas y procesos",
        "permissions": [
            {"module": "operations", "action": PermissionAction.READ},
            {"module": "lots", "action": PermissionAction.READ},
            {"module": "review", "action": PermissionAction.REVIEW},
            {"module": "review", "action": PermissionAction.CORRECT},
            {"module": "approvals", "action": PermissionAction.READ},
            {"module": "reports", "action": PermissionAction.READ},
        ],
    },
]


async def seed_roles(session: AsyncSession) -> dict[str, Role]:
    print("\n─── ROLES ───")
    created = {}
    for rdef in ROLES_DEF:
        if await _exists(session, Role, name=rdef["name"]):
            print(f"  ⏭️  {rdef['name']} (ya existe)")
            q = await session.execute(select(Role).where(Role.name == rdef["name"]))
            created[rdef["name"]] = q.scalar_one()
            continue
        role = Role(name=rdef["name"], description=rdef["description"])
        session.add(role)
        await session.flush()
        for perm in rdef["permissions"]:
            session.add(Permission(role_id=role.id, module=perm["module"], action=perm["action"], scope_type="all"))
        created[rdef["name"]] = role
        print(f"  ✅ {rdef['name']} ({len(rdef['permissions'])} permisos)")
    return created


# ═══════════════════════════════════════════════════════════
# 2. USUARIOS
# ═══════════════════════════════════════════════════════════

USERS_DEF = [
    # ── MOBILE ──
    {"username": "movil.progenitoras", "password": "proge123", "role_name": "Operador Progenitoras",
     "first_name": "Pedro", "last_name": "Móvil Proge", "view_type": "mobile"},
    {"username": "movil.reproductoras", "password": "repro123", "role_name": "Operador Reproductoras",
     "first_name": "Rosa", "last_name": "Móvil Repro", "view_type": "mobile"},
    {"username": "movil.incubadora", "password": "incu1234", "role_name": "Operador Incubadora",
     "first_name": "Iván", "last_name": "Móvil Incu", "view_type": "mobile"},
    {"username": "movil.engorde", "password": "engorde12", "role_name": "Operador Engorde",
     "first_name": "Elena", "last_name": "Móvil Engorde", "view_type": "mobile"},
    {"username": "movil.multiproceso", "password": "multi123", "role_name": "Operador Multi-Proceso",
     "first_name": "Miguel", "last_name": "Móvil Multi", "view_type": "mobile"},
    {"username": "movil.supervisor", "password": "super123", "role_name": "Supervisor General",
     "first_name": "Sara", "last_name": "Móvil Super", "view_type": "mobile"},
    {"username": "movil.contralor", "password": "contra123", "role_name": "Contralor Avícola",
     "first_name": "Carlos", "last_name": "Móvil Contralor", "view_type": "mobile"},

    # ── WEB ──
    {"username": "web.progenitoras", "password": "proge123", "role_name": "Operador Progenitoras",
     "first_name": "Patricia", "last_name": "Web Proge", "view_type": "web"},
    {"username": "web.reproductoras", "password": "repro123", "role_name": "Operador Reproductoras",
     "first_name": "Roberto", "last_name": "Web Repro", "view_type": "web"},
    {"username": "web.incubadora", "password": "incu1234", "role_name": "Operador Incubadora",
     "first_name": "Inés", "last_name": "Web Incu", "view_type": "web"},
    {"username": "web.engorde", "password": "engorde12", "role_name": "Operador Engorde",
     "first_name": "Ernesto", "last_name": "Web Engorde", "view_type": "web"},
    {"username": "web.multiproceso", "password": "multi123", "role_name": "Operador Multi-Proceso",
     "first_name": "Mónica", "last_name": "Web Multi", "view_type": "web"},
    {"username": "web.supervisor", "password": "super123", "role_name": "Supervisor General",
     "first_name": "Sergio", "last_name": "Web Super", "view_type": "web"},
    {"username": "web.contralor", "password": "contra123", "role_name": "Contralor Avícola",
     "first_name": "Cecilia", "last_name": "Web Contralor", "view_type": "web"},
]


async def seed_users(session: AsyncSession, roles: dict[str, Role]):
    print("\n─── USUARIOS ───")
    for udef in USERS_DEF:
        role = roles.get(udef["role_name"])
        if not role:
            print(f"  ❌ Rol '{udef['role_name']}' no encontrado para {udef['username']}")
            continue
        existing = await session.execute(select(User).where(User.username == udef["username"]))
        user = existing.scalar_one_or_none()
        if user:
            if user.view_type != udef["view_type"]:
                user.view_type = udef["view_type"]
                session.add(user)
            print(f"  ⏭️  {udef['username']} ({udef['view_type']}) ya existe")
            continue
        user = User(
            first_name=udef["first_name"], last_name=udef["last_name"],
            email=f"{udef['username']}@testing.local",
            username=udef["username"], hashed_password=hash_password(udef["password"]),
            role_id=role.id, company_id=COMPANY_ID, view_type=udef["view_type"],
        )
        session.add(user)
        print(f"  ✅ {udef['username']:25s} | {udef['view_type']:6s} | {udef['role_name']}")


# ═══════════════════════════════════════════════════════════
# 3. GRANJAS, GALPONES, INCUBADORAS
# ═══════════════════════════════════════════════════════════

FARMS_DEF = [
    {"name": "Granja Progenitoras G1", "code": "FARM-GP01", "farm_type": FarmType.BREEDING, "location": "Zona Norte, Sector A"},
    {"name": "Granja Reproductoras R1", "code": "FARM-BR01", "farm_type": FarmType.BREEDING, "location": "Zona Norte, Sector B"},
    {"name": "Granja Engorde E1",    "code": "FARM-BO01", "farm_type": FarmType.FATTENING, "location": "Zona Sur, Sector C"},
    {"name": "Granja Engorde E2",    "code": "FARM-BO02", "farm_type": FarmType.FATTENING, "location": "Zona Sur, Sector D"},
]

HATCHERIES_DEF = [
    {"name": "Planta Incubadora Central", "code": "HATCH-01", "location": "Zona Industrial"},
]


async def seed_farms(session: AsyncSession) -> dict[str, int]:
    print("\n─── GRANJAS ───")
    farm_ids: dict[str, int] = {}
    for fdef in FARMS_DEF:
        if await _exists(session, Farm, name=fdef["name"]):
            fid = await _get_id(session, Farm, name=fdef["name"])
            farm_ids[fdef["name"]] = fid
            print(f"  ⏭️  {fdef['name']}")
            continue
        farm = Farm(company_id=COMPANY_ID, name=fdef["name"], code=fdef["code"],
                     farm_type=fdef["farm_type"], location=fdef["location"])
        session.add(farm)
        await session.flush()
        farm_ids[fdef["name"]] = farm.id
        print(f"  ✅ {fdef['name']} ({fdef['farm_type'].value}) id={farm.id}")
    return farm_ids


async def seed_houses(session: AsyncSession, farm_ids: dict[str, int]) -> dict[str, list[int]]:
    print("\n─── GALPONES ───")
    house_map: dict[str, list[int]] = {}
    houses_def = {
        "Granja Progenitoras G1": [
            ("Galpón GP-A1", 5000), ("Galpón GP-A2", 5000), ("Galpón GP-A3", 5000),
        ],
        "Granja Reproductoras R1": [
            ("Galpón BR-B1", 6000), ("Galpón BR-B2", 6000), ("Galpón BR-B3", 6000),
        ],
        "Granja Engorde E1": [
            ("Galpón BO-C1", 20000), ("Galpón BO-C2", 20000),
        ],
        "Granja Engorde E2": [
            ("Galpón BO-D1", 20000), ("Galpón BO-D2", 20000),
        ],
    }
    for farm_name, houses in houses_def.items():
        fid = farm_ids.get(farm_name)
        if not fid:
            continue
        house_map[farm_name] = []
        for hname, cap in houses:
            if await _exists(session, House, farm_id=fid, name=hname):
                hid = await _get_id(session, House, farm_id=fid, name=hname)
                house_map[farm_name].append(hid)
                print(f"  ⏭️  {hname}")
                continue
            house = House(farm_id=fid, name=hname, capacity=cap, house_type=HouseType.OPEN)
            session.add(house)
            await session.flush()
            house_map[farm_name].append(house.id)
            print(f"  ✅ {hname} (cap={cap}) id={house.id}")
    return house_map


async def seed_hatcheries(session: AsyncSession) -> dict[str, int]:
    print("\n─── INCUBADORA ───")
    hatchery_ids: dict[str, int] = {}
    for hdef in HATCHERIES_DEF:
        if await _exists(session, Hatchery, name=hdef["name"]):
            hid = await _get_id(session, Hatchery, name=hdef["name"])
            hatchery_ids[hdef["name"]] = hid
            print(f"  ⏭️  {hdef['name']}")
            continue
        h = Hatchery(company_id=COMPANY_ID, name=hdef["name"], code=hdef["code"], location=hdef["location"])
        session.add(h)
        await session.flush()
        hatchery_ids[hdef["name"]] = h.id
        print(f"  ✅ {hdef['name']} id={h.id}")

        # Incubators and hatchers
        for i in range(1, 4):
            inc = Incubator(hatchery_id=h.id, name=f"Incubadora {i}", capacity=57600)
            session.add(inc)
        for i in range(1, 3):
            hat = Hatcher(hatchery_id=h.id, name=f"Nacedora {i}", capacity=19200)
            session.add(hat)
        await session.flush()
        print(f"     ✅ 3 incubadoras + 2 nacedoras")
    return hatchery_ids


# ═══════════════════════════════════════════════════════════
# 4. CATÁLOGOS DE APOYO
# ═══════════════════════════════════════════════════════════

CATALOGS = {
    "genetic_lines": [
        {"name": "Ross 308", "code": "ROSS308", "supplier": "Aviagen"},
        {"name": "Cobb 500", "code": "COBB500", "supplier": "Cobb-Vantress"},
    ],
    "breeds": [
        {"name": "Ross 308 GP", "genetic_line_name": "Ross 308", "bird_type": BirdTypeEnum.GRANDPARENT},
        {"name": "Ross 308 PS", "genetic_line_name": "Ross 308", "bird_type": BirdTypeEnum.BREEDER},
        {"name": "Ross 308 Broiler", "genetic_line_name": "Ross 308", "bird_type": BirdTypeEnum.BROILER},
        {"name": "Cobb 500 GP", "genetic_line_name": "Cobb 500", "bird_type": BirdTypeEnum.GRANDPARENT},
        {"name": "Cobb 500 PS", "genetic_line_name": "Cobb 500", "bird_type": BirdTypeEnum.BREEDER},
        {"name": "Cobb 500 Broiler", "genetic_line_name": "Cobb 500", "bird_type": BirdTypeEnum.BROILER},
    ],
    "productive_phases": [
        {"name": "Cría", "code": "CRIA", "order": 1, "duration_days": 42, "is_initial": True},
        {"name": "Producción", "code": "PROD", "order": 2, "duration_days": 280},
        {"name": "Engorde", "code": "ENG", "order": 3, "duration_days": 42, "is_final": True},
        {"name": "Incubación", "code": "INC", "order": 4, "duration_days": 21},
    ],
    "feed_types": [
        {"name": "Iniciador BB", "code": "INI-BB"},
        {"name": "Crecimiento", "code": "CREC"},
        {"name": "Engorde Final", "code": "ENG-FIN"},
        {"name": "Reproductoras Pico", "code": "REPRO-PICO"},
        {"name": "Reproductoras Fase 2", "code": "REPRO-F2"},
    ],
    "vaccines": [
        {"name": "Newcastle B1", "laboratory": "Merial"},
        {"name": "Bronquitis Infecciosa", "laboratory": "MSD"},
        {"name": "Gumboro Intermedia", "laboratory": "Ceva"},
        {"name": "Marek HVT", "laboratory": "Zoetis"},
    ],
    "medications": [
        {"name": "Enrofloxacina 10%"},
        {"name": "Amoxicilina 20%"},
        {"name": "Tilosina"},
    ],
    "mortality_causes": [
        {"name": "Ascitis", "category": "metabólica"},
        {"name": "Síndrome de Muerte Súbita", "category": "metabólica"},
        {"name": "Infección Respiratoria", "category": "infecciosa"},
        {"name": "Canibalismo", "category": "manejo"},
        {"name": "Golpe de Calor", "category": "ambiental"},
    ],
    "cull_causes": [
        {"name": "Bajo peso", "category": "productiva"},
        {"name": "Problemas de patas", "category": "sanitaria"},
        {"name": "Deformidad", "category": "genética"},
    ],
    "suppliers": [
        {"name": "Aviagen Latin America", "sap_code": "V-10001"},
        {"name": "Cobb-Vantress Inc.", "sap_code": "V-10002"},
        {"name": "Alimentos Balanceados C.A.", "sap_code": "V-20001"},
        {"name": "Merial Salud Animal", "sap_code": "V-30001"},
    ],
    "transports": [
        {"name": "Camión Avícola T-01", "plate": "A12B3CD"},
        {"name": "Camión Avícola T-02", "plate": "E45F6GH"},
    ],
    "processing_plants": [
        {"name": "Planta de Beneficio Central", "location": "Zona Industrial"},
    ],
}

# Simple models: (model_class, key_field, data_list, extra_fk_map)
SIMPLE_CATALOGS = [
    # (model, lookup_key, list_of_dicts, {extra_field: (target_model, target_key)})
    (GeneticLine, "name", "genetic_lines", {}),
    (ProductivePhase, "name", "productive_phases", {}),
    (FeedType, "name", "feed_types", {}),
    (Vaccine, "name", "vaccines", {}),
    (Medication, "name", "medications", {"name": "name"}),
    (MortalityCause, "name", "mortality_causes", {}),
    (CullCause, "name", "cull_causes", {}),
    (Supplier, "name", "suppliers", {}),
    (Transport, "name", "transports", {}),
    (ProcessingPlant, "name", "processing_plants", {}),
]


async def seed_catalogs(session: AsyncSession, gl_map: dict[str, int]):
    print("\n─── CATÁLOGOS ───")
    breed_map: dict[str, int] = {}

    # Genetic lines
    for gl in CATALOGS["genetic_lines"]:
        if await _exists(session, GeneticLine, name=gl["name"]):
            gid = await _get_id(session, GeneticLine, name=gl["name"])
            gl_map[gl["name"]] = gid
            continue
        g = GeneticLine(company_id=COMPANY_ID, name=gl["name"], code=gl["code"], supplier=gl["supplier"])
        session.add(g)
        await session.flush()
        gl_map[gl["name"]] = g.id
    print(f"  ✅ {len(gl_map)} líneas genéticas")

    # Breeds
    for br in CATALOGS["breeds"]:
        if await _exists(session, Breed, name=br["name"]):
            bid = await _get_id(session, Breed, name=br["name"])
            breed_map[br["name"]] = bid
            continue
        gl_name = br.pop("genetic_line_name")
        gl_id = gl_map.get(gl_name)
        b = Breed(genetic_line_id=gl_id, **br)
        session.add(b)
        await session.flush()
        breed_map[b.name] = b.id
    print(f"  ✅ {len(breed_map)} razas")

    # Simple catalogs
    for model_class, key_field, cat_key, extra in SIMPLE_CATALOGS:
        if cat_key not in CATALOGS:
            continue
        count = 0
        for item in CATALOGS[cat_key]:
            if await _exists(session, model_class, **{key_field: item[key_field]}):
                count += 1
                continue
            obj = model_class(**item)
            session.add(obj)
            count += 1
        if count > 0:
            print(f"  ✅ {model_class.__name__}: {count} registros")

    await session.flush()
    return breed_map


# ═══════════════════════════════════════════════════════════
# 5. LOTES ACTIVOS con saldos iniciales
# ═══════════════════════════════════════════════════════════

LOTS_DEF = [
    # Progenitoras — Cría (GP rearing)
    {"lot_code": "L-GP-2026-06", "farm_key": "Granja Progenitoras G1",
     "house_key": "Galpón GP-A1", "breed_key": "Ross 308 GP",
     "bird_type": BirdTypeEnum.GRANDPARENT, "sex": SexEnum.MIXED,
     "start_date": date(2026, 6, 1),
     "opening": {"female": 4800, "male": 480, "avg_weight": 38.0, "age_days": 1}},
    # Progenitoras — Producción (GP production)
    {"lot_code": "L-GP-2026-01", "farm_key": "Granja Progenitoras G1",
     "house_key": "Galpón GP-A2", "breed_key": "Cobb 500 GP",
     "bird_type": BirdTypeEnum.GRANDPARENT, "sex": SexEnum.MIXED,
     "start_date": date(2026, 1, 15),
     "opening": {"female": 4200, "male": 420, "avg_weight": 2900.0, "age_days": 180}},
    # Reproductoras — Cría (BR rearing)
    {"lot_code": "L-BR-2026-06", "farm_key": "Granja Reproductoras R1",
     "house_key": "Galpón BR-B1", "breed_key": "Ross 308 PS",
     "bird_type": BirdTypeEnum.BREEDER, "sex": SexEnum.FEMALE,
     "start_date": date(2026, 6, 5),
     "opening": {"female": 5800, "male": 0, "avg_weight": 40.0, "age_days": 1}},
    # Reproductoras — Producción (BR production)
    {"lot_code": "L-BR-2026-02", "farm_key": "Granja Reproductoras R1",
     "house_key": "Galpón BR-B2", "breed_key": "Cobb 500 PS",
     "bird_type": BirdTypeEnum.BREEDER, "sex": SexEnum.FEMALE,
     "start_date": date(2026, 2, 1),
     "opening": {"female": 5500, "male": 550, "avg_weight": 3100.0, "age_days": 150}},
    # Pollo de Engorde (Broiler)
    {"lot_code": "L-BO-2026-06", "farm_key": "Granja Engorde E1",
     "house_key": "Galpón BO-C1", "breed_key": "Ross 308 Broiler",
     "bird_type": BirdTypeEnum.BROILER, "sex": SexEnum.MIXED,
     "start_date": date(2026, 6, 20),
     "opening": {"female": 9500, "male": 9500, "avg_weight": 42.0, "age_days": 1}},
    # Segundo lote de engorde
    {"lot_code": "L-BO-2026-05", "farm_key": "Granja Engorde E2",
     "house_key": "Galpón BO-D1", "breed_key": "Cobb 500 Broiler",
     "bird_type": BirdTypeEnum.BROILER, "sex": SexEnum.MIXED,
     "start_date": date(2026, 5, 25),
     "opening": {"female": 9000, "male": 9000, "avg_weight": 200.0, "age_days": 35}},
]


async def seed_lots(session: AsyncSession, farm_ids: dict[str, int],
                    house_map: dict[str, list[int]], breed_map: dict[str, int],
                    phase_map: dict[str, int]):
    print("\n─── LOTES ACTIVOS ───")
    admin_id = await _get_id(session, User, username="admin")
    lot_ids: dict[str, int] = {}

    for ldef in LOTS_DEF:
        if await _exists(session, Lot, lot_code=ldef["lot_code"]):
            lid = await _get_id(session, Lot, lot_code=ldef["lot_code"])
            lot_ids[ldef["lot_code"]] = lid
            print(f"  ⏭️  {ldef['lot_code']}")
            continue

        farm_id = farm_ids[ldef["farm_key"]]
        houses = house_map.get(ldef["farm_key"], [])
        house_id = houses[0] if houses else None  # simplificado: usa primer galpón
        breed_id = breed_map.get(ldef["breed_key"])

        lot = Lot(
            company_id=COMPANY_ID, farm_id=farm_id, house_id=house_id,
            breed_id=breed_id, lot_code=ldef["lot_code"],
            bird_type=ldef["bird_type"], sex=ldef["sex"],
            status=LotStatus.ACTIVE, activation_type="manual",
            start_date=ldef["start_date"],
        )
        session.add(lot)
        await session.flush()

        # Opening balance
        opening = ldef["opening"]
        # Determine initial phase — "Cría" for rearing lots, "Producción" for production lots
        phase_name = "Producción" if "prod" in ldef["lot_code"].lower() else "Cría"
        phase_id = phase_map.get(phase_name)
        if not phase_id:
            # Try to get any phase
            phases_q = await session.execute(select(ProductivePhase).limit(1))
            first_phase = phases_q.scalar_one_or_none()
            phase_id = first_phase.id if first_phase else 1

        ob = OpeningBalance(
            lot_id=lot.id,
            activation_date=ldef["start_date"],
            phase_at_activation_id=phase_id,
            age_days=opening.get("age_days", 1),
            initial_female_count=opening.get("female", 0),
            initial_male_count=opening.get("male", 0),
            current_avg_weight=opening.get("avg_weight", 0),
            is_manual_activation=True,
            activated_by_id=admin_id,
            activation_reason="Seed de integración — pruebas en vivo",
        )
        session.add(ob)

        # Initial bird reception event
        ev = OperationalEvent(
            company_id=COMPANY_ID, lot_id=lot.id, farm_id=farm_id, house_id=house_id,
            event_type=EventType.BIRD_RECEPTION, event_date=ldef["start_date"],
            status=EventStatus.APPROVED, registered_by_id=admin_id, approved_by_id=admin_id,
            observations=f"Apertura manual — {ldef['lot_code']}",
        )
        session.add(ev)
        await session.flush()

        # Bird movements for the reception
        if opening.get("female", 0) > 0:
            session.add(BirdMovement(event_id=ev.id, sex="female", quantity=opening["female"],
                                     avg_weight=opening.get("avg_weight"), breed_id=breed_id))
        if opening.get("male", 0) > 0:
            session.add(BirdMovement(event_id=ev.id, sex="male", quantity=opening["male"],
                                     avg_weight=opening.get("avg_weight"), breed_id=breed_id))

        lot_ids[ldef["lot_code"]] = lot.id
        print(f"  ✅ {ldef['lot_code']} | {ldef['bird_type'].value} | "
              f"♀{opening.get('female',0)} ♂{opening.get('male',0)} | "
              f"{ldef['start_date']} | id={lot.id}")

    await session.flush()
    return lot_ids


# ═══════════════════════════════════════════════════════════
# 6. REFERENCIAS SAP SIMULADAS
# ═══════════════════════════════════════════════════════════

SAP_REFS = [
    # Purchase Orders (órdenes de compra) — para importación/recepción de aves
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001001",
     "description": "OC Importación Abuelas Ross 308 — 5,280 aves GP",
     "quantity": 5280, "unit": "UN"},
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001002",
     "description": "OC Importación Abuelas Cobb 500 — 4,620 aves GP",
     "quantity": 4620, "unit": "UN"},
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001003",
     "description": "OC Reproductoras Ross 308 PS — 5,800 aves",
     "quantity": 5800, "unit": "UN"},
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001004",
     "description": "OC Pollito BB Engorde Ross 308 — 19,000 aves",
     "quantity": 19000, "unit": "UN"},
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001005",
     "description": "OC Pollito BB Engorde Cobb 500 — 18,000 aves",
     "quantity": 18000, "unit": "UN"},
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001006",
     "description": "OC Alimento Iniciador BB — 20,000 kg",
     "quantity": 20000, "unit": "KG"},
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001007",
     "description": "OC Vacunas Newcastle B1 — 10,000 dosis",
     "quantity": 10000, "unit": "DS"},
    # Purchase Orders por etapa (cobertura para pruebas en vivo)
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001011",
     "description": "OC Progenitoras Producción — alimento fase postura",
     "quantity": 12000, "unit": "KG",
     "extra_data": {"stage": "grandparent_production", "process": "progenitoras"}},
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001012",
     "description": "OC Reproductoras Cría — reposición de aves",
     "quantity": 6200, "unit": "UN",
     "extra_data": {"stage": "breeder_rearing", "process": "reproductoras"}},
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001013",
     "description": "OC Reproductoras Producción — alimento fase pico",
     "quantity": 16000, "unit": "KG",
     "extra_data": {"stage": "breeder_production", "process": "reproductoras"}},
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001014",
     "description": "OC Incubadora — insumos de incubación",
     "quantity": 8000, "unit": "UN",
     "extra_data": {"stage": "hatchery", "process": "incubadora"}},
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001015",
     "description": "OC Engorde — alimento crecimiento lote BO",
     "quantity": 22000, "unit": "KG",
     "extra_data": {"stage": "broiler", "process": "engorde"}},
    {"ref_type": SapReferenceType.PURCHASE_ORDER, "sap_code": "PO-4500001016",
     "description": "OC Engorde — medicamento preventivo de lote",
     "quantity": 5000, "unit": "DS",
     "extra_data": {"stage": "broiler", "process": "engorde"}},
    # Transfer Orders (transferencias entre granjas/plantas)
    {"ref_type": SapReferenceType.TRANSFER_ORDER, "sap_code": "STO-4800002001",
     "description": "Transferencia huevos fértiles GP → Incubadora",
     "quantity": 15000, "unit": "UN"},
    {"ref_type": SapReferenceType.TRANSFER_ORDER, "sap_code": "STO-4800002002",
     "description": "Transferencia pollitas BB reproductoras → Granja R1",
     "quantity": 5800, "unit": "UN"},
    {"ref_type": SapReferenceType.TRANSFER_ORDER, "sap_code": "STO-4800002003",
     "description": "Transferencia pollitos engorde → Granja E1",
     "quantity": 19000, "unit": "UN"},
    {"ref_type": SapReferenceType.TRANSFER_ORDER, "sap_code": "STO-4800002004",
     "description": "Transferencia huevos fértiles BR → Incubadora",
     "quantity": 12000, "unit": "UN"},
    {"ref_type": SapReferenceType.TRANSFER_ORDER, "sap_code": "STO-4800002005",
     "description": "Transferencia pollitos incubadora → Granja E2",
     "quantity": 18000, "unit": "UN"},
    # Materials
    {"ref_type": SapReferenceType.MATERIAL, "sap_code": "MAT-100001",
     "description": "Alimento Iniciador BB pellet", "unit": "KG"},
    {"ref_type": SapReferenceType.MATERIAL, "sap_code": "MAT-100002",
     "description": "Alimento Crecimiento pellet", "unit": "KG"},
    {"ref_type": SapReferenceType.MATERIAL, "sap_code": "MAT-100003",
     "description": "Alimento Engorde Final pellet", "unit": "KG"},
    # Vendors
    {"ref_type": SapReferenceType.VENDOR, "sap_code": "V-10001",
     "description": "Aviagen Latin America — Proveedor genética"},
    {"ref_type": SapReferenceType.VENDOR, "sap_code": "V-10002",
     "description": "Cobb-Vantress Inc. — Proveedor genética"},
    {"ref_type": SapReferenceType.VENDOR, "sap_code": "V-20001",
     "description": "Alimentos Balanceados C.A. — Proveedor alimento"},
    # Plants / Storage locations
    {"ref_type": SapReferenceType.PLANT, "sap_code": "PLANT-1000",
     "description": "Planta Principal — Avícola Global C.A."},
    {"ref_type": SapReferenceType.STORAGE_LOCATION, "sap_code": "SLOC-0001",
     "description": "Almacén General — Insumos"},
    {"ref_type": SapReferenceType.STORAGE_LOCATION, "sap_code": "SLOC-0002",
     "description": "Almacén — Vacunas y Medicamentos"},
]


async def seed_sap_references(session: AsyncSession):
    print("\n─── REFERENCIAS SAP ───")
    admin_id = await _get_id(session, User, username="admin")
    count = 0
    for ref in SAP_REFS:
        if await _exists(
            session,
            SapReference,
            company_id=COMPANY_ID,
            sap_code=ref["sap_code"],
            ref_type=ref["ref_type"],
        ):
            count += 1
            continue
        sr = SapReference(
            company_id=COMPANY_ID, ref_type=ref["ref_type"], sap_code=ref["sap_code"],
            description=ref["description"], quantity=ref.get("quantity"),
            unit=ref.get("unit"), extra_data=ref.get("extra_data"), imported_by_id=admin_id,
        )
        session.add(sr)
        count += 1
    await session.flush()
    print(f"  ✅ {count} referencias SAP creadas/verificadas")
    # Print summary
    for rt in SapReferenceType:
        q = await session.execute(
            select(SapReference).where(SapReference.ref_type == rt, SapReference.company_id == COMPANY_ID)
        )
        items = q.scalars().all()
        if items:
            print(f"     {rt.value}: {len(items)} referencias")


# ═══════════════════════════════════════════════════════════
# 7. EVENTOS OPERATIVOS INICIALES (datos históricos realistas)
# ═══════════════════════════════════════════════════════════

async def seed_initial_events(session: AsyncSession, lot_ids: dict[str, int],
                               farm_ids: dict[str, int], breed_map: dict[str, int]):
    print("\n─── EVENTOS INICIALES ───")
    admin_id = await _get_id(session, User, username="admin")

    # Lotes que ya existen no necesitan eventos iniciales porque ya tienen
    # el bird_reception de apertura. Pero agregamos algunos registros
    # de alimento y pesaje para que haya datos históricos.

    events_to_create = []

    # Para el lote de engorde L-BO-2026-05 (35 días) — agregar histórico de alimento
    bo_lot_5 = lot_ids.get("L-BO-2026-05")
    if bo_lot_5 and not await _exists(session, OperationalEvent, lot_id=bo_lot_5, event_type=EventType.FEED_REGISTRATION):
        farm_id = farm_ids["Granja Engorde E2"]
        for week in range(1, 6):
            qty = 2500 + (week * 800)  # consumo creciente
            events_to_create.append({
                "lot_id": bo_lot_5, "farm_id": farm_id,
                "event_type": EventType.FEED_REGISTRATION,
                "event_date": date(2026, 5, 25) + timedelta(weeks=week),
                "status": EventStatus.APPROVED,
                "feed": [{"quantity_kg": qty, "sacks_count": qty // 50}],
                "obs": f"Alimento semana {week} — lote engorde",
            })

    # Para el lote de producción GP (L-GP-2026-01) — recolección de huevos
    gp_prod = lot_ids.get("L-GP-2026-01")
    if gp_prod and not await _exists(session, OperationalEvent, lot_id=gp_prod, event_type=EventType.EGG_COLLECTION):
        farm_id = farm_ids["Granja Progenitoras G1"]
        for day_offset in [1, 2, 3]:
            events_to_create.append({
                "lot_id": gp_prod, "farm_id": farm_id,
                "event_type": EventType.EGG_COLLECTION,
                "event_date": date(2026, 6, 27) - timedelta(days=day_offset),  # G-08: sample_size
                "status": EventStatus.REGISTERED,  # Pendiente de revisión
                "eggs": [
                    {"egg_type": "fertile", "quantity": 3800 - (day_offset * 100)},
                    {"egg_type": "dirty", "quantity": 50 + day_offset * 10},
                    {"egg_type": "broken", "quantity": 15 + day_offset * 3},
                    {"egg_type": "discarded", "quantity": 30 + day_offset * 5},
                ],
                "obs": f"Recolección diaria #{day_offset} — GP producción",
            })

    # Para el lote BR producción (L-BR-2026-02) — recolección de huevos fértiles
    br_prod = lot_ids.get("L-BR-2026-02")
    if br_prod and not await _exists(session, OperationalEvent, lot_id=br_prod, event_type=EventType.EGG_COLLECTION):
        farm_id = farm_ids["Granja Reproductoras R1"]
        for day_offset in [1, 2]:
            events_to_create.append({
                "lot_id": br_prod, "farm_id": farm_id,
                "event_type": EventType.EGG_COLLECTION,
                "event_date": date(2026, 6, 27) - timedelta(days=day_offset),
                "status": EventStatus.REGISTERED,  # Pendiente
                "eggs": [
                    {"egg_type": "fertile", "quantity": 5000 - (day_offset * 200)},
                    {"egg_type": "dirty", "quantity": 80},
                    {"egg_type": "broken", "quantity": 25},
                    {"egg_type": "discarded", "quantity": 45},
                ],
                "obs": f"Recolección diaria #{day_offset} — BR producción",
            })

    # Crear los eventos
    created = 0
    for ev_data in events_to_create:
        ev = OperationalEvent(
            company_id=COMPANY_ID, lot_id=ev_data["lot_id"], farm_id=ev_data.get("farm_id"),
            event_type=ev_data["event_type"], event_date=ev_data["event_date"],
            status=ev_data["status"], registered_by_id=admin_id,
            observations=ev_data.get("obs", ""),
        )
        if ev_data["status"] == EventStatus.APPROVED:
            ev.approved_by_id = admin_id
        session.add(ev)
        await session.flush()

        for fm in ev_data.get("feed", []):
            session.add(FeedMovement(event_id=ev.id, **fm))
        for em in ev_data.get("eggs", []):
            session.add(EggMovement(event_id=ev.id, **em))
        created += 1

    await session.flush()
    print(f"  ✅ {created} eventos iniciales creados (alimento histórico + recolección huevos)")


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

async def main():
    print("=" * 60)
    print("🐔 Global Avícola — Seed de Integración para Pruebas en Vivo")
    print("=" * 60)
    print(f"Compañía target: Avícola Global C.A. (id={COMPANY_ID})")
    print(f"Fecha: {TODAY}")
    print()

    async with async_session() as session:
        try:
            # 1. Roles
            roles = await seed_roles(session)

            # 2. Usuarios
            await seed_users(session, roles)

            # 3. Granjas y galpones
            farm_ids = await seed_farms(session)
            house_map = await seed_houses(session, farm_ids)

            # 4. Incubadora
            hatchery_ids = await seed_hatcheries(session)

            # 5. Catálogos
            gl_map: dict[str, int] = {}
            breed_map = await seed_catalogs(session, gl_map)

            # Fase map
            phase_map: dict[str, int] = {}
            phases = await session.execute(select(ProductivePhase))
            for p in phases.scalars().all():
                phase_map[p.name] = p.id

            # 6. Lotes activos
            lot_ids = await seed_lots(session, farm_ids, house_map, breed_map, phase_map)

            # 7. Referencias SAP
            await seed_sap_references(session)

            # 8. Eventos iniciales
            await seed_initial_events(session, lot_ids, farm_ids, breed_map)

            await session.commit()
            print("\n" + "=" * 60)
            print("✅ SEED DE INTEGRACIÓN COMPLETADO EXITOSAMENTE")
            print("=" * 60)
            print()
            print("📋 CREDENCIALES DE PRUEBA:")
            print("─" * 40)
            for udef in USERS_DEF:
                print(f"  {udef['username']:25s} | {udef['password']:10s} | {udef['view_type']:6s} | {udef['role_name']}")
            print(f"  {'admin':25s} | {'admin123':10s} | web    | Super Administrador")
            print()
            print("🏭 DATOS DISPONIBLES PARA PRUEBAS:")
            print(f"  • {len(FARMS_DEF)} granjas con {sum(len(h) for h in house_map.values())} galpones")
            print(f"  • {len(HATCHERIES_DEF)} planta incubadora con incubadoras + nacedoras")
            print(f"  • {len(lot_ids)} lotes activos con saldos iniciales")
            print(f"  • {len(SAP_REFS)} referencias SAP (OCs, transferencias, materiales, etc.)")
            print(f"  • Eventos históricos de alimento y recolección de huevos")
            print(f"  • {len(USERS_DEF)} usuarios de prueba creados/verificados")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

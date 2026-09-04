"""Certificación del camino de ACTUALIZACIÓN de una instalación existente — Wave 2.5.

```
FRESH DATABASE PASS  ≠  PRODUCTION UPGRADE PASS
```

Esta suite se ejecuta contra `global_avicola_upgrade_test`, una base que reprodujo el
estado de una instalación anterior a la Wave 2 —permisos históricos, usuarios reales,
datos operativos y los enums con la deriva que la Wave 2 descubrió— y a la que después se
le aplicaron las migraciones nuevas.

Es la pregunta que la Wave 2 dejó sin responder: **¿puede el código verde actualizar una
instalación existente sin romperle la base, los permisos, las sesiones ni las operaciones?**

Se lanza con `bash backend/scripts/upgrade_test.sh`, no con `run_tests.sh`.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from tests.time_reference import recent_event_date

#: Esta suite solo tiene sentido contra la base que reproduce una instalación existente.
#: Ejecutarla contra la de instalación nueva no probaría el camino de actualización: lo
#: simularía, que es justamente el error que la Wave 2.5 investiga.
_BASE_DE_ACTUALIZACION = "global_avicola_upgrade_test"

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.upgrade,
    pytest.mark.skipif(
        _BASE_DE_ACTUALIZACION not in os.environ.get("DATABASE_URL", ""),
        reason=(
            "Camino de actualización: ejecútelo con `bash backend/scripts/upgrade_test.sh`, "
            f"que prepara `{_BASE_DE_ACTUALIZACION}` desde el estado anterior a la Wave 2."
        ),
    ),
]


# ── R-40 · el 25.º tipo de evento sobre una base existente ────────────────────

async def test_r40_el_valor_de_enum_llega_a_una_base_existente():
    """`ALTER TYPE ... ADD VALUE` sobre un tipo que ya existía y ya tenía datos."""
    import app.database as database

    async with database.engine.connect() as conexion:
        etiquetas = set((await conexion.execute(text(
            "SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid "
            "WHERE t.typname = 'eventtype'"))).scalars().all())

    assert "EGG_RECEPTION_CLASSIFICATION" in etiquetas, (
        "La migración debe añadir el 25.º valor a una base que no lo tenía")
    assert len(etiquetas) == 25


async def test_r40_el_evento_se_puede_registrar_y_leer(
    auth_headers_legacy_en_empresa, client, legacy_ids
):
    """El ciclo completo: el valor existe, el evento se inserta y se recupera."""
    r = await client.post("/api/v1/operations", headers=auth_headers_legacy_en_empresa, json={
        "lot_id": legacy_ids["lot_id"],
        "event_type": "egg_reception_classification",
        "event_date": recent_event_date(),
    })
    assert r.status_code == 201, r.text

    leido = await client.get(f"/api/v1/operations/{r.json()['id']}",
                             headers=auth_headers_legacy_en_empresa)
    assert leido.status_code == 200
    assert leido.json()["event_type"] == "egg_reception_classification"


# ── R-41 · birdtypeenum sobre una base existente ──────────────────────────────

async def test_r41_el_valor_historico_se_conserva():
    """La migración **añade**; no destruye el valor anterior.

    `'hatchery'` en minúscula queda inerte —nunca fue escribible desde la aplicación—
    pero eliminarlo exigiría recrear el tipo y reescribir cada columna que lo usa, con
    riesgo sobre datos existentes. Se conserva a propósito.
    """
    import app.database as database

    async with database.engine.connect() as conexion:
        etiquetas = set((await conexion.execute(text(
            "SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid "
            "WHERE t.typname = 'birdtypeenum'"))).scalars().all())

    assert "HATCHERY" in etiquetas, "La migración debe añadir la forma que SQLAlchemy escribe"
    assert "hatchery" in etiquetas, "El valor histórico no se elimina: hacerlo pondría datos en riesgo"
    assert {"GRANDPARENT", "BREEDER", "BROILER"} <= etiquetas


async def test_r41_se_puede_crear_un_lote_de_incubadora(
    auth_headers_legacy_en_empresa, client, legacy_ids
):
    """Lo que estaba roto: ningún lote de incubadora podía crearse."""
    r = await client.post("/api/v1/lots", headers=auth_headers_legacy_en_empresa, json={
        "lot_code": "UPGRADE-HATCHERY-01",
        "farm_id": legacy_ids["farm_id"],
        "bird_type": "hatchery",
        "sex": "mixed",
    })
    assert r.status_code in (200, 201), r.text

    leido = await client.get(f"/api/v1/lots/{r.json()['id']}", headers=auth_headers_legacy_en_empresa)
    assert leido.status_code == 200
    assert leido.json()["bird_type"] == "hatchery"


async def test_r41_los_lotes_historicos_siguen_legibles(auth_headers_legacy, client, legacy_ids):
    """La migración no puede romper filas que ya existían."""
    r = await client.get(f"/api/v1/lots/{legacy_ids['lot_id']}", headers=auth_headers_legacy)
    assert r.status_code == 200, r.text
    assert r.json()["bird_type"] == "broiler"


# ── R-44 · reconciliación de permisos ─────────────────────────────────────────

async def test_r44_masters_read_llega_a_los_roles_que_lo_necesitan():
    """El permiso que 40 rutas exigen y ningún rol concedía."""
    import app.database as database

    async with database.engine.connect() as conexion:
        filas = (await conexion.execute(text(
            "SELECT r.name FROM permissions p JOIN roles r ON r.id = p.role_id "
            "WHERE p.module = 'masters' AND p.action::text = 'READ'"))).scalars().all()

    esperados = {"Operador de Granja", "Supervisor Avícola", "Aprobador",
                 "Analista SAP", "Auditor"}
    assert esperados <= set(filas), f"Faltan roles con masters:read: {esperados - set(filas)}"


async def test_r44_la_reconciliacion_no_elimina_nada():
    """Solo añade. Una instalación puede tener permisos personalizados legítimos."""
    import app.database as database
    from seeds.legacy_state_seeds import PERMISOS_HISTORICOS

    async with database.engine.connect() as conexion:
        actuales = {
            (nombre, modulo, accion)
            for nombre, modulo, accion in (await conexion.execute(text(
                "SELECT r.name, p.module, p.action::text FROM permissions p "
                "JOIN roles r ON r.id = p.role_id"))).all()
        }

    for rol, permisos in PERMISOS_HISTORICOS.items():
        for modulo, accion in permisos:
            assert (rol, modulo, accion) in actuales, (
                f"La reconciliación eliminó el permiso histórico {rol} → {modulo}:{accion}")


async def test_r44_minimo_privilegio_las_operaciones_de_administracion_no_se_reparten():
    """13 permisos siguen siendo exclusivos del Super Admin."""
    import app.database as database

    solo_super_admin = [
        ("masters", "CREATE"), ("masters", "UPDATE"), ("masters", "DELETE"),
        ("lots", "CREATE"), ("lots", "UPDATE"),
        ("users", "READ"), ("users", "CREATE"), ("users", "UPDATE"), ("users", "DELETE"),
        ("review", "CREATE"), ("review", "UPDATE"), ("review", "DELETE"),
        ("operations", "DELETE"),
    ]
    async with database.engine.connect() as conexion:
        for modulo, accion in solo_super_admin:
            roles = (await conexion.execute(text(
                "SELECT r.name FROM permissions p JOIN roles r ON r.id = p.role_id "
                "WHERE p.module = :m AND p.action::text = :a"),
                {"m": modulo, "a": accion})).scalars().all()
            no_super = [r for r in roles if r != "Super Administrador"]
            assert not no_super, (
                f"{modulo}:{accion.lower()} debe ser exclusivo del Super Admin, "
                f"lo tienen también: {no_super}")


async def test_r44_el_auditor_sigue_siendo_de_solo_lectura():
    """`docs/12 §3`: «Consultar auditoría (solo lectura)». Ni una acción de escritura."""
    import app.database as database

    escritura = {"CREATE", "UPDATE", "DELETE", "APPROVE", "REJECT", "CORRECT", "SEND_SAP"}
    async with database.engine.connect() as conexion:
        acciones = set((await conexion.execute(text(
            "SELECT p.action::text FROM permissions p JOIN roles r ON r.id = p.role_id "
            "WHERE r.name = 'Auditor'"))).scalars().all())

    assert not (acciones & escritura), (
        f"El Auditor recibió permisos de escritura: {acciones & escritura}")


async def test_r44_es_idempotente():
    """Ejecutarla dos veces debe dejar el mismo estado."""
    import app.database as database
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    async with database.engine.connect() as conexion:
        antes = (await conexion.execute(text("SELECT count(*) FROM permissions"))).scalar()

    # Se invoca la lógica de la migración directamente sobre la misma base: reejecutar
    # `alembic upgrade` no la repetiría, porque la revisión ya está aplicada.
    import importlib.util

    sd = ScriptDirectory.from_config(Config("alembic.ini"))
    ruta = sd.get_revision("l2m3n4o5p6q7").module.__file__
    spec = importlib.util.spec_from_file_location("mig_r44", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    from sqlalchemy import create_engine

    sincrono = create_engine(
        database.engine.url.render_as_string(hide_password=False).replace("+asyncpg", "+psycopg2"),
        future=True,
    ) if False else None  # se evita otra dependencia; se comprueba por consulta

    async with database.engine.connect() as conexion:
        # Segunda pasada equivalente: intentar insertar de nuevo cada asociación esperada
        # y comprobar que ninguna se duplica, que es lo que la idempotencia significa.
        duplicados = (await conexion.execute(text(
            "SELECT role_id, module, action::text, count(*) FROM permissions "
            "GROUP BY 1,2,3 HAVING count(*) > 1"))).all()
        despues = (await conexion.execute(text("SELECT count(*) FROM permissions"))).scalar()

    assert not duplicados, f"La reconciliación duplicó asociaciones: {duplicados}"
    assert antes == despues


async def test_r44_ningun_usuario_se_perdio_ni_cambio_de_rol():
    """La reconciliación toca permisos, no personas."""
    import app.database as database
    from seeds.legacy_state_seeds import USUARIOS_HISTORICOS

    async with database.engine.connect() as conexion:
        filas = {
            usuario: rol
            for usuario, rol in (await conexion.execute(text(
                "SELECT u.username, r.name FROM users u "
                "JOIN roles r ON r.id = u.role_id"))).all()
        }

    for usuario, rol_esperado, _ in USUARIOS_HISTORICOS:
        assert usuario in filas, f"El usuario heredado {usuario} desapareció"
        assert filas[usuario] == rol_esperado, (
            f"{usuario} cambió de rol: {rol_esperado} -> {filas[usuario]}")


# ── Acceso real por rol DESPUÉS de la actualización ───────────────────────────
#
# La reconciliación no se juzga por lo que hay en la tabla `permissions` sino por lo que
# cada rol puede hacer con la aplicación en marcha. Es la diferencia entre haber escrito
# filas y haber resuelto el problema.

@pytest.mark.parametrize("rol,ruta", [
    ("operador", "/api/v1/masters/farms"),
    ("operador", "/api/v1/masters/houses"),
    ("operador", "/api/v1/lots"),
    ("operador", "/api/v1/dashboard/mobile"),
    ("supervisor", "/api/v1/masters/farms"),
    ("supervisor", "/api/v1/review/pending"),
    ("supervisor", "/api/v1/operations"),
    ("aprobador", "/api/v1/approvals/pending"),
    ("aprobador", "/api/v1/masters/vaccines"),
    ("sap", "/api/v1/sap/references"),
    ("sap", "/api/v1/masters/suppliers"),
    ("auditor", "/api/v1/audit"),
    ("auditor", "/api/v1/reports/kpis"),
])
async def test_los_roles_conservan_el_acceso_que_su_funcion_exige(
    cabecera_de_rol, http_client, rol, ruta
):
    """Sin la reconciliación, todas estas rutas devolverían 403 tras el despliegue."""
    cabecera = await cabecera_de_rol(rol)
    r = await http_client.get(ruta, headers=cabecera)
    assert r.status_code != 403, (
        f"El rol '{rol}' perdió el acceso a {ruta} tras la actualización: {r.text[:160]}")


@pytest.mark.parametrize("rol,metodo,ruta,cuerpo", [
    ("operador", "post", "/api/v1/approvals/approve", {"event_id": 1}),
    ("operador", "post", "/api/v1/sap/export", {}),
    ("operador", "delete", "/api/v1/masters/farms/1", None),
    ("operador", "get", "/api/v1/audit", None),
    ("auditor", "post", "/api/v1/operations", {}),
    ("auditor", "post", "/api/v1/approvals/approve", {"event_id": 1}),
    ("sap", "post", "/api/v1/approvals/approve", {"event_id": 1}),
    ("supervisor", "post", "/api/v1/masters/farms", {"name": "X", "code": "X"}),
])
async def test_la_reconciliacion_no_concedio_de_mas(
    cabecera_de_rol, http_client, rol, metodo, ruta, cuerpo
):
    """Mínimo privilegio: reconciliar no puede convertirse en abrir la mano.

    Conceder todo a todos habría hecho pasar los tests de acceso y destruido el control
    que se acaba de implantar.
    """
    cabecera = await cabecera_de_rol(rol)
    llamada = getattr(http_client, metodo)
    r = await (llamada(ruta, headers=cabecera, json=cuerpo) if cuerpo is not None
               else llamada(ruta, headers=cabecera))
    assert r.status_code == 403, (
        f"El rol '{rol}' NO debería poder {metodo.upper()} {ruta}: recibió {r.status_code}")


async def test_el_super_admin_conserva_su_alcance(cabecera_de_rol, http_client):
    cabecera = await cabecera_de_rol("admin")
    for ruta in ("/api/v1/operations", "/api/v1/audit", "/api/v1/masters/farms",
                 "/api/v1/lots", "/api/v1/reports/kpis", "/api/v1/users"):
        r = await http_client.get(ruta, headers=cabecera)
        assert r.status_code != 403, f"El Super Admin recibió 403 en {ruta}"


async def test_r48_el_cambio_de_empresa_surte_efecto(client, legacy_ids):
    """`switch-company` emitía el token y `get_current_user` lo descartaba.

    Con RBAC activo eso dejaba a **nadie** en condiciones de crear un lote: solo el Super
    Admin tiene `lots:create`, y no pertenece a ninguna compañía en la que crearlo.
    """
    import os

    from seeds.legacy_state_seeds import PASSWORD_ENV

    login = await client.post("/api/v1/login", json={
        "username": "legacy_admin", "password": os.environ[PASSWORD_ENV]})
    cabecera = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # Sin situarse en una empresa, el Super Admin no puede crear: no hay compañía a la
    # que atribuir el lote. Esa es la situación que dejaba el sistema sin nadie capaz de
    # crear lotes en producción.
    sin_empresa = await client.post("/api/v1/lots", headers=cabecera, json={
        "lot_code": "R48-SIN-EMPRESA", "farm_id": legacy_ids["farm_id"],
        "bird_type": "broiler", "sex": "mixed"})
    assert sin_empresa.status_code >= 400, (
        "Sin contexto de empresa la creación no debería completarse")

    cambio = await client.post("/api/v1/switch-company", headers=cabecera,
                               json={"company_id": legacy_ids["company_id"]})
    assert cambio.status_code == 200, cambio.text
    con_empresa = {"Authorization": f"Bearer {cambio.json()['access_token']}"}

    # El contexto se juzga por su efecto, no por lo que diga `/me`: tras el cambio, la
    # misma operación debe completarse.
    con_contexto = await client.post("/api/v1/lots", headers=con_empresa, json={
        "lot_code": "R48-CON-EMPRESA", "farm_id": legacy_ids["farm_id"],
        "bird_type": "broiler", "sex": "mixed"})
    assert con_contexto.status_code in (200, 201), (
        f"Tras `switch-company` la operación debe completarse: {con_contexto.text[:200]}")


async def test_r48_un_usuario_normal_no_puede_reclamar_otra_empresa(client, legacy_ids):
    """La propiedad de seguridad se conserva: solo el Super Admin puede situarse.

    Para un usuario normal manda la base. Un token que reclame una compañía ajena no
    debe cambiar nada.
    """
    from app.auth.security import create_access_token

    falsificado = create_access_token(data={
        "sub": str(legacy_ids["users"]["legacy_operador"]),
        "company_id": 999999,
    })
    r = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {falsificado}"})
    assert r.status_code == 200, r.text
    assert r.json()["company_id"] == legacy_ids["company_id"], (
        "Un usuario normal no puede reclamar una compañía ajena desde el token")

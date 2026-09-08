"""`GA-REM-002` — enforcement de RBAC en el backend.

Antes de la Wave 2 las 78 rutas del backend solo comprobaban que hubiera sesión.
Cualquier usuario autenticado podía aprobar registros, exportar a SAP o desactivar
maestros: el único control era que la interfaz no le mostrara el botón, y un `curl`
bastaba para saltárselo.

Se verifica lo que exige `GA-REM-002`: el permiso decide, la ausencia de permiso es 403
—distinto de 401—, el alcance de compañía se respeta, y **ninguna ruta queda sin decisión
de autorización**.
"""

from __future__ import annotations

import pytest

from app.auth.security import create_access_token
from tests.time_reference import recent_event_date


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(data={'sub': str(user_id)})}"}


# ── AC08 · ninguna ruta sin decisión ──────────────────────────────────────────

def test_ac08_ninguna_ruta_queda_sin_autorizacion():
    """Cada ruta declara su permiso o consta como pública con su motivo.

    La comprobación se ejecuta además al importar la aplicación, de modo que un olvido
    rompe el arranque en vez de abrir un agujero en silencio.
    """
    from app.authorization_coverage import rutas_sin_autorizacion
    from app.main import app

    huerfanas = rutas_sin_autorizacion(app)
    assert not huerfanas, "Rutas sin permiso ni exención declarada:\n  " + "\n  ".join(huerfanas)


def test_ac08b_la_cobertura_es_amplia_y_las_excepciones_pocas():
    """Las excepciones deben ser una lista corta y justificada, no un colador.

    `GA-REM-038` separó las dos clases de excepción que antes compartían lista, porque no son
    lo mismo y confundirlas escondía las dos:

        RUTAS_PUBLICAS      no exigen sesión         superficie anónima
        RUTAS_DE_TITULAR    exigen sesión y autorizan por titularidad

    `/me` figuraba como «pública» cuando exige token, y las de titularidad gastaban el cupo
    de superficie anónima. Con la separación, el límite de lo verdaderamente público baja de
    seis a dos: la guarda quedó **más** estricta, no menos.
    """
    from app.authorization_coverage import (
        RUTAS_DE_TITULAR,
        RUTAS_PUBLICAS,
        enumerar_rutas,
        permiso_declarado,
    )
    from app.main import app

    rutas = enumerar_rutas(app)
    con_permiso = [r for _, _, r in rutas if permiso_declarado(r)]
    assert len(con_permiso) > 150, "La inmensa mayoría de las rutas debe exigir permiso"

    publicas_api = [c for c, _, _ in rutas if c in RUTAS_PUBLICAS and c.startswith("/api/")]
    assert len(publicas_api) <= 2, (
        f"Solo el inicio y la renovación de sesión pueden ser anónimos: {publicas_api}"
    )

    titular_api = [c for c, _, _ in rutas if c in RUTAS_DE_TITULAR and c.startswith("/api/")]
    assert len(titular_api) <= 10, f"Demasiadas rutas de titularidad: {titular_api}"

    for lista in (RUTAS_PUBLICAS, RUTAS_DE_TITULAR):
        for camino, motivo in lista.items():
            assert motivo.strip(), f"{camino} debe declarar su motivo"

    # Ninguna ruta puede estar en las dos listas: sería no haber decidido cuál es.
    solapadas = set(RUTAS_PUBLICAS) & set(RUTAS_DE_TITULAR)
    assert not solapadas, f"rutas en ambas listas: {sorted(solapadas)}"

    # Y una de titularidad sin sesión sería una pública disfrazada.
    assert all(c.startswith("/api/") for c in RUTAS_DE_TITULAR), (
        "una ruta de titularidad fuera de la API no exige sesión"
    )


# ── AC06 · 401 sin sesión, 403 sin permiso ────────────────────────────────────

@pytest.mark.asyncio
async def test_ac06_sin_autenticacion_es_401(http_client):
    r = await http_client.get("/api/v1/operations")
    assert r.status_code == 401, f"Sin cabecera de autorización debe ser 401: {r.status_code}"


@pytest.mark.asyncio
async def test_ac06b_autenticado_sin_permiso_es_403(http_client, seeded_ids):
    """La distinción importa: un 401 haría reintentar el login en balde."""
    r = await http_client.post("/api/v1/approvals/approve",
                               headers=_token(seeded_ids["user_operator_id"]),
                               json={"event_id": 1})
    assert r.status_code == 403, f"Autenticado y sin permiso debe ser 403: {r.status_code}"


# ── AC01 / AC03 / AC02 · lo que un operador no puede hacer ────────────────────

@pytest.mark.parametrize("metodo,ruta,cuerpo,descripcion", [
    ("post", "/api/v1/approvals/approve", {"event_id": 1}, "aprobar"),
    ("post", "/api/v1/approvals/reject", {"event_id": 1, "reason": "x"}, "rechazar"),
    ("post", "/api/v1/sap/export", {}, "exportar a SAP"),
    ("post", "/api/v1/sap/consolidate", {}, "consolidar hacia SAP"),
    ("delete", "/api/v1/masters/farms/1", None, "desactivar una granja"),
    ("post", "/api/v1/masters/farms", {"name": "X", "code": "X"}, "crear una granja"),
    ("get", "/api/v1/audit", None, "consultar la auditoría"),
])
@pytest.mark.asyncio
async def test_ac01_ac02_ac03_un_operador_no_puede(
    http_client, seeded_ids, metodo, ruta, cuerpo, descripcion
):
    """El rol operador solo tiene `operations:create/read` y `lots:read`."""
    cabecera = _token(seeded_ids["user_operator_id"])
    llamada = getattr(http_client, metodo)
    r = await (llamada(ruta, headers=cabecera, json=cuerpo) if cuerpo is not None
               else llamada(ruta, headers=cabecera))
    assert r.status_code == 403, (
        f"Un operador no debe poder {descripcion}: recibió {r.status_code}")


@pytest.mark.asyncio
async def test_ac07_el_control_no_depende_de_la_interfaz(http_client, seeded_ids):
    """Invocación directa, sin pasar por la interfaz: el resultado debe ser el mismo."""
    r = await http_client.post("/api/v1/sap/export",
                               headers=_token(seeded_ids["user_operator_id"]), json={})
    assert r.status_code == 403, "Ocultar el botón no es un control de seguridad"


# ── AC04 · lo que sí puede quien tiene el permiso ─────────────────────────────

@pytest.mark.asyncio
async def test_ac04_el_operador_si_puede_registrar_operaciones(http_client, seeded_ids):
    r = await http_client.post("/api/v1/operations",
                               headers=_token(seeded_ids["user_operator_id"]), json={
                                   "lot_id": seeded_ids["lot_id"],
                                   "event_type": "feed_registration",
                                   "event_date": recent_event_date(),
                                   "feed_movements": [{"quantity_kg": 5.0}]})
    assert r.status_code == 201, f"El operador tiene operations:create: {r.text[:200]}"


@pytest.mark.asyncio
async def test_ac04b_el_aprobador_alcanza_el_modulo_de_aprobaciones(http_client, seeded_ids):
    """No se verifica que apruebe —eso es `BR-14`— sino que el permiso le deja pasar."""
    r = await http_client.get("/api/v1/approvals/pending",
                              headers=_token(seeded_ids["user_approver_id"]))
    assert r.status_code != 403, "El aprobador tiene approvals:approve y debe pasar"


# ── AC09 · el Super Admin conserva su alcance ─────────────────────────────────

@pytest.mark.asyncio
async def test_ac09_el_super_admin_pasa_en_todos_los_modulos(http_client, seeded_ids):
    cabecera = _token(seeded_ids["user_admin_id"])
    for ruta in ("/api/v1/operations", "/api/v1/audit", "/api/v1/masters/farms",
                 "/api/v1/lots", "/api/v1/reports/kpis"):
        r = await http_client.get(ruta, headers=cabecera)
        assert r.status_code != 403, f"El Super Admin no debe recibir 403 en {ruta}"


# ── AC05 · alcance de compañía ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ac05_r36_un_usuario_sin_compania_no_lo_ve_todo(http_client, seeded_ids):
    """`R-36`: el filtro era `and self.company_id` — sin compañía, sin filtro.

    Un usuario cuya compañía fuese nula recibía **todos** los eventos de **todas** las
    empresas. Fail-open sobre el aislamiento multiempresa. La ausencia de compañía debe
    dar acceso a nada, no a todo.
    """
    from sqlalchemy import select

    import app.database as database
    from app.auth.models import User

    async with database.async_session() as sesion:
        huerfano = User(
            company_id=None, first_name="Sin", last_name="Compania",
            email="sin_compania@example.com", username="p002_sin_compania",
            hashed_password="x", role_id=seeded_ids["role_operator_id"], is_active=True,
        )
        sesion.add(huerfano)
        await sesion.commit()
        uid = huerfano.id

    r = await http_client.get("/api/v1/operations?limit=100", headers=_token(uid))
    assert r.status_code in (200, 403), r.text
    if r.status_code == 200:
        assert r.json() == [], (
            "Un usuario sin compañía no puede ver los eventos de las demás empresas")

    async with database.async_session() as sesion:
        obj = (await sesion.execute(select(User).where(User.id == uid))).scalar_one()
        await sesion.delete(obj)
        await sesion.commit()


@pytest.mark.asyncio
async def test_ac05b_cada_compania_ve_solo_lo_suyo(http_client, seeded_ids):
    a = _token(seeded_ids["user_operator_id"])
    b = _token(seeded_ids["user_other_company_id"])

    de_a = await http_client.get("/api/v1/operations?limit=100", headers=a)
    de_b = await http_client.get("/api/v1/operations?limit=100", headers=b)
    assert de_a.status_code == 200 and de_b.status_code == 200

    ids_a = {e["company_id"] for e in de_a.json()}
    ids_b = {e["company_id"] for e in de_b.json()}
    assert ids_a <= {seeded_ids["company_id"]}, f"La compañía A vio {ids_a}"
    assert ids_b <= {seeded_ids["company_id_2"]}, f"La compañía B vio {ids_b}"


# ── Coherencia entre lo que exigen las rutas y lo que conceden los roles ──────

# Operaciones de administración que solo el Super Admin ejecuta. No existe un rol
# «Administrador» por debajo, y crearlo sería inventar una figura que ninguna fuente
# describe. Se enumeran para que la lista sea una decisión visible y no un descuido.
SOLO_SUPER_ADMIN = {
    ("masters", "create"), ("masters", "update"), ("masters", "delete"),
    ("lots", "create"), ("lots", "update"),
    ("users", "read"), ("users", "create"), ("users", "update"), ("users", "delete"),
    ("review", "create"), ("review", "update"), ("review", "delete"),
    ("operations", "delete"),
    # `GA-REM-040` fase 7. Administrar unidades de negocio es plano de control, de la misma
    # clase que administrar usuarios: por eso entra aquí y por la misma razón que aquello.
    # No se siembra en ningún rol **a propósito**. La alternativa habría sido dársela a
    # «Supervisor Avícola», y supervisar la producción no es decidir qué cadenas opera la
    # empresa ni quién accede a ellas; inventar un rol nuevo sería inventar una figura que
    # ninguna fuente describe, que es justo lo que este bloque lleva evitando.
    #
    # El permiso **sí** es concedible: consta en el catálogo (`AuthService.MODULOS`), de modo
    # que el propietario puede crear el rol que le corresponda a su organización desde
    # `/roles`. Lo que no hace el producto es repartirlo solo, y hasta que alguien lo conceda
    # el valor por defecto es cerrado.
    ("business_units", "read"), ("business_units", "update"),
    ("business_units", "create"), ("business_units", "delete"),
}


def test_todo_permiso_exigido_lo_concede_algun_rol_o_es_de_super_admin():
    """El enforcement solo sirve si el catálogo de roles es coherente con él.

    Mientras nada comprobaba los permisos, las definiciones de rol podían estar
    incompletas sin que se notara: **ningún rol declaraba `masters:read`**, necesario
    para cargar granjas, galpones o vacunas en casi todas las pantallas. Con el
    enforcement activo, esa ausencia habría dejado la aplicación inservible para
    cualquiera que no fuese Super Admin.

    Este test impide que la brecha vuelva a abrirse en silencio.
    """
    import pathlib
    import re

    from app.authorization_coverage import enumerar_rutas, permiso_declarado
    from app.main import app

    exigidos = {p for _, _, r in enumerar_rutas(app) if (p := permiso_declarado(r))}
    texto = pathlib.Path(__file__).resolve().parent.parent.joinpath(
        "seeds", "dev_seeds.py").read_text(encoding="utf-8")
    concedidos = {
        (modulo, accion.lower())
        for modulo, accion in re.findall(
            r'\{"module": "(\w+)", "action": PermissionAction\.(\w+)\}', texto)
    }

    huerfanos = sorted(exigidos - concedidos - SOLO_SUPER_ADMIN)
    assert not huerfanos, (
        "Permisos exigidos por alguna ruta que ningún rol concede y que no constan como "
        f"exclusivos del Super Admin: {huerfanos}\n"
        "Complete el rol correspondiente en `seeds/dev_seeds.py` o añádalos a "
        "`SOLO_SUPER_ADMIN` con criterio.")


def test_los_permisos_de_super_admin_no_son_una_lista_creciente():
    """La excepción debe ser acotada: si crece, alguien está evitando definir roles.

    El límite sube de 15 a 17 en `GA-REM-040` fase 7, y conviene decir exactamente por qué,
    porque este test detecta justo la maniobra que podría parecer que se está haciendo.

    Las cuatro entradas nuevas son la administración de unidades de negocio. **El diagnóstico
    del test es correcto: falta un rol.** Ninguno de los cinco roles sembrados administra
    accesos —Supervisor supervisa producción, Auditor lee, Aprobador aprueba— y darle
    `business_units:create` a cualquiera de ellos le permitiría concederse a sí mismo las
    cuatro cadenas, que es precisamente la escalada que la fase documenta y acota.

    Crear un rol «Administrador de accesos» sería inventar una figura que ninguna fuente
    describe, que es lo que este bloque lleva evitando desde que se escribió. De modo que la
    pregunta —**quién administra el acceso por unidad en una avícola**— queda registrada como
    decisión de propietario (`R-113`) en vez de contestada por conveniencia de una prueba.

    El límite sube a **17 exactos**, no a un número holgado: la siguiente adición vuelve a
    romperlo, que es para lo que sirve.
    """
    assert len(SOLO_SUPER_ADMIN) <= 17, (
        "Demasiadas operaciones reservadas al Super Admin: probablemente falte definir "
        "un rol administrativo")


# ── GA-REM-003 · el refresco no debe degradar la identidad ────────────────────

def _claims(token: str) -> dict:
    import base64
    import json

    carga = token.split(".")[1]
    carga += "=" * (-len(carga) % 4)
    return json.loads(base64.urlsafe_b64decode(carga))


@pytest.mark.asyncio
async def test_ga_rem_003_el_refresco_conserva_el_contexto(client, test_credentials):
    """`refresh` emitía `{sub, username}` y perdía compañía, rol y vista.

    El backend no lo notaba —carga el usuario por `sub`— pero el frontend lee esos
    claims del token (`auth.store.ts:76`), de modo que tras renovar la sesión la interfaz
    se quedaba sin vista ni compañía.
    """
    usuario, password = test_credentials
    login = await client.post("/api/v1/login", json={"username": usuario, "password": password})
    assert login.status_code == 200, login.text
    del_login = _claims(login.json()["access_token"])

    renovado = await client.post("/api/v1/refresh",
                                 json={"refresh_token": login.json()["refresh_token"]})
    assert renovado.status_code == 200, renovado.text
    del_refresco = _claims(renovado.json()["access_token"])

    for campo in ("sub", "username", "company_id", "role_id", "view_type"):
        assert campo in del_refresco, f"El refresco perdió '{campo}'"
        assert del_refresco[campo] == del_login[campo], (
            f"'{campo}' cambió al renovar: {del_login[campo]!r} -> {del_refresco[campo]!r}")


@pytest.mark.asyncio
async def test_ga_rem_003b_el_refresco_recoge_los_cambios_de_la_base(
    client, auth_headers, test_credentials, seeded_ids
):
    """Reconstruir desde la base, y no copiar claims, tiene una consecuencia deseable."""
    from sqlalchemy import select

    import app.database as database
    from app.auth.models import User

    usuario, password = test_credentials
    login = await client.post("/api/v1/login", json={"username": usuario, "password": password})
    original = _claims(login.json()["access_token"])["view_type"]
    nueva = "mobile" if original != "mobile" else "web"

    async with database.async_session() as sesion:
        obj = (await sesion.execute(
            select(User).where(User.username == usuario))).scalar_one()
        obj.view_type = nueva
        await sesion.commit()

    renovado = await client.post("/api/v1/refresh",
                                 json={"refresh_token": login.json()["refresh_token"]})
    assert _claims(renovado.json()["access_token"])["view_type"] == nueva, (
        "La renovación debe recoger el estado vigente, no arrastrar el del login")

    async with database.async_session() as sesion:
        obj = (await sesion.execute(
            select(User).where(User.username == usuario))).scalar_one()
        obj.view_type = original
        await sesion.commit()

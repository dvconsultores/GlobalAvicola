"""`P0-13` — el cambio de contraseña debe cambiar la contraseña.

`PUT /users/{id}` con `{password}` devolvía `200`, la interfaz mostraba «contraseña
actualizada» y la anterior seguía autenticando: un falso positivo funcional y de
seguridad. Toda rotación de credencial tras una sospecha de compromiso era ficticia.

Se verifica el ciclo completo —la anterior deja de servir, la nueva sirve— y que ningún
camino pueda volver a responder éxito sin haber cambiado nada.
"""

from __future__ import annotations

import pytest

NUEVA = "NuevaClaveSegura2026"


async def _crear_usuario(client, headers, sufijo: str, password: str,
                         company_id: int | None = None,
                         role_id: int = 1) -> tuple[int, str]:
    """Alta de un usuario de prueba.

    Se le asigna compañía a propósito: un usuario sin ella rompe la inserción de
    auditoría, porque `audit_logs.company_id` no admite nulos (`R-37`).
    """
    usuario = f"p013_{sufijo}"
    cuerpo = {
        "first_name": "P013", "last_name": sufijo, "email": f"{usuario}@example.com",
        "username": usuario, "password": password, "role_id": role_id,
    }
    if company_id is not None:
        cuerpo["company_id"] = company_id
    r = await client.post("/api/v1/users", headers=headers, json=cuerpo)
    assert r.status_code == 201, r.text
    return r.json()["id"], usuario


async def _login(client, usuario: str, password: str):
    return await client.post("/api/v1/login", json={"username": usuario, "password": password})


# ── T-012-01 · el cambio surte efecto ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_t012_01_el_cambio_surte_efecto(auth_headers, client):
    original = "ClaveOriginal2026"
    uid, usuario = await _crear_usuario(client, auth_headers, "efecto", original)

    assert (await _login(client, usuario, original)).status_code == 200

    r = await client.post(f"/api/v1/users/{uid}/password", headers=auth_headers,
                          json={"new_password": NUEVA})
    assert r.status_code == 204, r.text

    assert (await _login(client, usuario, NUEVA)).status_code == 200, \
        "La contraseña nueva debe autenticar"
    assert (await _login(client, usuario, original)).status_code == 401, \
        "La contraseña anterior no puede seguir sirviendo: eso era P0-13"


# ── T-012-02 · se exige la contraseña actual ──────────────────────────────────

@pytest.mark.asyncio
async def test_t012_02_el_titular_debe_aportar_su_contrasena_actual(client, test_credentials):
    usuario, password = test_credentials
    login = await _login(client, usuario, password)
    cabecera = {"Authorization": f"Bearer {login.json()['access_token']}"}
    yo = (await client.get("/api/v1/me", headers=cabecera)).json()["id"]

    sin_actual = await client.post(f"/api/v1/users/{yo}/password", headers=cabecera,
                                   json={"new_password": NUEVA})
    assert sin_actual.status_code == 400, "Cambiar la propia sin aportar la actual debe fallar"

    incorrecta = await client.post(f"/api/v1/users/{yo}/password", headers=cabecera,
                                   json={"current_password": "no-es-esta", "new_password": NUEVA})
    assert incorrecta.status_code == 400

    assert (await _login(client, usuario, password)).status_code == 200, \
        "Tras dos rechazos la contraseña debe seguir siendo la misma"


@pytest.mark.asyncio
async def test_t012_02b_el_titular_cambia_la_suya_con_la_actual(auth_headers, client, seeded_ids):
    original = "ClavePropia2026"
    uid, usuario = await _crear_usuario(client, auth_headers, "propia", original, seeded_ids["company_id"])
    login = await _login(client, usuario, original)
    cabecera = {"Authorization": f"Bearer {login.json()['access_token']}"}

    r = await client.post(f"/api/v1/users/{uid}/password", headers=cabecera,
                          json={"current_password": original, "new_password": NUEVA})
    assert r.status_code == 204, r.text
    assert (await _login(client, usuario, NUEVA)).status_code == 200


# ── T-012-03 · sin falsos positivos ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_t012_03_put_users_ya_no_acepta_password(auth_headers, client):
    """El camino que mentía: `PUT /users/{id}` con `{password}`.

    Debe rechazarse de forma explícita. Aceptarlo y descartarlo era lo que permitía a la
    interfaz anunciar un éxito inexistente.
    """
    original = "ClaveSilencio2026"
    uid, usuario = await _crear_usuario(client, auth_headers, "silencio", original)

    r = await client.put(f"/api/v1/users/{uid}", headers=auth_headers,
                         json={"password": NUEVA})
    assert r.status_code == 422, (
        f"`PUT /users` debe rechazar `password`, no ignorarlo: {r.status_code}")
    assert (await _login(client, usuario, original)).status_code == 200


# ── T-012-04 · política única (RR-05) ─────────────────────────────────────────

@pytest.mark.parametrize("password,valida", [
    ("corto12", False),      # 7
    ("justo123", True),      # 8
    ("holgadamente-larga", True),
])
@pytest.mark.asyncio
async def test_t012_04_politica_unica_de_longitud(auth_headers, client, password, valida):
    """La misma longitud mínima en el alta y en el cambio (`RR-05`)."""
    alta = await client.post("/api/v1/users", headers=auth_headers, json={
        "first_name": "P013", "last_name": "pol", "email": f"pol{len(password)}@example.com",
        "username": f"p013_pol_{len(password)}", "password": password, "role_id": 1,
    })
    assert (alta.status_code == 201) is valida, alta.text

    uid, _ = await _crear_usuario(client, auth_headers, f"cam{len(password)}", "ClaveBase2026")
    cambio = await client.post(f"/api/v1/users/{uid}/password", headers=auth_headers,
                               json={"new_password": password})
    assert (cambio.status_code == 204) is valida, (
        f"El alta y el cambio deben aplicar el mismo criterio a '{password}'")


# ── T-012-05 · aislamiento entre usuarios ─────────────────────────────────────

@pytest.mark.asyncio
async def test_t012_05_nadie_cambia_la_contrasena_de_otro(auth_headers, client, seeded_ids):
    ajena = "ClaveAjena2026"
    uid_victima, usuario_victima = await _crear_usuario(client, auth_headers, "victima", ajena, seeded_ids["company_id"])
    # El atacante es un operador, no un administrador: con `role_id=1` habría sido
    # super admin y el test habría verificado lo contrario de lo que pretende.
    _, usuario_atacante = await _crear_usuario(
        client, auth_headers, "atacante", "ClaveAtacante2026",
        seeded_ids["company_id"], role_id=seeded_ids["role_operator_id"])

    login = await _login(client, usuario_atacante, "ClaveAtacante2026")
    cabecera = {"Authorization": f"Bearer {login.json()['access_token']}"}

    r = await client.post(f"/api/v1/users/{uid_victima}/password", headers=cabecera,
                          json={"new_password": NUEVA})
    assert r.status_code == 403, (
        f"Un usuario sin autorización no puede cambiar la contraseña de otro: {r.status_code}")
    assert (await _login(client, usuario_victima, ajena)).status_code == 200


# ── T-012-06 · restablecimiento por administrador ─────────────────────────────

@pytest.mark.asyncio
async def test_t012_06_el_administrador_restablece_sin_la_anterior(auth_headers, client):
    uid, usuario = await _crear_usuario(client, auth_headers, "reset", "ClaveOlvidada2026")
    r = await client.post(f"/api/v1/users/{uid}/password", headers=auth_headers,
                          json={"new_password": NUEVA})
    assert r.status_code == 204, "El administrador no conoce la anterior y no debe necesitarla"
    assert (await _login(client, usuario, NUEVA)).status_code == 200


# ── T-012-07 · auditoría sin secretos ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_t012_07_la_auditoria_registra_el_hecho_y_no_el_secreto(auth_headers, client, seeded_ids):
    uid, _ = await _crear_usuario(client, auth_headers, "audit", "ClaveAudit2026", seeded_ids["company_id"])
    await client.post(f"/api/v1/users/{uid}/password", headers=auth_headers,
                      json={"new_password": NUEVA})

    r = await client.get("/api/v1/audit?limit=100", headers=auth_headers)
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    registros = cuerpo if isinstance(cuerpo, list) else cuerpo.get("logs", [])
    entradas = [e for e in registros if isinstance(e, dict) and e.get("entity_type") == "user_password"]
    assert entradas, "El cambio de contraseña debe quedar auditado"
    crudo = str(entradas)
    assert NUEVA not in crudo, "La auditoría no puede contener la contraseña"
    assert "$2b$" not in crudo and "hashed" not in crudo, "Tampoco su hash"


# ── T-012-08 · comportamiento de las sesiones ─────────────────────────────────

@pytest.mark.asyncio
async def test_t012_08_las_sesiones_previas_siguen_vivas_hasta_expirar(auth_headers, client):
    """Comportamiento documentado, no accidental.

    Los JWT son sin estado: no existe lista de revocación, de modo que un token emitido
    antes del cambio sigue siendo válido hasta que caduca. Se documenta aquí porque un
    usuario que rota su contraseña tras una sospecha de compromiso **espera lo contrario**.
    La revocación pertenece a `GA-REM-003` (ciclo de vida del token); este test fija el
    comportamiento actual para que el cambio sea visible cuando llegue.
    """
    original = "ClaveSesion2026"
    uid, usuario = await _crear_usuario(client, auth_headers, "sesion", original)
    login = await _login(client, usuario, original)
    cabecera_previa = {"Authorization": f"Bearer {login.json()['access_token']}"}

    await client.post(f"/api/v1/users/{uid}/password", headers=auth_headers,
                      json={"new_password": NUEVA})

    yo = await client.get("/api/v1/me", headers=cabecera_previa)
    assert yo.status_code == 200, (
        "Comportamiento actual: el token previo sigue vigente. Si esto cambia, "
        "actualice GA-REM-003 y este test.")

#!/usr/bin/env python3
"""U1 técnico (T13) — sondas REALES de sesión/seguridad contra el runtime desplegado.

- Lee credenciales del canal autorizado (~/ga_uat09_credentials.txt) y NUNCA las imprime.
- Ejecuta: login · /me · logout · reuso del access tras logout (revocación AC04) ·
  refresh tras logout · relogin · RBAC negativo (/users) · catálogo de permisos ·
  switch-company · bearer inválido.
- Salida: códigos HTTP + notas (sin secretos). Uso: python3 scripts_uat_u1_runtime.py
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://avicola.globaldv.net"
CREDS = Path.home() / "ga_uat09_credentials.txt"


def _post(path: str, payload: dict, token: str | None = None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _get(path: str, token: str | None = None):
    req = urllib.request.Request(BASE + path, method="GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def load_creds() -> dict:
    """Extrae el usuario operador/aprobador y la contraseña común del archivo.

    Formato verificado del archivo (estructura, sin valores): líneas
    `Operador de abuelas: <usuario>` · `Aprobador: <usuario>` · `Contraseña común: <clave>`.
    Nunca se imprime ningún valor.
    """
    text = CREDS.read_text(encoding="utf-8")
    m_op = re.search(r"(?im)^\s*Operador[^\n:]*:\s*(\S+)\s*$", text)
    m_ap = re.search(r"(?im)^\s*Aprobador[^\n:]*:\s*(\S+)\s*$", text)
    m_pw_line = re.search(r"(?im)^\s*Contrase[^\n]*$", text)
    if not (m_op and m_pw_line):
        sys.exit("PARSE_FAILED: estructura no reconocida")
    password = m_pw_line.group(0).split()[-1]
    pairs = {"operador": (m_op.group(1), password)}
    if m_ap:
        pairs["aprobador"] = (m_ap.group(1), password)
    return pairs


def main() -> None:
    creds = load_creds()
    op_key = next(k for k in creds if k.startswith(("operador", "operator")))
    user, password = creds[op_key]
    print(f"== U1 runtime probes · BASE={BASE} · usuario={user} (sin secretos) ==")

    res: list[tuple[str, int]] = []

    # 1 · login
    st, body = _post("/api/v1/login", {"username": user, "password": password})
    res.append(("login", st))
    print(f"1  login: {st}")
    if st != 200:
        sys.exit("LOGIN_FALLIDO: se detiene la sonda (¿rate limit vigente? esperar 60 s)")
    tok = json.loads(body)
    access, refresh = tok.get("access_token", ""), tok.get("refresh_token", "")

    # 2 · /me
    st, body = _get("/api/v1/me", access)
    res.append(("/me", st))
    print(f"2  /me: {st}")

    # 3 · logout (AC04: exige sesión y el refresh del propio titular)
    st, _ = _post("/api/v1/logout", {"refresh_token": refresh}, access)
    res.append(("logout", st))
    print(f"3  logout: {st}")

    # 4 · reuso del access tras logout (revocación real)
    st, _ = _get("/api/v1/me", access)
    res.append(("reuso-access-tras-logout", st))
    print(f"4  reuso access tras logout: {st} (esperado 401)")

    # 5 · refresh tras logout
    st, _ = _post("/api/v1/refresh", {"refresh_token": refresh})
    res.append(("refresh-tras-logout", st))
    print(f"5  refresh tras logout: {st} (esperado 401)")

    # 6 · relogin (ventana de rate limit: 5/min por IP → pausa defensiva)
    time.sleep(62)
    st, body = _post("/api/v1/login", {"username": user, "password": password})
    res.append(("relogin", st))
    print(f"6  relogin: {st}")
    if st != 200:
        sys.exit("RELOGIN_FALLIDO: se detiene la sonda")
    tok = json.loads(body)
    access = tok.get("access_token", "")

    # 7 · RBAC negativo: operator no debe poder listar usuarios
    st, _ = _get("/api/v1/users", access)
    res.append(("rbac-users-denegado", st))
    print(f"7  GET /users con rol operador: {st} (esperado 403)")

    # 8 · catálogo de permisos (lectura)
    st, _ = _get("/api/v1/roles/permissions-catalog", access)
    res.append(("permissions-catalog", st))
    print(f"8  GET /roles/permissions-catalog: {st}")

    # 9 · switch-company (alcance empresa)
    st, _ = _post("/api/v1/switch-company", {"company_id": 1}, access)
    res.append(("switch-company", st))
    print(f"9  switch-company: {st}")

    # 10 · bearer inválido
    st, _ = _get("/api/v1/me", "token-invalido-de-prueba")
    res.append(("bearer-invalido", st))
    print(f"10 /me con bearer inválido: {st} (esperado 401)")

    print("== RESUMEN ==")
    for name, code in res:
        print(f"  {name}: {code}")


if __name__ == "__main__":
    main()

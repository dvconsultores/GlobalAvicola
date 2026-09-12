#!/usr/bin/env python3
"""`GA-R153` · limpieza de los artefactos sintéticos del E2E runtime.

Hace, en orden: cancelar eventos no terminales del ejercicio → revocar concesiones → dar de
baja usuarios sintéticos → desactivar roles sintéticos → restaurar el catálogo de unidades a
`OFF`. Guarda el resultado en `audit/ga-r153/evidence/cleanup.json`. Sin secretos: los tokens
no se imprimen ni se persisten.

Variables: `GA_FLOW_USER` / `GA_FLOW_PASSWORD` (admin global).
"""
import json
import os
import pathlib
import ssl
import urllib.error
import urllib.request

BASE = "https://avicola.globaldv.net/api/v1"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
EVIDENCIA = pathlib.Path(__file__).parent / "audit" / "ga-r153" / "evidence" / "cleanup.json"

#: Eventos no terminales creados por los ejercicios (importaciones registradas, recepción de
#: sonda, activo UI). Los aprobados no se tocan: quedan documentados en el ledger.
CANCELAR = [79, 81, 82, 83, 84, 87, 91]

RESULTADOS: dict = {}


def req(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if token:
        r.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(r, context=CTX, timeout=90) as resp:
            crudo = resp.read().decode() or "{}"
            try:
                return resp.status, json.loads(crudo)
            except json.JSONDecodeError:
                return resp.status, crudo[:200]
    except urllib.error.HTTPError as e:
        crudo = e.read().decode() or ""
        try:
            return e.code, json.loads(crudo)
        except json.JSONDecodeError:
            return e.code, crudo[:300]


def main():
    admin = req("POST", "/login", body={"username": os.environ["GA_FLOW_USER"],
                                        "password": os.environ["GA_FLOW_PASSWORD"]})[1]["access_token"]
    admin = req("POST", "/switch-company", admin, {"company_id": 1})[1]["access_token"]

    # 1 · eventos no terminales
    cancelados = {}
    for evento in CANCELAR:
        st, d = req("POST", f"/operations/{evento}/cancel", admin)
        cancelados[str(evento)] = {"status": st,
                                   "detalle": d.get("detail") if isinstance(d, dict) and st >= 400 else d.get("status")}
        print("cancelar", evento, "→", st)
    RESULTADOS["eventos_cancelados"] = cancelados

    # 2 · usuarios sintéticos (por prefijo) — concesiones primero
    st, us = req("GET", "/users?search=e2e-r153&limit=100", admin)
    usuarios = us if isinstance(us, list) else us.get("items", [])
    detalle_usuarios = []
    for u in usuarios:
        stg, concesiones = req("GET", f"/users/{u['id']}/business-units", admin)
        revocadas = []
        if stg == 200:
            for c in concesiones:
                if c.get("revoked_at") is None:
                    strv, _ = req("DELETE", f"/users/{u['id']}/business-units/{c['code']}", admin)
                    revocadas.append({"code": c["code"], "status": strv})
        std, _ = req("DELETE", f"/users/{u['id']}", admin)
        detalle_usuarios.append({"id": u["id"], "username": u["username"],
                                 "revocadas": revocadas, "baja": std})
        print("usuario", u["username"], "revocadas:", revocadas, "baja:", std)
    RESULTADOS["usuarios"] = detalle_usuarios

    # 3 · roles sintéticos
    st, rs = req("GET", "/roles?search=e2e-r153&limit=100", admin)
    roles = rs if isinstance(rs, list) else rs.get("items", [])
    detalle_roles = []
    for r in roles:
        sr, _ = req("PUT", f"/roles/{r['id']}", admin, {"is_active": False})
        detalle_roles.append({"id": r["id"], "name": r["name"], "desactivado": sr})
        print("rol", r["name"], "→", sr)
    RESULTADOS["roles"] = detalle_roles

    # 4 · catálogo a OFF y verificación
    st, _ = req("PATCH", "/business-units/grandparent/disable", admin)
    stc, catalogo = req("GET", "/business-units", admin)
    estado = {u["code"]: u["is_enabled"] for u in catalogo} if stc == 200 else {}
    RESULTADOS["catalogo_final"] = estado
    print("catálogo final:", estado)

    EVIDENCIA.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCIA.write_text(json.dumps(RESULTADOS, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("EVIDENCIA:", EVIDENCIA)


if __name__ == "__main__":
    main()

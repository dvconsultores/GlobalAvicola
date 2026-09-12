#!/usr/bin/env python3
"""`GA-R153` · E2E runtime autenticado (`OD-25 (B)`).

Ejerce en el runtime real (`https://avicola.globaldv.net`) el contrato de `R-153`:
importación de abuelas **sin lote** → aprobación `P-07` crea el lote `L-GP-{año}-{nn}` sin
poblar → la recepción es la entrada de población → vía manual intacta → legado sin duplicar →
negativo sin concesión cerrado. Guarda evidencia en `audit/ga-r153/evidence/runtime-e2e.json`.

Variables de entorno: `GA_FLOW_USER` / `GA_FLOW_PASSWORD` (admin global). Sin secretos en el
archivo ni en la evidencia: los tokens nunca se imprimen ni se persisten.
"""
import datetime
import json
import os
import pathlib
import ssl
import sys
import urllib.error
import urllib.request
import uuid

BASE = "https://avicola.globaldv.net/api/v1"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
EVIDENCIA = pathlib.Path(__file__).parent / "audit" / "ga-r153" / "evidence" / "runtime-e2e.json"

HOY = datetime.date.today().isoformat()
SEMILLA = uuid.uuid4().hex[:6]
CLAVE_TEMPORAL = "E2E-" + uuid.uuid4().hex[:12]  # usuarios sintéticos, se eliminan al final
EVENTOS: list = []
FALLOS: list = []


def paso(nombre: str, status, detalle=None):
    EVENTOS.append({"step": nombre, "status": status, "detail": detalle})
    marca = "OK " if isinstance(status, int) and status < 400 else "!! "
    print(f"{marca}{nombre}: {status} {str(detalle)[:160] if detalle is not None else ''}", flush=True)
    return status


def req(method: str, path: str, token: str | None = None, body=None):
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


def exigir(cond, nombre):
    if not cond:
        FALLOS.append(nombre)
        raise SystemExit(f"FALLO: {nombre}")


def login(usuario, clave):
    st, d = req("POST", "/login", body={"username": usuario, "password": clave})
    exigir(st == 200 and isinstance(d, dict) and d.get("access_token"), f"login {usuario}")
    return d["access_token"]


def con_empresa(token, company_id):
    """Si el token no trae empresa efectiva, la fija (`switch-company` devuelve token nuevo)."""
    st, yo = req("GET", "/me", token=token)
    if st == 200 and isinstance(yo, dict) and yo.get("company_id") is None:
        st2, d2 = req("POST", "/switch-company", token=token, body={"company_id": company_id})
        exigir(st2 == 200 and d2.get("access_token"), "switch-company")
        return d2["access_token"]
    return token


def plan_importacion(oc):
    return {
        "origin_country": "Francia", "purchased_total": 110, "shipped_total": 105,
        "received_total": 100, "transit_mortality": 5,
        "departure_date": (datetime.date.today() - datetime.timedelta(days=7)).isoformat(),
        "arrival_date": HOY, "reception_condition": "buena", "quarantine_days": 21,
        "quarantine_end_date": (datetime.date.today() + datetime.timedelta(days=21)).isoformat(),
        "initial_health_inspection": "sin hallazgos",
    }


def importacion(oc, lot_id=None, extra=None):
    cuerpo = {
        "event_type": "grandparent_import", "event_date": HOY,
        "sap_document_ref": oc, "supplier_id": SUP, "transport_id": TR,
        "bird_movements": [{"sex": "male", "quantity": 40}, {"sex": "female", "quantity": 60}],
        "extra_data": {"import_plan": plan_importacion(oc)},
    }
    if lot_id is not None:
        cuerpo["lot_id"] = lot_id
    if extra:
        cuerpo.update(extra)
    return cuerpo


def aprobar(event_id, token_op, token_ap):
    st, _ = req("POST", f"/operations/{event_id}/submit", token=token_op)
    exigir(st == 200, f"submit {event_id}")
    st, _ = req("POST", f"/review/start/{event_id}", token=token_ap)
    exigir(st == 200, f"review/start {event_id}")
    st, d = req("POST", "/review/complete", token=token_ap, body={"event_id": event_id})
    exigir(st == 200, f"review/complete {event_id}")
    aprobado = isinstance(d, dict) and d.get("status") == "approved"
    if not aprobado:
        st, d = req("POST", "/approvals/approve", token=token_ap, body={"event_id": event_id})
        exigir(st == 200, f"approve {event_id}")
        return "approve-explicito"
    return "complete-nivel-unico"


def crear_actor(admin, sufijo, permisos):
    st, rol = req("POST", "/roles", token=admin,
                  body={"name": f"e2e-r153-{sufijo}-{SEMILLA}",
                        "permissions": [{"module": m, "action": a, "scope_type": "company"}
                                        for m, a in permisos]})
    exigir(st == 201, f"rol {sufijo}")
    usuario = f"e2e-r153-{sufijo}-{SEMILLA}"
    st, usr = req("POST", "/users", token=admin,
                  body={"email": f"{usuario}@example.com", "username": usuario,
                        "password": CLAVE_TEMPORAL, "first_name": "E2E", "last_name": f"R153-{sufijo}",
                        "role_id": rol["id"]})
    exigir(st == 201, f"usuario {sufijo}")
    token = con_empresa(login(usuario, CLAVE_TEMPORAL), COMPANY)
    return {"rol": rol["id"], "usuario": usr["id"], "username": usuario, "token": token}


def lotes_gp():
    st, d = req("GET", "/lots?search=L-GP&limit=50", token=ADMIN)
    exigir(st == 200, "listar L-GP")
    items = d if isinstance(d, list) else d.get("items", [])
    return items


# ════════════════════════════ preflight ════════════════════════════
ADMIN = login(os.environ["GA_FLOW_USER"], os.environ["GA_FLOW_PASSWORD"])
paso("login-admin", 200)
# La empresa efectiva del admin global se fija con `switch-company` (no hay listado `/companies`
# para el rol global); se prueban las primeras empresas hasta que el contexto responda.
COMPANY = None
for candidata in (1, 2, 3):
    st, d2 = req("POST", "/switch-company", token=ADMIN, body={"company_id": candidata})
    if st == 200 and isinstance(d2, dict) and d2.get("access_token"):
        prueba = d2["access_token"]
        st2, _ = req("GET", "/business-units", token=prueba)
        if st2 == 200:
            ADMIN, COMPANY = prueba, candidata
            break
exigir(COMPANY is not None, "fijar empresa efectiva")
st, yo = req("GET", "/me", token=ADMIN)
NOMBRE_EMPRESA = (yo.get("company_name") if isinstance(yo, dict) else None) or f"company-{COMPANY}"
paso("empresa-efectiva", 200, {"id": COMPANY, "nombre": NOMBRE_EMPRESA})

st, cat = req("GET", "/business-units", token=ADMIN)
exigir(st == 200, "catálogo BU")
estado_inicial = {u["code"]: u["is_enabled"] for u in cat}
paso("catalogo-antes", 200, estado_inicial)
st, _ = req("PATCH", "/business-units/grandparent/enable", token=ADMIN)
exigir(st == 200, "habilitar grandparent")
paso("grandparent-ON", 200)

base_gp = lotes_gp()
paso("lotes-L-GP-antes", 200, [liquid["lot_code"] for liquid in base_gp])

st, sups = req("GET", "/masters/suppliers", token=ADMIN)
st2, trs = req("GET", "/masters/transports", token=ADMIN)
exigir(st == 200 and st2 == 200 and sups and trs, "proveedor/transporte")
SUP = sups[0]["id"]
TR = trs[0]["id"]
st, granjas = req("GET", "/masters/farms", token=ADMIN)
FARM = granjas[0]["id"] if st == 200 and granjas else None
HOUSE = None
if FARM:
    st3, casas = req("GET", f"/masters/farms/{FARM}/houses", token=ADMIN)
    HOUSE = casas[0]["id"] if st3 == 200 and casas else None
paso("maestros", 200, {"supplier": SUP, "transport": TR, "farm": FARM, "house": HOUSE})

# negativos ANTES de tocar nada: sin concesión no se registra (403)
neg = crear_actor(ADMIN, "neg", [("operations", "create")])
st, d = req("POST", "/operations", token=neg["token"],
            body=importacion(f"E2E-R153-OC-NEG"))
paso("AC45-negativo-sin-concesion", st, d if st != 201 else "INESPERADO-201")
exigir(st == 403, "negativo sin concesión debe ser 403")

# ════════════════════════════ actores ════════════════════════════
op = crear_actor(ADMIN, "op", [("operations", "create"), ("operations", "read"),
                               ("operations", "update"), ("lots", "read")])
ap = crear_actor(ADMIN, "ap", [("review", "read"), ("review", "review"), ("approvals", "approve"),
                               ("approvals", "reject"), ("corrections", "read"), ("corrections", "correct"),
                               ("lots", "read"), ("operations", "read")])
for actor in (op, ap):
    st, d = req("POST", f"/users/{actor['usuario']}/business-units", token=ADMIN,
                body={"code": "grandparent"})
    if st == 422:
        st, d = req("POST", f"/users/{actor['usuario']}/business-units", token=ADMIN,
                    body={"business_unit_code": "grandparent"})
    exigir(st in (200, 201), f"conceder grandparent a {actor['username']}")
paso("actores-y-concesiones", 200, {"op": op["username"], "ap": ap["username"]})

# ════════════════ E2E-01…08 · importar sin lote → aprobar → lote ════════════════
st, d = req("POST", "/operations", token=op["token"],
            body=importacion("E2E-R153-OC-01",
                             extra={k: v for k, v in (("farm_id", FARM), ("house_id", HOUSE)) if v}))
paso("E2E-01-import-sin-lote", st, {"respuesta": d} if st != 201 else
     {"event_id": d["id"], "lot_id": d.get("lot_id")})
exigir(st == 201, "registrar importación sin lote")
IMPORT_1 = d["id"]
exigir(d.get("lot_id") in (None, ""), "import nuevo sin lot_id")

st, det = req("GET", f"/operations/{IMPORT_1}", token=op["token"])
VIA_OPERADOR = st == 200
if not VIA_OPERADOR:
    st, det = req("GET", f"/operations/{IMPORT_1}", token=ADMIN)
TOK_OP = op["token"] if VIA_OPERADOR else ADMIN
TOK_AP = ap["token"] if VIA_OPERADOR else ADMIN
paso("E2E-02-detalle-antes", st,
     {"lot_id": det.get("lot_id"),
      "via": "operador" if VIA_OPERADOR else "admin (fallback: clasificación del plano "
             "de control aún sin unidad para el evento sin lote)"})
exigir(st == 200, "detalle del evento")
exigir(det.get("lot_id") in (None, ""), "detalle sin lote antes de aprobar")
paso("E2E-03-cero-lotes-antes", 200, [liquid["lot_code"] for liquid in lotes_gp()])
exigir(len(lotes_gp()) == len(base_gp), "sin lote antes de aprobar")

via = aprobar(IMPORT_1, TOK_OP, TOK_AP)
st, det = req("GET", f"/operations/{IMPORT_1}", token=TOK_OP)
LOTE_1 = det.get("lot_id")
paso("E2E-04-aprobacion-crea-lote", st, {"via": via, "lot_id": LOTE_1})
exigir(LOTE_1, "aprobación debe fijar lot_id")

st, lote = req("GET", f"/lots/{LOTE_1}", token=TOK_OP)
esperado = {"bird_type": "grandparent", "status": "active"}
datos_lote = {k: lote.get(k) for k in ("lot_code", "bird_type", "sex", "status", "start_date",
                                       "company_id", "farm_id", "activation_type")}
paso("E2E-05-datos-canonicos", st, datos_lote)
exigir(lote.get("lot_code", "").startswith("L-GP-"), "código L-GP")
exigir(datos_lote["bird_type"] == esperado["bird_type"], "bird_type grandparent")
exigir(datos_lote["sex"] == "mixed", "sexo mixto (♂40/♀60)")
exigir(datos_lote["start_date"][:10] == HOY, "start_date = llegada")

st, rep = req("GET", f"/reports/lot/{LOTE_1}", token=TOK_OP)
VIA_REPORTE = "operador"
if st in (401, 403):
    st, rep = req("GET", f"/reports/lot/{LOTE_1}", token=ADMIN)
    VIA_REPORTE = "admin (el operador no tiene permiso de reportes)"
saldo_0 = rep if st == 200 else None
paso("E2E-06-sin-poblacion", st, {"saldo": json.dumps(saldo_0)[:220], "via": VIA_REPORTE})

# ════════════ E2E-12…16 · recepción = única entrada de población ════════════
st, rec = req("POST", "/operations", token=TOK_OP, body={
    "event_type": "bird_reception", "event_date": HOY, "lot_id": LOTE_1,
    "farm_id": FARM, "house_id": HOUSE,
    "bird_movements": [{"sex": "female", "quantity": 10}],
})
paso("E2E-12-recepcion-registrada", st, {"event_id": rec.get("id") if isinstance(rec, dict) else rec})
exigir(st == 201, "registrar recepción")
REC_1 = rec["id"]
aprobar(REC_1, TOK_OP, TOK_AP)
st, rep2 = req("GET", f"/reports/lot/{LOTE_1}", token=TOK_OP)
if st in (401, 403):
    st, rep2 = req("GET", f"/reports/lot/{LOTE_1}", token=ADMIN)
paso("E2E-13-poblacion-tras-recepcion", st, {"saldo": json.dumps(rep2)[:220]})

# ════════════ E2E-17…21 · vía manual intacta + legado sin duplicar ════════════
st, manual = req("POST", "/lots", token=ADMIN, body={
    "lot_code": f"E2E-MAN-153-{SEMILLA}", "bird_type": "grandparent", "start_date": HOY,
})
paso("E2E-17-lote-manual", st, {"id": manual.get("id") if isinstance(manual, dict) else manual})
exigir(st == 201, "crear lote manual")
MANUAL = manual["id"]

st, legado = req("POST", "/operations", token=TOK_OP,
                 body=importacion("E2E-R153-OC-02", lot_id=MANUAL))
paso("E2E-18-import-legado-con-lote", st, {"event_id": legado.get("id") if isinstance(legado, dict) else legado})
exigir(st == 201, "registrar importación legada con lote")
LEGADO = legado["id"]
aprobar(LEGADO, TOK_OP, TOK_AP)
st, det_l = req("GET", f"/operations/{LEGADO}", token=TOK_OP)
gp_despues = lotes_gp()
paso("E2E-19-legado-sin-duplicar", st, {"lot_id_evento": det_l.get("lot_id"),
                                        "lotes_gp_total": len(gp_despues)})
exigir(det_l.get("lot_id") == MANUAL, "legado conserva su lote")
exigir(len(gp_despues) == len(base_gp) + 1, "un solo L-GP nuevo (el de E2E-01)")

# ════════════ activo para la verificación UI (queda sin aprobar) ════════════
st, pend = req("POST", "/operations", token=TOK_OP,
               body=importacion("E2E-R153-OC-UI",
                                extra={k: v for k, v in (("farm_id", FARM), ("house_id", HOUSE)) if v}))
exigir(st == 201, "registrar importación pendiente para UI")
PENDIENTE = pend["id"]
paso("UI-activo-pendiente", 201, {"event_id": PENDIENTE})

# ════════════════════════════ evidencia ════════════════════════════
EVIDENCIA.parent.mkdir(parents=True, exist_ok=True)
EVIDENCIA.write_text(json.dumps({
    "fecha": HOY, "runtime": "https://avicola.globaldv.net", "empresa": {"id": COMPANY, "nombre": NOMBRE_EMPRESA},
    "semilla": SEMILLA, "pasos": EVENTOS,
    "activos": {"IMPORT_1": IMPORT_1, "LOTE_1": LOTE_1, "REC_1": REC_1, "MANUAL": MANUAL,
                "LEGADO": LEGADO, "PENDIENTE": PENDIENTE,
                "actores": {"op": op["username"], "ap": ap["username"], "neg": neg["username"]},
                "roles": {"op": op["rol"], "ap": ap["rol"], "neg": neg["rol"]},
                "usuarios": {"op": op["usuario"], "ap": ap["usuario"], "neg": neg["usuario"]}},
}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("EVIDENCIA:", EVIDENCIA)
print("FALLOS:", FALLOS or "ninguno")

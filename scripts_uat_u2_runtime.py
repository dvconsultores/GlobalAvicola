#!/usr/bin/env python3
"""U2 técnico (T13) — recorrido REAL de Progenitoras contra el runtime desplegado.

C1: importación sin lote (201; lot_id null)   · C2: "se creará al aprobar" (detalle sin lote)
C3: la aprobación crea el lote (#N, L-GP-…, grandparent, mixto, fecha=llegada)
+ mortalidad pre-recepción rechazada · recepción ♂40+♀60 · población 100 una vez · vía manual intacta.

Credenciales del canal autorizado (nunca se imprimen). Uso:
    python3 scripts_uat_u2_runtime.py
"""

import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

BASE = "https://avicola.globaldv.net"
CREDS = Path.home() / "ga_uat09_credentials.txt"


def _req(method: str, path: str, token: str | None = None, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read()
            try:
                return r.status, json.loads(body) if body else None
            except json.JSONDecodeError:
                return r.status, body.decode(errors="replace")[:200]
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body) if body else None
        except json.JSONDecodeError:
            return e.code, body.decode(errors="replace")[:200]


def load_creds() -> dict:
    text = CREDS.read_text(encoding="utf-8")
    m_op = re.search(r"(?im)^\s*Operador[^\n:]*:\s*(\S+)\s*$", text)
    m_ap = re.search(r"(?im)^\s*Aprobador[^\n:]*:\s*(\S+)\s*$", text)
    m_pw = re.search(r"(?im)^\s*Contrase[^\n]*$", text)
    if not (m_op and m_ap and m_pw):
        sys.exit("PARSE_FAILED: estructura del archivo de credenciales no reconocida")
    pw = m_pw.group(0).split()[-1]
    return {"operador": (m_op.group(1), pw), "aprobador": (m_ap.group(1), pw)}


def login(user: str, pw: str):
    st, body = _req("POST", "/api/v1/login", payload={"username": user, "password": pw})
    if st != 200:
        sys.exit(f"LOGIN_FALLIDO ({st}) — ¿rate limit vigente? esperar 60 s")
    return body["access_token"]


def main() -> None:
    creds = load_creds()
    print(f"== U2 runtime · BASE={BASE} ==")
    tok_op = login(*creds["operador"])
    tok_ap = login(*creds["aprobador"])
    print("login operador: 200 · login aprobador: 200")

    hoy = date.today()
    plan = {
        "origin_country": "Francia",
        "purchased_total": 110,
        "shipped_total": 105,
        "received_total": 100,
        "transit_mortality": 5,
        "departure_date": (hoy - timedelta(days=10)).isoformat(),
        "arrival_date": hoy.isoformat(),
        "reception_condition": "buena",
        "quarantine_days": 21,
        "quarantine_end_date": (hoy + timedelta(days=21)).isoformat(),
        "initial_health_inspection": "sin hallazgos",
    }

    # ── descubrimiento ─────────────────────────────────────────────────────
    st, farms = _req("GET", "/api/v1/masters/farms?limit=50", tok_op)
    print(f"masters/farms: {st}")
    st2, sup = _req("GET", "/api/v1/masters/suppliers?limit=50", tok_op)
    st3, tr = _req("GET", "/api/v1/masters/transports?limit=50", tok_op)
    print(f"masters/suppliers: {st2} · masters/transports: {st3}")
    api_sap = None
    ref_code = None
    for p in ("/api/v1/sap/references?limit=100", "/api/v1/sap/references", "/api/v1/sap-references"):
        stx, refs = _req("GET", p, tok_op)
        detalle_x = ((refs or {}).get("detail") or "") if isinstance(refs, dict) else ""
        print(f"  OC vía {p}: {stx} {detalle_x[:80]}")
        if stx == 200 and isinstance(refs, dict) and isinstance(refs.get("references"), list):
            api_sap = refs["references"]
            break
        if stx == 200 and isinstance(refs, list):
            api_sap = refs
            break
    if api_sap:
        for r in api_sap:
            code = str(r.get("sap_code", ""))
            if code.startswith("PO-C001-GPR"):
                ref_code = code
                break
        if ref_code is None and api_sap:
            ref_code = str(api_sap[0].get("sap_code"))
    if ref_code is None:
        # La ficha U2 documenta la OC del contexto: el servidor la validará al registrar.
        ref_code = "PO-C001-GPR-0001"
        print(f"OC por fallback documentado: {ref_code} (validación server-side)")
    else:
        print(f"OC seleccionada vía API: {ref_code}")

    if not (farms and sup and tr and ref_code):
        sys.exit("PRECONDICIÓN_FAILED: faltan maestros/OC en el entorno")

    farm = farms[0]
    st, houses = _req("GET", f"/api/v1/masters/farms/{farm['id']}/houses", tok_op)
    if st != 200 or not houses:
        st, houses = _req("GET", "/api/v1/masters/houses?limit=50", tok_op)
    house = houses[0]
    print(f"granja={farm['id']} · galpón={house['id']} · proveedor={sup[0]['id']} · transporte={tr[0]['id']}")

    # ── C1 · importación SIN lote ──────────────────────────────────────────
    cuerpo = {
        "event_type": "grandparent_import",
        "event_date": hoy.isoformat(),
        "farm_id": farm["id"],
        "house_id": house["id"],
        "sap_document_ref": ref_code,
        "supplier_id": sup[0]["id"],
        "transport_id": tr[0]["id"],
        "bird_movements": [{"sex": "male", "quantity": 40}, {"sex": "female", "quantity": 60}],
        "extra_data": {"import_plan": plan},
    }
    st, ev = _req("POST", "/api/v1/operations", tok_op, cuerpo)
    print(f"C1 import sin lote: {st} · lot_id={ev.get('lot_id') if isinstance(ev, dict) else ev}")
    if st != 201:
        sys.exit(f"C1_FAILED: {st} {ev}")
    evento = ev["id"]

    # ── C2 · detalle pre-aprobación: sin lote ──────────────────────────────
    st, det = _req("GET", f"/api/v1/operations/{evento}", tok_op)
    print(f"C2 detalle pre-aprobación: {st} · lot_id={det.get('lot_id')} · status={det.get('status')}")

    # ── C3 · cadena de aprobación ──────────────────────────────────────────
    st, _ = _req("POST", f"/api/v1/operations/{evento}/submit", tok_op)
    print(f"submit (operador): {st}")
    st, _ = _req("POST", f"/api/v1/review/start/{evento}", tok_ap)
    print(f"review/start (aprobador): {st}")
    st, _ = _req("POST", "/api/v1/review/complete", tok_ap, {"event_id": evento})
    print(f"review/complete: {st}")
    st, ap = _req("POST", "/api/v1/approvals/approve", tok_ap, {"event_id": evento})
    print(f"approve: {st} · status={ap.get('status') if isinstance(ap, dict) else ap}")

    st, det = _req("GET", f"/api/v1/operations/{evento}", tok_op)
    lot_id = det.get("lot_id")
    print(f"C3 detalle post-aprobación: {st} · lot_id={lot_id}")
    if not lot_id:
        sys.exit("C3_FAILED: la aprobación no creó el lote")
    st, lote = _req("GET", f"/api/v1/lots/{lot_id}", tok_op)
    print(
        f"C3 lote: {st} · code={lote.get('lot_code')} · bird_type={lote.get('bird_type')} · "
        f"sex={lote.get('sex')} · start_date={str(lote.get('start_date'))[:10]} · farm={lote.get('farm_id')}"
    )
    st, ob = _req("GET", f"/api/v1/lots/{lot_id}/opening-balance", tok_op)
    print(f"opening-balance lote: {st} · {ob if st == 200 else ''}")

    # ── mortalidad pre-recepción (saldo 0 ⇒ rechazada) ─────────────────────
    st, causas = _req("GET", "/api/v1/masters/mortality-causes?limit=20", tok_op)
    causa = causas[0]["id"] if (st == 200 and causas) else None
    mort = {
        "event_type": "mortality_recording",
        "event_date": hoy.isoformat(),
        "lot_id": lot_id,
        "farm_id": farm["id"],
        "house_id": house["id"],
        "bird_movements": [{"sex": "mixed", "quantity": 100}],
    }
    if causa:
        mort["mortality_cause_id"] = causa
    st, r = _req("POST", "/api/v1/operations", tok_op, mort)
    detalle = (r.get("detail") if isinstance(r, dict) else str(r))[:160] if r else ""
    print(f"mortalidad pre-recepción (100): {st} · {detalle}")

    # ── recepción ♂40 + ♀60 ────────────────────────────────────────────────
    recep = {
        "lot_id": lot_id,
        "event_type": "bird_reception",
        "event_date": hoy.isoformat(),
        "farm_id": farm["id"],
        "house_id": house["id"],
        "sap_document_ref": ref_code,
        "bird_movements": [{"sex": "male", "quantity": 40}, {"sex": "female", "quantity": 60}],
    }
    st, rec = _req("POST", "/api/v1/operations", tok_op, recep)
    print(f"recepción 40+60: {st} · status={rec.get('status') if isinstance(rec, dict) else rec}")
    rec_id = rec["id"] if isinstance(rec, dict) and "id" in rec else None

    # si la recepción requiere aprobación, completarla (cadena P-07)
    if rec_id:
        st, det_rec = _req("GET", f"/api/v1/operations/{rec_id}", tok_op)
        estado = det_rec.get("status") if isinstance(det_rec, dict) else None
        if estado not in ("approved",):
            for (m, p, t, body) in (
                ("POST", f"/api/v1/operations/{rec_id}/submit", tok_op, None),
                ("POST", f"/api/v1/review/start/{rec_id}", tok_ap, None),
                ("POST", "/api/v1/review/complete", tok_ap, {"event_id": rec_id}),
                ("POST", "/api/v1/approvals/approve", tok_ap, {"event_id": rec_id}),
            ):
                stx, _ = _req(m, p, t, body)
                print(f"recepción · {p}: {stx}")
            st, det_rec = _req("GET", f"/api/v1/operations/{rec_id}", tok_op)
            print(f"recepción status final: {det_rec.get('status')}")

    # ── población = 100 una sola vez (sonda de saldo vía rechazo de 101) ───
    mort2 = dict(mort)
    mort2["bird_movements"] = [{"sex": "mixed", "quantity": 101}]
    st, r2 = _req("POST", "/api/v1/operations", tok_op, mort2)
    detalle2 = (r2.get("detail") if isinstance(r2, dict) else str(r2))[:160] if r2 else ""
    print(f"sonda saldo (mortalidad 101): {st} · {detalle2}")

    # ── vía manual «Nuevo lote» intacta ────────────────────────────────────
    st, r3 = _req("POST", "/api/v1/lots", tok_op, {})
    print(f"POST /lots (cuerpo vacío): {st} (esperado 422 ⇒ ruta manual viva)")

    print("== FIN U2 ==")


if __name__ == "__main__":
    main()

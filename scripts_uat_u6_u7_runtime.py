#!/usr/bin/env python3
"""U6/U7-lite técnicos (T13) — sondas REALES en el runtime desplegado, alcance GP.

La cuenta UAT-09 es «Operador de abuelas» (BU `grandparent` únicamente): las sondas
de U3/U4/U5/U8 que exigen escenarios breeder/hatchery/broiler quedan fuera de su
alcance por diseño X-BU (se documentan como llevadas por las suites de pila
completa). Este guion ejecuta lo que el canal autorizado habilita:

U6 · Revisión y reverso (P-07) sobre el lote GP 67 (R-153/AC28/29):
     peso → submit → start → return(obs) → resubmit → aprobación completa.
U7-lite · Notificaciones (bandeja propia) · trazabilidad del lote 67 ·
     permisos de reportes/auditoría del rol (sonda).
BR-18 · sonda de cierre del lote GP 67 al final (el último paso del recorrido).

Credenciales del canal autorizado (nunca se imprimen). Uso:
    python3 scripts_uat_u6_u7_runtime.py
"""

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

BASE = "https://avicola.globaldv.net"
CREDS = Path.home() / "ga_uat09_credentials.txt"
LOTE_GP = 67


def _req(method: str, path: str, token: str | None = None, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
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
    pw = m_pw.group(0).split()[-1]
    return {"operador": (m_op.group(1), pw), "aprobador": (m_ap.group(1), pw)}


def login(user: str, pw: str) -> str:
    st, body = _req("POST", "/api/v1/login", payload={"username": user, "password": pw})
    if st != 200:
        sys.exit(f"LOGIN_FALLIDO ({st})")
    return body["access_token"]


def resumen_cuenta(etiqueta: str, tok: str) -> None:
    st, me = _req("GET", "/api/v1/me", tok)
    if isinstance(me, dict):
        print(f"  {etiqueta}: perms={me.get('permissions')}")
        print(f"  {etiqueta}: BU efectiva={me.get('effective_business_units')}")


def main() -> None:
    creds = load_creds()
    print(f"== U6/U7-lite runtime · BASE={BASE} ==")
    tok_op = login(*creds["operador"])
    tok_ap = login(*creds["aprobador"])
    print("login operador/aprobador: 200")
    resumen_cuenta("operador", tok_op)
    resumen_cuenta("aprobador", tok_ap)
    hoy = date.today().isoformat()

    # ── U6 · evento para el ciclo de reverso (lote GP 67) ──────────────────────
    print("\n══ U6 · Revisión y reverso (P-07) — lote GP 67 ══")
    st, lote = _req("GET", f"/api/v1/lots/{LOTE_GP}", tok_op)
    farm = lote.get("farm_id") if isinstance(lote, dict) else None
    house = lote.get("house_id") if isinstance(lote, dict) else None
    base = {"lot_id": LOTE_GP, "farm_id": farm, "house_id": house, "event_date": hoy}

    fid = None
    st, r = _req("POST", "/api/v1/operations", tok_op, {
        **base, "event_type": "weight_recording",
        "bird_movements": [{"sex": "mixed", "quantity": 10, "avg_weight": 150}]})
    print(f"  peso de prueba: {st} id={r.get('id') if isinstance(r, dict) else r}")
    if st == 201:
        fid = r["id"]
    else:
        st, r = _req("POST", "/api/v1/operations", tok_op, {
            **base, "event_type": "mortality_recording",
            "bird_movements": [{"sex": "mixed", "quantity": 1}]})
        print(f"  fallback mortalidad 1 ave: {st} id={r.get('id') if isinstance(r, dict) else r}")
        if st == 201:
            fid = r["id"]

    if fid:
        st, r = _req("POST", f"/api/v1/operations/{fid}/submit", tok_op)
        print(f"  submit (operador): {st} status={r.get('status') if isinstance(r, dict) else r}")
        st, r = _req("POST", f"/api/v1/review/start/{fid}", tok_ap)
        print(f"  review/start (aprobador): {st} status={r.get('status') if isinstance(r, dict) else r}")
        st, band = _req("GET", "/api/v1/review/pending?status=in_review&limit=200", tok_ap)
        contiene = isinstance(band, dict) and any(e.get("id") == fid for e in band.get("events", []))
        print(f"  bandeja in_review: {st} contiene el evento: {contiene}")
        st, r = _req("POST", "/api/v1/review/return", tok_ap,
                     {"event_id": fid, "observations": "Corregir cantidad por favor"})
        print(f"  reverso con observaciones: {st} status={r.get('status') if isinstance(r, dict) else r}")
        st, band = _req("GET", "/api/v1/review/pending?status=returned&limit=200", tok_ap)
        contiene = isinstance(band, dict) and any(e.get("id") == fid for e in band.get("events", []))
        print(f"  bandeja returned: {st} contiene el evento: {contiene}")
        st, acciones = _req("GET", f"/api/v1/review/events/{fid}/actions", tok_ap)
        n = len(acciones) if isinstance(acciones, list) else "?"
        accs = [a.get("action") for a in acciones] if isinstance(acciones, list) else []
        print(f"  historial de acciones: {st} ({n} entradas: {accs})")
        st, r = _req("POST", f"/api/v1/operations/{fid}/submit", tok_op)
        print(f"  reenvío tras reverso: {st} status={r.get('status') if isinstance(r, dict) else r}")
        for (m, p, t, body) in (
            ("POST", f"/api/v1/review/start/{fid}", tok_ap, None),
            ("POST", "/api/v1/review/complete", tok_ap, {"event_id": fid}),
            ("POST", "/api/v1/approvals/approve", tok_ap, {"event_id": fid}),
        ):
            st, r = _req(m, p, t, body)
            print(f"  {p if not body else '/approvals/approve'}: {st}")
        st, det = _req("GET", f"/api/v1/operations/{fid}", tok_op)
        print(f"  status final del evento: {det.get('status') if isinstance(det, dict) else det} "
              f"(esperado approved)")
    else:
        print("  DEGRADED: no se pudo registrar el evento de reverso")

    # ── U7-lite · notificaciones, trazabilidad, sondas de rol ─────────────────
    print("\n══ U7-lite · Notificaciones / trazabilidad / rol ══")
    st, cont = _req("GET", "/api/v1/notifications/unread-count", tok_op)
    st2, lista = _req("GET", "/api/v1/notifications?limit=5", tok_op)
    tipos = sorted({n.get("notification_type") for n in (lista or [])}) if isinstance(lista, list) else []
    print(f"  notificaciones operador: unread={cont.get('unread') if isinstance(cont, dict) else cont} tipos={tipos}")
    st, traza = _req("GET", f"/api/v1/lots/{LOTE_GP}/traceability", tok_op)
    claves = sorted(traza.keys()) if isinstance(traza, dict) else traza
    print(f"  trazabilidad lote 67: {st} claves={claves}")
    for ruta in (f"/api/v1/reports/lot/{LOTE_GP}", f"/api/v1/reports/kpi/ipe/{LOTE_GP}", "/api/v1/audit?limit=5"):
        st, r = _req("GET", ruta, tok_op)
        d = r.get("detail") if isinstance(r, dict) else ""
        print(f"  sonda rol {ruta}: {st} {str(d)[:80]}")

    # ── BR-18 · sonda de cierre del lote GP 67 (último paso del recorrido) ─────
    print("\n══ BR-18 · sonda de cierre del lote GP 67 ══")
    st, cierre = _req("POST", f"/api/v1/lots/{LOTE_GP}/close", tok_op)
    d = cierre.get("detail") if isinstance(cierre, dict) else cierre
    print(f"  cierre: {st} · {str(d)[:200] if st != 200 else json.dumps(cierre)[:300]}")
    st, det = _req("GET", f"/api/v1/lots/{LOTE_GP}", tok_op)
    print(f"  lote tras sonda: status={det.get('status') if isinstance(det, dict) else det} "
          f"end_date={str(det.get('end_date'))[:10] if isinstance(det, dict) else ''}")

    print("\n== FIN U6/U7-lite ==")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Cierre BR-18 del lote GP 67 — paso final del recorrido de abuelas en runtime.

El cierre exige un registro de consumo de alimento (para FCR). Se registra,
se aprueba por la cadena P-07 y se reintenta el cierre. Uso:
    python3 scripts_uat_cierre_gp_runtime.py
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


def main() -> None:
    creds = load_creds()
    print(f"== Cierre BR-18 · lote GP {LOTE_GP} · BASE={BASE} ==")
    tok_op = login(*creds["operador"])
    tok_ap = login(*creds["aprobador"])
    print("login operador/aprobador: 200")
    hoy = date.today().isoformat()

    st, lote = _req("GET", f"/api/v1/lots/{LOTE_GP}", tok_op)
    farm = lote.get("farm_id") if isinstance(lote, dict) else None
    house = lote.get("house_id") if isinstance(lote, dict) else None
    print(f"lote {LOTE_GP}: status={lote.get('status') if isinstance(lote, dict) else lote}")

    st, tipos = _req("GET", "/api/v1/masters/feed-types?limit=1", tok_op)
    tipo_id = tipos[0]["id"] if (st == 200 and tipos) else None
    print(f"tipo de alimento: {st} id={tipo_id}")

    st, feed = _req("POST", "/api/v1/operations", tok_op, {
        "lot_id": LOTE_GP, "farm_id": farm, "house_id": house, "event_date": hoy,
        "event_type": "feed_registration",
        "feed_movements": [{"quantity_kg": 380.0, "feed_type_id": tipo_id}],
    })
    print(f"alimento 380 kg: {st} id={feed.get('id') if isinstance(feed, dict) else feed}")
    if st == 201:
        fid = feed["id"]
        for (m, p, t, body, etiqueta) in (
            ("POST", f"/api/v1/operations/{fid}/submit", tok_op, None, "submit"),
            ("POST", f"/api/v1/review/start/{fid}", tok_ap, None, "start"),
            ("POST", "/api/v1/review/complete", tok_ap, {"event_id": fid}, "complete"),
            ("POST", "/api/v1/approvals/approve", tok_ap, {"event_id": fid}, "approve"),
        ):
            st, _ = _req(m, p, t, body)
            print(f"  {etiqueta}: {st}")

    st, cierre = _req("POST", f"/api/v1/lots/{LOTE_GP}/close", tok_op)
    d = cierre.get("detail") if isinstance(cierre, dict) else cierre
    print(f"cierre: {st} · {str(d)[:220] if st != 200 else json.dumps(cierre)[:400]}")
    st, det = _req("GET", f"/api/v1/lots/{LOTE_GP}", tok_op)
    if isinstance(det, dict):
        print(f"lote tras cierre: status={det.get('status')} end_date={str(det.get('end_date'))[:10]} "
              f"(esperado closed/{hoy})")

    print("== FIN cierre BR-18 ==")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""U3–U8 técnicos (T13) — sondas REALES contra el runtime desplegado.

U3 · Reproductoras (P-03): BR-20 cuadre · distribución BR-17 · peso vs curva §4.5 · versión de curva
U4 · Incubadora (P-04+P-05): huevos fértiles · carga · saldo derivado · BR-03 · nacimiento BR-21 · despacho
U5 · Engorde y cierre (P-06): cadena completa + aprobaciones · cierre · resumen · R7 sin aprobar · FCR
U6 · Revisión y reverso (P-07): bandeja · reverso con observaciones · historial · reenvío · aprobación
U7 · Reportes/trazabilidad: reporte de lote · KPIs · IPE · uniformidad · trazabilidad · auditoría (sonda)
U8 · Maestros/usuarios: alta de maestros · notificaciones · activación manual (OD-10.c)

Credenciales del canal autorizado (nunca se imprimen). Uso:
    python3 scripts_uat_u3_u8_runtime.py
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
    if not (m_op and m_ap and m_pw):
        sys.exit("PARSE_FAILED: estructura del archivo de credenciales no reconocida")
    pw = m_pw.group(0).split()[-1]
    return {"operador": (m_op.group(1), pw), "aprobador": (m_ap.group(1), pw)}


def login(user: str, pw: str) -> str:
    st, body = _req("POST", "/api/v1/login", payload={"username": user, "password": pw})
    if st != 200:
        sys.exit(f"LOGIN_FALLIDO ({st}) — ¿rate limit vigente? esperar 60 s")
    return body["access_token"]


def company_of(token: str) -> int:
    carga = token.split(".")[1]
    carga += "=" * (-len(carga) % 4)
    import base64

    claims = json.loads(base64.urlsafe_b64decode(carga))
    return int(claims["company_id"])


def suf() -> str:
    return f"{int(time.time()) % 100000:05d}"


def hoy(d: int = 0) -> str:
    return (date.today() + timedelta(days=d)).isoformat()


def detalle(r) -> str:
    if isinstance(r, dict):
        d = r.get("detail") or r.get("rule") or ""
        return str(d)[:150]
    return str(r)[:150] if r else ""


class UAT:
    def __init__(self, tok_op: str, tok_ap: str, comp: int):
        self.op, self.ap, self.company = tok_op, tok_ap, comp

    def crear(self, path: str, data: dict, tok: str | None = None):
        return _req("POST", path, tok or self.op, data)

    def get(self, path: str, tok: str | None = None):
        return _req("GET", path, tok or self.op)

    def registrar(self, data: dict):
        return _req("POST", "/api/v1/operations", self.op, data)

    def aprobar(self, event_id: int, tok_op_owner: str | None = None):
        pasos = []
        st, _ = _req("POST", f"/api/v1/operations/{event_id}/submit", tok_op_owner or self.op)
        pasos.append(("submit", st))
        st, _ = _req("POST", f"/api/v1/review/start/{event_id}", self.ap)
        pasos.append(("start", st))
        st, _ = _req("POST", "/api/v1/review/complete", self.ap, {"event_id": event_id})
        pasos.append(("complete", st))
        st, _ = _req("POST", "/api/v1/approvals/approve", self.ap, {"event_id": event_id})
        pasos.append(("approve", st))
        return pasos

    def saldo(self, lot_id: int, incluye_load: bool) -> int:
        st, cuerpo = self.get(f"/api/v1/operations?lot_id={lot_id}&limit=100")
        eventos = cuerpo if isinstance(cuerpo, list) else (cuerpo or {}).get("events", [])
        total = 0
        for evento in eventos:
            if evento.get("status") == "cancelled":
                continue
            stx, det = self.get(f"/api/v1/operations/{evento['id']}")
            if evento["event_type"] == "egg_collection":
                total += sum(m.get("quantity", 0) for m in (det.get("egg_movements") or []))
            elif evento["event_type"] == "egg_dispatch":
                total -= sum(m.get("quantity", 0) for m in (det.get("egg_movements") or []))
            elif evento["event_type"] == "egg_reception_hatchery":
                total += sum(m.get("quantity", 0) for m in (det.get("egg_movements") or []))
            elif incluye_load and evento["event_type"] == "incubation_load":
                total -= sum(p.get("quantity_loaded", 0) for p in (det.get("hatchery_params") or []))
        return total


def seccion(t: str) -> None:
    print(f"\n══ {t} ══")


def escenario(u: UAT, pref: str, bird: str, con_curva: bool = False, start_days: int = 0):
    s = suf()
    datos: dict = {"farm": None, "house": None, "linea": None, "curva": None, "lot": None}
    st, farm = u.crear("/api/v1/masters/farms", {
        "company_id": u.company, "name": f"{pref}-granja-{s}", "code": f"{pref}-G-{s}",
        "location": "Escenario de certificación UAT", "farm_type": "breeding",
    })
    print(f"  granja: {st}")
    if st != 201:
        st, farms = u.get("/api/v1/masters/farms?limit=1")
        farm = (farms or [{}])[0]
        print(f"  fallback granja existente: {st}")
    st, house = u.crear("/api/v1/masters/houses", {
        "farm_id": farm["id"], "name": f"{pref}-galpon-{s}", "capacity": 50000,
    })
    print(f"  galpón: {st}")
    if st != 201:
        st, houses = u.get(f"/api/v1/masters/farms/{farm['id']}/houses")
        house = (houses or [{}])[0]
        print(f"  fallback galpón existente: {st}")
    if con_curva:
        st, linea = u.crear("/api/v1/masters/genetic-lines", {
            "company_id": u.company, "name": f"{pref}-linea-{s}",
        })
        print(f"  línea genética: {st}")
        if st == 201:
            datos["linea"] = linea
            st, curva = u.crear("/api/v1/masters/weight-curves", {
                "genetic_line_id": linea["id"], "version_label": f"{pref}-2024",
                "is_active": True,
                "points": [
                    {"age_days": 10, "min_weight": 90, "target_weight": 100, "max_weight": 110},
                    {"age_days": 20, "min_weight": 180, "target_weight": 200, "max_weight": 220},
                ],
            })
            print(f"  curva: {st}")
            if st == 201:
                datos["curva"] = curva
    lote = {
        "company_id": u.company, "farm_id": farm["id"], "house_id": house["id"],
        "lot_code": f"{pref}-LOTE-{s}", "bird_type": bird, "sex": "mixed",
    }
    if datos["linea"]:
        lote["genetic_line_id"] = datos["linea"]["id"]
    if start_days:
        lote["start_date"] = hoy(-start_days)
    st, lot = u.crear("/api/v1/lots", lote)
    print(f"  lote: {st} id={lot.get('id') if isinstance(lot, dict) else lot}")
    datos.update({"farm": farm, "house": house, "lot": lot if st == 201 else None})
    return datos


def main() -> None:
    creds = load_creds()
    print(f"== U3–U8 runtime · BASE={BASE} ==")
    tok_op = login(*creds["operador"])
    tok_ap = login(*creds["aprobador"])
    u = UAT(tok_op, tok_ap, company_of(tok_op))
    print(f"login operador/aprobador: 200 · company={u.company}")

    # ════════════════════════════ U3 · REPRODUCTORAS (P-03) ════════════════════
    seccion("U3 · Reproductoras (P-03)")
    esc3 = escenario(u, "U3", "breeder", con_curva=True, start_days=15)
    if esc3["lot"]:
        lot3, farm3, house3 = esc3["lot"]["id"], esc3["farm"]["id"], esc3["house"]["id"]
        base3 = {"lot_id": lot3, "farm_id": farm3, "house_id": house3, "event_date": hoy()}

        # BR-20 · cuadre exacto: negativo primero (Σ ≠ declarado), sin efectos colaterales.
        st, r = u.registrar({**base3, "event_type": "bird_reception",
                             "bird_movements": [{"sex": "mixed", "quantity": 3000}],
                             "received_total": 3000, "dead_on_arrival": 1, "rejected_on_arrival": 0})
        print(f"  BR-20 cuadre inconsistente: {st} · {detalle(r)}")

        recib = {**base3, "event_type": "bird_reception",
                 "bird_movements": [{"sex": "mixed", "quantity": 3000}],
                 "received_total": 3000, "dead_on_arrival": 0, "rejected_on_arrival": 0}
        st, r = u.registrar(recib)
        opcional_oc = ""
        if st not in (200, 201):
            s2 = suf()
            sto, oc = u.crear("/api/v1/sap/references/import", {
                "references": [{"ref_type": "purchase_order", "sap_code": f"U3-OC-{s2}", "quantity": 5000}],
            })
            print(f"  import OC nueva: {sto}")
            if sto == 201:
                st, r = u.registrar({**recib, "sap_document_ref": f"U3-OC-{s2}"})
                opcional_oc = f" (con OC U3-OC-{s2})"
            elif st == 400:
                st, r = u.registrar({**recib, "sap_document_ref": "PO-C001-GPR-0001"})
                opcional_oc = " (con OC existente)"
        print(f"  BR-20 recepción cuadrada 3000{opcional_oc}: {st} · {detalle(r) if st not in (200, 201) else ''}")

        # BR-17 · distribución por galpón.
        st, r = u.registrar({**base3, "event_type": "bird_distribution",
                             "bird_movements": [{"sex": "mixed", "quantity": 3000}]})
        print(f"  BR-17 distribución: {st}")

        # §4.5 · peso vs curva (edad 15 d ⇒ interpolado 135–165).
        st, dentro = u.registrar({**base3, "event_type": "weight_recording",
                                  "bird_movements": [{"sex": "mixed", "quantity": 100, "avg_weight": 150}]})
        print(f"  peso en norma (150 g): {st}")
        st, fuera = u.registrar({**base3, "event_type": "weight_recording",
                                 "bird_movements": [{"sex": "mixed", "quantity": 100, "avg_weight": 100}]})
        print(f"  peso bajo norma (100 g): {st}")
        if st == 201:
            stx, alertas = u.get(f"/api/v1/operations/alerts?lot_id={lot3}&limit=200")
            propias = [a for a in (alertas or []) if a.get("event_id") == fuera.get("id")]
            print(f"  alerta del evento: type={propias[0]['alert_type'] if propias else None} "
                  f"umbral={propias[0]['threshold_value'] if propias else None} "
                  f"valor={propias[0]['actual_value'] if propias else None} (esperado 135/100)")
        if st == 201 and dentro.get("id"):
            stx, alertas = u.get(f"/api/v1/operations/alerts?lot_id={lot3}&limit=200")
            propias = [a for a in (alertas or []) if a.get("event_id") == dentro.get("id")]
            print(f"  alertas del pesaje en norma: {len(propias)} (esperado 0)")

        # Versión de curva conservada.
        if esc3["curva"] and esc3["linea"]:
            sto, _ = u.crear("/api/v1/masters/weight-curves", {
                "genetic_line_id": esc3["linea"]["id"], "version_label": f"U3V-{suf()}",
                "is_active": True,
                "points": [{"age_days": 10, "min_weight": 900, "max_weight": 1100},
                           {"age_days": 20, "min_weight": 1800, "max_weight": 2200}],
            })
            stx, lote = u.get(f"/api/v1/lots/{lot3}")
            conserva = isinstance(lote, dict) and lote.get("weight_curve_id") == esc3["curva"]["id"]
            print(f"  nueva versión publicada: {sto} · lote conserva su curva: {conserva} "
                  f"(id={lote.get('weight_curve_id') if isinstance(lote, dict) else None})")
        else:
            print("  SKIPPED_PERM: sin curva creada (degradación por permisos)")
    else:
        print("  DEGRADED: no se pudo crear el lote U3")

    # ════════════════════════ U6 · REVISIÓN Y REVERSO (P-07) ════════════════════
    # Se usa un evento del lote U3 (alimentación) para el ciclo reverso→reenvío.
    seccion("U6 · Revisión y reverso (P-07)")
    if esc3["lot"]:
        st, tipos = u.get("/api/v1/masters/feed-types?limit=1")
        tipo_id = tipos[0]["id"] if (st == 200 and tipos) else None
        st, feed = u.registrar({**base3, "event_type": "feed_registration",
                                "feed_movements": [{"quantity_kg": 380.0, "feed_type_id": tipo_id}]})
        if st != 201:
            st, feed = u.registrar({**base3, "event_type": "weight_recording",
                                    "bird_movements": [{"sex": "mixed", "quantity": 50, "avg_weight": 150}]})
        print(f"  evento para reverso: {st} id={feed.get('id') if isinstance(feed, dict) else feed}")
        if st == 201:
            fid = feed["id"]
            st, _ = _req("POST", f"/api/v1/operations/{fid}/submit", u.op)
            print(f"  submit: {st}")
            st, _ = _req("POST", f"/api/v1/review/start/{fid}", u.ap)
            print(f"  start: {st}")
            stb, band0 = _req("GET", "/api/v1/review/pending?status=in_review&limit=200", u.ap)
            en_bandeja = any(e.get("id") == fid for e in (band0 or {}).get("events", [])) if isinstance(band0, dict) else False
            print(f"  bandeja in_review contiene el evento: {en_bandeja}")
            st, rev = _req("POST", "/api/v1/review/return", u.ap,
                           {"event_id": fid, "observations": "Corregir cantidad por favor"})
            print(f"  reverso con observaciones: {st} · status={rev.get('status') if isinstance(rev, dict) else rev}")
            stb, band = _req("GET", "/api/v1/review/pending?status=returned&limit=200", u.ap)
            contiene = any(e.get("id") == fid for e in (band or {}).get("events", [])) if isinstance(band, dict) else False
            print(f"  bandeja returned contiene el evento: {contiene}")
            sta, acciones = _req("GET", f"/api/v1/review/events/{fid}/actions", u.ap)
            print(f"  historial de acciones: {sta} ({len(acciones) if isinstance(acciones, list) else '?'} entradas)")
            st, _ = _req("POST", f"/api/v1/operations/{fid}/submit", u.op)
            print(f"  reenvío tras corrección: {st}")
            pasos = u.aprobar(fid)
            print(f"  ciclo final: {pasos}")
            st, det = u.get(f"/api/v1/operations/{fid}")
            print(f"  status final del evento: {det.get('status') if isinstance(det, dict) else det}")
            stn, cont = u.get("/api/v1/notifications/unread-count")
            stl, lista = u.get("/api/v1/notifications?limit=5")
            tipos_n = sorted({n.get("notification_type") for n in (lista or [])}) if isinstance(lista, list) else []
            print(f"  notificaciones operador: unread={cont.get('unread') if isinstance(cont, dict) else cont} tipos={tipos_n}")
    else:
        print("  DEGRADED: sin lote U3")

    # ═══════════════════════════ U4 · INCUBADORA (P-04/P-05) ═══════════════════
    seccion("U4 · Incubadora (P-04 + P-05)")
    esc4 = escenario(u, "U4", "hatchery")
    if esc4["lot"]:
        lot4, farm4, house4 = esc4["lot"]["id"], esc4["farm"]["id"], esc4["house"]["id"]
        base4 = {"lot_id": lot4, "farm_id": farm4, "house_id": house4, "event_date": hoy()}
        print(f"  saldo incubadora inicial: {u.saldo(lot4, incluye_load=True)} (esperado 0)")
        st, r = u.registrar({**base4, "event_type": "egg_reception_hatchery",
                             "egg_movements": [{"egg_type": "fertile", "quantity": 1000}]})
        print(f"  recepción de huevos: {st}")
        print(f"  saldo tras recepción: {u.saldo(lot4, incluye_load=True)} (esperado 1000)")
        st, r = u.registrar({**base4, "event_type": "incubation_load",
                             "hatchery_params": [{"quantity_loaded": 800, "temperature": 37.6,
                                                  "humidity": 55, "co2": 0.4, "turning": True}]})
        print(f"  carga incubadora 800: {st}")
        print(f"  saldo tras carga: {u.saldo(lot4, incluye_load=True)} (esperado 200)")
        st, r = u.registrar({**base4, "event_type": "ovoscopy",
                             "egg_movements": [{"egg_type": "infertile", "quantity": 40}]})
        print(f"  ovoscopía: {st}")
        st, r = u.registrar({**base4, "event_type": "birth_registration",
                             "bird_movements": [{"sex": "mixed", "quantity": 800}],
                             "chicks_healthy": 780, "chicks_weak": 20})
        print(f"  nacimiento BR-21 (780 sanos + 20 débiles ≤ 800): {st}")
        st, r = u.registrar({**base4, "event_type": "chick_dispatch",
                             "bird_movements": [{"sex": "mixed", "quantity": 700}]})
        print(f"  despacho pollitos: {st}")

        # BR-03 · carga en exceso rechazada sin consumir.
        esc4b = escenario(u, "U4B", "hatchery")
        if esc4b["lot"]:
            lot4b, farm4b, house4b = esc4b["lot"]["id"], esc4b["farm"]["id"], esc4b["house"]["id"]
            base4b = {"lot_id": lot4b, "farm_id": farm4b, "house_id": house4b, "event_date": hoy()}
            st, _ = u.registrar({**base4b, "event_type": "egg_reception_hatchery",
                                 "egg_movements": [{"egg_type": "fertile", "quantity": 500}]})
            print(f"  BR-03 recepción 500: {st}")
            st, r = u.registrar({**base4b, "event_type": "incubation_load",
                                 "hatchery_params": [{"quantity_loaded": 501, "temperature": 37.6, "humidity": 55}]})
            print(f"  BR-03 carga 501: {st} · rule={r.get('rule') if isinstance(r, dict) else r} "
                  f"detail={detalle(r)}")
            print(f"  BR-03 saldo intacto: {u.saldo(lot4b, incluye_load=True)} (esperado 500)")
    else:
        print("  DEGRADED: no se pudo crear el lote U4")

    # ═════════════════════════════ U5 · ENGORDE Y CIERRE (P-06) ════════════════
    seccion("U5 · Engorde y cierre (P-06)")
    st, causas = u.get("/api/v1/masters/mortality-causes?limit=1")
    st2, descartes = u.get("/api/v1/masters/cull-causes?limit=1")
    st3, vacunas = u.get("/api/v1/masters/vaccines?limit=1")
    st4, meds = u.get("/api/v1/masters/medications?limit=1")
    st5, alimentos = u.get("/api/v1/masters/feed-types?limit=1")
    m = {
        "causa": causas[0]["id"] if (st == 200 and causas) else None,
        "descarte": descartes[0]["id"] if (st2 == 200 and descartes) else None,
        "vacuna": vacunas[0]["id"] if (st3 == 200 and vacunas) else None,
        "medicamento": meds[0]["id"] if (st4 == 200 and meds) else None,
        "alimento": alimentos[0]["id"] if (st5 == 200 and alimentos) else None,
    }
    print(f"  catálogos: {m}")

    def cadena_engorde(pref: str, aprobar: bool):
        esc = escenario(u, pref, "broiler")
        if not esc["lot"]:
            return None
        lot, farm, house = esc["lot"]["id"], esc["farm"]["id"], esc["house"]["id"]
        base = {"lot_id": lot, "farm_id": farm, "house_id": house, "event_date": hoy()}
        pasos = [
            ("farm_inspection", {"inspection_details": [{"parameter": "Bioseguridad", "value": "ok", "status": "ok"}]}),
            ("bird_reception", {"bird_movements": [{"sex": "mixed", "quantity": 5000}]}),
            ("bird_distribution", {"bird_movements": [{"sex": "mixed", "quantity": 5000}]}),
            ("feed_registration", {"feed_movements": [{"quantity_kg": 850.5, "feed_type_id": m["alimento"]}]}),
            ("weight_recording", {"bird_movements": [{"sex": "mixed", "quantity": 100, "avg_weight": 2400}]}),
            ("mortality_recording", {"bird_movements": [{"sex": "mixed", "quantity": 40, "mortality_cause_id": m["causa"]}]}),
            ("cull_recording", {"bird_movements": [{"sex": "mixed", "quantity": 15, "cull_cause_id": m["descarte"]}]}),
            ("vaccination", {"vaccine_id": m["vacuna"]}),
            ("medication", {"medication_id": m["medicamento"]}),
        ]
        ids, fallos = [], []
        for tipo, extra in pasos:
            stx, r = u.registrar({**base, "event_type": tipo, **extra})
            if stx != 201:
                fallos.append(f"{tipo}:{stx}")
            else:
                ids.append(r["id"])
        print(f"  {pref} eventos: {len(ids)}/9 registrados {('fallos=' + str(fallos)) if fallos else ''}")
        if aprobar and len(ids) == 9:
            for eid in ids:
                pasos_ap = u.aprobar(eid)
                ultimos = [p for p in pasos_ap if p[1] >= 300]
                if ultimos:
                    print(f"  {pref} aprobación evento {eid}: {ultimos}")
        return {"lot": lot, "ids": ids}

    cadena = cadena_engorde("U5", aprobar=True)
    if cadena:
        st, cierre = u.crear(f"/api/v1/lots/{cadena['lot']}/close", {})
        print(f"  cierre del lote: {st} · {detalle(cierre) if st != 200 else ''}")
        if st == 200 and isinstance(cierre, dict):
            print(f"  resumen: mortality={cierre.get('total_mortality')} feed_kg={cierre.get('total_feed_kg')} "
                  f"eventos={cierre.get('total_events')} status={cierre.get('status')} "
                  f"(esperado 40 / 850.5 / 9 / closed)")
            stx, lote = u.get(f"/api/v1/lots/{cadena['lot']}")
            print(f"  end_date persistida: {str(lote.get('end_date'))[:10]} status={lote.get('status')} "
                  f"(esperado {hoy()} closed)")
        # R7 · cadena sin aprobar no cierra.
        cadena7 = cadena_engorde("U5R7", aprobar=False)
        if cadena7:
            st, r = u.crear(f"/api/v1/lots/{cadena7['lot']}/close", {})
            print(f"  R7 cierre con eventos sin aprobar: {st} · rule={r.get('rule') if isinstance(r, dict) else r} "
                  f"(esperado 400 R7)")
    else:
        print("  DEGRADED: no se pudo montar la cadena U5")

    # ═══════════════════════ U7 · REPORTES Y TRAZABILIDAD ══════════════════════
    seccion("U7 · Reportes y trazabilidad (P-15/P-10/P-09)")
    if cadena:
        st, rep = u.get(f"/api/v1/reports/lot/{cadena['lot']}")
        print(f"  reporte de lote: {st} claves={sorted(rep.keys())[:14] if isinstance(rep, dict) else rep}")
        if isinstance(rep, dict):
            print(f"  fcr reportado: {rep.get('fcr')} · peso final: {rep.get('final_weight') or rep.get('avg_weight')}")
        st, kpi = u.get("/api/v1/reports/kpis/feed-conversion")
        print(f"  KPI conversión alimenticia: {st} · {str(kpi)[:200]}")
        st, ipe = u.get(f"/api/v1/reports/kpi/ipe/{cadena['lot']}")
        print(f"  IPE lote cerrado: {st} · {str(ipe)[:220]}")
        st, unif = u.get(f"/api/v1/reports/kpi/weight-uniformity/{cadena['lot']}")
        print(f"  uniformidad de peso: {st} · {str(unif)[:220]}")
    if esc4["lot"]:
        st, traza = u.get(f"/api/v1/lots/{esc4['lot']['id']}/traceability")
        claves = sorted(traza.keys())[:10] if isinstance(traza, dict) else traza
        print(f"  trazabilidad lote U4: {st} claves={claves}")
    sta, audit = u.get("/api/v1/audit?limit=5")
    print(f"  auditoría (rol operador): {sta} {detalle(audit)[:80]}")
    stn, cont = u.get("/api/v1/notifications/unread-count")
    print(f"  notificaciones: {stn} unread={cont.get('unread') if isinstance(cont, dict) else cont}")

    # ═══════════════════════ U8 · MAESTROS Y USUARIOS (P-12/P-11) ══════════════
    seccion("U8 · Maestros y usuarios (P-12/P-13/P-11/P-14)")
    s8 = suf()
    altas = [
        ("/api/v1/masters/feed-types", {"company_id": u.company, "name": f"U8-alimento-{s8}"}),
        ("/api/v1/masters/vaccines", {"company_id": u.company, "name": f"U8-vacuna-{s8}"}),
        ("/api/v1/masters/medications", {"company_id": u.company, "name": f"U8-medicamento-{s8}"}),
        ("/api/v1/masters/mortality-causes", {"company_id": u.company, "name": f"U8-causa-m-{s8}"}),
        ("/api/v1/masters/cull-causes", {"company_id": u.company, "name": f"U8-causa-d-{s8}"}),
        ("/api/v1/masters/genetic-lines", {"company_id": u.company, "name": f"U8-linea-{s8}"}),
        ("/api/v1/masters/suppliers", {"company_id": u.company, "name": f"U8-prov-{s8}",
                                       "country": "Francia", "supplier_type": "international"}),
        ("/api/v1/masters/transports", {"company_id": u.company, "name": f"U8-trans-{s8}",
                                        "plate": f"U8-{s8}"}),
    ]
    for ruta, cuerpo in altas:
        st, r = u.crear(ruta, cuerpo)
        print(f"  alta {ruta.split('/')[-1]}: {st}")

    # Activación manual (OD-10.c) con fase inicial.
    st, fases = u.get("/api/v1/masters/productive-phases")
    fase = None
    if st == 200 and isinstance(fases, list) and fases:
        fase = next((f for f in fases if f.get("is_initial")), fases[0])
    else:
        stc, f = u.crear("/api/v1/masters/productive-phases", {
            "name": f"U8-Cría-{s8}", "code": f"U8-{s8}", "order": 1, "duration_days": 140, "is_initial": True,
        })
        print(f"  fase inicial creada: {stc}")
        if stc == 201:
            fase = f
    esc8 = escenario(u, "U8", "breeder", start_days=140)
    if esc8["lot"] and fase:
        st, r = u.crear("/api/v1/lots/activate-manual", {
            "lot_id": esc8["lot"]["id"], "activation_date": hoy(-140),
            "phase_at_activation_id": fase["id"], "initial_male_count": 4000,
            "initial_female_count": 1000, "activation_reason": "Lote existente antes de la implantación",
            "support_document_url": "https://ejemplo.invalid/soporte.pdf",
        })
        print(f"  activación manual OD-10.c: {st} · {detalle(r) if st != 201 else 'creada'}")
        stx, ob = u.get(f"/api/v1/lots/{esc8['lot']['id']}/opening-balance")
        print(f"  balance de apertura: {stx} · {str(ob)[:120] if stx == 200 else detalle(ob)}")
        st2, r2 = u.crear("/api/v1/lots/activate-manual", {
            "lot_id": esc8["lot"]["id"], "activation_date": hoy(-140),
            "phase_at_activation_id": fase["id"], "initial_male_count": 4000,
            "initial_female_count": 1000, "activation_reason": "reintento",
            "support_document_url": "https://ejemplo.invalid/soporte.pdf",
        })
        print(f"  segunda activación (idempotencia del flujo): {st2} · {detalle(r2)}")
    else:
        print(f"  DEGRADED activación: lote={bool(esc8['lot'])} fase={bool(fase)}")

    print("\n== FIN U3–U8 ==")


if __name__ == "__main__":
    main()

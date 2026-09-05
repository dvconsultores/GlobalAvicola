#!/usr/bin/env python
"""Arranque limpio: estados vacíos y primer flujo de negocio.

Entregable de `GA-REM-025` `AC13` y `AC14` (encargo §56 y §57).

Recorre, contra una base **sin ninguna historia de negocio**, el camino que hará el primer
cliente real:

    login → pantallas vacías → primeros maestros → primer lote → primera operación → saldo

Si algo del sistema dependiese en secreto de datos que un seed antiguo dejó puestos, aquí
es donde se rompería. Habla con la API por HTTP, como lo haría el frontend.
"""
from __future__ import annotations

import os
import secrets
import sys

import base64
import json
import time

import httpx

BASE = os.environ.get("GA_FLOW_BASE_URL", "http://127.0.0.1:8111")
USUARIO = os.environ.get("GA_FLOW_USER", "admin")
CLAVE = os.environ["GA_FLOW_PASSWORD"]

fallos: list[str] = []
pasos: list[tuple[str, str]] = []


def registrar(nombre: str, ok: bool, detalle: str = "") -> bool:
    pasos.append(("✅" if ok else "❌", f"{nombre}{f' — {detalle}' if detalle else ''}"))
    if not ok:
        fallos.append(nombre)
    return ok


def main() -> int:
    with httpx.Client(base_url=BASE, timeout=30) as c:
        # ── Autenticación ─────────────────────────────────────────────────────
        r = c.post("/api/v1/login", json={"username": USUARIO, "password": CLAVE})
        if not registrar("login del administrador", r.status_code == 200, f"HTTP {r.status_code}"):
            informe()
            return 1
        cab = {"Authorization": f"Bearer {r.json()['access_token']}"}

        # ── AC13 · estados vacíos ─────────────────────────────────────────────
        # Ninguna pantalla puede reventar porque no haya datos todavía.
        vacias = [
            ("lotes", "/api/v1/lots"),
            ("operaciones", "/api/v1/operations"),
            ("alertas", "/api/v1/operations/alerts"),
            ("panel", "/api/v1/dashboard/admin"),
            ("granjas", "/api/v1/masters/farms"),
            ("galpones", "/api/v1/masters/houses"),
            ("revisión", "/api/v1/review/batches"),
            ("aprobaciones pendientes", "/api/v1/approvals/pending"),
            ("auditoría", "/api/v1/audit"),
        ]
        for nombre, ruta in vacias:
            r = c.get(ruta, headers=cab)
            # 404 significa que la ruta no existe; se informa aparte para no confundirlo
            # con un fallo de estado vacío.
            ok = r.status_code < 500 and r.status_code != 404
            registrar(f"estado vacío · {nombre}", ok, f"HTTP {r.status_code}")

        # ── AC14 · primer flujo de negocio ────────────────────────────────────
        empresa = c.get("/api/v1/masters/companies", headers=cab).json()
        if not registrar("existe una empresa donde operar", bool(empresa)):
            informe()
            return 1
        company_id = empresa[0]["id"]

        # ── §39 · R-48 / R-54 sobre base limpia ───────────────────────────────
        # El único usuario de una instalación nueva es un Super Administrador sin empresa.
        # Para operar tiene que situarse en una: es el camino que `switch-company` existe
        # para cubrir, y conviene comprobarlo aquí porque si fallara, una instalación
        # recién hecha sería inoperable y nadie lo notaría hasta el primer cliente.
        r = c.post("/api/v1/switch-company", headers=cab, json={"company_id": company_id})
        if not registrar("R-48 · situarse en la empresa", r.status_code == 200,
                         f"HTTP {r.status_code} {r.text[:140]}"):
            informe()
            return 1
        cab = {"Authorization": f"Bearer {r.json()['access_token']}"}

        # La comprobación es sobre el token, no sobre `/me`: `/me` devuelve la empresa
        # **persistida** del usuario —nula para un Super Administrador— mientras que la
        # empresa **activa** vive en el token. El frontend hace lo mismo
        # (`company.store.ts:56`), así que medir `/me` mediría la cosa equivocada.
        carga = cab["Authorization"].split(".")[1]
        carga += "=" * (-len(carga) % 4)
        claims = json.loads(base64.urlsafe_b64decode(carga))
        registrar("R-54 · el token queda alcanzado a la empresa",
                  int(claims.get("company_id", -1)) == company_id,
                  f"company_id del token = {claims.get('company_id')}")

        yo = c.get("/api/v1/me", headers=cab)
        registrar("el perfil se lee sin error", yo.status_code == 200, f"HTTP {yo.status_code}")

        def crear(nombre: str, ruta: str, cuerpo: dict) -> int | None:
            r = c.post(ruta, headers=cab, json=cuerpo)
            if not registrar(f"crear {nombre}", r.status_code == 201, f"HTTP {r.status_code} {r.text[:120]}"):
                return None
            return r.json()["id"]

        farm_id = crear("granja", "/api/v1/masters/farms", {
            "company_id": company_id, "name": "FLOW-Granja 1", "code": "FLOW-G1",
            "location": "Primer flujo", "farm_type": "breeding",
        })
        if farm_id is None:
            informe()
            return 1

        house_id = crear("galpón", "/api/v1/masters/houses", {
            "farm_id": farm_id, "name": "FLOW-Galpón 1", "capacity": 5000,
        })
        linea_id = crear("línea genética", "/api/v1/masters/genetic-lines", {
            "company_id": company_id, "name": "FLOW-Línea", "code": "FLOW-L1",
        })
        raza_id = crear("raza", "/api/v1/masters/breeds", {
            "genetic_line_id": linea_id, "name": "FLOW-Raza",
        }) if linea_id else None
        causa_id = crear("causa de mortalidad", "/api/v1/masters/mortality-causes", {
            "company_id": company_id, "name": "FLOW-Causa",
        })

        lote = c.post("/api/v1/lots", headers=cab, json={
            "company_id": company_id, "farm_id": farm_id, "house_id": house_id,
            "genetic_line_id": linea_id, "breed_id": raza_id,
            "lot_code": "FLOW-LOTE-001", "bird_type": "breeder", "sex": "mixed",
        })
        if not registrar("crear primer lote", lote.status_code == 201,
                         f"HTTP {lote.status_code} {lote.text[:160]}"):
            informe()
            return 1
        lot_id = lote.json()["id"]

        # Saldo de apertura: sin él no hay población contra la que descontar.
        fases = c.get("/api/v1/masters/productive-phases", headers=cab).json()
        fase_inicial = next((f for f in fases if f.get("is_initial")), fases[0] if fases else None)
        registrar("existe la fase productiva inicial", fase_inicial is not None)
        apertura = c.post("/api/v1/lots/activate-manual", headers=cab, json={
            "lot_id": lot_id, "activation_date": "2026-09-01",
            "phase_at_activation_id": fase_inicial["id"] if fase_inicial else None,
            "initial_male_count": 1000, "initial_female_count": 4000,
        })
        registrar("activar lote con saldo de apertura",
                  apertura.status_code in (200, 201),
                  f"HTTP {apertura.status_code} {apertura.text[:160]}")

        # ── R-67 · el saldo de apertura no alimenta el saldo de aves ──────────
        # `activate-manual` guarda 5.000 aves, pero `get_current_bird_balance` solo suma
        # movimientos de eventos de entrada y no consulta `opening_balances`. Se comprueba
        # explícitamente para que el hallazgo quede medido y no se olvide.
        sonda = c.post("/api/v1/operations", headers=cab, json={
            "lot_id": lot_id, "farm_id": farm_id, "house_id": house_id,
            "event_type": "mortality_recording", "event_date": "2026-09-02",
            "cause_id": causa_id,
            "bird_movements": [{"sex": "male", "quantity": 1, "source_house_id": house_id}],
        })
        saldo_apertura_cuenta = sonda.status_code == 201
        registrar(
            "R-67 · el saldo de apertura alimenta el saldo de aves",
            saldo_apertura_cuenta,
            "no: un lote activado manualmente rechaza toda mortalidad "
            f"(HTTP {sonda.status_code})" if not saldo_apertura_cuenta else "",
        )

        # ── AC14 · primer flujo por el camino soportado ───────────────────────
        recepcion = c.post("/api/v1/operations", headers=cab, json={
            "lot_id": lot_id, "farm_id": farm_id, "house_id": house_id,
            "event_type": "bird_reception", "event_date": "2026-09-01",
            "observations": "Primera recepción del entorno limpio",
            "bird_movements": [
                {"sex": "male", "quantity": 1000, "target_house_id": house_id},
                {"sex": "female", "quantity": 4000, "target_house_id": house_id},
            ],
        })
        if not registrar("registrar primera recepción de aves", recepcion.status_code == 201,
                         f"HTTP {recepcion.status_code} {recepcion.text[:200]}"):
            informe()
            return 1

        evento = c.post("/api/v1/operations", headers=cab, json={
            "lot_id": lot_id, "farm_id": farm_id, "house_id": house_id,
            "event_type": "mortality_recording", "event_date": "2026-09-02",
            "cause_id": causa_id, "observations": "Primer registro del entorno limpio",
            "bird_movements": [
                {"sex": "male", "quantity": 5, "source_house_id": house_id},
                {"sex": "female", "quantity": 7, "source_house_id": house_id},
            ],
        })
        if not registrar("registrar primera mortalidad", evento.status_code == 201,
                         f"HTTP {evento.status_code} {evento.text[:200]}"):
            informe()
            return 1
        event_id = evento.json()["id"]

        detalle = c.get(f"/api/v1/operations/{event_id}", headers=cab)
        registrar("releer la operación", detalle.status_code == 200, f"HTTP {detalle.status_code}")

        # El saldo derivado debe ser 5.000 recibidas − 12 muertas.
        listado = c.get("/api/v1/operations", headers=cab, params={"lot_id": lot_id})
        # La recepción y la mortalidad, más la sonda de R-67 si el saldo de apertura
        # alimenta el balance: con R-67 resuelto esa sonda es una operación real.
        esperados = 3 if saldo_apertura_cuenta else 2
        registrar(f"las operaciones aparecen en el lote ({esperados})",
                  listado.status_code == 200 and len(listado.json()) == esperados,
                  f"HTTP {listado.status_code}, "
                  f"{len(listado.json()) if listado.status_code == 200 else '-'} eventos")

        lote_detalle = c.get(f"/api/v1/lots/{lot_id}", headers=cab)
        registrar("releer el lote con su historia", lote_detalle.status_code == 200,
                  f"HTTP {lote_detalle.status_code}")

        # ── §40 / §41 · aislamiento entre tenants sobre datos recién creados ──
        # El sujeto NO puede ser el Super Administrador: `masters/service.py:35` lo exime
        # del filtro por empresa a propósito, de modo que probar el aislamiento con él
        # mediría lo contrario de lo que se quiere medir. Se crean dos usuarios de tenant.
        #
        # Nada se apoya en historia previa: la granja y el lote de A acaban de crearse en
        # esta misma ejecución.
        empresas = c.get("/api/v1/masters/companies", headers=cab).json()
        otra = next((e for e in empresas if e["id"] != company_id), None)
        if otra is None:
            registrar("existe un segundo tenant para probar aislamiento", False)
            informe()
            return 1

        roles = c.get("/api/v1/roles", headers=cab).json()
        rol_operador = next((r for r in roles if r["name"] == "Operador de Granja"), None)
        if not registrar("existe el rol de operador", rol_operador is not None):
            informe()
            return 1

        # Generada por ejecución; el usuario que la lleva vive solo durante la prueba.
        CLAVE_TENANT = os.environ.get("GA_FIXTURE_PASSWORD") or secrets.token_urlsafe(16)

        def crear_usuario(sufijo: str, cid: int) -> str | None:
            r = c.post("/api/v1/users", headers=cab, json={
                "first_name": "Flow", "last_name": sufijo,
                "email": f"flow.{sufijo.lower()}@fixtures.globalavicola.com",
                "username": f"flow_{sufijo.lower()}",
                "password": CLAVE_TENANT, "role_id": rol_operador["id"],
                "company_id": cid, "view_type": "web",
            })
            if not registrar(f"crear usuario de tenant {sufijo}", r.status_code == 201,
                             f"HTTP {r.status_code} {r.text[:120]}"):
                return None
            return f"flow_{sufijo.lower()}"

        usuario_b = crear_usuario("B", otra["id"])
        if usuario_b is None:
            informe()
            return 1

        # ── R-68 · la escritura no es visible para la petición inmediata ──────
        # `get_db` confirma en el cierre de la dependencia, que FastAPI ejecuta después de
        # enviar la respuesta. Un cliente que actúe sobre el 201 al instante puede no ver
        # todavía la fila. Se mide explícitamente y luego se espera, para que un defecto
        # ya conocido no bloquee el resto de la certificación.
        inmediato = c.post("/api/v1/login", json={"username": usuario_b, "password": CLAVE_TENANT})
        registrar("R-68 · el alta es visible para la petición inmediata",
                  inmediato.status_code == 200,
                  "" if inmediato.status_code == 200 else
                  f"no: login inmediato HTTP {inmediato.status_code} tras un alta con 201")

        if inmediato.status_code == 200:
            r = inmediato
        else:
            time.sleep(1)
            r = c.post("/api/v1/login", json={"username": usuario_b, "password": CLAVE_TENANT})
        if not registrar("el usuario del tenant B entra", r.status_code == 200,
                         f"HTTP {r.status_code}"):
            informe()
            return 1
        cab_b = {"Authorization": f"Bearer {r.json()['access_token']}"}

        granjas_b = c.get("/api/v1/masters/farms", headers=cab_b)
        registrar("R-59 · B no ve las granjas de A",
                  granjas_b.status_code == 200 and not granjas_b.json(),
                  f"HTTP {granjas_b.status_code}, "
                  f"{len(granjas_b.json()) if granjas_b.status_code == 200 else '-'} granjas")

        lotes_b = c.get("/api/v1/lots", headers=cab_b)
        registrar("R-59 · B no ve los lotes de A",
                  lotes_b.status_code == 200 and not lotes_b.json(),
                  f"HTTP {lotes_b.status_code}, "
                  f"{len(lotes_b.json()) if lotes_b.status_code == 200 else '-'} lotes")

        detalle_cruzado = c.get(f"/api/v1/lots/{lot_id}", headers=cab_b)
        registrar("R-59 · B no lee el lote de A por id directo",
                  detalle_cruzado.status_code in (403, 404),
                  f"HTTP {detalle_cruzado.status_code}")

        operaciones_b = c.get("/api/v1/operations", headers=cab_b)
        registrar("R-59 · B no ve las operaciones de A",
                  operaciones_b.status_code == 200 and not operaciones_b.json(),
                  f"HTTP {operaciones_b.status_code}, "
                  f"{len(operaciones_b.json()) if operaciones_b.status_code == 200 else '-'} eventos")

        # Que la lectura esté filtrada no implica que la escritura lo esté: son controles
        # distintos y hay que comprobarlos por separado.
        cruzada = c.post("/api/v1/operations", headers=cab_b, json={
            "lot_id": lot_id, "farm_id": farm_id, "house_id": house_id,
            "event_type": "mortality_recording", "event_date": "2026-09-03",
            "bird_movements": [{"sex": "male", "quantity": 1, "source_house_id": house_id}],
        })
        registrar("R-42 · escritura de B sobre el lote de A denegada",
                  cruzada.status_code in (400, 403, 404),
                  f"HTTP {cruzada.status_code} {cruzada.text[:120]}")

    informe()
    return 1 if fallos else 0


def informe() -> None:
    print("\n── Arranque limpio: estados vacíos y primer flujo ──")
    for marca, texto in pasos:
        print(f"  {marca} {texto}")
    print(f"── {len(pasos) - len(fallos)}/{len(pasos)} pasos correctos ──")


if __name__ == "__main__":
    sys.exit(main())

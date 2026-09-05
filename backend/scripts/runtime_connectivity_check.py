#!/usr/bin/env python
"""Gate de conectividad de ejecución — `GA-REM-027`.

Comprueba por separado los tres niveles de salud, porque confundirlos fue exactamente lo
que dejó pasar dos incidentes:

    L2  host → backend        el contenedor escucha y responde
    L3  proxy público → API   la cadena completa funciona

    HTML   la SPA             NO es evidencia de nada sobre el backend

El hueco que este gate cubre: `startup_test.sh` certifica que el backend arranca, y lo hace
bien, pero llama al backend directamente. Entre «el backend arranca» y «la API responde»
está el proxy, y ninguna prueba lo recorría. El 2026-09-05 eso costó ocho horas de API
inalcanzable con el backend perfectamente sano.

    uso:  python -m scripts.runtime_connectivity_check \
              --public https://avicola.globaldv.net \
              [--direct http://84.247.161.106:8002]

`--direct` es opcional: solo es alcanzable si el backend publica su puerto al host.

No autentica, no escribe nada y no toca la base de datos. Es seguro contra cualquier
entorno.
"""
from __future__ import annotations

import argparse
import sys

import httpx

#: Ruta pública que devuelve JSON sin autenticar. Sirve para comprobar que el proxy llega
#: al backend y que el URI se transmite íntegro.
SONDA_API = "/api/v1/operations/event-types"

#: Ruta que un cliente sin sesión debe encontrar protegida. Un 401 demuestra que la
#: respuesta viene del backend y no de una página de error del proxy.
SONDA_PROTEGIDA = "/api/v1/me"


def _linea(marca: str, texto: str) -> None:
    print(f"  {marca} {texto}")


def comprobar(publico: str, directo: str | None) -> int:
    fallos = 0

    with httpx.Client(timeout=25, follow_redirects=False) as c:
        # ── L2 · host → backend ───────────────────────────────────────────────
        if directo:
            print("── L2 · host → backend ──")
            try:
                r = c.get(f"{directo}/health")
                tipo = r.headers.get("content-type", "")
                ok = r.status_code == 200 and "json" in tipo
                _linea("✅" if ok else "❌", f"/health → {r.status_code} {tipo}")
                if ok:
                    _linea("  ", r.text[:120])
                else:
                    fallos += 1
            except Exception as exc:  # noqa: BLE001
                _linea("❌", f"/health inalcanzable: {type(exc).__name__}")
                fallos += 1
        else:
            print("── L2 · host → backend ── (omitido: sin --direct)")

        # ── L3 · proxy público → API ──────────────────────────────────────────
        print("── L3 · proxy público → API ──")
        try:
            r = c.get(f"{publico}{SONDA_API}")
            tipo = r.headers.get("content-type", "")
            ok = r.status_code == 200 and "json" in tipo
            _linea("✅" if ok else "❌", f"{SONDA_API} → {r.status_code} {tipo}")
            if ok:
                _linea("  ", f"{len(r.json())} tipos de evento")
            else:
                fallos += 1
                if r.status_code == 502:
                    _linea("  ", "502: el proxy no alcanza el backend "
                                 "— compare con L2 antes de culpar a la aplicación")
        except Exception as exc:  # noqa: BLE001
            _linea("❌", f"{SONDA_API} inalcanzable: {type(exc).__name__}")
            fallos += 1

        try:
            r = c.get(f"{publico}{SONDA_PROTEGIDA}")
            ok = r.status_code == 401
            _linea("✅" if ok else "❌",
                   f"{SONDA_PROTEGIDA} → {r.status_code} (se espera 401: contesta el backend)")
            if not ok:
                fallos += 1
        except Exception as exc:  # noqa: BLE001
            _linea("❌", f"{SONDA_PROTEGIDA} inalcanzable: {type(exc).__name__}")
            fallos += 1

        # ── La SPA no es evidencia ────────────────────────────────────────────
        print("── control · la SPA no dice nada del backend ──")
        try:
            r = c.get(f"{publico}/health")
            tipo = r.headers.get("content-type", "")
            es_html = "html" in tipo
            _linea("ℹ️ ", f"/health → {r.status_code} {tipo}"
                          f"{'  ← es la SPA, NO el backend' if es_html else ''}")
            if es_html and r.status_code == 200:
                _linea("  ", "un 200 aquí no prueba nada: la SPA responde aunque "
                             "el backend no exista")
        except Exception as exc:  # noqa: BLE001
            _linea("ℹ️ ", f"/health: {type(exc).__name__}")

    print()
    if fallos:
        print(f"── CONECTIVIDAD: {fallos} fallo(s) ──")
    else:
        print("── CONECTIVIDAD: todos los niveles en verde ──")
    return 1 if fallos else 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--public", required=True, help="URL pública del entorno")
    p.add_argument("--direct", help="URL directa al backend, si publica su puerto al host")
    args = p.parse_args()
    return comprobar(args.public.rstrip("/"), args.direct.rstrip("/") if args.direct else None)


if __name__ == "__main__":
    raise SystemExit(main())

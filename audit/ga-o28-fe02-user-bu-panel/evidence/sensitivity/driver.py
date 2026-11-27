#!/usr/bin/env python3
"""O-28 · sensibilidad y falso verde (§22-23), DESPUÉS del commit de implementación.

Uso (desde la raíz del repo): python3 audit/ga-o28-fe02-user-bu-panel/evidence/sensitivity/driver.py <IMPL_SHA>
Cada variante se aplica en el árbol, se corre la campaña y se restaura con
`git restore --source=<IMPL_SHA> -- <archivo>` (restauración explícita por SHA). Las pausas de S2/S3
son TEMPORALES (simulan una red lenta) y nunca se commitean.
"""
import json, subprocess, sys
from pathlib import Path

SHA = sys.argv[1]
RAIZ = Path.cwd()
EV = RAIZ / "audit/ga-o28-fe02-user-bu-panel/evidence"
CAMP = EV / "campaign.sh"
F1 = "frontend/src/pages/users/__tests__/gaFe02.userBuPanel.test.tsx"
F2 = "frontend/src/pages/users/__tests__/uatAdminRbac.userBuPanel.test.tsx"
ARCH = [F1, F2]

SIN_ESPERA = ("  await esperarCargaDelPanel()\n}", "}")
UNITS_OK = "if (url === '/business-units') return Promise.resolve({ data: UNITS })"
UNITS_LENTO = "if (url === '/business-units') return new Promise(r => setTimeout(() => r({ data: UNITS }), 20))"
UNITS_VACIO = "if (url === '/business-units') return Promise.resolve({ data: [] })"

VARIANTES = [
    # (id, descripción, reemplazos, corridas, esperado)
    ("S1", "patrón defectuoso reintroducido (openPanel sin esperar la carga), red instantánea",
     [SIN_ESPERA], 20, "FALLA_ALGUNA", "file"),
    ("S1b", "patrón defectuoso reintroducido, red instantánea, subsuite SPEC 013 / GA-FE-02 (como en la reproducción C)",
     [SIN_ESPERA], 10, "FALLA_ALGUNA", "suite"),
    ("S2", "patrón defectuoso + respuesta de unidades diferida 20 ms (red lenta)",
     [SIN_ESPERA, (UNITS_OK, UNITS_LENTO)], 5, "FALLA_SIEMPRE", "file"),
    ("S3", "CONTROL: patrón nuevo + respuesta diferida 20 ms (debe pasar)",
     [(UNITS_OK, UNITS_LENTO)], 5, "PASA_SIEMPRE", "file"),
    ("S4", "falso verde: la API devuelve [] unidades",
     [(UNITS_OK, UNITS_VACIO)], 3, "FALLA_SIEMPRE", "file"),
]


def sh(cmd):
    return subprocess.run(cmd, shell=True, cwd=RAIZ, capture_output=True, text=True)


def restaurar():
    sh(f"git restore --source={SHA} -- {' '.join(ARCH)}")
    sucio = sh(f"git status --short -- {' '.join(ARCH)}").stdout.strip()
    if sucio:
        sys.exit(f"RESTAURACIÓN FALLIDA: {sucio}")


def aplicar(reemplazos):
    for ruta in ARCH:
        p = RAIZ / ruta
        s = p.read_text(encoding="utf-8")
        for viejo, nuevo in reemplazos:
            n = s.count(viejo)
            if n < 1:
                restaurar()
                sys.exit(f"{ruta}: no aparece {viejo[:60]!r}")
            s = s.replace(viejo, nuevo)
        p.write_text(s, encoding="utf-8")


restaurar()
lineas = [f"IMPL_SHA={SHA}"]
SOLO = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
for vid, desc, reemplazos, n, esperado, modo in VARIANTES:
    if SOLO and vid not in SOLO:
        continue
    aplicar(reemplazos)
    sh(f"bash {CAMP} sens_{vid} {n} {modo}")
    restaurar()
    corridas = sorted((EV / f"runs/sens_{vid}").glob("run_*.json"))
    con_fallo = 0; tests_fallidos = set()
    for c in corridas:
        j = json.loads(c.read_text())
        if j["numFailedTests"] > 0:
            con_fallo += 1
        for tf in j["testResults"]:
            for a in tf["assertionResults"]:
                if a["status"] == "failed":
                    tests_fallidos.add(f'{Path(tf["name"]).name} › {a["title"]}')
    ok = {"FALLA_ALGUNA": con_fallo >= 1, "FALLA_SIEMPRE": con_fallo == len(corridas),
          "PASA_SIEMPRE": con_fallo == 0}[esperado]
    lineas.append(f"[{vid}] {'OK' if ok else 'NO_CUMPLE'} · {desc} · esperado={esperado} · corridas con fallo={con_fallo}/{len(corridas)}")
    for t in sorted(tests_fallidos):
        lineas.append(f"      falla: {t}")
lineas.append("TREE=" + ("CLEAN" if not sh("git status --short -- frontend").stdout.strip() else "DIRTY"))
(EV / f"sensitivity/resultado{'_' + '_'.join(sorted(SOLO)) if SOLO else ''}.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
print("\n".join(lineas))

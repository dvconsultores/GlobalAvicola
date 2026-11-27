"""GA-HATCHERY-V4-BR03-UNKNOWN-FAILSAFE · SPEC 018 §10 — sensibilidad por mutación.

Se ejecuta desde la raíz del repositorio DESPUÉS del commit de implementación. Cada mutante es un
reemplazo literal (debe aparecer exactamente una vez); se corre la batería dirigida y el archivo
se restaura con `git restore --source=<SHA> -- <archivo>` (restauración explícita por SHA).
Un mutante está MUERTO si la batería falla. Solo se guarda el resumen de cada corrida (sin DSN).
Derivado del driver de `ga-uat-breeder-cria-s2-owner-decisions-2026-11-25`.

Uso: python3 audit/.../mutation/driver.py [backend|frontend|all] [ID,ID,...]
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path.cwd()
SALIDA = Path(__file__).resolve().parent
NODE = os.path.expanduser("~/.nvm/versions/node/v20.20.2/bin")

BACKEND_TESTS = [
    "tests/test_cutover_hatchery_v4_br03_unknown.py",
    "tests/test_cutover_hatchery_v4_od02.py",
    "tests/test_cutover_hatchery_v4.py",
]
FRONTEND_TESTS = []

K = "backend/app/cutover/saldo_incubadora.py"
O = "backend/app/operations/validators.py"
C = "backend/app/cutover/opening_corrections.py"

MUTANTES = [
    # ── mandato §23 ──
    ("M1", "backend", "§23.1 fosa UNKNOWN tratada como 0", K,
     "    componentes = [valores.get(campo) for campo in COMPONENTES_PRE_CARGA]",
     "    componentes = [(valores.get(campo) or 0) if campo == \"fertile_eggs_to_pit\" else valores.get(campo)\n"
     "                   for campo in COMPONENTES_PRE_CARGA]"),
    ("M2", "backend", "§23.2 sucio UNKNOWN tratado como 0", K,
     "    componentes = [valores.get(campo) for campo in COMPONENTES_PRE_CARGA]",
     "    componentes = [(valores.get(campo) or 0) if campo == \"eggs_non_incubable_dirty\" else valores.get(campo)\n"
     "                   for campo in COMPONENTES_PRE_CARGA]"),
    ("M3", "backend", "§23.3 la suma conocida se usa como saldo exacto", K,
     "    if any(valor is None for valor in componentes):\n        return None\n    return recibidos - cargados - sum(componentes)",
     "    return recibidos - cargados - sum(valor for valor in componentes if valor is not None)"),
    ("M4", "backend", "§23.4 se elimina el bloqueo de BR-03 por saldo UNKNOWN", O,
     "    if balance is None:\n        # SPEC 018 §10",
     "    if balance is None and False:\n        # SPEC 018 §10"),
    ("M5", "backend", "§23.5 el 0 conocido se trata como UNKNOWN", K,
     "    if any(valor is None for valor in componentes):",
     "    if any(not valor for valor in componentes):"),
    # ── adicionales ──
    ("M6", "backend", "la guarda de retiro de entrada ignora el saldo UNKNOWN", O,
     "        if saldo is None:\n            # SPEC 018 §10",
     "        if saldo is None and False:\n            # SPEC 018 §10"),
    ("M7", "backend", "la corrección gobernada deja una apertura imposible", C,
     "        if recibidos is not None and (nuevo > recibidos or conocidos > recibidos):",
     "        if False:"),
    ("M8", "backend", "la corrección no marca el componente como KNOWN", C,
     '        setattr(apertura, f"{data.field}_status", KNOWN)\n', ""),
    ("M9", "backend", "V3 histórica tratada como V4 (se bloquearía)", K,
     '    return version != "v3" if version is not None else True', "    return True"),
]


def sh(cmd, cwd=None, env=None, timeout=3600):
    p = subprocess.run(cmd, shell=True, cwd=cwd or RAIZ, env=env, capture_output=True, text=True,
                       timeout=timeout)
    return p.returncode, p.stdout + p.stderr


def resumen(texto, capa):
    lineas = texto.splitlines()
    if capa == "backend":
        sel = [l for l in lineas if re.search(r"=+ .*(passed|failed|error).* in [0-9.]+s", l)]
        sel += [l for l in lineas if l.startswith("FAILED ")][:15]
    else:
        sel = [l for l in lineas if re.search(r"^\s*(Test Files|Tests)\s", l)]
        sel += [l.strip() for l in lineas if re.search(r"^\s*(×|FAIL)\s", l)][:15]
    limpio = [re.sub(r"postgres(ql)?(\+\w+)?://\S+", "<DSN>", l) for l in sel]
    return "\n".join(limpio)


def correr(capa):
    if capa == "backend":
        return sh("bash backend/scripts/run_tests.sh " + " ".join(BACKEND_TESTS), timeout=3600)
    env = dict(os.environ, PATH=f"{NODE}:{os.environ['PATH']}")
    return sh("npx vitest run " + " ".join(FRONTEND_TESTS), cwd=RAIZ / "frontend", env=env, timeout=1800)


def main():
    capas = {"backend", "frontend"} if (len(sys.argv) < 2 or sys.argv[1] == "all") else {sys.argv[1]}
    sha = sh("git rev-parse HEAD")[1].strip()
    sucios = sh("git status --short -- backend/app frontend/src")[1].strip()
    if sucios:
        sys.exit(f"árbol sucio en código de producto, abortado:\n{sucios}")
    resultados_path = SALIDA / "results.json"
    resultados = json.loads(resultados_path.read_text()) if resultados_path.exists() else {}
    resultados.setdefault("_meta", {})["sha_restauracion"] = sha

    for capa in sorted(capas):
        rc, out = correr(capa)
        resultados["_meta"][f"linea_base_{capa}"] = {"rc": rc, "resumen": resumen(out, capa)}
        print(f"[BASE {capa}] rc={rc}\n{resumen(out, capa)}", flush=True)
        if rc != 0:
            resultados_path.write_text(json.dumps(resultados, indent=2, ensure_ascii=False))
            sys.exit(f"línea base {capa} en rojo: abortado")

    solo = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    for mid, capa, desc, archivo, viejo, nuevo in MUTANTES:
        if capa not in capas or (solo and mid not in solo):
            continue
        ruta = RAIZ / archivo
        texto = ruta.read_text(encoding="utf-8")
        n = texto.count(viejo)
        if n != 1:
            resultados[mid] = {"capa": capa, "descripcion": desc, "archivo": archivo,
                               "estado": "NO_APLICABLE", "apariciones": n}
            print(f"[{mid}] NO_APLICABLE ({n} apariciones)", flush=True)
            continue
        ruta.write_text(texto.replace(viejo, nuevo), encoding="utf-8")
        t0 = time.time()
        try:
            rc, out = correr(capa)
        finally:
            sh(f"git restore --source={sha} -- {archivo}")
        assert not sh(f"git status --short -- {archivo}")[1].strip(), f"{archivo} no quedó restaurado"
        estado = "MUERTO" if rc != 0 else "SOBREVIVE"
        resultados[mid] = {"capa": capa, "descripcion": desc, "archivo": archivo, "estado": estado,
                           "rc": rc, "segundos": round(time.time() - t0), "resumen": resumen(out, capa)}
        resultados_path.write_text(json.dumps(resultados, indent=2, ensure_ascii=False))
        print(f"[{mid}] {estado} · {desc}", flush=True)

    resultados_path.write_text(json.dumps(resultados, indent=2, ensure_ascii=False))
    vivos = [k for k, v in resultados.items() if not k.startswith("_") and v.get("estado") != "MUERTO"]
    print("SOBREVIVIENTES / NO APLICABLES:", vivos or "ninguno", flush=True)


if __name__ == "__main__":
    main()

"""GA-HATCHERY-V4-PIT-PRELOAD-DOMAIN-CORRECTION · SPEC 018 §9 (OD-HATCH-V4-02) — sensibilidad por mutación.

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
    "tests/test_cutover_hatchery_v4_od02.py",
    "tests/test_cutover_hatchery_v4.py",
    "tests/test_cutover_hatchery_v4_o15.py",
]
FRONTEND_TESTS = [
    "src/__tests__/cutoverHatcheryV4.test.tsx",
]

V = "backend/app/cutover/validation.py"
S = "backend/app/cutover/service.py"
O = "backend/app/operations/validators.py"
P = "frontend/src/pages/cutover/CargasInicialesPage.tsx"
ES = "frontend/public/locales/es/translation.json"

MUTANTES = [
    # ── mandato §33 ──
    ("M1", "backend", "§33.1 la fosa vuelve a restarse de eggs_in_process (derivado)", V,
     '                derivados["eggs_in_process"] = _val(fila, "eggs_set") - _val(fila, "eggs_transferred")\n',
     '                derivados["eggs_in_process"] = (_val(fila, "eggs_set") - _val(fila, "eggs_transferred")\n'
     '                                               - (_val(fila, "fertile_eggs_to_pit") or 0))\n'),
    ("M2", "backend", "§33.2 se elimina la fosa de la ecuación pre-carga", V,
     '_SALIDAS_PRE_CARGA = _NO_INCUBABLES + ("fertile_eggs_to_pit",)', '_SALIDAS_PRE_CARGA = _NO_INCUBABLES'),
    ("M3", "backend", "§33.3 `<=` pasa a `<` (la igualdad se rechaza)", V,
     "                if acumulado > recibidos:", "                if acumulado >= recibidos:"),
    ("M4", "backend", "§33.4 `<=` pasa a `>=`", V,
     "                if acumulado > recibidos:", "                if acumulado < recibidos:"),
    ("M5", "backend", "§33.5 UNKNOWN se convierte en 0 (saldo disponible)", V,
     '            if _known(fila, "eggs_received", "eggs_set", *_SALIDAS_PRE_CARGA):\n'
     '                derivados["eggs_available_to_set"] = (_val(fila, "eggs_received") - _val(fila, "eggs_set")\n'
     '                                                     - sum(_val(fila, c) for c in _SALIDAS_PRE_CARGA))',
     '            if _known(fila, "eggs_received", "eggs_set"):\n'
     '                derivados["eggs_available_to_set"] = (_val(fila, "eggs_received") - _val(fila, "eggs_set")\n'
     '                                                     - sum((_val(fila, c) or 0) for c in _SALIDAS_PRE_CARGA))'),
    # ── adicionales: el resto de consumidores ──
    ("M6", "backend", "reconciliación: la fosa vuelve a restarse de en proceso", S,
     "                        en_proceso = (cargados - transferidos) if None not in (cargados, transferidos) else None",
     "                        en_proceso = (cargados - transferidos - (fosa or 0)) if None not in (cargados, transferidos) else None"),
    ("M7", "backend", "reconciliación: el disponible no resta la fosa", S,
     "                        disponible = ((recibidos - cargados - total_no_incubable - fosa)\n"
     "                                      if None not in (total_no_incubable, fosa) else None)",
     "                        disponible = ((recibidos - cargados - total_no_incubable)\n"
     "                                      if None not in (total_no_incubable,) else None)"),
    ("M8", "backend", "BR-03 operativo no resta la fosa", O,
     "               - no_incubables - fosa)", "               - no_incubables)"),
    ("M9", "backend", "vuelve la regla superada transferidos + fosa ≤ cargados", V,
     '            if _known(fila, "eggs_transferred") and _val(fila, "eggs_transferred") > cargados:',
     '            if _known(fila, "eggs_transferred") and _val(fila, "eggs_transferred") + (_val(fila, "fertile_eggs_to_pit") or 0) > cargados:'),
    ("F1", "frontend", "preview: la columna de saldo pinta otro derivado", P,
     "    valor: disponibleDerivado },", "    valor: enProcesoDerivado },"),
    ("F2", "frontend", "preview: el saldo deja la etapa pre-carga (tras recibidos)", P,
     "{ clave: 'available', tras: 'eggs_set',", "{ clave: 'available', tras: 'eggs_received',"),
    ("F3", "frontend", "i18n: la fosa vuelve a rotularse post-carga", ES,
     '"fertileEggsToPit": "Huevos fértiles a fosa (pre-carga)",', '"fertileEggsToPit": "Huevos fértiles a fosa (post-carga)",'),
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

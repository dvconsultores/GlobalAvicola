"""GA-UAT-BREEDER-CRIA-S2-O23-NULL-TO-MASTER · SPEC 020 §7 — sensibilidad por mutación.

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
    "tests/test_uat_s2_o23_null_to_master.py",
]
FRONTEND_TESTS = [
    "src/pages/review/__tests__/uatS2o23.nullToMaster.test.tsx",
]

C = "backend/app/corrections/service.py"
CF = "frontend/src/pages/review/CorrectionForm.tsx"
RD = "frontend/src/pages/review/ReviewDetail.tsx"
U = "frontend/src/utils/correctionFields.ts"

MUTANTES = [
    ("B01", "backend", "AC-O23-02 el maestro vacío no se ofrece (corregibilidad por valor)", C,
     "                    and not (campo in MAESTROS_CORREGIBLES and _maestro_aplica(event, campo))):",
     "                    and not False):"),
    ("B02", "backend", "AC-O23-01 todo maestro aplica a todo tipo", C,
     "    return campo in MAESTROS_POR_TIPO_DE_EVENTO.get(EventType(tipo), frozenset())",
     "    return campo in MAESTROS_CORREGIBLES"),
    ("B03", "backend", "AC-O23-04 sin rechazo de campo ajeno al tipo", C,
     "            if (data.field_name in MAESTROS_CORREGIBLES and valor_original is None\n                    and not _maestro_aplica(event, data.field_name)):",
     "            if (data.field_name in MAESTROS_CORREGIBLES and valor_original is None\n                    and False):"),
    ("B04", "backend", "AC-O23-05 maestro inactivo aceptado", C,
     "        if activo is False:\n            raise BusinessRuleViolation(",
     "        if activo is None and False:\n            raise BusinessRuleViolation("),
    ("B05", "backend", "AC-O23-05 guarda de activo no invocada", C,
     "                await self._exigir_maestro_activo(data.field_name, valor_aplicado)",
     "                pass"),
    ("B06", "backend", "AC-O23-01 la recepción no admite proveedor", C,
     "    EventType.BIRD_RECEPTION: frozenset({\"supplier_id\"}),",
     "    EventType.BIRD_RECEPTION: frozenset(),"),
    ("F01", "frontend", "AC-O23-07 original vacío no dice «Sin valor»", U,
     "return valor === null || valor === undefined || String(valor) === ''",
     "return false"),
    ("F02", "frontend", "AC-O23-05/07 el selector ofrece inactivos", CF,
     " .filter((r: any) => r.is_active !== false)", " .filter((r: any) => r || true)"),
    ("F03", "frontend", "AC-O23-07 etiqueta sin código", U,
     " return codigo ? `${String(codigo)} — ${nombre}` : nombre", " return nombre"),
    ("F04", "frontend", "AC-O23-07 el historial no dice «Sin valor»", RD,
     "  return esValorVacio(texto)", "  return false"),
    ("F05", "frontend", "AC-O23-07 el original vuelve a mostrarse en blanco", CF,
     " const textoOriginal = esValorVacio(valorOriginal) ? String(t('corrections.noValue', 'Sin valor')) : String(valorOriginal)",
     " const textoOriginal = String(valorOriginal ?? '')"),
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

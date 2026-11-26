#!/usr/bin/env python3
"""GA-UAT-BREEDER-CRIA-S2-OWNER-DECISIONS · SPEC 020 §6 — sensibilidad por mutación.

Se ejecuta desde la raíz del repositorio DESPUÉS del commit de implementación. Cada mutante es un
reemplazo literal (debe aparecer exactamente una vez); se corre la batería dirigida y el archivo
se restaura con `git restore --source=<SHA> -- <archivo>` (restauración explícita por SHA).
Un mutante está MUERTO si la batería falla. Solo se guarda el resumen de cada corrida (sin DSN).

Uso: python3 audit/.../mutation/driver.py [backend|frontend|all] [ID,ID,...]
(con la lista de IDs solo se vuelven a correr esos mutantes; el resto de results.json se conserva)
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
    "tests/test_uat_s2_owner_decisions_a.py",
    "tests/test_uat_s2_owner_decisions_b.py",
    "tests/test_uat_s2_owner_decisions_c.py",
    "tests/test_uat_s2_owner_decisions_cat.py",
]
FRONTEND_TESTS = [
    "src/pages/operations/__tests__/uatS2c.requiredRules.test.ts",
    "src/pages/operations/__tests__/uatS2c.derivedFields.test.tsx",
    "src/pages/review/__tests__/uatS2c.correctionType.test.tsx",
    "src/utils/__tests__/semanaProductiva.test.ts",
]

V = "backend/app/operations/validators.py"
S = "backend/app/operations/service.py"
C = "backend/app/corrections/service.py"
SEM = "backend/app/operations/semana.py"
MS = "backend/app/masters/service.py"
OP = "frontend/src/pages/operations/operationPayload.ts"
SP = "frontend/src/utils/semanaProductiva.ts"
CF = "frontend/src/pages/review/CorrectionForm.tsx"

MUTANTES = [
    # ── backend ────────────────────────────────────────────────────────────────────────
    ("B01", "backend", "RR-27 tipo de corrección no exigido", C,
     "        if correction_type_id is None or correction_type_id <= 0:\n            raise BusinessRuleViolation(MENSAJE_TIPO_DE_CORRECCION, \"RR-27\")",
     "        if False:\n            raise BusinessRuleViolation(MENSAJE_TIPO_DE_CORRECCION, \"RR-27\")"),
    ("B02", "backend", "RR-27 tipo inactivo aceptado", C,
     "\"Tipo de corrección\", exigir_activo=True)", "\"Tipo de corrección\", exigir_activo=False)"),
    ("B03", "backend", "RR-31 lote de vacuna en blanco aceptado", V,
     "if vaccine_lot_number is None or str(vaccine_lot_number).strip() == \"\":",
     "if vaccine_lot_number is None:"),
    ("B04", "backend", "RR-32 causa de mortalidad no exigida", V,
     "if tipo == EventType.MORTALITY_RECORDING.value and cause_id is None:",
     "if False and cause_id is None:"),
    ("B05", "backend", "RR-32 causa de descarte no exigida", V,
     "if tipo == EventType.CULL_RECORDING.value and cull_cause_id is None:",
     "if False and cull_cause_id is None:"),
    ("B06", "backend", "RR-28 inspección vacía aceptada", V,
     "    raise BusinessRuleViolation(MENSAJE_INSPECCION_SIN_CONTENIDO, \"RR-28\")",
     "    return None"),
    ("B07", "backend", "RR-28 valores por defecto cuentan como contenido", V,
     "    return _con_texto(_leer(\"value\")) or _leer(\"value_numeric\") is not None or _con_texto(_leer(\"status\"))",
     "    return True"),
    ("B08", "backend", "RR-29 distribución de suma cero aceptada", V,
     "    if sum(cantidades) <= 0:", "    if sum(cantidades) < 0:"),
    ("B09", "backend", "RR-33 alimento sin tipo aceptado", V,
     "               for fila in (feed_movements or [])):\n            raise BusinessRuleViolation(\"Seleccione el tipo de alimento\", \"RR-33\")",
     "               for fila in (feed_movements or [])) and False:\n            raise BusinessRuleViolation(\"Seleccione el tipo de alimento\", \"RR-33\")"),
    ("B10", "backend", "RR-30 semana ISO-like (sin +1)", SEM,
     "    return dias // 7 + 1", "    return dias // 7"),
    ("B11", "backend", "RR-34 sin fase vigente se acepta", S,
     "            if fase is None:\n                raise BusinessRuleViolation(",
     "            if False:\n                raise BusinessRuleViolation("),
    ("B12", "backend", "RR-30 corrección de fecha no recalcula la semana", C,
     "            if data.field_name in (\"event_date\", \"lot_id\"):  # `RR-30` / `RR-34`: la semana sigue a la fecha",
     "            if False:  # mutante"),
    ("B13", "backend", "«Desconocida» compartida no se lista", MS,
     "    _CATALOGOS_CON_COMPARTIDOS = {\"mortality_causes\", \"cull_causes\"}",
     "    _CATALOGOS_CON_COMPARTIDOS = set()"),
    # ── frontend ───────────────────────────────────────────────────────────────────────
    ("F01", "frontend", "RR-27 UI sin tipo envía", CF,
     " if (!correctionTypeId) return t('corrections.typeRequired')", " if (false) return t('corrections.typeRequired')"),
    ("F02", "frontend", "RR-27 UI ofrece tipos inactivos", CF,
     "ctypes.filter((ct: any) => ct.is_active !== false)", "ctypes.filter((ct: any) => ct || true)"),
    ("F03", "frontend", "RR-31 UI lote de vacuna no exigido", OP,
     "if (tipo === 'vaccination' && String(datos?.vaccine_lot_number ?? '').trim() === '') return",
     "if (false && String(datos?.vaccine_lot_number ?? '').trim() === '') return"),
    ("F04", "frontend", "RR-32 UI causa de mortalidad no exigida", OP,
     "if (tipo === 'mortality_recording' && !idDeclarado(datos?.cause_id)) return",
     "if (false && !idDeclarado(datos?.cause_id)) return"),
    ("F05", "frontend", "RR-32 UI causa de descarte no exigida", OP,
     "if (tipo === 'cull_recording' && !idDeclarado(datos?.cull_cause_id)) return",
     "if (false && !idDeclarado(datos?.cull_cause_id)) return"),
    ("F06", "frontend", "RR-29 UI distribución en cero aceptada", OP,
     "    if (total <= 0) return 'operations.distributionRequired'",
     "    if (total < 0) return 'operations.distributionRequired'"),
    ("F07", "frontend", "RR-28 UI inspección vacía aceptada", OP,
     "  if (tipo === 'farm_inspection' && !inspeccionConContenido(datos)) return",
     "  if (false && !inspeccionConContenido(datos)) return"),
    ("F08", "frontend", "RR-33 UI alimento sin tipo aceptado", OP,
     "numeroDeclarado(fila?.quantity_kg) > 0 && !idDeclarado(fila?.feed_type_id))) {",
     "numeroDeclarado(fila?.quantity_kg) > 0 && false)) {"),
    ("F09", "frontend", "RR-30 UI semana sin +1", SP,
     "  return Math.floor(dias / 7) + 1", "  return Math.floor(dias / 7)"),
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

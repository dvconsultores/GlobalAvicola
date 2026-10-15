"""SPEC 006 · driver de sensibilidad S1–S12 (mandato §39) — NO es código de producción.

    uso: backend/.venv/bin/python audit/cutover-initial-balances/evidence/mutations/driver.py <IMPLEMENTATION_SHA> [S1 S2 ...]

Protocolo (`audit/remediation/MUTATION_CHECKPOINT_GOVERNANCE.md`): corre DESPUÉS del commit de
implementación, con el árbol productivo limpio y bajo `backend/scripts/mutation_guard.py`. Cada
mutación se instala en el archivo productivo, se ejecuta la prueba que debe enrojecer con el
arnés real (`run_tests.sh`), y se restaura con `git restore --source=<SHA> -- <archivo>`
comprobando byte a byte. Los logs se guardan saneados (sin DSN).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
BACKEND = RAIZ / "backend"
SALIDA = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))
from scripts.mutation_guard import GuardaDeMutacion  # noqa: E402

PARSER = "backend/app/cutover/parser.py"
VALIDACION = "backend/app/cutover/validation.py"
SERVICIO = "backend/app/cutover/service.py"
CONTRATOS = "backend/app/cutover/contracts.py"
VALIDADORES = "backend/app/operations/validators.py"

MUTACIONES: dict[str, dict] = {
    "S1": dict(desc="UNKNOWN → 0 (celda vacía de métrica se guarda como 0 KNOWN)", archivo=PARSER,
               viejo='                normalizado[spec.normalized] = {"value": None, "status": UNKNOWN}\n            continue\n        if isinstance(v, str) and v.strip().upper() in _NA:',
               nuevo='                normalizado[spec.normalized] = {"value": 0, "status": KNOWN}\n            continue\n        if isinstance(v, str) and v.strip().upper() in _NA:',
               prueba="tests/test_cutover_v2_contracts.py::test_vacio_es_unknown_cero_es_known_na_es_not_applicable"),
    "S2": dict(desc="N/A → UNKNOWN (se pierde NOT_APPLICABLE)", archivo=PARSER,
               viejo='                normalizado[spec.normalized] = {"value": None, "status": NOT_APPLICABLE}',
               nuevo='                normalizado[spec.normalized] = {"value": None, "status": UNKNOWN}',
               prueba="tests/test_cutover_v2_contracts.py::test_vacio_es_unknown_cero_es_known_na_es_not_applicable"),
    "S3": dict(desc="maestro de otra empresa permitido (granja resuelta sin filtro de empresa)", archivo=VALIDACION,
               viejo='select(Farm).where(Farm.company_id == self.company_id, Farm.code == _val(fila, "farm_code"))',
               nuevo='select(Farm).where(Farm.code == _val(fila, "farm_code"))',
               prueba="tests/test_cutover_v2_validation.py::test_maestro_de_otra_empresa_no_resuelve"),
    "S4": dict(desc="concesión de BU ignorada en el apply", archivo=SERVICIO,
               viejo='            if batch.business_unit not in alcance:\n                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,\n                                    detail=f"BU_NOT_GRANTED',
               nuevo='            if False and batch.business_unit not in alcance:\n                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,\n                                    detail=f"BU_NOT_GRANTED',
               prueba="tests/test_cutover_v2_apply.py::test_multiempresa_bu_deshabilitada_y_sin_concesion"),
    "S5": dict(desc="doble apply permitido (APPLIED deja de ser terminal y las filas ya aplicadas no bloquean): mutación de capa completa",
               archivo=SERVICIO,
               viejo=['        if batch.status != CutoverBatchStatus.APPROVED.value:\n            raise HTTPException(status_code=status.HTTP_409_CONFLICT,\n                                detail=f"BATCH_STATE_INVALID: el batch está en estado {batch.status}: solo uno APPROVED se aplica.")',
                      '        if any(item.validation_status != CutoverItemStatus.VALID.value for item in items):'],
               nuevo=['        if batch.status not in (CutoverBatchStatus.APPROVED.value, CutoverBatchStatus.APPLIED.value):\n            raise HTTPException(status_code=status.HTTP_409_CONFLICT,\n                                detail=f"BATCH_STATE_INVALID: el batch está en estado {batch.status}: solo uno APPROVED se aplica.")',
                      '        if any(item.validation_status not in (CutoverItemStatus.VALID.value, CutoverItemStatus.APPLIED.value) for item in items):'],
               prueba="tests/test_cutover_v2_apply.py::test_idempotencia_doble_apply_y_segregacion"),
    "S6": dict(desc="relación galpón→granja ignorada", archivo=VALIDACION,
               viejo='                    select(House).where(House.farm_id == granja.id, House.name == nombre),',
               nuevo='                    select(House).where(House.name == nombre),',
               prueba="tests/test_cutover_v2_validation.py::test_relaciones_padre_hijo"),
    "S7": dict(desc="campo crítico de incubadora (eggs_set) deja de ser obligatorio", archivo=CONTRATOS,
               viejo='    FieldSpec("eggs_set", "int", "Huevos ya cargados en incubadora. ≤ recibidos.", required=True, metric=True,',
               nuevo='    FieldSpec("eggs_set", "int", "Huevos ya cargados en incubadora. ≤ recibidos.", required=False, metric=True,',
               prueba="tests/test_cutover_v2_validation.py::test_campo_obligatorio_de_incubadora"),
    "S8": dict(desc="opening crítico no persistido (eggs_received de la apertura de incubadora)", archivo=SERVICIO,
               viejo='            eggs_received=_opcional(estado, "eggs_received"), eggs_received_status=_s(estado, "eggs_received"),',
               nuevo='            eggs_received=None, eggs_received_status=_s(estado, "eggs_received"),',
               prueba="tests/test_cutover_v2_continuity.py::test_hatchery_siguiente_paso_de_incubacion"),
    "S9": dict(desc="evento anterior o igual al corte permitido (CUT-GL-02 apagada)", archivo=VALIDADORES,
               viejo='    if fecha_evento <= fecha_corte:\n        raise BusinessRuleViolation(',
               nuevo='    if False and fecha_evento <= fecha_corte:\n        raise BusinessRuleViolation(',
               prueba="tests/test_cutover_v2_continuity.py::test_cut_gl_02_rechaza_eventos_hasta_el_corte"),
    "S10": dict(desc="mismo checksum en otro batch del mismo corte se acepta (duplica la carga)", archivo=SERVICIO,
                viejo='        if otro is not None:\n            raise HTTPException(status_code=status.HTTP_409_CONFLICT,\n                                detail=f"DUPLICATE_UPLOAD',
                nuevo='        if False and otro is not None:\n            raise HTTPException(status_code=status.HTTP_409_CONFLICT,\n                                detail=f"DUPLICATE_UPLOAD',
                prueba="tests/test_cutover_v2_apply.py::test_idempotencia_doble_apply_y_segregacion"),
    "S11": dict(desc="plantilla de reproductoras aceptada en batch de incubadora (sin comprobar BU/schema_id)", archivo=PARSER,
                viejo='    if business_unit != contrato.business_unit or (schema_id and schema_id != contrato.schema_id):',
                nuevo='    if False:',
                prueba="tests/test_cutover_v2_contracts.py::test_plantilla_de_otra_bu_rechazada"),
    "S12": dict(desc="cabecera obligatoria ausente en CSV aceptada", archivo=PARSER,
                viejo='    faltantes = [c for c in contrato.columns if c not in vistas]\n    if faltantes:',
                nuevo='    faltantes = [c for c in contrato.columns if c not in vistas]\n    if False:',
                prueba="tests/test_cutover_v2_contracts.py::test_cabeceras_duplicadas_desconocidas_y_faltantes"),
}

_RE_DSN = re.compile(r"postgresql(\+[a-z]+)?://[^ :@\n]+:[^ @\n]+@")
_RE_RESUMEN = re.compile(r"^=+ .*(passed|failed|error).* in [0-9.]+s =+$", re.M)


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(RAIZ), *args], capture_output=True, text=True, check=True).stdout


def _sanear(texto: str) -> str:
    return _RE_DSN.sub("postgresql://[REDACTADO]@", texto)


def ejecutar(sha: str, ids: list[str]) -> int:
    rutas = tuple(sorted({MUTACIONES[i]["archivo"] for i in ids}))
    guarda = GuardaDeMutacion(RAIZ, sha, rutas)
    guarda.exigir()
    resumen: list[str] = [f"IMPLEMENTATION_COMMIT = {sha}", ""]
    detectadas = 0
    for mid in ids:
        m = MUTACIONES[mid]
        ruta = RAIZ / m["archivo"]
        original = ruta.read_text(encoding="utf-8")
        viejos = m["viejo"] if isinstance(m["viejo"], list) else [m["viejo"]]
        nuevos = m["nuevo"] if isinstance(m["nuevo"], list) else [m["nuevo"]]
        mutado = original
        for viejo, nuevo in zip(viejos, nuevos):
            assert mutado.count(viejo) == 1, f"{mid}: cada fragmento a mutar debe aparecer exactamente una vez"
            mutado = mutado.replace(viejo, nuevo)
        ruta.write_text(mutado, encoding="utf-8")
        try:
            proc = subprocess.run(["bash", "scripts/run_tests.sh", m["prueba"], "-p", "no:cacheprovider"],
                                  cwd=BACKEND, capture_output=True, text=True)
            salida = _sanear(proc.stdout + "\n" + proc.stderr)
            lineas = _RE_RESUMEN.findall(salida)
            linea_resumen = [l for l in salida.splitlines() if _RE_RESUMEN.match(l)]
            resumen_pytest = linea_resumen[-1] if linea_resumen else "(sin resumen de pytest)"
            detectada = ("failed" in resumen_pytest or "error" in resumen_pytest) and proc.returncode != 0
        finally:
            subprocess.run(["git", "-C", str(RAIZ), "restore", f"--source={sha}", "--", m["archivo"]], check=True)
            guarda.exigir_restauracion(m["archivo"])
            esperado = _git("show", f"{sha}:{m['archivo']}")
            assert ruta.read_text(encoding="utf-8") == esperado, f"{mid}: restauración no es byte a byte"
        (SALIDA / f"{mid}.log").write_text(
            f"# {mid} · {m['desc']}\n# archivo: {m['archivo']}\n# prueba: {m['prueba']}\n# DETECTED: {'YES' if detectada else 'NO'}\n\n{salida}",
            encoding="utf-8")
        detectadas += int(detectada)
        resumen.append(f"{mid:<4} {'DETECTED' if detectada else 'NOT_DETECTED':<13} {resumen_pytest.strip('= ')}  · {m['archivo']} · {m['prueba'].split('::')[-1]}")
        print(resumen[-1], flush=True)
    diff = subprocess.run(["git", "-C", str(RAIZ), "diff", "--exit-code", sha, "--", "backend/app", "frontend/src", "backend/alembic"],
                          capture_output=True, text=True)
    resumen += ["", f"DETECTED = {detectadas}/{len(ids)}", f"FINAL_RESTORE_SHA = {sha}", f"FINAL_DIFF = {diff.returncode}",
                f"MUTATION = {'PASS' if detectadas == len(ids) and diff.returncode == 0 else 'FAIL'}"]
    (SALIDA / "SENSITIVITY_SUMMARY.log").write_text("\n".join(resumen) + "\n", encoding="utf-8")
    print("\n".join(resumen[-4:]))
    return 0 if detectadas == len(ids) and diff.returncode == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    seleccion = sys.argv[2:] or list(MUTACIONES)
    sys.exit(ejecutar(sys.argv[1], seleccion))

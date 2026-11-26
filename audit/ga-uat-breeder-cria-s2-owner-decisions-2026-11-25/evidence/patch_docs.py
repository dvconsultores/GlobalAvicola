#!/usr/bin/env python3
"""Documentación del cierre (desde la raíz del repo): spec §6.1 corregida, §6.3 estado y manual."""
import sys
from pathlib import Path

ERR = []


def R(path, old, new, count=1):
    p = Path(path)
    s = p.read_text(encoding="utf-8")
    n = s.count(old)
    if n != count:
        ERR.append(f"{path}: se esperaban {count} apariciones y hay {n}: {old[:90]!r}")
        return
    p.write_text(s.replace(old, new), encoding="utf-8")


F = "specs/020-uat-breeder-cria-s2/spec.md"
R(F, "con casos deterministas en frontera de semana y de año (incluida la comparación bajo `GA_TEST_SIMULATED_TODAY`); sin relajar la aserción `Δ == 10`.",
  "con casos deterministas en frontera de semana y de año; sin relajar la aserción `Δ == 10`. "
  "Prueba de determinismo con el reloj de los tests fijado (plugin de evidencia `reloj_controlado`, que fija "
  "`reference_today()`; el repositorio no expone un override de reloj): la versión anterior falla en lunes y "
  "martes (`Δ=0`) y pasa en domingo; la corregida pasa en domingo, lunes y martes, sola y dentro de la suite completa.")
R(F, "Observaciones nuevas: `O-26` (evidencia solo posterior al alta).",
  "Observaciones nuevas: `O-26` (evidencia solo posterior al alta).\n\n"
  "### 6.3 Estado de implementación (26-11-2026)\n"
  "`IMPLEMENTADO` en `develop`. Migración `i4d5e6f7a8b9` (cabeza Alembic): «Desconocida» compartida en "
  "`mortality_causes`/`cull_causes` y `feed_movements.phase_id`. Backend `7ee3327`, `412e234`, `a1c2d53`, "
  "`edb3d04`; frontend `7e18207`, `1bc438f`. Pruebas `OD01-01..05`, `OD02-01..05`, `OD03-01..05`, "
  "`OD04-01..05`, `OD05-01..04`, `OD06-01..05`, `OD07-01..05`, `T-CAT-1..6`, espejo en vitest y E2E "
  "`proceso-spec020b` (16 pasos).\n\n"
  "Hallazgo de la E2E, corregido: el formulario de corrección ofrecía tipos **inactivos**, que el servidor rechaza "
  "(`RR-27` exige activo); ahora el selector solo ofrece tipos activos (`1bc438f`, `OD01-05`).\n\n"
  "Observaciones: `O-26` (evidencia solo tras el alta); `O-27` un lote sin fase productiva vigente en la fecha "
  "no puede registrar alimento hasta que se registre su fase (`RR-34`, ratificado: no se inventa) — en el retest "
  "UAT, los lotes de prueba deben tener su fase cargada; `O-23` (asignar por corrección un maestro a un campo que "
  "estaba vacío) sigue abierta. Certificación: `audit/ga-uat-breeder-cria-s2-owner-decisions-2026-11-25/CERTIFICATION.md`.")

F = "docs/MANUAL_USUARIO.md"
R(F, "El **tipo de corrección es obligatorio** en toda corrección nueva: sin elegirlo el formulario avisa «Seleccione el tipo de corrección» y no envía nada.",
  "El **tipo de corrección es obligatorio** en toda corrección nueva: sin elegirlo el formulario avisa «Seleccione el tipo de corrección» y no envía nada. La lista solo ofrece los tipos de corrección **activos** del catálogo.")

if ERR:
    print("ERRORES:\n" + "\n".join(ERR))
    sys.exit(1)
print("OK: parches aplicados")

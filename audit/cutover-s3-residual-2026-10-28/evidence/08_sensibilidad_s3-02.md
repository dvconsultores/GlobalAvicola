# Sensibilidad / Mutation testing — S3-02 (SPEC 012)

**IMPL SHA (restauración):** `fc949f19f5ec6328fc9d0ecdc9a6faf3c4b11cae`
**Archivo mutado:** `backend/app/cutover/templates.py` (representación de `Meta.cutover_datetime` en zona de negocio)
**Suite objetivo:** `backend/scripts/run_tests.sh tests/test_cutover_s3_timezone.py tests/test_cutover_uat_hardening_s011.py`
**Restauración:** `git restore --source=fc949f1 -- backend/app/cutover/templates.py` tras cada mutación.

Mutaciones post-commit de implementación (§8). El ejecutor (DeepSeek, MCP) aplicó las ediciones; Claude verificó de forma independiente (diff vs SHA + suite real).

| Mutación | Cambio | Resumen suite | Veredicto |
|---|---|---|---|
| **baseline** | — (código de implementación) | `9 passed` | verde |
| **S1** | `astimezone(ZONA_NEGOCIO)` → `astimezone(timezone.utc)` (vuelve al bug UTC) | `8 failed, 1 passed` | **DETECTADA** |
| **S2** | `ZoneInfo("America/Caracas")` → `ZoneInfo("America/New_York")` (zona errónea) | `1 failed, 8 passed` (vector fin de año en invierno, −05:00) | **DETECTADA** |
| **restauración final** | `git restore --source=fc949f1` | `9 passed` | verde |

**Verificación independiente (Claude):**
- `git diff --stat fc949f1 -- backend/app/cutover/templates.py` → **vacío (0 cambios)**.
- `git status --short` → solo `audit/cutover-s3-residual-2026-10-28/` sin seguimiento.

**Resultado:** 2/2 mutaciones que cambian el comportamiento DETECTADAS. Nota: una zona de offset fijo equivalente a −04:00 (p. ej. `America/Port_of_Spain`) sería un **mutante equivalente** (produce exactamente la misma representación `-04:00`), representacionalmente correcto, no una brecha de cobertura. La persistencia (UTC) y la autoridad del batch no se mutan: las cubre la suite de apply/reconciliación en la regresión completa.

```
SENSIBILIDAD_S3-02=2/2_DETECTADAS · ARBOL_POST_RESTORE=LIMPIO · DIFF_VS_IMPL_SHA=0
```

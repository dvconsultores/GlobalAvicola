# Sensibilidad / Mutation testing — CUTOVER-DATA-01 (SPEC 011)

**IMPL SHA (fuente de restauración):** `5f3a698ade99a6d8c2ca459d7b0842af4d7fb6cd`
**Archivo mutado:** `backend/app/cutover/templates.py` (bloque display-only DATA-01, líneas ~216-220)
**Suite objetivo:** `backend/scripts/run_tests.sh tests/test_cutover_uat_hardening_s011.py`
**Restauración:** `git restore --source=5f3a698 -- backend/app/cutover/templates.py` tras cada mutación.

Las mutaciones se ejecutan DESPUÉS del commit de implementación (§8). El ejecutor (DeepSeek, MCP) aplicó las ediciones; Claude verificó de forma independiente (diff vs SHA + suite real).

| Mutación | Cambio | Resumen suite | Test que detecta | Veredicto |
|---|---|---|---|---|
| **baseline** | — (código de implementación) | `2 passed in 1.6s` | — | verde |
| **S1** | `if corte is None and cutover_datetime:` → `… and False:` | `1 failed, 1 passed` | `test_data01_meta_refleja_corte_sin_batch` (`'None'.startswith('2026-10-01T08:00:00')` → AssertionError) | **DETECTADA** |
| **S2** | `corte = datetime.fromisoformat(cutover_datetime)` → `corte = None` | `1 failed, 1 passed` | `test_data01_meta_refleja_corte_sin_batch` (mismo AssertionError) | **DETECTADA** |
| **restauración final** | `git restore --source=5f3a698` | `2 passed in 1.6s` | — | verde |

**Verificación independiente (Claude):**
- `git diff --stat 5f3a698 -- backend/app/cutover/templates.py` → **vacío (0 cambios)**.
- `git status --short` → solo `audit/cutover-uat-hardening-2026-10-27/` sin seguimiento; `templates.py` limpio.
- Líneas 216-220 idénticas al original de implementación.

**Resultado:** 2/2 mutaciones DETECTADAS; el test `test_data01_meta_refleja_corte_sin_batch` es portador de carga (guarda el relleno display-only de `Meta.cutover_datetime`). La autoridad del corte sigue en el batch (no mutada: la lee `service.py`, el parser ignora Meta — cubierto por `test_data01_parser_ignora_cutover_de_meta`, que permanece en verde en ambas mutaciones).

```
SENSIBILIDAD_DATA01=2/2_DETECTADAS · ARBOL_POST_RESTORE=LIMPIO · DIFF_VS_IMPL_SHA=0
```

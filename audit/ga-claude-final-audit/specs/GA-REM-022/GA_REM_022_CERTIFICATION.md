# GA-REM-022 · WAVE C (KPI P1) — CERTIFICACIÓN

Fecha: 2026-09-16 · Estado: **CERTIFIED_TECHNICALLY** (decisión del
propietario aplicada) · Decisión autoritativa:
`audit/ga-pre-sap-program/GA_OWNER_DECISION_WAVE_C_FORMAL.md` (commit `b58136a`).

## Alcance certificado (formula a formula, orden del propietario)

| Ítem | Decisión Owner | Implementación | Evidencia |
|---|---|---|---|
| **R-131** FCR | Corregir: `FCR = masa de alimento / ganancia de masa viva` (Δ peso medio × base ∩ estados aceptados); sin denominadores fabricados; UNKNOWN (null) si no hay evidencia de pesos | `reports/service.py::get_kpi_feed_conversion` + `_pesos_del_lote` (apertura o primer pesaje; último pesaje aceptado) | RED `3398dc4` · GREEN `tests/test_ga_rem_022_r131_r141.py` · regresión `evidence/green/regen-kpi-reportes-FINAL.log` |
| **OD-22** | **Sin cambios** (declarado explícitamente por el propietario) | IPE `(viabilidad%×ADG_g/día)/(FCR×10)` bandas <250/250-300/≥300 | `tests/test_r187_ipe_od22_scale.py` verde (bandas 249/250/300 exactas; fixtures fijan Δ=1000 g × 1000 aves = 1000 kg ⇒ FCR canónico numéricamente idéntico al anterior) |
| **Edad lote cerrado** | Congelada en `end_date` | `get_kpi_ipe`/detalle usan `end_date` si existe | RED/GREEN `tests/test_ga_rem_022_wave_c_kpi.py` (60 días) |
| **R-132** base mortalidad | Aprobada: base = `opening_population + recepciones`; UNKNOWN nunca 0 | `get_kpi_mortality` (+ claves aditivas `opening_population`, `receptions`) | RED/GREEN `test_ga_rem_022_wave_c_kpi.py` (10 % por recepción; 5 % no-regresión) |
| **R-141** agregados | Corregir: mismo conjunto filtrado que el detalle R-218 (estados `APPROVED, CONSOLIDATED, SENT_TO_SAP, SAP_CONFIRMED`) | IPE producción/uniformidad/tendencia con filtro de estado | RED/GREEN `test_ga_rem_022_r131_r141.py` (5250≠5520; 3 muestras iguales; Δ10≠510) |
| **R-133/R-134** | `DEFERRED_FUNCTIONAL_DEFINITION` — retiradas de superficies certificadas; **sin fórmulas inventadas** | FE: tarjetas AFCR/vacunación retiradas (`LotReportPage`, `ReportsPage`); E2E p15 ajustado; datos primarios conservados | FE 524/524 · build 0 · E2E `evidence/e2e/e2e-full-FINAL.log` |

## Cadena de gobernanza (checkpoint por checkpoint)

- **SPEC/AC**: micro-tranca `GA_REM_022_WAVE_C_KPI_MICRO.md` (estado → OWNER_APPROVED_IMPLEMENTED).
- **RED**: `3398dc4` — 5 fallos causa-exacta (2F FCR canónico: campos inexistentes/`2.0` fabricado; 3F R-141: 5250, 3 muestras, 510 cancelados). Log `evidence/red/rem022-red.log`.
- **IMPL**: `9e76254` — services BE + fixtures `r184/r186/r187` + retiro FE + E2E + docs.
- **GREEN dirigido**: `test_ga_rem_022_wave_c_kpi.py` + `test_ga_rem_022_r131_r141.py` + familia KPI: **142/0/35** post-restauración (`evidence/green/regen-kpi-reportes-FINAL.log`).
- **SENSIBILIDAD** (restore tras cada mutación):
  - **M1** (denominador fabricado `/1000`): **1F exacto** `test_r131_fcr_canonico_alimento_por_ganancia` (`evidence/sensibilidad/m1-fcr-canonico-sens.log`).
  - **M2** (filtro R-141 fuera de uniformidad): **1F exacto** `test_r141_uniformidad_mismo_conjunto_que_detalle` (`evidence/sensibilidad/m2-r141-filtro-sens.log`).
- **POST-MUTACIÓN**: worktree limpio (`git restore` desde HEAD verificado tras cada mutación).

## Gates finales

- **BE full final**: `evidence/green/be-full-FINAL.log` → **1436/0F/49S** (esta corrida **supersede** la suite provisional 1431/0/49, que queda clasificada SUPERSEDED).
  - **Preflight**: la primera corrida full post-IMPL arrojó **1435/1F/49S** — el único fallo fue el guard `T-028-04` (`test_time_determinism.py`) por la fecha ISO `2026-09-16` presente **en comentarios/docstrings** de los tests R-131/R-184/R-186/R-187. Corregido en `af1f1e2` (solo texto; cero cambio funcional), evidencia conservada en `evidence/green/be-full-PREFLIGHT-1435-1F.log`; re-corrida full final limpia.
- **FE**: `vitest` **524/524**, `tsc -b` 0, `npm run build` 0.
- **E2E completo**: **111/111** (`evidence/e2e/e2e-full-FINAL.log`; incluye P-15 ajustado por R-133).
- Guards de suite intactos (pins de cabeza `c8d9e0f1a2b3`, rutas 226, tablas 60).

## Restricciones respetadas (mandato Owner)

- OD-22 **no modificada** (verificado por r187).
- R-133/R-134 **sin fórmulas inventadas**: retiro de superficies + datos primarios conservados.
- Historia Git **no reescrita** (cadena `b58136a → 3398dc4 → 9e76254`); sin reset; sin force push.
- Evidencia provisional anterior **no reutilizada** como certificación (`evidence/PROVISIONAL_NOTE.md` → SUPERSEDED).

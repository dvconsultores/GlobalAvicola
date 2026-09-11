# GA-R186 · RECONCILIACIÓN DE CIERRE

## Mapa de extremo a extremo

| Eslabón | Artefacto / Verdad |
|---|---|
| 500 original | `audit/ga-r184/evidence/red/runtime-red.json` (`prodindex35`=500, heredado) + repro local determinista |
| Causa raíz | `date.today() − lot.start_date` (date − datetime aware) ⇒ TypeError (línea 602 pre-fix) |
| Fórmula G-05 | Preservada e intacta (diff C2: 1 expresión + comentario) |
| Semántica temporal | `_dia()` canónico reutilizado (R-75/GA-REM-028; mismo helper de R-184) |
| Implementación | C2 `0309225` (1 archivo, +4/−1) |
| Pruebas | Suite PG/CI (11 casos) + repro local + batería runtime 14/14 |
| Evidencia runtime | `GA_R186_AUTHENTICATED_RUNTIME_EVIDENCE.md` + `evidence/green/` |
| Seguridad | E2E-09/10/11/12/13 PASS (404/403/OD-16); sin fuga |
| Consumidor frontend | **API_ONLY** (re-verificado) ⇒ Owner UAT **NOT REQUIRED** |
| AC | `GA_R186_CHECKLIST.md` — todos cubiertos (colección N/A probada) |

## Preguntas explícitas

| Pregunta | Respuesta |
|---|---|
| 500 original | **RESOLVED** (200 en E2E-01/01b; repro local del TypeError confirmado) |
| Causa raíz | **CONFIRMED** (date − datetime; probado, no asumido) |
| Fórmula G-05 | **PRESERVED** (sin cambios de términos/redondeos/fallbacks) |
| G-06 | **UNCHANGED** (`ipe/11` = 556.6 exacto; diff limitado) |
| Semántica de fechas | **PASS** (edad exacta 110; mismo día 0 ⇒ PI 0; sin ±1) |
| Resultado determinista | **PASS** (5.1 == 5.1; independiente desde datos crudos) |
| Esquema de respuesta | **PRESERVED** (7 claves + `unit`) |
| Tenant / BU / RBAC | **PASS** (404/403/OD-16) |
| R-184 regression | **PASS** (556.6 + endpoint intacto) |
| Residual | **1 nota registrada** (docstring omite el `×10` del divisor; preservado el código; sin ID nuevo, ver reconciliación §7) + **1 pendiente heredada intacta** (observación de escala IPE — `OWNER_DECISION_REQUIRED`, ajena a esta tranche) |

**R-186: CLOSED (técnico).**

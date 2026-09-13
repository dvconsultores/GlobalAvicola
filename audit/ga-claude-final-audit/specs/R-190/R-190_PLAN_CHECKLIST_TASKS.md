# R-190 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: RED antes que GREEN; producto sólo en C2.** Ningún fichero de `frontend/src` (fuera de `__tests__`) ni de `backend/app` se toca en C1, C3 ni C4. La sensibilidad (mutaciones) se ejecuta **después del commit de implementación**, desde la raíz del repo, porque el driver revierte con `git checkout`.

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Dedup (hecho), finding, spec, clarificaciones (C-04 con dominio; C-03 elevada al propietario), matriz AC, diseño RED/E2E/UAT; escritura de las pruebas RED (`r190.locationEventsHouse.test.tsx`, `r190.resolverUbicacion.test.ts`, `test_r190_br08_contract.py`); ejecución y captura de la RED (vitest falla en los casos previstos; backend control verde) | este paquete | commit C1 «R-190 C1: gobernanza + RED (sin producto)» + `evidence/red/` | ☐ |
| **C2 · Implementación** | Helper `resolverUbicacionDelEvento`; derivación unificada en `onSubmit`; selector «Galpón del evento» ×4; `superRefine` de ubicación; i18n ES/EN; GREEN dirigido + vitest completa + tsc + build; sensibilidad tras commit | C1 verde en RED | commit C2 «R-190 C2: implementación» + `evidence/green/` | ☐ |
| **C3 · Certificación runtime** | Deploy de la generación; E2E-R190-01…08 en nube (actores UAT-09) + control lote con galpón; journal JSON + PNG + payloads; recertificación R-189 retry (7/7) | C2 desplegado | `evidence/runtime-c3/` + `R-190_RUNTIME_CERTIFICATION.md` | ☐ |
| **C4 · UAT del propietario** | UAT-R190-01…05 guiadas; acta; cierre en backlog | C3 | acta UAT + backlog actualizado | ☐ |

## CHECKLIST

- ☐ C1.1 Dedup registrada (`R-190_FINDING.md §4`)
- ☐ C1.2 Clarificación C-04 ratificada con dominio; C-03 enviada al propietario (`OWNER_DECISION_REQUIRED`)
- ☐ C1.3 RED escrita: 3 ficheros de prueba (§TAREAS T-01/T-02/T-03)
- ☐ C1.4 RED ejecutada y leída en HEAD: vitest falla exactamente en AC-R190-01/02/03/04/07/08/09/14; backend control verde; salida guardada en `evidence/red/`
- ☐ C1.5 Commit C1 sin producto (diff limitado a `audit/**`, `frontend/src/**/__tests__/**`, `backend/tests/**`)
- ☐ C2.1 Helper puro + unit verde
- ☐ C2.2 `onSubmit` unificado (F-01e intacto: `f01e.receptionHouse` 4/4)
- ☐ C2.3 Selector «Galpón del evento» en `bird_exit`, `egg_collection`, `egg_dispatch`, `transport_inspection`
- ☐ C2.4 `superRefine` de ubicación + mensajes i18n
- ☐ C2.5 GREEN dirigido (r190.*) + vitest completa + tsc + build
- ☐ C2.6 Commit C2; sensibilidad S1-S4 (§SENSIBILIDAD) ejecutada tras el commit y revertida con `git checkout`
- ☐ C3.1 Deploy y paridad bundle/backend
- ☐ C3.2 E2E-R190-01…08 ejecutadas; 0 fatales; 0 `5xx`
- ☐ C3.3 Retry R-189 UAT-01…07 7/7 sobre la nueva generación
- ☐ C3.4 Certificación escrita con artefactos referenciados
- ☐ C4.1 UAT-R190-01…05 con el propietario; acta
- ☐ C4.2 Backlog: R-190 `CLOSED`, GA-REM asignado, referencias cruzadas R-205/R-211

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | Unit jsdom RED camino real (7 casos) | `frontend/src/pages/operations/__tests__/r190.locationEventsHouse.test.tsx` (nuevo) | M | — | C1 |
| T-02 | Unit puro RED del helper (tabla tipo × fuente) | `frontend/src/pages/operations/__tests__/r190.resolverUbicacion.test.ts` (nuevo) | S | — | C1 |
| T-03 | Backend control BR-08 (verde en HEAD) | `backend/tests/test_r190_br08_contract.py` (nuevo; patrón `esc` de `test_reception_reconciliation.py`) | S | — | C1 |
| T-04 | Helper `resolverUbicacionDelEvento` | `frontend/src/pages/operations/operationPayload.ts` | S | T-02 | C2 |
| T-05 | Derivación unificada en `onSubmit` (`derivedHouseId`/`derivedFarmId`) | `frontend/src/pages/operations/OperationFormPage.tsx:381-462` | S | T-04 | C2 |
| T-06 | Selector «Galpón del evento» ×4 + preselección/bloqueo si el lote tiene galpón | `OperationFormPage.tsx` casos `bird_exit`, `egg_collection`, `egg_dispatch`, `transport_inspection` | M | T-05 | C2 |
| T-07 | `superRefine` de ubicación + mensajes | `OperationFormPage.tsx:178-187`; `public/locales/es/translation.json`; `public/locales/en/translation.json` | S | T-05 | C2 |
| T-08 | GREEN + regresión (vitest completa, tsc, build) | — | S | T-04…T-07 | C2 |
| T-09 | Sensibilidad S1-S4 tras el commit C2 | — | S | T-08 | C2 |
| T-10 | Runner E2E runtime (extensión de `scripts_e2e_f01_retry.mjs` o script propio `scripts_e2e_r190.mjs`) | raíz del repo | M | T-08 | C3 |
| T-11 | Ejecución C3 + certificación | `audit/ga-claude-final-audit/specs/R-190/evidence/runtime-c3/`, `R-190_RUNTIME_CERTIFICATION.md` | M | T-10 | C3 |
| T-12 | UAT guiada + acta + backlog | `audit/ga-claude-final-audit/specs/R-190/R-190_UAT_ACTA.md`; `audit/remediation/REMEDIATION_BACKLOG.md` | S | T-11 | C4 |
| T-13 | (Condicional, si C-03 = B) anexo de spec + RED backend (`add house on approval`) | nuevo anexo `R-190_ANEXO_C03_B.md` | M | decisión | — |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | fallback a `target_house_id` en `bird_distribution` | AC-R190-01 |
| S2 | selector «Galpón del evento» no escribe `house_id` en `bird_exit` | AC-R190-02 |
| S3 | `superRefine` de ubicación desactivado (el POST viaja sin `house_id`) | AC-R190-09 / AC-R190-04 |
| S4 | derivación de `farm_id` desde el galpón | AC-R190-10 |

## Regresión obligatoria

`f01e.receptionHouse` · `f01.payloadContract` · `f01.errorRendering` · `receptionFormContract` · `f01d.serializers` · `r153.importLotOptional` · `gaFe05.submitGates` · vitest completa · `tsc` · `build` · backend: `test_r26_error_contract.py`, `test_edit_validation_parity.py`, `test_submovement_structural_tenancy.py`, `test_population_invariant.py` (bird_exit BR-08) · runtime: retry R-189 UAT-01…07.

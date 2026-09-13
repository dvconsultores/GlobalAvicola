# R-205 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: RED antes que GREEN; producto sólo en C2.** Tranche conjunta con **R-190** (misma derivación/`onSubmit`); un commit por paquete o commits consecutivos con la misma RED.

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED: helper `resolverStageDelAsistente` (unit puro), paridad jsdom por rutas, regresión f01/r153; control backend BR-20; ejecución RED | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Derivación de `stage`; cuadre por cadena del lote; `superRefine`; i18n; GREEN dirigido + vitest completa + tsc + build; sensibilidad tras commit | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación runtime** | Deploy; `E2E-R205-01…06` en nube (actores UAT-09 + lote breeder de fixtures/creado); journal + PNG + payloads; verificación cruzada suites p03/p04/p11 tras GA-GOV-03 | C2 | `evidence/runtime-c3/` + certificación | ☐ |
| **C4 · UAT del propietario** | UAT-R205-01…04 (agrupada con R-190 si conviene); acta; backlog | C3 | acta UAT + backlog | ☐ |

## CHECKLIST

- ☐ C1.1 RED escrita/ejecutada (2 ficheros nuevos + regresión; rojos exactos)
- ☐ C1.2 Control backend BR-20 verde (sin cambio de validador)
- ☐ C1.3 Commit C1 sin producto
- ☐ C2.1 Helper puro + unit verde
- ☐ C2.2 Cuadre visible/obligatorio por lote breeder en cualquier ruta
- ☐ C2.3 `superRefine` de cuadre + i18n
- ☐ C2.4 GREEN dirigido + vitest completa + tsc + build
- ☐ C2.5 Sensibilidad S1-S3
- ☐ C3.1 E2E-R205-01…06 con artefactos; 0 fatales; 0 `5xx`
- ☐ C3.2 Verificación cruzada: p03/p04/p11 sin el bloqueo BR-20 (tras corrección GA-GOV-03)
- ☐ C4.1 UAT 4/4 + backlog

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | Unit puro del helper | `frontend/src/pages/operations/__tests__/r205.stageDerivation.test.ts` | S | — | C1 |
| T-02 | Paridad jsdom por rutas (hub/detalle/directa) | `__tests__/r205.breederReceptionParity.test.tsx` | M | — | C1 |
| T-03 | Helper `resolverStageDelAsistente` | `frontend/src/pages/operations/operationPayload.ts` | S | T-01 | C2 |
| T-04 | Derivación de `stage` + cuadre por lote | `OperationFormPage.tsx:316-319,667-680,1901-1915` | M | T-03 | C2 |
| T-05 | `superRefine` + i18n | `OperationFormPage.tsx:178-187`; locales `es/en` | S | T-04 | C2 |
| T-06 | GREEN + regresión + sensibilidad | — | S | T-03…T-05 | C2 |
| T-07 | Runner/E2E runtime | raíz del repo (extensión de `scripts_e2e_f01_retry.mjs` o propio) | M | T-06 | C3 |
| T-08 | Certificación + UAT + backlog | `specs/R-205/…`, backlog | M | T-07 | C3/C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | derivación de `stage` (vuelve a `null` con `?type=`) | AC-R205-01/02 |
| S2 | visibilidad del cuadre atada solo a `stage` | AC-R205-01/02 |
| S3 | `superRefine` de cuadre | AC-R205-05 |

## Regresión obligatoria

`f01e.receptionHouse` · `f01.payloadContract` · `f01.errorRendering` · `f01d.serializers` · `r153.importLotOptional` · `gaFe05.submitGates` · `r190.*` (tranche conjunta) · vitest completa · `tsc` · `build` · backend: `test_r26_error_contract.py` (BR-20), `test_reception_reconciliation.py`, `test_edit_validation_parity.py` · runtime: retry R-189 (7/7) + E2E-R205.

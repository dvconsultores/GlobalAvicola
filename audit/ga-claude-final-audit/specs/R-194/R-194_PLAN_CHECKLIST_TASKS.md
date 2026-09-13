# R-194 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: RED antes que GREEN; producto sólo en C2.** Tranche contigua a R-190/R-205 (misma familia); C-01/C-02 antes de C2.

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED `r194.hatcheryChain.test.tsx` (5 rojos) + ejecución; C-01/C-02 elevadas | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Ubicación (C-01), fértiles+`arrival_date` (C-02), dosis, `hatchery_id`; GREEN + regresión; sensibilidad | C1 (+C-01/C-02) | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación runtime** | Deploy; `E2E-R194-01…08` (cadena completa + móvil + EN + controles); journal/PNG/payloads | C2 | `evidence/runtime-c3/` + certificación | ☐ |
| **C4 · UAT del propietario** | UAT-R194-01…05 (agrupable con R-190/R-205); acta; backlog | C3 | acta + backlog | ☐ |

## CHECKLIST

- ☐ C1.1 RED escrita/ejecutada (5 rojos exactos; controles verdes)
- ☐ C1.2 C-01/C-02 elevadas
- ☐ C1.3 Commit C1 sin producto
- ☐ C2.1 Ubicación etapa incubadora (C-01)
- ☐ C2.2 Fértiles en `egg_movements` + `arrival_date` (C-02)
- ☐ C2.3 `dosage_per_bird` con `valueAsNumber` + error visible
- ☐ C2.4 `hatchery_id` en filas
- ☐ C2.5 GREEN + regresión completa + sensibilidad
- ☐ C3.1 Cadena E2E completa con artefactos; 0 fatales; 0 `5xx`
- ☐ C3.2 Verificación cruzada p05/p10 (tras GA-GOV-03) y X-BU
- ☐ C4.1 UAT 5/5 + backlog

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED jsdom de la cadena (5 defectos) | `frontend/src/pages/operations/__tests__/r194.hatcheryChain.test.tsx` | L | — | C1 |
| T-02 | Controles backend BR-03/04/21 | `backend/tests/test_r194_hatchery_controls.py` | S | — | C1 |
| T-03 | Ubicación etapa incubadora | `OperationFormPage.tsx:274-278,386,438` | M | T-01 | C2 |
| T-04 | Recepción: fértiles + almacenamiento + `arrival_date` | `OperationFormPage.tsx:1218-1236`; `operationPayload.ts` | M | T-01 | C2 |
| T-05 | `dosage_per_bird` | `OperationFormPage.tsx:1651` (+ i18n si aplica) | S | T-01 | C2 |
| T-06 | `hatchery_id` en filas | `OperationFormPage.tsx:139-149,2044-2056` | S | T-01 | C2 |
| T-07 | GREEN + regresión + sensibilidad | — | S | T-03…T-06 | C2 |
| T-08 | Runner E2E + ejecución C3 | raíz + `specs/R-194/evidence/runtime-c3/` | L | T-07 | C3 |
| T-09 | UAT + backlog | `specs/R-194/…`, backlog | M | T-08 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | fértiles del serializador de recepción | AC-R194-02/03 |
| S2 | `valueAsNumber` de la dosis | AC-R194-04 |
| S3 | ubicación etapa incubadora | AC-R194-01/05 |
| S4 | `hatchery_id` en filas | AC-R194-06 |

## Regresión obligatoria

`f01.*` completo · `f01d.serializers` · `f01e.receptionHouse` · `r153.importLotOptional` · `r190.*`/`r205.*` (tranche contigua) · `eggDispatchFormContract` · vitest completa · `tsc` · `build` · backend: `test_egg_incubation_concurrency.py`, `test_birth_classification.py`, `test_handoff_contract.py`, `test_r26_error_contract.py` (BR-08/21) · runtime: cadena completa E2E.

# R-209 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: RED antes que GREEN; producto sólo en C2.** Cambio FE + tests; backend control.

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED jsdom (2 rojos) + control backend; barrido de otros selectores | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Reutilizar helper canónico en los dos bloques; GREEN + regresión; sensibilidad tras commit | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación** | Payload real (runtime o local UI) + comparativo API; inventario de históricos; certificación | C2 | `evidence/r209/runtime-c3.json` | ☐ |
| **C4 · Cierre** | Backlog: R-209 `CLOSED` con GA-REM | C3 | backlog | ☐ |

## CHECKLIST

- ☐ C1.1 RED escrita/ejecutada (AC-01/02 rojos; control verde)
- ☐ C1.2 Barrido `String(id)`/`String(o.id)` en el asistente (resultado documentado)
- ☐ C1.3 Commit C1 sin producto
- ☐ C2.1 `bird_exit` con código canónico
- ☐ C2.2 `feed_registration` con código canónico
- ☐ C2.3 Fallback sin código → ausente (nunca id)
- ☐ C2.4 GREEN + regresión f01/vitest/tsc/build
- ☐ C2.5 Sensibilidad S1
- ☐ C3.1 Payload real + comparativo + inventario + certificación
- ☐ C4.1 Backlog

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED jsdom selectores internos | `frontend/src/pages/operations/__tests__/r209.sapCodeSelectors.test.tsx` | M | — | C1 |
| T-02 | Control backend comparativo | `backend/tests/test_r209_sap_document_ref_contract.py` | S | — | C1 |
| T-03 | `bird_exit` → código | `OperationFormPage.tsx:917-927` | S | T-01 | C2 |
| T-04 | `feed_registration` → código | `OperationFormPage.tsx:1033-1040` | S | T-01 | C2 |
| T-05 | GREEN + regresión + sensibilidad | — | S | T-03/T-04 | C2 |
| T-06 | Certificación + inventario | `specs/R-209/evidence/r209/` | S | T-05 | C3 |
| T-07 | Backlog/cierre | backlog | S | T-06 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | revertir `feed_registration` a `String(id)` | AC-R209-02 |

## Regresión obligatoria

`f01.payloadContract` · `f01d.serializers` · `f01e.receptionHouse` · `eggDispatchFormContract` (si comparte selector) · vitest completa · `tsc` · `build` · backend `test_purchase_order_receipt.py`, `test_sap.py` (comparativo) · runtime: verificación cruzada de R-189 (retry 7/7) si se ejecuta en la misma generación.

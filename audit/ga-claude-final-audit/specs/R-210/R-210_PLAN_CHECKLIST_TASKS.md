# R-210 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: RED antes que GREEN; producto sólo en C2.** Confirmación C-01 antes del cierre (no bloquea C1/C2 en la variante A).

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED `r210.weightUnit` (rojo) + control backend; ejecución | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Etiquetas «(g)», step coherente, fallbacks, `inputMode`; GREEN + regresión; sensibilidad | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación + UAT mínima** | Payload real en g; evaluación en banda; confirmación C-01 del propietario | C2 | `evidence/r210/runtime-c3.json` + acta C-01 | ☐ |
| **C4 · Cierre** | Backlog: R-210 `CLOSED` con GA-REM | C3 | backlog | ☐ |

## CHECKLIST

- ☐ C1.1 RED escrita/ejecutada (AC-01/02/04 rojos; control verde)
- ☐ C1.2 Commit C1 sin producto
- ☐ C2.1 Etiquetas g en los 6 puntos (ES/EN)
- ☐ C2.2 Step coherente; sin restos «kg»
- ☐ C2.3 Fallbacks corregidos
- ☐ C2.4 GREEN + regresión + sensibilidad
- ☐ C3.1 Payload g + evaluación + C-01 registrada
- ☐ C4.1 Backlog

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED de unidad de peso | `frontend/src/pages/operations/__tests__/r210.weightUnit.test.tsx` | M | — | C1 |
| T-02 | Control backend evaluación en g | `backend/tests/test_r210_weight_evaluation_grams.py` | S | — | C1 |
| T-03 | Etiquetas/step/fallbacks | `OperationFormPage.tsx:470,484,627,865,987,1703,1790`; locales | S | T-01 | C2 |
| T-04 | `inputMode` decimal (C-04) | `OperationFormPage.tsx` (inputs de peso) | S | — | C2 |
| T-05 | GREEN + regresión + sensibilidad | — | S | T-03/T-04 | C2 |
| T-06 | Certificación + acta C-01 | `specs/R-210/evidence/r210/` + acta | S | T-05 | C3 |
| T-07 | Backlog/cierre | backlog | S | T-06 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | restaurar `step="0.001"` + fallback kg | AC-R210-01/02/04 |

## Regresión obligatoria

`f01.payloadContract` · `f01d.serializers` · `receptionFormContract` · `weightEvaluation` (front) · vitest completa · `tsc` · `build` · backend: `test_genetic_curves.py`, `test_weight_evaluation*` (si existe) · UI: pesaje en lote de prueba (evaluación en banda).

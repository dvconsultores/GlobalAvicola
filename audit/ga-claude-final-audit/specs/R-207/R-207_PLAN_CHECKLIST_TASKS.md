# R-207 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED `r207.reversalSurface` (jsdom); ejecución (rojo) | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Acción+modal en detalle; servicio FE; badges; enlaces; GREEN + regresión | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación + UAT** | E2E local/nube: solicitar→contrapartida→aprobar→badges/enlace; UAT 4/4 | C2 | `evidence/r207/runtime-c3.json` + acta | ☐ |
| **C4 · Cierre** | Backlog: R-207 `CLOSED`; referencias R-192/R-193/P1-12 | C3 | backlog | ☐ |

## CHECKLIST

- ☐ C1.1 RED ejecutada (botón/badge/enlace rojos)
- ☐ C2.1 Acción + modal (motivo ≥5, confirmación)
- ☐ C2.2 Gate `reversals:create`
- ☐ C2.3 Contrapartida visible en bandejas (sin cambios en el motor)
- ☐ C2.4 Badges `reversed` (todas las listas/mapas)
- ☐ C2.5 Enlace original↔contrapartida
- ☐ C2.6 Errores seguros (409/400)
- ☐ C2.7 GREEN + regresión + sensibilidad
- ☐ C3.1 E2E + UAT + certificación (verificación R-192/R-193)
- ☐ C4.1 Backlog

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED de superficie | `frontend/src/pages/operations/__tests__/r207.reversalSurface.test.tsx` | M | — | C1 |
| T-02 | Servicio FE de reversos | `frontend/src/services/reversals.service.ts` (nuevo) | S | T-01 | C2 |
| T-03 | Acción+modal en detalle | `OperationDetailPage.tsx` | M | T-02 | C2 |
| T-04 | Badges `reversed` | `statusColors.ts`, `domain.types.ts`, mapas locales | S | T-01 | C2 |
| T-05 | Enlaces original↔contrapartida | `OperationDetailPage.tsx`, `ReviewDetail.tsx` | S | T-03 | C2 |
| T-06 | i18n | locales ES/EN | S | T-03 | C2 |
| T-07 | GREEN + regresión + sensibilidad | — | S | T-03…T-06 | C2 |
| T-08 | E2E + UAT + certificación | `specs/R-207/evidence/r207/` | M | T-07 | C3 |
| T-09 | Backlog | backlog | S | T-08 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | gate `reversals:create` | AC-R207-01 |
| S2 | badge `reversed` | AC-R207-03 |

## Regresión obligatoria

`test_internal_reversal.py` (API) · `test_reversal_role_matrix.py` · `r197.*`/`r208.*` (bandejas) · vitest completa · `tsc` · `build` · UI detalle (acción visible/oculta según permiso) · verificación cruzada R-192 (cierre tras reverso) y R-193 (BR-18).

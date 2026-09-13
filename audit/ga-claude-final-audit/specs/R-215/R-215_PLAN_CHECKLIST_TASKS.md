# R-215 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED `r215.errorRendering` (unit); ejecución (rojo) | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Boundary global + 5 consumidores; GREEN + regresión; sensibilidad | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación + UAT** | Repro maestros 422 ⇒ texto; boundary; ES/EN; móvil; UAT 2/2 | C2 | `evidence/r215/runtime-c3.json` + acta | ☐ |
| **C4 · Cierre** | Backlog: R-215 `CLOSED`; referencias R-196/R-195 | C3 | backlog | ☐ |

## CHECKLIST

- ☐ C1.1 RED ejecutada (throw con lista; boundary ausente ⇒ rojos)
- ☐ C2.1 Boundary global + claves i18n
- ☐ C2.2 MasterListPage normalizado
- ☐ C2.3 LotFormPage normalizado
- ☐ C2.4 TraceabilityTree normalizado
- ☐ C2.5 ProfilePage normalizado
- ☐ C2.6 UsersPage sin `[object Object]` (coord. R-195)
- ☐ C2.7 GREEN + regresión + sensibilidad
- ☐ C3.1 E2E + UAT + certificación
- ☐ C4.1 Backlog

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED de render/ boundary | `frontend/src/components/__tests__/r215.errorRendering.test.tsx` | M | — | C1 |
| T-02 | `ErrorBoundary` + integración | `components/ErrorBoundary.tsx` (nuevo); `main.tsx`/`App.tsx`; locales | M | T-01 | C2 |
| T-03 | Normalizar 5 consumidores | `MasterListPage.tsx:99`, `LotFormPage.tsx:137`, `TraceabilityTree.tsx:95,114,347,389`, `ProfilePage.tsx:38,70`, `UsersPage.tsx:85` | M | T-01 | C2 |
| T-04 | GREEN + regresión + sensibilidad | — | S | T-02/T-03 | C2 |
| T-05 | E2E + UAT + certificación | `specs/R-215/evidence/r215/` | M | T-04 | C3 |
| T-06 | Backlog | backlog | S | T-05 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | normalización en maestros | AC-R215-01 |
| S2 | boundary | AC-R215-04 |

## Regresión obligatoria

`f01.errorRendering` · `f01.payloadContract` · `r196.*`/`r195.*` (tranche contigua) · vitest completa · `tsc` · `build` · UI: repro maestros 422 (en blanco ⇒ texto).

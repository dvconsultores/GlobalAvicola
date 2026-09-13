# R-196 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED jsdom `r196.mastersCreate` + backend `test_r196_masters_create_context`; C-01/C-02 registradas | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Config por entidad + padres; numéricos; reactivación; `getErrorMessage`; company en servidor; navegación de entidades; GREEN + regresión | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación + UAT** | E2E crear 5 entidades + reactivar + navegar; UAT 4/4 | C2 | `evidence/r196/runtime-c3.json` + acta | ☐ |
| **C4 · Cierre** | Backlog: R-196 `CLOSED`; referencias R-50/R-215 | C3 | backlog | ☐ |

## CHECKLIST

- ☐ C1.1 RED ejecutada (rojo: `{}`/422; company ajena)
- ☐ C1.2 C-01/C-02 registradas
- ☐ C2.1 farms/hatcheries sin capturar company (resuelta)
- ☐ C2.2 houses/incubators/hatchers con selector padre
- ☐ C2.3 numéricos `null`; sin `''`
- ☐ C2.4 reactivación
- ☐ C2.5 errores seguros (sin React #31)
- ☐ C2.6 navegación de entidades en `/masters`
- ☐ C2.7 GREEN + regresión + sensibilidad
- ☐ C3.1 E2E + UAT + certificación
- ☐ C4.1 Backlog

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED jsdom creación | `frontend/src/pages/masters/__tests__/r196.mastersCreate.test.tsx` | L | — | C1 |
| T-02 | RED backend contexto Create | `backend/tests/test_r196_masters_create_context.py` | M | — | C1 |
| T-03 | Config por entidad (tipos/padres/numéricos) | `MasterListPage.tsx`, `App.tsx:135-166` | L | T-01 | C2 |
| T-04 | company en servidor + rechazo cliente | `masters/service.py`, `masters/schemas.py` (coord. R-50) | M | T-02 | C2 |
| T-05 | Reactivación + errores seguros | `MasterListPage.tsx` | S | T-01 | C2 |
| T-06 | Navegación de entidades | `MasterListPage.tsx`/ruta `/masters` | M | T-01 | C2 |
| T-07 | GREEN + regresión + sensibilidad | — | S | T-03…T-06 | C2 |
| T-08 | E2E + UAT + certificación | `specs/R-196/evidence/r196/` | M | T-07 | C3 |
| T-09 | Backlog | backlog | S | T-08 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | selector de padre (house) | AC-R196-02 |
| S2 | resolución de company en servidor | AC-R196-01 |
| S3 | `getErrorMessage` de maestros | AC-R196-06 |

## Regresión obligatoria

`test_master_management.py` · `test_master_tenant_isolation.py` · `test_company_catalog.py` · `test_lot_area_ownership.py` (área/OD-21) · vitest completa · `tsc` · `build` · UI `/masters/*` (16 planos intactos) · `r215.*` (render de errores, tranche contigua).

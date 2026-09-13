# R-195 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED** | Finding/spec/clarificaciones/AC/diseño (hecho); RED jsdom `r195.usersEdit`; ejecución (rojo) | este paquete | commit C1 + `evidence/red/` | ☐ |
| **C2 · Implementación** | Payload de edición; validaciones; errores normalizados; baja; gates de empresa; GREEN + regresión | C1 | commit C2 + `evidence/green/` | ☐ |
| **C3 · Certificación + UAT** | Editar por UI (rol+nombre); error forzado; baja; acta 3/3 | C2 | `evidence/r195/runtime-c3.json` + acta | ☐ |
| **C4 · Cierre** | Backlog: R-195 `CLOSED`; referencias R-202/R-215 | C3 | backlog | ☐ |

## CHECKLIST

- ☐ C1.1 RED ejecutada (payload con extras + alert, rojos)
- ☐ C2.1 Payload `UserUpdate` exacto
- ☐ C2.2 Errores normalizados (sin `alert`)
- ☐ C2.3 Validación `last_name` en cliente
- ☐ C2.4 Empresa por contexto (sin selector engañoso)
- ☐ C2.5 Baja con mensaje claro; modal coherente
- ☐ C2.6 GREEN + regresión + sensibilidad
- ☐ C3.1 E2E + UAT + certificación
- ☐ C4.1 Backlog

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | RED jsdom edición/errores | `frontend/src/pages/users/__tests__/r195.usersEdit.test.tsx` | M | — | C1 |
| T-02 | Payload de edición | `UsersPage.tsx:76-79` | S | T-01 | C2 |
| T-03 | Errores + validaciones + baja | `UsersPage.tsx:71,82-91,124-126` | M | T-01 | C2 |
| T-04 | Empresa/gates (C-03) | `UsersPage.tsx` | S | T-02 | C2 |
| T-05 | GREEN + regresión + sensibilidad | — | S | T-02…T-04 | C2 |
| T-06 | E2E + UAT + certificación | `specs/R-195/evidence/r195/` | S | T-05 | C3 |
| T-07 | Backlog | backlog | S | T-06 | C4 |

## SENSIBILIDAD (tras commit C2)

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| S1 | limpieza del payload | AC-R195-01 |
| S2 | normalización de error | AC-R195-02 |

## Regresión obligatoria

`test_user_tenant_isolation.py` · `test_p013_password.py` · `test_role_administration.py` · `test_od14_productive_surfaces.py` (usuarios) · vitest completa · `tsc` · `build` · UI `/users` (alta/edición/baja) · `r196.*` (tranche contigua si comparten sesión UAT).

# GA-FE-03 · CHECKLIST (AC ↔ tarea ↔ test ↔ evidencia)

Cada AC mapea a tarea de `GA_FE_03_TASKS.md`, prueba y evidencia. Sin AC huérfano; sin tarea
sin AC.

| AC | Tarea | Test (Vitest salvo indicación) | Evidencia runtime |
|---|---|---|---|
| NAV-AC01 | T1, T2 | `gaFe03.navigation.test.ts` (una definición; filtro único) | grep de cierre: 0 arrays de rutas duplicados |
| NAV-AC02 | T1 | `gaFe03.noRoleGating.test.ts` (grep estático) | — |
| NAV-AC03 | T1 | ídem | — |
| NAV-AC04 | T2 | matriz de visibilidad (S9/S10/S11) | D en cumplimiento (§72): sin admin/productivo |
| NAV-AC05 | T2, T4 | casos contenedor sin hijos | capturas sin grupo vacío |
| NAV-AC06 | T2, T5 | casos `view_type=mobile` | móvil §77 |
| NAV-AC07 | T4 | `gaFe03.menuHub.test.tsx` | hub sin hijos no autorizados (`D-2`) |
| NAV-AC08 | T5 | caso tarjetas Dashboard | captura dashboard S7 vs S10 |
| NAV-AC09 | T6 | `gaFe03.routeGuards.test.tsx` | deep links §79 |
| NAV-AC10 | T6 | ídem + backend | 403/404 registradas |
| NAV-AC11/12/13/14/15 | T2 | 3D de navegación en tests | runtime 3D 4/4 (§74) |
| NAV-AC16 | T2, T5 | caso Z | Z: CORE sí, productivo no |
| NAV-AC17 | T2 | caso E OFF/ON | E: OFF oculto, ON solo habilitadas |
| NAV-AC18 | T2, T6 | caso E no-contexto | selector visible; inquilino fail-closed |
| NAV-AC19 | T3, T7 | caso switch | switch + recálculo en runtime |
| NAV-AC20 | T3 | caso refresh | hard refresh idéntico |
| NAV-AC21/22 | T3 | casos grant/revoke | propagación registrada (refresh/relogin) |
| NAV-AC23/24 | T3 | casos de estancamiento | sin enlaces heredados |
| NAV-AC25/26/27/28 | T2, T4 | casos A/B/D | A/B descubren lo suyo; D nada |
| NAV-AC29/30 | T2, T6 | casos E no-contexto | selector sí; inquilino cerrado |
| NAV-AC31/32/33 | T7 | auditoría de claves (`gaFe03.i18n.test.ts`) | ES/EN en runtime |
| NAV-AC34/35/36 | T5 | móvil (delta overflow 0) | capturas móvil |
| NAV-AC37/38/39 | T5, T6 | consola/red | consola limpia; sin mutación falsa |
| NAV-AC40 | T8 | suite GA-FE-02 intacta | spots F1–F4/D1/D-1 |
| NAV-AC41 | T2, T9 | 3D + rutas directas | §74 completo |
| NAV-AC42 | T3 | sin flash (gating por `isLoading`) | inspección de hidratación |
| NAV-AC43 | T3 | fetch único por superficie | red §83 |
| NAV-AC44 | T4 | `D-2` hub | captura D |

**Criterio de completitud**: todos los AC con test (unit/integration) + evidencia runtime
autenticada donde la tabla la exige. Los AC de runtime **no** se cierran con unit tests.

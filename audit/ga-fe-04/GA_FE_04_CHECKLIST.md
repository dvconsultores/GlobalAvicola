# GA-FE-04 · CHECKLIST (AC ↔ tarea ↔ test ↔ evidencia)

| AC | Tarea | Test | Evidencia runtime |
|---|---|---|---|
| P13-AC01 | T0 reconciliación+inventario+contrato | — (docs) | — |
| P13-AC02 | T0 inventario 32 rutas | — | — |
| P13-AC03 | T0 contrato 31 acciones | — | — |
| P13-AC04 | T1..T12 (gates por permiso) | grep cierre 0 role-name + tests | matriz por actor |
| P13-AC05 | T1..T12 | grep cierre 0 username | — |
| P13-AC06 | T1 hooks sobre evaluador GA-FE-03 | `gaFe04.actionAuthority.test.ts` | — |
| P13-AC07 | T1 | deep API tests (R/D/P) | 403 backend |
| P13-AC08 | T13 negativas | `gaFe04.*` + API | §67-68 |
| P13-AC09..12 | T8/T13 + 3D | matriz 3D en tests | 3D 4/4 |
| P13-AC13 | T8 (global) | caso E | E: BU OFF sin acción + API deny |
| P13-AC14 | T8 (Z) | caso Z | Z sin mutaciones |
| P13-AC15..18 | T5/T6 admin | casos A/B | A/B por UI |
| P13-AC19 | T1..T12 (D) | caso D | D oculto + 403 |
| P13-AC20 | T9 verify | caso self | 403 + sin fila |
| P13-AC21 | T9 verify | caso cross | 404/no candidato |
| P13-AC22 | diseño (isLoading) | test de boot | inspección carga |
| P13-AC23 | diseño | — | fail-closed documentado |
| P13-AC24..27 | T7/T10 (estado de sesión) | casos switch/BU/grant | propagación §75 |
| P13-AC28 | T11 | móvil | 390×844 |
| P13-AC29 | T1..T12 | grep + tests | — |
| P13-AC30 | T4/T10 (CTAs vacío) | casos R/C | capturas |
| P13-AC31..33 | T11 i18n | `gaFe04.i18n.test.ts` | ES/EN |
| P13-AC34..36 | certificación | suite + runtime | consola/red/audit |
| P13-AC37..40 | regresión | suite completa + spots | F1–F4/D1/D-1/R-119 |

**Estado**: AC01–03 ✅ (docs C1). Resto pendiente de RED→GREEN→runtime.

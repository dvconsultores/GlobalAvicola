# GA-FE-05 · TAREAS

| ID | Fuente | Spec § | AC | Archivos | Test | Evidencia runtime | Depende | Estado |
|---|---|---|---|---|---|---|---|---|
| T1 | R-181 | §2 | AC01 | reconciliación | — | — | — | ✅ |
| T2 | R-181 | §3–5 | AC02/03 | reconciliación + auditoría frontend | — | — | T1 | ✅ |
| T3 | RED | §23/24 | AC08…26 (muestra) | `src/pages/operations/__tests__/gaFe05.submitGates.test.tsx` (nuevo) | RED→GREEN | runtime RED C | T2 | ✅ |
| T4 | RED runtime | §23 | AC08 | capturas pre-fix | — | `evidence/red/` | T3 | ✅ |
| T5 | i18n | §22 | AC31–33 | `public/locales/{es,en}/translation.json` | — | ES/EN | — | ✅ |
| T6 | UI submit | §12/13 | AC08–12 | `OperationDetailPage.tsx` | T3 | E2E-01 | T3 | ✅ |
| T7 | UI resubmit | §12/14 | AC16–20 | `OperationDetailPage.tsx` | T3 | E2E-07 | T3 | ✅ |
| T8 | autoridad | §9–11 | AC03–07/22–28 | `OperationDetailPage.tsx` (`useCan` + `requiresUnits`) | T3 | E2E-02–04 | T3 | ✅ |
| T9 | servicio | §13 | AC09 | reutilizar `operationsService.submit` | T3 | red | — | ✅ |
| T10 | refresh | §16 | AC10–15 | `OperationDetailPage.tsx` (`loadEvent` tras éxito/fallo) | T3 | E2E-01/07 | T6 | ✅ |
| T11 | gates | §23 | — | tsc/build/vitest | 263+9 | — | T5–T10 | ✅ |
| T12 | deploy | §25 | — | pipeline | — | bundle nuevo | T11 | ✅ |
| T13 | fixtures | §35 | — | actores C/P/Z/D/V + operaciones (flujo oficial) | — | ledger | T12 | ✅ |
| T14 | E2E-01 | §60 | AC08–15 | — | — | capturas+red | T13 | ✅ |
| T15 | E2E-02 | §61 | AC22/28 | — | — | capturas+API | T13 | ✅ |
| T16 | E2E-03 | §62 | AC23 | — | — | capturas+API | T13 | ✅ |
| T17 | E2E-04 | §63 | AC24/25 | — | — | capturas+API | T13 | ✅ |
| T18 | E2E-05 | §64 | AC26/27 | — | — | capturas+API | T13 | ✅ |
| T19 | E2E-08 | §67 | AC21 | — | — | capturas+API | T13 | ✅ |
| T20 | E2E-06 | §65 | AC16 | — | — | capturas | T13 | ✅ |
| T21 | E2E-07 | §66 | AC18–20 | — | — | capturas+red | T20 | ✅ |
| T22 | E2E-09/10 | §68/69 | AC34/13 | — | — | red+consola | T13 | ✅ |
| T23 | desktop/móvil/ES/EN | §70–72 | AC29–33 | — | — | capturas | T14 | ✅ |
| T24 | auditoría | §74 | AC37 | — | — | audit API | T14/T21 | ✅ |
| T25 | red | §73 | AC09/34 | — | — | red sanitizada | T14 | ✅ |
| T26 | limpieza | §79 | — | — | — | ledger | T14–T24 | ✅ |
| T27 | regresión | §75 | AC38–40 | suite + spots | 263/263 + GA-FE-04 22/22 | spots | T11 | ✅ |
| T28 | cierre | §82 | todos | `GA_FE_05_R181_CLOSURE_RECONCILIATION.md` | — | — | T14–T27 | ✅ |
| T29 | certificación | §84 | — | `GA_FE_05_CERTIFICATION.md` + addendum master | — | — | T28 | ✅ |
| T30 | UAT | §85 | — | `GA_FE_05_OWNER_UAT.md` | — | package | T29 | ✅ |

Prohibiciones vigentes: tocar backend (esperado 0), R-182, BU-D10, fases/Olas fuera de alcance. `git add` explícito; secret-check por commit.

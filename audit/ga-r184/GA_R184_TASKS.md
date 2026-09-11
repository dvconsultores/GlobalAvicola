# GA-R184 · TAREAS

| ID | Finding | Sección spec | AC | Archivos | Test | Evidencia runtime | Depende de | Estado |
|---|---|---|---|---|---|---|---|---|
| T1 | R-184 | §2-3, §5 | AC01–03 | `audit/ga-r184/evidence/red/*` | repro local | RED ya capturado | — | ✔ |
| T2 | R-184 | §5, §8 | AC04, 11–15 | `GA_R184_DATE_SEMANTICS_TRACE.md` | — | — | T1 | ✔ |
| T3 | R-184 | §3 | AC05 | `app/reports/service.py` (futuro diff) | revisión de diff | E2E-02 | T2 | ○ |
| T4 | R-184 | §17 | AC06–11, 14–15 | `backend/tests/test_r184_ipe_date_semantics.py` | suite `ipe` | E2E-01/02/03 | T3 | ○ |
| T5 | R-184 | §10, §17 | AC13, 16–21 | íd. | suite `hoy/nulo/inexistente` | E2E-04/06/07/08 | T3 | ○ |
| T6 | R-184 | §12, §17 | AC22–27 | íd. | suite seguridad | E2E-09…12 | T3 | ○ |
| T7 | R-184 | §18 | AC28–33 | frontend + runtime | Vitest/tsc/build + regresión | §regresión | T3, deploy | ○ |
| T8 | R-184 | §19-20 | AC34–37 | docs canónicos | verificación documental | — | T7 | ○ |
| T9 | R-184 | §18-19 | — | commits C2/C4 | — | deploy+E2E | T4-T6 | ○ |
| T10 | R-184 | §20-21 | — | cierre+certificación+UAT ready | — | — | T9 | ○ |
| T11 | (R-186) | reconciliación §7 | — | registro backlog | — | `prodindex35`=500 | — | Registrado (no implementado) |

## Estado final (2026-09-11)

T1–T8: **✔ COMPLETADAS** (T7/T8 con evidencia runtime + documental; T4–T6 con suite PG/CI + batería runtime ejecutada). T9: **✔** (C2 `3f88f94` desplegado; E2E 14/14; C4 de evidencia en este commit). T10: **✔** (cierre + certificación redactados; Owner UAT **READY**, sin convocar). T11: **Registrado** como candidato separado (sin implementación, por regla de alcance).

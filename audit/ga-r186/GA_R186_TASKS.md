# GA-R186 · TAREAS

| ID | Finding | Sección spec | AC | Archivos | Test | Runtime | Depende de | Estado |
|---|---|---|---|---|---|---|---|---|
| T1 | R-186 | §1-2 | AC01–03 | `audit/ga-r186/evidence/red/*` | repro local | RED heredado | — | ◐ (repro local en C1) |
| T2 | R-186 | §4 | AC04 | trazas | — | — | T1 | ✔ |
| T3 | R-186 | §2 | AC05 | `app/reports/service.py` (diff C2) | revisión | E2E-02 | T2 | ○ |
| T4 | R-186 | §13 | AC06–11, 15 | `tests/test_r186_g05_date_semantics.py` | suite G-05 | E2E-01/02/03 | T3 | ○ |
| T5 | R-186 | §6/13 | AC12–14, 16–27 | íd. | suite bordes/ausencias | E2E-04/05/08 | T3 | ○ |
| T6 | R-186 | §8 | AC28–33 | íd. | suite seguridad | E2E-09…13 | T3 | ○ |
| T7 | R-186 | §15 | AC34–41 | runtime + docs | regresión | E2E-R184 + spots GA-FE | T3, deploy | ○ |
| T8 | R-186 | §16 | AC42–43 | docs canónicos | verificación | — | T7 | ○ |
| T9 | R-186 | §14-16 | — | commits C2/C4 | — | deploy+E2E | T4-T6 | ○ |
| T10 | R-186 | §16-17 | — | cierre+certificación | — | — | T9 | ○ |

## Estado final (2026-09-11)

T1–T10: **✔ COMPLETADAS** (T4–T6 con suite PG/CI + batería runtime ejecutada; T9 con C2 `0309225` desplegado y E2E 14/14; T10 con cierre, certificación y UAT NOT REQUIRED documentada).

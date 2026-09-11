# GA-BU-D10 · TASKS

Campos: ID · OD-23 · SPEC § · AC · Objeto · Test · Evidencia runtime · Dependencia · Estado.

| ID | Contenido | OD-23 | SPEC § | AC | Objeto | Test | Runtime | Depende | Estado |
|---|---|---|---|---|---|---|---|---|---|
| T01 | Canonizar decisión + finding | §2 | — | AC01 | `GA_OD_BU_D10_OWNER_DECISION.md` · `…GAP_R188.md` | — | — | — | [x] |
| T02 | SPEC + matriz + clarificaciones + plan | §2-5 | — | AC01 | `audit/ga-bu-d10/*.md` | — | — | T01 | [x] |
| T10 | Implementación mínima | §2.1-2.5 | §5-6/§8/§12 | AC02-05,11,14-16,23-25 | `backend/app/business_units/admin.py` (`fijar_habilitacion` + docstrings) | `test_r188_bu_lifecycle.py` + actualización AC-A04/A06 | E2E-01..06, audit, ledger | C2 | [ ] |
| T11 | Seguridad/borde | §2.3-2.4 | §10-11 | AC06-09,17 | (sin cambios; cubierto por diseño) | suites OD-15 + R-188 | E2E-07..10 | T10 | [ ] |
| T12 | Regresiones | §2.5 | §14 | AC10,18-22 | (sin cambios) | Vitest 280 + suites transfer | spots runtime | T10 | [ ] |
| T13 | RED suite (PG/CI) + evidencia | — | §16 | — | `backend/tests/test_r188_bu_lifecycle.py` · `GA_BU_D10_RED_EVIDENCE.md` | — | — | — | [ ] |
| T20 | C2 commit decisión/spec/RED | — | — | — | git | — | — | T13 | [ ] |
| T21 | C3 implementación + tests | — | — | — | git | — | — | T10 | [ ] |
| T22 | Deploy + freeze | — | — | — | git/observación | — | probe generación | T21 | [ ] |
| T30 | Runtime E2E §54-64 | — | — | — | scripts efímeros | — | `GA_BU_D10_AUTHENTICATED_RUNTIME_EVIDENCE.md` | T22 | [ ] |
| T31 | Cleanup + ledger | — | — | — | runtime | — | `GA_BU_D10_TEST_DATA_LEDGER.md` | T30 | [ ] |
| T32 | Evidencia + closure + certificación | — | §15 | cobertura | `GA_BU_D10_*` docs | — | — | T30/31 | [ ] |
| T33 | Hogares canónicos (backlog/roadmap/catálogo/OD/R) | — | — | — | audit | — | — | T32 | [ ] |
| T34 | C4 + push + verificación | — | — | — | git | — | — | T33 | [ ] |
| T35 | Owner UAT package (REQUIRED) — sin auto-aprobación | — | §17 | — | `GA_BU_D10_OWNER_UAT.md` | — | — | T34 | [ ] |
| T36 | Informe final §78 + STOP | — | — | — | mensaje | — | — | T35 | [ ] |

Actores runtime previstos (sintéticos): `OP` (concesión broiler; acceso productivo) · `ADM` (Access Administrator OD-15: 4 permisos `business_units:*`; sin acceso productivo) · `ZBU` (zero-BU) · `NORBAC` (concesión sin `reports:read`) · `GLOBAL` = admin. Producto API testigo: `GET /api/v1/lots` (ruta productiva) y `GET /reports/kpi/ipe/54` (lectura productiva por lote).

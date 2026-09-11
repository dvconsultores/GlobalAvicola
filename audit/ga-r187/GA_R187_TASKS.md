# GA-R187 · TASKS

Campos: ID · R-187 · cláusula OD-22 · sección spec · AC · archivo/objeto · test · evidencia runtime · dependencia · estado.
Ninguna implementación antes de existir estas tareas (§22). Estados: [x] · [ ].

| ID | Contenido | Cláusula OD-22 | Spec § | AC | Archivo | Test | Runtime | Depende | Estado |
|---|---|---|---|---|---|---|---|---|---|
| T01 | Registro de autoridad y distinción de findings | §2-3 | §2-3 | AC01-02 | `audit/ga-r187/*` | — | — | — | [x] |
| T02 | Documentar fórmula vieja/nueva | §3 | §4-5 | AC03-04 | reconciliation | — | — | T01 | [x] |
| T03 | Probar unidades | §3.1 | §6 | AC05 | `GA_R187_UNIT_TRACE.md` | suite aserciones | committed+prefix | T01 | [x] |
| T10 | Retirar `× 100` en `get_kpi_ipe` (+ docstrings) | §3.2 | §5 | AC06-12 | `backend/app/reports/service.py:663` (+ docstring `:629`; router `:122`) | `test_r187_ipe_od22_scale.py` | E2E-01/02/06 | C1 | [ ] |
| T11 | Preservar bandas/labels/fronteras | §3.3 | §9 | AC13-18 | sin diff en bandas | tests frontera | E2E-03/04/05/04b/04c | T10 | [ ] |
| T12 | Preservar fechas R-184 | §3.4 | §7 | AC19-23 | sin diff `_dia` | control fechas | E2E-06 | T10 | [ ] |
| T13 | GREEN determinista | §3 | §15 | AC24-29 | suite | aserciones exactas | E2E-01 | T10 | [ ] |
| T20 | UI visible | — | §11 | AC30-36 | sin diff frontend | Vitest 280 | E2E-07..10 + capturas | C2+deploy | [ ] |
| T21 | Seguridad | — | §13 | AC37-42 | sin diff | suite seguridad | E2E-11..14 | C2+deploy | [ ] |
| T22 | Regresión R-184 técnica | — | §7 | AC43-45 | suite R-184 (aserción numérica **actualizada a OD-22**, §31; sin reescribir `audit/ga-r184/**`) | suite R-184 + R-187 | E2E-02 (5.6 == OD-22; NO 556.6) | C2+deploy | [ ] |
| T23 | Regresión R-186/GA-FE | — | §14 | AC46-52 | sin diff | suites | E2E G-05 + spots | C2+deploy | [ ] |
| T30 | Reconciliación de cierre + certificación + UAT | — | §18 | cobertura | `GA_R187_CLOSURE_RECONCILIATION.md` etc. | — | todas | T20-23 | [ ] |
| T31 | Cleanup + ledger | — | §16 | — | `GA_R187_TEST_DATA_LEDGER.md` | — | verificación 4×OFF | E2E | [ ] |
| T32 | Evidencia: network/authenticated/red/backend/frontend | — | §§15-16 | — | `GA_R187_*_EVIDENCE.md` | — | todas | E2E | [ ] |
| T33 | Commits C1/C2/C4 + push + verificación | §76 | — | — | git | — | — | por fase | [ ] |

## Identificadores de fixtures runtime (contrato para E2E)

| Alias | Edad | Muertes/1000 | Peso (g) | Alimento (kg) | FCR | IPE OD-22 esperado | Banda |
|---|---|---|---|---|---|---|---|
| DET | 19 | 50 (viab 95) | 2000 | 3000 | 3.0 | **333.3** | 🟢 |
| LOW | 28 | 100 (viab 90) | 1500 | 2000 | 2.0 | **241.1** | 🔴 |
| MID | 28 | 50 (viab 95) | 2500 | 3000 | 3.0 | **282.7** | 🟡 |
| B249 | 10 | 20 (viab 98) | 1020 | 4000 | 4.0 | **249.9** | 🔴 |
| B250 | 10 | 0 (viab 100) | 1000 | 4000 | 4.0 | **250.0** | 🟡 |
| B300 | 10 | 0 (viab 100) | 1200 | 4000 | 4.0 | **300.0** | 🟢 |

Actores sintéticos: `OP` (crea+submit+consulta+UI) · `REV` (review) · `APP` (approve) · `NOBU` (sin concesión) · `NOPERM` (sin `reports:read`). Negativos: lote ajeno (empresa 3). Legacy: lotes 11/53 (escala) · 33/35 (cero).

# GA-GOV-03 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · HEAD de partida `c0b4afc` · GA-REM a asignar al autorizar (siguiente libre GA-REM-043).

**Regla de la tranche: solo pruebas, CI y documentación. Cero producto.** `backend/app/**` y `frontend/src/**` (fuera de `__tests__` si aplica) quedan intactos; los docker-push no se tocan.

## PLAN por tranches

| Tranche | Contenido | Entrada | Salida | Estado |
|---|---|---|---|---|
| **C1 · Gobernanza + RED documentada** | Finding/spec/clarificaciones/AC/diseño (hecho); capturar la corrida RED actual (25+12) como referencia; escribir las actualizaciones de los 37 casos en rama de trabajo (sin ejecutar aún) | este paquete | commit C1 «GA-GOV-03 C1: gobernanza + RED (sin producto)» | ☐ |
| **C2 · Higiene de pruebas** | Actualizar 25 casos backend (grupos A/B/C) + 12 Playwright; ejecutar `run_tests.sh` completo (PG) y `scripts_e2e.sh` completos hasta 0 failed; guard `git diff --stat` sin producto | C1 | commit C2 «GA-GOV-03 C2: suite verde en HEAD (solo pruebas)» + `evidence/green/` | ☐ |
| **C3 · CI en push + regla de evidencia** | Añadir job de suite en `push` (PG efímero; sin gate del docker-push); verificar con un run real (commit de cierre); publicar plantilla de certificación «no GREEN por declaración»; reconciliar backlog/INDEX (`R-189`, `GA-UAT-09`, `OD-21…25`, `GA-REM-016`) | C2 | commit C3 + run CI verde (enlace + artefacto) + docs | ☐ |
| **C4 · Cierre** | Certificación del paquete (commit + comandos + logs + run); anotar vigencia en los 13 informes históricos; actualizar registro/cola | C3 | `GA-GOV-03_CERTIFICATION.md` + backlog | ☐ |

## CHECKLIST

- ☐ C1.1 RED capturada y versionada (`evidence/backend_full_suite.log`, `evidence/playwright_e2e.log` ya presentes)
- ☐ C1.2 Lista caso-a-caso cerrada (§7.1 de la spec) y revisada contra `test_od16_global_read_boundary.py` (contrato 404)
- ☐ C1.3 Commit C1 sin tocar pruebas aún (solo artefactos de gobernanza)
- ☐ C2.1 Grupo A (17 casos OD-16) actualizados a fail-closed 404; verde en PG local
- ☐ C2.2 Grupo B (5 casos R-188) con fixture `@example.com`; verde
- ☐ C2.3 Grupo C (3 guardas) actualizadas (cabeza Alembic `y5z6a7b8c9d0`; sin fechas literales)
- ☐ C2.4 Playwright: 12 casos actualizados (BR-20 ×3, BR-21 ×6, BR-03 ×1, R-118 ×1, locator ×1); verde completo
- ☐ C2.5 `git diff --stat c0b4afc..C2` sin `backend/app/**` ni `frontend/src/**`
- ☐ C3.1 Workflow de suite en `push` (PG efímero; artefacto junit/log); sin `needs:` desde docker-push
- ☐ C3.2 Run real del workflow verde (enlace al run + artefacto) sobre el commit de cierre
- ☐ C3.3 Plantilla «no GREEN por declaración» publicada (`audit/remediation/CERTIFICATION_EVIDENCE_TEMPLATE.md`)
- ☐ C3.4 Backlog: `R-189` y `GA-UAT-09` con entrada; `INDEX.md` con `OD-21…25`; `GA-REM-016` actualizado
- ☐ C4.1 Cabeceras de vigencia `NOT_REPRODUCIBLE_EN_HEAD (pre-GA-GOV-03)` en los 13 informes históricos
- ☐ C4.2 `GA-GOV-03_CERTIFICATION.md` (commit+comandos+logs+run) — aplica la regla a sí misma
- ☐ C4.3 Registro/cola actualizados: GA-GOV-03 → `CLOSED_TECH`

## TAREAS

| ID | Tarea | Ficheros | Tamaño | Depende | Tranche |
|---|---|---|---|---|---|
| T-01 | Actualizar 17 aserciones OD-16 | `backend/tests/{test_lots_bu_enforcement,test_operations_bu_enforcement,test_review_bu_enforcement,test_state_continuity,test_internal_reversal,test_od14_productive_surfaces,test_review_decision_concurrency}.py` | M | — | C2 |
| T-02 | Fixture R-188 dominio válido | `backend/tests/test_r188_bu_lifecycle.py` | S | — | C2 |
| T-03 | Guardas Alembic/tiempo | `test_company_catalog.py:267`, `test_population_invariant.py:398`, `test_time_determinism.py` (+docstrings citados) | S | — | C2 |
| T-04 | Playwright BR-20/BR-21/BR-03/R-118/locator | `e2e/proceso-p0{3,4,5,10,11,15}-*.spec.ts` | M | — | C2 |
| T-05 | Workflow suite `push` | `.github/workflows/` (nuevo o ampliación) | S | T-01…T-04 | C3 |
| T-06 | Plantilla de certificación | `audit/remediation/CERTIFICATION_EVIDENCE_TEMPLATE.md` (nuevo) | S | — | C3 |
| T-07 | Reconciliación backlog/INDEX | `audit/remediation/REMEDIATION_BACKLOG.md`, `specs/remediation/INDEX.md`, `specs/remediation/OD-21…25-*.md` (índice) | S | — | C3 |
| T-08 | Cabeceras de vigencia históricas | 13 `PROCESS-*-CERTIFICATION.md` | S | T-05 | C4 |
| T-09 | Certificación del paquete | `specs/GA-GOV-03/GA-GOV-03_CERTIFICATION.md` | S | T-05 | C4 |

## SENSIBILIDAD (tras el commit C2)

| Mutación | Qué quita | Debe fallar |
|---|---|---|
| S1 | Revertir una aserción OD-16 a `403` | El caso A correspondiente vuelve a rojo |
| S2 | Revertir el fixture R-188 a `@e.test` | Grupo B rojo (documenta la dependencia) |
| S3 | Retirar el job de suite del trigger `push` | Verificación AC-GOV03-06 no reproducible (run ausente) |

## Regresión obligatoria

Ninguna suite de producto cambia; la propia suite completa (backend+Playwright) **es** la regresión. No se alteran docker-push ni `quality-gates.yml`. Verificación final: `git diff --name-only c0b4afc..HEAD` sin ficheros de producto.

# GA-GOV-03 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · «RED en HEAD» = estado actual antes de la tranche. Artefactos bajo `audit/ga-claude-final-audit/specs/GA-GOV-03/evidence/`.

| AC | Criterio (resumen) | Verificación | RED en HEAD | Artefacto esperado |
|---|---|---|---|---|
| AC-GOV03-01 | Backend 0 failed (≥1201 passed) tras actualizar 25 casos | `backend/scripts/run_tests.sh` (PG aislado) | rojo (25 failed, `backend_full_suite.log:624`) | `evidence/green/backend_full.log` |
| AC-GOV03-02 | Playwright 0 failed (129 passed) tras actualizar 12 casos | `bash scripts_e2e.sh` | rojo (12 failed, `playwright_e2e.log:561-575`) | `evidence/green/playwright.log` |
| AC-GOV03-03 | 25 casos verdes **sin** diff en `backend/app/**` | `git diff --stat c0b4afc..C2 -- backend/app` = vacío | n/a | salida `git diff --stat` |
| AC-GOV03-04 | 12 casos verdes **sin** diff en `frontend/src/**` | `git diff --stat c0b4afc..C2 -- frontend/src` = vacío | n/a | salida `git diff --stat` |
| AC-GOV03-05 | Job de suite en `push` con PG efímero; sin gate de docker-push | revisión de `.github/workflows/` (sin `needs:` desde docker-push) | inexistente | diff del workflow |
| AC-GOV03-06 | Run real del workflow verde sobre el commit de cierre | enlace al run + descarga de artefacto | inexistente | `evidence/ci-run.json` (enlace + metadatos) |
| AC-GOV03-07 | Plantilla «no GREEN por declaración» publicada y aplicada a este cierre | revisión documental | ausente | `audit/remediation/CERTIFICATION_EVIDENCE_TEMPLATE.md` + certificación |
| AC-GOV03-08 | Backlog/INDEX reconciliados (`R-189`, `GA-UAT-09`, `OD-21…25`, `GA-REM-016`) | grep `R-189`/`GA-UAT-09` > 0; `INDEX.md` con OD-21…25 | rojo (grep = 0) | diff del backlog/INDEX |
| AC-GOV03-09 | Guardas temporales/Alembic verdes | `test_time_determinism`, `test_company_catalog`, `test_population_invariant` | rojo (3 casos) | log dirigido |
| AC-GOV03-10 | Sin reglas de producto relajadas | `git diff` sin `backend/app/**`/`frontend/src/**` | n/a | salida `git diff --stat` |
| AC-GOV03-11 | Caso `p11` aislamiento empresa con empresa del contexto | ejecución del spec dirigido | rojo | log dirigido |
| AC-GOV03-12 | Certificación de cierre cita commit+comandos+logs+run | revisión del documento de certificación | n/a | `GA-GOV-03_CERTIFICATION.md` |

Cobertura: 12 AC · 8 con RED documentada (01, 02, 08, 09, 11 + 03/04/10 como guardas de no-diff) · 1 verificación operativa de CI (06) · 1 aplicable a sí misma (12).

## Trazabilidad caso → AC (grupos)

| Grupo | Casos | AC |
|---|---|---|
| A · OD-16 fail-closed | 17 | AC-GOV03-01, 03 |
| B · fixture R-188 | 5 | AC-GOV03-01, 03 (robustez `/me` → R-213) |
| C · guardas | 3 | AC-GOV03-01, 03, 09 |
| Playwright BR-20/21/03/R-118/locator | 12 | AC-GOV03-02, 04, 11 |
| CI | — | AC-GOV03-05, 06 |
| Documental | — | AC-GOV03-07, 08, 12 |

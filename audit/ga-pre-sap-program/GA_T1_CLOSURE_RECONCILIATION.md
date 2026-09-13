# GA · T1 — RECONCILIACIÓN DE CIERRE (GA-GOV-03)

Formato §41 del encargo. Commit de implementación `66be1c1` · baseline `e828c3a`.

- **37 canonical cases: 37 / 37 reconciled** (25 backend + 12 Playwright; 0 sin disposición; matriz individual en `GA_GOV_03_EXECUTION_MATRIX.md`).
- **TEST_DEFECT confirmed: 37** (los 25 backend clasificados A/B/C y los 12 Playwright; RED pre-fix capturado y congelado).
- **Reclassified product defects: 0.** Nota: R-213 (`/me` 500 con dominios reservados) es defecto de producto **colateral del grupo B ya fuera de alcance por decisión C-05 del paquete**, con paquete propio (T11); el fixture se corrigió a dominio válido sin tocar producto.
- **Stale migration tests fixed: 2** (`test_company_catalog::test_t10`, `test_population_invariant::test_ac14`) — cabeza `x4y5z6a7b8c9` → `y5z6a7b8c9d0`, preservando la invariante de **cabeza única** (ahora `len(heads)==1` + cabeza canónica).
- **Stale security expectations fixed: 17** (grupo A completo: 403/visibilidad → **404/fila invisible** fail-closed OD-16; aserciones de no-mutación conservadas; 2 renames documentados).
- **Fixture defects fixed: 6 grupos de fixture** → backend: 1 fixture (R-188, dominio válido); Playwright: BR-20 ×3 (p03/p04/p11), BR-21+BR-04 (p05/p10/p15), BR-03 (p15), R-118 (p11: rol+usuario en B **y** concesión `AC-B01` por API); + locator desambiguado (p03-curvas).
- **Date/time defects fixed: 1 test** (`t028_04`; 4 literales retirados de 3 docstrings; guarda intacta; sin sustituir por fechas nuevas).
- **Other categories:** `STALE_FIXTURE` ×11 Playwright, `LOCATOR_AMBIGUITY` ×1 Playwright, `STALE_MIGRATION_HEAD` ×2, `STALE_DATE_LITERAL` ×1, `STALE_SECURITY_EXPECTATION` ×17.
- **Targeted suite: PASS** — 25/25 backend (`backend_targeted_25_green.log`) y 12/12 Playwright (`playwright_targeted_7specs_green.log` + `playwright_p11_green_retry.log`).
- **Backend full: 1226 passed · 0 failed · 0 errors · 49 skipped** (20:18; JUnit `tests=1275 failures=0 errors=0`).
- **Frontend full: 314/314** vitest · TS 0 · build OK (`index-DDCcWL76.js`) · i18n 1041=1041.
- **Alembic: 1 head `y5z6a7b8c9d0`** · 37 revisiones · 1 base.
- **CI: configurado** (`Quality Suite (push)`; PG efímero; artefactos). Push `66be1c1` ejecutado; **observación del run = `BLOCKED_EXTERNAL_CI_OBSERVATION`** (entorno sin credenciales GitHub; API anónima 404; equivalente local verde).
- **Artifact: disponible localmente** (`backend-junit-post-t1.xml`, `vitest-junit-post-t1.xml`, logs en `evidence/`); artefactos CI configurados (`backend-suite-<sha>` / `frontend-suite-<sha>`).
- **Product changes: 0 / PASS** · **Migration changes: 0 / PASS** · **Deployment changes: 0 / PASS** (`git diff e828c3a..66be1c1`: solo tests, e2e, workflow y audit/**).
- **Unresolved blocker: NONE** (única salvedad: verificación externa del run de CI desde GitHub, sin credenciales en este entorno).
- **GA-GOV-03: `CLOSED_FUNCTIONALLY_CERTIFIED`** (AC-06 externamente bloqueada y así certificada).
- **T1: CLOSED** (con la salvedad externa documentada; `QUALITY_GATES_READY = YES`).

# GA-GOV-03 · RESULTADOS POST-FIX DE LA SUITE (T1 · cierre)

Commit de implementación: **`66be1c1`** (tests + e2e + workflow; producto diff 0). Baseline congelada de entrada: `e828c3a`.

## 1 · Resumen

| Suite | Antes (PRE-T1) | Después (POST-T1) | Artefacto |
|---|---|---|---|
| Backend completa | 1201 passed · **25 failed** · 49 skipped | **1226 passed · 0 failed · 0 errors · 49 skipped** (20:18) | `evidence/backend_full_suite_post_t1.log` · JUnit `evidence/backend-junit-post-t1.xml` |
| Playwright (procesos + heredadas) | 117 passed · **12 failed** | **129 passed · 0 failed** (3.0 m) | `evidence/playwright_full_suite_post_t1.log` |
| Vitest | 314/314 | **314/314** (44 ficheros) | `evidence/frontend_checks_post_t1.log` · JUnit `evidence/vitest-junit-post-t1.xml` |
| TypeScript | 0 | **0** | id. |
| Build | OK | **OK** (`index-DDCcWL76.js` — idéntico al bundle desplegado) | id. |
| i18n ES/EN | paridad | **ES=1041 · EN=1041 · 0 faltantes** | id. |
| Alembic | 1 head `y5z6a7b8c9d0` | **1 head `y5z6a7b8c9d0` · 37 revisiones · 1 base** | comando directo |

## 2 · Dirigidos (los 37)

| Grupo | Casos | RED (pre) | GREEN (post) | Log |
|---|---|---|---|---|
| A · OD-16 fail-closed | 17 | 17/17 FAILED reproducidos | **17/17 PASSED** (44.49 s) | `evidence/backend_group_a_green.log` |
| B · fixture R-188 | 5 | 5/5 FAILED (`/me` 500) | **10/10 PASSED** (fichero completo) | `evidence/backend_group_b_green.log` |
| C · guardas | 3 | 3/3 FAILED | **3/3 PASSED** (2.77 s) | `evidence/backend_group_c_green.log` |
| 25 backend juntos | 25 | 25/25 FAILED (44 s) | **25/25 PASSED** (37 s) | `evidence/backend_targeted_25_green.log` |
| Playwright | 12 | 11/12 reproducidos (locator latente) | **12/12 PASSED** (49+6 en dos pasadas) | `evidence/playwright_targeted_7specs_green.log` · `evidence/playwright_p11_green_retry.log` |

## 3 · Clasificación de residuos

- **Fallos inexplicados: 0.** Errores: 0. Fallos fuera de los 37: **0** (`OUTSIDE_GA_GOV_03: []`).
- 16 warnings (deprecations/asyncio-mark) preexistentes, sin impacto; sin cambios.
- RED Playwright del locator: no reproducido en la BD de la sesión (id del evento ≠ 135) — corregido por construcción y verificado en GREEN (sigue latente-bajo-condición, ahora determinista).

## 4 · Comandos canónicos (reproducibles)

```
# Backend completa (PG efímero de usuario vía pgserver)
bash backend/scripts/run_tests.sh -q --junitxml=reports/backend-junit.xml

# Playwright completa (levanta backend 8099 + frontend 5199 sobre BD aislada)
bash scripts_e2e.sh

# Frontend
(cd frontend && npx vitest run --reporter=default --reporter=junit --outputFile=vitest-junit.xml)
(cd frontend && npx tsc -b --noEmit && npm run build)
# i18n: script de paridad de quality-gates.yml (ES=1041/EN=1041)
```

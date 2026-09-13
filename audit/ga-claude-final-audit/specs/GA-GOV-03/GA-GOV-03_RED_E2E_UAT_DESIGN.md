# GA-GOV-03 · DISEÑO DE PRUEBAS RED · EJECUCIÓN E2E DE LA TRANCHÉ · UAT

HEAD `c0b4afc` · Sin implementación en este documento. Esta spec no introduce producto: su «RED→GREEN» es el **estado de la suite** y la **existencia de evidencia ejecutable**.

## 1 · Diseño RED (estado actual documentado)

### 1.1 RED backend (25)

Ejecución de referencia (ya capturada): `backend/scripts/run_tests.sh` ⇒ `1201 passed · 25 failed · 49 skipped` (`evidence/backend_full_suite.log`). Aislamiento determinista de los 25: `evidence/backend_targeted_failing.log` («25 failed, 189 passed»). Los casos y su cambio requerido están en `GA-GOV-03_SPEC.md §7.1` (grupos A 17 / B 5 / C 3).

Criterio RED por caso (ejemplo representativo):

| Caso | Aserción actual (roja vs producto vigente) | Aserción objetivo | Por qué es TEST_DEFECT |
|---|---|---|---|
| `test_lots_bu_enforcement::test_l08_put_sobre_unidad_apagada_es_403_para_la_autoridad_global` | `404 == 403` | `404` + `detail` «Lote no encontrado» | OD-16 (`9ffc5ec`) cambió a fail-closed; el test quedó en el contrato anterior |
| `test_r188_bu_lifecycle::*` (×5) | `GET /me` `500 == 200` | `/me` 200 con fixture `@example.com` (o skip explicado hasta R-213) | Fixture con dominio reservado; depende de R-213 (robustez), no de BU-D10 |
| `test_company_catalog::test_t10` | `['y5z6a7b8c9d0'] == ['x4y5z6a7b8c9']` | cabeza vigente `y5z6a7b8c9d0` | Guarda fijada antes de `b4d8c3a` |

### 1.2 RED Playwright (12)

`bash scripts_e2e.sh` ⇒ `117 passed · 12 failed` (`evidence/playwright_e2e.log`). Cambio requerido por caso en `GA-GOV-03_SPEC.md §7.1` (bloque «Playwright (12)»).

### 1.3 RED documental (3)

| Guarda | Verificación en HEAD (rojo) | Objetivo |
|---|---|---|
| `grep -c "R-189" REMEDIATION_BACKLOG.md` = 0 | backlog sin el hallazgo que bloqueó la UAT del propietario | ≥1 entrada con `CLOSED_TECH_UAT_PENDING` y referencias |
| `grep -n "OD-2[1-5]" specs/remediation/INDEX.md` = 0 | decisiones sin hogar en `specs/remediation/` | filas con enlace a su hogar canónico (`audit/ga-*`) |
| Ausencia de plantilla de certificación | certificaciones por declaración | `CERTIFICATION_EVIDENCE_TEMPLATE.md` publicado |

### 1.4 Ejecución de la RED

```bash
# Backend (PG efímero o GA_TEST_ENV=1 + GA_TEST_DATABASE_URL)
bash backend/scripts/run_tests.sh                      # esperado HEAD: 25 failed
# Playwright de procesos
bash scripts_e2e.sh                                    # esperado HEAD: 12 failed
```

Salidas a `evidence/red/` (ya versionadas como logs de esta auditoría).

## 2 · Ejecución E2E de la tranche (GREEN)

No hay E2E de producto; la «E2E» de esta spec es triple:

| Paso | Comando/Verificación | Criterio |
|---|---|---|
| E2E-GOV03-01 | `bash backend/scripts/run_tests.sh` (completa) | 0 failed; log a `evidence/green/backend_full.log` |
| E2E-GOV03-02 | `bash scripts_e2e.sh` (completa) | 0 failed; log a `evidence/green/playwright.log` |
| E2E-GOV03-03 | Run de CI del commit de cierre (workflow de suite en `push`, PG efímero) | run verde; artefacto descargado; enlace guardado en `evidence/ci-run.json` |
| E2E-GOV03-04 | Verificación de la invariante de deploy | `git log -1 --format=%H` del docker-push del mismo commit: imagen publicada sin depender del job de suite |
| E2E-GOV03-05 | Guardas de no-diff | `git diff --stat c0b4afc..C2 -- backend/app frontend/src` vacío (salvo `__tests__` si algún test vive ahí) |

Duración esperada: backend ≈20 min; Playwright ≈15-25 min (2 workers); CI total < 60 min (decisión C-02).

## 3 · Plan UAT (no requerido; guion de verificación del propietario si lo pide)

| Paso | El propietario ve | Resultado esperado |
|---|---|---|
| V-01 | Apertura del run de CI verde del commit de cierre (enlace + artefacto) | «Suite completa en verde, ejecutada por el propio repositorio en `push`» |
| V-02 | Los dos logs de corrida local (backend + Playwright) | 0 failed en ambos; mismos casos que estaban rojos |
| V-03 | Confirmación de despliegue | El docker-push del mismo commit corrió y publicó imagen (los tests no lo bloquearon) |
| V-04 | Diff de producto | Cero cambios en `backend/app` y `frontend/src` |

Criterio: verificación informativa; **no bloquea** ninguna decisión. Si el propietario quisiera endurecer la política (C-03), se abre decisión separada.

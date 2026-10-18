# 12 · Sensibilidad, trazabilidad y cierre — SPEC 007

## Commits (rama `main`, sin rama nueva)

| Etapa | SHA | Contenido |
|---|---|---|
| Baseline | `3e146ac` | SPEC-006 RUNTIME |
| IMPLEMENTATION (SPEC+IMPL) | `9a5d11a6ce8636e4ac05f0b458de6aa7a87f3274` | SPEC 007, seed canónico, tests, evidencia 01–11, manifest, matriz, fixtures, guía QA MD+DOCX, plantilla, manuales |
| CERTIFICATION | `b7942c7ca27d4908967cf30005ee6ea9d988a2af` | sensibilidad, regresión post-mutación, este documento |
| REMOTE | `b7942c7ca27d4908967cf30005ee6ea9d988a2af` | `git push git@github.com:dvconsultores/GlobalAvicola.git main:main` (3e146ac..b7942c7) · `REMOTE_SHA_MATCH=PASS` |
| CLOSE | *(este commit; registra los SHAs anteriores)* | actualización de 12 y tasks |

## Sensibilidad / mutación (tras el commit de implementación; log `evidence/12_sensitivity.log`)

Cada mutación se aplica sobre el seed, se ejecuta `tests/test_qa_integral_dataset.py` en el arnés aislado y se restaura con `git restore --source=9a5d11a -- <archivo>` (diff=0 tras cada restauración).

| Mut. | Mutación | Test que la detecta | Resultado |
|---|---|---|---|
| S1 | guarda de entorno eliminada (`if entorno in FORBIDDEN_ENVIRONMENTS` ⇒ `if False`) | `test_entorno_prohibido_aborta_antes_de_conectar[×5]` | **DETECTED** (5 failed) |
| S2 | `--confirm-target` ya no obligatorio | `test_escritura_sin_confirm_target_aborta` | **DETECTED** |
| S3 | `sap_responses` fuera del plan de limpieza | `test_cleanup_cubre_toda_tabla_que_referencia_a_las_que_borra` | **DETECTED** |
| S4 | fail-closed desactivado (ambiguos ignorados) | `test_cleanup_fail_closed_ante_datos_no_marcados` | **DETECTED** |
| S5 | `es_codigo_qa` acepta cualquier código | `test_es_codigo_qa` | **DETECTED** |
| S6 | contraseña literal introducida en `qa_integral_builders.py` | `test_sin_contrasenas_literales_en_el_seed` | **DETECTED** |

**6/6 DETECTED · FINAL_DIFF=0 · post-mutación targeted 16 passed.** Regresión completa post-mutación (`evidence/10_backend_regression_post_mutation.log`): **1722 passed · 0 failed · 49 skipped** (22 min 14 s), idéntica a la pre-mutación.

## Cumplimiento del mandato (§84)

```
SPEC_007                 = CREATED (specs/007-qa-integral-demo-dataset, 9 documentos)
SEED_CANONICO            = backend/seeds/qa_integral_dataset.py (+ qa_integral_builders.py) · --inventory/--apply/--verify/--cleanup/--dry-run
QA_DATA_LOCAL_ISOLATED   = CERTIFIED (apply 719 en 14 s · verify 22/22 PASS · re-apply CREATED=0 · cleanup 2438 baseline intacto · recreate 719 PASS)
QA_DATA_RUNTIME          = NOT_LOADED · BLOCKED_EXTERNAL (base del runtime no alcanzable desde la estación; runbook en 09)
QA_DATA_READY            = NO (hasta ejecutar el runbook de 09 en el host del backend; después YES)
CLEANUP                  = IMPLEMENTED · TESTED · DOCUMENTED · READY_NOT_EXECUTED
REAL_SAP_CALLS           = 0 · OUTBOUND = NOT_ENABLED · SAP_REAL_TEST = PENDING_2026_10_20
CREDENTIALS              = NOT_VERSIONED (GA_QA_SEED_PASSWORD o archivo 0600; entrega por canal separado)
TESTS                    = 16 nuevos · regresión backend 1722/0/49 · frontend 542/542 · tsc+build PASS · sensibilidad 6/6
QA_MANUAL                = docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.md + .docx · docs/QA_EXECUTION_RESULTS_TEMPLATE.docx
COVERAGE                 = 26/26 entradas de navigationConfig.ts · 4/4 BU · 12/12 usuarios · 11/11 estados · 28/28 tipos de evento
BRANCH                   = main (sin rama nueva)
```

## Cierre (2026-10-18)

```
IMPL_SHA          = 9a5d11a6ce8636e4ac05f0b458de6aa7a87f3274
CERT_SHA          = b7942c7ca27d4908967cf30005ee6ea9d988a2af
LOCAL_SHA         = b7942c7ca27d4908967cf30005ee6ea9d988a2af
REMOTE_SHA        = b7942c7ca27d4908967cf30005ee6ea9d988a2af   (origin/main, SSH)
REMOTE_SHA_MATCH  = PASS
TREE              = limpio (solo un archivo local de credenciales del arnés, no versionable y no versionado)
POST_MUTATION     = 1722/0/49 (idéntica a pre-mutación)
```

Nota: el remoto `origin` está configurado por HTTPS sin credenciales en esta estación; el push se hace, como en SPEC 005/006, por la URL SSH explícita (AOD-29).

Pendiente externo: ejecutar el runbook de `09_RUNTIME_VERIFICATION.md` en el host del backend (base del runtime no alcanzable desde la estación). Al hacerlo, `QA_DATA_READY` pasa a `YES`.

## R1 (2026-10-18) — pendiente de cierre

Revisión independiente + remediación R1: ver `13_INDEPENDENT_REVIEW_AND_REMEDIATION.md` y `specs/…/remediation-r1.md`. Commits de R1, sensibilidad S7–S9 y regresión post-mutación: se registran al cerrar la ronda.

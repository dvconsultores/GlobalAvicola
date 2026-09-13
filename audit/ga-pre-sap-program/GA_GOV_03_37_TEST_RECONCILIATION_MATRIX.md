# GA · GA-GOV-03 — RECONCILIACIÓN DE LOS 37 TEST_DEFECT (TRANCHE 0 · §16)

Fuente: `specs/GA-GOV-03/GA-GOV-03_FINDING.md` §2.1-2.2 + `evidence/backend_full_suite.log` / `evidence/playwright_e2e.log` (materializados). Regla de la tranche: **cambio de producto = 0; cambio de test = 37/37** (son pruebas obsoletas, no defectos de aplicación; `R-213` es colateral y tiene paquete propio). Spec dueña: **GA-GOV-03** (T1). Decisión habilitante: `OD-16` (contrato 403/404 — el producto fail-closed es el canónico) y `OD-23` (suite certificada roja).

## 1 · Backend — 25 fallos (T1 · `backend/tests/**`)

| # | Fichero | Test | Fallo actual | Contrato esperado | Código actual (producto) | Decisión canónica | Clase | ¿Cambio producto? | ¿Cambio test? | Spec dueña | Tranche |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1-4 | `test_lots_bu_enforcement.py` | `l08` ×4 (casos l08_01…04) | Esperan 403 / visibilidad con autoridad global sobre unidad apagada | Lectura productiva **fail-closed**: 404 «no encontrado» / fila invisible | `business_units/service.py:126-146` (`unidades_de_alcance_productivo`) + `9ffc5ec` | OD-16 «apagar prevalece» | TEST_DEFECT (A) | **NO** | **SÍ** | GA-GOV-03 | T1 |
| 5 | `test_lots_bu_enforcement.py` | `l11` | Ídem | Ídem | Ídem | OD-16 | TEST_DEFECT (A) | NO | SÍ | GA-GOV-03 | T1 |
| 6 | `test_lots_bu_enforcement.py` | `e06` | Ídem | Ídem | Ídem | OD-16 | TEST_DEFECT (A) | NO | SÍ | GA-GOV-03 | T1 |
| 7-10 | `test_operations_bu_enforcement.py` | `w13` ×4 | Ídem | Ídem | Ídem | OD-16 | TEST_DEFECT (A) | NO | SÍ | GA-GOV-03 | T1 |
| 11 | `test_operations_bu_enforcement.py` | `a08` | Ídem | Ídem | Ídem | OD-16 | TEST_DEFECT (A) | NO | SÍ | GA-GOV-03 | T1 |
| 12 | `test_operations_bu_enforcement.py` | `a13` | Ídem | Ídem | Ídem | OD-16 | TEST_DEFECT (A) | NO | SÍ | GA-GOV-03 | T1 |
| 13 | `test_review_bu_enforcement.py` | `test_165_01` | Ídem | Ídem | Ídem (review ×3 remociones) | OD-16 | TEST_DEFECT (A) | NO | SÍ | GA-GOV-03 | T1 |
| 14 | `test_state_continuity.py` | `test_s07` | Ídem | Ídem | Ídem | OD-16 | TEST_DEFECT (A) | NO | SÍ | GA-GOV-03 | T1 |
| 15 | `test_internal_reversal.py` | `test_s03_s04` | Ídem | Ídem | Ídem | OD-16 | TEST_DEFECT (A) | NO | SÍ | GA-GOV-03 | T1 |
| 16 | `test_od14_productive_surfaces.py` | `test_s02` | Ídem | Ídem | Ídem | OD-16 | TEST_DEFECT (A) | NO | SÍ | GA-GOV-03 | T1 |
| 17 | `test_review_decision_concurrency.py` | `test_r166_12` | Ídem | Ídem | Ídem | OD-16 | TEST_DEFECT (A) | NO | SÍ | GA-GOV-03 | T1 |
| 18-22 | `test_r188_bu_lifecycle.py` | ×5 | Fixture con correo `…@e.test` → `GET /me` **500** | `/me` debe responder 200; la lectura estricta de `EmailStr` en `UserRead` es el defecto (**R-213**) | `auth/schemas.py:30` + `auth/service.py:329` (500) | R-213 (fix producto en T11); fixture debe usar dominios válidos **o** esperar la corrección de R-213 según decisión | TEST_DEFECT (B) — colateral R-213 | **NO en T1** (el fix de /me es T11/R-213) | **SÍ en T1** (fixture a dominio válido para desbloquear verde) | GA-GOV-03 (+R-213 rastro) | T1 (test) · T11 (producto /me) |
| 23 | `test_company_catalog.py` | `test_t10` | Guarda fijada a `x4y5z6a7b8c9` | Cabeza real `y5z6a7b8c9d0` | Cadena avanzó en `b4d8c3a` | Alembic único head | TEST_DEFECT (C) | NO | SÍ | GA-GOV-03 | T1 |
| 24 | `test_population_invariant.py` | `test_ac14` | Ídem | Ídem | Ídem | Alembic único head | TEST_DEFECT (C) | NO | SÍ | GA-GOV-03 | T1 |
| 25 | `test_time_determinism.py` | `test_t028_04` | Fechas ISO literales en comentarios/docstrings (`test_r188_bu_lifecycle.py:3`, `test_r184_ipe_date_semantics.py:4,50`, `test_r187_ipe_od22_scale.py:3`) | Sin fechas literales (o guarda actualizada a la política T-028 vigente) | Guarda `T-028-04` (`:95-115`) | Política T-028 | TEST_DEFECT (C) | NO | SÍ | GA-GOV-03 | T1 |

## 2 · Playwright — 12 fallos (T1 · `e2e/**`)

| # | Spec:línea | Prueba | Fallo actual | Causa real | Contrato/regla vigente | ¿Cambio producto? | ¿Cambio test? | Spec dueña | Tranche |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `e2e/proceso-p03-curvas-ui.spec.ts:374` | P-03 curvas · cadena completa | `strict mode violation: getByText(/135/) resolved to 2 elements` («Evento #135» vs «135–165 g») | Locator ambiguo por construcción (id coincide con `MINIMO_A_LOS_15`) | Locator debe discriminar | NO | SÍ (locator) | GA-GOV-03 | T1 |
| 2 | `e2e/proceso-p03-reproductoras-cria.spec.ts:107` | P-03 cría · cadena completa | 400 **BR-20** falta `received_total`/`dead_on_arrival`/`rejected_on_arrival` | Fixture previa a `a759a17` | BR-20 vigente (`validators.py:536-565`) | NO | SÍ (fixture) | GA-GOV-03 | T1 |
| 3 | `e2e/proceso-p04-reproductoras-huevo-fertil.spec.ts:71` | P-04 huevo fértil | Ídem BR-20 | Ídem | Ídem | NO | SÍ | GA-GOV-03 | T1 |
| 4 | `e2e/proceso-p05-incubacion.spec.ts:60` | P-05 incubación | 400 **BR-21** (`chicks_healthy`/`chicks_weak`) y cascada 400 **BR-04** (`viables 0`) | Fixture previa a `c653ff8` | BR-21 (`validators.py:577-613`) | NO | SÍ | GA-GOV-03 | T1 |
| 5-9 | `e2e/proceso-p10-trazabilidad-generacional.spec.ts:73,145,167,186,203` | P-10 (5 casos, helper `tresGeneraciones`) | 400 **BR-21** en el nacimiento del helper | Ídem | Ídem | NO | SÍ | GA-GOV-03 | T1 |
| 10 | `e2e/proceso-p11-activacion-manual-de-lotes.spec.ts:160` | P-11 negativo | 400 **BR-20** (`crearLoteHistorico` crea `breeder`) | Ídem | Ídem | NO | SÍ | GA-GOV-03 | T1 |
| 11 | `e2e/proceso-p11-activacion-manual-de-lotes.spec.ts:210` | P-11 aislamiento | «el sujeto debe estar en la empresa B» (Expected 2 · Received 1) | `POST /users` toma empresa del contexto del actor (`auth/service.py:349-357`, R-118/OD-14.c); fixture usa cabecera del admin en A | R-118/OD-14.c vigente | NO | SÍ (fixture) | GA-GOV-03 | T1 |
| 12 | `e2e/proceso-p15-reportes-e-indicadores.spec.ts:28` | P-15 incubadora | 400 **BR-03** (carga 1000 > fértiles 800) | Fixture previa a `64dff76` (sólo fértil es disponibilidad) | `TIPO_DISPONIBLE="fertile"` | NO | SÍ | GA-GOV-03 | T1 |

## 3 · Reglas de ejecución T1

1. **No se suprime ninguna prueba**: se corrigen a la regla vigente y deben quedar **verdes**.
2. **Artefacto obligatorio**: cada corrida de cierre genera `evidence/backend_full_suite_<sha>.log` y `evidence/playwright_e2e_<sha>.log` (regla «no GREEN por declaración», GA-GOV-03 §6).
3. **CI**: `backend-ci.yml`/`frontend-ci.yml` deben cubrir `push` a `main` (o `workflow_dispatch`) manteniendo `docker-push` no bloqueado por tests de PR; decisión `OD-23` documentada.
4. **Grupo B**: en T1 el fixture pasa a dominio válido (desbloqueo de suite); el defecto de `/me` se corrige en T11 (R-213) con su propio test de lectura tolerante.
5. **Grupo C**: guardas actualizadas a `y5z6a7b8c9d0` vía import del head real (no literal), para que vuelvan a caducar de forma detectable.
6. Salida esperada de T1: **1226 passed · 0 failed · 49 skipped** (backend) y **129 passed · 0 failed** (Playwright) — cifras objetivo, a verificar con la corrida real (la suma exacta puede variar ±skips; la condición es 0 failed).

## 4 · Relación con otras specs

- `R-213` (T11): defecto de producto que destapa el grupo B — la matriz lo deja en su tranche para no mezclar producto y gobernanza en T1.
- `R-118` (fixture p11): la regla «el actor manda» es producto vigente decidido; sólo el fixture cambia.
- `R-172/RR-17` (p15 BR-03) y `R-204` (T3): el fixture de fértiles se corrige en T1; los agregados de incubadora sin predicado de unidad se corrigen en R-204 (T3).

# BACKEND TEST FAILURE MATRIX — RUN 05

**Fecha** 2026-09-03 · **Wave** 1.5 · **Track** C · **GA-REM-015**
**Resultado** `26 failed · 74 passed · 1 skipped in 22.78s` · reproducible con `bash backend/scripts/run_tests.sh`
**Línea base histórica** → `BACKEND_TEST_BASELINE_RUN_01.md` (congelado)

`GA-REM-015` es **CERTIFICACIÓN y DIAGNÓSTICO**, no `FIX ALL TESTS`. Ningún fallo se
corrige aquí. Todos quedan clasificados y trazados.

---

## 1. Taxonomía aplicada

| Clase | Significado |
|---|---|
| `IMPLEMENTATION_BUG` | El código de aplicación está mal. El test tiene razón. |
| `OBSOLETE_TEST` | El test codificaba un contrato que cambió legítimamente. |
| `TEST_DEFECT` | El test está mal escrito: nunca ejerció el contrato real. |
| `FIXTURE_DEFECT` | El test es correcto; los datos de siembra no lo sostienen. |
| `SPEC_MISMATCH` | Código y test difieren y la spec no arbitra. |
| `REQUIREMENT_CONFLICT` | El fallo depende de un `RC` sin resolver. |
| `TEST_ENVIRONMENT` | Infraestructura de pruebas, no producto. |
| `MIGRATION_DEFECT` | Esquema y modelo divergen. |
| `CONTRACT_DEFECT` | Contrato FE↔BE roto. |
| `UNKNOWN` | Sin diagnóstico concluyente. |

---

## 2. Matriz completa — 26 fallos

| # | Test | Resultado | Módulo | Clasificación | GA-REM | RC | Evidencia | Acción |
|---|---|---|---|---|---|---|---|---|
| 1 | `test_auth.py::test_login_success` | `assert 401 == 200` | auth | `OBSOLETE_TEST` | `004` | — | usa `admin/admin123`, credencial eliminada por `GA-REM-004` (Wave 1) | actualizar el test a las credenciales de siembra de prueba |
| 2 | `test_auth.py::test_get_me` | `assert 404 == 200` | auth | `TEST_DEFECT` | — | — | llama a `/api/v1/auth/me`; el router se monta con prefijo `/api/v1` y la ruta es `/me` (`main.py:103`, `auth/router.py:37`) | corregir la ruta en el test |
| 3 | `test_full_workflow_audit.py::test_f1_create_feed_registration` | `ForeignKeyViolationError` en `feed_movements_feed_type_id_fkey` | operaciones | `FIXTURE_DEFECT` | `015` | — | el test envía `feed_type_id: 1`; `test_seeds.py` no crea tipos de alimento | sembrar catálogo mínimo de `feed_types` |
| 4 | `test_f1_create_egg_collection` | `BR-08` sin manejar → **500** | operaciones | `TEST_DEFECT` + expone `R-26` | `015` · `002` | — | el *payload* omite `farm_id`/`house_id` (`test_full_workflow_audit.py:158`); el frontend sí los envía (`OperationFormPage.tsx:404`) | completar el *payload*; `R-26` aparte |
| 5 | `test_f1_create_farm_inspection` | `BR-08` sin manejar → **500** | operaciones | `TEST_DEFECT` + expone `R-26` | `015` | — | `house_id` va dentro de `inspection_details`, no en el nivel superior (`:190-195`) | ídem |
| 6 | `test_f1_create_vaccination` | `assert None == 1` (`vaccine_id`) | operaciones | **`IMPLEMENTATION_BUG`** | **`023`** | — | `service.py:69-81` no asigna `vaccine_id`; la columna existe (`models.py:107`) y el esquema la declara (`schemas.py:95`) | **`P0-14`** — no se corrige en esta Wave |
| 7 | `test_f1_create_egg_dispatch` | `BR-08` sin manejar → **500** | operaciones | `TEST_DEFECT` + expone `R-26` | `015` | — | omite `farm_id` (`:251-257`) | completar el *payload* |
| 8 | `test_f2_submit_to_review` | `BR-08` sin manejar → **500** | revisión | `TEST_DEFECT` + expone `R-26` | `015` | — | `bird_reception` sin `farm_id` (`:312-314`) | ídem |
| 9 | `test_f3_start_review_and_correct` | `BR-08` sin manejar → **500** | revisión | `TEST_DEFECT` + expone `R-26` | `015` | — | ídem | ídem |
| 10 | `test_f4_approve_event` | `403` «Un operador no puede aprobar sus propios registros» | aprobación | **`TEST_DEFECT`** | `007` | `RC-03` → `RR-03` | el test registra y aprueba con el **mismo** `admin_client`; `BR-14` actúa correctamente (`review/service.py:318`) | el test debe usar dos identidades distintas |
| 11 | `test_f4b_segregation_enforcement` | `BR-08` sin manejar → **500** | aprobación | `TEST_DEFECT` + expone `R-26` | `015` | — | falla antes de llegar a la aserción de segregación | completar el *payload* |
| 12 | `test_f5_reject_event` | `BR-08` sin manejar → **500** | revisión | `TEST_DEFECT` + expone `R-26` | `015` | — | ídem | ídem |
| 13 | `test_f8b_duplicate_sap_document_blocked` | `BR-10` sin manejar → **500** (esperaba 400) | SAP | **`IMPLEMENTATION_BUG`** | **`023`** | — | `validate_sap_document_unique` (`service.py:325`) se invoca **fuera** del `try/except` de `service.py:336-364` | **`R-26`** — la regla se aplica, pero devuelve 500 en vez de 400 |
| 14 | `test_f10_all_event_types_registered` | `Expected 24 event types, got 25` | operaciones | `OBSOLETE_TEST` | `018` | — | `egg_reception_classification` añadido en `939fd14` (2026-06-27), presente en enum, catálogo API, `processCatalog.ts:181` y `OperationFormPage.tsx:981` | actualizar el test a 25 |
| 15 | `test_multi_company::test_company_a_cannot_access_company_b_operations` | `assert 404 == 200` | multiempresa | `TEST_DEFECT` | — | — | llama a `/operations` sin el prefijo `/api/v1` (`test_multi_company.py:47`) | corregir la ruta |
| 16 | `test_multi_company::test_super_admin_sees_all_companies` | `assert 404 == 200` | multiempresa | `TEST_DEFECT` | — | — | ídem (`:83`) | ídem |
| 17 | `test_multi_company::test_idempotency_key_prevents_duplicate` | `assert 404 == 200` | multiempresa | `TEST_DEFECT` | — | — | ídem (`:113`) | ídem |
| 18 | `test_operations.py::test_list_event_types` | `assert 25 == 24` | operaciones | `OBSOLETE_TEST` | `018` | — | mismo origen que el #14 | actualizar a 25 |
| 19 | `test_operations.py::test_create_bird_reception` | `BR-08` sin manejar → **500** | operaciones | `TEST_DEFECT` + expone `R-26` | `015` | — | omite `farm_id` | completar el *payload* |
| 20 | `test_farm_inspection_numeric_values_per_house` | `BR-08` sin manejar → **500** | operaciones | `TEST_DEFECT` + expone `R-26` | `015` | — | ídem | ídem |
| 21 | `test_farm_inspection_without_house_id_still_accepted` | `BR-08` sin manejar → **500** | operaciones | **`SPEC_MISMATCH`** | `015` · `018` | — | el nombre del test afirma que la inspección **sin** `house_id` debe aceptarse; `validators.py:365-366` la rechaza explícitamente. Ninguna spec arbitra | escalar: ¿`BR-08` exige galpón en `farm_inspection`? |
| 22 | `test_farm_inspection_rejects_qualitative_only` | `BR-08` sin manejar → **500** | operaciones | `TEST_DEFECT` + expone `R-26` | `015` | — | falla por `farm_id`, no por lo que pretende probar | completar el *payload* |
| 23 | `test_vaccination_stores_vaccine_id` | `assert None == 1` | operaciones | **`IMPLEMENTATION_BUG`** | **`023`** | — | mismo origen que el #6 | **`P0-14`** |
| 24 | `test_medication_stores_medication_id` | `assert None == 1` | operaciones | **`IMPLEMENTATION_BUG`** | **`023`** | — | `medication_id` nunca asignado (`models.py:110` vs `service.py:69-81`) | **`P0-14`** |
| 25 | `test_review.py::test_seed_default_approval_steps` | `assert 500 == 201` | revisión | `FIXTURE_DEFECT` + `IMPLEMENTATION_BUG` | `015` · `023` | — | el servicio busca los roles «Supervisor Avícola», «Aprobador», «Analista SAP» (`review/service.py:471,481,489`); las semillas crean roles con prefijo `TEST ` (`test_seeds.py:91-115`). Además `_get_role_by_name` responde **500** ante una configuración ausente (`:505-508`) | alinear semillas **y** devolver 4xx accionable |
| 26 | `test_sap.py::test_sap_connection_check` | `assert False == True` | SAP | **`OBSOLETE_TEST`** | `010` | — | consecuencia **directa y deseada** de `GA-REM-010`: `ManualSapAdapter.check_connection()` devuelve `False` porque no hay entrega real a SAP | actualizar el test — **el código es correcto** |

---

## 3. Recuento por clasificación

```
TEST_DEFECT ................ 14   (54 %)
IMPLEMENTATION_BUG .........  4   (15 %)
OBSOLETE_TEST ..............  4   (15 %)
FIXTURE_DEFECT .............  2   ( 8 %)   [#25 comparte clase con IMPLEMENTATION_BUG]
SPEC_MISMATCH ..............  1   ( 4 %)
REQUIREMENT_CONFLICT .......  0
TEST_ENVIRONMENT ...........  0
MIGRATION_DEFECT ...........  0
CONTRACT_DEFECT ............  0
UNKNOWN ....................  0
```

**Cero `UNKNOWN`.** Los 26 fallos tienen diagnóstico con evidencia en ruta y línea.
**Cero `TEST_ENVIRONMENT`**: la infraestructura quedó saneada en RUN 05, y eso es
precisamente lo que permite que estos 26 fallos signifiquen algo.

**El dato relevante no es el número de fallos, sino su composición.** 20 de 26 son
problemas de los propios tests —escritos y jamás ejecutados durante junio de 2026—. Solo
4 son defectos reales del producto. Pero esos 4 son graves, y dos de ellos no los habría
encontrado ninguna lectura de código: aparecieron porque la suite por fin corre.

---

## 4. Defectos reales del producto revelados por RUN 05

### `P0-14` — 14 columnas de datos operativos se descartan en silencio

`OperationalEventService.create_event` construye `OperationalEvent` asignando **11
campos** (`backend/app/operations/service.py:69-81`). El modelo declara **40 columnas** y
el esquema de entrada `OperationalEventBase` (`schemas.py:83-106`) declara **14 campos
específicos de operación que el servicio nunca asigna**:

```
supplier_id           cause_id              cull_cause_id
vaccine_id            vaccination_route     vaccine_lot_number
medication_id         dosage_per_bird       treatment_days
destination_farm_id   destination_plant_id  transport_id
sample_size           extra_data
```

La API los acepta, responde `201` y `OperationalEventRead` los devuelve como `null`.
Alcance funcional:

| Campo perdido | Proceso afectado | Fuente que lo exige |
|---|---|---|
| `cause_id` | **causa de mortalidad** | cliente §16: «Mortalidad — Cantidad, **causa**» |
| `supplier_id` | recepción de aves | `docs/02 §3.5` |
| `vaccine_id`, `vaccination_route`, `vaccine_lot_number`, `dosage_per_bird` | vacunación | `docs/02 §3.5.7` · cliente §2 |
| `medication_id`, `treatment_days` | medicación | ídem |
| `destination_farm_id`, `destination_plant_id`, `transport_id` | salida de aves y despacho de huevos | `docs/02 §3.5.9` |
| `sample_size` | muestreo de peso | cliente §11 «Muestra tomada» |
| `extra_data` | campos extendidos por proceso | `OperationFormPage.tsx:1129` sí los envía |

Severidad **P0**: el módulo de mortalidad no puede registrar la causa, y la vacunación no
puede registrar qué vacuna se aplicó. Es el mismo patrón que `P0-13` (descarte silencioso
de un campo aceptado por la API), en 14 columnas a la vez.

### `R-26` — siete reglas de negocio devuelven 500 en lugar de 400

El bloque `try/except BusinessRuleViolation → HTTP 400` de `_apply_business_rules` abarca
solo las líneas `336-364` (`service.py`). Todos los validadores invocados **antes** quedan
fuera y su excepción sale sin manejar:

| Regla | Validador | Línea | HTTP real |
|---|---|---|---|
| `BR-07` | `validate_lot_active` | `service.py:317` | **500** |
| `BR-06` | `validate_event_date` | `:318` | **500** |
| `BR-08` | `validate_farm_house` | `:320` | **500** |
| `BR-19` | `validate_period_open` | `:322` | **500** |
| `BR-10` | `validate_sap_document_unique` | `:325` | **500** |
| `BR-17`/G-R04 | `validate_house_capacity` | `:332` | **500** |
| G-R05 | `validate_oc_limit` | `:334` | **500** |
| `BR-01` y 4 más |  dentro del `try` |  `:336-364` | 400 ✔ |

Verificado en ejecución contra la base aislada:

```
bird_reception sin farm_id      -> HTTP 500  Internal Server Error
mortality_recording sobre saldo -> HTTP 400  {"detail":"Mortalidad (999999) excede el saldo..."}
```

No existe manejador global para `BusinessRuleViolation`: `main.py` solo registra
`RateLimitExceeded` (`:54`). En producción el operador que olvida la granja ve «Internal
Server Error» en lugar del motivo, y las 7 reglas contaminan cualquier métrica de 5xx.
Severidad **P1** por experiencia y observabilidad; **P0** por diagnóstico, porque oculta
el cumplimiento real de reglas de negocio.

### `R-27` — `_get_role_by_name` responde 500 ante configuración ausente

`review/service.py:505-508` lanza `HTTP_500_INTERNAL_SERVER_ERROR` cuando falta un rol del
sistema. Un requisito de configuración no satisfecho no es un error del servidor: debe ser
un 4xx accionable que nombre el rol que falta.

### `P0-1` — confirmado en ejecución

`NameError: name 'get_current_bird_balance' is not defined` en
`app/operations/service.py:244`, dentro de `_check_and_create_alerts`. La función existe en
`validators.py:21` con **dos** parámetros; la llamada pasa **tres** y no la importa.

Es invisible para la suite actual: `test_f8c_business_rule_mortality_exceeds_balance`
**pasa** porque usa `quantity: 999999`, que `validate_mortality` rechaza antes de que el
generador de alertas se ejecute. **Ningún test de los 101 recorre la ruta de `P0-1`.**
Sigue asignado a `GA-REM-005`.

---

## 5. La suite tiene fecha de caducidad

`validate_period_open` (`validators.py:343`, `BR-19`) rechaza eventos con más de 90 días
de antigüedad. Los tests heredados fijan fechas literales de junio de 2026:

```
test_full_workflow_audit.py   event_date: "2026-06-29"   ->  caduca ~2026-09-27
test_operations.py            event_date: "2026-06-23"   ->  caduca ~2026-09-21
```

A partir de esas fechas **decenas de tests hoy en verde empezarán a fallar** sin que nadie
cambie una línea de código. Se detectó al sondear `P0-1` con fecha `2026-06-01`, que ya
está fuera de plazo:

```
app/operations/validators.py:343: BusinessRuleViolation:
  La fecha del evento (2026-06-01) está en un período cerrado (+90 días).
```

Se registra como **`R-28` (P1)**: las fechas de los tests deben ser **relativas a `date.today()`**,
no literales. Sin esto, la línea base de RUN 05 no es reproducible dentro de un mes, y
`GA-REM-016` (E2E) heredaría el mismo defecto. **Debe resolverse antes de que expire el
plazo**, es decir, antes del 2026-09-21.

---

## 6. Hallazgos nuevos generados por Track C

| ID | Hallazgo | Sev. | Evidencia | Destino |
|---|---|---|---|---|
| `P0-14` | 14 columnas de datos operativos descartadas en la creación de eventos | **P0** | `service.py:69-81` vs `schemas.py:83-106` vs `models.py:104-117` | **`GA-REM-023`** (nueva) |
| `R-26` | 7 reglas de negocio devuelven 500 en lugar de 400 | P1 | `service.py:309-364` · verificado en ejecución | **`GA-REM-023`** |
| `R-27` | `_get_role_by_name` responde 500 ante configuración ausente | P2 | `review/service.py:505-508` | `GA-REM-023` |
| `R-28` | La suite caduca por `BR-19`: fechas literales de junio de 2026 | P1 | `validators.py:343` · fechas en 2 ficheros de test | `GA-REM-015` (cierre) |
| `R-29` | `test_farm_inspection_without_house_id_still_accepted` contradice a `validators.py:365` sin árbitro documental | P2 | `SPEC_MISMATCH` | `GA-REM-018` |

Ninguno se corrige en esta Wave.

---

## 7. Declaración de integridad

- **Ningún test se modificó** para que pasara.
- **Ningún código de aplicación se modificó** para complacer a un test.
- Las dos sondas temporales (`test_p01_probe.py`, `test_rc_probe.py`, `test_r26_probe.py`)
  se eliminaron tras cada ejecución y no forman parte de la suite.
- La ejecución final se reprodujo dos veces con resultado idéntico.
- Producción no se tocó en ningún momento.

# GLOBAL AVÍCOLA — Auditoría final independiente pre-SAP · Compuerta de integridad de datos

| Campo | Valor |
|---|---|
| Repositorio | `/home/maria/Proyectos/GlobalAvicola` · rama `main` · HEAD `c0b4afc` (GA-F01 C3) |
| Runtime de referencia | `https://avicola.globaldv.net` (empresa 1) + pila local aislada (uvicorn con `lifespan`, base sembrada) |
| Fecha de auditoría | 2026-09-13 |
| Auditor | Claude (auditoría independiente; sin modificar código, tests ni documentación existente) |
| Alcance de este documento | Encargo §33–38 (población/saldos, máquina de estados, maestros, reportes, auditoría, atomicidad/concurrencia/idempotencia), §60 (compuerta de integridad de datos) y §61 (compuerta de base de datos). Los huecos de autorización se tratan en `GA_CLAUDE_SECURITY_FINAL_AUDIT.md` y aquí se referencian por su código `GAP-xx`. |
| Método | Lectura directa de `backend/app` y `frontend/src`; grep transversal; cruce con `backend/tests`; suite completa ejecutada en PostgreSQL de pruebas; sondas de runtime local (con `lifespan`, para observar el listener de auditoría) y productivo por UI/API oficiales; deduplicación contra `audit/remediation/REMEDIATION_BACKLOG.md`. |
| Codificación de hallazgos | `E-xx` (dominio, este documento) y `GAP-xx` (seguridad). **No se asignan R-numbers**. |

Rutas abreviadas: `app/…` = `backend/app/…`; `tests/…` = `backend/tests/…`; `alembic/…` = `backend/alembic/…`; `frontend/…` = `frontend/src/…`. Leyenda: **PASS** · **PARTIAL** · **FAIL** · **UNKNOWN**. Estado de confirmación: **CONFIRMED_IN_CODE** (lectura), **CONFIRMED_RUNTIME** (observado), **UNKNOWN_RUNTIME** (no discriminado).

---

## 0. Resumen ejecutivo

**Veredicto de la compuerta de integridad de datos: FAIL.**

El **ledger de población** es correcto y está protegido: invariante `saldo ≥ 0` bajo `SELECT … FOR UPDATE` para aves, huevos e incubación; idempotencia de alta por clave de cliente; reverso neto cero; todo cubierto por tests y confirmado en runtime productivo (horquilla exacta 50/51 tras una recepción de 50; mortalidad de 99999 rechazada con «excede el saldo (49)»; BR-08, BR-14, BR-18 aplicados; 0×5xx). La **atomicidad** por petición está verificada en arranque y la aprobación con lote automático (OD-25) es una sola transacción.

La compuerta falla en los **consumidores** del ledger y en la **pista de auditoría**:

| Bloqueante | Sev. | Naturaleza | Registro |
|---|---|---|---|
| **E-02** | **P1** | Un lote con cualquier reverso efectivo **no puede cerrarse nunca**: `validate_lot_records_approved` trata `REVERSED` como «sin aprobar» y `REVERSED` no es cancelable. Reverso y cierre son mutuamente excluyentes. | **NUEVO** |
| **E-01** | P2 | Tras un reverso de `bird_reception`, la OC (BR-18) acumula **2n en lugar de 0** (original y contrapartida `REVERSED` cuentan): entregas legítimas rechazadas; consumo de OC incorrecto hacia SAP. Incumple «reversal consistency» (§60). | **NUEVO** |
| **E-11** | P1 (backlog `P1-12`) | Auditoría **duplicada en runtime real**: listener `after_flush` y helpers escriben a la vez; observado en local con `lifespan`: 13 filas para 5 acciones (created ×2, review_started ×3, approved ×2 + `corrected` espuria). Los tests no lo ven porque `ASGITransport` no ejecuta `lifespan`. | **EXISTING** `P1-12` sin evidencia de cierre |
| **E-09** | P2 | `batch-approve`/`batch-reject` exigen `review:review` (un «Supervisor Avícola» aprueba en lote) frente a `approvals:approve/reject` en las rutas unitarias. Rompe la consistencia de aprobación (§60) sobre el estado SAP-bound. | **NUEVO** |
| **GAP-06** | P2 | Referencias foráneas sin verificar en el lote (`house_id`, `genetic_line_id`, `weight_curve_id`). | NUEVO (documento de seguridad) |
| **GAP-14** | P3 (fase SAP) | Consolidación SAP sin bloqueo → duplicado de `ConsolidatedMovement`; re-enlace idempotente roto. | NUEVO (documento de seguridad) |
| **E-25** | P1 SAP (`R-157`) | `SENT_TO_SAP`/`SAP_CONFIRMED` no auditados; `SAP_ERROR` sin productor; `retry` salta `SENT_TO_SAP`; nivel 3 de aprobación sin efecto. Es el trabajo pendiente de la fase SAP. | **EXISTING** `R-157`, `P1-13`, `R-142` |

Condicionales: **R-164** (`lots.company_id` nulable; deuda de datos `UNKNOWN`: bloquea si existen filas `NULL` en el entorno certificable) y **GAP-05** (`R-50`, si se delega `masters:*`).

Los KPI (compuerta FAIL por fórmulas `R-131/132/133/134/141` presentes y E-05/E-24) **no bloquean SAP** por sí mismos: no son dato SAP-bound y la ola C está pausada por decisión del propietario.

---

## 1. Método, fuentes y estado de la evidencia

### 1.1 Fuentes primarias

- Código: `app/operations/validators.py`, `app/operations/service.py`, `app/lots/service.py`, `app/review/service.py`, `app/corrections/service.py`, `app/reversals/service.py`, `app/reports/service.py`, `app/dashboard/service.py`, `app/audit/{listeners,helpers,service,models}.py`, `app/notifications/{sla,recipients}.py`, `app/integrations/sap/service.py`, `app/masters/{models,service,curves}.py`, `app/transaction.py`, `app/database.py`, `alembic/versions/*` (38 revisiones), `backend/docker-entrypoint.sh`.
- Especificación canónica: `specs/global-avicola/spec.md:287-302` (BR-01…BR-16), `docs/02-functional-spec.md` §3.11/§3.12/§3.14, `docs/12-approval-workflow.md` §4/§6, `specs/remediation/OD-17`, `OD-19`, `audit/ga-gov-02/GA_GOV_02_OWNER_DECISION_PACKET.md` (OD-22), `audit/ga-r153/GA_OD_25_GRANDPARENT_LOT_ON_APPROVAL_DECISION.md` (OD-25).
- Tests: `backend/tests/*.py` en HEAD: **1201 passed · 25 failed · 49 skipped** (clasificación completa en `GA_CLAUDE_SECURITY_FINAL_AUDIT.md §1.2` y Anexo B: 17 obsoletos frente a OD-16, 5 por fixture `.test`, 3 guardas obsoletas; ninguno revela regresión de integridad).
- Runtime: `evidence/runtime-gp-e2e.json` (producción-like), `evidence/ui-e2e-local.json` (local con `lifespan`), `evidence/ui-e2e-local-pass2.json` (H8b, en curso), certificación `R-189` en el mensaje del commit `c0b4afc` (corrida B 35/35, población exacta 100 con horquilla 100/101).

### 1.2 Evidencia de runtime relevante para integridad

| Observación | Entorno | Resultado | Fuente |
|---|---|---|---|
| Horquilla exacta de población tras recepción de 50 | producción-like, empresa 1 | mortalidad 51 → 400 «Mortalidad (51) excede el saldo de aves disponibles (50)»; 50 aceptado | `evidence/runtime-gp-e2e.json` R-07 |
| BR-01 sobre saldo vivo | producción-like | mortalidad 99999 → 400 «excede el saldo de aves disponibles (49)» (saldo ya decrementado por la mortalidad anterior) | ídem R-13 |
| BR-14 segregación | producción-like | aprobador que rechazó → `approve` 403 | ídem R-11 |
| BR-08 (galpón en eventos de ubicación), BR-18 (límite de OC) | producción-like | aplicados (4xx con mensaje) | ídem |
| Sin 5xx en el recorrido | producción-like | `5xx 0 · 4xx 52` | ídem, resumen |
| Población exacta 100 y horquilla 100/101 en el retry UAT-01..07 | producción-like (R-189) | 7/7 | commit `c0b4afc` |
| Línea de tiempo de auditoría de un evento operativo | **local con `lifespan`** | **13 filas para 5 acciones** (detalle §2.7) | `evidence/ui-e2e-local.json` H6/H8 |
| Reverso vía API | local | `POST /reversals` → contrapartida `pending_review` → `start` 200 → `complete` 200 → original y contrapartida `reversed` | ídem H8 |
| `REVERSED` no cancelable | local | `cancel` → 400 «No se puede cancelar un evento aprobado, consolidado, enviado o confirmado por SAP, con error de SAP o ya anulado» | ídem H8 |
| Cierre del lote con reverso | local | bloqueado antes por BR-05: 400 «sin al menos un registro de pesaje» (el lote de prueba no tenía pesaje) → E-02 no reproducido en H8; experimento de lotes gemelos H8b en curso | ídem H8; H8b |
| Cierre con registros sin aprobar (R7) | local | 400 «10 registro(s) sin aprobar (10 en «registered»)» y luego «(10 en «pending_review»)» | ídem BO-close |
| Población visible en detalle de lote | local | `lotdetail-poblacion-visible: false` (E-20) | ídem |

---

## 2. Compuertas

### 2.1 Población (ledger de aves) — **PARTIAL** (invariante PASS · consumidores FAIL)

#### 2.1.1 Función canónica

| Aspecto | Evidencia |
|---|---|
| Función | `get_current_bird_balance(db, lot_id)` — `app/operations/validators.py:49-88` |
| Fórmula | `apertura + Σ entradas − Σ salidas` (`:52-57`). Apertura = `OpeningBalance.initial_male_count + initial_female_count` (`:79-88`). Entradas = `BIRD_RECEPTION`, `BIRTH_REGISTRATION` (`:70`). Salidas = `MORTALITY_RECORDING`, `CULL_RECORDING`, `BIRD_EXIT`, `CHICK_DISPATCH` (`:71-76`). Neutros = `BIRD_TRANSFER`, `BIRD_DISTRIBUTION` (RR-02, `:57`). Acumulados históricos del `OpeningBalance` no se restan (RR-08, `:65-68`). |
| Filtro de estado | `_suma_neta` (`:21-46`): cuentan **todos los estados salvo `CANCELLED`** (`:39`); la aprobación no es requisito para contar (decisión documentada `:744-748`). Contrapartidas de reverso excluidas del natural (`:40`) y restadas solo si `status == REVERSED` (`:42-45`). |
| Cantidad sumada | `bird_movements.quantity` sin discriminar sexo (`:77-78`); `chicks_healthy/weak`, `dead_on_arrival`, `received_total`, `rejected_on_arrival` son atributos y no afectan al saldo (`models.py:129-137`; RR-12 `:536-574`). |
| Empresa | La función suma por `lot_id` sin `company_id`; mitigado por `validate_lot_active(..., company_id)` en el alta (`:501-529`) y `verificar_pertenencia` en edición/corrección. |
| Serialización | `bloquear_saldo_del_lote` (`SELECT … FOR UPDATE` sobre `lots.id`, `:197-208`); multi-lote en orden ascendente `bloquear_saldos_de_lotes` `:316-323`. |
| Observabilidad | **No existe** endpoint que exponga el saldo (grep en `router.py`/`schemas.py`); la UI muestra `initial_population` (solo `OpeningBalance`) como población (`frontend/pages/lots/LotDetailPage.tsx:52-58,358-362` → `reports/service.py:143-144`). **E-20**. Confirmado en local: `lotdetail-poblacion-visible: false`. |

Otros saldos (mismo fichero):

| Saldo | Función | IN | OUT | Filtro | Bloqueo de fila |
|---|---|---|---|---|---|
| Huevo fértil en granja (BR-02) | `get_egg_balance` `:117-146` | `EGG_COLLECTION` filas `egg_type == 'fertile'` (`:130-133`) | `EGG_DISPATCH` fértil (`:140-143`) | `≠ CANCELLED`; sin `_suma_neta` (huevos no reversibles, OD-19 §18, `reversals/service.py:42-46,107-109`) | `validate_egg_dispatch` `:239-256` → `bloquear_saldo_del_lote` (`:249`) — **R-161 cerrado** |
| Huevo en incubadora (BR-03) | `get_hatchery_egg_balance` `:149-175` | `EGG_RECEPTION_HATCHERY` fértil (`:160-163`) | `INCUBATION_LOAD.hatchery_params.quantity_loaded` (`:167-173`) | `≠ CANCELLED` | `validate_incubation_load` `:259-274` (`:267`) |
| Pollitos viables (BR-04) | `get_viable_chick_balance` `:178-192` | `BIRTH_REGISTRATION` | `CHICK_DISPATCH` + `MORTALITY` + `CULL` (R-130) | `_suma_neta` (reverso incluido) | `validate_chick_dispatch` `:277-288` (`:281`) |
| Ovoscopía / transfer_to_hatcher / clasificación | — | — | — | **Sin saldo** (`ENTRADAS_DE_SALDO`/`SALIDAS_DE_SALDO` `:297-300`); no reversibles | — |

#### 2.1.2 Ledger por evento / acción (§33 del encargo)

| Evento / acción | Disparador (ruta · permiso) | Entrada | Δ saldo | Lote | Precondición | Chequeo negativo | Protección doble conteo | Reverso | Auditoría |
|---|---|---|---|---|---|---|---|---|---|
| `bird_reception` | `POST /operations` · `operations:create` (`operations/router.py:70-77`) | `bird_movements[].quantity/sex`, `house_id`, `sap_document_ref`, `received_total`, `dead_on_arrival`, `rejected_on_arrival` | **+Σ quantity** (DOA/rechazadas no restan, RR-12 `validators.py:536-565`) | `lot_id` | BR-07 (`:501-529`, `service.py:836`); BR-06 fecha (`:488-498`); BR-08 galpón (`:822-839`); BR-19 periodo (`:794-819`); BR-17 capacidad **por evento** (`:712-725`, `service.py:900-902`); BR-18 acumulado de OC (`:728-791`); B01 cuadre reproductoras (`:553-565`) | n/a (entrada) | `idempotency_key` único (`service.py:225-234`, `models.py:101`); `≠ CANCELLED`; contrapartida excluida del natural | Elegible (`reversals/service.py:33-36`); al aprobar `saldo − n ≥ 0` (`:198-207`) | `audit_event_created` `service.py:308` |
| `bird_distribution` | ídem | `bird_movements`, `house_id` | **0** (RR-02) | `lot_id` | BR-07/08/19; BR-17/18 (`service.py:900-906`) | n/a | — | Elegible «sin saldo» (`:37-41`) | ídem |
| `bird_transfer` | ídem | `source_house_id/target_house_id` | **0** — no hay ledger por galpón; solo pertenencia (`service.py:863-867`) | `lot_id` | BR-07/08/19 | n/a | — | Elegible «sin saldo» | ídem |
| `bird_exit` | ídem | `bird_movements`, `destination_farm_id/plant_id`, `transport_id` | **−Σ quantity** | origen (el destino registra su propia recepción) | `validate_bird_decrement` `:211-231` bajo `FOR UPDATE` (`service.py:939-946`) | BR-01 (R-130) | `≠ CANCELLED`; contrapartida | Elegible; saldo resultante ≥ 0 | ídem |
| `mortality_recording` | ídem | `bird_movements`, `cause_id` | **−Σ quantity** | `lot_id` | `validate_mortality` `:234-236` → BR-01 (`service.py:931-938`); alerta ≥3 %/8 % (`:551-581`, `config.py:89-90`) | BR-01 | ídem | Elegible; BR-01 y BR-04 (`reversals/service.py:198-214`) | ídem |
| `cull_recording` | ídem | `bird_movements`, `cull_cause_id` | **−Σ quantity** | `lot_id` | `validate_bird_decrement` (`service.py:939-946`) | BR-01 | ídem | Elegible | ídem |
| `birth_registration` | ídem | `bird_movements` (por sexo o `mixed`), `chicks_healthy/weak` | **+Σ quantity**; sanos+débiles ≤ nacidos (BR-21 `:577-613`) | `lot_id` (incubadora) | BR-21 nacidos ≥ 1 | n/a | ídem | Elegible (`:208-214`) | ídem |
| `chick_dispatch` | ídem | `bird_movements`, `destination_farm_id` | **−Σ quantity** | `lot_id` (incubadora) | `validate_chick_dispatch` `:277-288` (BR-04; R-174 rechaza 0 `service.py:961-966`) | BR-04 + BR-01 | ídem; `ChickBatch` por destino (`service.py:498-517`) | Elegible | ídem |
| `grandparent_import` | ídem (lote opcional `service.py:61-68`) | `extra_data.import_plan`, `bird_movements` ♂/♀, `sap_document_ref`, `supplier_id` | **0** — documental (BR-22 `:624-667`; `validate_oc_limit` solo cuenta `BIRD_RECEPTION` `:774`) | ninguno (o legado) | BR-22 | n/a | — | **No elegible** (`reversals/service.py:110-112`) | ídem |
| Lote automático OD-25 | `approve`/`complete_review` de la importación sin lote (`review/service.py:513-515`, `:349-351`) → `crear_lote_de_importacion_si_procede` (`lots/service.py:128-196`) | plan `arrival_date`, sexos | **0** — `Lot` sin `OpeningBalance` ni recepción (`:158-168`; OD-25 §2.5) → **población cero verificada** | `L-GP-{año}-{nn}` | solo al aprobar; lock consultivo por (empresa, año) `:152` | n/a | unicidad global de `lot_code` con reintento `:154-181` | — | `audit_accion CREATED` módulo `LOTS`, `origin="grandparent_import_approval"` `:191-195` |
| Saldo de apertura (`activate-manual`, R-67) | `POST /lots/activate-manual` · `lots:create` (`lots/router.py:99-106`) | `initial_male/female_count`, acumulados, `activation_date`, `phase_at_activation_id` | **+(♂+♀)** vía `OpeningBalance` (`:79-88`) | `lot_id` | pertenencia y unidad (`lots/service.py:573-580`); único por lote (`:583-590`, 409); sin historia de eventos (`:596-611`); mortalidad acumulada ≤ inicial (`:614-623`) | n/a | 409 si ya hay eventos | no aplica | **Sin `audit_accion`** (`:555-659`) — **E-10** |
| Cierre de lote (`POST /lots/{id}/close`) | `lots:create` (`lots/router.py:80-92`) | — | **0** | `lot_id` | activo (`:445-449`); BR-05 pesaje + alimento (`:456` → `validators.py:362-390`); R7/R-76 sin registros no aprobados (`:465` → `validators.py:409-455`) | n/a | 2.º cierre → 400 | — | **Sin `audit_accion`** (`:438-549`) — **E-10** |
| Evento `lot_closure` | `POST /operations` tipo `lot_closure` | `lot_id` | **0**; **no cierra el lote** (solo BR-05 `service.py:967-970`) | `lot_id` | BR-05 | — | — | no elegible | `audit_event_created` |
| `update_event` (PUT) | `PUT /operations/{id}` · `operations:update` (`router.py:295-303`) | `OperationalEventUpdate` (`schemas.py:195-253`) **sin `bird_movements`** (cantidad inmutable tras alta) | **mover el efecto entero** si cambia `lot_id` (R-173) | origen y destino | `EDITABLES` (`service.py:73-74`), BR-15 (`:1134`), no contrapartida (`:1141-1144`); `verificar_destino_de_edicion` `:1261-1305` | entrada: origen ≥ 0 (`validate_retiro_de_entrada` `:326-344`); salida: destino como alta (`:347-359`), bajo bloqueo de ambos lotes (`:1296`) | relectura bajo bloqueo (`:1297-1299`) | — | `audit_state_transition` con `previous_values/new_values` `:1172-1173` |
| `cancel_event` | `POST /operations/{id}/cancel` · `operations:create` (`router.py:320-327`) | — (sin motivo: R-140) | **−efecto** | `lot_id` | `NO_CANCELABLES` (`:76-78`); relectura bajo `FOR UPDATE` (`:1332-1334`) | entrada: `saldo − n ≥ 0` (`:1342-1343`) | 2.ª → 400 (`tests/test_edit_cancel_balance.py:380-417`) | — | `audit_state_transition` `:1350` |
| Corrección (`POST /corrections`) | `corrections:correct` (`corrections/router.py:16-20`) | `field_name` de `campos_corregibles()` (`corrections/service.py:171-181`) — sin cantidades | **Δ solo si `lot_id`** (`:70-81`) | ídem | estados correctables `:38-39`; no contrapartida `:33-36` | ídem PUT | — | — | `audit_correction` `:105-112` + `CorrectionLog` |
| Reverso (OD-19) | `POST /reversals` · `reversals:create` (`reversals/router.py:16-20`) + aprobación | `event_id`, `reason` | solicitud **0**; aprobación **−efecto del original** (ambos `REVERSED` `:215-216`) | lote del original | original `APPROVED` no consolidado (`:99-106`); tipo elegible; una contrapartida activa (`:115-123` → 409) | BR-01/BR-04 sobre el resultante (`:198-214`) | `FOR UPDATE` del original en solicitud y aplicación (`:74-79`, `:96`, `:194`) | — | `audit_accion CREATED entity=reversal` `:156-161`; `audit_state_transition approved→reversed` `:218` |

#### 2.1.3 Secuencias de riesgo

| Secuencia | Resultado | Evidencia | Estado |
|---|---|---|---|
| Aprobar → editar / corregir | Bloqueado (`APPROVED ∉ EDITABLES`, `service.py:73-74,1137-1138`; `corrections/service.py:38-44`) | tests `test_edit_cancel_balance.py` | PASS |
| Aprobar → cancelar | Bloqueado (`NO_CANCELABLES` `:76-78,1338-1339`); único camino: reverso | runtime local: `REVERSED` → cancel 400 | PASS |
| Reverso de recepción tras mortalidad | Aprobación del reverso exige `saldo − n ≥ 0` (`reversals/service.py:204-207`) o `ROLLBACK` (`tests/test_internal_reversal.py:342`) | — | PASS |
| Decrementos concurrentes | `FOR UPDATE` antes de leer (`validators.py:225,249,267,281`); `tests/test_population_invariant.py:341`; `test_egg_incubation_concurrency.py:272-288` | — | PASS |
| Cancelar entrada vs salida concurrente | cancelación bloquea y relee (`service.py:1332-1334`); `tests/test_edit_cancel_balance.py:419-460` | — | PASS |
| Idempotencia de alta | `idempotency_key` (`models.py:101`; `service.py:225-234`); `test_population_invariant.py:355`; `tests/test_multi_company.py:107` | — | PASS |
| Recepción cuenta población **una sola vez** | única fila de `bird_movements` por recepción; `≠ CANCELLED`; sin doble suma por estado; DOA/rechazadas fuera del saldo | runtime: horquilla exacta 50/51 y 100/101 | PASS (CONFIRMED_RUNTIME) |
| Lote automático con población cero | `Lot` sin `OpeningBalance` ni recepción (`lots/service.py:158-168`) | runtime R-189: import 121 → `L-GP-2026-11` → recepción 122 → población 100 | PASS |
| **Reverso de recepción con OC (BR-18)** | `validate_oc_limit` (`validators.py:769-783`) suma `BIRD_RECEPTION` con `status.not_in([CANCELLED])` y la misma `sap_document_ref`; la contrapartida copia `sap_document_ref` (`reversals/service.py:126-134`) y termina `REVERSED` junto al original (`:215-216`) ⇒ **ambos cuentan**: acumulado = 2n en lugar de 0 | **E-01** | **FAIL** (CONFIRMED_IN_CODE) |
| **Lote con reverso efectivo no cierra** | `validate_lot_records_approved` excluye solo `ESTADOS_APROBADOS + CANCELLED` (`validators.py:400-406,436-438`); `REVERSED ∉` ambos; `REVERSED ∈ NO_CANCELABLES` (`service.py:76-78`) ⇒ 400 «1 en «reversed»» sin salida. Tests R7 no incluyen `REVERSED` (`tests/test_lot_close_approval.py:33-43`) | **E-02** | **FAIL** (CONFIRMED_IN_CODE; ver §2.11) |
| **Resumen de cierre cuenta anulados** | `close_lot` suma `total_mortality`, `total_feed_kg`, `total_eggs` sin filtro de estado (`lots/service.py:469-498`): incluye `CANCELLED` (y `REVERSED` + contrapartida) | **E-03** | **FAIL** (CONFIRMED_IN_CODE) |
| Alta rechazada sigue descontando | `REJECTED` cuenta hasta cancelación (decisión `validators.py:744-748`, `:426-427`) | documentado | decisión |
| BR-17 no acumulativa | `validate_house_capacity` compara un evento contra `House.capacity` (`:721`); N recepciones superan la capacidad; no hay ledger por galpón (RR-02) | **E-04** (parcial en `R-176`, `BACKLOG:1294`) | P3 decisión |

**Veredicto población**: invariante, serialización y reverso neto cero **PASS** (código + tests + runtime). **FAIL** en tres consumidores (E-01, E-02, E-03) y en observabilidad (E-20).

### 2.2 Saldos de huevo e incubación — **PASS**

| Control | Código | Tests | Notas |
|---|---|---|---|
| BR-02/BR-03/BR-04 bajo bloqueo de fila (R-161) | `validators.py:239-288` (`validate_egg_dispatch`, `validate_incubation_load`, `validate_chick_dispatch` llaman `bloquear_saldo_del_lote` antes de leer) | `tests/test_egg_incubation_concurrency.py::test_r161_05/06_*` (`:227-316`) | **R-161 CERRADO** en código; la fila `REMEDIATION_BACKLOG.md:1001` y recuentos `:1013,1045` conservan texto «OPEN» anterior a la evidencia `:1267` (inconsistencia documental) |
| Sin reverso de huevos/incubación (OD-19 §18) | `reversals/service.py:42-46` (`BLOQUEADOS_POR_R161`) | `tests/test_internal_reversal.py` | coherente con la ausencia de `_suma_neta` en `get_egg_balance` |
| Traspaso entre cadenas (OD-10): par despacho/recepción exactamente uno por despacho; cantidades derivadas de los movimientos persistidos | `business_units/handoff.py:34-67`; `operations/service.py:433-541` (`:477-496,523-541`), `:388-400`; `lots/router.py:203-236` | `tests/test_handoff_contract.py`, `tests/test_reception_lineage.py`, `tests/test_lineage_cancel_move.py`, `tests/test_birth_classification.py` | Sin unicidad en BD de `dispatch_event_id` en `egg_batches`/`chick_batches` (`lots/models.py`): unicidad «exactamente uno» de aplicación y sin bloqueo (P3, ver §2.10) |

### 2.3 Atomicidad — **PASS**

| Control | Veredicto | Código | Tests | Notas |
|---|---|---|---|---|
| Frontera transaccional por petición: commit en la ruta antes de responder; fallo de commit → 500 + rollback; errores → rollback en `get_db` | PASS | `app/transaction.py:36-60`; `app/database.py:25-44`; verificación en arranque `transaction.py:76-104`, `main.py:181-183` | `tests/test_transaction_boundary.py::test_t_026_01…12` | Excepciones documentadas de commit en servicio: `auth/service.py:199` (auditoría de login fallido), `operations/service.py:1383,1414` (evidencias, `test_t_026_09`), `notifications/sla.py:252` (tarea de fondo) |
| Aprobación + lote automático `L-GP-{año}-{nn}` en la **misma** transacción; fallo revierte ambos | PASS | `review/service.py:490-531`, `:333-351`; `lots/service.py:128-196`: `pg_advisory_xact_lock(hashtext('lote-gp:{empresa}:{año}'))` (`:100-108,152`), `begin_nested()` + reintento ante `IntegrityError` de `lot_code` (`:154-181`), `event.lot_id` fijado `:185` | `tests/test_r153_import_lot_auto.py::test_r153_ac31_ac32_fallo_de_lote_revierte_la_aprobacion`, `::test_r153_ac23_ac26_doble_aprobacion_no_duplica`, `::test_r153_ac09_ac10_secuencia_consecutiva` | Lock solo en PostgreSQL (`:106`) |
| Recepción + saldo (decremento bajo `FOR UPDATE`) | PASS | `validators.py:197-231` | `tests/test_population_invariant.py`, `tests/test_mortality.py` | La aprobación no bloquea el saldo (`R-166 ≠ R-161`, decisión) |
| Ciclo de concesión (disable → revocaciones + auditoría por concesión, una transacción) | PASS | `business_units/admin.py:178-214` | `tests/test_r188_bu_lifecycle.py` (5 rojos por fixture `.test`, no por producto), `tests/test_business_unit_admin.py` | runtime `ga-fe-02-e §12` auditoría 1:1 |
| Reverso: original bloqueado al solicitar y al aplicar; ambos `REVERSED` en la misma transacción; notificación en la misma transacción | PASS | `reversals/service.py:74-79`, `:96`, `:181-219` | `tests/test_internal_reversal.py` (RV/EF/S/AU) | — |
| Traspaso entre cadenas: vínculo automático en la transacción del alta | PASS | `operations/service.py:433-541` | `tests/test_handoff_contract.py` | — |
| Riesgos de estado partido conocidos | PARTIAL (P3) | `operations/service.py:1409-1414` (`os.remove` antes del commit); `router.py:374-380` (fichero escrito antes de `create_evidence`); `sap/adapter.py:110-113` (artefacto escrito antes de persistir `SapPayload`) | `test_t_026_09` (solo doble commit) | = GAP-12 (parcial) |

### 2.4 Idempotencia — **PARTIAL**

| Control | Veredicto | Código | Tests | Notas |
|---|---|---|---|---|
| `operations.idempotency_key` (R-146): clave de cliente, opcional, inmutable tras alta, única global, consultada por empresa; devuelve el existente | PASS (implementado) | `operations/schemas.py:167,183`; `operations/models.py:101`; `operations/service.py:224-234` | `tests/test_multi_company.py::test_idempotency_key_prevents_duplicate` (`:107`), `tests/test_population_invariant.py:355` | **EXISTING `R-146`** (`BACKLOG:938` aún como hallazgo: verificar cierre). Residuo GAP-15: colisión de clave entre empresas → `IntegrityError` 500 + oráculo (P3). Sin clave, doble `POST` duplica (decisión). |
| Doble `submit`/`cancel` | PASS | `service.py:1332-1339` (cancel bloquea y relee); `:1307-1323` (submit sin bloqueo, transición idempotente) | `tests/test_edit_cancel_balance.py`, `tests/test_state_continuity.py::test_u05_*` | doble submit concurrente deja dos filas `UPDATED` (sin efecto en saldo) |
| Doble aprobación / doble reverso | PASS | `review/service.py:89-107` (`FOR UPDATE` + relectura); `reversals/service.py:113-123` (409 si contrapartida activa) | `tests/test_review_decision_concurrency.py::test_r166_02`, `tests/test_internal_reversal.py::test_rv03` | — |
| SAP: `idempotency_key` SHA-256 única; estados `PREPARED/SENDING/CONFIRMED/FAILED/RETRYING`; backoff 1/5/15 min; adaptador manual nunca marca `SENT_TO_SAP` | PASS con defecto | `sap/adapter.py:196-202`; `sap/models.py:47-52,143-144`; `sap/service.py:275-293`, `:344-373`, `:402-462` | `tests/test_sap.py`, `tests/test_sap_transversal.py` | **GAP-14**: `service.py:289-291` consume el `Result` dos veces (re-enlace idempotente → 500); `consolidate_approved` (`:158-227`) sin bloqueo → dos consolidaciones concurrentes crean dos `ConsolidatedMovement` con los mismos `event_ids` |
| Unicidad de concesiones/habilitaciones | PASS | `business_units/models.py:67`, `:121-122` | `tests/test_business_unit_admin.py::test_conceder_dos_veces_no_duplica`, `tests/test_migration_bu_catalog.py` | — |

### 2.5 Concurrencia — **PASS**

| Control | Código | Tests |
|---|---|---|
| Saldos de aves, huevos, incubación y viables bajo `FOR UPDATE` de la fila del lote | `validators.py:197-208`, `:225,249,267,281`, `:316-323` | `tests/test_population_invariant.py`, `tests/test_egg_incubation_concurrency.py`, `tests/test_edit_cancel_balance.py:419-460` |
| Decisión de revisión concurrente: `FOR UPDATE` + relectura (R-166) **después** de la cadena inquilino/unidad | `review/service.py:89-107`, aplicado `:401`, `:627` | `tests/test_review_decision_concurrency.py::test_r166_01…13` (12 rojo por aserción 403→404, no por concurrencia) |
| Reverso: exclusión de contrapartida activa y de efectos | `reversals/service.py:74-79`, `:113-123`, `:181-219` | `tests/test_internal_reversal.py` |
| Consecutivo del lote automático: lock consultivo por (empresa, año) + reintento | `lots/service.py:100-108,152-181` | `tests/test_r153_import_lot_auto.py` |
| Consolidación SAP sin bloqueo | `sap/service.py:158-227` | — | GAP-14 (P3, fase SAP) |

### 2.6 Referencias foráneas (inquilino / unidad / catálogo) — **FAIL**

| Control | Veredicto | Código | Tests | Notas |
|---|---|---|---|---|
| Submovimientos: referencias estructurales (R-180) y catálogos (R-179) verificados contra la empresa | PASS | `operations/service.py:841-877`, `:1209-1216`; `tenancy.py:73-186` | `tests/test_submovement_structural_tenancy.py`, `tests/test_master_reference_tenancy.py` | — |
| Lote: `farm_id` (403 si ajena) y `area_id` (activa, OD-21) | PASS | `lots/service.py:320-329`, `:341-347`; `tenancy.py:94-117` | `tests/test_lot_area_ownership.py::test_ga06a_01/02` | — |
| **Lote: `house_id`, `genetic_line_id`, `weight_curve_id` sin verificar** en alta y edición | **FAIL** | `lots/service.py:362-392`, `:275-307`, `:411-436`; `masters/service.py:187` (`_PADRES_TENANT = {farm_id, hatchery_id}`); `lots/schemas.py:14-20,65-67` | NO TEST | **GAP-06** — lote de A en galpón de B; evaluación de peso contra la curva de B (`operations/service.py:744-824`) |
| **Maestros: `company_id` fijable por el cliente** (Create/Update) | **FAIL** (mitigado por semilla) | `masters/schemas.py:64-65,124-125,436-503,632-651`; `masters/service.py:232-234,248-254` | NO TEST | **GAP-05 = R-50** (ausente del backlog) |
| Cadena granja→galpón, planta→incubadora | PASS | `masters/service.py:187-206`; `masters/router.py:132-174` | `tests/security/test_multitenant_isolation.py::test_no_se_puede_crear_un_galpon_en_una_granja_ajena` | — |
| Traspaso: vínculo generacional y flujos permitidos | PASS | `lots/router.py:239-331`; `tenancy.py:204-253`; `handoff.py:34-67` | `tests/test_handoff_contract.py`, `tests/test_traceability_ownership.py` | — |
| OD-21 / R-185: elegibilidad por estado **solo Área→Lote** | PASS (alcance documentado) | `tenancy.py:94-117` (`exigir_activo=True`) desde `lots/service.py:345-347`, `:433-435`; `verificar_catalogos_del_evento` (`tenancy.py:120-154`) no pasa `exigir_activo`; `validate_house_capacity`, `verificar_ubicacion`, `verificar_pertenencia` no miran `is_active` | `BACKLOG:1831-1864` CLOSED_OWNER_ACCEPTED | Los demás selectores admiten referencias inactivas; `MasterService.get_all` (`:122-168`) no filtra `is_active`; el wizard (`OperationFormPage.tsx:343-368`) tampoco. No es defecto nuevo (no sobregeneralizar OD-21). |
| `lots.company_id` nulable sin `NOT NULL` | **PARTIAL** | `masters/models.py:283`; solo índice (`alembic/versions/4982c3092c14:37`); prevención de aplicación (`AC-L05`) | — | **EXISTING `R-164`** (`BACKLOG:1071`, deuda de datos `UNKNOWN`, `BLOCKED_RUNTIME`) |
| Catálogos compartidos (`company_id NULL`) aceptados como referencia pero no listados al inquilino | nota | `tenancy.py:114` vs `masters/service.py:95-96` | — | inconsistencia lectura/escritura, no fuga |

### 2.7 Pista de auditoría — **FAIL**

#### 2.7.1 Dos productores concurrentes y duplicación en runtime (E-11, CONFIRMED_RUNTIME)

| Mecanismo | Registro | Qué escribe |
|---|---|---|
| Listener `after_flush` | `audit/listeners.py:71-113`; registrado en `main.py:41-42` (`register_audit_listeners()` dentro de `lifespan`); usuario vía `ContextVar` fijado en `auth/security.py:165` | `OperationalEvent` nuevo → `CREATED`; cambio de `status` → acción según `_STATUS_TO_AUDIT_ACTION` (`:43-56`; nótese `"pending_review": CREATED` `:45`); `CorrectionLog` → `CORRECTED`; `ApprovalAction` → según `_APPROVAL_ACTION_TO_AUDIT` (`:58-64`). `company_id or 0` (`:140`). |
| Helpers explícitos | `audit/helpers.py` (`audit_event_created` `:73-92`, `audit_state_transition` `:95-148`, `audit_correction` `:151-174`, `audit_accion` `:225-262`) | llamados por los servicios (`operations/service.py:308`, `:1172`, `:1322`, `:1350`; `review/service.py:285`, `:314`, `:370`, `:376-380`, `:527`, `:551-553`; `corrections/service.py:105`; `reversals/service.py:156-161`, `:218`) |
| Tests | `tests/conftest.py:117-140` usa `httpx.ASGITransport(app=app)` **sin `lifespan`** ⇒ el listener no se registra; `tests/test_edit_cancel_balance.py:393` exige exactamente 1 fila `cancelled`; `test_audit_coverage.py:171` exige 1 `REVIEW_COMPLETED` | los tests **no pueden** detectar la duplicación |

**Observado en la pila local con `lifespan` (evidence/ui-e2e-local.json, H8, evento 15, `GET /audit/timeline`)** — 13 filas para 5 acciones de negocio:

| Acción de negocio | Filas escritas (`action` · `previous→new` · módulo · comentario) | Origen |
|---|---|---|
| Crear evento | `created` None→registered · operations · —; `created` None→registered · operations · — | listener (`:163-197`) + helper `audit_event_created` |
| Submit | `created` registered→pending_review · operations · —; `updated` registered→pending_review · operations · «Enviado a revisión» | listener (mapa `pending_review → CREATED`, **acción semánticamente incorrecta**) + helper |
| Start review | `review_started` pending_review→in_review · operations; `review_started` None→None · review; `review_started` pending_review→in_review · review · «Revisión iniciada por supervisor» | listener (status) + listener (`ApprovalAction STARTED_REVIEW`) + helper |
| Complete review (nivel único) | `approved` in_review→approved · operations; **`corrected` None→None · approvals**; `approved` in_review→approved · approvals; `review_completed` None→None · review | listener (status) + listener (`ApprovalAction` de tipo `CORRECTED` que escribe `complete_review`, `review/service.py:363`, mapeado por `listeners.py:61`) + helper + helper `REVIEW_COMPLETED` |
| Aplicación del reverso | `updated` approved→reversed · operations; `reversed` approved→reversed · operations · «Reverso…» | listener (status) + helper |

H6 (evento 1, solo alta): `created` ×2 con 22 ms de diferencia. Conclusión: **P1-12 «auditoría duplicada» no está resuelto**; además el listener introduce filas con acción incorrecta (`created` en submit, `corrected` en una aprobación sin corrección) que contaminan cualquier consulta por `action`.

#### 2.7.2 Cobertura por acción de negocio

| Acción | `AuditAction` · módulo | Escrita en | old/new | motivo | Hueco |
|---|---|---|---|---|---|
| Evento: crear / editar / submit / cancel | `CREATED` / `UPDATED` / `UPDATED` / `CANCELLED` · `OPERATIONS` | `operations/service.py:308`, `:1172-1173`, `:1322`, `:1350` | editar sí | cancel **sin motivo** (R-140) | E-21 |
| Batch de revisión → `PENDING_REVIEW` | solo `ApprovalAction STARTED_REVIEW` | `review/service.py:206-243` (`update()` masivo `:229-233`) | — | — | **E-06**: sin `audit_state_transition` ⇒ sin fila `new_state='pending_review'` ⇒ el SLA 24 h (`sla.py:44-60`) no ve estos eventos; ídem la contrapartida de reverso (`reversals/service.py:131`) |
| start / return / complete_review | `REVIEW_STARTED` / `RETURNED` / `APPROVED`+`REVIEW_COMPLETED` · `REVIEW` | `:285`, `:314`, `:370,376-380` | estados | sí | — |
| approve / reject | `APPROVED` (o `REVERSED`) / `REJECTED` · `APPROVALS` | `:527`, `:551-553` | estados | observaciones | **E-08**: `reject` fija `previous_state="corrected"` aunque venga de `IN_REVIEW` (`:629` permite ambos) |
| corrección | `CORRECTED` · `CORRECTIONS` | `corrections/service.py:105-112` | campo | `reason` | — |
| reverso solicitud / aplicación | `CREATED entity=reversal` / `REVERSED` | `reversals/service.py:156-161`, `:218` | ids | `reason` | — |
| Lote: crear (manual / auto) / editar | `CREATED` / `UPDATED` · `LOTS` | `lots/service.py:402-408`, `:191-195`; `masters/service.py:257-258` | sí | — | — |
| **Lote: cerrar / activate-manual / fases** | **NO** | `lots/service.py:438-549`, `:555-659`, `:685-697` | — | — | **E-10** (el cierre cambia `status`/`end_date`; la activación fija el saldo de apertura, dato crítico del ledger; `tests/test_opening_balance.py:363-388` solo comprueba campos) |
| Maestros CRUD (20 entidades) | `CREATED/UPDATED/DELETED` · `MASTERS` | `masters/service.py:242,257,266` | sí | — | — |
| **Curvas de peso: crear / activar** | **NO** | `masters/curves.py:90,143` | — | — | E-12 |
| **Usuarios: crear / editar (incl. rol) / desactivar** | **NO** | `auth/service.py:337-382`, `:384-421`, `:491-506` | — | — | **E-13** (`docs/02 §3.11.1` «cada acción»; `GA-REM-032` no los incluyó) |
| Contraseña | `UPDATED entity=user_password` · `AUTH` | `:474-489` | no | comentario | — |
| Roles: crear / editar | `PERMISSION_CHANGE` · `USERS` | `:613`, `:653` | permisos | — | — |
| Login / login fallido | `LOGIN` / `LOGIN_FAILED` · `AUTH` | `:212-214` / `:188-190` | — | — | usuario inexistente no auditado (R-83 = GAP-10) |
| **Logout** | **no existe endpoint** | `auth/router.py` | — | — | E-14 (= P1-4, `GA-REM-032 AC01` afirma lo contrario) |
| switch-company | `CONTEXT_SWITCHED` · `AUTH` | `:525-527` | — | — | — |
| BU habilitar/deshabilitar; conceder/revocar | `CONFIG_CHANGE` + `PERMISSION_CHANGE` (con `cause`) | `business_units/admin.py:197-214`, `:385-390`, `:423-428` | estados | — | — |
| Clasificar / reclasificar | `UPDATED` / `CORRECTED` · `OPERATIONS` | `classification.py:201-203`, `:327-329` | — | motivo | — |
| **Evidencias: subir / borrar** | **NO** | `operations/service.py:1363-1414` | — | — | E-15 (= GAP-12) |
| Alertas: resolver | NO | `:1011-1025` | — | — | menor |
| SAP: importar / consolidar / exportar / reintentar | `IMPORT` (`sap/service.py:118-122`) / **solo listener** / `EXPORT` (`:387-390`) / **NO** | — | — | — | E-25 |
| **Exportación Excel/PDF** | **NO** (100 % cliente `frontend/utils/export.ts`); `AuditModule.REPORTS` nunca usado | — | — | — | E-16 (`GA-REM-032 AC04` incumplido para informes) |

#### 2.7.3 Enum, inmutabilidad y consulta

- **`AuditAction` nunca escritos**: `LOGOUT`, `SENT_TO_SAP`, `SAP_CONFIRMED` (transiciones con `update()` masivo, `sap/service.py:353-360,446-450`), `SAP_ERROR` (sin productor); `CONSOLIDATED` solo por listener. Columnas `ip_address`, `user_agent`, `is_sensitive`, `sap_reference_id` **nunca pobladas** (grep) ⇒ filtro «documento SAP» y dato «IP o dispositivo» (`docs/02 §3.11.1/§3.11.2`) vacíos por construcción (E-17).
- **Inmutabilidad (R-148 = GAP-13)**: solo en aplicación (`audit/router.py:16-63` de solo lectura; sin `UPDATE/DELETE` en `app/`); en BD sin trigger/regla/`REVOKE` (`alembic/versions/ee30bd1aa374_add_audit_log.py`; grep en `alembic/versions`: vacío). Abierto (`BACKLOG:940`).
- **`company_id NOT NULL`** (R-83 = GAP-10): acciones sin empresa se descartan (`helpers.py:250-252`); el listener escribe `company_id or 0` (`listeners.py:140`, FK inexistente).
- **Contrato de consulta**: `GET /audit` (`audit/router.py:16-41`) aplica en servidor `user_id, action, entity_type, entity_id, module, lot_id, farm_id, date_from, date_to, state, sap_reference_id` (`audit/service.py:32-100`) acotado a empresa (`:48-49`). `AuditPage.tsx:61-72` solo envía `action, module, date_from, date_to` (E-17).

**Veredicto auditoría**: FAIL — duplicación confirmada en runtime (E-11, P1-12 abierto), dato crítico del ledger sin rastro (E-10: saldo de apertura, cierre), usuarios sin rastro (E-13), inmutabilidad solo aplicativa (R-148).

### 2.8 Máquina de estados — **PARTIAL**

`EventStatus` (`operations/models.py:58-73`). Transiciones implementadas:

| # | Transición | Ruta · permiso | Precondición | UI | Auditoría | Repetida | Nota |
|---|---|---|---|---|---|---|---|
| T1 | crear → `REGISTERED` | `POST /operations` · `operations:create` | — (`service.py:264`) | `OperationFormPage.tsx` | `:308` | `idempotency_key` | `DRAFT` **sin productor** (R-154 PARTIAL) |
| T2 | editar | `PUT /operations/{id}` · `operations:update` | `EDITABLES = DRAFT, REGISTERED, RETURNED, REJECTED` (`:73-74`); BR-15; no contrapartida | **Ninguna** (sin `api.put('/operations…')` en `frontend/src`) | `:1172` | — | backend-only |
| T3 | submit → `PENDING_REVIEW` | `POST /operations/{id}/submit` · `operations:create` | `REENVIABLES = REGISTERED, RETURNED, REJECTED` (`:75,1314`) | `OperationDetailPage.tsx:120-141,183-191` | `:1322` | 2.ª → 400 | — |
| T4 | cancel → `CANCELLED` | `POST /operations/{id}/cancel` · `operations:create` | `∉ NO_CANCELABLES` (`:76-78`) ⇒ cancelable en `PENDING_REVIEW`/`IN_REVIEW`/`CORRECTED`; sin motivo ni rol | **Ninguna** (`operations.service.ts:47` sin llamador) | `:1350` | 2.ª → 400 | **E-21 = R-140** (`docs/12 §4` fila 13: administrador + motivo) |
| T5 | batch de revisión → `PENDING_REVIEW` | `POST /review/batches` · `review:review` | `REGISTERED`/`PENDING_REVIEW` (`review/service.py:211`) | `ReviewCenter.tsx:146` | solo `ApprovalAction` (`:234-239`) | — | **E-06** |
| T6 | start_review → `IN_REVIEW` | `POST /review/start/{id}` · `review:review` | `PENDING_REVIEW`; `FOR UPDATE` (`:89-107`) | `ReviewDetail.tsx:212-215` | `:285` | 2.ª → 400 | — |
| T7 | return → `RETURNED` | `POST /review/return` · `review:review` | `IN_REVIEW` (`:294`) | `ReviewDetail.tsx:229` | `:314` | 2.ª → 400 | — |
| T8 | complete_review (1 nivel) → `APPROVED` | `POST /review/complete` · `review:review` | `IN_REVIEW`; BR-14 (`:338`); `approval_levels ≤ 1` (`:333`) | `ReviewDetail.tsx:218-222` | `:370`, `:376-380` | 2.ª → 400 | + lote OD-25 (`:349-351`) |
| T9 | complete_review (≥2 niveles) → `CORRECTED` | ídem | `approval_levels ≥ 2` | ídem | `:370` | — | `CORRECTED` como «pendiente de aprobador» (**R-142**); `ApprovalStep` solo se leen para `require_segregation` (`:76-85`); nivel 3 sin efecto (**P1-13**) |
| T10 | corrección → `CORRECTED` | `POST /corrections` · `corrections:correct` | `REGISTERED, PENDING_REVIEW, IN_REVIEW, RETURNED, REJECTED` (`corrections/service.py:38-39`) | `CorrectionForm.tsx:52-57` | `:105` | 2.ª sobre `CORRECTED` → 400 | **E-07**: una sola corrección por ciclo; corrección sobre `REGISTERED` salta la revisión |
| T11 | approve → `APPROVED` | `POST /approvals/approve` · `approvals:approve` | `CORRECTED`/`IN_REVIEW` (`:629`); BR-14 + R-143 (`:27-67`); `FOR UPDATE` (`:627`) | `ReviewDetail.tsx:239-244`, `ApprovalPanel.tsx:54,238-240` | `:527` | 2.ª → 400 (`test_r166_02`) | — |
| T12 | reject → `REJECTED` | `POST /approvals/reject` · `approvals:reject` | ídem | `ApprovalPanel.tsx:70,242-244` | `:551-553` | 2.ª → 400 | **E-08** `previous_state` fijo |
| T13 | batch-approve / batch-reject | `POST /approvals/batch-*` · **`review:review`** (`review/router.py:143-160`) | por evento | `ApprovalPanel.tsx:100,119,173-183` | por evento | — | **E-09**: permiso más débil que el unitario; «Supervisor Avícola» (`alembic/versions/l2m3n4o5p6q7:54-60`) aprueba en lote sin `approvals:approve` |
| T14 | reverso: solicitud | `POST /reversals` · `reversals:create` | original `APPROVED` no consolidado; elegible; sin contrapartida activa | **Ninguna** (`grep -ril reversal frontend/src` → 0) | `:156-161` | 2.ª → 409 | backend-only; contrapartida nace en `PENDING_REVIEW` sin fila de transición (E-06) |
| T15 | reverso: aplicación → `REVERSED` ×2 | dentro de T8/T11 (`efectuar_reverso_si_procede` `:181-219`) | original sigue `APPROVED`; saldos ≥ 0 | — | `:218` | una contrapartida efectiva | CONFIRMED_RUNTIME (local H8) |
| T16 | consolidate → `CONSOLIDATED` | `POST /sap/consolidate` · `sap:send_sap` | `APPROVED` (`sap/service.py:158-160`) | `SapManagerPage.tsx:53,135` | solo listener | 2.ª → `[]` | GAP-14 (sin bloqueo) |
| T17 | export → `SENT_TO_SAP` | `POST /sap/export` · `sap:send_sap` | `CONSOLIDATED`; solo si `adapter.delivers_to_sap` (`:350-360`) | `SapManagerPage.tsx:62,139` | `EXPORT` (`:387-390`); transición no auditada (`update()`) | clave | con `SAP_ADAPTER=manual` (`config.py:131`) nunca se alcanza |
| T18 | retry → `SAP_CONFIRMED` | `POST /sap/retry` · `sap:send_sap` | payload `FAILED`, `retry_count < 3` | **Ninguna** | **Ninguna** | backoff | salta `SENT_TO_SAP` (`:446-450`) — E-25 |
| T19 | → `SAP_ERROR` | **sin productor** | — | — | — | — | R-157 |
| T20 | classify / reclassify | `POST /operations/{id}/classify` · `masters:update`; `/reclassify` · `corrections:correct` | pendiente / clasificado | **Ninguna** | `classification.py:201,327` | — | backend-only |

**Estados inmutables**: `APPROVED`/`CONSOLIDATED`/`SENT_TO_SAP`/`SAP_CONFIRMED`/`SAP_ERROR`/`REVERSED` no se editan (T2), corrigen (T10) ni cancelan (T4); `validate_sap_edit_lock` (`validators.py:701-709`); contrapartida no editable (`service.py:1141-1144`, `corrections/service.py:33-36`). Confirmado en runtime local: `REVERSED` → cancel 400.

**Transiciones sin camino de usuario** (§34: «No transition may exist only in backend if users need to trigger it»): T2 (PUT), T4 (cancel), T14 (reverso), T18 (retry SAP), T20 (classify/reclassify), `POST /sap/references/import`, `POST /lots/activate-manual` (`grep activate-manual frontend/src/pages` → 0), `approval-steps`. **Sin productor**: `DRAFT`, `SAP_ERROR`, `LotStatus.CANCELLED` (R-154, `BACKLOG:1084`), `AuditAction.LOGOUT`. **UI sin backend**: ninguna; anomalía `ReportsPage.tsx:193` enlaza a `/reports/lot/2` (lote fijo).

`LotStatus` (`masters/models.py:47-50`): crear → `ACTIVE` (`lots/router.py:39-46`; auto OD-25); `ACTIVE → CLOSED` (`:80-92`, UI `LotDetailPage.tsx:185-193`, **sin auditoría** E-10); reapertura no existe (`LotUpdate` excluye `status`, `lots/schemas.py:50-63`, R-51); `CANCELLED` sin productor; activación manual y fases sin UI ni auditoría.

### 2.9 KPI / reportes: fórmulas y alcance — **FAIL** (no SAP-bound)

Autorización común `reports:read` (`reports/router.py:15-156`); alcance por lote `_exigir_lote` → 404 (`reports/service.py:37-62`); dashboard `dashboard:read` con `_lotes()` (`dashboard/service.py:17-36`).

| Endpoint | Fórmula (líneas) | Filtro de estado | Hueco |
|---|---|---|---|
| `/kpis/mortality` | `total_deaths / (OB.♂+OB.♀) × 100` (`:140-153`) | aprobados (`:84-87`), excluye `SAP_ERROR` (documentado) | **R-132** presente (denominador solo `OpeningBalance` → 0 % en lotes activados por recepción) |
| `/kpis/feed-conversion` | **`FCR = total_feed_kg / 1000`** (`:161`) | aprobados | **R-131** presente |
| `/kpis/egg-production` | `hen_day = total_eggs / (OB.♀ × 30) × 100` (`:172`); fertilidad (`:185-189`) | aprobados; **suma `EGG_COLLECTION` + `EGG_CLASSIFICATION`** (`:115`) | **E-05** doble conteo; R-141 (×30) |
| `/kpis/hatchery` (lote opcional) | nacimiento/eclosión/rendimiento (`:191-246`) | `_aprobados` (`:255-260`) | **E-23 = GAP-07** sin `lotes_alcanzables` cuando `lot_id is None` |
| `/kpis/animal-welfare` (G-01) | heurística `ILIKE '%salud%'` (`:439-465`) | **sin filtro** | R-141; E-24 |
| `/kpis/vaccination-efficiency` (G-02) | `count(eventos)/(nacidos/1000)×100` (`:490-504`) | eventos sin filtro | **R-133** presente |
| `/kpis/transfer-efficiency` (G-03) | `despachados / nacidos × 100` (`:512-543`) | aprobados | — |
| `/kpis/afcr` (G-04) | `feed_kg / (Σ quantity(WEIGHT_RECORDING, BIRD_EXIT)/1000)` (`:554-566`) | peso sin filtro | **R-134** presente; E-24 |
| `/kpis/production-index` (G-05) | `(avg_weight_g × viabilidad)/(age_days × FCR × 10)` (`:611`); `avg_weight` de todos los `bird_movements.avg_weight` (`:587-595`); `age_days = hoy − start_date` (`:605`) | **sin filtro** | E-24; sin consumidor frontend |
| `/kpi/ipe/{lot}` (G-06) | `(viab% × ADG)/(FCR × 10)` sin `×100` (`:626-681`, `:668-670`); bandas `>300 / 250-300 / 200-250` (`:680`) | peso **sin filtro** (`:641-648`) | **OD-22 conforme en escala** (`GA_GOV_02_OWNER_DECISION_PACKET.md:11-12,50`; `tests/test_r187_ipe_od22_scale.py:347-356`; `LotDetailPage.tsx:396-397`). Entradas viciadas por R-131 (`:664-665`) y R-132 (`:638-639`): correcto en escala, no en valor. E-24 |
| `/kpi/weight-uniformity/{lot}` (G-07) | `CV% = stddev/avg × 100` (`:687-743`) | sin filtro (`:696-710`) | E-24 |
| `/lot/{lot}` | conteos por tipo/estado, apertura, fases (`:314-373`) | todos | — |
| `/sap-comparison` | matched = `SAP_CONFIRMED/SENT_TO_SAP`, pending = `APPROVED` (`:379-409`) | por definición | superficie `CONTRATO` (`BU-D04`) |
| `GET /dashboard/admin` | `by_status`, pendientes, 7 días, `lots_by_type`, `mortality_trend`, `active_alerts` (`:87-152`) | `mortality_trend` sin filtro (`:185-200`); `active_alerts` sin `_ambito` (`:212-227`) | R-132; **E-22 = GAP-08** |

Estado de la ola C (pausada por decisión del propietario, `BACKLOG:923-933`): **R-131, R-132, R-133, R-134, R-141 presentes** en código; R-184/R-186/R-187 cerrados (`:602-605`, `:656-660`, `:668-670`). Exportaciones 100 % cliente (`frontend/utils/export.ts:10-66`); IPE, uniformidad, AFCR, incubadora, vacunación y traslado no se exportan; sin auditoría (E-16).

**No bloquea SAP**: los KPI no son dato SAP-bound (§60 «incorrect business data toward SAP» no aplica); la corrección está gobernada por la decisión de pausa de la ola C. Los huecos de alcance E-22/E-23 sí se tratan como bloqueantes por regla §23 en el documento de seguridad.

### 2.10 Base de datos y migraciones — **PARTIAL**

| Control | Veredicto | Evidencia | Notas |
|---|---|---|---|
| Cadena de migraciones: 38 revisiones, **una sola cabeza** `y5z6a7b8c9d0` | PASS | `ls alembic/versions | wc -l` = 38; grafo `down_revision` sin bifurcación; `alembic heads` → `y5z6a7b8c9d0 (head)` (`y5z6a7b8c9d0_seed_business_unit_catalog.py`) | — |
| Ejecución de migraciones en arranque | PASS | `backend/docker-entrypoint.sh:34` `alembic upgrade head` bajo `set -e` (si falla, el contenedor no sirve, `:28-33`); `backend/Dockerfile:61-62` (`ENTRYPOINT` + `CMD uvicorn`) | `GA-REM-024`; runtime `ga-fe-02-b` F1: la migración `y5z6a7b8c9d0` corrió por pipeline normal |
| Guardas de cabeza en tests | PARTIAL | dinámicas (correctas): `tests/test_clean_baseline.py:53` (una sola cabeza), `tests/test_smoke.py:132-143` (`alembic_version == head`), `tests/test_runtime_startup.py:42-46`, `tests/test_upgrade_path.py:199-208`; **obsoletas**: `tests/test_population_invariant.py:398` y `tests/test_company_catalog.py:259-266` afirman `["x4y5z6a7b8c9"]` | 2 de los 25 rojos |
| Deriva modelo ↔ esquema | UNKNOWN | no existe test de `compare_metadata`/autogenerate (grep en `tests/`: vacío); `test_humo_10` compara solo `alembic_version` | recomendación: test de deriva |
| `lots.company_id` nulable | **PARTIAL** | `masters/models.py:283` `nullable=True`; solo índice (`alembic/versions/4982c3092c14:37`); sin migración `NOT NULL`; `count(*) WHERE company_id IS NULL` **no ejecutado** en el entorno certificable | **EXISTING `R-164`** (`BACKLOG:1071`, `BLOCKED_RUNTIME`). Condicional: bloquea si existen filas `NULL` (lotes huérfanos invisibles a todo filtro de empresa) |
| Inventario de unicidades declaradas (`backend/app/*/models.py`) | — | `masters/models.py:61` `companies.name`; `:219` `(genetic_line_id, version_label)`; `:242` `(curve_id, age_days)`; `:294` `lots.lot_code` (**global**); `lots/models.py:45` `opening_balances.lot_id`; `auth/models.py:18-19` `users.email`, `users.username` (**globales**); `business_units/models.py:41` `business_units.code`, `:67` `uq_company_business_unit`, `:121-122` índice único parcial (`revoked_at IS NULL`); `operations/models.py:101` `operational_events.idempotency_key` (**global**); `sap/models.py:143-144` `sap_payloads.idempotency_key`, `external_transaction_id` | Unicidades globales consultadas por empresa → oráculo entre inquilinos (GAP-15, P3) |
| Unicidades ausentes | PARTIAL | sin unicidad para `farms.code`, `houses(farm_id, name)`, `sap_references(company_id, ref_type, sap_code)`, `egg_batches/chick_batches(dispatch_event_id)` («exactamente uno» solo en aplicación, `operations/service.py:477-496,523-541`) | P3; `sap_references` relevante para la fase SAP (import duplicado de OC) |
| FKs y tenencia | PASS con notas | FKs declaradas en modelos; `audit_logs.company_id NOT NULL` + listener `company_id or 0` (FK inexistente → `IntegrityError` si dispara sin empresa; hoy inalcanzable por `OD-14.d`) | R-83 |
| Enums | PASS con notas | `EventStatus` incluye `DRAFT`, `SAP_ERROR` sin productor; `LotStatus.CANCELLED` sin productor; `AuditAction.LOGOUT/SENT_TO_SAP/SAP_CONFIRMED/SAP_ERROR` nunca escritos; `AuditModule.REPORTS` sin uso | valores muertos, no deriva |
| Inmutabilidad de `audit_logs` en BD | FAIL (registrado) | sin trigger/`REVOKE` (`ee30bd1aa374_add_audit_log.py`) | R-148 |
| Bloqueo consultivo del consecutivo de lote | PASS | `lots/service.py:100-108` (`pg_advisory_xact_lock`; solo PostgreSQL `:106`) | — |

### 2.11 Semántica de cierre de lote — **FAIL**

| Control | Veredicto | Código | Tests | Runtime |
|---|---|---|---|---|
| Precondiciones: activo; BR-05 (pesaje + alimento); R7 (sin registros no aprobados) | PASS | `lots/service.py:445-449`, `:456` → `validators.py:362-390`, `:465` → `validators.py:409-455` | `tests/test_lot_close_approval.py` (R7, `BLOQUEAN`/`NO_BLOQUEAN` `:33-43`) | local: 400 «10 en «registered»» / «10 en «pending_review»»; 400 «sin al menos un registro de pesaje» |
| **E-02** · `REVERSED` bloquea el cierre para siempre | **FAIL (P1)** · CONFIRMED_IN_CODE | `validators.py:400-406` (`ESTADOS_APROBADOS` sin `REVERSED`), `:436-438` (`not_in((*ESTADOS_APROBADOS, CANCELLED))`); `operations/service.py:76-78` (`REVERSED ∈ NO_CANCELABLES`); OD-19 declara `REVERSED` terminal | `tests/test_lot_close_approval.py:33-43` (`BLOQUEAN`/`NO_BLOQUEAN` sin `REVERSED`) | H8: reverso efectivo confirmado (original y contrapartida `reversed`), cancelación 400, cierre bloqueado antes por BR-05 (lote sin pesaje). Evidencia runtime local: ver evidence/ui-e2e-local-pass2.json (H8b) |
| **E-03** · resumen de cierre cuenta anulados | **FAIL (P2)** · CONFIRMED_IN_CODE | `lots/service.py:469-498` (`total_mortality`, `total_feed_kg`, `total_eggs` sin filtro de estado); `approved_events` (`:507-516`, `status.in_([APPROVED, CONSOLIDATED, SENT_TO_SAP, SAP_CONFIRMED])`) excluye `SAP_ERROR`/`REVERSED`; UI `LotDetailPage.tsx:199-209` | — | parcial en **R-144** (`BACKLOG:936`: «sin FCR ni peso final»), que no cubre el filtro de estado |
| **E-10** · cierre sin auditoría | **FAIL (P2)** | `lots/service.py:438-549` | — | — |
| Reapertura | n/a (no existe; R-51) | `lots/schemas.py:50-63` | `tests/test_security_regression.py::test_r51_*` | — |
| Evento `lot_closure` no cierra el lote | nota | `operations/service.py:967-970` | — | dos caminos con el mismo nombre y distinto efecto (UX) |

---

## 3. Tabla consolidada de hallazgos de dominio E-01 … E-25

| ID | Área | Descripción | Sev. | Evidencia | Estado | Registro (dedup) | ¿Bloquea SAP? | Razonamiento |
|---|---|---|---|---|---|---|---|---|
| **E-01** | Ledger / BR-18 | Tras un reverso efectivo de `bird_reception`, `validate_oc_limit` cuenta original **y** contrapartida (ambos `REVERSED`, misma `sap_document_ref`) ⇒ acumulado contra la OC = 2n; entregas legítimas rechazadas. | **P2** | `validators.py:769-783`; `reversals/service.py:126-134,215-216` | CONFIRMED_IN_CODE | **NUEVO** (grep BR-18/reverso en backlog → 0; vecinos OD-19 §5, R-176) | **SÍ** | §60 «reversal consistency»: el consumo de OC (documento SAP) queda incorrecto tras la única vía de corrección de un aprobado. Corrección: aplicar la semántica de `_suma_neta` o excluir `REVERSED` + contrapartidas. |
| **E-02** | Cierre / R7 | `REVERSED` tratado como «sin aprobar»; terminal y no cancelable ⇒ un lote con cualquier reverso efectivo **no puede cerrarse nunca**. | **P1** | `validators.py:400-406,436-438`; `operations/service.py:76-78`; `tests/test_lot_close_approval.py:33-43` | CONFIRMED_IN_CODE (H8b en curso) | **NUEVO** (R-76 cerrado no lo contempla; OD-19 §1) | **SÍ** | Bloqueo funcional irreversible: reverso y cierre son mutuamente excluyentes. Corrección: añadir `REVERSED` al conjunto excluido en `validate_lot_records_approved` + test. |
| **E-03** | Cierre / resumen | `close_lot` suma mortalidad, alimento y huevos sin filtro de estado (incluye `CANCELLED`, `REVERSED` + contrapartida). | P2 | `lots/service.py:469-517`; `LotDetailPage.tsx:199-209` | CONFIRMED_IN_CODE | Parcial: **R-144** (`BACKLOG:936`) no cubre el filtro de estado | NO (recomendado) | Resumen a UI, no a SAP; corregir junto a R-144. |
| E-04 | BR-17 | Capacidad de galpón validada por evento, no acumulada; sin ledger por galpón. | P3 | `validators.py:712-725`; `service.py:900-902` | CONFIRMED_IN_CODE | Parcial: **R-176** (`BACKLOG:1294`, «capacidad estática») | NO | Decisión de dominio (RR-02). |
| E-05 | KPI huevos | `_sum_egg_quantity` suma `EGG_COLLECTION` + `EGG_CLASSIFICATION` ⇒ doble conteo en `total_eggs`/hen-day. | P2 | `reports/service.py:108-122` | CONFIRMED_IN_CODE | NUEVO (familia **R-141**, ola C pausada) | NO | KPI no SAP-bound; ola C pausada por el propietario. |
| E-06 | Estado / SLA | `create_review_batch` cambia a `PENDING_REVIEW` con `update()` sin `audit_state_transition`; contrapartida de reverso nace en `PENDING_REVIEW` sin transición ⇒ SLA 24 h ciego; transición no auditada. | P2 | `review/service.py:206-243`; `reversals/service.py:131`; `sla.py:44-60` | CONFIRMED_IN_CODE | NUEVO | NO (recomendado) | Aviso y auditoría; no altera dato SAP. |
| E-07 | Estado / correcciones | `CORRECTED ∉ correctable` ⇒ una sola corrección por ciclo; corrección sobre `REGISTERED` salta la revisión. | P2 | `corrections/service.py:38-44,99` | CONFIRMED_IN_CODE | Parcial: **R-142**, P1-13 | NO (recomendado) | Flujo; resolver con R-142/GA-REM-019. |
| E-08 | Auditoría | `reject` escribe `previous_state="corrected"` fijo aunque venga de `IN_REVIEW`. | P3 | `review/service.py:551-553,629` | CONFIRMED_IN_CODE | NUEVO | NO | — |
| **E-09** | Permisos / estado | `batch-approve`/`batch-reject` exigen `review:review`; unitarias `approvals:approve/reject`; «Supervisor Avícola» aprueba en lote. | **P2** | `review/router.py:123-160`; `ApprovalPanel.tsx:100,119,173`; semilla `l2m3n4o5p6q7:54-74` | CONFIRMED_IN_CODE | **NUEVO** (grep batch-approve → 0) | **SÍ** | §60 «approval consistency»: `APPROVED` es el estado de entrada al camino SAP y puede alcanzarse sin el permiso designado. Corrección: `require_permission("approvals","approve"/"reject")` en las rutas de lote + gate UI. |
| **E-10** | Auditoría / lotes | `close_lot`, `activate_manual`, `add_phase` sin auditoría (cierre cambia `status`/`end_date`; activación fija el saldo de apertura). | **P2** | `lots/service.py:438-549,555-659,685-697`; `tests/test_opening_balance.py:363-388` | CONFIRMED_IN_CODE | NUEVO (GA-REM-032 AC02 cubre solo `MasterService`) | NO (recomendado pre-SAP) | Dato crítico del ledger sin rastro; no altera el dato en sí. |
| **E-11** | Auditoría | Listener `after_flush` **y** helpers activos en runtime real ⇒ filas duplicadas/triplicadas y acciones incorrectas (`created` en submit, `corrected` en aprobación); tests ciegos (`ASGITransport` sin `lifespan`). | **P1** (P1-12) | `main.py:41-42`; `listeners.py:43-64,71-113`; `helpers.py`; `conftest.py:117-140`; `tests/test_edit_cancel_balance.py:393`; `review/service.py:363` | **CONFIRMED_RUNTIME** (local H6/H8: 13 filas / 5 acciones) | **EXISTING: P1-12** «auditoría duplicada e incompleta» (`BACKLOG:98`, asignada a GA-REM-003 AC06 + GA-REM-019; AC06 es solo autenticación; sin evidencia de cierre de la parte «duplicada») | **SÍ** | §37/§60 «auditability»: la pista no es fiable por conteo ni por acción; P1 registrado y abierto. Corrección: un solo productor (retirar el listener o los helpers) + test con `lifespan`. |
| E-12 | Auditoría / maestros | Curvas de peso (crear versión, activar) sin auditoría. | P3 | `masters/curves.py:90,143` | CONFIRMED_IN_CODE | NUEVO | NO | — |
| **E-13** | Auditoría / usuarios | Alta, edición (incl. cambio de rol) y baja de usuarios sin auditoría. | **P2** | `auth/service.py:337-382,384-421,491-506` | CONFIRMED_IN_CODE | Parcial: P1-12 «incompleta»; GA-REM-032 no lo incluyó | NO (recomendado pre-SAP) | Seguridad + `docs/02 §3.11.1`; agrava GAP-01 (la fabricación del rol se audita, la asignación al usuario no). |
| E-14 | Auditoría / auth | Sin `POST /logout`; `LOGOUT` nunca se escribe pese a GA-REM-032 AC01. | P3 (P2 si se exige revocación) | `auth/router.py` | CONFIRMED_IN_CODE | **EXISTING: P1-4** (`BACKLOG:90`) = GAP-09 | (ver GAP-09) | — |
| E-15 | Auditoría / evidencias | Subida y borrado físico sin auditoría. | P3 | `operations/service.py:1363-1414` | CONFIRMED_IN_CODE | NUEVO (= GAP-12) | NO | — |
| E-16 | Auditoría / reportes | Exportación Excel/PDF 100 % cliente sin rastro; `AuditModule.REPORTS` sin uso; GA-REM-032 AC04 incumplido. | P3 | `frontend/utils/export.ts`; `audit/models.py:61` | CONFIRMED_IN_CODE | NUEVO | NO | — |
| E-17 | Auditoría / consulta | `AuditPage` envía solo `action/module/date_from/date_to`; `sap_reference_id`, `ip_address`, `user_agent`, `is_sensitive` nunca se rellenan. | P3 | `AuditPage.tsx:61-72`; `audit/helpers.py`; `audit/models.py:93-96` | CONFIRMED_IN_CODE | Parcial: GA-REM-032 AC09/AC11 (filtros backend) | NO | — |
| E-18 | Maestros / UI | Selectores con `limit=100` sin paginación ni búsqueda; catálogos > 100 truncados. | P3 | `OperationFormPage.tsx:343-368`; `masters/router.py:33` | CONFIRMED_IN_CODE | NUEVO | NO | — |
| E-19 | Notificaciones / UI | `NotificationType` TS omite `lot_near_close`; `destino()` no navega para `lot`/`sap_payload`; `detalle()` para 2 de 6 tipos. | P3 | `notifications.ts:11-20,58-63`; `NotificationBell.tsx:107-112` | CONFIRMED_IN_CODE | NUEVO | NO | — |
| E-20 | Ledger / observabilidad | Sin endpoint ni pantalla del saldo vivo; la UI muestra `initial_population`. El operador no conoce el saldo contra el que BR-01 rechaza. | P2 | `validators.py:49-88`; `LotDetailPage.tsx:52-58,358-362`; `reports/service.py:143-144` | **CONFIRMED_RUNTIME** (`lotdetail-poblacion-visible: false`) | Parcial: **R-132** (`BACKLOG:924`) | NO (recomendado) | UX de dominio; el ledger es correcto. |
| E-21 | Estado / cancelación | `cancel_event` en `PENDING_REVIEW`/`IN_REVIEW`/`CORRECTED` por cualquier `operations:create`, sin motivo ni rol, sin UI; `docs/12 §4` fila 13 exige administrador + motivo. | P2 | `operations/service.py:76-78,1325-1351`; `router.py:320-327` | CONFIRMED_IN_CODE | **EXISTING: R-140** (`BACKLOG:932`, PARTIAL: sí bloquea `SAP_CONFIRMED/SAP_ERROR`) | NO (recomendado) | Registrado; no altera saldo (la fila deja de contar) ni dato SAP (no cancelable tras aprobación). |
| E-22 | Dashboard / alcance | `_get_active_alerts` calcula `_ambito` y no lo aplica. | P2 (P1 por §23) | `dashboard/service.py:206-231` | CONFIRMED_IN_CODE; UNKNOWN_RUNTIME | NUEVO (= **GAP-08**) | (ver GAP-08) | Tratado en seguridad. |
| E-23 | KPI / alcance | `/reports/kpis/hatchery` sin `lot_id` agrega toda la empresa; `_filtro_de_lotes` sin uso. | P2 (P1 por §23) | `reports/service.py:64-70,191-246` | CONFIRMED_IN_CODE; UNKNOWN_RUNTIME | NUEVO (= **GAP-07**) | (ver GAP-07) | Tratado en seguridad. |
| E-24 | KPI / estado | IPE, uniformidad, G-05, AFCR (peso) y bienestar sin filtro de estado; G-05 promedia pesos de cualquier tipo. | P2 | `reports/service.py:587-595,641-648,696-710,554-563,442-453` | CONFIRMED_IN_CODE | Parcial: **R-131/R-134/R-141** (ola C pausada) no nombran el filtro de estado | NO | KPI no SAP-bound. |
| **E-25** | Estado / SAP | `retry_failed` → `SAP_CONFIRMED` saltando `SENT_TO_SAP` y sin auditoría; `SENT_TO_SAP`/`SAP_CONFIRMED` nunca auditados; `SAP_ERROR` sin productor; nivel 3 de aprobación sin efecto. | P2 (P1 SAP) | `sap/service.py:353-360,446-450`; `review/service.py:333-355` | CONFIRMED_IN_CODE | **EXISTING: R-157** (`BACKLOG:949`, P1 D), P1-13, R-142 | **SÍ (fase SAP)** | Es el trabajo pendiente de `GA-REM-017`; la máquina de estados SAP no está completa. |

---

## 4. Deduplicación contra el backlog

| Referencia | Fila del backlog | Estado verificado | Relación |
|---|---|---|---|
| P1-12 «auditoría duplicada e incompleta» | `BACKLOG:98` | **abierto y confirmado en runtime** | E-11 (duplicada), E-10/E-13 (incompleta) |
| P1-4 «sin logout ni revocación» | `BACKLOG:90` | abierto | E-14 = GAP-09 |
| P1-13 «aprobación multinivel no operativa» | `BACKLOG:99` | abierto | E-25, E-07 |
| R-140 | `BACKLOG:932` | PARTIAL (bloquea `SAP_CONFIRMED/SAP_ERROR`; sin motivo/rol) | E-21 |
| R-142 | `BACKLOG:934` | abierto | E-07 |
| R-144 | `BACKLOG:936` | abierto (no cubre filtro de estado) | E-03 |
| R-132 | `BACKLOG:924` | presente (`reports/service.py:143-146`; `dashboard/service.py:185-200`) | E-20, E-24 |
| R-131 / R-133 / R-134 / R-141 | `BACKLOG:923,925,926,933` | presentes (`reports/service.py:161`, `:490-499`, `:554-566`, `:172,:445-457,:229,:667`) | E-05, E-24 |
| R-176 | `BACKLOG:1294` | abierto (P3) | E-04 |
| R-157 | `BACKLOG:949` | abierto (P1 SAP) | E-25 |
| R-146 | `BACKLOG:938` | **implementada en código**; fila aún como hallazgo | §2.4 (verificar cierre) |
| R-161 | `BACKLOG:1001,1267` | cerrada en código; texto «OPEN» residual | §2.2 |
| R-164 | `BACKLOG:1071` | abierto, `BLOCKED_RUNTIME` | §2.10 |
| R-148 | `BACKLOG:940` | abierto | §2.7.3 (= GAP-13) |
| R-83 | `BACKLOG:275` | abierto | §2.7.3 (= GAP-10) |
| R-50 | **ausente** del backlog (`UPDATE_SCHEMA_SECURITY_MATRIX.md:59,105`) | abierto | §2.6 (= GAP-05) |
| R-185 / OD-21 | `BACKLOG:1831-1864` CLOSED_OWNER_ACCEPTED | alcance solo Área→Lote confirmado | §2.6 |
| OD-22 / R-187 | `GA_GOV_02_OWNER_DECISION_PACKET.md` | conforme en escala | §2.9 |
| OD-25 | `GA_OD_25_…DECISION.md` | lote automático con población cero verificado | §2.1.2 |

---

## 5. Veredicto de compuerta de integridad de datos: **FAIL**

Regla aplicada (§60): «population integrity · balance integrity · foreign-reference integrity · approval consistency · transaction atomicity · no duplicate event · idempotency · concurrency safety · auditability · reversal consistency. Any known defect that can send incorrect business data toward SAP: NO-GO.» Y §38: «A critical transaction with known duplicate/split-state risk is NO-GO SAP.»

| Requisito §60 | Veredicto | Sustento |
|---|---|---|
| Integridad de población | PASS (invariante) / FAIL (consumidores) | §2.1 |
| Integridad de saldos | PASS | §2.2 |
| Integridad de referencias foráneas | FAIL | GAP-06, GAP-05 (condicional), R-164 (condicional) |
| Consistencia de aprobación | FAIL | E-09 |
| Atomicidad | PASS | §2.3 |
| Sin evento duplicado | PASS (operaciones) / FAIL (fase SAP) | `idempotency_key`; GAP-14 |
| Idempotencia | PARTIAL | §2.4 |
| Seguridad de concurrencia | PASS | §2.5 |
| Auditabilidad | FAIL | E-11 (P1-12), E-10, E-13, R-148 |
| Consistencia de reverso | FAIL | E-01, E-02 |

### 5.1 Bloqueantes

| Orden | ID | Sev. | Por qué bloquea | Esfuerzo estimado |
|---|---|---|---|---|
| 1 | **E-02** | P1 | Lote con reverso efectivo no se puede cerrar nunca (bloqueo irreversible de la única vía de corrección de un aprobado) | Trivial: añadir `REVERSED` al conjunto excluido de `validate_lot_records_approved` + test |
| 2 | **E-11** | P1 (`P1-12`) | Auditoría duplicada y con acciones incorrectas en runtime real; registrado como P1 sin evidencia de cierre | Bajo-medio: un solo productor; test con `lifespan`; revisar aserciones «== 1» |
| 3 | **E-01** | P2 | Consumo de OC (BR-18) incorrecto tras reverso: 2n en lugar de 0; dato de documento SAP | Bajo: semántica `_suma_neta` en `validate_oc_limit` + test |
| 4 | **E-09** | P2 | `APPROVED` alcanzable en lote sin el permiso designado (consistencia de aprobación) | Trivial: permisos en `review/router.py:143-160` + gate UI |
| 5 | **GAP-06** | P2 | Referencias foráneas del lote sin verificar (documento de seguridad) | Bajo |
| 6 | **GAP-14** | P3 (fase SAP) | Duplicado de consolidación (§38) | Bajo |
| 7 | **E-25** | P1 SAP (`R-157`) | Máquina de estados SAP incompleta; trabajo de `GA-REM-017` | Fase SAP |
| Condicionales | **R-164**, **GAP-05** | P2 | R-164 bloquea si `count(*) FROM lots WHERE company_id IS NULL > 0` en el entorno certificable (pendiente de ejecutar); GAP-05 bloquea si se delega `masters:*` antes de corregirlo | Medio (migración `NOT NULL` + decisión sobre filas) / Bajo |

### 5.2 No bloqueantes (recomendados antes de SAP)

E-03 (resumen de cierre, con R-144), E-06 (SLA/auditoría de batch y contrapartida), E-07 (corrección única, con R-142), E-10 (auditoría de cierre/activación/fases), E-13 (auditoría de usuarios), E-20 (saldo visible), E-21 (R-140), R-148/GAP-13 (trigger de inmutabilidad), R-83/GAP-10, E-08, E-12, E-15, E-16, E-17, E-18, E-19, E-04. KPI (E-05, E-24, R-131/132/133/134/141): sujetos a la decisión de reanudar la ola C.

### 5.3 Condiciones de re-evaluación

1. Corregir E-02, E-01, E-09 con tests RED→GREEN dirigidos (ninguno de los tres tiene test hoy) y cerrar el experimento H8b como evidencia de runtime de E-02.
2. Resolver E-11 con un único productor de auditoría y una suite que ejecute `lifespan` (o registre el listener explícitamente) para que la duplicación sea detectable; recontar aserciones «exactamente 1».
3. Ejecutar `count(*) FROM lots WHERE company_id IS NULL` en el entorno certificable (R-164) y decidir migración `NOT NULL`.
4. Cerrar documentalmente R-146 y R-161 en el backlog; reincorporar R-50.
5. Suite verde en HEAD (25 rojos: 17 aserciones OD-16, 5 fixture `.test`, 3 guardas) y ejecución en CI sobre `push` a `main`.

---

## Anexo — Maestros y notificaciones (§35, §3.14): conforme al alcance documentado

- **Maestros**: 20 entidades (no 22) declaradas en `frontend/App.tsx:135-162` y registradas con `register_crud` (`masters/router.py:104-125`) + 4 rutas de curvas (`:183-242`); `DELETE` = baja lógica (`masters/service.py:261-266`, audit `DELETED`); tenencia: `company_id` no nulo en `Farm`/`Hatchery`, derivado por padre en `House`/`Incubator`/`Hatcher`/`GeneticWeightCurve`, nulable (= compartido) en 12 catálogos, plataforma sin `company_id` en `Breed`/`ProductivePhase` (`masters/models.py:79-438`); OD-21 solo Área→Lote (§2.6).
- **Notificaciones**: 6 tipos producidos (`record_rejected` `review/service.py:565-590`; `sap_send_failed` `sap/service.py:464-525`; `mortality_over_threshold`/`weight_out_of_standard` `operations/service.py:643-694`; `review_pending_24h` `sla.py:63-102`; `lot_near_close` `sla.py:126-200`); destinatarios OD-08 (`recipients.py:101-147`); tarea SLA cada 3600 s (`sla.py:225-256`, `config.py:103-104`, `main.py:47-52`); aislamiento por destinatario y empresa (`notifications/service.py:124-134`); tests `tests/test_notifications.py:159-507`. Hueco funcional: E-06 (batch y contrapartida invisibles al SLA); menores E-19.

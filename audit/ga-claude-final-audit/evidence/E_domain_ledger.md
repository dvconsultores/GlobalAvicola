# E · Auditoría de dominio — ledger de población, máquina de estados, auditoría, KPI, maestros y notificaciones

Repositorio: `/home/maria/Proyectos/GlobalAvicola` · HEAD `c0b4afc` (GA-F01 C3) · fecha 2026-09-13 · modo **solo lectura** (sin tests, sin builds, sin git).
Rutas citadas como `fichero:línea` relativas a la raíz del repo (`backend/app/...`, `frontend/src/...`, `backend/tests/...`).

Fuentes canónicas consultadas: `specs/global-avicola/spec.md:287-302` (BR-01…BR-16), `docs/02-functional-spec.md` (§3.11 :432-463, §3.12.1 :466-480, §3.14 :510-519), `docs/12-approval-workflow.md` (§4 :57-73, §6 :134-147), `specs/remediation/OD-17-…md`, `specs/remediation/OD-19-…md`, `audit/ga-gov-02/GA_GOV_02_OWNER_DECISION_PACKET.md` (OD-22), `audit/ga-r153/GA_OD_25_GRANDPARENT_LOT_ON_APPROVAL_DECISION.md` (OD-25), `audit/remediation/REMEDIATION_BACKLOG.md` (dedup).

---

## 1 · LEDGER DE POBLACIÓN Y SALDOS

### 1.1 Función canónica del saldo de aves y filtro de estado

| Aspecto | Evidencia |
|---|---|
| Función | `get_current_bird_balance(db, lot_id)` — `backend/app/operations/validators.py:49-88` |
| Fórmula | `apertura + Σ entradas − Σ salidas` (:52-57). Apertura = `OpeningBalance.initial_male_count + initial_female_count` (:79-88). Entradas = `BIRD_RECEPTION`, `BIRTH_REGISTRATION` (:70). Salidas = `MORTALITY_RECORDING`, `CULL_RECORDING`, `BIRD_EXIT`, `CHICK_DISPATCH` (:71-76). Neutros = `BIRD_TRANSFER`, `BIRD_DISTRIBUTION` (RR-02, :57). Los acumulados históricos del `OpeningBalance` **no** se restan (RR-08, :65-68). |
| Filtro de estado | `_suma_neta` (:21-46): cuentan **todos los estados salvo `CANCELLED`** (:39) — `registered`, `pending_review`, `in_review`, `returned`, `corrected`, `rejected`, `approved`, SAP… **La aprobación no es requisito para contar en el saldo** (decisión documentada en :744-748 para BR-18: «un control de recepción no puede esperar a la aprobación»). Las contrapartidas de reverso (`Reversal.reversal_event_id`) se excluyen del natural (:40) y se restan sólo si `status == REVERSED` (:42-45). |
| Cantidad sumada | `bird_movements.quantity` (sin discriminar sexo; `sex` es atributo, :77-78). `chicks_healthy/weak`, `dead_on_arrival`, `received_total`, `rejected_on_arrival` **no** afectan al saldo (son atributos: `models.py:129-137`; RR-12 en :536-574). |
| Sin filtro de empresa | La función suma por `lot_id` sin `company_id` (mitigado por `validate_lot_active(..., company_id)` en el alta, :501-529, y por `verificar_pertenencia` en edición/corrección). |
| Endpoint | **No existe** endpoint que exponga `get_current_bird_balance` (`grep` en `backend/app/**/router.py` y `schemas.py`: sin coincidencias). El saldo sólo es observable a través de los rechazos BR-01/BR-04 y de la alerta de mortalidad (`operations/service.py:559-562`). |
| UI | `frontend/src/pages/lots/LotDetailPage.tsx:52-58` carga `/reports/kpis?lot_id`, `/operations?lot_id`, `/lots/{id}/phases`, `/reports/kpi/ipe/{id}`, `/reports/kpi/weight-uniformity/{id}`, `/operations/alerts`. **No muestra el saldo vivo**; el único «población» visible es `initial_population` del KPI de mortalidad (:358-362 → `reports/service.py:143-144`, que es sólo `OpeningBalance`). ⇒ el número de la UI **no** es el del ledger. |

Otros saldos (mismo fichero):

| Saldo | Función | IN | OUT | Filtro | Bloqueo de fila |
|---|---|---|---|---|---|
| Huevo fértil en granja (BR-02) | `get_egg_balance` :117-146 | `EGG_COLLECTION` filas `egg_type == 'fertile'` (:130-133) | `EGG_DISPATCH` fértil (:140-143) | `≠ CANCELLED` — **no usa `_suma_neta`** (sin tratamiento de contrapartidas; coherente con OD-19 §18: huevos no reversibles, `reversals/service.py:42-46,107-109`) | `validate_egg_dispatch` :239-256 → `bloquear_saldo_del_lote` (:249) — **R-161 CERRADO (técnico)** (`REMEDIATION_BACKLOG.md:1254-1267`; `tests/test_egg_incubation_concurrency.py:227-316`) |
| Huevo en incubadora (BR-03) | `get_hatchery_egg_balance` :149-175 | `EGG_RECEPTION_HATCHERY` fértil (:160-163) | `INCUBATION_LOAD.hatchery_params.quantity_loaded` (:167-173) | `≠ CANCELLED` | `validate_incubation_load` :259-274 (:267) — R-161 cerrado |
| Pollitos viables (BR-04) | `get_viable_chick_balance` :178-192 | `BIRTH_REGISTRATION` | `CHICK_DISPATCH` + `MORTALITY` + `CULL` (R-130) | `_suma_neta` (reverso incluido) | `validate_chick_dispatch` :277-288 (:281) |
| Ovoscopía / transfer_to_hatcher / clasificación | — | — | — | **Sin saldo**: no participan en ningún agregado (`ENTRADAS_DE_SALDO`/`SALIDAS_DE_SALDO` :297-300). Bloqueados para reverso por OD-19 §18. | — |

Primitiva de serialización: `bloquear_saldo_del_lote` (`SELECT … FOR UPDATE` sobre `lots.id`, :197-208); orden ascendente multi-lote en `bloquear_saldos_de_lotes` :316-323.

### 1.2 Tabla por evento / acción con efecto (o no) en la población

| Evento / acción | Disparador (ruta · permiso) | Campos de entrada | Δ saldo (signo · cantidad) | Lote afectado | Precondición | Chequeo saldo negativo | Protección doble conteo | Efecto del reverso | Auditoría |
|---|---|---|---|---|---|---|---|---|---|
| `bird_reception` | `POST /operations` · `operations:create` (`operations/router.py:70-77`) | `bird_movements[].quantity/sex`, `house_id`, `sap_document_ref`, `received_total`, `dead_on_arrival`, `rejected_on_arrival` | **+Σ quantity** (alojadas). DOA/rechazadas no restan (RR-12 `validators.py:536-565`) | `lot_id` | BR-07 lote activo y de la empresa (:501-529, `service.py:836`); BR-06 fecha (:488-498); BR-08 granja+galpón (:822-839); BR-19 periodo (:794-819); **BR-17** capacidad del galpón **por evento** (`validate_house_capacity` :712-725, llamada `service.py:900-902`); **BR-18** acumulado de OC vía `sap_references.quantity` (:728-791; `≠ CANCELLED`, sin unicidad BR-10 para recepción `service.py:890-895`); **B01** cuadre reproductoras `recibidas == alojadas + DOA + rechazadas` (:553-565) | n/a (entrada) | `idempotency_key` único (`service.py:225-234`, `models.py:101`); cancelación `≠ CANCELLED`; contrapartida excluida del natural (`_suma_neta`) | Elegible (`ELEGIBLES_CON_SALDO_DE_AVES` `reversals/service.py:33-36`); al aprobar se valida `saldo − n ≥ 0` (:198-207) | `audit_event_created` `service.py:308` |
| `bird_distribution` | ídem | `bird_movements`, `house_id` | **0** (neutro, RR-02) | `lot_id` | BR-07/08/19; BR-17 y BR-18 también se aplican (`service.py:900-906`) | n/a | — | Elegible «sin saldo» (`reversals/service.py:37-41`) | ídem |
| `bird_transfer` | ídem | `bird_movements[].source_house_id/target_house_id` | **0** — **no mueve población entre lotes ni galpones** (no hay ledger por galpón; sólo se verifica pertenencia de galpones `service.py:863-867`) | `lot_id` | BR-07/08/19 | n/a | — | Elegible «sin saldo» | ídem |
| `bird_exit` | ídem | `bird_movements`, `destination_farm_id/plant_id`, `transport_id` | **−Σ quantity** | `lot_id` (origen). No acredita al destino: éste registra su propia `bird_reception` | `validate_bird_decrement` :211-231 (cantidad > 0 y ≤ saldo) bajo `FOR UPDATE` (`service.py:939-946`) | BR-01 (R-130) | `≠ CANCELLED`; contrapartida | Elegible; al aprobar se comprueba que el saldo resultante no quede negativo | ídem |
| `mortality_recording` | ídem | `bird_movements`, `cause_id` | **−Σ quantity** | `lot_id` | `validate_mortality` :234-236 → BR-01 (`service.py:931-938`); alerta ≥3 %/8 % sobre saldo previo (:551-581, umbrales `config.py:89-90`) | BR-01 | ídem | Elegible; valida BR-01 y BR-04 (`reversals/service.py:198-214`) | ídem |
| `cull_recording` | ídem | `bird_movements`, `cull_cause_id` | **−Σ quantity** | `lot_id` | `validate_bird_decrement` (`service.py:939-946`) | BR-01 (R-130) | ídem | Elegible | ídem |
| `birth_registration` | ídem | `bird_movements` (una fila por sexo o `mixed`), `chicks_healthy/weak` | **+Σ quantity** (nacidos); sanos/débiles son atributos con `sanos+débiles ≤ nacidos` (BR-21 :577-613; R-170/B13) | `lot_id` (incubadora) | BR-21 nacidos ≥ 1; sanos/débiles obligatorios en `hatchery` | n/a | ídem | Elegible; se valida viables y aves (`reversals/service.py:208-214`) | ídem |
| `chick_dispatch` | ídem | `bird_movements`, `destination_farm_id` | **−Σ quantity** | `lot_id` (incubadora) | `validate_chick_dispatch` :277-288 (BR-04 sobre viables = nacidos − muertos − descartes − despachados; R-174 rechaza 0 `service.py:961-966`) | BR-04 + BR-01 (viables ≤ saldo) | ídem; vínculo `ChickBatch` por destino declarado (`service.py:498-517`) | Elegible | ídem |
| `grandparent_import` | ídem (lote opcional `service.py:61-68`) | `extra_data.import_plan`, `bird_movements` ♂/♀, `sap_document_ref`, `supplier_id` | **0** — documental (BR-22 :624-667; no está en `in_types`; `validate_oc_limit` sólo cuenta `BIRD_RECEPTION` :774) | ninguno (o lote legado) | BR-22 identidades del plan | n/a | — | **No elegible** (no está en ninguna lista `reversals/service.py:33-46` → «no es reversible» :110-112) | ídem + lote auto (abajo) |
| Lote auto OD-25 | `approve`/`complete_review` de la importación sin lote (`review/service.py:513-515`, `349-351`) → `crear_lote_de_importacion_si_procede` (`lots/service.py:128-196`) | plan `arrival_date`, sexos | **0** — `Lot` sin `OpeningBalance` y sin recepción (:158-168; OD-25 §2.5) | lote nuevo `L-GP-{año}-{nn}` | sólo al aprobar; lock consultivo por (empresa, año) :152 | n/a | unicidad global de `lot_code` con reintento :154-181 | — | `audit_accion CREATED` módulo `LOTS`, `new_values.origin="grandparent_import_approval"` :191-195 |
| Saldo de apertura (`activate-manual`, R-67) | `POST /lots/activate-manual` · `lots:create` (`lots/router.py:99-106`) | `initial_male/female_count`, acumulados, `activation_date`, `phase_at_activation_id` | **+ (♂+♀)** vía `OpeningBalance` (:79-88) | `lot_id` | pertenencia y unidad (`lots/service.py:573-580`); único por lote (:583-590, 409); **sin historia** de eventos no cancelados (doble conteo, :596-611); mortalidad acumulada ≤ inicial (:614-623) | n/a | conflicto 409 si ya hay eventos | no aplica | **Sin `audit_accion`** (:555-659; el test `test_t_067_10` sólo comprueba campos del `OpeningBalance`) |
| Cierre de lote (`POST /lots/{id}/close`) | `lots:create` (`lots/router.py:80-92`) | — | **0** (no toca saldos) | `lot_id` | activo (:445-449); **BR-05** pesaje + alimento (:456 → `validators.py:362-390`); **R7/R-76** sin registros no aprobados (:465 → `validators.py:409-455`) | n/a | segundo cierre → 400 | — | **Sin `audit_accion`** (:438-549) |
| Evento `lot_closure` | `POST /operations` tipo `lot_closure` | `lot_id` | **0**; **no cierra el lote** (sólo corre BR-05: `service.py:967-970`) | `lot_id` | BR-05 | — | — | no elegible para reverso | `audit_event_created` |
| `update_event` (PUT) | `PUT /operations/{id}` · `operations:update` (`router.py:295-303`) | campos de `OperationalEventUpdate` (`schemas.py:195-253`) — **sin `bird_movements`**: la cantidad es inmutable tras el alta (`tests/test_edit_cancel_balance.py:267`) | **Δ = mover el efecto entero** si cambia `lot_id` (R-173) | origen y destino | estados `EDITABLES` (`service.py:73-74`), BR-15 (:1134), no contrapartida (:1141-1144); `verificar_destino_de_edicion` :1261-1305 (reglas puras R-176 :1185-1230; sin vínculo vigente R-178 :1232-1259) | entrada: origen `≥ 0` (`validate_retiro_de_entrada` :326-344); salida: se valida en destino como alta (:347-359), bajo bloqueo de ambos lotes (:1296) | relectura bajo bloqueo (:1297-1299) | — | `audit_state_transition` con `previous_values/new_values` :1172-1173 |
| `cancel_event` | `POST /operations/{id}/cancel` · `operations:create` (`router.py:320-327`) | — (sin motivo: R-140 OPEN) | **Δ = −efecto** (la fila deja de contar) | `lot_id` | `NO_CANCELABLES` (:76-78); relectura bajo `FOR UPDATE` (:1332-1334) | entrada: `saldo − n ≥ 0` (:1342-1343) | segunda cancelación → 400 (`tests/test_edit_cancel_balance.py:380-417`) | — | `audit_state_transition` :1350 |
| Corrección (`POST /corrections`) | `corrections:correct` (`corrections/router.py:16-20`) | `field_name` de `campos_corregibles()` (`corrections/service.py:171-181`) — **sin cantidades** | **Δ sólo si `lot_id`** (misma guarda que PUT :70-81) | ídem | estados correctables :38-39; no contrapartida :33-36 | ídem PUT | — | — | `audit_correction` :105-112 (+ `CorrectionLog`) |
| Reverso (OD-19) | `POST /reversals` · `reversals:create` (`reversals/router.py:16-20`) + aprobación por el motor existente | `event_id`, `reason` | Solicitud: **0** (contrapartida `PENDING_REVIEW` excluida del natural). Aprobación: **−efecto del original** (ambos `REVERSED`, :215-216) | `lot_id` del original | original `APPROVED` no consolidado (:99-106); tipo elegible; una sola contrapartida activa (:115-123 → 409) | BR-01/BR-04 sobre el saldo resultante (:198-214) | `FOR UPDATE` del original en solicitud y aplicación (:74-79, 96, 194) | — | `audit_accion CREATED entity=reversal` :156-161; `audit_state_transition approved→reversed` :218 |

### 1.3 Análisis de secuencias de riesgo

| Secuencia | Resultado | Evidencia |
|---|---|---|
| Aprobar → editar | Bloqueado: `APPROVED ∉ EDITABLES` (`service.py:73-74,1137-1138`); tampoco corregible (`corrections/service.py:38-44`). | OK |
| Aprobar → cancelar | Bloqueado (`NO_CANCELABLES` :76-78,1338-1339). Único camino: reverso. | OK |
| Reverso de una recepción después de mortalidad | La aprobación del reverso comprueba `saldo − n ≥ 0` (`reversals/service.py:204-207`); si dejara negativo → `BusinessRuleViolation` y `ROLLBACK` (`tests/test_internal_reversal.py:342`). | OK |
| Decrementos concurrentes | `FOR UPDATE` sobre `lots.id` antes de leer (`validators.py:225,249,267,281`); `tests/test_population_invariant.py:341` (3 descartes), `test_egg_incubation_concurrency.py:272-288`. | OK |
| Cancelar entrada vs salida concurrente | Cancelación bloquea la fila del lote y relee (`service.py:1332-1334`); `tests/test_edit_cancel_balance.py:419-460`. | OK |
| Idempotencia de alta | `idempotency_key` único (`models.py:101`; `service.py:225-234`); `test_population_invariant.py:355`. | OK |
| **Reverso de recepción con OC (BR-18)** | `validate_oc_limit` (`validators.py:769-783`) suma `BIRD_RECEPTION ≠ CANCELLED` con la misma `sap_document_ref`. La contrapartida copia `sap_document_ref` (`reversals/service.py:126-134`) y queda `REVERSED`; el original también `REVERSED` y **ambos cuentan** ⇒ tras un reverso el acumulado contra la OC es **2n en lugar de 0**, bloqueando entregas legítimas. **GAP** (#E-01). | `validators.py:769-783`, `reversals/service.py:126-134,215-216` |
| **Lote con un reverso efectivo no puede cerrarse** | `validate_lot_records_approved` excluye sólo `ESTADOS_APROBADOS + CANCELLED` (`validators.py:400-406,436-438`); `REVERSED` (terminal, no cancelable: `service.py:78`) cuenta como «sin aprobar» ⇒ `POST /lots/{id}/close` → 400 «1 en «reversed»» sin salida posible. Los tests de R7 no incluyen `REVERSED` (`tests/test_lot_close_approval.py:34-42`). **GAP** (#E-02). | |
| **Resumen de cierre cuenta anulados** | `close_lot` suma `total_mortality`, `total_feed_kg`, `total_eggs` **sin filtro de estado** (`lots/service.py:469-498`): incluye `CANCELLED` (y, si existieran, `REVERSED` + contrapartida). El resumen devuelto a la UI (`LotDetailPage.tsx:199-209`) es incorrecto ante cualquier anulación. **GAP** (#E-03). | |
| Alta por debajo del saldo aprobado | Un `mortality_recording` `registered` (aún no aprobado) ya descuenta; si luego se **rechaza** (`REJECTED`) sigue descontando hasta que se cancele. Es la decisión documentada (`validators.py:744-748`) — «rejected sí cuenta» en R7 (:426-427). No es defecto, pero implica que un rechazo no libera saldo. | documentado |
| BR-17 acumulativa | `validate_house_capacity` compara **un evento** contra `House.capacity` (`validators.py:721`); N recepciones al mismo galpón pueden superar la capacidad. No existe ledger por galpón (RR-02). **GAP** (#E-04; R-176 la trata como «capacidad estática», `BACKLOG:1294`). | |
| `egg_classification` y KPI de huevos | `_sum_egg_quantity` suma `EGG_COLLECTION` **y** `EGG_CLASSIFICATION` (`reports/service.py:115`) ⇒ un mismo huevo recolectado y luego clasificado cuenta dos veces en `total_eggs`/hen-day. No afecta al saldo BR-02 (que sólo mira `EGG_COLLECTION`). **GAP** (#E-05). | |

**Veredicto población:** el invariante `saldo ≥ 0` y la serialización están cerrados y probados (`test_population_invariant`, `test_edit_cancel_balance`, `test_internal_reversal`, `test_egg_incubation_concurrency`). Los defectos residuales están en los **consumidores** del ledger (BR-18 tras reverso, R7 con `REVERSED`, resumen de cierre) y en la **observabilidad** (sin endpoint ni UI del saldo).

---

## 2 · MÁQUINA DE ESTADOS

### 2.1 `EventStatus` (`operations/models.py:58-73`) — transiciones implementadas

| # | Transición | Ruta · permiso | Precondición (estado origen) | Estado resultante | UI (control) | Audit | Idempotente / repetida | Notas |
|---|---|---|---|---|---|---|---|---|
| T1 | crear → `REGISTERED` | `POST /operations` · `operations:create` (`router.py:70-77`) | — (`service.py:264`) | `registered` | `OperationFormPage.tsx` (wizard) | `audit_event_created` `service.py:308` | `idempotency_key` → devuelve el existente | **`DRAFT` no tiene productor** (`grep EventStatus.DRAFT` → sólo `EDITABLES` :73; R-154 PARTIAL). |
| T2 | editar (sin cambio de estado) | `PUT /operations/{id}` · `operations:update` (:295-303) | `EDITABLES` = `DRAFT, REGISTERED, RETURNED, REJECTED` (`service.py:73-74`); BR-15 (:1134); no contrapartida | igual | **Ninguna** (no hay `api.put('/operations…')` en `frontend/src`; `OperationListPage.tsx:89` «editar» enlaza al detalle) | `audit_state_transition` :1172 | — | **Backend-only**. |
| T3 | submit → `PENDING_REVIEW` | `POST /operations/{id}/submit` · `operations:create` (:310-317) | `REENVIABLES` = `REGISTERED, RETURNED, REJECTED` (:75, :1314; OD-17.a/b) | `pending_review` | `OperationDetailPage.tsx:120-141,183-191` (gate `operations:create` + unidad) | :1322 | 2.ª llamada → 400 | |
| T4 | cancel → `CANCELLED` | `POST /operations/{id}/cancel` · `operations:create` (:320-327) | `∉ NO_CANCELABLES` (`APPROVED, CONSOLIDATED, SENT_TO_SAP, SAP_CONFIRMED, SAP_ERROR, CANCELLED, REVERSED` :76-78) ⇒ **se puede cancelar en `PENDING_REVIEW`/`IN_REVIEW`/`CORRECTED`**; sin motivo, sin rol (R-140 OPEN) | `cancelled` | **Ninguna** (`operations.service.ts:47` define `cancel` pero ningún componente lo llama) | :1350 | 2.ª → 400 | **Backend-only**; `docs/12 §4` fila 13 exige «solo administrador (requiere motivo)». |
| T5 | batch de revisión → `PENDING_REVIEW` | `POST /review/batches` · `review:review` (`review/router.py:47-54`) | `REGISTERED` o `PENDING_REVIEW` (`review/service.py:211`) | `pending_review` + `reviewed_by_id` (:229-233, `update()` masivo) | `ReviewCenter.tsx:146` | **Sólo `ApprovalAction STARTED_REVIEW`** (:234-239); **no** `audit_state_transition` ⇒ sin fila `new_state='pending_review'` ⇒ el SLA 24 h (`sla.py:49-50`) nunca ve estos eventos | — | **GAP** (#E-06). |
| T6 | start_review → `IN_REVIEW` | `POST /review/start/{id}` · `review:review` (:73-80) | `PENDING_REVIEW` (`service.py:266`), `FOR UPDATE` + relectura (:89-107) | `in_review` | `ReviewDetail.tsx:212-215`, `ReviewCenter.tsx:317-323` | :285 | 2.ª → 400 (`test_r166_10`) | |
| T7 | return → `RETURNED` | `POST /review/return` · `review:review` (:83-90) | `IN_REVIEW` (:294) | `returned` | `ReviewDetail.tsx:229` | :314 | 2.ª → 400 | |
| T8 | complete_review (1 nivel) → `APPROVED` | `POST /review/complete` · `review:review` (:93-100) | `IN_REVIEW`; BR-14 (:338); `Company.approval_levels ≤ 1` (:333) | `approved` (o `reversed` si es contrapartida :343-346; + lote OD-25 :349-351) | `ReviewDetail.tsx:218-222` | :370 + `REVIEW_COMPLETED` :376-380 | 2.ª → 400 | |
| T9 | complete_review (≥2 niveles) → `CORRECTED` | ídem | `IN_REVIEW`, `approval_levels ≥ 2` | `corrected` («pendiente de aprobador», **sin corrección**: R-142 OPEN) | ídem | :370 | | Los `ApprovalStep` (`review/models.py:69-85`) sólo se leen para `require_segregation` (:76-85); el nivel 3 «Confirmación» no tiene efecto en runtime (P1-13 → GA-REM-019). |
| T10 | corrección → `CORRECTED` | `POST /corrections` · `corrections:correct` | `REGISTERED, PENDING_REVIEW, IN_REVIEW, RETURNED, REJECTED` (`corrections/service.py:38-39`) | `corrected` (:99) | `ReviewDetail.tsx:232-235,255-258` → `CorrectionForm.tsx:52-57` | `audit_correction` :105 | **Una 2.ª corrección sobre `CORRECTED` → 400** (`CORRECTED ∉ correctable`) ⇒ sólo un campo por ciclo; para otro campo hay que rechazar primero. **GAP** (#E-07). Además una corrección sobre `REGISTERED` salta la revisión y va directo al aprobador. | |
| T11 | approve → `APPROVED` | `POST /approvals/approve` · `approvals:approve` (:123-130) | `CORRECTED` o `IN_REVIEW` (`service.py:629`); BR-14 + R-143 (:27-67); `FOR UPDATE` (:627) | `approved` / `reversed` (contrapartida :506-508) / + lote OD-25 (:513-515) | `ReviewDetail.tsx:239-244`, `ApprovalPanel.tsx:54,238-240` | :527 | 2.ª → 400 (`test_r166_02`) | |
| T12 | reject → `REJECTED` | `POST /approvals/reject` · `approvals:reject` (:133-140) | `CORRECTED` o `IN_REVIEW` | `rejected` + notificación `record_rejected` (:565-590) | `ReviewDetail.tsx:246-250`, `ApprovalPanel.tsx:70,242-244` (motivo ≥10 car. en UI :65) | :551-553 — **`previous_state` fijado a `"corrected"` aunque venga de `IN_REVIEW`** (#E-08) | 2.ª → 400 | `REJECTED` es reenviable/editable/corregible (OD-17.a). |
| T13 | batch-approve / batch-reject | `POST /approvals/batch-*` · **`review:review`** (:143-160) | por evento como T11/T12 | | `ApprovalPanel.tsx:100,119,173-183` (gate `review:review`) | por evento | | **Permiso más débil que la ruta unitaria** (`review:review` vs `approvals:approve/reject`): un revisor sin `approvals:approve` aprueba en lote. **GAP** (#E-09). |
| T14 | reverso: solicitud | `POST /reversals` · `reversals:create` | original `APPROVED`, no consolidado, tipo elegible, sin contrapartida activa | contrapartida nueva `PENDING_REVIEW` (`reversals/service.py:131`); original sigue `APPROVED` | **Ninguna** (`grep -ril reversal frontend/src` → 0) | :156-161 | 2.ª → 409 (:121-123) | **Backend-only**. La contrapartida nace en `PENDING_REVIEW` sin fila de auditoría `new_state=pending_review` ⇒ fuera del SLA 24 h. |
| T15 | reverso: aplicación → `REVERSED` (ambos) | dentro de T8/T11 (`efectuar_reverso_si_procede` :181-219) | original sigue `APPROVED` (:195-197); saldos ≥ 0 | `reversed` × 2 | — | :218 (`approved→reversed`) | una sola contrapartida efectiva (`test_rv03`) | |
| T16 | consolidate → `CONSOLIDATED` | `POST /sap/consolidate` · `sap:send_sap` (`sap/router.py:49-53`) | `APPROVED` (`sap/service.py:158-160`) | `consolidated` (:224, ORM) | `SapManagerPage.tsx:53,135` | **Sin helper**; sólo el listener (`listeners.py:51`) si está registrado (ver §3.1) | 2.ª → `[]` | |
| T17 | export → `SENT_TO_SAP` | `POST /sap/export` · `sap:send_sap` | `CONSOLIDATED` sin `sap_payload_id`; **sólo si `adapter.delivers_to_sap`** (:350-360) — con `manual`/`mock` los eventos **no cambian** (:361-364) | `sent_to_sap` (vía `update()` masivo) | `SapManagerPage.tsx:62,139` | `audit_accion EXPORT` (:387-390); **sin transición auditada** (`update()` no dispara listener) | clave de idempotencia (:276-293) | En producción (`SAP_ADAPTER=manual`, `config.py:131`) **nunca se alcanza**. |
| T18 | retry → `SAP_CONFIRMED` | `POST /sap/retry` · `sap:send_sap` | payload `FAILED`, `retry_count < 3` | `sap_confirmed` (:446-450, `update()`; **salta `SENT_TO_SAP`**) | **Ninguna** (`sap.service.ts:50` definido; `SapManagerPage` no lo llama) | **Ninguna** | backoff | Backend-only. |
| T19 | → `SAP_ERROR` | **Sin productor** (`grep SAP_ERROR backend/app` → sólo listas/guardas) | — | — | — | — | — | R-157 (P1, SAP). |
| T20 | clasificar / reclasificar unidad | `POST /operations/{id}/classify` · `masters:update`; `/reclassify` · `corrections:correct` (`router.py:147-244`) | pendiente / ya clasificado | sin cambio de `status` | **Ninguna** (`grep classify frontend/src` → 0) | `audit_accion UPDATED`/`CORRECTED` (`classification.py:201,327`) | | Backend-only. |

**Estados inmutables**: `APPROVED`/`CONSOLIDATED`/`SENT_TO_SAP`/`SAP_CONFIRMED`/`SAP_ERROR`/`REVERSED` no se editan (T2), no se corrigen (T10) ni se cancelan (T4). `BR-15` en `validate_sap_edit_lock` (`validators.py:701-709`). La contrapartida no se edita ni corrige (`service.py:1141-1144`, `corrections/service.py:33-36`).

**Transiciones sin camino de usuario (backend-only):** T2 (PUT), T4 (cancel), T14 (reverso), T18 (retry SAP), T20 (classify/reclassify), `POST /sap/references/import` (sin UI), `POST /lots/activate-manual` (sin UI: `grep activate-manual frontend/src/pages` → 0), `approval-steps` (sin UI).
**Sin productor:** `DRAFT`, `SAP_ERROR`, `LotStatus.CANCELLED`, `AuditAction.LOGOUT` (no existe `/logout`: `auth/router.py`).
**UI sin backend:** ninguna encontrada. Anomalía: `ReportsPage.tsx:193` enlaza a `/reports/lot/2` (lote fijo).

### 2.2 `LotStatus` (`masters/models.py:47-50`)

| Transición | Ruta · permiso | Precondición | UI | Audit |
|---|---|---|---|---|
| crear → `ACTIVE` | `POST /lots` · `lots:create` (`lots/router.py:39-46`); auto OD-25 (`lots/service.py:128-196`) | código único (409), granja propia, área activa (OD-21), unidad habilitada | `LotFormPage.tsx` | `CREATED` módulo `LOTS` (`lots/service.py:402-408`, :191-195) |
| `ACTIVE` → `CLOSED` | `POST /lots/{id}/close` · `lots:create` (:80-92) | activo; BR-05; R7 | `LotDetailPage.tsx:185-193` (gate `lots:create` + `status==='active'`), :111 | **Ninguna** (#E-10) |
| `CLOSED` → `ACTIVE` (reapertura) | **No existe**; `LotUpdate` excluye `status` (`lots/schemas.py:50-63`, R-51) | | | |
| → `CANCELLED` | **Sin productor** (R-154 OPEN, `BACKLOG:1084`) | | | |
| activación manual | `POST /lots/activate-manual` | lote sin historia | **Ninguna** | **Ninguna** (#E-10) |
| fase (`POST /lots/{id}/phases`) | `lots:create` | lote alcanzable | `LotDetailPage.tsx:125` | **Ninguna** (`lots/service.py:685-697`) |

---

## 3 · AUDITORÍA

### 3.1 Dos mecanismos concurrentes (listener + helpers)

| Mecanismo | Registro | Qué escribe |
|---|---|---|
| Listener `after_flush` | `audit/listeners.py:71-113`; registrado en `main.py:41-42` (`register_audit_listeners()` dentro de `lifespan`); usuario vía `ContextVar` fijado en `auth/security.py:165` | `OperationalEvent` nuevo → `CREATED` con volcado completo (:163-197); `OperationalEvent` con cambio de `status` → acción según `_STATUS_TO_AUDIT_ACTION` (:43-56, :200-263); `CorrectionLog` nuevo → `CORRECTED` (:270-288); `ApprovalAction` nuevo → `REVIEW_STARTED/RETURNED/CORRECTED/APPROVED/REJECTED` (:295-325). `company_id or 0` (:140). |
| Helpers explícitos | `audit/helpers.py` (`audit_event_created` :73-92, `audit_state_transition` :95-148, `audit_correction` :151-174, `audit_accion` :225-262) | Llamados por los servicios (inventario en §3.2). `audit_accion` devuelve `None` sin empresa (:250-252, R-83). |
| Tests | `tests/conftest.py:117-140` usa `httpx.ASGITransport(app=app)` **sin `lifespan`** ⇒ el listener **no está registrado en los tests**; `tests/test_edit_cancel_balance.py:393` exige **exactamente 1** fila `cancelled` por cancelación; `test_audit_coverage.py:171` exige 1 `REVIEW_COMPLETED`. | |
| Consecuencia | En **runtime real** (uvicorn ejecuta `lifespan`) el listener sí queda registrado y el `ContextVar` se propaga al greenlet de SQLAlchemy ⇒ **filas duplicadas**: alta = 2 `CREATED`; aprobación = hasta 3 `APPROVED` (status dirty + `ApprovalAction` + helper); corrección = 2 `CORRECTED`; cancelación = 2 `CANCELLED`. Los tests no lo detectan por construcción. Coincide con **P1-12 «auditoría duplicada e incompleta»** (`BACKLOG:98`, asignada a GA-REM-003 AC06 + GA-REM-019; AC06 es sólo autenticación). **GAP** (#E-11, verificar en runtime). | |

### 3.2 Acción de negocio → auditoría

| Acción | `AuditAction` · módulo | Escrita en | actor | empresa | old/new values | motivo/comentario |
|---|---|---|---|---|---|---|
| Evento: crear | `CREATED` · `OPERATIONS` | `operations/service.py:308` | sí | sí | sólo `new_state` (helper); volcado completo sólo por listener | `observations` |
| Evento: editar (PUT) | `UPDATED` (`old==new` estado) · `OPERATIONS` | :1172-1173 | sí | sí | **sí** (`previous_values/new_values`) | «Evento actualizado» |
| Evento: submit | `UPDATED` (`new_state=pending_review`) | :1322 | sí | sí | estados | «Enviado a revisión» |
| Evento: cancel | `CANCELLED` | :1350 | sí | sí | estados | «Evento cancelado» — **sin motivo** (R-140) |
| Batch de revisión | — (sólo `ApprovalAction`) | `review/service.py:206-243` | | | | **sin `audit_state_transition`** (#E-06) |
| start_review | `REVIEW_STARTED` · `REVIEW` | :285 | sí | sí | estados | sí |
| return | `RETURNED` · `REVIEW` | :314 | sí | sí | estados | observaciones |
| complete_review | `APPROVED`/`CORRECTED` + `REVIEW_COMPLETED` | :370, :376-380 | sí | sí | estados | observaciones |
| corrección | `CORRECTED` · `CORRECTIONS` | `corrections/service.py:105-112` | sí | sí | **sí** (campo) | `reason` |
| approve | `APPROVED` (o `REVERSED`) · `APPROVALS` | `review/service.py:527` | sí | sí | estados | observaciones |
| reject | `REJECTED` · `APPROVALS` | :551-553 | sí | sí | estados (**previous fijo «corrected»**, #E-08) | observaciones |
| reverso: solicitud / aplicación | `CREATED entity=reversal` · `OPERATIONS`; `REVERSED` | `reversals/service.py:156-161`, :218 | sí | sí | ids | `reason` |
| Lote: crear (manual / auto OD-25) | `CREATED` · `LOTS` | `lots/service.py:402-408` / :191-195 (`origin`) | sí | sí | `lot_code`, `bird_type`/`origin` | — |
| Lote: editar | `UPDATED` · `LOTS` | `masters/service.py:257-258` (vía `MasterService.update`) | sí | sí | sí | — |
| Lote: cerrar | **NO** | `lots/service.py:438-549` | | | | #E-10 |
| Lote: activate-manual | **NO** | :555-659 | | | | #E-10 |
| Lote: fases | **NO** | :685-697 | | | | #E-10 |
| Maestros CRUD (20 entidades) | `CREATED/UPDATED/DELETED` · `MASTERS` | `masters/service.py:242,257,266` | sí | sí | sí | — |
| Curvas de peso: crear / activar | **NO** | `masters/curves.py:90,143` (no pasan por `MasterService`) | | | | #E-12 |
| Usuarios: crear / editar / desactivar | **NO** | `auth/service.py:337-382, 384-421, 491-506` | | | | #E-13 (docs/02 §3.11.1 «cada acción»; GA-REM-032 no los incluyó en AC02/AC03) |
| Cambio de contraseña | `UPDATED entity=user_password` · `AUTH` | `auth/service.py:474-489` | sí | titular | no | comentario |
| Roles: crear / editar (permisos) | `PERMISSION_CHANGE` · `USERS` | :613, :653 | sí | sí | | |
| Login / login fallido | `LOGIN` / `LOGIN_FAILED` · `AUTH` | :212-214 / :188-190 | sí | sí (fallido sin empresa → `None`, R-83) | | |
| Logout | **NO existe endpoint** (`auth/router.py`); GA-REM-032 AC01 afirma «el cierre escribe `LOGOUT`» | | | | | #E-14 (P1-4 conocido, `BACKLOG:90`) |
| switch-company | `CONTEXT_SWITCHED` · `AUTH` | :525-527 | sí | sí | | |
| BU habilitar/deshabilitar | `CONFIG_CHANGE` · `CONFIG` + por cada concesión terminada `PERMISSION_CHANGE` con `cause=company_business_unit_disabled` (OD-23) | `business_units/admin.py:197-203`, :207-214 | sí | sí | estados | |
| BU conceder / revocar | `PERMISSION_CHANGE` · `USERS` | :385-390, :423-428 | sí | sí | estados | |
| Clasificar / reclasificar | `UPDATED` / `CORRECTED` · `OPERATIONS` | `classification.py:201-203`, :327-329 | sí | sí | | motivo (reclasificar) |
| Evidencias: subir / borrar | **NO** | `operations/service.py:1363-1414` | | | | #E-15 |
| Alertas: resolver | **NO** | :1011-1025 | | | | (menor) |
| SAP: importar referencias / consolidar / exportar / reintentar | `IMPORT` (`sap/service.py:118-122`) / **sólo listener** (T16) / `EXPORT` (:387-390) / **NO** (T18) | | | | | |
| Notificaciones | no auditadas (por diseño: `notifications/models.py` docstring) | | | | | |
| Exportación Excel/PDF (reportes) | **NO** (cliente, `frontend/src/utils/export.ts`); `AuditModule.REPORTS` nunca se usa; GA-REM-032 AC04 «exportar un informe escribe `EXPORT`» no se cumple para informes | | | | | #E-16 |

### 3.3 Enum, inmutabilidad y contrato de consulta

- **`AuditAction` nunca escritos**: `LOGOUT` (sin endpoint), `SENT_TO_SAP` y `SAP_CONFIRMED` (las transiciones se hacen con `update()` masivo, `sap/service.py:353-360,446-450`, sin helper ni listener), `SAP_ERROR` (sin productor). `CONSOLIDATED` sólo por listener. `AuditModule.REPORTS` nunca usado. Columnas `ip_address`, `user_agent`, `is_sensitive` **nunca pobladas** (`grep` en `backend/app` → sólo modelo/esquema), pese a `docs/02 §3.11.1` «IP o dispositivo».
- **Inmutabilidad (R-148, P2 OPEN)**: sólo en aplicación (router de sólo lectura `audit/router.py:16-63`; sin `UPDATE/DELETE`); en BD no hay trigger ni regla (`alembic/versions/ee30bd1aa374_add_audit_log.py` crea la tabla; `grep -i trigger|rule|revoke` → 0). Confirmado OPEN (`BACKLOG:940`).
- **Contrato de consulta**: `GET /audit` (`audit/router.py:16-41` · `audit:read`) acepta `user_id, action, entity_type, entity_id, module, lot_id, farm_id, date_from, date_to, state, sap_reference_id, limit, offset`; todos aplicados en servidor (`audit/service.py:32-100`), acotados a `company_id` (:48-49). Los siete de `docs/02 §3.11.2` están cubiertos. **`AuditPage.tsx:61-72` sólo envía `action`, `module`, `date_from`, `date_to`** (y `action=corrected` en la pestaña de correcciones); no ofrece usuario, lote, estado ni documento SAP (`audit.service.ts` declara `user_id/lot_id/farm_id` pero la página no los usa). `sap_reference_id` **nunca se escribe** (ningún helper lo rellena) ⇒ el filtro «documento SAP» siempre devuelve vacío (#E-17).

---

## 4 · REPORTES / KPI

Autorización común: `require_permission("reports","read")` en todas las rutas (`reports/router.py:15-156`); alcance por lote `_exigir_lote` → `lotes_alcanzables(company, unidades)` → 404 (`reports/service.py:37-62`); dashboard `dashboard:read` (`dashboard/router.py:13-28`) con `_lotes()` (`dashboard/service.py:17-36`).

| Endpoint | Fórmula (líneas) | Filtro de estado | Fecha / unidad | Consumidor frontend |
|---|---|---|---|---|
| `GET /reports/kpis?lot_id` | agrega mortalidad, FCR, huevos, incubadora, bienestar, vacunación, traslado (`:415-433`) | mixto (ver filas) | | `ReportsPage.tsx:17`, `LotDetailPage.tsx:53` |
| `/kpis/mortality` | `total_deaths / (OB.♂+OB.♀) × 100` (:140-153) | `_sum_bird_quantity` → `APPROVED, CONSOLIDATED, SENT_TO_SAP, SAP_CONFIRMED` (:84-87); **excluye `SAP_ERROR`** (documentado `validators.py:398-399`) | % | `ReportsPage.tsx:97-101`, `LotDetailPage.tsx:358-362`, `export.ts:97-98` |
| `/kpis/feed-conversion` | **`FCR = total_feed_kg / 1000`** (:161) | aprobados (:100-103) | «kg/kg (estimado)» con `note` (:162-163) | `ReportsPage.tsx:104-108`, `export.ts:99-100` |
| `/kpis/egg-production` | `hen_day = total_eggs / (OB.♀ × 30) × 100` (:172); `fertilidad_pct` (:185-189) | aprobados; **suma `EGG_COLLECTION` + `EGG_CLASSIFICATION`** (:115) | % | `ReportsPage.tsx:111-115`, `LotDetailPage.tsx:371-375` |
| `/kpis/hatchery` (lote opcional) | nacimiento = nacidos/cargados; eclosión = nacidos/fértiles; rendimiento = (nacidos − descartes)/cargados (:191-246); `None` sin base (:248-253) | `_aprobados` (:255-260) | % | `ReportsPage.tsx:118-121`, `LotReportPage.tsx:33,126-135` |
| `/kpis/animal-welfare` (G-01) | `100 − (observations ILIKE '%salud%' / inspecciones) × 100` (:439-465) | **sin filtro** | % | `ReportsPage.tsx:207-210` |
| `/kpis/vaccination-efficiency` (G-02) | **`count(eventos vacunación) / (nacidos/1000) × 100`**, tope 100 (:490-504) | nacidos aprobados; eventos **sin filtro** (:490-496) | % | `ReportsPage.tsx:213-216`, `LotReportPage.tsx:31` |
| `/kpis/transfer-efficiency` (G-03) | `despachados / nacidos × 100` (:512-543) | aprobados | % | `ReportsPage.tsx:219-222`, `LotReportPage.tsx:32` |
| `/kpis/afcr` (G-04) | **`feed_kg / (Σ quantity(WEIGHT_RECORDING, BIRD_EXIT)/1000)`** — suma **aves** como gramos (:554-566) | alimento aprobado; **peso sin filtro** (:554-563) | kg/kg | `LotReportPage.tsx:30` |
| `/kpis/production-index` (G-05) | `(avg_weight_g × viabilidad) / (age_days × FCR × 10)` (:611); `avg_weight` = media de **todos** los `bird_movements.avg_weight` del lote, cualquier tipo/estado (:587-595); `age_days = hoy − start_date` (R-186) (:605) | **sin filtro** en peso | índice | **ninguno** (`grep production-index frontend/src` → 0) |
| `/kpi/ipe/{lot}` (G-06) | `IPE = (viab% × ADG) / (FCR × 10)`; `ADG = avg_weight_g(WEIGHT_RECORDING) / age_days` (:626-681); sin `×100` (OD-22/R-187, :668-670); `reference {>300, 250-300, 200-250}` (:680) | **sin filtro de estado** en peso (:641-648) | escala EPEF | `LotDetailPage.tsx:56,389-403` (bandas `>=300`/`>=250`), `LotReportPage.tsx:28` |
| `/kpi/weight-uniformity/{lot}` (G-07) | `CV% = stddev/avg × 100` sobre `avg_weight` de `WEIGHT_RECORDING` (:687-743); bandas <8/<12 | **sin filtro** (:696-710) | % | `LotDetailPage.tsx:57,409-416`, `LotReportPage.tsx:29` |
| `/lot/{lot}` | conteos por tipo y estado, apertura, fases (:314-373) | todos (distribución) | | `LotReportPage.tsx:26`, `export.ts:71-89` |
| `/sap-comparison` | eventos con `sap_document_ref`; matched = `SAP_CONFIRMED/SENT_TO_SAP`, pending = `APPROVED` (:379-409) | por definición | | `SapComparisonPage.tsx:14` |
| `GET /dashboard/mobile` | conteos del usuario (hoy, `RETURNED`, aprobados hoy) (`dashboard/service.py:38-85`) | | | `DashboardPage.tsx:94` |
| `GET /dashboard/admin` | `by_status`, pendientes, top tipos, 7 días, `lots_by_type`, `mortality_trend`, `active_alerts` (:87-152) | `mortality_trend` **sin filtro de estado** (:185-200); `active_alerts` **sin `_ambito` de unidad** (calculado :212-213 pero no aplicado en :224-227) | semanas ISO | `DashboardPage.tsx:94-98,148,554-559` |

**Verificación G-06 / OD-22**: fórmula `(viabilidad × ganancia_diaria) / (fcr × 10)` sin `×100` (`reports/service.py:670`) — conforme a `GA_GOV_02_OWNER_DECISION_PACKET.md:11-12,50` (Opción A, bandas `>300 / 250-300 / 200-250`). Frontera 250 → «Bueno», 300 → «Excelente» (`tests/test_r187_ipe_od22_scale.py:347-356`; `LotDetailPage.tsx:396-397`). **Pero** sus entradas siguen viciadas: `fcr` viene de R-131 (`feed_kg/1000`, :664-665) y `viabilidad` de R-132 (denominador sólo `OpeningBalance` ⇒ mortalidad 0 % y viabilidad 100 % en lotes activados por recepción, :638-639). El IPE es correcto en **escala** y no en **valor**.

**Estado en código de los hallazgos abiertos de ola C (todos siguen presentes):**

| Hallazgo | Estado | Evidencia |
|---|---|---|
| R-131 FCR = `feed/1000`; edad con `date.today()` en lotes cerrados | **PRESENTE** | `reports/service.py:161`; :605, :660 usan `date.today()` (no `end_date`) |
| R-132 % mortalidad con denominador sólo `OpeningBalance`; tendencia sin filtro de estado | **PRESENTE** | :143-146; `dashboard/service.py:185-200` |
| R-133 vacunación cuenta eventos `/1000` | **PRESENTE** | :490-499 |
| R-134 AFCR suma `quantity` como gramos; sin peso de muertos | **PRESENTE** | :554-566 |
| R-141 hen-day ×30 · bienestar heurístico · rendimiento «cargados» · ganancia diaria aproximada | **PRESENTE** | :172, :445-457, :229, :667 |
| R-184 / R-186 / R-187 (fecha y escala) | CERRADOS | :602-605, :656-660, :668-670 |

**Exportaciones** (`frontend/src/utils/export.ts`): 100 % cliente (SheetJS :10-27; jsPDF+autotable :31-66); `kpisToRows` exporta `lot_id, mortality_rate, total_deaths, feed_conversion, total_feed_kg, total_eggs, hen_day_pct, chicks_born, hatchability_pct` (:92-107, desde `ReportsPage.tsx:53-58`); `lotReportToRows` exporta código, tipo, estado, fechas, apertura ♂/♀ y `total_events` (:71-89, desde `LotReportPage.tsx:57-58`). IPE, uniformidad, AFCR, incubadora, vacunación y traslado **no se exportan** aunque se muestran. Sin auditoría de exportación (#E-16).

---

## 5 · MAESTROS Y NOTIFICACIONES

### 5.1 Maestros

- **Inventario**: `App.tsx:135-162` declara **20** entidades (no 22): companies, farms, houses, hatcheries, suppliers, areas, genetic-lines, breeds, feed-types, vaccines, mortality-causes, transports, processing-plants, incubators, hatchers, productive-phases, medications, cull-causes, rejection-reasons, correction-types; más la ruta `/masters/genetic-lines/:id/weight-curves` (`WeightCurvesPage`, :227-228). El backend registra exactamente esos 20 con `register_crud` (`masters/router.py:104-125`) + 4 rutas de curvas (:183-242).
- **Rutas por entidad** (`register_crud` :20-94): `GET` lista (`masters:read`, cabecera `X-Total-Count`), `POST` (`masters:create`), `GET /{id}`, `PUT /{id}` (`masters:update`), `DELETE /{id}` = **baja lógica** `is_active=False` (`masters:delete`, `MasterService.deactivate` `masters/service.py:261-266`, audit `DELETED`). Sin reactivación explícita salvo `PUT` con `is_active` si el esquema lo admite.
- **Tenant vs compartido** (`masters/models.py`): `company_id` **no nulo** en `Farm` (:79), `Hatchery` (:110); derivados por padre `House` (:96), `Incubator` (:126), `Hatcher` (:139), `GeneticWeightCurve` (:199); **nulable = compartido si NULL** en `Area` (:163), `GeneticLine` (:178), `Supplier` (:329), `FeedType` (:342), `Vaccine` (:354), `Medication` (:368), `MortalityCause` (:380), `CullCause` (:391), `Transport` (:402), `ProcessingPlant` (:415), `RejectionReason` (:426), `CorrectionType` (:438); **plataforma global sin `company_id`**: `Breed` (:246-257), `ProductivePhase` (:260-271); `Company` es el inquilino (`_INQUILINO_POR_IDENTIDAD` `masters/service.py:54`). Filtro de lectura: `_apply_company_filter` (:62-97, cero filas sin empresa) + unidad (:99-120).
- **`is_active`**: sólo baja lógica. `MasterService.get_all` (:122-168) **no filtra `is_active`** ⇒ los listados y los selectores devuelven inactivos. `get_houses_by_farm` (:132-152) idem.
- **OD-21 / R-185** (`BACKLOG:1831-1864`, CLOSED_OWNER_ACCEPTED): elegibilidad por estado implementada **sólo Área→Lote**: `verificar_catalogo_de_empresa(..., exigir_activo=True)` (`tenancy.py:94-117`) llamado desde `lots/service.py:345-347` (alta) y :433-435 (cambio de área). Confirmado que **los demás selectores admiten referencias inactivas**: `verificar_catalogos_del_evento` (`tenancy.py:120-154`) no pasa `exigir_activo`; `validate_house_capacity` (`validators.py:712-725`), `verificar_ubicacion` (`tenancy.py:189-201`) y `verificar_pertenencia` (:32-70) no miran `is_active`. Alcance documentado, no defecto nuevo.
- **Wizard de operaciones** (`OperationFormPage.tsx:343-368`): carga `lots?limit=100`, `sap/references?ref_type=transfer_order|purchase_order&limit=50`, y `masters/{vaccines, medications, mortality-causes, cull-causes, transports, farms, processing-plants, suppliers, breeds, houses, feed-types, incubators, hatchers, hatcheries}?limit=100`. **No filtra `is_active`** (sólo galpones por `farm_id` :293-298 y lotes por granja :285); depende del backend para empresa. Tope `limit=100` (máximo de la ruta) ⇒ selectores truncados a partir de 100 filas (#E-18, menor). `LotFormPage.tsx:86-102` filtra **sólo áreas** por `is_active` (:102).

### 5.2 Notificaciones (6 tipos de `docs/02 §3.14:512-519`)

| Tipo | Productor | Destinatarios (OD-08 `recipients.py:101-147`: explícitos ∪ originador ∪ admin ∪ contralor ∪ gerente/supervisor del área) | Idempotencia |
|---|---|---|---|
| `record_rejected` | `review/service.py:565-590` (misma transacción del rechazo) | originador explícito + OD-08 | — |
| `sap_send_failed` | `sap/service.py:464-525` (export y retry) | `Analista SAP` explícito + originadores de los eventos + OD-08 | `evitar_duplicado_sin_leer` |
| `mortality_over_threshold` | `operations/service.py:643-694` (alerta `high_mortality`, umbral `config.py:89-90`) | originador + OD-08 | sin leer |
| `weight_out_of_standard` | ídem (alerta `weight_deviation`, curva OD-06) | ídem | sin leer |
| `review_pending_24h` | `sla.py:63-102`; condición `AuditLog.new_state='pending_review'` + 24 h (:44-60) | originador + OD-08 | sin leer |
| `lot_near_close` | `sla.py:126-200`; ventana `0 ≤ días ≤ 3` a `planned_close_date` | originador = creador del lote según auditoría (:203-222) + OD-08 | por `ocurrencia` (`lot:{id}:{fecha}`) |

- **Cadencia SLA**: tarea en proceso `vigilar_revisiones_pendientes` (`sla.py:225-256`), cada `NOTIFICATION_SLA_SCAN_SECONDS = 3600` (`config.py:103-104`), arrancada en `main.py:47-52` salvo `GA_TEST_ENV=1`. Evalúa 24 h y cierre próximo en el mismo ciclo (:250-251).
- **Consecuencia de §2 T5/T14**: los eventos puestos en `pending_review` por **batch** o la **contrapartida de reverso** no tienen fila `new_state='pending_review'` ⇒ el SLA de 24 h no los detecta (#E-06).
- **API** (`notifications/router.py:26-80`): `GET /notifications` (+`X-Total-Count`), `GET /unread-count`, `GET /{id}`, `PATCH /{id}/read`; autorización por propiedad (`get_current_user`), aislamiento `recipient_user_id` + `company_id` (`service.py:124-134`); marcar leída idempotente (:167-176); sin `read-all`/borrado/creación por diseño. Tests `test_notifications.py:159-507`.
- **UI**: `NotificationBell.tsx` — sondeo 60 s (:21), lista 20, marca leída al abrir (:87-103), navega sólo a `operational_event` (`notifications.ts:58-63`; `lot` y `sap_payload` no navegan). `notifications.ts:15-20` **omite `lot_near_close`** del tipo `NotificationType` (comentario obsoleto «OD-08 sigue abierta»), aunque el i18n sí lo tiene (`public/locales/es/translation.json:1145`) y el backend lo emite ⇒ sólo desalineación de tipos TS, sin efecto en runtime (#E-19, menor). `detalle()` sólo muestra texto para 2 de 6 tipos (:107-112).

---

## DOMAIN GAP CANDIDATES

| # | Área | Descripción | Severidad propuesta | Evidencia | ¿Hallazgo existente? |
|---|---|---|---|---|---|
| E-01 | Ledger / BR-18 | Tras un reverso efectivo de `bird_reception`, `validate_oc_limit` cuenta el original **y** la contrapartida (ambos `REVERSED`, misma `sap_document_ref`) ⇒ acumulado contra la OC = 2n; entregas parciales posteriores rechazadas. Debe aplicar la semántica de `_suma_neta` o excluir `REVERSED`+contrapartidas. | **P2** (integridad de dominio; bloquea operación) | `validators.py:769-783`; `reversals/service.py:126-134,215-216` | No (grep BR-18/reverso en backlog → 0). Vecino: OD-19 §5, R-176 |
| E-02 | Cierre de lote / R7 | `validate_lot_records_approved` trata `REVERSED` como «sin aprobar»; como `REVERSED` es terminal y no cancelable, **un lote con cualquier reverso efectivo no puede cerrarse nunca**. Tests R7 no cubren `REVERSED`. | **P1** (bloqueo funcional irreversible) | `validators.py:400-406,436-438`; `operations/service.py:76-78`; `tests/test_lot_close_approval.py:34-42` | No (grep reversed+cierre → 0). Relacionado: R-76 (cerrado), OD-19 §1 |
| E-03 | Cierre de lote / resumen | `close_lot` suma mortalidad, alimento y huevos **sin filtro de estado** (incluye `CANCELLED`); `approved_events` excluye `SAP_ERROR`/`REVERSED`. Resumen mostrado en UI incorrecto. | **P2** | `lots/service.py:469-517`; `LotDetailPage.tsx:199-209` | Parcial: R-144 (P2, «resumen sin FCR ni peso final», AOD-08) no cubre el filtro de estado |
| E-04 | BR-17 | Capacidad de galpón validada **por evento**, no acumulada por galpón; N recepciones consecutivas superan `House.capacity`. No hay ledger por galpón (RR-02). | P3 (decisión de dominio) | `validators.py:712-725`; `service.py:900-902` | Parcial: R-176 (`BACKLOG:1294` «capacidad estática») |
| E-05 | KPI huevos | `_sum_egg_quantity` suma `EGG_COLLECTION` + `EGG_CLASSIFICATION` ⇒ doble conteo de huevos clasificados en `total_eggs`/hen-day. | P2 (fórmula) | `reports/service.py:108-122` | No. Familia R-141 (ola C, pausada) |
| E-06 | Estado / SLA | `create_review_batch` cambia a `PENDING_REVIEW` con `update()` sin `audit_state_transition`; la contrapartida de reverso nace en `PENDING_REVIEW` sin auditoría de transición ⇒ sin fila `new_state='pending_review'` ⇒ el aviso «pendiente > 24 h» no los alcanza; además la transición no queda auditada. | P2 | `review/service.py:206-243`; `reversals/service.py:131`; `sla.py:44-60` | No (grep batches/SLA → 0) |
| E-07 | Estado / correcciones | `CORRECTED ∉ correctable` ⇒ sólo **una** corrección por ciclo; la segunda exige rechazar y volver a corregir. Una corrección sobre `REGISTERED` salta la revisión y va directo al aprobador. | P2 (flujo) | `corrections/service.py:38-44,99` | Parcial: R-142 (P2, `CORRECTED` como «pendiente de aprobador»), P1-13 |
| E-08 | Auditoría | `reject` escribe `previous_state="corrected"` fijo aunque el evento venga de `IN_REVIEW` (aprobación directa permitida por `docs/12 §4` fila 4). | P3 | `review/service.py:551-553,629` | No |
| E-09 | Permisos / estado | `POST /approvals/batch-approve` y `batch-reject` exigen `review:review` mientras las rutas unitarias exigen `approvals:approve`/`approvals:reject`; un revisor sin capacidad de aprobar aprueba/rechaza en lote. | **P2** (control interno) | `review/router.py:123-160`; `ApprovalPanel.tsx:100,119,173` | No (grep batch-approve → 0) |
| E-10 | Auditoría / lotes | `close_lot`, `activate_manual` y `add_phase` **no escriben auditoría**; el cierre cambia `status`/`end_date` y la activación fija el saldo de apertura (dato crítico del ledger). `test_t_067_10` sólo comprueba campos del `OpeningBalance`. | **P2** (docs/02 §3.11.1 «cada acción») | `lots/service.py:438-549,555-659,685-697`; `tests/test_opening_balance.py:363-388` | No (GA-REM-032 AC02 cubre alta/edición/baja vía `MasterService`, no estas rutas) |
| E-11 | Auditoría | Listener `after_flush` **y** helpers activos en runtime real (`lifespan` registra el listener; tests con `ASGITransport` sin `lifespan` no lo registran) ⇒ filas duplicadas/triplicadas por acción en producción y tests incapaces de detectarlo (aseveran «== 1»). Requiere verificación en runtime. | **P2** (potencial P1 si se confirma) | `main.py:41-42`; `listeners.py:71-113`; `helpers.py`; `conftest.py:117-140`; `tests/test_edit_cancel_balance.py:393` | Sí: **P1-12** «auditoría duplicada e incompleta» (`BACKLOG:98`) asignada a GA-REM-003 AC06 + GA-REM-019; la parte «duplicada» no tiene evidencia de cierre |
| E-12 | Auditoría / maestros | Curvas de peso (crear versión, activar) no auditadas (no pasan por `MasterService`). | P3 | `masters/curves.py:90,143`; `masters/router.py:200-242` | No |
| E-13 | Auditoría / usuarios | Alta, edición (incluido cambio de rol) y baja de usuarios sin auditoría. | **P2** (seguridad + docs/02 §3.11.1) | `auth/service.py:337-382,384-421,491-506` | Parcial: P1-12 «incompleta»; GA-REM-032 no lo incluyó |
| E-14 | Auditoría / auth | No existe `POST /logout`; `AuditAction.LOGOUT` nunca se escribe pese a GA-REM-032 AC01. | P3 (documental) / P2 si se exige revocación | `auth/router.py`; `specs/remediation/GA-REM-032*.md` AC01 | Sí: P1-4 «sin logout ni revocación» (`BACKLOG:90`) |
| E-15 | Auditoría / evidencias | Subida y borrado físico de evidencias sin auditoría (borrado incluso elimina el fichero). | P3 | `operations/service.py:1363-1414` | No |
| E-16 | Auditoría / reportes | Exportación Excel/PDF 100 % cliente sin rastro; `AuditModule.REPORTS` sin uso; GA-REM-032 AC04 «exportar un informe escribe `EXPORT`» incumplido para informes. | P3 | `frontend/src/utils/export.ts`; `audit/models.py:61` | No |
| E-17 | Auditoría / consulta | `AuditPage` sólo envía `action/module/date_from/date_to`; `sap_reference_id`, `ip_address`, `user_agent`, `is_sensitive` nunca se rellenan ⇒ filtro «documento SAP» y dato «IP o dispositivo» (§3.11.1/§3.11.2) vacíos por construcción. | P3 | `AuditPage.tsx:61-72`; `audit/helpers.py` (sin `sap_reference_id`); `audit/models.py:93-96` | Parcial: GA-REM-032 AC09/AC11 (filtros backend cerrados); la escritura de `sap_reference_id` no |
| E-18 | Maestros / UI | Selectores del wizard y del lote cargan `limit=100` (máximo de la ruta) sin paginación ni búsqueda; catálogos > 100 filas quedan truncados. | P3 | `OperationFormPage.tsx:343-368`; `masters/router.py:33` | No |
| E-19 | Notificaciones / UI | `NotificationType` TS omite `lot_near_close` (comentario obsoleto); `destino()` no navega para `lot`/`sap_payload`; `detalle()` sólo para 2 de 6 tipos. | P3 (UX) | `notifications.ts:11-20,58-63`; `NotificationBell.tsx:107-112` | No |
| E-20 | Ledger / observabilidad | Ningún endpoint ni pantalla expone `get_current_bird_balance`; la UI muestra `initial_population` (sólo `OpeningBalance`) como población. Un operador no puede conocer el saldo contra el que BR-01 rechaza. | P2 (UX de dominio) | `validators.py:49-88`; `LotDetailPage.tsx:52-58,358-362`; `reports/service.py:143-144` | Parcial: R-132 («sin % contra población actual», `BACKLOG:924`) |
| E-21 | Estado / cancelación | `cancel_event` permitido en `PENDING_REVIEW`/`IN_REVIEW`/`CORRECTED` por cualquier `operations:create`, sin motivo ni rol, y sin UI; `docs/12 §4` fila 13 exige administrador + motivo. | P2 | `operations/service.py:76-78,1325-1351`; `router.py:320-327` | Sí: **R-140 PARTIAL/OPEN** (`BACKLOG:932,1084,1096`) |
| E-22 | Dashboard / alcance | `_get_active_alerts` calcula `_ambito` de unidades y **no lo aplica**; el panel lista alertas de cadenas no alcanzables (fuga de dimensión análoga a `lots_by_type` ya corregida). | P2 (alcance BU) | `dashboard/service.py:206-231` | No (grep active_alerts → 0). Vecino: `test_kpi_scope.py:266` sólo cubre `lots_by_type` |
| E-23 | KPI / alcance | `GET /reports/kpis/hatchery` sin `lot_id` agrega **toda la empresa** sin `lotes_alcanzables`; `_filtro_de_lotes` está definido y nunca usado. | P2 (alcance BU) | `reports/service.py:64-70,191-246` | No |
| E-24 | KPI / estado | IPE, uniformidad, G-05, AFCR (peso) y bienestar **no filtran estado** ⇒ pesajes cancelados/no aprobados alteran los índices; G-05 promedia pesos de cualquier tipo de evento. | P2 (fórmula) | `reports/service.py:587-595,641-648,696-710,554-563,442-453` | Parcial: R-131/R-134/R-141 (ola C pausada) no nombran el filtro de estado |
| E-25 | Estado / SAP | `retry_failed` lleva los eventos a `SAP_CONFIRMED` con `update()` saltando `SENT_TO_SAP` y sin auditoría; `SENT_TO_SAP`/`SAP_CONFIRMED` nunca auditados; `SAP_ERROR` sin productor; nivel 3 de aprobación sin efecto. | P2 (SAP, diferido) | `sap/service.py:353-360,446-450`; `review/service.py:333-355` | Sí: R-157 (P1 SAP), P1-13, R-142 |

---

## VEREDICTOS

- **Población (invariante `saldo ≥ 0`, serialización, reverso neto cero): PASS** — validadores, bloqueos y tests cubren alta, edición, cancelación, reverso y concurrencia. **FAIL en consumidores**: BR-18 tras reverso (E-01), R7 con `REVERSED` bloquea el cierre (E-02), resumen de cierre con anulados (E-03), sin observabilidad del saldo (E-20).
- **Saldos de huevos/incubadora: PASS** — R-161 cerrado con bloqueo de fila; sin reverso por OD-19 §18 (coherente con la ausencia de `_suma_neta`).
- **Máquina de estados: PARCIAL** — transiciones núcleo idempotentes y protegidas; sin UI para editar, cancelar, reversar, reintentar SAP, activar manualmente y clasificar; `DRAFT`, `SAP_ERROR`, `LotStatus.CANCELLED`, `LOGOUT` sin productor; permisos de lote (E-09) y corrección única (E-07).
- **Auditoría: PARCIAL** — ciclo del evento, maestros, lotes (alta/edición), BU, roles y acceso cubiertos; **huecos**: cierre/activación/fases de lote, usuarios, evidencias, curvas, exportaciones, batch de revisión; duplicación listener+helper en runtime (E-11); inmutabilidad sólo aplicativa (R-148 OPEN).
- **KPI: OD-22 conforme en escala; fórmulas R-131/132/133/134/141 siguen presentes** (ola C pausada) y añaden E-05, E-23, E-24.
- **Maestros/notificaciones: conforme al alcance documentado** (OD-21 sólo Área→Lote; 20 entidades, no 22; 6 tipos de notificación producidos; SLA horario), con los menores E-18/E-19 y el hueco de SLA E-06.

# R-192 · FINDING — CIERRE DE LOTE IMPOSIBLE TRAS UN REVERSO EFECTIVO; RESUMEN DE CIERRE CON ANULADOS; ERROR DE CIERRE INVISIBLE EN LA UI

| Campo | Valor |
|---|---|
| **Hallazgo canónico** | **R-192** (nuevo; asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`) |
| **Registro** | `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §1 G-03` · ficha §2 «R-192» |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) · runtime `https://avicola.globaldv.net` (`index-DDCcWL76.js` == build local) |
| **Clase (§9)** | `DATA_INTEGRITY` (E-02, E-03) + `ERROR_HANDLING` (C-8) |
| **Prioridad** | **P1** · **BLOQUEA SAP: SÍ** (bloqueo funcional irreversible del ciclo de vida del lote; resumen de cierre — dato de cierre de lote — incorrecto ante cualquier anulación) |
| **Proceso** | P-06 (cierre de lote) · P-07/OD-19 (reverso interno) · P-01…P-06 (todo lote con reverso) |
| **Dedup (§48)** | Buscado en `audit/remediation/REMEDIATION_BACKLOG.md` (R-001…R-189, GA-REM-001…042, OD/AOD, OBS, GA-UAT, GA-FE), `specs/remediation/*`, `audit/ga-*`. Vecinos: **R-76** (`GA-REM-036`, R7 implementada — CERRADA, sin `REVERSED`), **R-144** (P2, «resumen sin FCR ni peso final», AOD-08 — no cubre el filtro de estado), **OD-19 / GA-REM-041** (define `REVERSED` terminal; §3.3 «ninguno cuenta en KPI»; no dice nada del cierre), **B-41/C-8** (`LotDetailPage` errores sólo en consola). Ninguno cubre la brecha ⇒ **hallazgo nuevo**. |
| **Origen** | Informe E (`E_domain_ledger.md` §1.3 E-02, E-03) + informe C (C-8) + evidencia runtime local pasa 1 (`H8-*`) y diseño pasa 2 (`H8b-*`). |

## 1 · Síntoma

1. **E-02** — Un lote con **un reverso efectivo** (`OD-19`: original y contrapartida en `REVERSED`) **no puede cerrarse nunca**: `POST /lots/{id}/close` responde `400 R7` «No se puede cerrar el lote: N registro(s) sin aprobar (N en «reversed»). Apruébelos o anúlelos antes de cerrar.» y **ninguna de las dos acciones que el mensaje propone es posible** (`REVERSED` es terminal: no se aprueba, no se cancela, no se edita).
2. **E-03** — El resumen de cierre (`LotClosureSummary`) suma mortalidad, alimento y huevos **sin filtro de estado**: incluye registros `CANCELLED` y, tras un reverso, el original **y** su contrapartida (ambos `REVERSED`, mismas cantidades) ⇒ el resumen mostrado al usuario es incorrecto ante cualquier anulación.
3. **C-8** — La UI de cierre (`LotDetailPage`) descarta el error del backend (`console.error`) y no muestra nada: el usuario pulsa «Cerrar Lote», el modal se cierra y el lote sigue activo sin explicación.

## 2 · Evidencia de código (verificada en HEAD)

| # | Fichero:línea | Qué hay |
|---|---|---|
| E-02.a | `backend/app/operations/validators.py:400-406` | `ESTADOS_APROBADOS = (APPROVED, CONSOLIDATED, SENT_TO_SAP, SAP_CONFIRMED, SAP_ERROR)` — sin `REVERSED`. |
| E-02.b | `backend/app/operations/validators.py:409-455` (`validate_lot_records_approved`) · `:436-438` | Cuenta como «sin aprobar» todo estado `∉ ESTADOS_APROBADOS ∪ {CANCELLED}`; el docstring razona `cancelled`/`rejected` y **no considera `REVERSED`** (`OD-19` es posterior a `R-76`). |
| E-02.c | `backend/app/operations/service.py:76-78` | `NO_CANCELABLES` incluye `REVERSED` («lo revertido es terminal»). |
| E-02.d | `backend/app/reversals/service.py:181-219` (`efectuar_reverso_si_procede`) · `:215-216` | La aprobación de la contrapartida deja **ambos** eventos en `REVERSED` en la misma transacción. |
| E-02.e | `backend/app/lots/service.py:465` | `close_lot` invoca `validate_lot_records_approved` antes de mutar ⇒ 400 y nada cambia (correcto), pero sin salida posible. |
| E-02.f | `backend/tests/test_lot_close_approval.py:34-42` | `BLOQUEAN`/`NO_BLOQUEAN` recorren 13 estados; **`REVERSED` no está en ninguna lista** ⇒ la suite R7 no detecta la brecha. |
| E-03.a | `backend/app/lots/service.py:469-477` | `total_mortality`: `Σ BirdMovement.quantity` de `MORTALITY_RECORDING` **sin filtro de `status`**. |
| E-03.b | `backend/app/lots/service.py:480-487` | `total_feed_kg`: `Σ FeedMovement.quantity_kg` **sin filtro de `status`** ni de tipo. |
| E-03.c | `backend/app/lots/service.py:490-498` | `total_eggs`: `Σ EggMovement.quantity` de `EGG_COLLECTION` **sin filtro de `status`**. |
| E-03.d | `backend/app/lots/service.py:501-517` | `total_events` (todos) y `approved_events` (`APPROVED, CONSOLIDATED, SENT_TO_SAP, SAP_CONFIRMED` — excluye `SAP_ERROR` y `REVERSED`). |
| E-03.e | `backend/app/lots/schemas.py:264-282` (`LotClosureSummary`) · `backend/app/lots/router.py:80-92` | Contrato tipado del resumen (`GA-REM-029 AC02`). |
| BR-05 | `backend/app/operations/validators.py:362-390` (`validate_lot_closure`) | Pesaje y alimento «existen» si `status ≠ CANCELLED`: un pesaje/alimento **revertido** sigue satisfaciendo BR-05 (coherencia pendiente, ver spec §7). |
| C-8.a | `frontend/src/pages/lots/LotDetailPage.tsx:107-118` (`handleCloseLot`) · `:115` | `catch` ⇒ `console.error(err.response?.data?.detail || t('lots.closeError'))`; sin toast, sin estado de error. |
| C-8.b | `frontend/src/pages/lots/LotDetailPage.tsx:11,42` · `:79-81` | `useToast`/`getErrorMessage` ya importados y usados para alertas — el patrón existe en el mismo fichero. |
| C-8.c | `frontend/src/pages/lots/LotDetailPage.tsx:185-195` · `:198-209` · `:511` | Botón «Cerrar Lote» (gate `lots:create` + `status==='active'`), tarjeta del resumen (`age_days`, `total_mortality`, `total_feed_kg`, `total_eggs`, `total_events`, `approved_events`, `end_date`), modal de confirmación. |
| i18n | `frontend/public/locales/{es,en}/translation.json:857-861` | `lots.closeConfirm`, `lots.closeError`, `lots.closeButton`, `lots.closedSummary` existen. |

## 3 · Evidencia runtime (pila local aislada, semillas `seeds.test_seeds`, aprobación de un nivel)

**Pasa 1** — `audit/ga-claude-final-audit/evidence/ui-e2e-local-pass1.json` (`H8-*`):

| Paso | Resultado |
|---|---|
| `H8-lote-api` | lote `AUD-REV-01` (id 5) creado por API. |
| `H8-feed-aprobado` | `feed_registration` id 15: submit 200 → start 200 → complete 200 ⇒ `approved`. |
| `H8-reverso-solicitado` | `POST /reversals` ⇒ 201, `reversal_event_id` 16 (contrapartida nace `pending_review`). |
| `H8-reverso-efectuado` | start/complete de la contrapartida ⇒ original `reversed`, contrapartida `reversed`. |
| `H8-reversed-no-cancelable` | `POST /operations/15/cancel` ⇒ **400** «No se puede cancelar un evento aprobado, consolidado, enviado o confirmado por SAP, con error de SAP o ya anulado». |
| `H8-cierre-lote-con-reverso` | `POST /lots/5/close` ⇒ **400 BR-05** «sin al menos un registro de pesaje» — el arnés de la pasa 1 no sembró pesaje: BR-05 (`lots/service.py:456`) se evalúa **antes** que R7 (`:465`), por lo que la pasa 1 **no discrimina** E-02 (el aserto `H8-E02-…` quedó `ok:false` por esa causa, no por ausencia del defecto). |

**Pasa 2 — «H8b (pasa 2)»** (`audit/ga-claude-final-audit/evidence/ui-e2e-local-pass2.json`, `H8b-*`; diseño en el runner `ui_e2e_local_pass2.mjs:527-559`): dos **lotes gemelos** `broiler` con recepción (100 aves), pesaje y alimento **aprobados** (BR-05 satisfecho). Control `AUD-REV-CTRL` ⇒ `close` esperado **200**. Gemelo `AUD-REV-REV` ⇒ reverso del alimento (solicitud + aprobación ⇒ ambos `reversed`) ⇒ `close` esperado **400 R7** con detalle «2 registro(s) sin aprobar (2 en «reversed»)»; `cancel` del original ⇒ 400; líneas de tiempo de auditoría del original y de la contrapartida registradas. Resultado exacto: ver el JSON al cierre de la pasa 2 (si el fichero no está presente al leer este paquete, el experimento se re-ejecuta en C3 con el diseño de `R-192_RED_E2E_UAT_DESIGN.md §2`).

## 4 · Causa raíz

- **E-02**: `OD-19` introdujo `REVERSED` como estado terminal (`specs/remediation/OD-19-INTERNAL-REVERSAL-OF-APPROVED-RECORDS.md:52`; `GA-REM-041 §3.1/§3.3`) **después** de que `R-76`/`GA-REM-036` fijara el conjunto de estados de R7; nadie reconcilió R7 con el nuevo estado y la suite `test_lot_close_approval.py` no lo parametriza.
- **E-03**: `close_lot` fue reparado en `R-73`/`R-74`/`R-75` (500, BR-05 en la puerta correcta, fecha con zona) sin revisar la semántica de los sumatorios, que datan del `G-09` original (sin filtro de estado); `OD-19 §3`/`GA-REM-041 §3.4` definen la aritmética neta para los saldos (`_suma_neta`, `validators.py:21-46`) pero el resumen de cierre no la usa.
- **C-8**: `handleCloseLot` es anterior al patrón `toast.error(getErrorMessage(...))` adoptado en el mismo fichero para alertas (`:79-81`) y en el asistente (`R-189 F-01`).

## 5 · Impacto

- Cualquier lote con un reverso interno aprobado queda **abierto para siempre**; el reverso (`GA-REM-041`, certificado) se vuelve una acción con efecto colateral no documentado que contradice `OD-19 §3.3` («ninguno cuenta»).
- El resumen final del lote (dato que documenta el cierre y alimenta la futura fase SAP) puede reportar mortalidad, alimento y huevos que **no ocurrieron** (anulados) o **duplicados** (par revertido).
- El operador no recibe ninguna explicación del rechazo del cierre (ni R7, ni BR-05, ni 403/404).

## 6 · Decisiones vigentes que se preservan

`OD-19` (semántica del reverso: ambos `REVERSED`, neto 0, terminal, no cancelable) · `R-130` (invariante `saldo ≥ 0`; el cierre no toca saldos) · `R-76`/R7 (docs/12 §6: «un lote no puede cerrarse si tiene registros sin aprobar» — se **precisa** que un par revertido no es «sin aprobar») · BR-05 · `GA-REM-029 AC02` (contrato `LotClosureSummary`, sin campos obligatorios nuevos) · `OD-25 (B)` · `R-161` (huevos no reversibles: el sumatorio de huevos sólo excluye `CANCELLED` en la práctica).

## 7 · Paquete

`R-192_SPEC.md` · `R-192_CLARIFICATIONS.md` · `R-192_PLAN_CHECKLIST_TASKS.md` · `R-192_AC_MATRIX.md` · `R-192_RED_E2E_UAT_DESIGN.md`. Sin producto, sin tests, sin edición de ficheros existentes (modo auditoría). GA-REM: **no asignado** (siguiente libre `GA-REM-043`, se asigna al autorizar la ejecución).

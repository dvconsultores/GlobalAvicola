# MATRIZ DE EFECTOS PARA UN REVERSO INTERNO · `R-136` (2026-09-09 · pre-flight del tranche 5 · **sin implementación**)

Inventario de **qué efecto de negocio ya ocurrió** cuando un registro está aceptado, leído del código. Las columnas de
**acción de reverso** están `OWNER_DECISION_REQUIRED` (`AOD-21`): esta matriz existe para que la decisión se tome sobre
hechos, no para implementar. Fuente de verdad de todo efecto: **las filas de `operational_events` y sus submovimientos**;
no hay libro materializado. Un efecto «ocurre» cuando una consulta lo cuenta.

| PROCESO | RECURSO | TIPO DE EVENTO | ESTADO ORIGEN | ¿EFECTO YA APLICADO? | TIPO DE EFECTO | VALOR | FUENTE DE VERDAD | ACCIÓN DE REVERSO | ¿COMPENSACIÓN? | FORMA | ESTADO DESTINO | IDEMPOTENTE | MOTIVO | PERMISO | INQUILINO | BU | AUDITORÍA | SAP | HALLAZGO |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| población (`P-01…`) | `bird_movements` | `bird_reception` · `birth_registration` | `APPROVED` (y todo estado ≠ `CANCELLED`) | **sí, desde el registro**: el saldo suma toda fila no `CANCELLED` (`get_current_bird_balance`) | `+ aves` | `Σ quantity` | filas | `AOD-21` | `AOD-21` (exclusión del conjunto o evento inverso) | `AOD-21` | `AOD-21` (`CANCELLED` reutilizado vs `REVERSED` nuevo) | por definir | **sí** (`Reversal.reason` NOT NULL · `docs/13`) | `AOD-21`/`AOD-18` | empresa efectiva (`OD-14`) | unidad habilitada (`OD-16`) | `audit_logs` + `reversals` | pre-envío: no · post-envío: `SAP_DEFERRED` | `R-136` |
| población | `bird_movements` | `mortality_recording` · `cull_recording` · `bird_exit` · `chick_dispatch` | ídem | **sí**: resta en el saldo (`R-130`, bloqueo de fila) | `− aves` | `Σ quantity` | filas | `AOD-21` | `AOD-21` — **restaurar aves** debe respetar `R-130` (nunca negativo; sin doble restauración) | `AOD-21` | `AOD-21` | por definir | sí | `AOD-21` | ídem | ídem | ídem | ídem | `R-136` |
| huevos (`P-04`, `P-05`) | `egg_movements` | `egg_collection` · `egg_dispatch` · `egg_reception_hatchery` · carga de incubadora | ídem | **sí**: `get_egg_balance`, `get_hatchery_egg_balance` | `± huevos` | `Σ quantity` | filas | `AOD-21` | `AOD-21` — **`R-161`** (saldos de huevos sin bloqueo) condiciona la corrección concurrente: el reverso de huevos **no** puede resolverse sin tocar `R-161` → excluir este subtipo o registrar dependencia | — | — | — | sí | — | ídem | ídem | ídem | — | `R-136` · `R-161` |
| incubadora (`P-05`) | `hatchery_params` · `birth_registration` | nacimientos | ídem | **sí**: `get_viable_chick_balance` | `± pollitos` | `Σ` | filas | `AOD-21` | ídem | — | — | — | sí | — | ídem | ídem | ídem | — | `R-136` |
| alimento / sanidad | `feed_movements` · vacunas · medicación | `feed_registration` · `vaccination` · `medication` | ídem | **sí para KPI** (`reports/service.py`: `APPROVED`, `CONSOLIDATED`, `SENT_TO_SAP`, `SAP_CONFIRMED`) · sin stock local (`G-R08`) | consumo | `Σ kg / dosis` | filas | `AOD-21` | `AOD-21` | — | — | — | sí | — | ídem | ídem | ídem | post-envío: `SAP_DEFERRED` | `R-136` |
| alertas (`P-14`) | `operational_alerts` | cualquiera | al **crear** (`_check_and_create_alerts`) | **sí**: fila de alerta ya emitida | aviso | 1 fila | `operational_alerts` | ¿resolver? ¿conservar como historia? | `AOD-21` | — | — | — | — | — | — | — | — | — | `R-136` |
| trazabilidad (`P-10`) | `egg_batches` · `chick_batches` | `egg_dispatch`+`egg_reception_hatchery` · `chick_dispatch`+`bird_reception` | al **crear** (`_auto_create_traceability_batches`) | **sí**: fila de vínculo generacional | vínculo | 1 fila | `lots.egg_batches/chick_batches` | ¿deshacer el vínculo? contrato `P-10` certificado | `AOD-21` | — | — | — | — | — | — | — | — | — | `R-136` |
| revisión (`P-07`) | `approval_actions` · `approved_by_id` | cualquiera | `APPROVED` | **sí**: decisión registrada | decisión | filas | `approval_actions` | ¿el reverso deshace la aprobación o la conserva como historia? | `AOD-21` | — | — | — | — | — | — | — | `audit_logs` | — | `R-136` |
| consolidación (`P-08`) | `sap_payloads` | cualquiera | `CONSOLIDATED` | **sí**: payload preparado, evento marcado `CONSOLIDATED` (atómico por lote, `R8`) | documento preparado | 1 payload/grupo | `sap_payloads` | reverso pre-envío exige **des-consolidar el grupo** | `AOD-21` | — | — | — | — | — | — | — | — | preparación | `R-136` |
| envío (`P-08`) | `sap_payloads` · `external_transaction_id` | cualquiera | `SENT_TO_SAP` · `SAP_CONFIRMED` · `SAP_ERROR` | **sí, en SAP** | documento contabilizado | — | SAP | **documento de reverso SAP** (`BR-16`, `R16`, `OD-17.c`) | sí, en SAP | `Reversal.reversal_event_id` | — | — | sí | `sap:send_sap` | — | — | — | **`SAP_DEFERRED`** (`GA-REM-017` `BLOCKED_EXTERNAL`) | `R-136` (SAP) |
| lote (`P-06`, `P-11`) | `lots.status` · `opening_balances` | cierre (`POST /lots/{id}/close`) · activación manual | `closed` · saldo de apertura creado | **sí**: `status = closed`, `end_date`; `OpeningBalance` | estado de lote | 1 fila | `lots` | reapertura / anulación del saldo de apertura: **`AOD-08`** (dos «cierres»), `R-154` | `AOD-08` | — | — | — | — | — | — | — | — | — | `R-154` (no `R-136`) |

## Estados origen (mapa vigente del tranche 4 + esta lectura)

| Estado | ¿Reversible internamente? | Por qué |
|---|---|---|
| `DRAFT` · `REGISTERED` · `PENDING_REVIEW` · `IN_REVIEW` · `RETURNED` · `REJECTED` · `CORRECTED` | **NO** — no hay efecto aceptado; la vía es corrección/reenvío/cancelación (`GA-REM-006-A`) | `OD-17.a/b` |
| `APPROVED` | **por decidir** (`AOD-21`): Rec. 7.17 exige «versión/reverso» para tocarlo; hoy es inmutable (`AC-S10`) y no cancelable (`NO_CANCELABLES`) | `docs/12 R5` no aplica (no enviado) |
| `CONSOLIDATED` | **por decidir** (`AOD-21`): choca con `R8` (consolidación atómica) | — |
| `SENT_TO_SAP` · `SAP_CONFIRMED` · `SAP_ERROR` | **NO internamente**: reverso de documento SAP (`BR-16`) | `SAP_DEFERRED` |
| `CANCELLED` | **NO**: terminal; sin efecto (excluido de todo saldo y KPI) | `OD-17.a` |
| `REVERSED` | **no existe** en `EventStatus` | `AOD-21` decide si nace |

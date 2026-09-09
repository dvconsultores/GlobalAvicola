# MATRIZ DE ESTADOS Y CORRECCIÓN · `P-07` — `R-135` + `R-143` (+ `R-140` guarda · `R-154` `DRAFT`/`version`)

**WAVE B · tranche 4** · 2026-09-09 · base `5b64104` · construida **antes** de los AC y del código

Fuentes: `R-135`, `R-143`, `R-140`, `R-154` (backlog + `WAVE_B §1` filas 4-7, 15), `H360-P02/P03/P04/P06/P10/P11`,
`OD-17.a/b/c`, `docs/12 §2, §3, §4, §6 (R1-R9), §8, §11`, `spec.md §4.10, §4.11`, `GA-REM-006` (`RR-01`, AC01-09,
certificada), `GA-REM-007` (`RR-03`, AC01-07, certificada), `OPERATIONAL_PROCESS_STATE_AND_CLOSURE_MATRIX.md §1, §2, §5`,
`operations/models.EventStatus`, `operations/service.py` (`update_event:1017`, `submit_to_review:1058`,
`cancel_event:1072`), `review/service.py` (`_exigir_segregacion:27`, `start_review:211`, `return_to_operator:239`,
`complete_review:268`, `approve:423`, `reject:452`, `_get_event_for_approval:533`), `corrections/service.py`
(`create_correction`, `campos_corregibles`), `review/models.py` (`ActionType`, `ApprovalStep`, `ApprovalAction`),
`corrections/models.CorrectionLog`, `audit/helpers.py` (`audit_state_transition`: `previous_state`/`new_state`),
`validators.get_current_bird_balance` (excluye solo `CANCELLED`), `frontend/src/services/operations.service.ts:47`
(`cancel` sin cuerpo), `tests/test_corrections.py`, `tests/test_full_workflow_audit.py`, `tests/test_review.py`.

## 1. Hallazgos exactos

| ID | Sev. | Título (backlog) | Defecto exacto en el código | Requisito raíz | Decisión | Spec |
|---|:--:|---|---|---|---|---|
| `R-135` | P1 | `RETURNED` no se reenvía; `REJECTED` es terminal | `submit_to_review` solo desde `REGISTERED` (`:1058`); `update_event` admite `DRAFT/REGISTERED/RETURNED` y **no** `REJECTED` (`:1017`); `create_correction` admite `REGISTERED/PENDING_REVIEW/IN_REVIEW/RETURNED` y **no** `REJECTED` | `docs/12 §2` («Devuelto → Operador reenvía», «Rechazado → Operador reenvía (corregido)»), `§4` filas 5 y 8; `spec §4.10` | **`OD-17.a/b`** ✓ | `GA-REM-006` enm. A |
| `R-143` | P2 | `docs/12 R2` (quien corrige no aprueba) no implementada | `_exigir_segregacion` compara solo `registered_by_id` con el aprobador; `correction_logs.corrected_by_id` no se consulta | `docs/12 §6 R2`; `OD-17.b` («quien rechazó no aprueba el reenvío si la configuración lo exige») | `RC-03`/`RR-03` (configurable) ✓ | `GA-REM-007` enm. A |
| `R-140` | P2 | `cancel` sin motivo ni rol; no bloquea `SAP_CONFIRMED`/`SAP_ERROR` | `cancel_event` deniega solo `APPROVED/CONSOLIDATED/SENT_TO_SAP` (`:1072`); ruta sin cuerpo; permiso `operations:create` | `docs/12 §4` fila 13 | permiso «solo administrador» → **`AOD-18`** (pendiente); motivo → contrato de ruta que el cliente llama **sin cuerpo** (`operations.service.ts:47`) → exige vertical de UI (fuera de alcance) | **PARTE A** (guarda de estados) en este tranche; motivo y permiso **OPEN** |
| `R-154` | P3 | `DRAFT` sin productor · dos «cierres» · `version` no incrementa · `LotStatus.CANCELLED` | `DRAFT` declarado, nunca asignado; `version` **sí** avanza en `update_event` y en `create_correction` (la matriz 360 lo daba por no incrementado: corregido por evidencia) | `docs/12 §4` fila 1; `docs/13` | «cierres» → **`AOD-08`** (pendiente) | **subconjunto `DRAFT`/`version`** en este tranche (mapa de transiciones + controles); resto **OPEN** |

**¿Misma raíz `R-135` + `R-143`?** Misma máquina de estados (`P-07`), mismo servicio (`review`), mismo camino de escritura
(`CORRECTED → approve`), misma decisión de propietario (`OD-17.b` nombra las dos: reenvío **y** segregación del
reenvío). **Causa raíz distinta** (mapa de transiciones vs comparador de segregación) y **spec distinta** (`GA-REM-006`
vs `GA-REM-007`). Por eso: **dos enmiendas, un tranche**, AC, pruebas, estado y evidencia **separados** por hallazgo.

## 2. Grafo de estados real (enumerado de `EventStatus`, sin estados nuevos)

```
                                     update (DRAFT·REGISTERED·RETURNED  +  REJECTED*)
                                        ▲
 create ──► REGISTERED ──submit──► PENDING_REVIEW ──start──► IN_REVIEW ──complete (1 nivel; BR-14)──► APPROVED
   DRAFT ─(sin productor; declarado)     ▲                       │  │                                    ▲
     └─ cancel ─┐                        │                       │  └─ complete (≥2 niveles) ──► CORRECTED ─┤ approve (BR-14 + R2*)
 REGISTERED ─ cancel ─┤                  │      return ◄─────────┘        ▲  ▲                    │ reject
                      ▼                  │        │                       │  │                    ▼
                  CANCELLED  ◄─ cancel ──┼── RETURNED ──correct (RR-01)───┘  │                 REJECTED ──correct*──► CORRECTED
                 (terminal)              │        └── resubmit* ────────────►│(PENDING_REVIEW)     └── resubmit* ──► PENDING_REVIEW
                                         │                                   │                     └── update* (editable)
 APPROVED ──consolidate──► CONSOLIDATED ──export──► SENT_TO_SAP ──► SAP_CONFIRMED (final)      [SAP_DEFERRED · OD-17.c]
                                                                 └► SAP_ERROR ──► correct/reprocess/REENVÍO EXPLÍCITO  [SAP_DEFERRED]
 * = transición que este tranche añade (R-135); el resto ya existe.
```

| Desde | Acción | Estado destino | Clase | Fuente |
|---|---|---|---|---|
| `DRAFT` | `update` | `DRAFT` | ALLOWED (sin productor; `R-154`) | `docs/12 §4` fila 1 |
| `DRAFT` | `submit` | — | **DENIED** (`400`: «solo registrados/devueltos/rechazados») | `docs/12 §2`: Borrador → Registrado → Enviado |
| `DRAFT` | `cancel` | `CANCELLED` | ALLOWED | `docs/12 §2` |
| `REGISTERED` | `update` · `submit` · `cancel` · `correct` | `REGISTERED` · `PENDING_REVIEW` · `CANCELLED` · `CORRECTED` | ALLOWED (existentes) | `docs/12`, `RR-01` |
| `PENDING_REVIEW` | `start` · `correct` · `cancel` | `IN_REVIEW` · `CORRECTED` · `CANCELLED` | ALLOWED (existentes) | — |
| `IN_REVIEW` | `return` (motivo ≥ 10) · `complete` · `approve` · `reject` (motivo ≥ 10) · `correct` | `RETURNED` · `APPROVED`/`CORRECTED` · `APPROVED` · `REJECTED` · `CORRECTED` | ALLOWED (existentes) | `docs/12 §2`; `CORRECTED` por `complete` = `R-142` (**OWNER_DECISION_REQUIRED** `AOD-17`, **no se toca**) |
| `RETURNED` | `update` | `RETURNED` | ALLOWED (existente) | `docs/12 §4` fila 5 |
| `RETURNED` | **`resubmit`** (`POST /operations/{id}/submit`) | **`PENDING_REVIEW`** | **ALLOWED*** (`R-135`) | `docs/12 §2` «Operador reenvía»; `OD-17.b` |
| `RETURNED` | `correct` | `CORRECTED` | ALLOWED (existente) | `RR-01`, `OD-17.b` |
| `REJECTED` | **`update`** · **`resubmit`** · **`correct`** | `REJECTED` · **`PENDING_REVIEW`** · **`CORRECTED`** | **ALLOWED*** (`R-135`, `OD-17.a`: no es terminal) | `docs/12 §4` fila 8; `OD-17.b` |
| `CORRECTED` | `approve` | `APPROVED` | ALLOWED con `BR-14` **+ `R2`** (aprobador ∉ {registrador, correctores, quien rechazó}) si `require_segregation` (`R-143`) | `docs/12 §6 R1-R2`; `OD-17.b`; `RR-03` |
| `CORRECTED` | `reject` (motivo) | `REJECTED` | ALLOWED (existente) | `docs/12 §6 R3` |
| `CORRECTED` | `update` · `submit` | — | **DENIED** (`400`) | control: el corregido espera al aprobador |
| `APPROVED` | `update` · `correct` · `submit` · `cancel` | — | **DENIED** (`400`; `cancel` ya lo deniega) | `AC-S10`; `docs/12 R5`; `BR-15/BR-16` (el aprobado solo cambia por reverso) |
| `CANCELLED` · `SAP_CONFIRMED` · `SAP_ERROR` · `CONSOLIDATED` · `SENT_TO_SAP` | `update` · `correct` · `submit` · `cancel` | — | **DENIED** (`update`/`correct`/`submit` ya; **`cancel` desde `SAP_CONFIRMED`/`SAP_ERROR`/`CANCELLED`: `R-140` PARTE A**) | `OD-17.a` terminales; `docs/12 R5`; `BR-15` |
| `APPROVED …` | reverso · reenvío SAP | — | **SAP_DEFERRED** (`R-136`, `OD-17.c`) | no se construye |

## 3. Matriz estado × acción (alcance seleccionado)

| ESTADO ACTUAL | ACCIÓN | ACTOR | PERMISO | ¿MOTIVO? | ¿CAMPOS MUTABLES? | DESTINO | VERSIÓN/HISTORIA | AUDITORÍA | EFECTO COLATERAL | INQUILINO | BU | INVÁLIDO DESDE | CONTRATO DE ERROR | HALLAZGO | AC | TEST |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `RETURNED` | resubmit | operador (quien registra) | `operations:create` | no (el motivo del revisor ya consta) | no (la edición es `PUT`, aparte) | `PENDING_REVIEW` | `audit_logs` (`previous_state=returned`, `new_state=pending_review`); `approval_actions.RETURNED` intacto | `AuditAction.UPDATED` (mapa existente) | ninguno: misma fila, saldo igual (el saldo cuenta todo salvo `CANCELLED`) | `get_event` (empresa) | `get_event` (unidad efectiva) + `exigir_unidad_operativa` (global: habilitada) | `DRAFT`, `CORRECTED`, `APPROVED`, terminales | `400` «Solo eventos registrados, devueltos o rechazados…» | `R-135` | `S01 S02 S03 U02 U03 R01 R05 R07` | `test_state_continuity.py::s01*, u0*` |
| `REJECTED` | resubmit | operador | `operations:create` | no | no | `PENDING_REVIEW` | ídem; `approval_actions.REJECTED` intacto | ídem | ninguno | ídem | ídem | ídem | `400` | `R-135` | `S01 S02 U02 U03 R01` | `::s01_rejected*` |
| `REJECTED` | update (`PUT`) | operador | `operations:update` | no | campos operativos (`OperationalEventUpdate`, sin `status`) | `REJECTED` | `version += 1`; `audit_logs` | `UPDATED` | ninguno hasta aprobar (el valor cambia en la fila; el saldo lo refleja como hoy con `RETURNED`) | `get_event` | ídem | `APPROVED`, terminales, `CORRECTED` | `400` | `R-135` | `S03 S12 D06` | `::s03_update_rejected*` |
| `REJECTED` | correct (`POST /corrections`) | quien tenga `corrections:correct` | `corrections:correct` | **sí** (≥ 5, `RR-01`) | 1 campo de la lista blanca | `CORRECTED` | `correction_logs` (original + corregido + `corrected_by_id`); `version += 1`; `audit_logs.CORRECTED` | `CORRECTED` | el valor cambia en la fila; ningún duplicado | empresa (**hoy solo esto**) | **hoy ninguna** → `predicado_de_evento` (404) + `exigir_unidad_operativa` | `APPROVED`, `CANCELLED`, SAP | `400` estado; `404` fuera de alcance | `R-135` + cadena BU | `S01 S03 S05 S06 S07 S08 R02 R03 R04` | `::s0*_correct*` |
| `RETURNED` | correct | ídem | ídem | sí | ídem | `CORRECTED` | ídem | ídem | ídem | ídem | ídem (**hoy ninguna**) | — | — | cadena BU (`AC-C05`) | `S06 S07` | `::s06*, ::s07*` |
| `CORRECTED` | approve | aprobador | `approvals:approve` | no | no | `APPROVED` | `approval_actions.APPROVED`; `audit_logs` | `APPROVED` | KPI/reportes pasan a contar el evento | `_get_event_for_approval` | `_ambito_de_unidad` | otros | `403 BR-14` si aprobador ∈ {registrador, **correctores**, **quien rechazó**} y `require_segregation` | **`R-143`** | `G01…G06` | `test_segregation_r143.py` |
| `APPROVED` | update · correct · submit | cualquiera | — | — | — | — | — | ninguna (denegación sin rastro de éxito) | — | — | — | siempre | `400` | control `S10` | `S10 D06` | `::s10*` |
| `CANCELLED` · `SAP_CONFIRMED` · `SAP_ERROR` | cancel | operador | `operations:create` (permiso: `AOD-18`, fuera) | fuera (`R-140` motivo: UI) | — | — | — | — | ninguno | `get_event` | ídem | siempre | `400` | **`R-140` PARTE A** | `S11` | `::s11_cancel*` |
| `DRAFT` | update / submit / cancel | operador | `operations:update` / `create` | — | operativos | `DRAFT` / **denegado** / `CANCELLED` | `version += 1` en `update` | `UPDATED` | ninguno | `get_event` | ídem | — | `submit`: `400` | `R-154` subconjunto | `D01…D05` | `::d0*` |
| cualquiera | `PUT` con `status` | cualquiera | — | — | — | — | — | — | — | — | — | — | `422` (`extra="forbid"`, `R-32`) | control | `S12`, `D03` | `::s12*` |

## 4. Semántica fijada (lecturas de las fuentes, no decisiones nuevas)

- **Reenvío** = un acto explícito del operador (`POST /operations/{id}/submit`) que devuelve el registro **a la cola
  de revisión** (`PENDING_REVIEW`). `docs/12 §2` lo dibuja como «Devuelto → Registrado (reenvía)» y «Registrado →
  Enviado»; `OD-17.b` como «→ (review)». Se toma la lectura de `OD-17` (una acción, un destino gobernado) y se
  documenta: no se crea ruta nueva, no se pasa por `REGISTERED`.
- **Motivo del revisor**: `return`/`reject` escriben `event.observations` **y** `approval_actions.observations` **y**
  `audit_logs.comments`. La edición del operador puede tocar `event.observations` (campo operativo); la historia
  estructurada (`approval_actions`, `audit_logs`) es la que se exige intacta (`AC-R01`).
- **Motivo de la corrección**: obligatorio (`RR-01`, `CorrectionCreate.reason ≥ 5`); del reenvío: **no exigido** por
  ninguna fuente (`docs/12 §4` fila 5 y 8 solo exigen el motivo al rechazar/anular).
- **`CORRECTED`** conserva su doble semántica (`R-142`, `AOD-17`): no se toca `complete_review`.
- **Aprobado inmutable**: `update`/`correct`/`submit` ya lo deniegan; se fija en AC y se sujeta con sensibilidad.
- **Sin doble efecto**: el saldo (`get_current_bird_balance`) cuenta la misma fila en todo el ciclo salvo
  `CANCELLED`; reenviar no crea filas ni movimientos → el efecto ocurre una vez, sea cual sea el estado (regla actual;
  no se inventa «efecto solo al aprobar»).
- **Concurrencia**: `resubmit` es idempotente en destino (dos reenvíos → `PENDING_REVIEW`); la carrera
  `approve`/`reject` es `R-166` (registrada, fuera).

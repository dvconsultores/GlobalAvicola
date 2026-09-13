# R-193 · FINDING — BR-18 CUENTA EL ORIGINAL Y LA CONTRAPARTIDA TRAS UN REVERSO (ACUMULADO 2n CONTRA LA OC)

| Campo | Valor |
|---|---|
| **Hallazgo canónico** | **R-193** (nuevo; `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`) |
| **Registro** | §1 G-04 · ficha §2 «R-193» |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` |
| **Clase (§9)** | `DATA_INTEGRITY` (E-01) |
| **Prioridad** | **P2** · **BLOQUEA SAP: SÍ (integridad)** — el control de la orden de compra (dato fuente SAP, `SapReference.quantity`) rechaza entregas legítimas y contabiliza el doble tras un reverso. |
| **Proceso** | P-01 / P-03 / P-06 (recepción de aves contra OC) · P-07/OD-19 (reverso) |
| **Dedup (§48)** | Buscado «BR-18», «oc_limit», «reverso» en `REMEDIATION_BACKLOG.md`, `specs/remediation/*` (GA-REM-035 = BR-18 acumulado, GA-REM-041 = reverso), `audit/ga-*`. `GA-REM-035` (R-169/GA-TD-014, CERRADA) fijó el acumulado con `≠ CANCELLED` **antes** de `OD-19`; `GA-REM-041 §3.4` definió la aritmética neta sólo para los saldos de aves/viables (`_suma_neta`) y no reconcilió BR-18; `R-176` (edición) no lo toca. ⇒ **hallazgo nuevo**. |
| **Origen** | Informe E (`E_domain_ledger.md §1.3` fila «Reverso de recepción con OC (BR-18)», candidato E-01). Evidencia de código (no se ejecutó runtime específico; el RED del diseño lo reproduce por API). |

## 1 · Síntoma

Recepción de `n` aves contra la OC `X` (`sap_document_ref = X`) aprobada ⇒ reverso solicitado y aprobado (`OD-19`): original y contrapartida quedan `REVERSED`, ambos con `sap_document_ref = X` y `bird_movements` de `n`. Una nueva recepción legítima de `n` contra `X` es rechazada: `400 BR-18` «La recepción de n elevaría lo recibido contra la OC X a 3n, por encima de las … ordenadas (ya recibidas: 2n)». Lo recibido real es **0**.

## 2 · Evidencia de código (verificada en HEAD)

| # | Fichero:línea | Qué hay |
|---|---|---|
| a | `backend/app/operations/validators.py:728-791` (`validate_oc_limit`) · **`:769-783`** | `acumulado_q = Σ BirdMovement.quantity` de eventos con `sap_document_ref == X`, `event_type == BIRD_RECEPTION`, `status.not_in([CANCELLED])` (+ `company_id`, `exclude_event_id`). **No excluye `REVERSED` ni las contrapartidas** (`Reversal.reversal_event_id`). |
| b | `backend/app/operations/validators.py:744-748` (docstring) | «Los ocho saldos de este mismo fichero excluyen exactamente `CANCELLED` y nada más, y se sigue ese precedente» — precedente **anterior** a `OD-19`; hoy los saldos de aves usan `_suma_neta`. |
| c | `backend/app/operations/validators.py:21-46` (`_suma_neta`) | Semántica vigente para aves/viables: natural (`≠ CANCELLED`, sin contrapartidas) − contrapartidas efectivas (`REVERSED`). |
| d | `backend/app/reversals/service.py:126-134` | La contrapartida **copia todas las columnas** del original salvo `id, status, version, idempotency_key, registered_by_id, reviewed_by_id, approved_by_id, event_date, event_time, observations, classified_at, created_at, updated_at` ⇒ **`sap_document_ref` se copia**. `:140-145`: copia `bird_movements` con las mismas cantidades. |
| e | `backend/app/reversals/service.py:215-216` | Al aprobar: `original.status = REVERSED; contrapartida.status = REVERSED`. |
| f | `backend/app/reversals/service.py:33-36` | `bird_reception ∈ ELEGIBLES_CON_SALDO_DE_AVES` ⇒ el escenario es alcanzable por producto. |
| g | `backend/app/operations/service.py:898-906` | `validate_oc_limit` se invoca para `BIRD_RECEPTION` y `BIRD_DISTRIBUTION` con `total_qty` del evento. |
| h | `backend/tests/test_purchase_order_receipt.py:106-258` (`test_t_014_01…07`) | Cubre parciales, exceso, cancelada (`_05` «una recepción cancelada deja de contar»), otra empresa, completar. **Ningún caso con reverso.** `tests/test_internal_reversal.py` no cubre BR-18. |

## 3 · Consecuencia numérica

OC de 1000. Recepción A = 400 (aprobada). Reverso de A aprobado ⇒ A y A' `REVERSED`, ambos 400 contra la OC. Acumulado = **800** (real: 0). Recepción B = 400 ⇒ total 1200 > 1000 ⇒ **400 BR-18**. Sólo cabrían 200 más; la orden queda «consumida» en 800 sin haber recibido nada. Con dos reversos, la OC queda bloqueada por completo.

## 4 · Causa raíz

`GA-REM-035` (acumulado `≠ CANCELLED`) y `GA-REM-041` (`REVERSED`, contrapartida con copia literal del original) se implementaron en tranches distintas; la segunda actualizó los saldos de aves (`_suma_neta`) pero no el acumulado de OC, que suma por `sap_document_ref` y no por lote. El docstring de BR-18 sigue citando un precedente ya superado.

## 5 · Impacto

- Entregas parciales legítimas rechazadas (P-01/P-03/P-06 recepción) tras cualquier reverso de recepción.
- Dato de conciliación contra la OC (fuente SAP) inflado ×2 por reverso: incompatible con la futura conciliación P-08.
- Rodeo hoy: ninguno por producto (no hay UI de reverso — `R-207` — pero el reverso es alcanzable por API y forma parte del contrato certificado `GA-REM-041`).

## 6 · Decisiones que se preservan

`OD-19` (ambos `REVERSED`, contrapartida copia del original) · `OD-04` (entregas parciales) · `GA-REM-035` (acumulado, sin tolerancia, sin cierre automático de la OC) · `R-130` · BR-01..BR-22 · `R-176` (edición: `exclude_event_id`).

## 7 · Paquete

`R-193_SPEC.md` · `R-193_CLARIFICATIONS.md` · `R-193_PLAN_CHECKLIST_TASKS.md` · `R-193_AC_MATRIX.md` · `R-193_RED_E2E_UAT_DESIGN.md`. Sin UI (no requiere UAT del propietario; certificación técnica + runtime por API). GA-REM: no asignado (siguiente libre `GA-REM-043`).

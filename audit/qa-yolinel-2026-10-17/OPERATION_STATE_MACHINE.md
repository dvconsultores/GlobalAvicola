# Máquina de estados del evento operativo — Revisión QA 2026-10-17

**Documento**: respuesta a **QA-010** («¿desde qué estado pueden ocurrir rechazado, cancelado, reversado?»)
**Fecha**: 2026-10-18 · **Baseline de código**: `83c9cd8` · **Spec asociada**: `specs/008-qa-yolinel-findings-remediation/spec.md` (FR-08 / AC-08.1)
**Carácter**: descripción del comportamiento **real** del backend; no propone cambios

Estados (`backend/app/operations/models.py` `EventStatus`): `draft` · `registered` · `pending_review` ·
`in_review` · `returned` · `corrected` · `approved` · `rejected` · `cancelled` · `consolidated` ·
`sent_to_sap` · `sap_confirmed` · `sap_error` · `reversed`.

**Nota sobre «quién»**: los servicios de revisión, corrección y reverso **no** comparan nombres de rol.
Lo que aplican es (a) el permiso del endpoint, (b) el alcance de empresa y unidad efectiva
(`404` fuera de alcance) y (c) la habilitación de la unidad (`403`) — `review/service.py`,
`_exigir_habilitacion` (`R-165` · `OD-19 §13`). La única exclusión nominal de persona es **BR-14**
(segregación de funciones). Por eso la columna «Quién» habla de **capacidades**, no de roles.

---

## 1. Transiciones admitidas

| Estado origen | Acción | Estado destino | Quién (permiso) | Regla |
|---|---|---|---|---|
| `draft` | Guardar como registrado | `registered` | Operador con alta en la unidad | Alta del evento; `BR-07` (lote de su empresa y activo), `BR-06` (fecha), `BR-19` (periodo abierto) — `operations/service.py:889` (`_apply_business_rules`) |
| `registered` / `returned` / `rejected` | Enviar a revisión | `pending_review` | Operador | `REENVIABLES` (`operations/service.py:88`); cualquier otro estado ⇒ `400` (`service.py:1394-1406`) |
| `registered` / `pending_review` / `in_review` / `returned` / `rejected` | Corregir | `corrected` | Operador o supervisor con escritura en la unidad | Lista `correctable` (`corrections/service.py:37-41`); escribe el valor y deja el registro pendiente de aprobación (`RR-01`) |
| `pending_review` | Iniciar revisión | `in_review` | Supervisor de revisión | `review/service.py:335-362`; solo desde `pending_review`, otro estado ⇒ `400` |
| `in_review` | Devolver con observaciones | `returned` | Supervisor de revisión | `review/service.py:363-391`; solo desde `in_review` |
| `in_review` | Completar revisión con **1 nivel** de aprobación | `approved` | Supervisor de revisión (**no** quien registró) | `review/service.py:392-458`; `approval_levels <= 1` ⇒ aprobar; exige **BR-14** (`_exigir_segregacion`, `service.py:35-75`) |
| `in_review` | Completar revisión con **2+ niveles** | `corrected` | Supervisor de revisión | `review/service.py:392-458`; queda a la espera del paso de aprobación |
| `corrected` (y `in_review` en nivel único) | Aprobar | `approved` —o `reversed` si es contrapartida— | Aprobador (**no** quien registró, **no** quien corrigió, **no** quien rechazó) | `review/service.py:562-604`; estado aprobable en `686-706`; **BR-14** en `35-75`; reverso en `188` (`efectuar_reverso_si_procede`) |
| `corrected` (y `in_review` en nivel único) | Rechazar (motivo obligatorio) | `rejected` | Aprobador | `review/service.py:605-665`; notifica al operador que registró (`RECORD_REJECTED`) |
| `draft` / `registered` / `pending_review` / `in_review` / `returned` / `corrected` / `rejected` | Cancelar | `cancelled` | Quien registró **u otro** usuario con permiso sobre la unidad | `NO_CANCELABLES` (`operations/service.py:89-91`), guarda en `cancel_event` (`service.py:1412-1439`) |
| `approved` | Solicitar reverso | (crea contrapartida en `pending_review`) | Usuario con escritura en la unidad | `reversals/service.py:88-170`; elegibilidad `99-125` |
| `approved` (contrapartida aprobada) | Aplicar compensación | `approved → reversed` **y** contrapartida `→ reversed` | Aprobador (misma aprobación) | `reversals/service.py:188-225`; saldos `BR-01`/`BR-04` revalidados |
| `approved` | Consolidar | `consolidated` | Proceso de integración | `integrations/sap/service.py:287-289` |

Estados **terminales**: `cancelled`, `reversed` (`OD-19`: lo revertido es terminal) y el ciclo SAP
(`sent_to_sap`, `sap_confirmed`, `sap_error`), que en la práctica solo se alcanza desde `consolidated`.

## 2. Diagrama (flujo humano)

```
                    +-------------------------------------------+
                    |                                           |
  draft --registrar--> registered --enviar--> pending_review --iniciar--> in_review
    |                     |  ^                     |                        |   |
    |                     |  |                     | (corregir)             |   | (devolver)
    |                     |  |                     v                        |   v
    |                     |  |                  corrected <--completar(2+)--+ returned
    |                     |  |                     |                           |
    |                     |  +---enviar(rechazado/ devuelto)-----------------+
    |                     |                        | (aprobar, 1 nivel desde in_review)
    |                     |                        v
    |                     |                     approved ----solicitar reverso----> contrapartida
    |                     |                        |                              (pending_review)
    |                     |                        |                                    |
    |                     |                        |<-----aprobar contrapartida----------+
    |                     |                        v                                    v
    |                     |                     reversed <--------------------------- reversed
    |                     |                        |
    |                     +----cancelar----> cancelled <----cancelar (desde draft/registered/
                                                          pending_review/in_review/returned/
                                                          corrected/rejected)
                      rejected --(corregir | enviar)--> corrected | pending_review
```

`approved` es el **único** estado desde el que se abre un reverso y el **primero** que ya no se
cancela. `consolidated` y los estados SAP quedan **fuera del flujo humano** (ver §5).

---

## 3. REJECT — el registro vuelve al operador como rechazado

- **Desde dónde**: `corrected` en el flujo multinivel y `in_review` en el de nivel único; el estado
  aprobable se comprueba en un solo punto (`review/service.py:686-706`, comentario «Can approve from
  CORRECTED or IN_REVIEW (single-level)»). Cualquier otro estado ⇒ `400` «El evento no está en estado
  aprobable».
- **Quién**: el aprobador. **BR-14** (`review/service.py:35-75`) impide rechazar a quien registró, a
  quien corrigió y a quien ya había rechazado ese mismo registro; la bandera
  `ApprovalStep.require_segregation` la activa o desactiva **por empresa** (`RR-03`,
  `service.py:77-90`; por defecto `True`).
- **Qué ocurre**: `status = rejected`, la observación pasa a `event.observations` y se escribe un
  `ApprovalAction(REJECTED)` (`review/service.py:605-665`). Se notifica a quien registró
  (`RECORD_REJECTED`), dentro de la misma transacción.
- **Es reenviable**: `rejected` está en `REENVIABLES` (`operations/service.py:88`) y en `correctable`
  (`corrections/service.py:38-39`); no es terminal (`OD-17.a`).
- **Observación de auditoría**: el rastro de transición de `reject` escribe el origen literal
  `"corrected"` (`review/service.py`, llamada a `audit_state_transition(..., "corrected", "rejected", ...)`),
  de modo que un rechazo desde `in_review` queda registrado con origen `corrected`. No altera la
  decisión efectiva (el estado vive en la fila), pero conviene que QA lo sepa antes de leer el log.

## 4. CANCEL — la anulación del registro

- **Desde dónde**: desde **todo** salvo `approved`, `consolidated`, `sent_to_sap`, `sap_confirmed`,
  `sap_error`, `cancelled` y `reversed` (`NO_CANCELABLES`, `operations/service.py:89-91`; guarda en
  `service.py:1420-1426`). El mensaje de error de esa guarda ya anticipa la política (`R-140` PARTE A):
  lo aprobado, lo consolidado, lo enviado/confirmado/rechazado por SAP y lo ya anulado **no se cancelan**.
- **Quién**: el servicio **no** compara al usuario con `event.registered_by_id`. Lo que exige es
  alcance de empresa y unidad efectiva y la unidad habilitada (`exigir_unidad_operativa`,
  `service.py:1414`). En la práctica: quien registró siempre puede; cualquier otro usuario con el
  permiso del endpoint y acceso a esa unidad también. (Ver `open_issues` del informe.)
- **Reglas de saldo**: si el evento es una **entrada** de saldo (recepción, nacimiento, recolección,
  recepción en incubadora) y ya tuvo salidas, la anulación se rechaza cuando dejaría el saldo negativo
  (`validate_retiro_de_entrada`, `service.py:1429-1432`, `AC-R173-05`). La fila del lote se bloquea
  antes de releer el estado: dos anulaciones concurrentes se serializan.
- **Qué ocurre**: `status = cancelled` + rastro de auditoría «Evento cancelado». `cancelled` es
  terminal: no se edita, no se envía, no se corrige, no se reasigna.

## 5. REVERSE — neutralizar lo aprobado sin borrar la historia

- **Desde dónde**: **solo** `approved` (`reversals/service.py:99-107`). Se rechaza `reversed` («ya fue
  revertido», `BR-16`), `consolidated` («no se reversa internamente; diferido», `OD-19 §11`) y cualquier
  otro estado («Solo un registro aprobado y no enviado a SAP se reversa»).
- **Tipos reversibles**: la unión de `ELEGIBLES_CON_SALDO_DE_AVES` y `ELEGIBLES_SIN_SALDO`
  (`reversals/service.py:30-41`). Fuera de esa unión el tipo «no es reversible».
- **Bloqueo R-161**: `BLOQUEADOS_POR_R161` (`reversals/service.py:42-46`) excluye **todo** el ciclo de
  huevo e incubación —`egg_collection`, `egg_classification`, `egg_reception_classification`,
  `egg_dispatch`, `egg_reception_hatchery`, `incubation_load`, `ovoscopy`, `transfer_to_hatcher`— con el
  mensaje «El reverso de huevos e incubación queda bloqueado por R-161 (`OD-19 §18`)».
- **Cómo funciona** (no es una transición directa):
  1. `solicitar` crea una **contrapartida**: mismo tipo y mismas cantidades y movimientos que el
     original, `event_date = hoy`, `registered_by_id = solicitante`, estado `pending_review`
     (`reversals/service.py:127-145`). El original **no** cambia de estado en este paso.
  2. La contrapartida recorre el flujo normal (revisión/aprobación); quien la solicita **no** puede
     aprobarla porque es su registrador (**BR-14**).
  3. Al aprobarse la contrapartida, `efectuar_reverso_si_procede` (`reversals/service.py:188-225`)
     bloquea el original, exige que siga `approved`, revalida `BR-01`/`BR-04` y marca **ambos**
     `reversed` en la misma transacción. Si algo falla, no queda nada aplicado.
- **Una sola vez**: `CONTRAPARTIDA_ACTIVA` (`reversals/service.py:48-52`) define qué estados de una
  contrapartida **bloquean** otra solicitud sobre el mismo original (`409` «ya tiene una solicitud de
  reverso activa o efectiva»). La contrapartida, además, no se corrige ni se reversa (`AC-RV06`).
- **Neto cero**: como los saldos son un agregado dinámico, original + contrapartida suman cero; la
  historia no se borra nunca.

## 6. Estados SAP (posteriores a `consolidated`, fuera del flujo humano)

`approved → consolidated` (consolidación, `integrations/sap/service.py:287-289`) y desde ahí
`sent_to_sap → sap_confirmed` / `sap_error`. Ningún usuario los produce desde la interfaz de
operaciones; son consecuencia de la integración. En esta ronda el **envío a SAP no está activo** y la
prueba de conexión real está programada para **2026-10-20**. `consolidated`, `sent_to_sap`,
`sap_confirmed`, `sap_error` y `reversed` no se cancelan.

# `R-166` · Matriz de concurrencia de la decisión de revisión (`R166_REVIEW_DECISION_CONCURRENCY_MATRIX`)

**WAVE B · tranche 13 · pre-flight** · 2026-09-10 · baseline `a93d4d1` · hallazgo `R-166` (registrado P3; **normalizado P2**, §6) ·
spec gobernante `GA-REM-007` (segregación y centralización de las reglas de aprobación) → enmienda B · **sin decisión del propietario** (§5).

## 1. Hallazgo exacto

> `R-166` · P3 · «`approve` y `reject` sobre el mismo evento `CORRECTED` no se excluyen (sin bloqueo de fila; el último `flush` gana)» ·
> `review/service.py:423-470` · `REMEDIATION_BACKLOG.md:1072` (alta en el tranche 5, `R-135-R-143-STATE-CONTINUITY-EVIDENCE`).

## 2. Fila autoritativa de la decisión (`§32`)

| Candidata | ¿Es la decisión efectiva? | Por qué |
|---|---|---|
| **`operational_events`** (la fila del evento) | **sí** | `status` es la decisión efectiva (`APPROVED`/`REJECTED`); `approved_by_id` la firma; todo lo demás se deriva de ella. `GA-REM-006-A §A.2` modela `P-07` como transiciones de **esa** fila |
| `approval_actions` | no | **historia** de la acción (`ActionType`); no gobierna el estado ni se consulta para decidir |
| `review_batches` | no | agrupación de la cola de revisión |
| `lots` (saldo) | **no** | `R-161`/`R-130` bloquean el lote para el **saldo**; la decisión de revisión no toca saldos (`§33`: R-166 ≠ R-161) |

→ La serialización debe ocurrir sobre `operational_events.id`, con la misma primitiva ya usada en el repositorio: `_bloquear_original`
(`reversals/service.py:74`, `SELECT … FOR UPDATE` + `populate_existing`, «es lo que serializa dos solicitudes o dos aprobaciones»).

## 3. Punto en que la decisión se hace efectiva (`§35`) y secuencia actual

```
ACTUAL (approve y reject)
  _get_event_for_approval(event_id)
      SELECT … WHERE id, company_id, predicado_de_unidad        ← sin FOR UPDATE
      _exigir_habilitacion (R-165 · OD-16)
      if status not in (CORRECTED, IN_REVIEW): 400              ← comprobación sobre estado POSIBLEMENTE OBSOLETO
  [approve] _exigir_segregacion (BR-14)
  event.status = APPROVED / REJECTED ; flush
  efectuar_reverso_si_procede (solo approve)                     ← este sí bloquea su original (GA-REM-041)
  ApprovalAction(...) ; flush ; refresh
  audit_state_transition(...)
  [reject] notificaciones (OD-07/OD-08)
```

Dos peticiones concurrentes leen `CORRECTED`, **ambas** superan la comprobación y **ambas** escriben: el `status` final lo fija la última en confirmar,
pero la historia, la auditoría y las notificaciones quedan duplicadas o contradictorias.

## 4. Reproducción real por API (`§36`-`§39`) — sondeo del pre-flight sobre `a93d4d1`

Escenario: empresa A, unidad `breeder` ON, evento en `CORRECTED`, dos revisores distintos y autorizados (`approvals:approve` / `approvals:reject`),
ninguno es el registrador (`BR-14` satisfecha), `asyncio.gather` de dos peticiones HTTP independientes.

```
approve || reject   →  approve=200 · reject=200
                       estado final = APPROVED (approved_by_id = revisor 1)
                       approval_actions = APPROVED(1) + REJECTED(1)        ← dos decisiones efectivas registradas
                       audit            = APPROVED(1) + REJECTED(1)        ← dos auditorías de ÉXITO
                       notificaciones   = 1  «registro rechazado» al operador  ← de un evento que quedó APROBADO

approve || approve  →  200 · 200
                       approval_actions = APPROVED(2)
                       audit            = APPROVED(2)
```

Defecto confirmado en su forma más grave: **historia incoherente + efecto lateral (notificación) de la decisión que no prevaleció**. (Sondeo temporal,
retirado; el rojo formal lo repite como prueba versionada con `reject || reject` incluido.)

## 5. Matriz de superficies de decisión (`§34`)

| Superficie | Estado revisable | Ruta | Fila autoritativa | ¿Bloqueo hoy? | ¿Bloqueo antes de leer el estado? | ¿Relectura bajo bloqueo? | ¿`ApprovalAction`? | ¿Auditoría? | ¿Notificación? | ¿Efecto de saldo/reverso? | Segunda decisión hoy | Resultado exigido | Regla de actor | Inquilino | Unidad | RBAC | AC | Prueba |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `POST /approvals/approve` | `CORRECTED` · `IN_REVIEW` | `ApprovalService.approve` | `operational_events` | **no** | no | no | sí (`APPROVED`) | sí (`APPROVED`/`REVERSED`) | no | **sí** si es contrapartida de reverso (`efectuar_reverso_si_procede`, con su propio bloqueo) | **se aplica** (200) | `400` (estado no aprobable) tras relectura | `BR-14` (`GA-REM-007-A`) | `company_id` en la consulta | `_ambito_de_unidad` + `_exigir_habilitacion` (`R-165`) | `approvals:approve` | `AC-R166-01…08` | `REVI-` |
| `POST /approvals/reject` | ídem | `ApprovalService.reject` | ídem | **no** | no | no | sí (`REJECTED`) | sí (`REJECTED`) | **sí** (`RECORD_REJECTED`, `OD-07`/`OD-08`) | no | **se aplica** (200) | `400` tras relectura | sin segregación propia (no se inventa, `§40`) | ídem | ídem | `approvals:reject` | ídem | `REVI-` |
| `POST /review/complete/{id}` | `IN_REVIEW` | `ReviewService.complete_review` | ídem | **no** | no | no | no | sí | no | sí (mismo camino a `APPROVED` con un nivel) | ídem | ídem | `BR-14` | ídem | ídem | `review:review` | `AC-R166-09` | `REVI-` |
| `POST /review/start/{id}` · `POST /review/return/{id}` | `PENDING_REVIEW` · `IN_REVIEW` | `start_review` · `return_to_operator` | ídem | **no** | no | no | no | sí | sí (devolución) | no | ídem | ídem | — | ídem | ídem | `review:review` | `AC-R166-10` | `REVI-` |
| `POST /approvals/batch-approve` · `batch-reject` | ídem | `batch_approve`/`batch_reject` | ídem (una por evento) | no | no | no | sí | sí | sí | sí | ídem | hereda el contrato (llaman a `approve`/`reject`) | ídem | ídem | ídem | `review:review` | control |
| aprobación de la **contrapartida de reverso** | `CORRECTED`/`IN_REVIEW` | mismo `approve` | evento contrapartida **+** original (`_bloquear_original`) | **parcial**: el original sí se bloquea (`GA-REM-041`) | n/a | sí, para el original | sí | sí | no | sí | el segundo falla en `BR-16` (el original ya está `REVERSED`) pero **tras** haber escrito estado e historia | una sola decisión efectiva antes de llegar ahí | `OD-19` | ídem | ídem | ídem | `AC-R166-11` | `REVI-` |

## 6. Severidad normalizada (`§26` del método)

| Criterio | Evidencia |
|---|---|
| ¿Dos decisiones efectivas sobre el mismo ciclo? | **sí** (`approval_actions` APPROVED+REJECTED; APPROVED×2) |
| ¿Doble auditoría de éxito? | **sí** |
| ¿Efecto lateral de la decisión perdedora? | **sí** (notificación de rechazo sobre evento aprobado) |
| ¿Afecta saldos o población? | **no** (`R-161`/`R-130` intactos; el reverso tiene su propio bloqueo) |
| ¿Rompe inquilino/unidad/RBAC? | no |

→ **`P2`** (era P3). Integridad de la decisión de revisión y de la auditoría, sin daño de saldo.

## 7. Puerta de decisión (`§48`)

Ninguna. El estado terminal de la segunda petición ya está gobernado por `GA-REM-006-A §A.2` (mapa de transiciones: desde `APPROVED`/`REJECTED` no se
aprueba ni se rechaza) y por el contrato de error vigente: `_get_event_for_approval` **ya** responde `400` «El evento no está en estado aprobable (actual: …)».
La corrección no inventa semántica: hace que esa comprobación se evalúe sobre el estado **posterior al bloqueo**. Sin código de error nuevo, sin idempotencia nueva.

## 8. Contrato exigido (`§35`, `§71`-`§74`)

```
autenticar → empresa efectiva → cargar el evento (empresa + unidad alcanzable)  ← puede leerse antes del bloqueo (autorización)
  → _exigir_habilitacion (R-165 · OD-16)
  → BLOQUEAR operational_events.id  (SELECT … FOR UPDATE, populate_existing)
  → RELEER status
  → validar la transición contra el estado post-bloqueo   ← aquí muere la segunda decisión
  → [approve] BR-14
  → aplicar la decisión (status, approved_by_id)
  → efectos gobernados (reverso, ApprovalAction, auditoría, notificaciones)
  → confirmar
```

Invariante: `COUNT(decisiones efectivas por ciclo de revisión) == 1`. La historia de intentos fallidos no existe hoy (una denegación no escribe
`ApprovalAction`) y no se crea.

## 9. AC → prueba (contrato completo en `GA-REM-007` enmienda B)

| AC | Criterio | Prueba (`tests/test_review_decision_concurrency.py`, prefijo `REVI-`) |
|---|---|---|
| `AC-R166-01` | `approve \|\| reject` → exactamente una decisión efectiva: un `ApprovalAction`, una auditoría de éxito, estado coherente con ella; **cero** notificaciones de rechazo si ganó la aprobación | `_01` |
| `AC-R166-02` | `approve \|\| approve` → un `ApprovalAction` APPROVED, una auditoría; la segunda `400` | `_02` |
| `AC-R166-03` | `reject \|\| reject` → un `ApprovalAction` REJECTED, una auditoría, **una** notificación | `_03` |
| `AC-R166-04` | la fila del evento se bloquea antes de releer el estado (probado por el resultado: la segunda espera y ve el estado terminal) | `_01…_03` |
| `AC-R166-05` | la segunda petición revalida contra el estado post-bloqueo y responde `400` con el estado real | `_01…_03` |
| `AC-R166-06` | efectos exactamente una vez: `approval_actions`, `audit_logs` de éxito, `notifications` | `_01…_03` |
| `AC-R166-07` | `BR-14` intacta: el registrador no aprueba (control) | `_07` |
| `AC-R166-08` | control secuencial: aprobar y después rechazar el mismo evento → `400` (sin cambio de contrato) | `_08` |
| `AC-R166-09` | `complete_review` concurrente con `approve` → una sola transición a `APPROVED` | `_09` |
| `AC-R166-10` | `start_review \|\| return` (o `start \|\| start`) → una sola transición | `_10` |
| `AC-R166-11` | contrapartida de reverso: `approve \|\| approve` → un solo reverso efectivo (original `REVERSED` una vez), `OD-19` intacto | `_11` |
| `AC-R166-12` | seguridad: otra empresa → `404`; unidad apagada → `403` (`R-165`); sin permiso → `403`; global sin contexto → cerrado | `_12` |
| `AC-R166-13` | sin bloqueo de saldos: el lote no se serializa por revisar (`R-161`/`R-130` intactos) | `_13` (control) |

Sensibilidad: `R166-S1` (quitar el bloqueo) · `R166-S2` (bloquear **después** de leer el estado) · `R166-S3` (bloquear pero validar contra el estado previo) ·
`R166-S4` (quitarlo solo del camino de aprobación) · `R166-S5` (solo del de rechazo) · `R166-S6` (permitir el efecto lateral duplicado: notificación/`ApprovalAction`) ·
`R166-S7` (`BU` apagada) · `R166-S8` (inquilino).

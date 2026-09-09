# GA-REM-006 — CORRECCIONES E INTEGRIDAD DEL DATO

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-006` · **Tipo** `DATA INTEGRITY + BUSINESS WORKFLOW SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** |
| **Estado** | `SPEC_READY` — `RC-01` resuelto por evidencia el 2026-09-03 (regla `RR-01`, ver `audit/remediation/REQUIREMENT_CONFLICT_RESOLUTION.md §3`) |
| **Dependencias** | `GA-REM-001` · `GA-REM-014` · coordinada con `GA-REM-002` (quién corrige) y `GA-REM-011` (la pantalla está rota) |
| **Hallazgos** | P0-2 · P0-5 · `GA-TD-002` · `GA-REQ-025` (`ROTO`) · BR-09 |
| **Revalidado** | 2026-09-03 — `corrections/service.py` contiene `event.status = CORRECTED` y **ningún `setattr` sobre el evento** |

## Problema
Una corrección aprobada queda registrada administrativamente pero **no modifica el dato**. `create_correction` crea el `CorrectionLog` con `field_name`, `original_value` y `corrected_value`, cambia el estado del evento a `CORRECTED` y audita — sin escribir jamás el valor corregido sobre el evento ni sobre sus submovimientos.

Consecuencia en cadena: el dato erróneo es el que se aprueba, el que alimenta los KPI y el que se consolida hacia SAP. El sistema queda con **dos verdades divergentes**.

## Evidencia
| Ítem | Ruta |
|---|---|
| Creación del log sin aplicación del valor | `backend/app/corrections/service.py:37-58` |
| Estados corregibles | `corrections/service.py:33` — `REGISTERED, PENDING_REVIEW, IN_REVIEW, RETURNED` |
| Pantalla de corrección rota (422) | `frontend/src/pages/review/CorrectionForm.tsx:27` |
| El campo por defecto del formulario es `observations` | `CorrectionForm.tsx:18` |
| KPI calculados sobre eventos aprobados | `backend/app/reports/service.py:29-38` |

## Comportamiento actual
```
POST /corrections {event_id, field_name, original_value, corrected_value, reason}
  → valida compañía y estado corregible
  → INSERT CorrectionLog
  → event.status = CORRECTED
  → audit_correction()
  ⇒ el campo del evento conserva el valor erróneo
```

## Comportamiento esperado — pendiente de decisión
```
evento original → solicitud de corrección → revisión → aprobación/rechazo
  → APLICACIÓN EFECTIVA sobre el dato
  → audit trail con original y corregido
  → recálculo de derivados
  → consolidación
```

## REQUIREMENT_CONFLICT abierto — `RC-01`

Las fuentes no coinciden sobre si la corrección es **inmediata** o **sujeta a aprobación**:

| Fuente | Dice |
|---|---|
| `spec.md §4.10` | «Corrección auditada (valor original + corregido + motivo)» — no define si requiere aprobación |
| `spec.md BR-09` | «Toda corrección es auditada (original + corregido)» — habla de auditoría, no de aplicación |
| `docs/12-approval-workflow.md` | describe corrección dentro del flujo de revisión |
| Código actual | aplica el cambio de estado inmediatamente, sin aprobación, y **no aplica el valor** |
| Documentación del cliente | no define el flujo de corrección |

**Decisión requerida antes de implementar** (Art. 18 de la constitución). Alternativas:

| Opción | Descripción | Impacto |
|---|---|---|
| **A** | La corrección se aplica inmediatamente al registrarla; el `CorrectionLog` conserva el original | simple; coherente con el estado actual; el revisor asume la responsabilidad |
| **B** | La corrección se solicita, un aprobador la aprueba y solo entonces se aplica | más control; exige nuevo estado y nueva UI; mayor alcance |
| **C** | Aplicación inmediata + posibilidad de reverso auditado | intermedia; se apoya en la tabla `reversals` hoy huérfana |

Hasta resolver `RC-01`, esta spec permanece en `SPEC_DRAFT`.

## Alcance (común a las tres opciones)
1. Aplicar efectivamente el valor corregido sobre el campo destino.
2. **Mapa campo → destino**: qué campos son corregibles y en qué tabla viven (`operational_events`, `bird_movements`, `egg_movements`, `feed_movements`, `hatchery_params`, `inspection_details`).
3. Validación del valor corregido con las mismas reglas que la captura original.
4. Recálculo o invalidación de derivados afectados (saldos, KPI).
5. Preservación del original en `CorrectionLog` (ya funciona).
6. Reparación de la pantalla (coordinada con `GA-REM-011`).

## Fuera de alcance
Flujo de reverso post-SAP (BR-16, `reversals`) — es backlog `GA-REM-019` salvo que `RC-01` se resuelva por la opción C · corrección masiva · corrección de eventos ya enviados a SAP (BR-15 lo impide y debe seguir impidiéndolo).

## Reglas de negocio afectadas
`BR-09` (corrección auditada), `BR-15` (registros enviados a SAP no se editan directamente) y las reglas de validación de cada campo corregible, que deben reaplicarse.

## Backend afectado
`corrections/service.py` (aplicación del valor, mapa de campos), `corrections/schemas.py` (posible tipado del campo destino), `operations/validators.py` (reutilización de validaciones).

## Frontend afectado
`pages/review/CorrectionForm.tsx` — hoy no carga (`limit=200` → 422) y ofrece un campo libre por defecto. Debe presentar los campos realmente corregibles del evento.

## Base de datos afectada
**Posible**: columna en `correction_logs` que identifique el submovimiento destino cuando el campo no pertenece a `operational_events`. Decisión ligada al mapa de campos.

## Seguridad
Quién puede corregir se define en `GA-REM-002` (`review:correct`). Esta spec **no** debe permitir corregir sin ese permiso.

## Compatibilidad
Las correcciones ya registradas en producción **no aplicaron su valor**. Se requiere decidir si se reprocesan retroactivamente. Se coordina con la auditoría de datos del paso 8 del programa.

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| Campo no corregible | rechazo con lista de campos admitidos |
| Valor corregido que viola una regla de negocio (p. ej. mortalidad > saldo) | rechazo; la corrección no puede saltarse las validaciones |
| Evento en estado enviado a SAP | rechazo por BR-15 |
| Dos correcciones concurrentes sobre el mismo campo | control de concurrencia mediante `OperationalEvent.version` |
| Corrección sobre un campo de submovimiento con varias filas | debe identificar la fila destino sin ambigüedad |
| Corrección que cambia una cantidad de la que dependen saldos posteriores | recálculo o rechazo explícito, nunca inconsistencia silenciosa |
| Motivo con menos de 5 caracteres | rechazo (el frontend ya lo valida; el backend debe hacerlo también) |

## Acceptance Criteria (aplicables a la opción que resuelva `RC-01`)

**AC01 — El valor se aplica**
```
Given un evento de mortalidad con quantity=10 en estado registered
When  se registra una corrección de quantity a 8 con motivo válido
Then  el evento (o su submovimiento) pasa a quantity=8
And   el CorrectionLog conserva original_value=10 y corrected_value=8
```
**AC02 — Los derivados se recalculan**
```
Given el escenario de AC01 sobre un lote con saldo 990
When  la corrección se aplica
Then  el saldo del lote pasa a 992
```
**AC03 — La corrección respeta las reglas de negocio**
```
Given un lote con saldo de 100 aves
When  se intenta corregir una mortalidad a 500
Then  la corrección se rechaza con el identificador BR-01
And   ni el evento ni el CorrectionLog se modifican
```
**AC04 — Campos no corregibles**
```
Given un evento cualquiera
When  se intenta corregir un campo fuera del mapa de campos corregibles
Then  la respuesta es 400 con la lista de campos admitidos
```
**AC05 — BR-15 se mantiene**
```
Given un evento en estado sent_to_sap
When  se intenta corregirlo
Then  la respuesta es 400 con el identificador BR-15
```
**AC06 — Auditoría completa**
```
Given una corrección aplicada
When  se consulta la línea de tiempo del evento
Then  aparece la corrección con usuario, fecha, campo, valor original, valor corregido y motivo
```
**AC07 — Motivo obligatorio en el servidor**
```
Given una corrección con motivo vacío o de menos de 5 caracteres
When  se envía directamente al API sin pasar por la interfaz
Then  la respuesta es 400
```
**AC08 — Concurrencia**
```
Given dos correcciones simultáneas sobre el mismo campo del mismo evento
When  ambas se procesan
Then  la segunda falla por conflicto de versión, o se aplica de forma determinista y auditada
```
**AC09 — Permiso exigido**
```
Given un usuario sin permiso review:correct
When  hace POST /api/v1/corrections
Then  recibe 403
```

## Tests requeridos
`T-006-01..09` correspondientes a AC01–AC09 (integración) + `T-006-10` E2E: supervisor corrige un valor desde la interfaz y el listado refleja el valor corregido.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Aplicar el valor sin revalidar abre un bypass de todas las reglas | AC03 lo cubre explícitamente |
| El mapa de campos corregibles queda incompleto y bloquea correcciones legítimas | se deriva de los 25 tipos de evento y se revisa en la spec |
| Reprocesar correcciones históricas corrompe saldos | decisión explícita en la auditoría de datos; por defecto **no** se reprocesa |

## Rollback lógico
Reversible por commit. Las correcciones aplicadas **no** se revierten automáticamente: el `CorrectionLog` permite reconstruir el estado anterior manualmente.

## Definition of Done
- [ ] `RC-01` resuelto y documentado · [ ] Mapa de campos corregibles versionado · [ ] AC01–AC09 verificados · [ ] Tests en verde · [ ] Decisión sobre datos históricos documentada · [ ] Certification report

---

# Enmienda A · un registro devuelto o rechazado sigue vivo — continuidad de estados de `P-07` (2026-09-09 · WAVE B tranche 4)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-006-A` · `BUSINESS WORKFLOW / STATE MACHINE` · **Estado** **`CERTIFIED`** (frontera técnica, 2026-09-09; E2E `BLOCKED_RUNTIME`) · evidencia `R-135-R-143-STATE-CONTINUITY-EVIDENCE.md` |
| **Hallazgos seleccionados** | **`R-135`** (P1, `H360-P03`/`D09`): `RETURNED` no se reenvía; `REJECTED` es terminal · **`R-140` PARTE A** (guarda de estados de `cancel`: `SAP_CONFIRMED`/`SAP_ERROR`/`CANCELLED`) · **`R-154` subconjunto** (`DRAFT` en el mapa de transiciones; semántica de `version`) · cadena inquilino/unidad en `POST /corrections` (`AC-C05`, `OD-16.e/f`, hoy solo empresa) |
| **Porciones excluidas** | `R-140` motivo obligatorio del `cancel` (el cliente llama la ruta **sin cuerpo**, `operations.service.ts:47`: exige vertical de UI, fuera de alcance) y permiso «solo administrador» (**`AOD-18`**) → **OPEN** · `R-154` dos «cierres» (**`AOD-08`**) y `LotStatus.CANCELLED` → **OPEN** · `R-142` (`CORRECTED` doble semántica, **`AOD-17`**): `complete_review` **no se toca** · `R-165`, `R-166` (registrados en el pre-flight) |
| **Fuentes** | `docs/12 §2` (Devuelto → «Operador reenvía»; Rechazado → «Operador reenvía (corregido)»; Borrador → Registrado/Anulado), `§4` filas 1, 5, 8, 13, `§6 R3-R5`, `§8`, `§11` · `spec.md §4.10-4.11` · `BR-09`, `BR-15`, `BR-16` · `RR-01` · **`OD-17.a/b`** (vigente) · `OD-17.c` (SAP: **diferido**) · `OD-09/OD-14/OD-16` + `GA-REM-040-G/H` (cadena de escritura productiva) |
| **Matriz previa** | `R135_R143_STATE_CORRECTION_MATRIX.md` (grafo §2, matriz §3, semántica §4) |
| **Relación con `R-143`** | misma máquina de estados y mismo servicio; **raíz distinta** → `GA-REM-007` enmienda A, mismo tranche, AC/pruebas/estado separados |

## A.1 Estados actuales y destino

`EventStatus` no cambia (sin migración, sin renombrar): `DRAFT`, `REGISTERED`, `PENDING_REVIEW`, `IN_REVIEW`, `RETURNED`,
`CORRECTED`, `APPROVED`, `REJECTED`, `CONSOLIDATED`, `SENT_TO_SAP`, `SAP_CONFIRMED`, `SAP_ERROR`, `CANCELLED`. Clases
(`OD-17.a`): **devolución interna** = `RETURNED`, `REJECTED` (vivos); **futuro SAP** = `SAP_ERROR` (diferido); **terminal**
= `CANCELLED`, reverso, cierre. Grafo completo en la matriz §2.

## A.2 Transiciones que esta enmienda añade o fija

| Desde | Acción (ruta existente) | Destino | Regla |
|---|---|---|---|
| `RETURNED` · `REJECTED` | **reenvío** = `POST /operations/{id}/submit` (`operations:create`) | `PENDING_REVIEW` | acto explícito del operador; sin motivo; `audit_logs` con `previous_state`/`new_state`; `approval_actions` del revisor intactos |
| `REJECTED` | `PUT /operations/{id}` (`operations:update`) | `REJECTED` | mismos campos que `RETURNED` (`OperationalEventUpdate`, sin `status`); `version += 1` |
| `REJECTED` | `POST /corrections` (`corrections:correct`) | `CORRECTED` | `RR-01`: valor aplicado, original conservado, motivo ≥ 5, `version += 1`; sigue el camino existente al aprobador |
| `RETURNED` · `REJECTED` · cualquier corregible | `POST /corrections` | — | **cadena de escritura productiva**: evento resuelto con `predicado_de_evento` (actor: `404` fuera de su alcance) + `exigir_unidad_operativa` (global: unidad habilitada o `403`; sin contexto `403`) |
| `CANCELLED` · `SAP_CONFIRMED` · `SAP_ERROR` | `POST /operations/{id}/cancel` | — | **denegado** `400` (`R-140` PARTE A); permiso y motivo fuera |
| `DRAFT` | `submit` | — | denegado `400` (`docs/12 §2`); `update`/`cancel` como hoy (`R-154`) |
| `CORRECTED` | `update` · `submit` | — | denegado `400` (control) |
| `APPROVED` (y posteriores) | `update` · `correct` · `submit` · `cancel` | — | denegado (control, `AC-S10`); solo reverso (`R-136`, diferido) |

**Mapa explícito, no `setattr` de estado**: `submit_to_review` valida `event.status ∈ {REGISTERED, RETURNED, REJECTED}`;
`update_event` `∈ {DRAFT, REGISTERED, RETURNED, REJECTED}`; `create_correction` `∈ {REGISTERED, PENDING_REVIEW,
IN_REVIEW, RETURNED, REJECTED}`; `cancel_event` `∉ {APPROVED, CONSOLIDATED, SENT_TO_SAP, SAP_CONFIRMED, SAP_ERROR,
CANCELLED}`. El cliente nunca fija `status` (`R-32`, `extra="forbid"`; lista blanca de `campos_corregibles`).

## A.3 Actores, permisos, inquilino, unidad

Sin nombres de rol: `operations:create` reenvía, `operations:update` edita, `corrections:correct` corrige,
`approvals:*` decide. Toda transición es `TENANT_SCOPED` (`OD-14.c`): `get_event`/`predicado_de_evento` para el
actor de empresa; la autoridad global situada, sin concesión, sobre unidad **habilitada** (`OD-16.e/f`, `G.3`/`H.5`);
sin contexto → fallo cerrado. Administrador de Accesos y Contraloría (rol de solo lectura/control) → `403` por RBAC.

## A.4 Motivos, historia, auditoría, efectos

- Motivo del revisor (`return` ≥ 10, `reject` ≥ 10): **se preserva** en `approval_actions` y `audit_logs`; la
  corrección/reenvío no lo borra ni lo sobrescribe allí. Motivo de corrección: **obligatorio** (`RR-01`). Motivo del
  reenvío: **no exigido** (ninguna fuente lo pide).
- Historia: `correction_logs` (original + corregido + `corrected_by_id`), `audit_logs` (`previous_state`, `new_state`,
  actor, fecha, comentarios), `version` avanza en edición y corrección. **No se inventa** un sistema de versiones nuevo.
- Efectos: el saldo cuenta la misma fila en todo el ciclo salvo `CANCELLED`; el reenvío no crea filas ni movimientos
  (efecto **una vez**). Denegación = cero cambios, cero auditoría de éxito.
- `CORRECTED` no se convierte en `APPROVED` sin acto del aprobador (`AC-U01`); el reenvío vuelve a la cola de revisión.

## A.5 Criterios de aceptación

### Continuidad (`AC-S`)

| `AC` | Criterio | Contrato |
|---|---|---|
| `AC-S01` | evento `RETURNED` **y** evento `REJECTED` admiten reenvío por su operador → `PENDING_REVIEW` (hoy: `RETURNED` `400`; `REJECTED` `400`) | `200` |
| `AC-S02` | `REJECTED` no es terminal: editable (`PUT`) y corregible (`POST /corrections`) por actor autorizado | `200` · `201` |
| `AC-S03` | la corrección autorizada de `RETURNED`/`REJECTED` produce `CORRECTED` (camino gobernado al aprobador) | `201`, `status=corrected` |
| `AC-S04` | actor sin `corrections:correct` → `403`; actor sin `operations:create` no reenvía → `403` | RBAC |
| `AC-S05` | actor de empresa `B` no corrige ni reenvía el evento de `A` → `404` (anti-enumeración) | `404` |
| `AC-S06` | actor de `A` sin la unidad del evento (habilitada, no concedida) → `POST /corrections` `404`; reenvío `404` | `404` |
| `AC-S07` | unidad **apagada** para la empresa: actor con concesión histórica → `404`; autoridad global situada → corrección `403`, reenvío `403` | `404` / `403` |
| `AC-S08` | permiso RBAC ausente → `403` antes de tocar el estado | `403` |
| `AC-S09` | estado origen inválido → `400` (reenvío desde `CORRECTED`, `APPROVED`, `CANCELLED`; corrección desde `APPROVED`, `CANCELLED`, `SAP_*`) | `400` |
| `AC-S10` | `APPROVED` no admite `PUT`, corrección ni reenvío | `400` |
| `AC-S11` | `CANCELLED`, `SAP_CONFIRMED`, `SAP_ERROR` no admiten reenvío, corrección ni **cancelación** (`R-140` PARTE A) | `400` |
| `AC-S12` | ni la corrección ni el reenvío alteran `company_id`, `lot_id`-cadena, `registered_by_id`; `status` en `PUT` → `422`; `status`/`company_id` en corrección → `400` | `422` / `400` |

### Motivo y auditoría (`AC-R`)

| `AC` | Criterio |
|---|---|
| `AC-R01` | el motivo del revisor (`approval_actions.RETURNED`/`REJECTED`, `audit_logs`) permanece tras corrección y reenvío |
| `AC-R02` | corrección sin motivo → `422`; motivo < 5 → `422` (`RR-01`, `GA-REM-006 AC07`) — control |
| `AC-R03` | motivo en blanco (espacios) → rechazado (`422`/`400`) |
| `AC-R04` | la corrección registra `corrected_by_id` y `created_at`; el reenvío registra actor y fecha en `audit_logs` |
| `AC-R05` | `audit_logs` del reenvío conserva `previous_state` (`returned`/`rejected`) y `new_state` (`pending_review`) |
| `AC-R06` | una corrección/reenvío denegado no deja auditoría `APPROVED`/`CORRECTED`/`UPDATED` de éxito |
| `AC-R07` | denegación → cero cambios de estado, valor, `version`, `correction_logs`, saldo |

### `DRAFT` (`AC-D`, `R-154` subconjunto)

| `AC` | Criterio |
|---|---|
| `AC-D01` | `DRAFT` editable por actor con `operations:update` de su empresa/unidad (fila sembrada: no hay productor) |
| `AC-D02` | `DRAFT` de otra cadena → `404`; sin permiso → `403` |
| `AC-D03` | `PUT` con `status` → `422`; `DRAFT` nunca pasa a `APPROVED` por edición |
| `AC-D04` | `submit` desde `DRAFT` → `400` (el borrador se registra primero: `docs/12 §2`) |
| `AC-D05` | `version` avanza en cada `PUT` y en cada corrección (semántica vigente, documentada) |
| `AC-D06` | `APPROVED` no se edita como si fuera borrador (= `AC-S10`) |

### Reenvío (`AC-U`)

| `AC` | Criterio |
|---|---|
| `AC-U01` | `CORRECTED` no pasa a `APPROVED` sin `approve` (control) |
| `AC-U02` | el reenvío es explícito (`submit`); ni `PUT` ni corrección cambian solos el estado a `PENDING_REVIEW` |
| `AC-U03` | el reenvío vuelve a `PENDING_REVIEW` (cola de revisión), no a `APPROVED` ni a `REGISTERED` |
| `AC-U04` | el reenvío conserva las reglas de revisión: `start`/`return`/`complete` funcionan sobre el reenviado; `BR-14` sigue (`GA-REM-007-A`) |
| `AC-U05` | sin doble efecto: reenviar no crea eventos ni movimientos; el saldo del lote es el mismo antes y después |

## A.6 Tareas

| Tarea | Contenido |
|---|---|
| `T-006-A1` | pruebas rojas `backend/tests/test_state_continuity.py` (fixture propia: empresa `A`/`B`, unidades ON/OFF explícitas, eventos sembrados en `RETURNED`, `REJECTED`, `CORRECTED`, `APPROVED`, `CANCELLED`, `SAP_CONFIRMED`, `DRAFT`, con `approval_actions` del revisor; actores: operador, corrector, aprobador, sin permiso, `B`, Administrador de Accesos, control-lectura, global) |
| `T-006-A2` | `submit_to_review`: origen `∈ {REGISTERED, RETURNED, REJECTED}`; `update_event`: + `REJECTED`; `cancel_event`: + `SAP_CONFIRMED`, `SAP_ERROR`, `CANCELLED` denegados |
| `T-006-A3` | `create_correction`: + `REJECTED`; resolución del evento con `predicado_de_evento` + `exigir_unidad_operativa` |
| `T-006-A4` | sensibilidad `S1`, `S2`, `S3`, `S4`, `S5`, `S8` (+ `S6`/`S7`/`S9` según §A.7); regresión; evidencia `R-135-R-143-STATE-CONTINUITY-EVIDENCE.md` |

## A.7 Sensibilidad

| Mut. | Retira | Debe caer |
|---|---|---|
| `S1` | `RETURNED`/`REJECTED` del mapa de reenvío (vuelve a `REGISTERED` solo) | `AC-S01` |
| `S2` | la guarda de estado origen en `submit` (cualquier estado reenvía) | `AC-S09`/`S10`/`S11` |
| `S3` | el permiso en la ruta de corrección (`corrections:correct` → `read`) | `AC-S04` |
| `S4` | la empresa en `create_correction` | `AC-S05` |
| `S5` | la habilitación de la unidad en la corrección (guarda compartida) | `AC-S07` |
| `S6` | el motivo mínimo de la corrección (`min_length`) | `AC-R02`/`R03` |
| `S7` | la auditoría del reenvío (`audit_state_transition`) | `AC-R04`/`R05` |
| `S8` | la inmutabilidad de `APPROVED` en `update_event` | `AC-S10`/`D06` |
| `S9` | doble aplicación | **`N/A`**: no existe rama que duplique filas o movimientos al reenviar; `AC-U05` es control |

## A.8 Fuera de alcance

SAP (`OD-17.c`: `SAP_ERROR`, reenvío, reproceso, `external_transaction_id`, conector) · `R-136` reverso · `R-142`
(`AOD-17`) · `R-140` motivo/permiso (`AOD-18`, UI) · `R-154` cierres (`AOD-08`) · `R-161` · `R-144` · `R-147` ·
`R-148` · `R-152` · `R-153` · `R-156` · `GA-REM-021` · ola C · fase 9 · `R-158` · `BU-D10` · `R-165` · `R-166` ·
frontend · migración · sistema de versiones nuevo.

## A.9 Definición de terminado

`AC-S01…S12`, `AC-R01…R07`, `AC-D01…D06`, `AC-U01…U05` verdes · rojo válido · `S1–S8` válidas, `S9` `N/A` ·
`R-130` 21/21 · `R-160/R-159` 40/40 · `R-163/R-162` 28/28 · `R-139` 35/35 · `GA-REM-006` 9/9 · flujo completo
23/23 · regresión completa · sin migración · sin rutas · sin frontend · `R-135` cerrado; `R-140` y `R-154` **PARTIAL**.

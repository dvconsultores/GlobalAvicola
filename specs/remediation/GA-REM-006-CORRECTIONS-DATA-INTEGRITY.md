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

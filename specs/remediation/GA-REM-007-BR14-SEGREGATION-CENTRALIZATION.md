# GA-REM-007 — BR-14: SEGREGACIÓN DE FUNCIONES Y CENTRALIZACIÓN DE REGLAS

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-007` · **Tipo** `BUSINESS RULE SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** · **Estado** `SPEC_READY` |
| **Dependencias** | `GA-REM-001` · `GA-REM-002` (quién puede aprobar) · `GA-REM-014` |
| **Hallazgos** | P0-10 · S-05 · `GA-TD-009` · `GA-REQ-029` (`PARCIAL`) |
| **Revalidado** | 2026-09-03 — `validate_segregation` se invoca **una sola vez** en todo el backend: `review/service.py:318` |

## Problema — definición exacta de BR-14

**Texto normativo vigente** (`specs/global-avicola/spec.md §5`):
> «BR-14 — Operador no aprueba su propia carga (segregación)»

**Texto de `docs/02-functional-spec.md §5`, regla R14**:
> «Ningún operador debe aprobar su propia carga (**si el flujo requiere segregación**)»

La regla se valida **en un único punto de entrada** (`ApprovalService.approve`) cuando existen **dos** rutas capaces de producir la transición a `approved`.

## Evidencia
| Punto de entrada | Valida BR-14 | Ruta |
|---|---|---|
| `ApprovalService.approve()` | **sí** | `backend/app/review/service.py:315-320` |
| `ApprovalService.batch_approve()` | sí (delega en `approve`) | `review/service.py:341-347` |
| **`ReviewService.complete_review()`** | **NO** | `review/service.py:196-234` — con `approval_levels <= 1` asigna `APPROVED` y `approved_by_id` sin validar |
| `ApprovalStep.require_segregation` | **nunca se consulta** | `review/models.py`; `approve()` no la lee |

**Ruta de elusión completa, ejecutable por el propio autor y sin permisos especiales:**
```
POST /operations              → registered
POST /review/batches          → pending_review
POST /review/start/{id}       → in_review
POST /review/complete         → APPROVED  ← aprobado por sí mismo
```

## Comportamiento actual
La segregación es eludible por diseño del flujo, no por un fallo puntual. Además, el campo `ApprovalStep.require_segregation`, que debería gobernar si la regla aplica, es decorativo.

## Comportamiento esperado
BR-14 se evalúa en **todos** los puntos de entrada que produzcan una transición a `approved`, de forma centralizada y gobernada por la configuración de la compañía.

## Alcance
1. **Inventariar exhaustivamente** todos los puntos de entrada que pueden llevar un evento a `approved`.
2. Centralizar la evaluación de BR-14 en un único punto de control invocado por todos ellos.
3. Determinar el gobierno de la condición «si el flujo requiere segregación»: hoy existe `ApprovalStep.require_segregation` sin uso y `Company.approval_levels`.
4. Cubrir con tests cada punto de entrada.
5. Establecer el patrón de centralización como referencia para el resto de reglas (Art. 22 de la constitución).

## Fuera de alcance
Implementar la aprobación multinivel completa (`ApprovalStep` secuenciado) — es backlog `GA-REM-019` · cambiar la máquina de estados · redefinir los roles.

## `RC-03` RESUELTO POR EVIDENCIA — regla `RR-03`
Resuelto el 2026-09-03 (`audit/remediation/REQUIREMENT_CONFLICT_RESOLUTION.md §5`). El cliente **no se pronuncia** sobre segregación de funciones, de modo que decide el nivel de proceso operativo, que lo hace dos veces y en el mismo sentido: `docs/02-functional-spec.md:554` («si el flujo requiere segregación») y `docs/12-approval-workflow.md:139` («si configuración lo exige»). El esquema de datos ya materializa esa lectura: `ApprovalStep.require_segregation` existe con `default=True` (`review/models.py:81`). `spec.md:275` la enuncia como absoluta, pero es una celda de tabla resumen y un nivel inferior en la jerarquía.

> **`RR-03`.** `BR-14` es **configurable por paso de aprobación** mediante `ApprovalStep.require_segregation`, con valor por defecto `True`. Toda ruta que apruebe, consolide o envíe a SAP debe consultar la bandera del paso aplicable y aplicar segregación salvo que esté explícitamente en `False`. Desactivarla es un cambio de configuración auditable y de alcance por empresa; nunca implícito. **Ninguna ruta de aprobación puede eludir la comprobación.**

La resolución no relaja el control: con el valor por defecto el comportamiento es idéntico al actual. Convierte una bandera muerta en una bandera honesta.

**Hallazgo nuevo incorporado — `R-23` (P1).** `complete_review` fija `APPROVED` y `approved_by_id` **sin llamar a `validate_segregation`** cuando `approval_levels <= 1` (`review/service.py:203-207`). Es una ruta de aprobación que elude `BR-14` por completo, y debe entrar en el inventario de puntos de entrada de esta spec.

## Reglas de negocio afectadas
`BR-14` (objeto de la spec). Colateralmente `BR-13`: si un operador puede aprobar su propia carga, puede llevarla a SAP.

## Backend afectado
`review/service.py` (`complete_review`, `approve`, `batch_approve`), `operations/validators.py` (punto de control centralizado), posible lectura de `ApprovalStep`.

## Frontend afectado
Ninguno funcionalmente. Conviene que la interfaz no ofrezca «completar revisión» sobre un registro propio, como defensa en profundidad.

## Base de datos afectada
Ninguna. `ApprovalStep.require_segregation` y `Company.approval_levels` ya existen.

## Seguridad
Cierra `S-05` (P0). Es una regla de **control interno**, no solo de aplicación.

## Compatibilidad
**Ruptura intencionada**: usuarios que hoy aprueban sus propios registros dejarán de poder. Debe verificarse cuántos registros en producción fueron auto-aprobados por esta vía, como parte de la auditoría de datos.

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| El autor completa la revisión de su propio registro | rechazo 403 con identificador BR-14 |
| El autor aprueba en lote incluyendo un registro propio | rechazo del lote completo, o rechazo selectivo — **decidir y documentar** |
| Un Super Admin aprueba su propio registro | **no hay excepción por rol**. `RR-03` solo admite la exención por `require_segregation = False` en el paso, configurada y auditada |
| Registro creado por un usuario ya eliminado | la regla compara identificadores; sigue aplicando |
| Compañía con `approval_levels = 1` | la regla **debe seguir aplicando**; es el caso que hoy la elude |
| Registro corregido por un tercero y aprobado por el autor original | decidir: el autor del **registro** es quien no puede aprobar |

## Acceptance Criteria

**AC01 — Elusión cerrada en `complete_review`**
```
Given un usuario que registró un evento
And   su compañía con approval_levels = 1
When  ejecuta la secuencia batches → start → complete sobre ese evento
Then  la última llamada devuelve 403 con el identificador BR-14
And   el evento no queda en estado approved
```
**AC02 — La ruta ya cubierta sigue cubierta**
```
Given un usuario que registró un evento en estado corrected
When  hace POST /approvals/approve sobre él
Then  recibe 403 con el identificador BR-14
```
**AC03 — Aprobación en lote**
```
Given un lote de aprobación que incluye un registro propio del aprobador
When  se ejecuta batch-approve
Then  el comportamiento coincide con lo documentado en esta spec
And   ningún registro propio queda approved
```
**AC04 — Un tercero sí puede aprobar**
```
Given un evento registrado por el usuario A
When  el usuario B, con permiso de aprobación, lo aprueba
Then  la operación tiene éxito y el evento queda approved
```
**AC05 — Cobertura de todos los puntos de entrada**
```
Given el inventario de puntos de entrada a estado approved documentado en esta spec
When  se ejecuta el test paramétrico sobre cada uno con el autor del registro
Then  todos rechazan con BR-14
```
**AC06 — Gobierno de la regla**
```
Given la regla `RR-03` (configurable por paso, `require_segregation` por defecto `True`)
When  se consulta la configuración que gobierna BR-14
Then  su comportamiento coincide con lo documentado
And   cualquier desactivación queda registrada en la auditoría
```
**AC07 — Identificador de regla coherente**
```
Given cualquier rechazo por segregación
When  se inspecciona el mensaje de error
Then  cita el identificador BR-14, el mismo que usan la spec y el código
```

## Tests requeridos
`T-007-01..07` para AC01–AC07 (integración) — `T-007-05` es paramétrico sobre el inventario de puntos de entrada + `T-007-08` E2E de la ruta de elusión completa.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Bloquear operaciones legítimas en compañías pequeñas donde una sola persona hace todo | `RR-03` lo resuelve: la empresa puede fijar `require_segregation = False` en el paso correspondiente. Es un cambio de configuración explícito y auditado, nunca el valor por defecto (`OD-03`) |
| Existen registros auto-aprobados en producción | inventariar en la auditoría de datos; decidir si se revierten |

## Rollback lógico
Reversible por commit. Sin cambios de esquema ni de datos.

## Definition of Done
- [x] `RC-03` resuelto (`RR-03`) · [ ] `R-23` cubierto (`complete_review`) · [ ] Inventario de puntos de entrada versionado · [ ] AC01–AC07 verificados · [ ] Tests en verde · [ ] Inventario de registros auto-aprobados en producción · [ ] Certification report

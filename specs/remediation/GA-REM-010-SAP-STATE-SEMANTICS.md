# GA-REM-010 — SEMÁNTICA DE ESTADOS SAP

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-010` · **Tipo** `INTEGRATION SEMANTICS SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** — integridad de datos en producción · **Estado** `SPEC_READY` |
| **Dependencias** | `GA-REM-001` |
| **Habilita** | `GA-REM-017` (SAP real) |
| **Hallazgos** | P0-7 · `GA-TD-007` · `GA-TD-034` · `GA-REQ-010`/`012` (`PARCIAL`) · `GA-TD-056` (estados inalcanzables) |
| **Revalidado** | 2026-09-03 — `get_adapter()` devuelve siempre `ManualSapAdapter`; `FEATURE_SAP_ENABLED` activo en el compose de producción |

> Esta spec **no implementa la integración SAP real** (eso es `GA-REM-017`). Su objeto es que el sistema deje de afirmar algo falso.

## Problema
Un adaptador manual está produciendo el efecto de una integración confirmada. `POST /sap/export` escribe un JSON en `/tmp` (efímero), devuelve siempre éxito con un identificador ficticio `MANUAL-<12 hex>`, y el servicio marca los eventos como `SENT_TO_SAP` con esa referencia. A partir de ahí, **BR-15 impide editarlos**.

Resultado: registros bloqueados como «enviados a SAP» que nunca llegaron a SAP, sin archivo recuperable y sin forma de distinguirlos de un envío real.

## Evidencia
| Ítem | Ruta |
|---|---|
| Adaptador hardcodeado con `# TODO` | `backend/app/integrations/sap/service.py:34-38` |
| Éxito siempre, identificador ficticio | `backend/app/integrations/sap/adapter.py:88-105` |
| Marcado como `SENT_TO_SAP` | `sap/service.py:307-311` |
| Bloqueo posterior por BR-15 | `backend/app/operations/validators.py:286-294` |
| Chequeo de conexión siempre positivo | `adapter.py:107-109` — `return True` |
| Flag activo en producción | `docker-compose.yml:26` — `FEATURE_SAP_ENABLED: ${FEATURE_SAP_ENABLED:-true}`, commit `bfccdfb` |
| Estados inalcanzables | `SAP_CONFIRMED` y `SAP_ERROR` no se asignan en ningún punto |
| `mock_adapter.py` no compila | `from .interface import SapAdapter` → `ModuleNotFoundError` (verificado) |
| Tarea pendiente | `tasks.md` T-085 `RealSapAdapter`, marcada «🔴 Crítica (bloquea prod)» |

## Comportamiento actual
```
POST /sap/export → ManualSapAdapter → archivo en /tmp (se pierde)
                → SapExportResult(success=True, sap_document_id="MANUAL-xxxx")
                → OperationalEvent.status = SENT_TO_SAP
                → sap_document_ref = "MANUAL-xxxx"   ← identificador inexistente en SAP
                → BR-15 bloquea toda edición posterior
```

## Comportamiento esperado
Un adaptador manual o simulado **no puede** dejar un registro en un estado que signifique «confirmado por el sistema externo» (Art. 21 de la constitución). Los estados deben distinguir entre preparado, enviado, confirmado y fallido, y el modo de operación debe ser visible.

## Alcance
1. Selección de adaptador **por configuración**, no por código (eliminar el `# TODO`).
2. Revisión de la máquina de estados de integración para que el modo manual no produzca `SENT_TO_SAP`.
3. `GET /sap/connection-check` debe reflejar el adaptador real en uso y no afirmar conectividad que no existe.
4. Persistencia del artefacto de exportación manual (se apoya en `GA-REM-009`).
5. Decisión ejecutiva registrada: mantener `FEATURE_SAP_ENABLED=true` con semántica corregida, o desactivarlo hasta `GA-REM-017`.
6. Inventario y saneamiento de los eventos ya marcados con referencia `MANUAL-*`.
7. Eliminar o reparar `mock_adapter.py` (no compila).

## Fuera de alcance
Implementar `RealSapAdapter` (`GA-REM-017`) · definir el contrato con SAP · credenciales de SAP.

## Estados de integración — propuesta para revisión
La spec **no impone** nombres que contradigan el modelo vigente. Sobre el enum `EventStatus` actual:

| Estado | Significado propuesto | Situación actual |
|---|---|---|
| `APPROVED` | aprobado, aún no consolidado | correcto |
| `CONSOLIDATED` | agrupado en un movimiento consolidado, listo para enviar | correcto |
| **nuevo o reutilizado** | **preparado para SAP en modo manual**: el artefacto existe y espera carga por el analista | **hoy inexistente** — es el hueco que causa el problema |
| `SENT_TO_SAP` | enviado por un adaptador con transporte real | **hoy lo asigna el adaptador manual** ← defecto |
| `SAP_CONFIRMED` | SAP confirmó el documento | **inalcanzable hoy** |
| `SAP_ERROR` | SAP rechazó o falló el envío | **inalcanzable hoy** |

**Decisión requerida en revisión**: introducir un estado nuevo (`READY_FOR_SAP`) o reutilizar `CONSOLIDATED` con un indicador de artefacto generado. La segunda evita una migración de enum.

## Reglas de negocio afectadas
`BR-13` (nada a SAP sin aprobación) se mantiene · `BR-15` (no editar enviados a SAP) **debe dejar de aplicarse** a registros que solo tienen un artefacto manual · `BR-12` (idempotencia) se conserva.

## Backend afectado
`integrations/sap/service.py` (selección de adaptador, transiciones), `integrations/sap/adapter.py` (`check_connection` honesto), `config.py` (variable de selección de adaptador), `operations/validators.py` (alcance de BR-15).

## Frontend afectado
`SapManagerPage.tsx` debe mostrar el adaptador en uso y el estado real, sin sugerir integración confirmada.

## Base de datos afectada
**Depende de la decisión**: si se introduce un estado nuevo en el enum `EventStatus` → migración Alembic con docstring citando `GA-REM-010`. Si se reutiliza `CONSOLIDATED` con indicador → posible columna booleana o ninguna.

**Datos**: los eventos con `sap_document_ref` que empieza por `MANUAL-` requieren decisión de saneamiento.

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| Exportación en modo manual | el evento **no** queda como enviado a SAP; queda como preparado |
| Registro preparado en modo manual | debe poder corregirse todavía (BR-15 no aplica) |
| El analista confirma la carga manual en SAP | debe existir una acción que registre la confirmación con la referencia real de SAP |
| Chequeo de conexión en modo manual | informa «modo manual, sin conexión», no `connected: true` |
| Eventos ya marcados con `MANUAL-*` | inventariados y saneados según decisión documentada |
| Cambio de adaptador con envíos en curso | la idempotencia por `SapPayload` lo cubre |

## Acceptance Criteria

**AC01 — El modo manual no simula integración**
```
Given el sistema configurado con el adaptador manual
When  se ejecuta POST /api/v1/sap/export sobre movimientos consolidados
Then  ningún evento queda en estado sent_to_sap
And   ningún evento recibe una referencia SAP con prefijo MANUAL-
```
**AC02 — El artefacto manual persiste**
```
Given una exportación en modo manual
When  el contenedor se recrea
Then  el artefacto generado sigue siendo recuperable
```
**AC03 — El estado refleja la realidad**
```
Given una exportación en modo manual completada
When  se consulta el evento
Then  su estado indica que está preparado para SAP, no confirmado por SAP
```
**AC04 — Los registros no enviados siguen siendo corregibles**
```
Given un evento con artefacto manual generado y sin confirmación de SAP
When  un usuario autorizado intenta corregirlo
Then  la corrección se permite
And   BR-15 no lo bloquea
```
**AC05 — El chequeo de conexión es honesto**
```
Given el adaptador manual configurado
When  se consulta GET /api/v1/sap/connection-check
Then  la respuesta identifica el adaptador en uso
And   no afirma conectividad con un sistema SAP real
```
**AC06 — El adaptador se selecciona por configuración**
```
Given la variable de configuración de adaptador
When  se cambia su valor y se reinicia el servicio
Then  el adaptador en uso cambia
And   no queda ningún TODO de selección de adaptador en el código
```
**AC07 — Inventario de registros afectados**
```
Given la base de datos de producción
When  se ejecuta el inventario de referencias MANUAL-*
Then  existe el recuento de eventos afectados y la decisión de saneamiento documentada
```
**AC08 — Código muerto retirado**
```
Given el módulo de integración SAP
When  se importa cada archivo del paquete
Then  ninguno lanza ModuleNotFoundError
```
**AC09 — El deployment no ha sido modificado**
```
Given el diff de cierre de GA-REM-010
Then  ningún archivo de .github/workflows/ ha sido modificado
And   watchtower, pull_policy y la etiqueta :latest permanecen sin cambios
```

## Tests requeridos
`T-010-01..08` para AC01–AC08 (integración y estáticos) · `T-010-09` verificación del diff.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Cambiar el enum de estados rompe consultas y frontend | preferir la opción sin migración de enum; si se migra, inventariar todos los consumidores |
| Los registros ya bloqueados quedan en un limbo | AC07 obliga a inventariar y decidir |
| Desactivar el flag SAP deja sin función a `SapManagerPage` | es aceptable y honesto; la pantalla debe indicar que la integración está desactivada |

## Rollback lógico
Reversible por commit y por variable de configuración. El saneamiento de datos requiere procedimiento con copia previa.

## Definition of Done
- [ ] Decisión sobre el estado nuevo vs reutilización documentada · [ ] Decisión ejecutiva sobre `FEATURE_SAP_ENABLED` registrada · [ ] AC01–AC09 verificados · [ ] Inventario y saneamiento de `MANUAL-*` · [ ] Certification report

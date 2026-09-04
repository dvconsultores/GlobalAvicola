# GA-REM-008 — TRAZABILIDAD GENERACIONAL

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-008` · **Tipo** `DOMAIN + BUGFIX SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** · **Estado** `SPEC_DRAFT` — requiere resolver `RC-04` |
| **Dependencias** | `GA-REM-001` · `GA-REM-014` · `GA-REM-011` (la pantalla que lo muestra está rota) · **informada por** `GA-REM-020` |
| **Hallazgos** | P0-11 · `GA-TD-011` · `GA-REQ-039` (`ROTO`) · `GA-REQ-040` (`PARCIAL`) · `CODE_BEFORE_SPEC` (código 03:51, spec 18:38) |
| **Revalidado** | 2026-09-03 — el emparejamiento por `lot_id == data.lot_id` persiste en las cuatro ramas |

## Problema
La creación automática de `EggBatch` y `ChickBatch` empareja el evento de despacho con el de recepción **exigiendo que ambos pertenezcan al mismo lote**, y después asigna el lote destino como `reception.lot_id` — es decir, el mismo lote.

Por definición del dominio, el despacho se registra en el lote origen y la recepción en el lote destino: son lotes distintos. La coincidencia **nunca ocurre** en operación normal y no se crea ningún vínculo; si por accidente coincidiera, se crearía un lote enlazado consigo mismo.

## Evidencia
| Rama | Ruta | Defecto |
|---|---|---|
| `EGG_DISPATCH` busca `EGG_RECEPTION_HATCHERY` | `backend/app/operations/service.py:131-137` | filtra `lot_id == data.lot_id`; asigna `hatchery_lot_id = reception.lot_id` |
| `EGG_RECEPTION_HATCHERY` busca `EGG_DISPATCH` | `service.py:160-166` | mismo filtro |
| `CHICK_DISPATCH` busca `BIRD_RECEPTION` | `service.py:178-186` | mismo filtro; asigna `destination_lot_id = reception.lot_id` |
| `BIRD_RECEPTION` busca `CHICK_DISPATCH` | `service.py:209-216` | mismo filtro |
| Enlace manual sí funciona | `frontend/src/components/TraceabilityTree.tsx:86,105` → `POST /lots/egg-batches`, `/chick-batches` | correcto |
| El árbol vive en una pantalla rota | `LotDetailPage.tsx:45` (422) | inaccesible |
| Consulta sin filtro de compañía | `backend/app/lots/router.py:157-176` | `S-13` |

## Comportamiento actual
La trazabilidad generacional automática **no produce ningún vínculo**. El único mecanismo funcional es el enlace manual, alojado en una pantalla que no carga.

## Comportamiento esperado
```
Lote GRANDPARENT ──egg_dispatch──▶ [EggBatch] ──egg_reception_hatchery──▶ Lote HATCHERY
Lote BREEDER(prod) ──egg_dispatch──▶ [EggBatch] ──egg_reception_hatchery──▶ Lote HATCHERY
Lote HATCHERY ──chick_dispatch──▶ [ChickBatch] ──bird_reception──▶ Lote BROILER | BREEDER
```
Con emparejamiento por un identificador compartido entre origen y destino, no por identidad de lote.

## Fuente de verdad del dominio
La documentación original del cliente (`Bases Consideradas en el Desarrollo de la App Avicola.pdf`) define explícitamente los datos de traslado y exige **«Identificación de Lote: número o código del lote para la trazabilidad»** tanto en el traslado de huevo fértil a incubadora como en el traslado de pollitos a engorde. Ese es el mecanismo de emparejamiento que el negocio previó y que la implementación no usa.

## Alcance
1. Definir el **mecanismo de emparejamiento**: identificador de despacho compartido, declarado en el evento de despacho y referenciado en el de recepción.
2. Corregir las cuatro ramas de `_auto_create_traceability_batches`.
3. Definir el comportamiento cuando no hay contrapartida (despacho sin recepción, recepción sin despacho).
4. Definir invariantes: un lote no puede ser su propio origen; las cantidades recibidas no pueden exceder las despachadas sin justificación.
5. Filtrar por compañía en la consulta de trazabilidad (`S-13`).
6. Conservar el enlace manual como mecanismo de corrección.
7. Contrastar el mecanismo elegido contra el requisito del cliente («Identificación de Lote para la trazabilidad»), usando `GA-REM-020` como fuente de validación.

## Fuera de alcance
Refactor estructural de `EggBatch`/`ChickBatch` salvo necesidad demostrada · trazabilidad hacia la planta de beneficio · la cadena LIVIANAS (fuera de v1).

## REQUIREMENT_CONFLICT — `RC-04`
La spec del proyecto (`spec.md §4.9`) dice: «Un EggBatch se crea automáticamente al registrar `egg_dispatch` + `egg_reception_hatchery` **para el mismo lote de huevos**». Esa redacción es la que el código interpretó literalmente como *el mismo `lot_id`*, produciendo el defecto.

«El mismo lote de huevos» significa **la misma remesa física**, no el mismo registro de lote. La spec es ambigua y debe corregirse antes de implementar.

## Backend afectado
`operations/service.py` (cuatro ramas), `lots/router.py` (filtro de compañía), `operations/models.py` o `schemas.py` (campo de identificador de despacho, si se opta por esa vía).

## Frontend afectado
`OperationFormPage.tsx` (capturar el identificador de despacho en los eventos de despacho y recepción), `TraceabilityTree.tsx`, `LotDetailPage.tsx` (depende de `GA-REM-011`).

## Base de datos afectada
**Probable**: campo de identificador de despacho en `operational_events` o reutilización de `sap_document_ref` / `extra_data.dispatch_order` (ya existe en el formulario de `bird_distribution`). Si se añade columna → migración Alembic con docstring citando `GA-REM-008`.

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| Despacho sin recepción registrada aún | `EggBatch` con `quantity_received` nulo y sin `reception_event_id`; se completa al recibir |
| Recepción sin despacho previo | se registra igualmente; se marca como cadena incompleta, nunca se inventa el origen |
| Cantidad recibida distinta de la despachada | se registra la diferencia; no es error, es merma trazable |
| Cantidad recibida mayor que la despachada | alerta o rechazo — **decidir y documentar** |
| Un despacho se reparte en varias recepciones | el modelo debe soportarlo, o rechazarlo explícitamente |
| Lote origen = lote destino | **invariante violada**: rechazo |
| Lotes de compañías distintas | rechazo (`S-13`) |

## Acceptance Criteria

**AC01 — Cadena huevo creada entre lotes distintos**
```
Given un lote reproductor A en fase producción y un lote de incubadora B
When  se registra egg_dispatch en A y egg_reception_hatchery en B con el mismo identificador de despacho
Then  se crea un EggBatch con source_lot_id = A y hatchery_lot_id = B
And   A ≠ B
```
**AC02 — Cadena pollito creada entre lotes distintos**
```
Given un lote de incubadora B y un lote de engorde C
When  se registra chick_dispatch en B y bird_reception en C con el mismo identificador de despacho
Then  se crea un ChickBatch con hatchery_lot_id = B y destination_lot_id = C
And   el ChickBatch referencia el EggBatch que originó a B cuando exista
```
**AC03 — Nunca se crea un vínculo auto-referencial**
```
Given cualquier combinación de eventos
When  se ejecuta la creación automática de trazabilidad
Then  no existe ningún EggBatch ni ChickBatch con lote origen igual al lote destino
```
**AC04 — Despacho sin recepción**
```
Given un egg_dispatch registrado sin recepción posterior
When  se consulta la trazabilidad del lote origen
Then  aparece el despacho con la cadena marcada como incompleta
```
**AC05 — Navegación entre generaciones**
```
Given una cadena A → B → C completa
When  se consulta GET /lots/{B}/traceability
Then  devuelve el lote origen A y el lote destino C
```
**AC06 — Aislamiento por compañía**
```
Given lotes de dos compañías distintas
When  un usuario de la compañía 1 consulta la trazabilidad
Then  no obtiene ningún batch que referencie lotes de la compañía 2
```
**AC07 — El enlace manual sigue disponible**
```
Given dos lotes sin vínculo automático
When  un usuario autorizado crea el enlace manualmente
Then  el vínculo se crea y aparece en el árbol
```

## Tests requeridos
`T-008-01..07` para AC01–AC07 (integración) + `T-008-08` E2E de la cadena completa reproductora → incubadora → engorde.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Cambiar el mecanismo invalida los vínculos existentes | inventariar `egg_batches`/`chick_batches` en producción antes de migrar |
| Añadir un campo obligatorio rompe la captura actual | el identificador debe ser opcional en la primera iteración y obligatorio tras un período de transición |
| La corrección se hace sin resolver `RC-04` y se repite el error de interpretación | `RC-04` bloquea el paso a `SPEC_READY` |

## Rollback lógico
Reversible por commit. Si se añade columna, `downgrade()` funcional. Los vínculos creados no se borran.

## Definition of Done
- [ ] `RC-04` resuelto y la spec original corregida · [ ] AC01–AC07 verificados · [ ] Inventario de vínculos existentes en producción · [ ] Certification report

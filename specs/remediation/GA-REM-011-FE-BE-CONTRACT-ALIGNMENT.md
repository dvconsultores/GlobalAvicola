# GA-REM-011 — ALINEACIÓN DE CONTRATOS FRONTEND ↔ BACKEND

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-011` · **Tipo** `CONTRACT SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** — 5 pantallas caídas · **Estado** `SPEC_READY` |
| **Dependencias** | `GA-REM-001` · `GA-REM-014` (para los tests de contrato) |
| **Habilita** | `GA-REM-006` (pantalla de corrección), `GA-REM-008` (árbol de trazabilidad), `GA-REM-016` |
| **Hallazgos** | P0-5 · `GA-TD-005` · `GA-TD-014` · `GA-TD-015` · `GA-TD-018` · `GA-TD-019` · `GA-TD-020` · `GA-TD-031` |
| **Revalidado** | 2026-09-03 — los 6 `limit=200` persisten, más 2 adicionales en la capa de hooks muerta |

## Problema
La auditoría contabilizó **176 llamadas del frontend sobre 99 URL distintas** contra **167 operaciones de backend**, con **13 desajustes de contrato**. Ninguna llamada apunta a una ruta inexistente: todos los fallos son de **forma** del contrato.

La causa raíz es arquitectónica: existe una capa `services/` + `hooks/` (21 módulos, ~600 LOC) que **ninguna página utiliza**. Las páginas llaman a axios directamente con URL literales, por lo que no hay un punto único donde definir límites, filtros ni formas de payload.

## Evidencia consolidada

### Grupo 1 — Límite fuera de rango → HTTP 422 (6 llamadas, 5 pantallas caídas)
| Archivo:línea | Llamada | Tope backend | Efecto |
|---|---|---|---|
| `stores/company.store.ts:38` | `/masters/companies?limit=200` | `le=100` | selector de compañía siempre vacío |
| `pages/users/UsersPage.tsx:21` | ídem, dentro de `Promise.all` | `le=100` | **toda** la pantalla cae: sin usuarios ni roles |
| `pages/lots/LotDetailPage.tsx:45` | `/lots?limit=200` fuera del `allSettled` | `le=100` | aborta KPIs, fases, eventos, alertas y trazabilidad |
| `pages/review/ReviewDetail.tsx:32` | `/operations?limit=200` | `le=100` | «evento no encontrado» |
| `pages/review/CorrectionForm.tsx:27` | `/operations?limit=200` | `le=100` | «evento no encontrado» |
| `pages/reports/ReportsPage.tsx:19` | `/operations?lot_id=&limit=200` | `le=100` | gráficas vacías |

Adicionalmente en la capa muerta: `hooks/useMasters.ts:59-62` (×4) y `hooks/useOperations.ts:55`.

### Grupo 2 — Parámetros que el backend no acepta (7, silenciosos)
| Pantalla | Parámetro | Efecto |
|---|---|---|
| `MyPendingPage:33` | `registered_by_me` | ignorado → muestra eventos de toda la compañía |
| `MyPendingPage:33` | `status="draft,registered"` | valor inválido para el enum → **500** |
| `ReviewCenter:86` | `status` | pestañas de estado inertes |
| `ReviewCenter:91` | `operator_id` | filtro de operador inerte |
| `AuditPage:44` | `search` | buscador inerte |
| `AuditPage:47` | `action_contains` | pestaña «Correcciones» inerte |
| `AuditPage:48` | `group_by` | pestaña «Por usuario» inerte |

### Grupo 3 — Campos del contrato nunca enviados (2)
| Campo | Consecuencia |
|---|---|
| `sap_document_ref` | el formulario guarda la orden SAP en `extra_data.sap_order_ref`; BR-11 y BR-18 nunca se disparan; el comparativo SAP siempre vacío |
| `idempotency_key` | BR-12 inerte; un doble envío crea dos eventos |

### Grupo 4 — Método inexistente (405)
`MasterListPage:79` emite `PUT /masters/{entidad}/{id}` para 12 entidades; el backend solo registró `PUT` para 4 → **405 en 8 pantallas de catálogo**.

### Grupo 5 — Respuestas sin envoltorio uniforme
`masters`, `lots`, `operations` y `users` devuelven listas planas sin total; `review`, `approvals`, `audit` y `sap` devuelven `{items, total}`. `MasterListPage:43` hace `setTotal(response.data.length)` → paginación falsa.

## Alcance
1. **Construir primero la matriz de contrato consolidada** antes de corregir nada. Clasificación obligatoria por fila: `MATCH` · `FE_WRONG` · `BE_WRONG` · `CONTRACT_DRIFT` · `MISSING_ENDPOINT` · `UNUSED_ENDPOINT` · `INCOMPATIBLE_DTO` · `INCOMPATIBLE_QUERY`.
2. Corregir por **grupos coherentes**, no con parches aislados.
3. Unificar los topes de paginación del backend y el envoltorio de respuesta.
4. **Decisión arquitectónica sobre la capa muerta**: adoptarla en todas las páginas o eliminarla. No ambas.
5. Generar y versionar `openapi.json` como contrato de referencia.
6. Contract testing derivado del esquema.

## Fuera de alcance
Rediseño de pantallas · nuevas funcionalidades · cambio del cliente HTTP · adopción de React Query (backlog `GA-REM-019`).

## Matriz de contrato — formato obligatorio
| ID | Pantalla | Acción | Método FE | URL FE | Endpoint BE | Query | Request | Response | Auth | Clasificación |
|---|---|---|---|---|---|---|---|---|---|---|

Se versiona en `audit/remediation/CONTRACT_MATRIX.md` y es entregable de esta spec.

## Decisión arquitectónica requerida — capa `services/` + `hooks/`
| Opción | Ventaja | Coste |
|---|---|---|
| **A · Adoptarla** | punto único de contrato; evita la reincidencia | tocar 24 páginas |
| **B · Eliminarla** | menos código muerto; menor alcance inmediato | los contratos siguen dispersos; el defecto se repetirá |
| **C · Adoptarla solo en las pantallas que se tocan** | alcance progresivo | convivencia temporal de dos patrones |

**Recomendación para la revisión: opción C con compromiso explícito hacia A.** Toda pantalla que esta spec toque queda migrada; el resto se migra en `GA-REM-019`.

## Backend afectado
Topes de paginación en los 10 routers · `masters/router.py` (los 15 `update_schema` faltantes) · `review/router.py` y `audit/router.py` (parámetros de filtro) · `operations/router.py` (`registered_by_me`, estados múltiples) · envoltorio de respuesta uniforme.

## Frontend afectado
Las 6 llamadas con `limit=200` · `MyPendingPage` · `ReviewCenter` · `AuditPage` · `MasterListPage` · `OperationFormPage` (`sap_document_ref`, `idempotency_key`) · capa de servicios según la decisión.

## Base de datos afectada
Ninguna.

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| Petición con `limit` por encima del tope | 422 con mensaje claro, y el frontend nunca la emite |
| Filtro de estado con varios valores | el backend acepta lista, o el frontend emite varias peticiones — decidir y documentar |
| Filtro no soportado enviado por un cliente antiguo | se ignora sin romper, y queda registrado |
| Entidad maestra sin `PUT` | o se añade el método, o la interfaz no ofrece «Editar» |
| Listado sin total | el frontend no debe inventar el total |

## Acceptance Criteria

**AC01 — Ninguna llamada del frontend produce 422 por límite**
```
Given la aplicación en ejecución
When  se recorren las 24 pantallas cargando sus datos
Then  ninguna petición devuelve 422 por parámetro limit fuera de rango
```
**AC02 — Las 5 pantallas caídas cargan**
```
Given un usuario autorizado
When  abre Detalle de Lote, Detalle de Revisión, Formulario de Corrección, Usuarios y Reportes
Then  cada pantalla muestra sus datos sin error
```
**AC03 — Mis Pendientes muestra solo lo propio**
```
Given un operador con eventos propios y ajenos en su compañía
When  abre Mis Pendientes
Then  solo ve los registrados por él
And   la petición no devuelve 500
```
**AC04 — Los filtros filtran o no existen**
```
Given las pestañas de estado de Revisión y el buscador de Auditoría
When  el usuario los utiliza
Then  el resultado cambia conforme al filtro
Or    el control no se presenta en la interfaz
```
**AC05 — La referencia SAP se persiste en su campo**
```
Given un formulario de operación con una orden SAP seleccionada
When  se guarda el evento
Then  sap_document_ref queda poblado en operational_events
And   BR-11 se dispara ante un documento duplicado
```
**AC06 — Idempotencia efectiva**
```
Given un formulario enviado dos veces con el mismo contenido
When  ambas peticiones llegan al backend
Then  se crea un solo evento
```
**AC07 — Edición de maestros**
```
Given las 12 pantallas de catálogo con edición ofrecida
When  se edita un registro en cada una
Then  ninguna devuelve 405
```
**AC08 — Paginación con total real**
```
Given un catálogo con 150 registros y página de 20
When  se consulta la primera página
Then  la interfaz muestra 150 como total
```
**AC09 — Contrato versionado**
```
Given el repositorio tras el cierre
When  se consulta el contrato de API
Then  existe un openapi.json versionado que coincide con las rutas de la aplicación
```
**AC10 — Contract testing activo**
```
Given una modificación que rompe un contrato consumido por el frontend
When  se ejecuta la suite de contract testing
Then  falla identificando la ruta y el campo afectados
```

## Tests requeridos
`T-011-01` barrido de las 24 pantallas sin 422 (E2E) · `T-011-02..08` para AC02–AC08 · `T-011-09` generación y comparación de `openapi.json` (CI) · `T-011-10` suite de contract testing.

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Unificar topes rompe consumidores no inventariados | la matriz de contrato es entregable **previo** a cualquier corrección |
| Corregir 13 desajustes uno a uno reintroduce el problema | la spec obliga a agrupar por causa, no por síntoma |
| La decisión sobre la capa muerta se pospone indefinidamente | AC de la spec exige decisión documentada antes de cerrar |

## Rollback lógico
Reversible por commit y por grupos. Sin cambios de esquema ni datos.

## Definition of Done
- [ ] `CONTRACT_MATRIX.md` completa y versionada · [ ] Decisión sobre la capa `services/hooks` documentada · [ ] AC01–AC10 verificados · [ ] `openapi.json` versionado · [ ] Contract testing en CI · [ ] Certification report

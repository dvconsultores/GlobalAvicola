# MATRIZ DE CONTRATO FRONTEND ↔ BACKEND

> Entregable de **`GA-REM-011`** · Wave 1 · 2026-09-03 · Commit base `bfccdfb`
> Consolidada **antes** de aplicar corrección alguna (§23 del encargo de Wave 1).

Clasificación: `MATCH` · `FE_WRONG` · `BE_WRONG` · `CONTRACT_DRIFT` · `MISSING_ENDPOINT` · `UNUSED_ENDPOINT` · `INCOMPATIBLE_QUERY` · `INCOMPATIBLE_DTO` · `REQUIREMENT_CONFLICT`

Acción en Wave 1: `CORREGIDO` · `DIFERIDO` · `BLOCKED_BY_REQUIREMENT_CONFLICT`

---

## 1. Panorama

```
Operaciones backend ....................... 167 (+/health)
Consumidas por el frontend ................ 133  (79,6 %)
Huérfanas (UNUSED_ENDPOINT) ...............  34  (20,4 %)
Llamadas a rutas inexistentes .............   0
Desajustes de contrato .................... 13
```

---

## 2. Grupo 1 — `INCOMPATIBLE_QUERY`: límite fuera de rango → HTTP 422

Los endpoints declaran `limit: int = Query(20, ge=1, le=100)`. Seis llamadas piden `limit=200`.

| ID | Pantalla | Archivo:línea | URL FE | Endpoint BE | Clasificación | Impacto | Acción W1 |
|---|---|---|---|---|---|---|---|
| C-01 | Selector de compañía | `stores/company.store.ts:38` | `/masters/companies?limit=200` | `le=100` | **`FE_WRONG`** | selector siempre vacío → multi-compañía inutilizable | **`CORREGIDO`** |
| C-02 | Usuarios | `pages/users/UsersPage.tsx:21` | ídem, dentro de `Promise.all` | `le=100` | **`FE_WRONG`** | **toda la pantalla cae**: sin usuarios ni roles | **`CORREGIDO`** |
| C-03 | Detalle de lote | `pages/lots/LotDetailPage.tsx:45` | `/lots?limit=200` fuera de `allSettled` | `le=100` | **`FE_WRONG`** | aborta KPIs, fases, eventos, alertas y trazabilidad | **`CORREGIDO`** |
| C-04 | Detalle de revisión | `pages/review/ReviewDetail.tsx:32` | `/operations?limit=200` | `le=100` | **`FE_WRONG`** | «evento no encontrado» | **`CORREGIDO`** |
| C-05 | Formulario de corrección | `pages/review/CorrectionForm.tsx:27` | `/operations?limit=200` | `le=100` | **`FE_WRONG`** | «evento no encontrado» | **`CORREGIDO`** |
| C-06 | Reportes (gráficas) | `pages/reports/ReportsPage.tsx:19` | `/operations?lot_id=&limit=200` | `le=100` | **`FE_WRONG`** | gráficas vacías | **`CORREGIDO`** |
| C-07 | Capa muerta (hooks) | `hooks/useMasters.ts:59-62`, `hooks/useOperations.ts:55` | 5 llamadas `limit: 200` | `le=100` | **`FE_WRONG`** | latente: sin consumidor hoy, rompería al adoptar la capa | **`CORREGIDO`** (preventivo) |

**Diagnóstico:** en C-03, C-04 y C-05 el frontend pide una **lista completa para localizar un único registro**, existiendo el endpoint por identificador (`GET /lots/{id}`, `GET /operations/{id}`). La corrección no es subir el límite: es usar el endpoint correcto.

---

## 3. Grupo 2 — `INCOMPATIBLE_QUERY`: parámetros no soportados

| ID | Pantalla | Parámetro | ¿Existe en BE? | Clasificación | Impacto | Acción W1 |
|---|---|---|---|---|---|---|
| C-08 | Mis Pendientes | `registered_by_me=true` | **No** | **`BE_WRONG`** — la intención de la pantalla es inequívoca | muestra eventos de toda la compañía, no los propios | **`CORREGIDO`** |
| C-09 | Mis Pendientes | `status="draft,registered"` | acepta `status`, pero lo compara contra un `Enum` | **`BE_WRONG`** | valor inválido → **HTTP 500** | **`CORREGIDO`** |
| C-10 | Bandeja de revisión | `status` (pestañas) | **No** en `GET /review/pending` | `CONTRACT_DRIFT` | pestañas de estado inertes | **`DIFERIDO`** |
| C-11 | Bandeja de revisión | `operator_id` | **No** | `CONTRACT_DRIFT` | filtro de operador inerte | **`DIFERIDO`** |
| C-12 | Auditoría | `search` | **No** | `CONTRACT_DRIFT` | buscador inerte | **`DIFERIDO`** |
| C-13 | Auditoría | `action_contains` | **No** | `CONTRACT_DRIFT` | pestaña «Correcciones» inerte | **`DIFERIDO`** |
| C-14 | Auditoría | `group_by` | **No** | `CONTRACT_DRIFT` | pestaña «Por usuario» inerte | **`DIFERIDO`** |

**Criterio de diferimiento (C-10 … C-14):** implementar estos filtros cambia la semántica de consulta de Revisión y Auditoría, y su comportamiento esperado depende de decisiones que Wave 1 no resuelve (qué estados debe mostrar cada pestaña, cómo se agrupa por usuario). Hoy son **inertes pero no rompen nada**. Se difieren a Wave 2 con `GA-REM-011` reabierta.

---

## 4. Grupo 3 — `CONTRACT_DRIFT`: campos del contrato nunca enviados

| ID | Campo | Situación | Clasificación | Acción W1 | Justificación |
|---|---|---|---|---|---|
| C-15 | `sap_document_ref` | el formulario guarda la orden SAP en `extra_data.sap_order_ref`; el campo tipado nunca se puebla | **`CONTRACT_DRIFT`** | **`DIFERIDO`** | enviarlo **activa BR-11 y BR-18**, que hoy están inertes. Es un cambio de comportamiento de negocio que puede bloquear registros de operadores. Requiere coordinarse con `GA-REM-010` y con la decisión de `RC-07`. **No es inequívoco en el sentido del §23.** |
| C-16 | `idempotency_key` | el backend implementa deduplicación con índice único; el frontend nunca la genera | **`CONTRACT_DRIFT`** | **`DIFERIDO`** | §33 del encargo previo indica preferir **idempotencia del lado servidor**. Decidir dónde se genera es una decisión de diseño, no un defecto inequívoco. Ver `GA-REQ-059`. |

---

## 5. Grupo 4 — `BE_WRONG`: método inexistente → HTTP 405

| ID | Situación | Clasificación | Acción W1 |
|---|---|---|---|
| C-17 | `MasterListPage:79` emite `PUT /masters/{entidad}/{id}` para **12** entidades; el backend registró `PUT` solo para `companies`, `farms`, `houses`, `hatcheries` → **405 en 8 pantallas** | **`BE_WRONG`** | **`CORREGIDO`** |

Entidades sin `PUT` que la UI ofrece editar: `suppliers`, `genetic-lines`, `breeds`, `feed-types`, `vaccines`, `mortality-causes`, `transports`, `processing-plants`.

**Criterio:** editar un catálogo maestro es una operación evidentemente legítima; el defecto es la ausencia del método, no la oferta de la UI. La corrección es aditiva y de bajo riesgo.

---

## 6. Grupo 5 — `CONTRACT_DRIFT`: respuestas sin envoltorio uniforme

| ID | Situación | Clasificación | Acción W1 |
|---|---|---|---|
| C-18 | `masters`, `lots`, `operations` y `users` devuelven listas planas sin total; `review`, `approvals`, `audit` y `sap` devuelven `{items, total}`. `MasterListPage:43` hace `setTotal(response.data.length)` → paginación falsa | `CONTRACT_DRIFT` | **`DIFERIDO`** |

**Criterio:** unificar el envoltorio afecta a 4 módulos y a todos sus consumidores. Es un cambio de contrato amplio, no un defecto puntual. Wave 2.

---

## 7. Endpoints huérfanos — `UNUSED_ENDPOINT` (34)

Sin consumidor en el frontend. **Ninguno se elimina en Wave 1**: podrían corresponder a funcionalidad pendiente de exponer.

| Grupo | Nº | Destino |
|---|---|---|
| Configuración de aprobación multinivel (`/approval-steps` ×5) | 5 | `GA-REM-019` — diferenciador de producto sin UI |
| KPI sin consumidor (`animal-welfare`, `production-index`, `transfer-efficiency`, `vaccination-efficiency`) | 4 | **`GA-REM-022`** — 4 de ellos son KPI que el cliente exige (`R-17`) |
| Maestros sin pantalla (`productive-phases`, `rejection-reasons` completos; escritura de `medications`, `cull-causes`, `incubators`, `hatchers`, `correction-types`) | 20 | backlog |
| `GET /users/{id}`, `GET /operations/{id}/evidences` | 2 | backlog |
| Otros | 3 | backlog |

Adicionalmente, **8 endpoints solo son referenciados desde la capa `services/` muerta**: alcanzables en teoría, inalcanzables en la práctica.

---

## 8. Resumen de acciones de Wave 1

```
Desajustes inventariados ................... 18  (C-01 … C-18)
  CORREGIDOS en Wave 1 ..................... 10  (C-01…C-09, C-17)
  DIFERIDOS a Wave 2 ....................... 8   (C-10…C-16, C-18)
  BLOCKED_BY_REQUIREMENT_CONFLICT .......... 0
```

**Ningún desajuste quedó bloqueado por `RC-01` … `RC-05`.** Los 8 diferidos lo están por criterio de alcance —cambian comportamiento de negocio o contrato amplio—, no por conflicto de requerimiento. Cada uno tiene justificación explícita arriba.

## 9. Decisión sobre la capa `services/` + `hooks/`

**Diferida a Wave 2** con recomendación registrada: opción **C** (migrar solo las pantallas que se toquen, con compromiso hacia la adopción completa).

En Wave 1 se corrigieron también los `limit: 200` de la capa muerta (C-07) como medida preventiva: si se adopta la capa en Wave 2, el defecto no reaparece.

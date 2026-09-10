# BACKEND CAPABILITY MAP — lo que el frontend PUEDE consumir

**2026-09-10** · base `3808ed5` · 211 rutas · este mapa **no certifica** el backend (eso ya está en su propio programa); documenta qué ofrece hoy al frontend, para juzgar la ausencia de interfaz.

## 1. Generación desplegada (probada sin autenticar)

| Familia | Ruta de la sonda | Respuesta | Lectura |
|---|---|:--:|---|
| Unidades de negocio (fase 7) | `GET /api/v1/business-units` | 401 | existe y exige permiso |
| Concesiones por usuario (fase 7 + R-129) | `POST /api/v1/users/{id}/business-units` | 401 | existe |
| Clasificación pendiente (fase 6) | `GET /api/v1/operations/pending-classification` | 401 | existe |
| Reverso (tranche 5) | `GET /api/v1/reversals` | 401 | existe |
| Notificaciones (GA-REM-038) | `GET /api/v1/notifications/unread-count` | 401 | existe |
| Alertas | `GET /api/v1/operations/alerts` | 401 | existe |
| Empresas (catálogo seguro, R-127) | `GET /api/v1/masters/companies` (con sesión) · `GET` sin sesión | 401 | existe; contrato seguro `CompanyCatalogRead` |
| Cambio de empresa | `POST /api/v1/switch-company` | 405 (en GET) | existe (POST) |

```
DEPLOYED BACKEND = NEW  (cada familia entregada hasta la fecha está viva)
```

## 2. Mapa por capacidad de producto (solo las que exigen interfaz)

| Capacidad | Rutas backend | Permiso | Alcance | Estado backend | Consumidor frontend |
|---|---|---|---|---|---|
| Sesión | `POST /auth/login`, `POST /auth/refresh` | — | — | IMPLEMENTED | ✅ existe |
| Usuarios | `GET/POST/PUT /users`, `GET /users/{id}` | `users:*` | inquilino (AC13–16) | IMPLEMENTED | ✅ existe |
| Roles | `GET/POST/PUT /roles`, `GET /roles/permissions-catalog` | `roles:*`/admin | producto | IMPLEMENTED | ⚠️ local, **no desplegado** |
| Unidades por empresa | `GET /business-units`, `PATCH /business-units/{code}/enable|disable` | `business_units:read/update` | inquilino | IMPLEMENTED | ❌ **no existe UI** |
| Unidades por usuario | `GET /business-units/{code}/grant-candidates`, `POST/DELETE /users/{id}/business-units` | `business_units:create/delete` | inquilino | IMPLEMENTED (R-129 incluido) | ❌ **no existe UI** |
| Clasificación pendiente | `GET /operations/pending-classification`, `POST …/classify`, `…/reclassify` | `masters:update` / `corrections:correct` | inquilino | IMPLEMENTED | ❌ **no existe UI** |
| Selector de empresa | `GET /masters/companies`, `POST /switch-company` | `masters:read` | control global | IMPLEMENTED | ⚠️ selector super_admin (existe) |
| Recepción de aves | `POST /operations` (+ BR-08/17/18/19/20) | `operations:create` | unidad (enmienda G) | IMPLEMENTED | ⚠️ formulario desactualizado en runtime (BR-20) |
| Nacimiento | `POST /operations` (+ BR-21) | `operations:create` | unidad | IMPLEMENTED | ⚠️ ídem (BR-21) |
| Importación abuelas | `POST /operations` (+ BR-22, `import_plan`) | `operations:create` | unidad + grandparent | IMPLEMENTED | ⚠️ ídem (BR-22) |
| Despacho | `POST /operations` (+ BR-02/BR-04) | `operations:create` | unidad | IMPLEMENTED | ⚠️ ídem |
| Agua | `POST /operations` (`water_consumption`) | `operations:create` | unidad | IMPLEMENTED | ⚠️ captura local sin desplegar |
| Envío a revisión | `POST /operations/{id}/submit` | `operations:update` | unidad | IMPLEMENTED | ❌ **sin llamador UI (R-181)** |
| Revisión/aprobación | `GET /review/pending`, `POST /review/start|complete|return`, `POST /approvals/approve|reject` | `review:*`/`approvals:*` | unidad (R-165) | IMPLEMENTED | ✅ existe |
| Correcciones | `POST /corrections`, `GET /corrections/event/{id}` | `corrections:*` | unidad | IMPLEMENTED | ✅ existe |
| Reverso | `POST/GET /reversals` (+ aprobación por el plano de revisión) | `reversals:create/read` | unidad | IMPLEMENTED | ❌ **sin UI (fase 9)** |
| Lotes | `/lots*` (+ AC-L01…L15) | `lots:*` | unidad | IMPLEMENTED | ✅ existe |
| Maestros (20) | `/masters/*` | `masters:*` | por maestro | IMPLEMENTED | ⚠️ 7 nuevos + áreas sin desplegar |
| Auditoría | `/audit/*` | `audit:read` | inquilino | IMPLEMENTED | ⚠️ filtros reales sin desplegar |
| Notificaciones | `/notifications/*` | destinatario | por usuario | IMPLEMENTED | ⚠️ sin desplegar |
| Dashboard/KPI | `/dashboard/*` | — | unidad | IMPLEMENTED | ✅ existe |
| SAP | `/sap/*` (8 rutas sin `response_model`, R-112) | `sap:*` | transversal (OD-12) | PARTIAL | ✅ existe |

## 3. Reglas de negocio que el backend exige y el runtime viejo no satisface

| Regla | Exigencia | Contrato frontend requerido | Runtime viejo |
|---|---|---|---|
| `BR-20` | recepción de reproductoras: `received_total = alojadas + dead_on_arrival + rejected_on_arrival` (sin tolerancia; la ausencia no es 0) | tres campos explícitos | **no los envía → 400** |
| `BR-21` | nacimiento incubadora: una fila por sexo (`mixed` excluyente), `chicks_healthy`/`chicks_weak` obligatorios | quitar fila «total»; dos campos | **duplica el total y no los envía → 400** |
| `BR-22` | importación de abuelas: `extra_data.import_plan` tipado + identidades | formulario del plan | **no lo envía → 400** |
| `BR-02`/`BR-04` | despacho: solo huevo fértil; cantidad > 0 | fila única fértil | probable **400** con otras selecciones |

## 4. Lo que el backend NO tiene (nada que consumir)

- Creación automática del lote de abuelas (`R-153`, decisión `AOD-25`).
- Integración SAP real (`P-08`, `BLOCKED_EXTERNAL`).
- Escritura de `sap_config` en empresas (`R-127.b`, `DEFERRED` por `OD-18.b`).

## 5. Fuentes

`BACKEND_ROUTE_MODULE_MATRIX.md` (inventario de 211 rutas) · `BACKEND_API_IMPLEMENTATION_MATRIX.md` · `GA_REM_040_PHASE_8_EVIDENCE.md` (contrato de sesión) · sondas propias del 2026-09-10 (fingerprint §5) · `validators.py` (BR-20/21/22) · `WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX.md` (estado por tranche).

# Contrato de API — Global Avícola

> **Documento:** 06-api-contract.md
> **Versión:** 1.0.0
> **Fecha:** 2026-06-22

---

## 1. CONVENCIONES

- **Base URL:** `/api/v1`
- **Formato:** JSON (request/response)
- **Autenticación:** Bearer JWT en header `Authorization: Bearer <token>`
- **Idioma:** Header `Accept-Language: es|en`
- **Paginación:** Cursor-based para listados grandes
- **Errores:** Formato estándar `{ "error": { "code": "...", "message": "..." } }`

---

## 2. ENDPOINTS POR MÓDULO

### 2.1 Auth

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/auth/login` | Iniciar sesión |
| `POST` | `/auth/refresh` | Refrescar token |
| `POST` | `/auth/logout` | Cerrar sesión |
| `GET` | `/auth/me` | Perfil del usuario autenticado |

### 2.2 Users & Roles

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/users` | Listar usuarios |
| `POST` | `/users` | Crear usuario |
| `GET` | `/users/{id}` | Obtener usuario |
| `PUT` | `/users/{id}` | Actualizar usuario |
| `DELETE` | `/users/{id}` | Desactivar usuario (soft) |
| `GET` | `/roles` | Listar roles |
| `POST` | `/roles` | Crear rol |
| `PUT` | `/roles/{id}` | Actualizar rol |
| `GET` | `/permissions` | Listar permisos disponibles |

### 2.3 Masters / Catálogos

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/masters/companies` | Listar empresas |
| `POST` | `/masters/companies` | Crear empresa |
| `GET` | `/masters/farms` | Listar granjas |
| `POST` | `/masters/farms` | Crear granja |
| `GET` | `/masters/houses` | Listar galpones |
| `POST` | `/masters/houses` | Crear galpón |
| `GET` | `/masters/hatcheries` | Listar incubadoras |
| `GET` | `/masters/genetic-lines` | Listar líneas genéticas |
| `GET` | `/masters/breeds` | Listar razas |
| `GET` | `/masters/productive-phases` | Listar fases productivas |
| `GET` | `/masters/suppliers` | Listar proveedores |
| `GET` | `/masters/feed-types` | Listar tipos de alimento |
| `GET` | `/masters/vaccines` | Listar vacunas |
| `GET` | `/masters/mortality-causes` | Listar causas de mortalidad |
| `GET` | `/masters/rejection-reasons` | Listar motivos de rechazo |

### 2.4 SAP References

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/sap/references` | Listar referencias SAP |
| `POST` | `/sap/references/import` | Importar referencias (CSV/JSON) |
| `GET` | `/sap/references/{type}` | Filtrar por tipo (PO, TO, Material, etc.) |
| `POST` | `/sap/sync/export` | Iniciar exportación a SAP |
| `GET` | `/sap/sync/jobs` | Listar trabajos de sincronización |
| `GET` | `/sap/sync/jobs/{id}` | Detalle de trabajo de sincronización |
| `GET` | `/sap/errors` | Listar errores de SAP pendientes |

### 2.5 Lots

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/lots` | Listar lotes (filtros: granja, fase, estado) |
| `POST` | `/lots` | Crear lote |
| `GET` | `/lots/{id}` | Detalle de lote (con fases, saldos) |
| `PUT` | `/lots/{id}` | Actualizar lote |
| `POST` | `/lots/{id}/close` | Cerrar lote |
| `POST` | `/lots/activate-manual` | Activar lote manualmente (opening balance) |
| `GET` | `/lots/{id}/balances` | Saldos actuales del lote |
| `GET` | `/lots/{id}/phases` | Fases del lote |

### 2.6 Operations / Eventos Operativos

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/operations/feed` | Registrar alimento |
| `POST` | `/operations/weight` | Registrar pesaje |
| `POST` | `/operations/mortality` | Registrar mortalidad |
| `POST` | `/operations/vaccination` | Registrar vacunación |
| `POST` | `/operations/medication` | Registrar medicamento |
| `POST` | `/operations/bird-reception` | Registrar recepción de aves |
| `POST` | `/operations/bird-distribution` | Registrar distribución de aves |
| `POST` | `/operations/bird-exit` | Registrar salida de aves |
| `POST` | `/operations/egg-collection` | Registrar recolección de huevos |
| `POST` | `/operations/egg-classification` | Registrar clasificación de huevos |
| `POST` | `/operations/egg-dispatch` | Registrar despacho de huevos |
| `POST` | `/operations/egg-reception-hatchery` | Registrar recepción en incubadora |
| `POST` | `/operations/incubation-load` | Registrar carga de incubación |
| `POST` | `/operations/ovoscopy` | Registrar ovoscopia |
| `POST` | `/operations/birth` | Registrar nacimiento |
| `POST` | `/operations/chick-dispatch` | Registrar despacho de pollitos |
| `POST` | `/operations/farm-inspection` | Registrar inspección de granja |
| `POST` | `/operations/transport-inspection` | Registrar inspección de transporte |
| `POST` | `/operations/grandparent-import` | Registrar importación de abuelas |
| `GET` | `/operations` | Listar eventos (filtros avanzados) |
| `GET` | `/operations/{id}` | Detalle de evento operativo |

### 2.7 Review Center

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/review/pending` | Bandeja de revisión (registros pendientes) |
| `POST` | `/review/batches` | Crear lote de revisión |
| `GET` | `/review/batches/{id}` | Detalle de lote de revisión |
| `POST` | `/review/batches/{id}/start-review` | Iniciar revisión |
| `POST` | `/review/batches/{id}/return` | Devolver al operador |
| `POST` | `/review/batches/{id}/complete-review` | Completar revisión |

### 2.8 Corrections

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/corrections` | Registrar corrección (auditada) |
| `GET` | `/corrections/{eventId}` | Ver correcciones de un evento |

### 2.9 Approvals

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/approvals/pending` | Registros pendientes de aprobación |
| `POST` | `/approvals/{eventId}/approve` | Aprobar registro |
| `POST` | `/approvals/{eventId}/reject` | Rechazar registro |
| `POST` | `/approvals/batch-approve` | Aprobar en lote |
| `POST` | `/approvals/consolidate` | Consolidar aprobados |

### 2.10 Audit

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/audit` | Consultar auditoría (filtros avanzados) |
| `GET` | `/audit/{id}` | Detalle de registro de auditoría |
| `GET` | `/audit/event/{eventId}/timeline` | Línea de tiempo de un registro |

### 2.11 Reports & Dashboard

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/dashboard/mobile` | Dashboard móvil (operador) |
| `GET` | `/dashboard/admin` | Dashboard web (supervisor/admin) |
| `GET` | `/reports/lot/{id}` | Reporte completo de lote |
| `GET` | `/reports/kpis/mortality` | KPIs de mortalidad |
| `GET` | `/reports/kpis/feed-conversion` | KPIs de conversión alimenticia |
| `GET` | `/reports/kpis/egg-production` | KPIs de producción de huevos |
| `GET` | `/reports/kpis/hatchery` | KPIs de incubación |
| `GET` | `/reports/sap-comparison` | Comparación SAP vs App |
| `GET` | `/reports/export/{type}` | Exportar reporte (Excel/PDF) |

---

## 3. FORMATO DE RESPUESTA ESTÁNDAR

### Éxito
```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "next_cursor": "eyJ..."
  }
}
```

### Error
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "La cantidad de mortalidad excede el saldo disponible",
    "details": [
      {
        "field": "quantity",
        "message": "Máximo permitido: 950"
      }
    ]
  }
}
```

### Códigos de error HTTP
- `400` — Error de validación / regla de negocio
- `401` — No autenticado
- `403` — No autorizado (sin permiso)
- `404` — Recurso no encontrado
- `409` — Conflicto (idempotencia, duplicado)
- `422` — Entidad no procesable
- `500` — Error interno del servidor

---

## 4. OPENAPI

FastAPI genera documentación OpenAPI automáticamente en:
- `/docs` — Swagger UI
- `/redoc` — ReDoc
- `/openapi.json` — Especificación JSON

# Plan de Pruebas (QA) — Global Avícola

> **Documento:** 07-qa-plan.md
> **Versión:** 1.0.0
> **Fecha:** 2026-06-22

---

## 1. ESTRATEGIA DE PRUEBAS

**Pirámide de testing:**

```
         ┌──────┐
         │ E2E  │  Playwright (flujos críticos)
         ├──────┤
         │ Int. │  API contract tests + DB integration
         ├──────┤
         │ Unit │  Pytest (backend) + Vitest (frontend)
         └──────┘
```

---

## 2. PRUEBAS UNITARIAS

### 2.1 Backend (Pytest)

| Módulo | Qué probar | Cobertura objetivo |
|---|---|---|
| **auth** | JWT creación/validación, RBAC, hashing | 90% |
| **masters** | CRUD de cada entidad, validaciones | 85% |
| **lots** | Creación, fases, activación manual, saldos | 85% |
| **operations** | Cada tipo de evento, reglas de negocio | 90% |
| **review** | Flujo de revisión, estados, transiciones | 90% |
| **approvals** | Aprobación multinivel, rechazo, segregación | 90% |
| **corrections** | Corrección auditada, conservación de original | 90% |
| **audit** | Registro automático, inmutabilidad | 85% |
| **sap** | Idempotencia, reintentos, payloads | 85% |
| **reports** | Cálculo de KPIs, agregaciones | 80% |

### 2.2 Frontend (Vitest + React Testing Library)

| Componente | Qué probar |
|---|---|
| **Formularios** | Validación, envío, estados de error |
| **Tablas** | Paginación, filtros, ordenamiento |
| **Bandeja de revisión** | Renderizado de estados, acciones |
| **Componentes UI** | Renderizado, props, eventos |

---

## 3. PRUEBAS DE INTEGRACIÓN (Backend)

| Prueba | Descripción |
|---|---|
| **API + DB** | Cada endpoint con base de datos de prueba |
| **Auth flow** | Login → token → acceso a endpoint protegido |
| **RBAC** | Usuario sin permiso → 403 |
| **Transacciones** | Rollback en caso de error |
| **Migraciones** | Alembic upgrade/downgrade sin pérdida de datos |

---

## 4. PRUEBAS E2E (Playwright)

### 4.1 Flujos críticos a probar

| # | Flujo | Prioridad |
|---|---|---|
| 1 | Login → Dashboard → Logout | Crítica |
| 2 | Registro de alimento (móvil) | Crítica |
| 3 | Registro de mortalidad (móvil) | Crítica |
| 4 | Envío a revisión → Supervisor revisa | Crítica |
| 5 | Corrección auditada | Crítica |
| 6 | Aprobación → Consolidación | Crítica |
| 7 | Envío a SAP (mock) → Confirmación | Crítica |
| 8 | Rechazo con motivo → Operador reenvía | Alta |
| 9 | Activación manual de lote | Alta |
| 10 | Cierre de lote con resumen | Alta |
| 11 | Cambio de idioma (ES ↔ EN) | Media |
| 12 | CRUD de usuarios y roles | Media |

### 4.2 Matriz de navegadores y viewports

| Navegador | 360×640 | 390×844 | 412×915 | 768×1024 | 1440×900 |
|---|---|---|---|---|---|
| Chrome | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edge | ✅ | ✅ | ✅ | ✅ | ✅ |
| Firefox | ✅ | - | ✅ | ✅ | ✅ |
| Safari | ✅ | ✅ | - | ✅ | ✅ |
| Opera | ✅ | - | - | - | ✅ |
| iOS Safari | - | ✅ | - | ✅ | - |
| Android Chrome | ✅ | - | ✅ | - | - |

---

## 5. PRUEBAS ESPECÍFICAS

### 5.1 Reglas de negocio

| Regla | Prueba |
|---|---|
| BR-01 | Intentar registrar mortalidad > saldo → debe fallar |
| BR-02 | Intentar despachar más huevos de los disponibles → debe fallar |
| BR-03 | Intentar cargar incubadora > recibidos → debe fallar |
| BR-09 | Corregir un valor → verificar que original y corregido se guardan |
| BR-11 | Intentar crear referencia SAP duplicada → debe fallar |
| BR-12 | Enviar mismo payload 2 veces → solo 1 llega a SAP |
| BR-13 | Intentar enviar a SAP sin aprobación → debe fallar |
| BR-14 | Operador intenta aprobar su propio registro → debe fallar |

### 5.2 Auditoría

| Prueba |
|---|
| Cada creación de registro genera AuditLog |
| Cada edición registra previous_values y new_values |
| Cada corrección registra original + corregido |
| Cada aprobación registra responsable y timestamp |
| Cada rechazo registra motivo |
| No se puede modificar un AuditLog |
| No se puede eliminar un AuditLog |

### 5.3 i18n

| Prueba |
|---|
| Cambiar idioma a inglés → todas las etiquetas cambian |
| Cambiar idioma a español → todas las etiquetas cambian |
| Texts no hardcodeados (buscar strings en español sin i18n) |
| Fechas y números usan formato del idioma seleccionado |

### 5.4 SAP Integration

| Prueba |
|---|
| Mock SAP: enviar payload → respuesta simulada OK |
| Mock SAP: enviar payload → respuesta error → reintento |
| Idempotencia: payload duplicado → no se reenvía |
| Payload tiene formato correcto según especificación |
| Error de conexión → reintento con backoff |

---

## 6. HERRAMIENTAS

| Herramienta | Uso |
|---|---|
| **Pytest** | Unit + integration tests backend |
| **HTTPX** | Async HTTP client para tests de API |
| **Vitest** | Unit tests frontend |
| **React Testing Library** | Component tests |
| **Playwright** | E2E cross-browser + mobile |
| **Coverage.py** | Cobertura backend |
| **c8 / istanbul** | Cobertura frontend |
| **GitHub Actions** | CI/CD pipeline de tests |

---

## 7. CRITERIOS DE CALIDAD

- Backend coverage > 80%
- Frontend coverage > 70%
- 0 tests fallando en main branch
- E2E tests pasan en todos los navegadores requeridos
- Todos los flujos críticos cubiertos por E2E
- Reglas de negocio 100% cubiertas por tests unitarios

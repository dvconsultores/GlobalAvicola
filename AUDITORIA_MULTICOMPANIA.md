# 🔍 Auditoría Integral Multi-Compañía — Global Avícola

**Fecha:** 2026-06-29  
**Alcance:** Backend (FastAPI + SQLAlchemy), Frontend (React + Zustand), Integración SAP, UI/UX  
**Objetivo:** Certificar que la aplicación soporta operación multi-compañía con aislamiento de datos correcto

---

## 📊 RESUMEN EJECUTIVO

| Aspecto | Calificación | Estado |
|---------|-------------|--------|
| Modelo de datos multi-compañía | ⭐⭐⭐⭐⭐ | ✅ Robusto |
| Aislamiento backend (servicios) | ⭐⭐⭐⭐☆ | ⚠️ 1 fuga de datos |
| Aislamiento backend (endpoints) | ⭐⭐⭐⭐☆ | ⚠️ 1 endpoint sin filtro |
| SAP multi-compañía | ⭐⭐⭐☆☆ | ⚠️ Adapter no por compañía |
| Frontend: selector compañía (desktop) | ⭐⭐⭐⭐☆ | ✅ Funcional |
| Frontend: selector compañía (mobile) | ⭐☆☆☆☆ | ❌ Inexistente |
| Frontend: contexto de compañía | ⭐⭐☆☆☆ | ⚠️ No se usa en páginas |
| Tests multi-compañía | ⭐⭐⭐☆☆ | ⚠️ Faltan tests SAP |
| UX multi-compañía | ⭐⭐☆☆☆ | ⚠️ Móvil sin indicador |

**Veredicto:** La arquitectura multi-compañía es **sólida en backend** pero requiere correcciones de seguridad y completar la experiencia en frontend, especialmente en móvil. La aplicación **puede operar multi-compañía** pero con limitaciones de UX y un riesgo de seguridad que debe corregirse.

---

## 1. MODELO DE DATOS — ARQUITECTURA

### 1.1 Entidad `Company`

```python
# backend/app/masters/models.py:62-78
class Company(Base):
    __tablename__ = "companies"
    id, name (UNIQUE), tax_id, country, currency
    sap_config: JSON       # ← Diseñado pero NO expuesto en API
    approval_levels: int   # 1-3, por compañía
    is_active: bool
```

✅ **Fortaleza:** Modelo completo. `approval_levels` y `sap_config` por compañía permiten flujos de aprobación y configuración SAP diferenciados.

⚠️ **Gap:** `sap_config` existe en la tabla pero **NO** está en los esquemas Pydantic (`CompanyBase`, `CompanyCreate`, `CompanyRead`). No se puede leer ni escribir vía API.

### 1.2 Estrategia de aislamiento — Dos niveles

| Nivel | Entidades | `company_id` | Significado |
|-------|-----------|-------------|-------------|
| **Obligatorio** | `Farm`, `Hatchery`, `OperationalEvent`, `Evidence`, `Alert`, `Reversal`, `ReviewBatch`, `ApprovalStep`, `SapReference`, `ConsolidatedMovement`, `SapSyncJob`, `SapPayload`, `AuditLog` | NOT NULL, FK | Solo existen dentro de una compañía |
| **Opcional** | `Lot`, `GeneticLine`, `Supplier`, `FeedType`, `Vaccine`, `Medication`, `MortalityCause`, `CullCause`, `Transport`, `ProcessingPlant`, `RejectionReason`, `CorrectionType` | NULLABLE, FK | NULL = catálogo global/compartido entre compañías |
| **Heredado** | `House` (vía Farm), `Incubator`/`Hatcher` (vía Hatchery), `Breed` (vía GeneticLine), `BirdMovement`/`EggMovement`/`FeedMovement` (vía OperationalEvent) | Sin campo propio | Heredan compañía del padre |

✅ **Fortaleza:** Diseño bien pensado. Los catálogos pueden ser globales (NULL) o específicos por compañía. Las entidades core son siempre de una compañía.

⚠️ **Riesgo:** `User.company_id` y `Role.company_id` **no tienen FK** a `companies.id`. Esto es deliberado (orden de migraciones) pero permite registros huérfanos si se borra una compañía.

---

## 2. BACKEND — AISLAMIENTO EN CONSULTAS

### 2.1 `MasterService` — Motor central de aislamiento

```python
# backend/app/masters/service.py:31-39
def _apply_company_filter(self, query):
    if self.is_super_admin:
        return query          # Super Admin ve todo
    if not self.user_company_id:
        return query          # Sin compañía → sin filtro
    if hasattr(self.model, "company_id"):
        query = query.where(self.model.company_id == self.user_company_id)
    return query
```

✅ Usado por: `LotService`, `OperationsService`, masters CRUD genérico.  
✅ `create()` auto-asigna `company_id` del usuario autenticado.  
✅ `get_by_id()` aplica filtro → cross-company access devuelve 404.

### 2.2 Servicios con filtro directo (sin `MasterService`)

| Servicio | Archivo | Filtro |
|----------|---------|--------|
| `DashboardService` | `dashboard/service.py:14` | `OperationalEvent.company_id == self.company_id` ✅ |
| `ReportsService` | `reports/service.py:18` | `OperationalEvent.company_id == self.company_id` ✅ |
| `CorrectionsService` | `corrections/service.py:16` | Validación de pertenencia ✅ |
| `ApprovalService` | `review/service.py:19` | `self.company_id = current_user.get("company_id")` ✅ |
| `SapService` | `integrations/sap/service.py:30` | Todas las queries filtradas ✅ |
| `AuditService` | `audit/` | `AuditLog.company_id` ✅ |

✅ **Fortaleza:** Todos los servicios aplican filtro por `company_id`. El patrón es consistente.

### 2.3 🔴 CRÍTICO — Fuga de datos en trazabilidad

**Archivo:** `backend/app/lots/router.py:149-169`

```python
@router.get("/{lot_id}/traceability", ...)
async def get_lot_traceability(lot_id: int, ...):
    result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = result.scalar_one_or_none()
    # ... consultas de EggBatch, ChickBatch sin filtro de compañía
```

**Problema:** El endpoint busca el `Lot` directamente sin aplicar `_apply_company_filter`. Un usuario de la Compañía A puede consultar la trazabilidad de un lote de la Compañía B simplemente conociendo su `lot_id`.

**Riesgo:** Fuga de datos entre compañías. **Crítico.**

**Solución recomendada:**
```python
# Usar LotService que sí aplica filtro de compañía
from .service import LotService
svc = LotService(db, current_user)
lot = await svc.get_lot(lot_id)  # ← Ya valida compañía
```

### 2.4 🟡 MEDIO — Creación de lote no valida granja

**Archivo:** `backend/app/lots/service.py:76`

```python
lot = Lot(
    company_id=self.company_id,
    farm_id=data.farm_id,  # ← No verifica que farm.company_id == self.company_id
    ...
)
```

**Problema:** Un usuario podría pasar un `farm_id` de otra compañía. El lote quedaría con `company_id` del usuario pero `farm_id` de otra empresa, creando inconsistencia.

**Riesgo:** Bajo-Medio (el lote es de la compañía del usuario, pero la granja no).

**Solución recomendada:** Validar que `Farm.company_id == self.company_id or Farm.company_id is None` antes de crear el lote.

---

## 3. AUTENTICACIÓN Y CAMBIO DE COMPAÑÍA

### 3.1 JWT con `company_id`

```python
# backend/app/auth/security.py:37-38
if "company_id" in to_encode and to_encode["company_id"] is not None:
    to_encode["company_id"] = str(to_encode["company_id"])
```

✅ El token JWT incluye `company_id`.  
✅ `get_current_user` recarga el usuario desde BD en cada request (no confía solo en el token).  
✅ `is_super_admin` se determina por permisos `module="*"` + `scope_type="all"`.

### 3.2 `POST /switch-company` (Super Admin)

```python
# backend/app/auth/service.py:152-173
async def switch_company(self, company_id: int, current_user: dict):
    if not current_user.get("is_super_admin"):
        raise HTTPException(403, "Solo super administradores...")
    # Valida que la compañía existe y está activa
    # Emite nuevos tokens con el nuevo company_id
```

✅ Solo Super Admin puede cambiar.  
✅ Valida que la compañía destino existe y está activa.  
✅ Emite tokens frescos con el nuevo `company_id`.

### 3.3 Dependencias de seguridad

| Dependencia | Archivo | Comportamiento |
|-------------|---------|---------------|
| `get_current_user` | `auth/security.py:74` | Extrae `company_id` del token + BD |
| `get_company_filter` | `auth/security.py:130` | Super Admin → None; usuario → su company_id |
| `require_company` | `auth/security.py:140` | 403 si no tiene compañía asignada |

✅ Diseño correcto y seguro.

---

## 4. INTEGRACIÓN SAP MULTI-COMPAÑÍA

### 4.1 Modelos SAP con `company_id`

Todas las 5 tablas SAP tienen `company_id` con FK a `companies.id`:
`SapReference`, `ConsolidatedMovement`, `SapSyncJob`, `SapPayload`, `SapResponse`

✅ Correcto.

### 4.2 `SapService` — Filtrado por compañía

```python
# backend/app/integrations/sap/service.py:30
self.company_id = current_user.get("company_id")
```

Todas las queries (import, list, consolidate, export, retry, jobs, errors, payloads) aplican `company_id`. ✅

### 4.3 🟡 MEDIO — Adapter SAP no usa `company.sap_config`

```python
# backend/app/integrations/sap/service.py:34-37
def get_adapter(self) -> SapIntegrationAdapter:
    if self._adapter is None:
        # TODO: read from config/env which adapter to use
        self._adapter = ManualSapAdapter()
    return self._adapter
```

**Problema:** El adapter siempre es `ManualSapAdapter()`. No lee `company.sap_config` para determinar qué entorno SAP (mandante, sistema) usar para cada compañía.

**Impacto:** Si dos compañías usan mandantes SAP distintos (ej. mandante 100 vs 200), el sistema no puede diferenciarlos. Actualmente no es bloqueante porque SAP está en modo manual, pero **bloquea la puesta en producción multi-compañía con SAP real.**

### 4.4 🟡 MEDIO — `sap_config` no expuesto en API

El campo `sap_config` (JSON) existe en la tabla `companies` pero NO en los esquemas Pydantic `CompanyCreate`/`CompanyRead`. No hay forma de configurar SAP por compañía vía API o UI.

---

## 5. FRONTEND — EXPERIENCIA MULTI-COMPAÑÍA

### 5.1 Store de compañía (`company.store.ts`)

```typescript
// frontend/src/stores/company.store.ts
activeCompanyId: number | null
activeCompanyName: string | null
companies: CompanyOption[]
switchCompany(id, name) → POST /switch-company → actualiza tokens
```

✅ Store bien diseñado.  
⚠️ `activeCompanyId` **nunca se usa** fuera de `Header.tsx`. Ninguna página, servicio o filtro lo consulta.

### 5.2 Selector de compañía — Desktop

**Archivo:** `frontend/src/components/layout/Header.tsx:61-115`

| Modo | Usuario | Comportamiento |
|------|---------|---------------|
| Super Admin | `is_super_admin === true` | Dropdown con lista de compañías, puede cambiar |
| Regular | `is_super_admin === false` | Badge estático con nombre de compañía |

✅ Funcionalidad correcta en desktop.  
✅ Switch llama `POST /switch-company` y refresca tokens + perfil.

### 5.3 🔴 CRÍTICO — Móvil sin selector ni indicador de compañía

| Componente | ¿Muestra compañía? |
|------------|-------------------|
| `Header.tsx` (mobile) | ❌ Solo logo, nombre, tagline, idioma |
| `MobileNav.tsx` | ❌ Sin referencia a compañía |
| `MobileDrawer.tsx` | ❌ Sin referencia a compañía |

**Problema:** Un operador móvil **no puede ver en qué compañía está trabajando** ni cambiar de compañía. Esto es crítico para operadores que manejan múltiples compañías.

### 5.4 Páginas — Sin contexto de compañía visible

| Página | ¿Muestra compañía activa? |
|--------|--------------------------|
| `DashboardPage` | ❌ KPIs sin indicar compañía |
| `ProcessStagePage` | ❌ Procesos sin indicar compañía |
| `OperationFormPage` | ❌ Formulario sin indicar compañía |
| `LotListPage` | ❌ Lista sin indicar compañía |
| `LotDetailPage` | ❌ Detalle sin indicar compañía |
| `MasterListPage` | ❌ Maestros sin indicar compañía |
| `SapManagerPage` | ❌ SAP sin indicar compañía |
| `ProfilePage` | ❌ Perfil sin mostrar compañía |
| `UsersPage` | ❌ `company_id` en tipo de formulario pero sin selector UI |

⚠️ **Riesgo UX:** Un usuario que maneja varias compañías no tiene confirmación visual de en cuál está operando. Podría registrar operaciones en la compañía equivocada sin darse cuenta.

### 5.5 API Layer — Contexto implícito vía JWT

La capa API **no** envía `company_id` como header o parámetro. El backend lo extrae del JWT. Esto es correcto como patrón de seguridad, pero significa que el frontend **depende completamente del backend** para el filtrado.

✅ Seguridad: correcto (no se puede manipular desde el cliente).  
⚠️ UX: no hay feedback visual de "estás viendo datos de Compañía X".

---

## 6. TESTS MULTI-COMPAÑÍA

### 6.1 Tests existentes

**Archivo:** `backend/tests/test_multi_company.py` — 5 tests:

| Test | Verifica |
|------|----------|
| `test_company_a_cannot_access_company_b_operations` | Listado filtrado ✅ |
| `test_company_a_cannot_get_company_b_event` | Acceso directo 404 ✅ |
| `test_super_admin_sees_all_companies` | Super Admin sin filtro ✅ |
| `test_company_a_cannot_access_company_b_houses` | Cross-company farm/house ✅ |
| `test_idempotency_key_prevents_duplicate` | Idempotencia con tokens ✅ |

### 6.2 🟡 Tests faltantes

| Área | Test faltante |
|------|--------------|
| SAP | Compañía A no ve payloads SAP de Compañía B |
| SAP | Compañía A no puede exportar a SAP datos de Compañía B |
| SAP | Switch de compañía regenera correctamente el scope SAP |
| Trazabilidad | Compañía A no ve trazabilidad de lote de Compañía B |
| Usuarios | Asignar usuario a compañía inexistente |
| Aprobaciones | Lote de Compañía A no aparece en revisión de Compañía B |
| Dashboard | KPIs de Compañía A vs Compañía B |

---

## 7. RECOMENDACIONES — PLAN DE ACCIÓN

### 🔴 Críticas (corregir antes de producción multi-compañía)

| # | Acción | Archivo | Esfuerzo |
|---|--------|---------|----------|
| 1 | **Corregir fuga en trazabilidad** — usar `LotService` en `get_lot_traceability` | `backend/app/lots/router.py:149` | 5 min |
| 2 | **Validar farm.company_id al crear lote** | `backend/app/lots/service.py:76` | 10 min |
| 3 | **Agregar indicador de compañía en móvil** — badge en Header mobile y/o MobileDrawer | `frontend/src/components/layout/Header.tsx` | 30 min |

### 🟡 Altas (antes de producción multi-compañía)

| # | Acción | Archivo | Esfuerzo |
|---|--------|---------|----------|
| 4 | **Exponer `sap_config` en API** — agregar a `CompanyBase` schema | `backend/app/masters/schemas.py` | 5 min |
| 5 | **Usar `company.sap_config` en adapter** — leer configuración SAP por compañía | `backend/app/integrations/sap/service.py` | 1-2 h |
| 6 | **Agregar badge de compañía en páginas clave** — Dashboard, ProcessStage, SAP Manager | Varios `frontend/src/pages/` | 1 h |
| 7 | **Agregar selector de compañía en UsersPage** — dropdown para asignar `company_id` | `frontend/src/pages/users/UsersPage.tsx` | 30 min |
| 8 | **Mostrar compañía en ProfilePage** | `frontend/src/pages/users/ProfilePage.tsx` | 15 min |

### 🟢 Medias (mejora continua)

| # | Acción | Esfuerzo |
|---|--------|----------|
| 9 | Agregar tests multi-compañía para SAP (payloads, export, sync jobs) | 1 h |
| 10 | Agregar test de fuga en trazabilidad | 15 min |
| 11 | Wire `company.switchSuccess`/`switchError` i18n → toast notifications | 15 min |
| 12 | Agregar FK constraint a `users.company_id` y `roles.company_id` (migración) | 30 min |
| 13 | Documentar arquitectura multi-compañía en `docs/` | 30 min |

---

## 8. CONCLUSIÓN

La aplicación Global Avícola tiene una **arquitectura multi-compañía bien diseñada en backend**, con:

- ✅ Modelo de datos completo con dos niveles de aislamiento (obligatorio/opcional)
- ✅ `MasterService` como motor central de filtrado por compañía
- ✅ Servicios de dominio (Dashboard, Reports, SAP, Review, Corrections, Audit) correctamente aislados
- ✅ JWT con `company_id` y dependencias de seguridad robustas
- ✅ `POST /switch-company` para cambio de contexto por Super Admin
- ✅ Tests multi-compañía con cobertura básica
- ✅ Store Zustand para manejo de estado de compañía en frontend

**Se requiere acción inmediata en 3 áreas:**

1. 🔴 **Corregir fuga de datos en endpoint de trazabilidad** — riesgo de seguridad real
2. 🔴 **Agregar indicador de compañía en interfaz móvil** — los operadores móviles no saben en qué compañía están
3. 🟡 **Completar integración SAP multi-compañía** — el adapter no usa `company.sap_config`

Con estas correcciones, la aplicación estará **certificada para operación multi-compañía segura** en producción.

---

*Auditoría generada el 2026-06-29 por análisis exhaustivo de código fuente (backend + frontend + docs).*

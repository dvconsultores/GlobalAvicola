# VALIDACIÓN DEL PLAN — Correcciones y Ajustes

**Documento:** VALIDACION_PLAN.md  
**Fecha:** 2026-06-24  
**Propósito:** Auditoría del plan propuesto contra el código real. Corregir errores, ajustar prioridades, dar un plan accionable y verdadero.

---

## ⚠️ CORRECCIONES CRÍTICAS AL PLAN ANTERIOR

El plan `AUDIT_REDISEÑO_INTEGRAL.md` contiene **errores importantes** por haber sido escrito sin leer todo el código real. Este documento lo corrige.

---

## 1. LO QUE EL PLAN DIJO MAL

### ❌ ERROR #1: "Mobile true NO EXISTE"

**Lo que dice el plan:** *"No hay true mobile UI, solo responsive web"*  
**La realidad:** La arquitectura mobile/web **YA EXISTE y funciona** vía `user.view_type`:

```tsx
// AppLayout.tsx — YA IMPLEMENTADO
const isMobileUser = user?.view_type === 'mobile'

return (
  <div>
    {!isMobileUser && <Sidebar />}      // ← Desktop/web: Sidebar completo
    <Header />
    <main className={`${!isMobileUser ? 'lg:ml-64' : ''}`}>
      <Outlet />
    </main>
    {isMobileUser && <MobileNav />}     // ← Mobile: Bottom nav 4 items
  </div>
)
```

```tsx
// App.tsx — YA IMPLEMENTADO
function WebOnlyRoute({ children }) {
  const { user } = useAuthStore()
  if (user?.view_type === 'mobile') return <Navigate to="/" replace />
  return <>{children}</>
}
// Rutas web-only: /review, /approvals, /audit, /sap, /users
// Rutas compartidas: /operations, /lots, /reports, /dashboard
```

**Estado real:** La separación existe y es correcta por diseño. El campo `view_type` en el JWT controla qué ve cada usuario.

**Lo que FALTA en mobile (ajustado):**
1. ❌ Header móvil NO tiene botón de hamburger/menú
2. ❌ No hay página "Mis Registros Pendientes" para operador
3. ❌ MobileNav solo tiene 4 items (Home, Lots, Ops, Reports) — falta Pending
4. ❌ Los formularios de operaciones no están optimizados para táctil (campos muy pequeños)

---

### ❌ ERROR #2: "Sprint 1 propone crear useResponsive hook + routing dual"

**Lo que dice el plan:** Crear `useResponsive.ts`, `MobileShell`, `WebShell`, refactorizar `App.tsx`  
**La realidad:** Hacer esto **destruiría la arquitectura existente** que ya funciona correctamente.

**Corrección:** NO crear routing dual por viewport. La arquitectura actual (por `view_type`) es MEJOR porque:
- Un admin puede usar desktop o móvil con vista web
- Un operador siempre ve vista mobile sin importar el dispositivo
- Es coherente con el modelo de negocio (roles definen qué ves)

**Lo que sí hay que hacer (Sprint 1 corregido):**
- Agregar hamburger menu al Header mobile (slide-out drawer)
- Agregar página `/pending` para operadores mobile
- Añadir "Pending" al MobileNav (5to item)

---

### ❌ ERROR #3: "El plan propone 12-16 personas y 10 semanas para implementar todo"

**La realidad:** Muchas funcionalidades ya existen y solo necesitan ajustes. El esfuerzo real es **significativamente menor**. Con 3-4 developers buenos, se puede completar el MVP en 6-8 semanas.

---

## 2. AUDITORÍA REAL: LO QUE REALMENTE EXISTE

### Frontend — Estado real verificado en código

| Módulo | Archivo | Estado | Notas |
|--------|---------|--------|-------|
| **Login** | LoginPage.tsx | ✅ Completo | JWT, i18n, validación |
| **Layout Desktop** | AppLayout, Sidebar, Header | ✅ Completo | Sidebar oculto en mobile |
| **Layout Mobile** | MobileNav, Header | ⚠️ Incompleto | Falta hamburger menu |
| **Dashboard** | DashboardPage.tsx | ✅ Funcional | KPIs básicos, charts |
| **Lotes - Lista** | LotListPage.tsx | ✅ Funcional | Filtros, tipo, estado |
| **Lotes - Detalle** | LotDetailPage.tsx | ✅ Funcional | STAGE_OPERATIONS por tipo, KPIs |
| **Operaciones - Lista** | OperationListPage.tsx | ✅ Funcional | Filtros, paginación |
| **Operaciones - Formulario** | OperationFormPage.tsx | ✅ Funcional | 24 tipos, campos dinámicos |
| **Operaciones - Detalle** | OperationDetailPage.tsx | ✅ Funcional | Todos los campos |
| **Revisión** | ReviewCenter.tsx | ✅ Funcional | Filtros, bulk, estados |
| **Revisión Detalle** | ReviewDetail.tsx | ✅ Funcional | Corregir, aprobar, rechazar |
| **Corrección** | CorrectionForm.tsx | ✅ Funcional | Auditoría de cambio |
| **Aprobaciones** | ApprovalPanel.tsx | ✅ Funcional | Bulk approve/reject |
| **Reportes** | ReportsPage.tsx | ⚠️ Básico | Charts existentes, falta profundidad |
| **Reporte Lote** | LotReportPage.tsx | ⚠️ Básico | Datos OK, gráficas básicas |
| **SAP Comparación** | SapComparisonPage.tsx | ⚠️ Básico | Solo datos en tabla |
| **SAP Manager** | SapManagerPage.tsx | ⚠️ Básico | Consolidar/exportar manual |
| **Auditoría** | AuditPage.tsx | ✅ Funcional | Log inmutable |
| **Maestros** | MasterListPage.tsx | ✅ Funcional | CRUD genérico para 12+ entidades |
| **Usuarios** | UsersPage.tsx | ✅ Funcional | CRUD completo |
| **Perfil** | ProfilePage.tsx | ✅ Funcional | Cambio contraseña |
| **i18n** | ES/EN JSONs | ✅ Completo | 300+ claves bilingüe |

**Frontend real:** ~75% completo (no 60% como decía el plan)

---

### STAGE_OPERATIONS — Brechas Identificadas en Código Real

El código actual (`LotDetailPage.tsx`) tiene:

```javascript
// GRANDPARENT (Progenitoras)
grandparent: [
  farm_inspection, bird_reception, bird_distribution, feed_registration,
  weight_recording, mortality_recording, vaccination, medication, bird_exit
]
// ❌ FALTA: egg_collection, egg_classification, egg_dispatch
// ❌ (Las progenitoras SÍ producen huevos para incubadora)
```

```javascript
// BREEDER (Reproductoras)  
breeder: [
  farm_inspection, bird_reception, bird_distribution, feed_registration,
  weight_recording, mortality_recording, vaccination, medication,
  egg_collection, egg_classification, egg_dispatch, bird_exit
]
// ✅ CORRECTO para fase producción
// ❌ FALTA: fase cría (sin huevos) vs fase producción (con huevos)
// La fase cría de reproductoras es igual a progenitoras sin huevos
```

```javascript
// BROILER (Engorde)
broiler: [
  farm_inspection, bird_reception, feed_registration, weight_recording,
  mortality_recording, vaccination, medication, lot_closure
]
// ❌ FALTA: bird_distribution (distribución entre galpones)
// ❌ FALTA: cull_recording (descarte)
// ❌ FALTA: chick_dispatch → despacho a planta
```

```javascript
// ❌ FALTA COMPLETAMENTE: Etapa de INCUBADORA/HATCHERY
// No existe 'hatchery' en STAGE_OPERATIONS
// Necesita: egg_reception_hatchery, incubation_load, ovoscopy,
//           transfer_to_hatcher, birth_registration, chick_dispatch
```

---

### Backend — Estado real verificado en código

| Módulo | Estado | Notas |
|--------|--------|-------|
| **Auth + JWT** | ✅ Completo | view_type en JWT |
| **RBAC** | ✅ Completo | Permisos granulares |
| **Maestros** | ✅ Completo | 20+ entidades |
| **Lotes** | ✅ Completo | CRUD, fases, opening balance |
| **Operaciones** | ✅ Completo | 24 tipos, sub-elementos |
| **Revisión/Corrección** | ✅ Completo | Flujo completo |
| **Aprobación** | ✅ Completo | Individual y batch |
| **AuditLog** | ✅ Completo | Inmutable |
| **Multi-compañía** | ✅ Completo | Aislamiento company_id |
| **Dashboard** | ✅ Funcional | KPIs básicos |
| **Reports KPIs** | ⚠️ Básico | Falta conversión, yield |
| **SAP Layer** | ⚠️ Básico | Consolidar/exportar, no automático |
| **EggBatch/ChickBatch** | ❌ No existe | Trazabilidad generacional |
| **Notificaciones** | ❌ No existe | Real-time para aprobadores |

**Backend real:** ~70% completo

---

## 3. BRECHAS REALES — CORREGIDAS Y PRIORIZADAS

### 🔴 CRÍTICAS (Bloquean funcionalidad avícola core)

| # | Brecha | Impacto Operativo | Dificultad |
|---|--------|-------------------|------------|
| 1 | **Incubadora/Hatchery no tiene etapa en UI** | Operador de incubadora no puede registrar | Media |
| 2 | **Progenitoras sin operaciones de huevo** | Trazabilidad genética rota | Pequeña |
| 3 | **EggBatch/ChickBatch no existe** | No se sabe de dónde vienen los pollitos | Alta |
| 4 | **Broiler incompleto (distribución, descarte)** | Operaciones faltantes para engorde | Pequeña |
| 5 | **Mobile Header sin hamburger** | Operador no puede acceder a perfil/config | Pequeña |

### 🟡 ALTAS (Reducen calidad del producto)

| # | Brecha | Impacto | Dificultad |
|---|--------|---------|------------|
| 6 | **SAP sync no automática** | Proceso manual, riesgo de olvido | Alta |
| 7 | **KPIs incompletos** (conversión alimenticia, yield) | No se pueden tomar decisiones con datos | Media |
| 8 | **No hay página "Mis Pendientes" en mobile** | Operador no ve el estado de sus registros | Pequeña |
| 9 | **Reproductora cría vs producción no diferenciada** | Misma lista de operaciones para fases distintas | Media |
| 10 | **Reportes no son analíticos** | Gráficas básicas sin benchmarks ni alertas | Alta |

### 🟢 MEDIAS (Mejoran UX sin bloquear)

| # | Brecha | Impacto | Dificultad |
|---|--------|---------|------------|
| 11 | **Offline mode no existe** | Pérdida de registro si no hay WiFi | Muy Alta |
| 12 | **Formularios móvil no optimizados** | UX mejorable en campo | Media |
| 13 | **No hay alertas por desviación** (peso, mortalidad) | Sin visibilidad de anomalías | Media |
| 14 | **Dashboard no tiene "Lotes por etapa"** | Visión global no clara | Pequeña |
| 15 | **Masters sin CRUD de edición** | Solo lista, no formulario de edición | Media |

### 🔵 BAJAS (Nice to have)

| # | Brecha | Impacto | Dificultad |
|---|--------|---------|------------|
| 16 | **Notificaciones real-time** | UX mejorada para aprobadores | Alta |
| 17 | **Export PDF/Excel** | Reportes descargables | Media |
| 18 | **Dark mode** | Preferencia visual | Media |
| 19 | **Video tutorials** | Onboarding | Baja |
| 20 | **Biometric auth** | iOS/Android nativo | Muy Alta |

---

## 4. PLAN DE IMPLEMENTACIÓN CORREGIDO

### Priorización Real (No 10 semanas, sino 4-6 semanas con equipo de 3-4 devs)

---

### SPRINT 1 — Mobile UX + Etapas Completas (2 semanas)
**Objetivo:** Completar las brechas funcionales críticas que bloquean el uso real.

**Frontend (4-5 días):**

**T-F101: Agregar hamburger menu al Header mobile**
```tsx
// Header.tsx — AGREGAR botón hamburger
import { Menu } from 'lucide-react'

// Agregar estado y drawer slide-out
const [drawerOpen, setDrawerOpen] = useState(false)

// Header MÓVIL ya existe (lg:hidden), agregar botón menu:
<button onClick={() => setDrawerOpen(true)} className="p-2 text-white">
  <Menu size={24} />
</button>

// Crear MobileDrawer.tsx con:
// - Link al Perfil
// - Cambio de idioma  
// - Cerrar sesión
// - Otros links según rol
```

**T-F102: Agregar página Mis Registros Pendientes (`/my-pending`)**
```tsx
// Nuevo: pages/operations/MyPendingPage.tsx
// - Lista de eventos registrados por el usuario actual
// - Estados con colores (Registrado → Devuelto → Aprobado)
// - Filtro por estado
// - Botón "Ver" y "Corregir" cuando está devuelto
```

**T-F103: Agregar "Pending" al MobileNav**
```tsx
// MobileNav.tsx — AGREGAR item
{ path: '/my-pending', labelKey: 'nav.myPending', Icon: Clock, fallback: 'Pendientes' }
// Cambiar de 4 a 5 items
```

**T-F104: Completar STAGE_OPERATIONS (progenitoras + hatchery + broiler)**
```typescript
// LotDetailPage.tsx — CORREGIR STAGE_OPERATIONS

grandparent: [
  // Fases operativas (igual que antes)
  farm_inspection, bird_reception, bird_distribution, feed_registration,
  weight_recording, mortality_recording, vaccination, medication,
  // AGREGAR: operaciones de huevo para progenitoras
  egg_collection, egg_classification, egg_dispatch,
  bird_exit
]

broiler: [
  // AGREGAR: los que faltan
  farm_inspection, bird_reception, bird_distribution,  // ← AGREGAR bird_distribution
  feed_registration, weight_recording, mortality_recording,
  cull_recording,  // ← AGREGAR
  vaccination, medication,
  chick_dispatch,  // ← AGREGAR (despacho a planta)
  lot_closure
]

// AGREGAR ETAPA NUEVA: hatchery (Incubadora)
hatchery: [
  hatchery_inspection,       // Inspección de incubadora
  egg_reception_hatchery,    // Recepción de huevos
  incubation_load,           // Carga de incubadora
  ovoscopy,                  // Ovoscopia (día 7, día 18)
  transfer_to_hatcher,       // Transferencia a nacedora
  birth_registration,        // Registro de nacimiento
  chick_dispatch,            // Despacho de pollitos
]
```

**T-F105: Reproductroras — diferenciar Cría vs Producción**
```typescript
// PROBLEMA: 'breeder' es un solo tipo, pero tiene dos fases (cría y producción)
// SOLUCIÓN: Usar el campo lot.current_phase para mostrar operaciones distintas
// En LotDetailPage:

const phase = lot.current_phase?.name?.toLowerCase() || ''
const isProductionPhase = phase.includes('produccion') || phase.includes('postura')

const breederOps = isProductionPhase
  ? [...opsCria, egg_collection, egg_classification, egg_dispatch]  // Producción: cría + huevos
  : [...opsCria]  // Solo cría: sin huevos
```

**Backend (3-4 días):**

**T-B101: Agregar endpoint `GET /operations?registered_by_me=true`**
```python
# operations/router.py — AGREGAR filtro
@router.get("/operations/")
async def list_operations(
    registered_by_me: bool = False,  # ← AGREGAR
    ...
):
    if registered_by_me:
        query = query.where(OperationalEvent.registered_by_id == current_user['id'])
```

**T-B102: Agregar 'hatchery' como bird_type válido**
```python
# masters/models.py — ACTUALIZAR enum
class BirdTypeEnum(str, Enum):
    GRANDPARENT = "grandparent"
    BREEDER = "breeder"  
    BROILER = "broiler"
    HATCHERY = "hatchery"  # ← AGREGAR
```

**T-B103: Crear migración Alembic para BirdTypeEnum con HATCHERY**

---

### SPRINT 2 — Trazabilidad Generacional (2 semanas)
**Objetivo:** Implementar la funcionalidad diferenciadora: rastrear huevo → pollito.

**Backend (1 semana):**

**T-B201: Crear modelos EggBatch y ChickBatch**
```python
# operations/models.py — AGREGAR

class EggBatch(Base):
    """Lote de huevos despachados desde reproductora hacia incubadora."""
    __tablename__ = "egg_batches"
    
    id: Mapped[int] = PK
    company_id: Mapped[int] = FK(companies)
    source_lot_id: Mapped[int] = FK(lots)          # Lote reproductora/progenitora
    dispatch_event_id: Mapped[int] = FK(operational_events)  # Evento despacho
    destination_hatchery_id: Mapped[int] = FK(hatcheries)
    dispatch_date: Mapped[date]
    total_eggs: Mapped[int]
    fertile_eggs: Mapped[int] = default(0)
    
    # Relaciones
    source_lot: "Lot"
    dispatch_event: "OperationalEvent"
    destination_hatchery: "Hatchery"
    chick_batches: list["ChickBatch"]

class ChickBatch(Base):
    """Lote de pollitos nacidos en incubadora."""
    __tablename__ = "chick_batches"
    
    id: Mapped[int] = PK
    company_id: Mapped[int] = FK(companies)
    source_egg_batch_id: Mapped[int] = FK(egg_batches)  # De qué huevos vinieron
    birth_event_id: Mapped[int] = FK(operational_events)  # Evento nacimiento
    hatchery_id: Mapped[int] = FK(hatcheries)
    destination_lot_id: Mapped[Optional[int]] = FK(lots)  # Lote engorde destino
    birth_date: Mapped[date]
    total_chicks: Mapped[int]
    viable_chicks: Mapped[int]
    
    # Relaciones
    source_egg_batch: "EggBatch"
    destination_lot: Optional["Lot"]
```

**T-B202: Endpoints EggBatch/ChickBatch**
```python
# POST /operations/egg-batches/  — Crear lote huevos al despachar
# GET /operations/egg-batches/{id}/  — Detalle con relaciones
# POST /operations/chick-batches/  — Crear lote pollitos al nacer
# GET /operations/traceability/{lot_id}/  — Cadena completa lote
```

**T-B203: Servicio de trazabilidad**
```python
async def get_lot_traceability(self, lot_id: int) -> dict:
    """
    Retorna la cadena completa de trazabilidad para un lote.
    
    Para lote ENGORDE:
    ← ChickBatch ← EggBatch ← Lote Reproductora/Progenitora
    
    Para lote REPRODUCTORA:
    → EggBatch → ChickBatch → Lote Engorde
    """
```

**Frontend (1 semana):**

**T-F201: Sección "Origen" en LotDetailPage**
```tsx
// Mostrar en detalle de lote de ENGORDE:
"Pollitos originados de:"
├── ChickBatch #3 (22/05/2026)
│   └── Huevos de Lote L-2026-R-001 (Reproductoras)
│       └── 1,250 huevos fértiles
│           └── 1,180 pollitos viables (94.4% eclosión)
```

**T-F202: Formulario de despacho de huevos crea EggBatch automáticamente**
```tsx
// OperationFormPage.tsx — cuando tipo es egg_dispatch
// Al guardar el evento: también crear EggBatch via API
// Agregar campo "Destino: ¿Incubadora o Comercial?"
// Si Incubadora → seleccionar cuál → se crea EggBatch
```

---

### SPRINT 3 — KPIs Completos + Reportes (2 semanas)
**Objetivo:** Completar cálculos de KPIs avícolas profesionales.

**T-B301: Servicio KPIs avanzados**
```python
# kpi_service.py — AGREGAR

async def get_feed_conversion_ratio(self, lot_id) -> float:
    """FCR = kg alimento / kg ganancia total"""

async def get_hatchery_yield(self, egg_batch_id) -> float:
    """% Eclosión = (pollitos viables / huevos fértiles) × 100"""

async def get_posture_percentage(self, lot_id, date_from, date_to) -> float:
    """% Postura = (huevos recolectados / aves alojadas) × 100"""

async def get_mortality_by_week(self, lot_id) -> list[dict]:
    """Mortalidad semanal con tendencia"""

async def get_weight_vs_standard(self, lot_id) -> list[dict]:
    """Peso actual vs estándar genético por semana"""
```

**T-F301: Mejorar reportes con benchmarks**
```tsx
// KPI card mejorada:
// ┌─────────────────────────────┐
// │ Mortalidad   2.1%  ↑ ⚠️   │
// │ Estándar: < 2%             │
// │ [Semana 1-5 trend gráfica] │
// └─────────────────────────────┘
```

**T-F302: Dashboard "Lotes por etapa"**
```tsx
// DashboardPage — AGREGAR sección:
// Progenitoras activas: 2 lotes | 12,000 aves
// Reproductoras cría: 3 lotes | 45,000 aves
// Reproductoras producción: 5 lotes | 60,000 aves
// Incubadoras: 2 | 3 máquinas activas
// Engorde: 8 lotes | 120,000 aves
```

---

### SPRINT 4 — SAP Sync + Polish (2 semanas)
**Objetivo:** Automatizar SAP y pulir UX.

**T-B401: SAP sync automática (polling)**
```python
# integrations/sap/sync_service.py
# Tarea background (FastAPI BackgroundTasks o APScheduler)
# Cada hora:
#   1. Buscar eventos APPROVED y no en SAP aún
#   2. Consolidar en payload SAP
#   3. Enviar (cuando API disponible) o preparar para exportación
#   4. Registrar resultado en SapSyncJob
```

**T-F401: Dashboard SAP mejorado**
```tsx
// SapManagerPage — MEJORAR:
// Estado sync: última sincronización, próxima
// Lista de jobs con estado
// Errores y reintentos
// Estadísticas: X eventos enviados, Y confirmados, Z en error
```

**T-F402: Mobile UX refinement**
```tsx
// Agregar en OperationFormPage:
// - Botones táctiles más grandes (min-h-[48px])
// - Campos de número con teclado numérico (inputMode="numeric")
// - Paso a paso para formularios complejos (multi-step en mobile)
```

---

## 5. RESUMEN EJECUTIVO CORREGIDO

### Estado Real (vs. lo que dijo el plan)

| Aspecto | Plan decía | Realidad verificada |
|---------|-----------|---------------------|
| Frontend completitud | 60% | **~75%** |
| Backend completitud | 40% | **~70%** |
| Mobile view | "No existe" | **Existe vía view_type, incompleto** |
| Routing | "Requiere rediseño total" | **Solo agregar hamburger + 1 página** |
| Esfuerzo total | 10 semanas, 12-16 personas | **6-8 semanas, 3-4 developers** |
| Presupuesto | $95,000 | **$30,000-45,000 más realista** |

### Brechas Reales (vs. exageradas en el plan)

| Brecha | Plan decía | Realidad |
|--------|-----------|---------|
| Mobile architecture | "Reconstruir todo" | **Agregar hamburger + 1 página** |
| Etapas avícolas | "Incompletas" | **Agregar hatchery + fix grandparent eggs** |
| Trazabilidad | "No existe" | **Crear EggBatch/ChickBatch, moderado** |
| SAP | "No integrado" | **Existe, automatizar sync** |
| KPIs | "Incompletos" | **Básicos OK, agregar avanzados** |

---

## 6. ARCHIVOS A MODIFICAR (SPRINT 1)

### Frontend
```
frontend/src/
├── components/layout/
│   ├── Header.tsx                    MODIFICAR: agregar hamburger state + botón
│   ├── MobileNav.tsx                 MODIFICAR: agregar 5to item "Pendientes"
│   └── MobileDrawer.tsx              CREAR: slide-out menú mobile
├── pages/
│   ├── lots/LotDetailPage.tsx        MODIFICAR: STAGE_OPERATIONS (+ hatchery, + grandparent eggs, + broiler fix)
│   └── operations/
│       └── MyPendingPage.tsx         CREAR: página "Mis Registros Pendientes"
└── App.tsx                           MODIFICAR: agregar ruta /my-pending
```

### Backend
```
backend/app/
├── operations/router.py              MODIFICAR: filtro registered_by_me
├── masters/models.py                 MODIFICAR: agregar HATCHERY al BirdTypeEnum
└── alembic/versions/                 CREAR: migración para HATCHERY enum
```

### Traducciones
```
frontend/public/locales/es/translation.json  MODIFICAR: añadir 'nav.myPending', 'nav.hatchery'
frontend/public/locales/en/translation.json  MODIFICAR: mismas claves
```

---

## 7. CHECKLIST INMEDIATO (Esta semana)

```
Sprint 1 - Semana 1 (Jun 24-28):

FRONTEND
[ ] T-F101: Hamburger menu en Header.tsx (estimado: 3h)
    ├── Agregar state hamburger al Header
    ├── Crear MobileDrawer.tsx con links perfil/logout/lang
    └── Verificar en móvil (375px)

[ ] T-F103: Agregar "Pendientes" al MobileNav (estimado: 1h)
    └── Cambiar de 4 a 5 items con ruta /my-pending

[ ] T-F104: Completar STAGE_OPERATIONS (estimado: 2h)
    ├── Agregar egg ops a grandparent[]
    ├── Agregar bird_distribution + cull_recording + chick_dispatch a broiler[]
    └── AGREGAR objeto hatchery[] completo

[ ] T-F102: Crear MyPendingPage.tsx (estimado: 4h)
    ├── Llamar GET /operations?registered_by_me=true
    ├── Mostrar lista con estado color-coded
    └── Link a /review/:id cuando estado = devuelto

BACKEND
[ ] T-B101: Agregar filtro registered_by_me en GET /operations (estimado: 1h)
[ ] T-B102: Agregar HATCHERY al BirdTypeEnum (estimado: 2h incluye migración)

Sprint 1 - Semana 2 (Jul 1-8):
[ ] Testing de los cambios
[ ] Review con operadores de campo (si disponible)
[ ] Fix de bugs detectados
[ ] Commit y deploy a staging
```

---

## 8. DECISIONES DE DISEÑO QUE NO SE DEBEN CAMBIAR

Estos aspectos del plan original son **CORRECTOS** y no deben modificarse:

1. ✅ **Arquitectura view_type (mobile/web)** — Mantener. No usar viewport para routing.
2. ✅ **SAP es auxiliar** — Global Avícola como capa operativa, SAP como sistema principal.
3. ✅ **Flujo: Registro → Revisión → Corrección → Aprobación → SAP** — No cambiar este flujo.
4. ✅ **Auditoría inmutable** — Cada cambio queda registrado, no borrable.
5. ✅ **Multi-compañía con company_id isolation** — Obligatorio, no simplificar.
6. ✅ **i18n ES/EN desde el inicio** — Ya completo, mantener para todos los nuevos textos.
7. ✅ **Zod validación en frontend** — Mantener para todos los formularios.
8. ✅ **JWT con view_type y role** — Mantener, permite stateless auth.

---

## 9. PRÓXIMOS PASOS CORREGIDOS

### HOY (Jun 24)
1. ✅ Leer este documento de validación
2. ✅ Confirmar: "¿Empezamos por Sprint 1 o hay cambios de prioridad?"

### ESTA SEMANA (Jun 24-28)
1. Implementar T-F101 (hamburger menu) — **3 horas**
2. Implementar T-F104 (STAGE_OPERATIONS completo) — **2 horas**
3. Implementar T-F103 (Pending en MobileNav) — **1 hora**
4. Implementar T-B101 (filtro mis registros) — **1 hora**

### PRÓXIMAS 2 SEMANAS (Jul 1-14)
1. Implementar T-F102 (MyPendingPage)
2. Implementar T-B102 (HATCHERY enum + migración)
3. Comenzar T-B201 (EggBatch/ChickBatch modelos)
4. Testing y validación con usuarios reales

### MES 2 (Jul - Ago)
1. Sprint 2: Trazabilidad generacional completa
2. Sprint 3: KPIs avanzados + Reportes
3. Sprint 4: SAP sync automática + Polish

---

## 10. CONCLUSIÓN

**El plan original fue demasiado pesimista sobre lo que existe y demasiado complejo en las soluciones.**

**Lo que realmente hay que hacer:**

1. **3 cambios pequeños en mobile** (hamburger, pendientes, nav item) → Sprint 1, Semana 1
2. **2 correcciones en STAGE_OPERATIONS** (hatchery + grandparent eggs + broiler fix) → Sprint 1, Semana 1
3. **1 nuevo módulo de trazabilidad** (EggBatch/ChickBatch) → Sprint 2
4. **Mejoras de KPI** → Sprint 3
5. **SAP automation** → Sprint 4

**Total: 4-6 semanas con 2-3 developers, presupuesto de $25,000-$40,000.**

La base técnica es sólida. No hay que reconstruir, hay que completar.

---

**Documento de Validación v1.0**  
**Fecha:** 2026-06-24  
**Verificado contra código fuente real**

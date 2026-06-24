# GLOBAL AVÍCOLA — Plan de Implementación UI/UX y Navegación

> **Fecha:** 2026-06-24  
> **Versión:** 1.0  
> **Basado en:** `GLOBAL_AVICOLA_UI_UX_NAVIGATION_AUDIT.md`  
> **Stack:** React 19 + Vite + TypeScript + TailwindCSS v4 + lucide-react  
> **Duración estimada:** ~25 días hábiles (5 semanas)

---

## Índice

1. [Visión General](#1-visión-general)
2. [Plan de Implementación por Fases](#2-plan-de-implementación-por-fases)
3. [Arquitectura de Componentes](#3-arquitectura-de-componentes)
4. [Layout Principal](#4-layout-principal)
5. [Sidebar](#5-sidebar)
6. [Submenús](#6-submenús)
7. [Breadcrumbs](#7-breadcrumbs)
8. [Cards y Tarjetas KPI](#8-cards-y-tarjetas-kpi)
9. [Tablas](#9-tablas)
10. [Formularios](#10-formularios)
11. [Status Badges](#11-status-badges)
12. [Review Panels](#12-review-panels)
13. [Approval Screens](#13-approval-screens)
14. [Audit Timeline](#14-audit-timeline)
15. [SAP Integration Panels](#15-sap-integration-panels)
16. [Mobile Navigation](#16-mobile-navigation)
17. [Responsive Rules](#17-responsive-rules)
18. [i18n Impacts](#18-i18n-impacts)
19. [Pruebas Visuales](#19-pruebas-visuales)
20. [Pruebas de Navegación](#20-pruebas-de-navegación)
21. [Pruebas Mobile](#21-pruebas-mobile)
22. [Pruebas Cross-Browser](#22-pruebas-cross-browser)

---

## 1. Visión General

### 1.1 Objetivo

Transformar la experiencia de usuario de Global Avícola mediante una reestructuración completa de la navegación y una mejora significativa del diseño visual, manteniendo intacta la lógica funcional avícola, los procesos de negocio y la arquitectura backend.

### 1.2 Principios rectores

| Principio | Descripción |
|-----------|-------------|
| **No romper funcionalidad** | Cero cambios en lógica de negocio, reglas de validación, estados de registro, flujos de aprobación |
| **No copiar Atenea** | Inspiración en patrones de navegación, no en código ni branding |
| **Mobile-first real** | Todo cambio se diseña primero para 360px, luego se expande |
| **Jerarquía visible** | El usuario siempre sabe dónde está y cómo llegó |
| **Componentes reutilizables** | Cada pieza UI nueva es un componente atómico |
| **i18n desde el inicio** | Todo texto nuevo tiene traducción ES/EN |
| **Sidebar como centro de navegación** | El menú lateral es la columna vertebral de la experiencia |

### 1.3 Estructura de archivos nueva/refactorizada

```
frontend/src/
├── components/
│   ├── layout/
│   │   ├── AppLayout.tsx          ← REFACTOR: breadcrumbs, sidebar state
│   │   ├── Sidebar.tsx            ← REFACTOR MAYOR: submenús, secciones, colapsable
│   │   ├── SidebarSection.tsx     ← NUEVO: sección con separador (OPERATIVO, REVISIÓN, etc.)
│   │   ├── SidebarItem.tsx        ← NUEVO: item de menú con icono + label
│   │   ├── SidebarSubmenu.tsx     ← NUEVO: submenú colapsable con items anidados
│   │   ├── Header.tsx             ← REFACTOR: breadcrumbs + mejor diseño
│   │   ├── MobileDrawer.tsx       ← REFACTOR MAYOR: jerarquía completa
│   │   ├── MobileNav.tsx          ← REFACTOR: contextual según ruta activa
│   │   └── SubNavHeader.tsx       ← NUEVO: back button + breadcrumbs + título
│   │
│   ├── ui/
│   │   ├── index.ts               ← UPDATE: export nuevos componentes
│   │   ├── Breadcrumbs.tsx        ← NUEVO: migas de pan jerárquicas
│   │   ├── KpiCard.tsx            ← NUEVO: tarjeta KPI con tendencia
│   │   ├── EmptyState.tsx         ← NUEVO: estado vacío con acción
│   │   ├── LoadingSkeleton.tsx    ← NUEVO: skeleton contextual
│   │   ├── FilterPanel.tsx        ← NUEVO: panel de filtros colapsable
│   │   ├── ConfirmDialog.tsx      ← NUEVO: modal de confirmación estándar
│   │   ├── StatusTimeline.tsx     ← NUEVO: línea de tiempo de estados
│   │   ├── SectionCard.tsx        ← NUEVO: tarjeta de sección con título
│   │   └── StepWizard.tsx         ← NUEVO: wizard de formularios multi-paso
│   │
│   └── ... (resto de componentes existentes se mantienen)
│
├── hooks/
│   ├── useSubNavigation.ts        ← NUEVO: pila de navegación para sub-vistas
│   ├── useSidebar.ts              ← NUEVO: estado del sidebar (expandido/seleccionado)
│   └── ... (hooks existentes se mantienen)
│
├── stores/
│   ├── ui.store.ts                ← UPDATE: agregar sidebar state
│   └── ... (stores existentes se mantienen)
│
├── pages/
│   ├── poultry/
│   │   ├── PoultryHubPage.tsx     ← NUEVO (basado en ProcessHubPage)
│   │   └── PoultryStagePage.tsx   ← NUEVO (basado en ProcessStagePage)
│   ├── review/
│   │   ├── ReviewCenter.tsx       ← REFACTOR MAYOR: tabs + filtros
│   │   ├── ReviewList.tsx         ← NUEVO: lista filtrada por estado
│   │   └── ... (resto se mantiene)
│   ├── sap/
│   │   ├── SapManagerPage.tsx     ← REFACTOR: dashboard + tabs
│   │   ├── SapOrdersPage.tsx      ← NUEVO: órdenes de compra SAP
│   │   ├── SapPendingPage.tsx     ← NUEVO: documentos pendientes
│   │   ├── SapErrorsPage.tsx      ← NUEVO: errores SAP
│   │   └── SapLogPage.tsx         ← NUEVO: bitácora SAP
│   ├── audit/
│   │   ├── AuditPage.tsx          ← REFACTOR: dashboard auditoría
│   │   ├── AuditDetail.tsx        ← NUEVO: detalle por lote/usuario/documento
│   │   └── AuditCorrections.tsx   ← NUEVO: cambios y correcciones
│   ├── masters/
│   │   ├── MastersHubPage.tsx     ← NUEVO: agrupación de maestros
│   │   └── ... (MasterListPage se mantiene)
│   ├── settings/
│   │   ├── SettingsPage.tsx        ← NUEVO: configuración general
│   │   ├── ApprovalFlowsPage.tsx   ← NUEVO: flujos de aprobación
│   │   ├── ParamsPage.tsx          ← NUEVO: parámetros del sistema
│   │   └── PreferencesPage.tsx     ← NUEVO: preferencias de usuario
│   ├── dashboard/
│   │   └── DashboardPage.tsx      ← REFACTOR: atajos por rol
│   └── ... (resto de páginas se mantienen)
│
└── App.tsx                        ← REFACTOR MAYOR: nuevas rutas + migración
```

---

## 2. Plan de Implementación por Fases

### 2.1 Fase 1 — Fundación de navegación (Días 1-6)

**Objetivo:** Establecer la nueva arquitectura de navegación sin romper la existente.

#### Día 1-2: Sidebar con submenús colapsables (C-01)

**Archivos a crear:**
- `components/layout/SidebarSection.tsx`
- `components/layout/SidebarItem.tsx`
- `components/layout/SidebarSubmenu.tsx`

**Archivos a modificar:**
- `components/layout/Sidebar.tsx` — refactor mayor
- `stores/ui.store.ts` — agregar estado de sidebar

**Detalle de implementación:**

```tsx
// SidebarSection.tsx
interface SidebarSectionProps {
  label: string;       // i18n key
  fallback: string;
  children: React.ReactNode;
}

// Render: separador visual con texto
// <div className="px-6 py-2 mt-4">
//   <span className="text-[10px] font-bold text-blue-300/50 uppercase tracking-widest">
//     {t(label, fallback)}
//   </span>
// </div>
```

```tsx
// SidebarItem.tsx
interface SidebarItemProps {
  icon?: LucideIcon;
  label: string;
  fallback: string;
  to: string;
  depth?: 0 | 1 | 2;  // Nivel de indentación
  active?: boolean;
  badge?: number;       // Badge opcional (pendientes count)
}

// Render: Link con icono + label + active state
// depth 0: pl-4 (nivel principal)
// depth 1: pl-11 (subfase)
// depth 2: pl-16 (operación)
```

```tsx
// SidebarSubmenu.tsx
interface SidebarSubmenuProps {
  icon: LucideIcon;
  label: string;
  fallback: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

// Render: header clickeable + ChevronDown animado + children colapsables
// Animación: max-height transition + opacity
// ARIA: aria-expanded, aria-controls
```

```tsx
// Sidebar.tsx — Nueva estructura
// Secciones:
//   1. Logo + branding
//   2. Dashboard (item simple)
//   3. Sección "OPERATIVO"
//      - Gestión Avícola (submenú con fases → subfases)
//   4. Sección "REVISIÓN"
//      - Centro de Revisión (submenú con estados)
//      - Aprobaciones (item simple)
//   5. Sección "INTEGRACIÓN"
//      - Integración SAP (submenú)
//   6. Sección "REPORTES"
//      - Reportes (submenú)
//   7. Sección "ADMINISTRACIÓN"
//      - Auditoría (submenú)
//      - Maestros (submenú)
//      - Configuración (submenú)
//      - Usuarios y Roles (item simple)
//   8. User section (avatar, perfil, logout)
```

#### Día 3: Breadcrumbs y SubNavHeader (C-02, C-03)

**Archivos a crear:**
- `components/ui/Breadcrumbs.tsx`

**Archivos a modificar:**
- `components/layout/Header.tsx`
- `components/layout/AppLayout.tsx`

**Detalle de implementación:**

```tsx
// Breadcrumbs.tsx
interface BreadcrumbItem {
  label: string;      // i18n key
  fallback: string;
  to?: string;        // opcional — el último item no tiene link
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  homeIcon?: boolean;  // mostrar icono de casa al inicio
}
```

**Reglas de breadcrumbs por ruta:**

| Ruta | Breadcrumbs |
|------|-------------|
| `/` | Dashboard |
| `/poultry` | Gestión Avícola |
| `/poultry/breeder/rearing` | Gestión Avícola › Reproductoras › Cría |
| `/poultry/breeder/rearing?lot_id=123` | Gestión Avícola › Reproductoras › Cría › Lote L-2026-042 |
| `/review/pending` | Centro de Revisión › Pendientes |
| `/review/123` | Centro de Revisión › Detalle de Revisión |
| `/sap/errors` | Integración SAP › Errores SAP |
| `/audit/lot/123` | Auditoría › Por Lote › Lote L-2026-042 |

#### Día 4: MobileDrawer con jerarquía (C-05)

**Archivos a modificar:**
- `components/layout/MobileDrawer.tsx` — refactor mayor
- `components/layout/Header.tsx`

**Cambios:**
- Drawer muestra la misma jerarquía que el sidebar desktop
- Submenús colapsables (mismo comportamiento que sidebar)
- Cierra al navegar (ya implementado)
- Footer: selector de idioma + perfil + logout

#### Día 5: Active states refinados + i18n (C-14, C-20)

**Archivos a modificar:**
- `components/layout/Sidebar.tsx`
- `public/locales/es/translation.json`
- `public/locales/en/translation.json`

**Active state nuevo:**
```tsx
// Item activo:
className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all
  ${isActive
    ? 'bg-blue-600/30 text-white border-l-2 border-blue-400 shadow-sm'
    : 'text-blue-100/80 hover:bg-blue-700/40 hover:text-white'
  }`}
```

**i18n — Nuevas claves necesarias:**
```json
{
  "nav": {
    "sections": {
      "operational": "OPERATIVO",
      "review": "REVISIÓN",
      "integration": "INTEGRACIÓN",
      "reports": "REPORTES",
      "administration": "ADMINISTRACIÓN"
    },
    "poultry": "Gestión Avícola",
    "grandparent": "Abuelas",
    "grandparentRearing": "Importación",
    "grandparentProduction": "Recepción",
    "breederRearing": "Cría",
    "breederProduction": "Producción",
    "hatchery": "Incubadora",
    "broiler": "Engorde",
    "reviewCenter": "Centro de Revisión",
    "pending": "Pendientes",
    "inReview": "En Revisión",
    "returned": "Devueltos",
    "approved": "Aprobados",
    "consolidated": "Consolidados",
    "sapIntegration": "Integración SAP",
    "purchaseOrders": "Órdenes de Compra",
    "transferOrders": "Órdenes de Transferencia",
    "sapPending": "Documentos Pendientes",
    "sapSent": "Envíos a SAP",
    "sapErrors": "Errores SAP",
    "sapLog": "Bitácora SAP",
    "audit": "Auditoría",
    "auditByLot": "Por Lote",
    "auditByUser": "Por Usuario",
    "auditBySap": "Por Documento SAP",
    "auditCorrections": "Cambios y Correcciones",
    "masters": "Maestros",
    "settings": "Configuración",
    "approvalFlows": "Flujos de Aprobación",
    "parameters": "Parámetros",
    "preferences": "Preferencias"
  }
}
```

#### Día 6: Integración y pruebas de Fase 1

- Verificar que sidebar funciona con todos los roles
- Verificar que MobileDrawer muestra la jerarquía correcta
- Verificar que breadcrumbs aparecen en páginas internas
- Verificar que las rutas existentes siguen funcionando
- Verificar i18n de todos los nuevos textos

---

### 2.2 Fase 2 — Mejora de pantallas operativas (Días 7-13)

#### Día 7-8: ReviewCenter con tabs (C-07)

**Archivos a modificar:**
- `pages/review/ReviewCenter.tsx` — refactor mayor

**Archivos a crear:**
- `components/ui/FilterPanel.tsx`
- `pages/review/ReviewList.tsx`

**Nueva estructura de ReviewCenter:**

```tsx
// ReviewCenter.tsx
export default function ReviewCenter() {
  const [activeTab, setActiveTab] = useState<'pending' | 'in_review' | 'returned' | 'approved' | 'consolidated'>('pending')

  return (
    <div>
      <SubNavHeader title={t('review.center')} />
      
      {/* Tabs de estado */}
      <div className="border-b border-slate-200 mb-6">
        <div className="flex gap-1">
          <TabButton active={activeTab === 'pending'} onClick={() => setActiveTab('pending')}>
            Pendientes <Badge count={pendingCount} />
          </TabButton>
          <TabButton active={activeTab === 'in_review'} onClick={() => setActiveTab('in_review')}>
            En Revisión
          </TabButton>
          {/* ... más tabs */}
        </div>
      </div>

      {/* FilterPanel colapsable */}
      <FilterPanel>
        <FilterGroup label="Lote">
          <input ... />
        </FilterGroup>
        <FilterGroup label="Fecha">
          <input type="date" ... />
          <input type="date" ... />
        </FilterGroup>
        {/* ... más filtros agrupados */}
      </FilterPanel>

      {/* Lista de eventos según tab activo */}
      <ReviewList status={activeTab} />
    </div>
  )
}
```

```tsx
// FilterPanel.tsx
interface FilterPanelProps {
  children: React.ReactNode;
  onClear?: () => void;
}

// Render:
// <details className="bg-white rounded-xl border border-slate-200 mb-4">
//   <summary className="px-4 py-3 font-semibold text-sm cursor-pointer">
//     Filtrar resultados
//   </summary>
//   <div className="px-4 pb-4 flex flex-wrap gap-3">
//     {children}
//   </div>
// </details>
```

#### Día 9-10: Dashboard con quick actions (C-10)

**Archivos a modificar:**
- `pages/dashboard/DashboardPage.tsx` — refactor

**Archivos a crear:**
- `components/ui/KpiCard.tsx`

**KpiCard component:**
```tsx
interface KpiCardProps {
  icon: LucideIcon;
  label: string;        // i18n key
  value: string | number;
  trend?: {
    direction: 'up' | 'down' | 'stable';
    value: string;
  };
  color?: 'blue' | 'green' | 'amber' | 'red' | 'slate';
  onClick?: () => void;
}
```

**Dashboard por rol:**

```tsx
// DashboardPage.tsx
export default function DashboardPage() {
  const { user } = useAuthStore()
  
  // Render diferente según rol
  if (user?.view_type === 'mobile') return <MobileDashboard />
  if (user?.role === 'supervisor') return <SupervisorDashboard />
  if (user?.role === 'approver') return <ApproverDashboard />
  if (user?.role === 'sap_analyst') return <SapDashboard />
  return <AdminDashboard />
}
```

**MobileDashboard:**
```
┌──────────────────────────┐
│ 📋 Mis Lotes Activos     │
│                          │
│ ┌──────────────────────┐ │
│ │ L-2026-042           │ │
│ │ Reproductoras — Cría │ │
│ │ Edad: 12 semanas     │ │
│ │ [Registrar →]        │ │
│ └──────────────────────┘ │
│                          │
│ ⚡ Acciones Rápidas      │
│ ┌──────┐ ┌──────┐ ┌───┐ │
│ │ 💀   │ │ ⚖️   │ │🌾 │ │
│ │Mort. │ │Pesaje│ │Ali│ │
│ └──────┘ └──────┘ └───┘ │
└──────────────────────────┘
```

**SupervisorDashboard:**
```
┌─────────────────────────────────────────────┐
│ 📊 Panel de Supervisión                     │
│                                             │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │
│ │📋 12 │ │✅ 45 │ │⏳ 8  │ │❌ 3  │       │
│ │Pend. │ │Aprob.│ │Rev.  │ │Rech. │       │
│ └──────┘ └──────┘ └──────┘ └──────┘       │
│                                             │
│ 📈 Producción últimas 24h                   │
│ [Gráfico Recharts]                          │
│                                             │
│ 🔄 Últimas operaciones                      │
│ [Tabla compacta]                            │
└─────────────────────────────────────────────┘
```

#### Día 11: Formularios con secciones (C-16)

**Archivos a modificar:**
- `pages/operations/OperationFormPage.tsx`

**Mejoras:**
- Agrupar campos en secciones visuales con border y título
- Secciones colapsables en mobile
- Indicador de progreso (paso X de Y)
- Botones "Guardar y otro" para registros consecutivos

**Estructura de formulario mejorado:**
```
┌──────────────────────────────┐
│ Registrar Mortalidad         │
│ Gestión Avícola › Repro › Cría │  ← SubNavHeader
├──────────────────────────────┤
│                              │
│ ─── Información del Lote ─── │
│  Lote: [select ▼]           │
│  Fecha: [date]              │
│                              │
│ ─── Registro de Mortalidad ─ │
│  Sexo: [Macho ▼]            │
│  Cantidad: [number]         │
│  Causa: [select ▼]          │
│  Observaciones: [text]      │
│                              │
│ ─── Validación ───────────── │
│  ✅ Saldo disponible: 4,250  │
│                              │
│ [Cancelar]     [Guardar]     │
└──────────────────────────────┘
```

#### Día 12: MobileNav contextual (C-17) + ConfirmDialog (C-19)

**Archivos a modificar:**
- `components/layout/MobileNav.tsx` — contextual según ruta

**Archivos a crear:**
- `components/ui/ConfirmDialog.tsx`

**MobileNav contextual:**
```tsx
// Determinar items según ruta actual
const getNavItems = (pathname: string) => {
  if (pathname.startsWith('/operations/new')) {
    return [
      { path: '#back', label: 'Atrás', Icon: ArrowLeft, action: 'back' },
      { path: '#', label: 'Lote actual', Icon: Bird, disabled: true },
      { path: '#save', label: 'Guardar', Icon: Save, action: 'save' },
      { path: '#kpis', label: 'KPIs', Icon: TrendingUp, action: 'kpis' },
      { path: '#menu', label: 'Menú', Icon: Menu, action: 'menu' },
    ]
  }
  // Default items
  return defaultMobileItems
}
```

#### Día 13: Integración y pruebas de Fase 2

- Verificar ReviewCenter con tabs y filtros
- Verificar Dashboard con quick actions por rol
- Verificar formularios con secciones
- Verificar MobileNav contextual
- Verificar ConfirmDialog en flujos críticos

---

### 2.3 Fase 3 — Pantallas administrativas y SAP (Días 14-19)

#### Día 14-15: Refactor SAP Manager (C-08)

**Archivos a modificar:**
- `pages/sap/SapManagerPage.tsx` — refactor a dashboard SAP

**Archivos a crear:**
- `pages/sap/SapOrdersPage.tsx`
- `pages/sap/SapPendingPage.tsx`
- `pages/sap/SapErrorsPage.tsx`
- `pages/sap/SapLogPage.tsx`

**Nueva estructura SAP:**

```tsx
// SapManagerPage.tsx — Dashboard SAP
export default function SapManagerPage() {
  return (
    <div>
      <SubNavHeader title="Integración SAP" />
      
      {/* KPIs de integración */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KpiCard icon={Clock} label="Pendientes" value={pendingCount} color="amber" />
        <KpiCard icon={CheckCircle} label="Enviados" value={sentCount} color="green" />
        <KpiCard icon={AlertTriangle} label="Errores" value={errorCount} color="red" />
        <KpiCard icon={RefreshCw} label="Última sincronización" value={lastSync} color="blue" />
      </div>

      {/* Navegación interna con tabs estilo cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <Link to="/sap/purchase-orders" className="card ...">Órdenes de Compra</Link>
        <Link to="/sap/transfer-orders" className="card ...">Órdenes de Transferencia</Link>
        <Link to="/sap/pending" className="card ...">Documentos Pendientes</Link>
        <Link to="/sap/sent" className="card ...">Envíos a SAP</Link>
        <Link to="/sap/errors" className="card ...">Errores SAP</Link>
        <Link to="/sap/log" className="card ...">Bitácora SAP</Link>
      </div>
    </div>
  )
}
```

**PayloadViewer (incluido en SapPendingPage):**
```tsx
// Componente para ver el payload JSON antes de enviar
// Modal o panel expandible con sintaxis coloreada
// Botones: [Enviar a SAP] [Cancelar]
```

#### Día 16-17: Refactor Auditoría (C-09)

**Archivos a modificar:**
- `pages/audit/AuditPage.tsx` — refactor

**Archivos a crear:**
- `pages/audit/AuditDetail.tsx`
- `pages/audit/AuditCorrections.tsx`
- `components/ui/StatusTimeline.tsx`

**StatusTimeline component:**
```tsx
interface TimelineEvent {
  date: string;
  action: string;        // i18n key
  user: string;
  description: string;
  type: 'create' | 'review' | 'correction' | 'approval' | 'rejection' | 'sap_send' | 'sap_error';
}

interface StatusTimelineProps {
  events: TimelineEvent[];
}

// Render: línea vertical con puntos
// Cada evento: icono + fecha + usuario + descripción
// Colores por tipo de evento
```

#### Día 18: Maestros agrupados (C-15) + FilterPanel (C-18)

**Archivos a crear:**
- `pages/masters/MastersHubPage.tsx`

**Agrupación de maestros:**

```tsx
const MASTER_GROUPS = [
  {
    title: 'Granjas e Instalaciones',
    icon: Building2,
    entities: [
      { entity: 'companies', label: 'Empresas' },
      { entity: 'farms', label: 'Granjas' },
      { entity: 'houses', label: 'Galpones' },
      { entity: 'hatcheries', label: 'Incubadoras' },
    ]
  },
  {
    title: 'Insumos y Sanidad',
    icon: Syringe,
    entities: [
      { entity: 'feed-types', label: 'Alimentos' },
      { entity: 'vaccines', label: 'Vacunas' },
      { entity: 'medications', label: 'Medicamentos' },  // Nota: verificar si existe
    ]
  },
  {
    title: 'Parámetros Genéticos',
    icon: Dna,
    entities: [
      { entity: 'genetic-lines', label: 'Líneas Genéticas' },
      { entity: 'breeds', label: 'Razas' },
    ]
  },
  {
    title: 'Logística',
    icon: Truck,
    entities: [
      { entity: 'transports', label: 'Transportes' },
      { entity: 'processing-plants', label: 'Plantas de Proceso' },
    ]
  },
  {
    title: 'Parámetros de Registro',
    icon: ClipboardList,
    entities: [
      { entity: 'mortality-causes', label: 'Causas de Mortalidad' },
      { entity: 'suppliers', label: 'Proveedores' },
    ]
  },
]
```

#### Día 19: Integración y pruebas de Fase 3

- Verificar SAP Manager con tabs y KPIs
- Verificar PayloadViewer
- Verificar Auditoría con timeline
- Verificar Maestros agrupados
- Verificar FilterPanel en ReviewCenter y otras páginas

---

### 2.4 Fase 4 — Migración de rutas y pulido (Días 20-25)

#### Día 20: Migración de rutas /processes → /poultry (C-04)

**Archivos a modificar:**
- `App.tsx`
- `Sidebar.tsx`
- `MobileDrawer.tsx`
- `MobileNav.tsx`
- i18n

**Estrategia de migración:**

```tsx
// App.tsx — Nuevas rutas
<Route path="/poultry" element={<PoultryHubPage />} />
<Route path="/poultry/:birdType/:phase?" element={<PoultryStagePage />} />

// Redirecciones para mantener compatibilidad
<Route path="/processes" element={<Navigate to="/poultry" replace />} />
<Route path="/processes/:stage" element={<PoultryRedirect />} />

// PoultryRedirect — mapea stage keys antiguas a nuevas rutas
const STAGE_ROUTE_MAP: Record<string, string> = {
  'grandparent_rearing': '/poultry/grandparent/rearing',
  'grandparent_production': '/poultry/grandparent/production',
  'breeder_rearing': '/poultry/breeder/rearing',
  'breeder_production': '/poultry/breeder/production',
  'hatchery': '/poultry/hatchery',
  'broiler': '/poultry/broiler',
};
```

#### Día 21: EmptyState + LoadingSkeleton (C-11, C-12)

**Archivos a crear:**
- `components/ui/EmptyState.tsx`
- `components/ui/LoadingSkeleton.tsx`

```tsx
// EmptyState.tsx
interface EmptyStateProps {
  icon: LucideIcon;
  title: string;        // i18n key
  description?: string; // i18n key
  action?: {
    label: string;
    onClick: () => void;
  };
}

// LoadingSkeleton.tsx
interface SkeletonProps {
  variant: 'table' | 'card' | 'form' | 'text';
  rows?: number;
  cards?: number;
}
```

#### Día 22: Pruebas visuales (cross-browser)

Ver sección [19. Pruebas Visuales](#19-pruebas-visuales)

#### Día 23: Pruebas de navegación

Ver sección [20. Pruebas de Navegación](#20-pruebas-de-navegación)

#### Día 24: Pruebas mobile

Ver sección [21. Pruebas Mobile](#21-pruebas-mobile)

#### Día 25: Pruebas cross-browser + ajustes finales

Ver sección [22. Pruebas Cross-Browser](#22-pruebas-cross-browser)

---

## 3. Arquitectura de Componentes

### 3.1 Árbol de componentes del layout

```
<AppLayout>
  ├── <Sidebar>                          ← Desktop (lg+)
  │   ├── <Logo />
  │   ├── <SidebarSection label="OPERATIVO">
  │   │   ├── <SidebarItem icon={Home} to="/" />
  │   │   └── <SidebarSubmenu icon={Bird} label="Gestión Avícola">
  │   │       ├── <SidebarSubmenu label="Abuelas">
  │   │       │   ├── <SidebarItem to="/poultry/grandparent/rearing" />
  │   │       │   └── <SidebarItem to="/poultry/grandparent/production" />
  │   │       ├── <SidebarSubmenu label="Reproductoras">
  │   │       │   ├── <SidebarItem to="/poultry/breeder/rearing" />
  │   │       │   └── <SidebarItem to="/poultry/breeder/production" />
  │   │       ├── <SidebarItem to="/poultry/hatchery" />
  │   │       └── <SidebarItem to="/poultry/broiler" />
  │   │   </SidebarSubmenu>
  │   ├── <SidebarSection label="REVISIÓN">
  │   │   └── <SidebarSubmenu icon={Search} label="Centro de Revisión">
  │   │       ├── <SidebarItem to="/review/pending" badge={count} />
  │   │       ├── <SidebarItem to="/review/in-review" />
  │   │       ├── <SidebarItem to="/review/returned" />
  │   │       ├── <SidebarItem to="/review/approved" />
  │   │       └── <SidebarItem to="/review/consolidated" />
  │   │   </SidebarSubmenu>
  │   ├── ... (más secciones)
  │   └── <UserSection />
  │
  ├── <Header>                           ← Mobile (<lg)
  │   ├── <HamburgerButton />
  │   ├── <Breadcrumbs />
  │   └── <HeaderActions />              ← Lang toggle, logout
  │
  ├── <main>
  │   <Breadcrumbs />                    ← Desktop breadcrumbs
  │   <Outlet />                         ← Page content
  │
  ├── <MobileDrawer>                     ← Mobile overlay
  │   ├── (misma jerarquía que Sidebar)
  │   └── <DrawerFooter />
  │
  └── <MobileNav>                        ← Mobile bottom bar (contextual)
```

### 3.2 Data flow

```
useAuthStore (user, role, permissions)
    │
    ▼
Sidebar ← useSidebar hook (expanded sections, active item)
    │
    ▼
App.tsx (routes)
    │
    ▼
Pages ← useSubNavigation hook (sub-page history stack)
    │
    ▼
Components ← ui.store (loading, toasts, modals)
```

---

## 4. Layout Principal

### 4.1 AppLayout.tsx — Refactor

```tsx
export default function AppLayout() {
  const { user } = useAuthStore()
  const location = useLocation()
  const isMobileUser = user?.view_type === 'mobile'

  // Generar breadcrumbs según la ruta actual
  const breadcrumbs = useMemo(() => generateBreadcrumbs(location.pathname), [location.pathname])

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Desktop sidebar */}
      {!isMobileUser && <Sidebar />}
      
      {/* Mobile header (always visible) */}
      <Header breadcrumbs={breadcrumbs} />
      
      {/* Breadcrumbs en desktop (debajo del header si existe) */}
      {!isMobileUser && breadcrumbs.length > 0 && (
        <div className="hidden lg:block bg-white border-b border-slate-200">
          <div className="max-w-7xl mx-auto px-8">
            <Breadcrumbs items={breadcrumbs} />
          </div>
        </div>
      )}

      {/* Main content */}
      <main className={`
        pb-16 lg:pb-0
        ${!isMobileUser ? 'lg:ml-64' : ''}
        transition-all duration-200
      `}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 lg:py-6">
          <Outlet />
        </div>
      </main>

      {/* Mobile bottom nav */}
      {isMobileUser && <MobileNav />}
      <MobileDrawer />
    </div>
  )
}
```

### 4.2 generateBreadcrumbs helper

```tsx
// utils/breadcrumbs.ts
interface Crumb {
  label: string;
  fallback: string;
  to?: string;
}

const BREADCRUMB_MAP: Record<string, Crumb[]> = {
  '/': [{ label: 'nav.dashboard', fallback: 'Dashboard' }],
  '/poultry': [
    { label: 'nav.dashboard', fallback: 'Dashboard', to: '/' },
    { label: 'nav.poultry', fallback: 'Gestión Avícola' },
  ],
  '/poultry/breeder/rearing': [
    { label: 'nav.dashboard', fallback: 'Dashboard', to: '/' },
    { label: 'nav.poultry', fallback: 'Gestión Avícola', to: '/poultry' },
    { label: 'nav.breeder', fallback: 'Reproductoras', to: '/poultry/breeder' },
    { label: 'nav.breederRearing', fallback: 'Cría' },
  ],
  // ... más rutas
}

export function generateBreadcrumbs(pathname: string): Crumb[] {
  // Buscar coincidencia exacta primero
  if (BREADCRUMB_MAP[pathname]) return BREADCRUMB_MAP[pathname]
  
  // Coincidencia parcial (para rutas con parámetros como /lots/123)
  const base = '/' + pathname.split('/').slice(1, -1).join('/')
  if (BREADCRUMB_MAP[base]) return [...BREADCRUMB_MAP[base], { label: 'common.detail', fallback: 'Detalle' }]
  
  // Default
  return [{ label: 'nav.dashboard', fallback: 'Dashboard', to: '/' }]
}
```

---

## 5. Sidebar

### 5.1 Especificación visual

| Propiedad | Valor |
|-----------|-------|
| **Ancho** | `w-64` (256px) |
| **Fondo** | `bg-[#1E3A5F]` |
| **Posición** | `fixed left-0 top-0 h-screen` |
| **Z-index** | `z-30` |
| **Overflow** | `overflow-y-auto overflow-x-hidden` |
| **Transición** | `transition-all duration-200` |
| **Visible en** | `lg:flex` (solo desktop) |

### 5.2 Animaciones

```css
/* Sidebar submenu expand/collapse */
.sidebar-submenu-enter {
  max-height: 0;
  opacity: 0;
}
.sidebar-submenu-enter-active {
  max-height: 500px;
  opacity: 1;
  transition: max-height 300ms ease-in-out, opacity 200ms ease;
}
.sidebar-submenu-exit {
  max-height: 500px;
  opacity: 1;
}
.sidebar-submenu-exit-active {
  max-height: 0;
  opacity: 0;
  transition: max-height 200ms ease-in-out, opacity 150ms ease;
}

/* Chevron rotation */
.sidebar-chevron {
  transition: transform 200ms ease;
}
.sidebar-chevron-open {
  transform: rotate(180deg);
}
```

### 5.3 Sidebar state management

```tsx
// hooks/useSidebar.ts
interface SidebarState {
  expandedSections: Record<string, boolean>;  // 'poultry' | 'review' | 'sap' | ...
  setSectionExpanded: (key: string, expanded: boolean) => void;
  toggleSection: (key: string) => void;
  activeItem: string;  // ruta activa
  setActiveItem: (path: string) => void;
}

// Persistir expandedSections en localStorage para recordar estado entre sesiones
const STORAGE_KEY = 'global-avicola-sidebar-state'
```

---

## 6. Submenús

### 6.1 Comportamiento

| Estado | Comportamiento |
|--------|---------------|
| **Colapsado** | Solo se ve el header del submenú con icono + label + chevron |
| **Expandido** | Se muestran los items hijos con animación de altura |
| **Con item activo** | El submenú se expande automáticamente al navegar a una ruta hija |
| **Persistencia** | El estado expandido/colapsado se guarda en localStorage |

### 6.2 Estructura de datos

```tsx
// Configuración de la navegación completa
const NAV_CONFIG = {
  dashboard: {
    icon: Home,
    label: 'nav.dashboard',
    to: '/',
    section: 'main',
  },
  poultry: {
    icon: Bird,
    label: 'nav.poultry',
    section: 'operational',
    children: {
      grandparent: {
        label: 'nav.grandparent',
        children: {
          import: { label: 'nav.import', to: '/poultry/grandparent/import' },
          reception: { label: 'nav.reception', to: '/poultry/grandparent/reception' },
        }
      },
      breeder: {
        label: 'nav.breeder',
        children: {
          rearing: { label: 'nav.breederRearing', to: '/poultry/breeder/rearing' },
          production: { label: 'nav.breederProduction', to: '/poultry/breeder/production' },
        }
      },
      hatchery: { label: 'nav.hatchery', to: '/poultry/hatchery' },
      broiler: { label: 'nav.broiler', to: '/poultry/broiler' },
    }
  },
  // ... más secciones
}
```

---

## 7. Breadcrumbs

### 7.1 Componente

```tsx
// components/ui/Breadcrumbs.tsx
export function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs font-medium py-2">
      {items.map((item, index) => (
        <Fragment key={index}>
          {index > 0 && (
            <ChevronRight size={14} className="text-slate-300 shrink-0" />
          )}
          {item.to && index < items.length - 1 ? (
            <Link
              to={item.to}
              className="text-slate-500 hover:text-blue-600 transition-colors truncate max-w-[200px]"
            >
              {t(item.label, item.fallback)}
            </Link>
          ) : (
            <span className="text-slate-900 font-semibold truncate max-w-[200px]">
              {t(item.label, item.fallback)}
            </span>
          )}
        </Fragment>
      ))}
    </nav>
  )
}
```

### 7.2 Mobile breadcrumbs

En mobile, los breadcrumbs se muestran en el Header, con scroll horizontal si son muchos:

```tsx
// Header.tsx
<div className="overflow-x-auto whitespace-nowrap scrollbar-hide">
  <Breadcrumbs items={breadcrumbs} />
</div>
```

---

## 8. Cards y Tarjetas KPI

### 8.1 KpiCard

```tsx
export function KpiCard({ icon: Icon, label, value, trend, color = 'blue', onClick }: KpiCardProps) {
  const colors = {
    blue: { bg: 'bg-blue-50', icon: 'text-blue-600', text: 'text-blue-700' },
    green: { bg: 'bg-emerald-50', icon: 'text-emerald-600', text: 'text-emerald-700' },
    amber: { bg: 'bg-amber-50', icon: 'text-amber-600', text: 'text-amber-700' },
    red: { bg: 'bg-red-50', icon: 'text-red-600', text: 'text-red-700' },
    slate: { bg: 'bg-slate-50', icon: 'text-slate-600', text: 'text-slate-700' },
  }
  const c = colors[color]

  return (
    <div
      onClick={onClick}
      className={`
        relative bg-white rounded-xl border border-slate-200 p-4
        ${onClick ? 'cursor-pointer hover:shadow-md hover:border-blue-200' : ''}
        transition-all duration-200
      `}
    >
      <div className={`absolute top-3 right-3 w-10 h-10 rounded-lg ${c.bg} flex items-center justify-center`}>
        <Icon size={20} className={c.icon} />
      </div>
      <p className="text-xs font-medium text-slate-500 mb-1">{t(label)}</p>
      <p className="text-2xl font-extrabold text-slate-900">{value}</p>
      {trend && (
        <div className="flex items-center gap-1 mt-1">
          {trend.direction === 'up' && <TrendingUp size={14} className="text-emerald-500" />}
          {trend.direction === 'down' && <TrendingDown size={14} className="text-red-500" />}
          {trend.direction === 'stable' && <Minus size={14} className="text-slate-400" />}
          <span className={`text-xs font-semibold ${
            trend.direction === 'up' ? 'text-emerald-600' :
            trend.direction === 'down' ? 'text-red-600' :
            'text-slate-500'
          }`}>
            {trend.value}
          </span>
        </div>
      )}
    </div>
  )
}
```

---

## 9. Tablas

### 9.1 Estándar de tabla

Mantener DataTable existente con las siguientes mejoras:

```tsx
// DataTable.tsx — mejoras
interface DataTableProps {
  columns: Column[];
  data: any[];
  loading?: boolean;
  emptyState?: {
    icon: LucideIcon;
    title: string;
    description?: string;
  };
  onRowClick?: (row: any) => void;
  sortable?: boolean;
  pagination?: {
    page: number;
    total: number;
    limit: number;
    onChange: (page: number) => void;
  };
  stickyHeader?: boolean;
  maxHeight?: string;
}
```

### 9.2 Vista mobile de tabla

En mobile (< 768px), las tablas se convierten en cards:

```tsx
// hook o util para detectar si mostrar tabla o cards
// <div className="hidden md:block">
//   <DataTable ... />  ← desktop
// </div>
// <div className="md:hidden space-y-3">
//   {data.map(item => <MobileRowCard item={item} />)}  ← mobile
// </div>
```

---

## 10. Formularios

### 10.1 Estructura de formulario con secciones

```tsx
// FormSection.tsx
interface FormSectionProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  defaultOpen?: boolean;
  collapsible?: boolean;
  children: React.ReactNode;
}

// Render:
// <section className="border border-slate-200 rounded-xl bg-white mb-4">
//   <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
//     {icon && <Icon size={16} className="text-slate-500" />}
//     <h3 className="text-sm font-bold text-slate-700">{title}</h3>
//   </div>
//   <div className="p-4 space-y-4">
//     {children}
//   </div>
// </section>
```

### 10.2 StepWizard para formularios largos

```tsx
interface Step {
  title: string;
  description?: string;
  fields: string[];  // nombres de campos en este paso
}

interface StepWizardProps {
  steps: Step[];
  currentStep: number;
  onStepChange: (step: number) => void;
  children: React.ReactNode;  // formulario del paso actual
}
```

---

## 11. Status Badges

### 11.1 Badge component mejorado

Extender el Badge existente con variantes para cada estado:

```tsx
type BadgeVariant =
  | 'registered'
  | 'pending_review'
  | 'in_review'
  | 'returned'
  | 'corrected'
  | 'approved'
  | 'rejected'
  | 'cancelled'
  | 'sap_sent'
  | 'sap_error'
  | 'sap_confirmed'
  | 'consolidated'
  | 'draft'

const BADGE_STYLES: Record<BadgeVariant, { bg: string; text: string; icon: LucideIcon }> = {
  registered:      { bg: 'bg-sky-100', text: 'text-sky-700', icon: FileText },
  pending_review:  { bg: 'bg-amber-100', text: 'text-amber-700', icon: Clock },
  in_review:       { bg: 'bg-indigo-100', text: 'text-indigo-700', icon: Search },
  returned:        { bg: 'bg-orange-100', text: 'text-orange-700', icon: Undo2 },
  corrected:       { bg: 'bg-teal-100', text: 'text-teal-700', icon: RefreshCw },
  approved:        { bg: 'bg-emerald-100', text: 'text-emerald-700', icon: CheckCircle },
  rejected:        { bg: 'bg-red-100', text: 'text-red-700', icon: XCircle },
  cancelled:       { bg: 'bg-slate-100', text: 'text-slate-500', icon: Ban },
  sap_sent:        { bg: 'bg-blue-100', text: 'text-blue-700', icon: Send },
  sap_error:       { bg: 'bg-red-100', text: 'text-red-700', icon: AlertTriangle },
  sap_confirmed:   { bg: 'bg-emerald-100', text: 'text-emerald-700', icon: Check },
  consolidated:    { bg: 'bg-violet-100', text: 'text-violet-700', icon: Package },
  draft:           { bg: 'bg-slate-100', text: 'text-slate-600', icon: File },
}
```

---

## 12. Review Panels

### 12.1 Estructura del nuevo ReviewCenter

```
┌──────────────────────────────────────────────────────────┐
│ Centro de Revisión                              [Crear Lote] │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [Pendientes] [En Revisión] [Devueltos] [Aprobados] [Consolidados] │
│      12           3             2           45         8       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ▼ Filtros                                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │ 📅 Fecha         🐔 Lote      👤 Operador        │   │
│  │ [desde] [hasta]  [select ▼]  [select ▼]          │   │
│  │                                                    │   │
│  │ 📋 Tipo          🏭 Granía     📊 Estado          │   │
│  │ [select ▼]       [select ▼]   [select ▼]          │   │
│  │                                           [Limpiar]│   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ ☐ │ Lote        │ Tipo     │ Fecha   │ Estado  │ ⚡ │
│  ├──────────────────────────────────────────────────┤   │
│  │ ☐ │ L-2026-042  │ Mort.    │ 24/06   │ 🔍 Rev. │ → │
│  │ ☐ │ L-2026-042  │ Pesaje   │ 24/06   │ 🔍 Rev. │ → │
│  │ ☐ │ L-2026-041  │ Alimento │ 23/06   │ 📋 Pend.│ → │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  [✓ Iniciar Revisión] [↩ Devolver] [✓✓ Completar]       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 12.2 Vista lado a lado (comparación)

Para la revisión de detalle:

```
┌─── Panel Izquierdo (60%) ───┬─── Panel Derecho (40%) ───┐
│                              │                            │
│ 📋 Evento: Mortalidad       │ 📊 Comparación             │
│ Lote: L-2026-042             │                            │
│ Fecha: 24/06/2026            │ Parámetro   │ Reg. │ Ant. │
│ Operador: Juan Pérez         │─────────────┼──────┼──────│
│                              │ Cantidad    │ 150  │ 145  │
│ ─── Datos Registrados ────  │ Causa       │      │      │
│                             │             │      │      │
│ Sexo: Macho                 │ ────────────────────────  │
│ Cantidad: 150               │                            │
│ Causa: Enfermedad           │ [✓ Aprobar] [✗ Rechazar]  │
│ Observaciones:              │ [↩ Devolver con motivo]    │
│                             │                            │
│ ─── Historial ────────────  │                            │
│ 📝 Registrado: Juan, 24/06  │                            │
│ 📋 En revisión: María, 24/06│                            │
└─────────────────────────────┴────────────────────────────┘
```

---

## 13. Approval Screens

### 13.1 ApprovalPanel refactorizado

```tsx
// ApprovalPanel.tsx
export default function ApprovalPanel() {
  return (
    <div>
      <SubNavHeader title={t('nav.approvals')} />
      
      {/* Resumen ejecutivo */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KpiCard icon={Clock} label="Pendientes" value={12} color="amber" />
        <KpiCard icon={CheckCircle} label="Aprobados hoy" value={8} color="green" />
        <KpiCard icon={XCircle} label="Rechazados hoy" value={1} color="red" />
        <KpiCard icon={BarChart3} label="Tiempo promedio" value="2.3h" color="blue" />
      </div>

      {/* Filtros */}
      <FilterPanel>
        <FilterGroup label="Lote">
          <input type="text" placeholder="Código de lote..." />
        </FilterGroup>
        <FilterGroup label="Fecha">
          <input type="date" />
          <input type="date" />
        </FilterGroup>
        <FilterGroup label="Tipo">
          <select>
            <option>Todos</option>
            <option>Mortalidad</option>
            <option>Pesaje</option>
            {/* ... */}
          </select>
        </FilterGroup>
      </FilterPanel>

      {/* Lista agrupada por lote */}
      <div className="space-y-4">
        {groupedByLot.map(lot => (
          <ApprovalLotGroup key={lot.id} lot={lot} />
        ))}
      </div>
    </div>
  )
}
```

### 13.2 ApprovalLotGroup

```tsx
// Agrupar operaciones por lote para aprobación consolidada
function ApprovalLotGroup({ lot }: { lot: LotWithEvents }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      {/* Header del lote */}
      <div className="px-4 py-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <div>
          <span className="font-bold text-slate-800">{lot.code}</span>
          <span className="text-sm text-slate-500 ml-2">
            {lot.farm} · {lot.phase} · {lot.events.length} operaciones
          </span>
        </div>
        <div className="flex gap-2">
          <Button variant="success" size="sm">Aprobar lote</Button>
          <Button variant="danger" size="sm">Rechazar lote</Button>
        </div>
      </div>
      {/* Eventos del lote */}
      <div className="divide-y divide-slate-100">
        {lot.events.map(event => (
          <ApprovalEventRow key={event.id} event={event} />
        ))}
      </div>
    </div>
  )
}
```

---

## 14. Audit Timeline

### 14.1 StatusTimeline component

```tsx
export function StatusTimeline({ events }: { events: TimelineEvent[] }) {
  return (
    <div className="relative">
      {/* Línea vertical */}
      <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-slate-200" />
      
      {/* Eventos */}
      <div className="space-y-6">
        {events.map((event, index) => {
          const typeStyle = TIMELINE_STYLES[event.type]
          return (
            <div key={index} className="relative flex gap-4">
              {/* Círculo en la línea */}
              <div className={`
                relative z-10 w-10 h-10 rounded-full flex items-center justify-center shrink-0
                ${typeStyle.bg} ring-4 ring-white
              `}>
                <typeStyle.icon size={16} className={typeStyle.color} />
              </div>
              {/* Contenido */}
              <div className="flex-1 pt-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-800">
                    {t(event.action)}
                  </span>
                  <span className="text-xs text-slate-400">{event.date}</span>
                </div>
                <p className="text-sm text-slate-600 mt-0.5">{event.description}</p>
                <p className="text-xs text-slate-400 mt-0.5">por {event.user}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

### 14.2 Timeline visual example

```
  🔵
  │  📝 24/06/2026 — Registro de mortalidad
  │  Registradas 150 aves
  │  por Juan Pérez
  │
  🔍
  │  📋 24/06/2026 — Inicio de revisión
  │  Revisión asignada a María García
  │  por María García
  │
  ✏️
  │  🔄 24/06/2026 — Corrección
  │  Cantidad: 150 → 145
  │  Motivo: Error de conteo
  │  por María García
  │
  ✅
  │  ✔️ 24/06/2026 — Aprobación
  │  Aprobado por Carlos López
  │  por Carlos López
  │
  📦
  │  📦 24/06/2026 — Consolidación
  │  Consolidado en lote de envío SAP-2026-06-24
  │  por Carlos López
  │
  📤
  │  🔄 24/06/2026 — Envío a SAP
  │  Payload enviado. ID SAP: 123456
  │  Estado: Confirmado
  │  por Sistema
```

---

## 15. SAP Integration Panels

### 15.1 Dashboard SAP

```
┌──────────────────────────────────────────────────────────┐
│ Integración SAP                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                    │
│ │⏳ 12 │ │📤 45 │ │❌ 3  │ │🔄 Hoy │                    │
│ │Pend. │ │Env.  │ │Error │ │Sync  │                    │
│ └──────┘ └──────┘ └──────┘ └──────┘                    │
│                                                          │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│ │ 📄 Órdenes   │ │ 🔄 Órdenes   │ │ ⏳ Documentos │      │
│ │ de Compra    │ │ Transferencia│ │ Pendientes    │      │
│ └──────────────┘ └──────────────┘ └──────────────┘      │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│ │ 📤 Envíos    │ │ ❌ Errores   │ │ 📋 Bitácora  │      │
│ │ a SAP        │ │ SAP         │ │ SAP          │      │
│ └──────────────┘ └──────────────┘ └──────────────┘      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 15.2 PayloadViewer

```tsx
// Componente para ver payloads JSON
function PayloadViewer({ payload, onSend, onCancel }: PayloadViewerProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-slate-900 rounded-xl overflow-hidden">
      <div className="px-4 py-2 bg-slate-800 flex items-center justify-between">
        <span className="text-xs text-slate-400 font-mono">Payload SAP</span>
        <button onClick={() => setExpanded(!expanded)} className="text-xs text-blue-400">
          {expanded ? 'Contraer' : 'Expandir'}
        </button>
      </div>
      {expanded && (
        <pre className="p-4 text-xs text-green-400 font-mono overflow-x-auto">
          {JSON.stringify(payload, null, 2)}
        </pre>
      )}
      <div className="px-4 py-2 bg-slate-800 flex gap-2 justify-end">
        <Button variant="ghost" size="sm" onClick={onCancel}>Cancelar</Button>
        <Button variant="primary" size="sm" onClick={onSend}>
          <Send size={14} className="mr-1" /> Enviar a SAP
        </Button>
      </div>
    </div>
  )
}
```

---

## 16. Mobile Navigation

### 16.1 Bottom Nav contextual

```tsx
// hooks/useMobileNav.ts
export function useMobileNav() {
  const location = useLocation()
  const pathname = location.pathname

  const items = useMemo(() => {
    // Contexto: formulario de operación
    if (pathname.startsWith('/operations/new')) {
      return [
        { id: 'back', icon: ArrowLeft, label: 'Atrás', action: 'back' },
        { id: 'lot', icon: Bird, label: 'Lote' },
        { id: 'save', icon: Save, label: 'Guardar', action: 'save', primary: true },
        { id: 'history', icon: Clock, label: 'Historial' },
        { id: 'menu', icon: Menu, label: 'Menú', action: 'drawer' },
      ]
    }
    // Contexto: detalle de lote
    if (pathname.startsWith('/lots/')) {
      return [
        { id: 'home', icon: Home, label: 'Inicio', to: '/' },
        { id: 'register', icon: PlusCircle, label: 'Registrar', to: `/operations/new?lot_id=${lotId}` },
        { id: 'lots', icon: Bird, label: 'Lotes', to: '/lots' },
        { id: 'kpis', icon: TrendingUp, label: 'KPIs', to: `/reports/lot/${lotId}` },
        { id: 'menu', icon: Menu, label: 'Menú', action: 'drawer' },
      ]
    }
    // Default
    return [
      { id: 'home', icon: Home, label: 'Inicio', to: '/' },
      { id: 'register', icon: PlusCircle, label: 'Registrar', action: 'quick-register' },
      { id: 'lots', icon: Bird, label: 'Lotes', to: '/lots' },
      { id: 'kpis', icon: TrendingUp, label: 'KPIs', to: '/reports' },
      { id: 'menu', icon: Menu, label: 'Menú', action: 'drawer' },
    ]
  }, [pathname])

  return items
}
```

### 16.2 MobileDrawer con jerarquía

Replicar la misma estructura del Sidebar desktop pero en un drawer que ocupa el 80% del ancho:

```tsx
// MobileDrawer.tsx — estructura
<nav className="w-[80vw] max-w-sm bg-[#1E3A5F] text-white h-full overflow-y-auto">
  {/* Header con usuario */}
  <div className="px-5 py-4 border-b border-white/10">
    <div className="flex items-center justify-between">
      <div>
        <p className="font-bold text-sm">Global Avícola</p>
        <p className="text-xs text-blue-300">{user?.first_name}</p>
      </div>
      <button onClick={onClose}><X size={18} /></button>
    </div>
  </div>

  {/* Navegación — misma data que Sidebar */}
  <div className="px-3 py-4 space-y-1">
    <SidebarItem icon={Home} label="Dashboard" to="/" />
    
    <SidebarSubmenu icon={Bird} label="Gestión Avícola">
      <SidebarItem to="/poultry/grandparent/rearing" label="Abuelas" depth={1} />
      <SidebarItem to="/poultry/breeder/rearing" label="Reproductoras — Cría" depth={1} />
      <SidebarItem to="/poultry/breeder/production" label="Reproductoras — Producción" depth={1} />
      <SidebarItem to="/poultry/hatchery" label="Incubadora" depth={1} />
      <SidebarItem to="/poultry/broiler" label="Pollo de Engorde" depth={1} />
    </SidebarSubmenu>
    
    {/* ... más secciones */}
  </div>

  {/* Footer */}
  <div className="px-5 py-4 border-t border-white/10">
    <button onClick={toggleLang} className="text-xs text-blue-300">
      {i18n.language === 'es' ? 'English' : 'Español'}
    </button>
  </div>
</nav>
```

---

## 17. Responsive Rules

### 17.1 Breakpoints

| Tailwind | Min-width | Target |
|----------|-----------|--------|
| `sm` | 640px | Mobile landscape |
| `md` | 768px | Tablet |
| `lg` | 1024px | Desktop compacto |
| `xl` | 1280px | Desktop estándar |
| `2xl` | 1536px | Desktop grande |

### 17.2 Reglas por breakpoint

| Elemento | < lg (mobile) | ≥ lg (desktop) |
|----------|---------------|-----------------|
| **Sidebar** | Oculto (usar drawer) | `w-64` fijo, visible |
| **Header** | Iconos + breadcrumbs reducidos | Breadcrumbs completos |
| **Breadcrumbs** | 2 niveles máximo, scroll si overflow | Todos los niveles |
| **Content padding** | `px-4 py-4` | `px-8 py-6` |
| **KPI grid** | 2 columnas | 4 columnas |
| **Operation grid** | 2 columnas | 3 columnas |
| **Formularios** | Una columna, secciones colapsables | Una columna con secciones |
| **Tablas** | Cards (vista mobile) | Tabla completa |
| **Review panel** | Panel único | Dos paneles (split view) |
| **Bottom nav** | Visible, fijo abajo | Oculto |
| **Filter panel** | Sección colapsable | Panel expandido |
| **Font size h1** | `text-xl` | `text-3xl` |
| **Font size body** | `text-sm` | `text-base` |

### 17.3 Mobile-first media queries

```css
/* Base: mobile (< 640px) */
.component { ... }

/* sm: 640px+ */
@media (min-width: 640px) { ... }

/* md: 768px+ */
@media (min-width: 768px) { ... }

/* lg: 1024px+ */
@media (min-width: 1024px) { ... }

/* xl: 1280px+ */
@media (min-width: 1280px) { ... }
```

---

## 18. i18n Impacts

### 18.1 Nuevas claves de traducción necesarias

Estimación: **~120 nuevas claves** entre ES y EN.

#### Navegación (nav.*)

```json
{
  "nav": {
    "sections": {
      "operational": "OPERATIVO",
      "review": "REVISIÓN",
      "integration": "INTEGRACIÓN",
      "reports": "REPORTES",
      "administration": "ADMINISTRACIÓN"
    },
    "poultry": "Gestión Avícola",
    "grandparent": "Abuelas",
    "grandparentRearing": "Importación",
    "grandparentProduction": "Recepción",
    "breeder": "Reproductoras",
    "breederRearing": "Cría",
    "breederProduction": "Producción",
    "hatchery": "Incubadora",
    "hatcheryEggs": "Recepción de Huevos",
    "hatcheryIncubation": "Incubación",
    "hatcheryBirth": "Nacimiento",
    "hatcheryDispatch": "Despacho",
    "broiler": "Pollo de Engorde",
    "broilerReception": "Recepción",
    "broilerGrowing": "Engorde",
    "broilerExit": "Salida",
    "broilerClosure": "Cierre de Lote",
    "reviewCenter": "Centro de Revisión",
    "pending": "Pendientes",
    "inReview": "En Revisión",
    "returned": "Devueltos",
    "approved": "Aprobados",
    "consolidated": "Consolidados",
    "sapIntegration": "Integración SAP",
    "purchaseOrders": "Órdenes de Compra",
    "transferOrders": "Órdenes de Transferencia",
    "sapPending": "Documentos Pendientes",
    "sapSent": "Envíos a SAP",
    "sapErrors": "Errores SAP",
    "sapLog": "Bitácora SAP",
    "audit": "Auditoría",
    "auditByLot": "Por Lote",
    "auditByUser": "Por Usuario",
    "auditBySap": "Por Documento SAP",
    "auditCorrections": "Cambios y Correcciones",
    "masters": "Maestros",
    "settings": "Configuración",
    "approvalFlows": "Flujos de Aprobación",
    "parameters": "Parámetros",
    "preferences": "Preferencias"
  }
}
```

#### Breadcrumbs

```json
{
  "breadcrumb": {
    "dashboard": "Dashboard",
    "poultry": "Gestión Avícola",
    "grandparent": "Abuelas",
    "breeder": "Reproductoras",
    "hatchery": "Incubadora",
    "broiler": "Pollo de Engorde",
    "rearing": "Cría",
    "production": "Producción",
    "reviewCenter": "Centro de Revisión",
    "reviewDetail": "Detalle de Revisión",
    "approvals": "Aprobaciones",
    "sap": "Integración SAP",
    "reports": "Reportes",
    "audit": "Auditoría",
    "masters": "Maestros",
    "settings": "Configuración",
    "users": "Usuarios y Roles",
    "lots": "Lotes",
    "lotDetail": "Detalle de Lote",
    "operations": "Operaciones",
    "operationDetail": "Detalle de Operación"
  }
}
```

#### Componentes UI

```json
{
  "ui": {
    "filterPanel": {
      "title": "Filtros",
      "clear": "Limpiar filtros",
      "apply": "Aplicar"
    },
    "confirmDialog": {
      "confirm": "Confirmar",
      "cancel": "Cancelar",
      "approveConfirm": "¿Está seguro de aprobar este registro?",
      "rejectConfirm": "¿Está seguro de rechazar este registro?",
      "reasonRequired": "El motivo es obligatorio"
    },
    "emptyState": {
      "noData": "No hay datos disponibles",
      "noResults": "No se encontraron resultados",
      "noLots": "No hay lotes activos para este proceso",
      "noOperations": "No hay operaciones registradas",
      "action": "Comenzar"
    },
    "quickActions": {
      "title": "Acciones Rápidas",
      "register": "Registrar",
      "myLots": "Mis Lotes"
    },
    "stepWizard": {
      "step": "Paso",
      "of": "de",
      "next": "Siguiente",
      "back": "Anterior",
      "finish": "Finalizar"
    }
  }
}
```

### 18.2 Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `public/locales/es/translation.json` | Agregar ~120 nuevas claves |
| `public/locales/en/translation.json` | Agregar ~120 nuevas claves con traducción |

---

## 19. Pruebas Visuales

### 19.1 Checklist de pruebas visuales

| ID | Prueba | Cobertura | Método |
|----|--------|-----------|--------|
| V-01 | Sidebar se renderiza correctamente en desktop | Todos los items, secciones, submenús | Inspección visual + screenshot |
| V-02 | Submenús colapsables funcionan | Animación expand/colapse, chevron rotación | Test interactivo |
| V-03 | Active state del sidebar | Item activo destacado, submenú padre expandido | Navegar a cada ruta |
| V-04 | Breadcrumbs en todas las rutas | Cada ruta muestra breadcrumbs correctos | Navegar por todas las rutas |
| V-05 | KPI cards | 4 variantes de color, con/sin tendencia | Renderizar dashboard |
| V-06 | Status badges | 13 variantes de estado | Revisar en lista de operaciones |
| V-07 | Empty states | Aparecen cuando no hay datos | Forzar estado vacío |
| V-08 | Loading skeletons | Aparecen durante carga de datos | Medir tiempos de carga |
| V-09 | ConfirmDialog | Modal con botones primary/danger | Ejecutar acción crítica |
| V-10 | FilterPanel | Colapsable, filtros agrupados, limpiar | Interactuar con filtros |
| V-11 | StatusTimeline | Línea vertical con eventos, colores | Ver auditoría de un registro |
| V-12 | Paleta de colores | Blanco base, azul corporativo, colores de estado | Inspección CSS |
| V-13 | Tipografía | Inter en todos los textos, tamaños correctos | Inspección CSS |
| V-14 | Iconografía | lucide-react en todos los iconos, sin emojis | Inspección visual |
| V-15 | Espaciado consistente | Padding, margin, gap uniformes | Inspección visual |

### 19.2 Herramientas

- **Vitest** para pruebas unitarias de componentes
- **Playwright** para pruebas visuales cross-browser
- **Storybook** (opcional) para catálogo de componentes
- **Chromatic** (opcional) para regresión visual

---

## 20. Pruebas de Navegación

### 20.1 Flujos críticos

| ID | Flujo | Pasos | Resultado esperado |
|----|-------|-------|-------------------|
| N-01 | Operador registra mortalidad | Dashboard → Quick action "Registrar" → Seleccionar lote → Seleccionar mortalidad → Formulario → Guardar | Operación creada con estado "Registrado" |
| N-02 | Supervisor revisa operación | Sidebar → Centro de Revisión → Pendientes → Click en operación → Ver detalle → Iniciar revisión | Operación pasa a "En Revisión" |
| N-03 | Aprobador aprueba lote | Sidebar → Aprobaciones → Ver lote → Aprobar → Confirmar | Operaciones pasan a "Aprobado" |
| N-04 | Usuario SAP envía a SAP | Sidebar → Integración SAP → Documentos Pendientes → Ver payload → Enviar | Documento enviado con ID SAP |
| N-05 | Navegación jerárquica completa | Sidebar → Gestión Avícola → Reproductoras → Cría → Seleccionar lote → Registrar pesaje | Llega a formulario en ≤3 clicks |

### 20.2 Redirects y migración

| ID | Ruta antigua | Debe redirigir a | Resultado |
|----|-------------|------------------|-----------|
| R-01 | `/processes` | `/poultry` | Redirect 301 sin pérdida de estado |
| R-02 | `/processes/breeder_rearing` | `/poultry/breeder/rearing` | Redirect con stage mapping |
| R-03 | `/processes/breeder_production` | `/poultry/breeder/production` | Redirect con stage mapping |
| R-04 | `/processes/hatchery` | `/poultry/hatchery` | Redirect con stage mapping |
| R-05 | `/processes/broiler` | `/poultry/broiler` | Redirect con stage mapping |

### 20.3 Pruebas de accesibilidad

| ID | Prueba | Criterio |
|----|--------|----------|
| A-01 | Navegación por teclado | Tab, Enter, Escape, flechas |
| A-02 | ARIA labels | Sidebar, submenús, breadcrumbs |
| A-03 | Focus visible | `focus:ring-2 focus:ring-blue-500` |
| A-04 | Contraste de color | Ratio ≥ 4.5:1 texto normal |
| A-05 | Screen reader | Estructura semántica `<nav>`, `<main>`, `<header>` |

---

## 21. Pruebas Mobile

### 21.1 Dispositivos simulados

| Dispositivo | Viewport | User agent |
|-------------|----------|------------|
| iPhone SE | 375×667 | iOS Safari |
| iPhone 14 Pro | 390×844 | iOS Safari |
| Samsung Galaxy S23 | 360×780 | Android Chrome |
| Google Pixel 7 | 412×915 | Android Chrome |
| iPad Air | 820×1180 | Safari (tablet) |
| Samsung Galaxy Tab | 800×1280 | Android Chrome |

### 21.2 Checklist mobile

| ID | Prueba | Método |
|----|--------|--------|
| M-01 | Bottom nav visible y funcional | Playwright mobile viewport |
| M-02 | Drawer se abre/cierra correctamente | Click hamburger + click overlay |
| M-03 | Submenús en drawer funcionan | Expandir/colapsar en drawer |
| M-04 | Touch targets ≥ 44×44px | Inspección CSS |
| M-05 | Formularios se ven correctamente | Llenar formulario completo |
| M-06 | Teclado no oculta campos | Input cerca del bottom |
| M-07 | Scrolling en tablas horizontales | DataTable con overflow-x |
| M-08 | Quick actions visibles en dashboard | Verificar en viewport 360px |
| M-09 | Breadcrumbs scroll horizontal | Breadcrumbs largos |
| M-10 | Safe area en notch devices | `safe-area-bottom` class |

### 21.3 Comandos Playwright

```typescript
// tests/mobile-nav.spec.ts
test('mobile navigation works correctly', async ({ page }) => {
  // iPhone viewport
  await page.setViewportSize({ width: 375, height: 667 })
  
  // Verificar bottom nav
  await expect(page.locator('nav.fixed.bottom-0')).toBeVisible()
  
  // Abrir drawer
  await page.click('[aria-label="Menú"]')
  await expect(page.locator('[role="navigation"]')).toBeVisible()
  
  // Navegar a Gestión Avícola
  await page.click('text=Gestión Avícola')
  await expect(page.locator('text=Reproductoras')).toBeVisible()
  
  // Ir a Cría
  await page.click('text=Cría')
  await expect(page).toHaveURL(/\/poultry\/breeder\/rearing/)
})
```

---

## 22. Pruebas Cross-Browser

### 22.1 Navegadores objetivo

| Navegador | Versión | Platforma |
|-----------|---------|-----------|
| Google Chrome | Últimas 2 | Windows, macOS, Linux, Android |
| Mozilla Firefox | Últimas 2 | Windows, macOS, Linux |
| Apple Safari | Últimas 2 | macOS, iOS |
| Microsoft Edge | Últimas 2 | Windows, macOS |
| Opera | Últimas 2 | Windows, macOS |
| Samsung Internet | Últimas 2 | Android |
| Android WebView | Últimas 2 | Android |

### 22.2 Checklist cross-browser

| ID | Prueba | Chrome | Firefox | Safari | Edge | Opera | Samsung |
|----|--------|--------|---------|--------|------|-------|---------|
| X-01 | Sidebar renderizado | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| X-02 | Submenús colapsables | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| X-03 | Breadcrumbs | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| X-04 | Animaciones CSS | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| X-05 | Formularios y validación | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| X-06 | Tablas con datos | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| X-07 | Modales y diálogos | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| X-08 | i18n (ES/EN) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| X-09 | Touch events | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| X-10 | Scroll y overflow | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| X-11 | Loading states | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| X-12 | Empty states | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### 22.3 Configuración de Playwright

```typescript
// playwright.config.ts (extender)
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
  { name: 'Mobile Safari', use: { ...devices['iPhone 13'] } },
  { name: 'Mobile Samsung', use: { ...devices['Galaxy S9+'] } },  // Samsung Internet
  { name: 'Tablet', use: { ...devices['iPad Air'] } },
  { name: 'Edge', use: { channel: 'msedge', ...devices['Desktop Edge'] } },
]
```

---

## Apéndice A: Resumen de archivos a crear

| # | Archivo | Descripción |
|---|---------|-------------|
| 1 | `components/layout/SidebarSection.tsx` | Sección con separador visual |
| 2 | `components/layout/SidebarItem.tsx` | Item de menú con icono y active state |
| 3 | `components/layout/SidebarSubmenu.tsx` | Submenú colapsable animado |
| 4 | `components/layout/SubNavHeader.tsx` | Back button + breadcrumbs + título |
| 5 | `components/ui/Breadcrumbs.tsx` | Migas de pan jerárquicas |
| 6 | `components/ui/KpiCard.tsx` | Tarjeta KPI con tendencia |
| 7 | `components/ui/EmptyState.tsx` | Estado vacío con acción |
| 8 | `components/ui/LoadingSkeleton.tsx` | Skeleton contextual |
| 9 | `components/ui/FilterPanel.tsx` | Panel de filtros colapsable |
| 10 | `components/ui/ConfirmDialog.tsx` | Modal de confirmación estándar |
| 11 | `components/ui/StatusTimeline.tsx` | Línea de tiempo de estados |
| 12 | `components/ui/SectionCard.tsx` | Tarjeta de sección con título |
| 13 | `components/ui/StepWizard.tsx` | Wizard de formularios multi-paso |
| 14 | `hooks/useSubNavigation.ts` | Pila de navegación para sub-vistas |
| 15 | `hooks/useSidebar.ts` | Estado del sidebar |
| 16 | `pages/poultry/PoultryHubPage.tsx` | Hub de gestión avícola |
| 17 | `pages/poultry/PoultryStagePage.tsx` | Página de fase productiva |
| 18 | `pages/review/ReviewList.tsx` | Lista filtrada por estado |
| 19 | `pages/sap/SapOrdersPage.tsx` | Órdenes de compra SAP |
| 20 | `pages/sap/SapPendingPage.tsx` | Documentos pendientes SAP |
| 21 | `pages/sap/SapErrorsPage.tsx` | Errores SAP |
| 22 | `pages/sap/SapLogPage.tsx` | Bitácora SAP |
| 23 | `pages/audit/AuditDetail.tsx` | Detalle de auditoría |
| 24 | `pages/audit/AuditCorrections.tsx` | Cambios y correcciones |
| 25 | `pages/masters/MastersHubPage.tsx` | Agrupación de maestros |
| 26 | `pages/settings/SettingsPage.tsx` | Configuración general |
| 27 | `pages/settings/ApprovalFlowsPage.tsx` | Flujos de aprobación |
| 28 | `pages/settings/ParamsPage.tsx` | Parámetros del sistema |
| 29 | `pages/settings/PreferencesPage.tsx` | Preferencias de usuario |

**Total: ~29 archivos nuevos**

## Apéndice B: Resumen de archivos a modificar

| # | Archivo | Cambio |
|---|---------|--------|
| 1 | `components/layout/Sidebar.tsx` | REFACTOR MAYOR: submenús, secciones |
| 2 | `components/layout/AppLayout.tsx` | REFACTOR: breadcrumbs, sidebar state |
| 3 | `components/layout/Header.tsx` | REFACTOR: breadcrumbs, mejor diseño |
| 4 | `components/layout/MobileDrawer.tsx` | REFACTOR MAYOR: jerarquía completa |
| 5 | `components/layout/MobileNav.tsx` | REFACTOR: contextual según ruta |
| 6 | `stores/ui.store.ts` | UPDATE: sidebar state |
| 7 | `pages/review/ReviewCenter.tsx` | REFACTOR MAYOR: tabs + filtros |
| 8 | `pages/sap/SapManagerPage.tsx` | REFACTOR: dashboard + tabs |
| 9 | `pages/audit/AuditPage.tsx` | REFACTOR: dashboard auditoría |
| 10 | `pages/dashboard/DashboardPage.tsx` | REFACTOR: atajos por rol |
| 11 | `pages/operations/OperationFormPage.tsx` | REFACTOR: secciones y wizard |
| 12 | `pages/operations/ProcessHubPage.tsx` | UPDATE: renombrar a PoultryHub |
| 13 | `pages/operations/ProcessStagePage.tsx` | UPDATE: breadcrumbs + ruta |
| 14 | `App.tsx` | REFACTOR MAYOR: nuevas rutas + redirects |
| 15 | `public/locales/es/translation.json` | UPDATE: +120 claves |
| 16 | `public/locales/en/translation.json` | UPDATE: +120 claves |

**Total: ~16 archivos a modificar**

---

> **Fin del documento — GLOBAL AVICOLA UI IMPLEMENTATION PLAN**
>
> *Siguiente paso: Iniciar Fase 1 (Fundación de navegación) comenzando por el refactor del Sidebar con submenús colapsables.*

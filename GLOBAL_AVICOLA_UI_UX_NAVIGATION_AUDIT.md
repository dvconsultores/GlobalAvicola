# GLOBAL AVÍCOLA — Auditoría UI/UX, Navegación y Experiencia de Usuario

> **Fecha:** 2026-06-24  
> **Versión:** 1.0  
> **Tipo:** Auditoría integral de interfaz, navegación y experiencia de usuario  
> **Equipo:** UI/UX Lead Senior, Frontend Architect, Product Designer, Analista Funcional Avícola, Especialista en Sistemas Empresariales  
> **Proyecto auditado:** Global Avícola (frontend React + Vite + TypeScript + TailwindCSS)  
> **Referencia externa:** Atenea (frontend de nómina — solo como referencia de navegación)

---

## Índice

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Auditoría de Atenea — Referencia de Navegación](#2-auditoría-de-atenea--referencia-de-navegación)
3. [Qué NO debe copiarse de Atenea](#3-qué-no-debe-copiarse-de-atenea)
4. [Auditoría de Global Avícola — Estado Actual](#4-auditoría-de-global-avícola--estado-actual)
5. [Problemas Actuales de Navegación](#5-problemas-actuales-de-navegación)
6. [Problemas Actuales de UI](#6-problemas-actuales-de-ui)
7. [Problemas de Experiencia Mobile](#7-problemas-de-experiencia-mobile)
8. [Problemas de Experiencia Web](#8-problemas-de-experiencia-web)
9. [Nueva Arquitectura de Navegación Propuesta](#9-nueva-arquitectura-de-navegación-propuesta)
10. [Nuevo Mapa de Menú](#10-nuevo-mapa-de-menú)
11. [Recomendaciones por Pantalla](#11-recomendaciones-por-pantalla)
12. [Recomendaciones por Tipo de Usuario](#12-recomendaciones-por-tipo-de-usuario)
13. [Recomendaciones de Componentes](#13-recomendaciones-de-componentes)
14. [Recomendaciones de Diseño Visual](#14-recomendaciones-de-diseño-visual)
15. [Recomendaciones Mobile-First](#15-recomendaciones-mobile-first)
16. [Recomendaciones de Web Administrativa](#16-recomendaciones-de-web-administrativa)
17. [Matriz de Cambios Recomendados](#17-matriz-de-cambios-recomendados)
18. [Priorización de Mejoras](#18-priorización-de-mejoras)
19. [Riesgos de Tocar Lógica Funcional](#19-riesgos-de-tocar-lógica-funcional)
20. [Criterios de Aceptación](#20-criterios-de-aceptación)

---

## 1. Resumen Ejecutivo

Global Avícola es una plataforma empresarial web/mobile-first para la gestión operativa del ciclo productivo avícola completo (abuelas → reproductoras → incubación → engorde), integrada con SAP. El frontend actual está construido con React 19 + Vite + TypeScript + TailwindCSS v4, con una arquitectura sólida, un catálogo de procesos bien definido (`processCatalog.ts`), y componentes UI reutilizables.

**Hallazgo principal:** La aplicación tiene una base técnica excelente y procesos avícolas correctamente implementados, pero la **navegación y experiencia de usuario necesitan una evolución significativa** para alcanzar el nivel de calidad visual y operativa que el proyecto merece.

**Problemas clave identificados:**

| # | Problema | Impacto | Prioridad |
|---|----------|---------|-----------|
| 1 | Menú lateral plano (11 items) sin jerarquía ni agrupación | Alto | Inmediata |
| 2 | "Processes" y "Operations" como entidades separadas en el menú | Alto | Inmediata |
| 3 | Sin submenús colapsables — toda la navegación es plana | Alto | Inmediata |
| 4 | Sin breadcrumbs — el usuario pierde contexto de profundidad | Medio | Alta |
| 5 | Sin indicador visual de jerarquía (Fase → Subfase → Operación) | Medio | Alta |
| 6 | Mobile bottom nav con solo 5 genéricos sin contexto de proceso | Medio | Alta |
| 7 | MobileDrawer con solo 6 items — subutilizado | Medio | Media |
| 8 | Pantallas sobrecargadas de filtros (ReviewCenter) | Medio | Media |
| 9 | Sin vista consolidada de "Gestión Avícola" desde el sidebar | Alto | Inmediata |
| 10 | Dashboard sin atajos rápidos a operaciones frecuentes | Bajo | Media |
| 11 | Sin distinción visual clara entre secciones operativas vs administrativas | Medio | Alta |
| 12 | Auditoría y SAP como páginas planas sin estructura interna | Bajo | Media |

**Calificación general de UI/UX actual:** 6.5/10  
**Calificación objetivo post-implementación:** 9.5/10

---

## 2. Auditoría de Atenea — Referencia de Navegación

### 2.1 Datos del proyecto auditado

| Atributo | Valor |
|----------|-------|
| **Nombre** | Atenea (atenea-front) |
| **Tipo** | Software de nómina / RH (payroll) |
| **Stack** | React 19 + Vite + TypeScript + TailwindCSS v4 |
| **Ruta** | `/home/maria/Proyectos/atenea-front` |

### 2.2 Estructura de navegación

**Menú lateral (sidebar):**

```
┌──────────────────────────┐
│  [Logo AteneaRH]         │
│                          │
│  🧭 Dashboard            │
│  ⚙️ Settings             │
│  👥 HR Admin             │
│  👛 Payroll              │
│  🏆 Performance          │
│  📊 Reportes             │
│  ✅ Mi Atenea            │
│                          │
│  [User Avatar]           │
│  🚪 Logout               │
└──────────────────────────┘
```

- **7 items planos** (sin submenús colapsables)
- Íconos Lucide a 16px
- Estado activo con gradiente (`gradient-brand`) + sombra
- Hover con desplazamiento horizontal (`hover:translate-x-1`)
- Texto `text-[11px] font-bold` (compacto pero legible)

**Subnavegación interna:**

Atenea implementa un **patrón de dos niveles** muy efectivo:

1. **Nivel 1 (Sidebar):** Módulos principales (Dashboard, Settings, HR, Payroll, etc.)
2. **Nivel 2 (Interno del módulo):** Cada módulo usa `useSubNavigation` + `SubNavHeader` con:
   - Botón "Atrás" (back)
   - Breadcrumbs (migajas de pan)
   - Grid de tarjetas de menú para las opciones internas

```
┌──────────────────────────────────────────────────┐
│  ← Settings  ›  Company Details                  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Company  │  │ Org      │  │ Tax      │       │
│  │ Info     │  │ Levels   │  │ Setup    │       │
│  └──────────┘  └──────────┘  └──────────┘       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Payroll  │  │ Benefit  │  │ Work     │       │
│  │ Config   │  │ Plans    │  │ Schedule │       │
│  └──────────┘  └──────────┘  └──────────┘       │
└──────────────────────────────────────────────────┘
```

### 2.3 Patrones de Atenea que SIRVEN como inspiración

| Patrón | Descripción | Aplica a Global Avícola |
|--------|-------------|------------------------|
| **Sidebar con módulos claros** | 7 items de alto nivel, fáciles de escanear | ✅ Sí — agrupar módulos en vez de 11 items planos |
| **SubNavHeader con breadcrumbs** | Back + breadcrumbs que muestran profundidad | ✅ Sí — esencial para navegación jerárquica |
| **Grid de tarjetas de menú** | Opciones internas como tarjetas icono+texto | ✅ Sí — perfecto para operaciones dentro de una fase |
| **useSubNavigation (history stack)** | Pila de navegación para sub-vistas con back | ✅ Sí — implementar hook similar |
| **Estados activos con gradiente** | Active tab con fondo gradiente + sombra | ✅ Sí — mejorar el active state actual |
| **Hover con desplazamiento** | Pequeño translate-x en hover para feedback | ✅ Sí — micro-interacción sutil |
| **Layout consistente** | Sidebar w-64 + header h-16 + padding uniforme | ✅ Sí — mantener consistencia |
| **Permisos en sidebar** | Items ocultos según rol del usuario | ✅ Sí — ya existe, pero mejorar visibilidad |
| **Glass morphism moderado** | Backdrop blur en headers y cards | ⚠️ Con medida — solo en headers |
| **Gradientes en hero sections** | Decorativos, no funcionales | ✅ Sí — ya existe en ProcessHub |

### 2.4 Lo que Atenea NO tiene (y Global Avícola tampoco necesita)

| Ausencia en Atenea | Relevancia para Global Avícola |
|--------------------|-------------------------------|
| Sin submenús colapsables | Global Avícola SÍ necesita submenús jerárquicos |
| Sin React Router (estado plano) | Global Avícola SÍ tiene React Router (correcto) |
| Sin breadcrumbs nativos | Global Avícola necesita breadcrumbs |
| Sin distinción visual de módulos | Global Avícola necesita agrupar visualmente |

---

## 3. Qué NO debe copiarse de Atenea

| Elemento | Razón |
|----------|-------|
| **Colores exactos** | Atenea usa teal/cyan como primario; Global Avícola usa azul corporativo (#1E3A5F / #2563EB) |
| **Branding "AteneaRH"** | Global Avícola tiene su propia identidad corporativa |
| **Texto "Settings", "HR Admin", "Payroll"** | Son módulos de nómina, no aplican a gestión avícola |
| **Estructura funcional de nómina** | No copiar lógica de payroll, employees, performance reviews |
| **Flat navigation sin jerarquía** | Global Avícola necesita jerarquía (Fase → Subfase → Operación) |
| **State-based routing sin React Router** | React Router es superior y ya está implementado |
| **Dependencias innecesarias** | No copiar @telegram-apps, organizational-chart, etc. |
| **MiAteneaMobileShell** | Global Avícola tiene su propio patrón mobile |
| **Dark mode completo** | Global Avícola optó por diseño claro corporativo (sin dark mode) |

---

## 4. Auditoría de Global Avícola — Estado Actual

### 4.1 Mapa de navegación actual

```
SIDEBAR (11 items planos — sin jerarquía)
─────────────────────────────────────────
🏠 Home          →  /                    (DashboardPage)
⚙️ Processes     →  /processes           (ProcessHubPage → 6 stages)
🐔 Lots          →  /lots                (LotListPage)
📄 Operations    →  /operations          (OperationListPage)
🗄️ Masters       →  /masters/:entity     (12 entities)
🔍 Review        →  /review              (ReviewCenter)
✅ Approvals     →  /approvals           (ApprovalPanel)
📈 Reports       →  /reports             (ReportsPage)
🛡️ Audit         →  /audit               (AuditPage)
🔄 SAP           →  /sap                 (SapManagerPage)
👥 Users         →  /users               (UsersPage)
```

### 4.2 Análisis de la estructura actual

**Fortalezas:**

✅ **ProcessCatalog bien definido:** 6 etapas productivas, 24 tipos de evento, flujos por etapa, colores e íconos. Es la columna vertebral correcta.

✅ **Componentes UI reutilizables:** Button, Badge, Card, Input, Modal, DataTable — base sólida.

✅ **Responsive:** Sidebar desktop + BottomNav mobile + Drawer.

✅ **i18n completo:** Español/Inglés desde el inicio.

✅ **Rutas claras:** `/processes/:stage`, `/lots/:id`, `/review/:id` — URL semántica.

✅ **Protección de rutas:** `ProtectedRoute`, `WebOnlyRoute` — correcta separación.

✅ **Design system documentado:** `docs/11-ui-ux-design-system.md` con paleta, tipografía, componentes.

✅ **ProcessHub visualmente atractivo:** Gradientes, tarjetas, contadores.

**Debilidades:**

❌ **Sidebar plano sin submenús:** 11 items al mismo nivel. No hay manera de navegar directamente a "Reproductoras → Cría" desde el sidebar.

❌ **"Processes" y "Operations" separados:** Conceptual y funcionalmente son lo mismo. Un operador no distingue entre "ir a procesos" e "ir a operaciones".

❌ **Sin breadcrumbs:** Al navegar a `/processes/breeder_rearing`, no hay indicación visual de "Gestión Avícola → Reproductoras → Cría".

❌ **MobileDrawer infrautilizado:** Solo 6 items genéricos cuando podría mostrar la jerarquía completa.

❌ **Sin agrupación visual en sidebar:** Masters, Review, Approvals, Reports, Audit, SAP, Users — todo mezclado sin separación entre operativo, revisión, reportes y configuración.

❌ **Dashboard sin atajos operativos:** Muestra KPIs pero no permite al operador ir rápidamente a su tarea del día.

❌ **ReviewCenter sobrecargado:** Demasiados filtros en una sola fila, sin agrupación lógica.

❌ **SAP como página plana:** Sin sub-secciones para órdenes, documentos, envíos, errores.

❌ **Auditoría como página plana:** Sin separación por lote/usuario/documento SAP.

---

## 5. Problemas Actuales de Navegación

### 5.1 Problemas Estructurales

| ID | Problema | Descripción | Severidad |
|----|----------|-------------|-----------|
| NAV-01 | **Menú sin jerarquía avícola** | El sidebar trata "Grandparent", "Breeder", "Hatchery", "Broiler" como un solo ítem "Processes". No se puede navegar directamente a una fase específica. | 🔴 Alta |
| NAV-02 | **Processes vs Operations confusos** | Son rutas separadas en el menú, pero funcionalmente son el mismo flujo. El operador no sabe cuál usar. | 🔴 Alta |
| NAV-03 | **Sin submenús colapsables** | No hay manera de expandir "Gestión Avícola" para ver sus fases, o expandir "Reproductoras" para ver Cría/Producción. | 🔴 Alta |
| NAV-04 | **Sin breadcrumbs** | El usuario no sabe dónde está en la jerarquía. Ej: está en una operación de mortalidad ¿de qué lote? ¿qué fase? | 🟡 Media |
| NAV-05 | **Sin atajos contextuales** | Desde un lote no se puede ir directamente a "Registrar mortalidad". Hay que ir a Processes → seleccionar etapa → seleccionar operación. | 🟡 Media |

### 5.2 Problemas de Información

| ID | Problema | Descripción | Severidad |
|----|----------|-------------|-----------|
| NAV-06 | **Falta de contexto en rutas** | `/operations/new?type=mortality_recording&lot_id=123` — la URL no muestra la jerarquía (fase, subfase). | 🟡 Media |
| NAV-07 | **Masters es un cajón de sastre** | 12 entidades diferentes en una sola ruta genérica `/masters/:entity`. Sin agrupación por tipo (granjas, insumos, parámetros). | 🟡 Media |
| NAV-08 | **Reportes sin organización** | ReportsPage central pero sin sub-navegación para producción, mortalidad, pesaje, SAP comparison. | 🟢 Baja |

---

## 6. Problemas Actuales de UI

### 6.1 Problemas Visuales

| ID | Problema | Descripción | Severidad |
|----|----------|-------------|-----------|
| UI-01 | **Sidebar visualmente denso** | 11 items verticales sin separación, agrupación o jerarquía visual. Cansa la vista. | 🔴 Alta |
| UI-02 | **Falta de distinción de secciones** | Un sidebar item "Masters" (administrativo) está al mismo nivel que "Processes" (operativo). Sin separador visual. | 🟡 Media |
| UI-03 | **ReviewCenter: filtros desordenados** | 7+ filtros en una fila horizontal sin agrupar. En mobile esto se rompe. | 🟡 Media |
| UI-04 | **Active state poco destacado** | El azul `bg-blue-700` sobre `bg-[#1E3A5F]` tiene poco contraste. | 🟡 Media |
| UI-05 | **Sin loading skeletons** | Las páginas muestran un spinner genérico o texto "Cargando..." en lugar de skeletons contextuales. | 🟢 Baja |
| UI-06 | **Empty states genéricos** | Cuando no hay datos, se muestra una pantalla en blanco o solo "No data". | 🟢 Baja |
| UI-07 | **Sin breadcrumbs visuales** | No hay indicador de profundidad en ninguna página. | 🟡 Media |

### 6.2 Problemas de Consistencia

| ID | Problema | Descripción | Severidad |
|----|----------|-------------|-----------|
| UI-08 | **Tamaños de botón inconsistentes** | Algunos botones son `px-4 py-2`, otros `px-3 py-1.5`. Sin estándar unificado. | 🟢 Baja |
| UI-09 | **Formularios sin secciones** | OperationFormPage muestra campos sin agrupar por categorías (ej: "Datos del ave", "Control sanitario"). | 🟡 Media |
| UI-10 | **Tablas sin estandarización** | Algunas usan DataTable, otras tablas HTML directas con estilos inconsistentes. | 🟡 Media |

---

## 7. Problemas de Experiencia Mobile

| ID | Problema | Descripción | Severidad |
|----|----------|-------------|-----------|
| MOB-01 | **MobileNav genérico** | 5 botones fijos (Home, Lots, Processes, KPIs, Pending) sin adaptación al contexto del lote activo. | 🔴 Alta |
| MOB-02 | **MobileDrawer subutilizado** | Solo 6 items, no aprovecha para mostrar acceso rápido a fases productivas. | 🟡 Media |
| MOB-03 | **Sin "quick actions" en dashboard mobile** | El operador debería poder tocar "Registrar mortalidad" directo desde el dashboard. | 🟡 Media |
| MOB-04 | **Formularios largos sin secciones colapsables** | Los formularios operativos son largos y no están divididos en pasos o secciones. | 🟡 Media |
| MOB-05 | **Sin indicador de progreso en registro** | El operador no sabe cuántos pasos faltan para completar un registro. | 🟢 Baja |
| MOB-06 | **Touch targets pequeños en filtros** | Los selects y campos de filtro en ReviewCenter tienen padding insuficiente para mobile. | 🟡 Media |

---

## 8. Problemas de Experiencia Web

| ID | Problema | Descripción | Severidad |
|----|----------|-------------|-----------|
| WEB-01 | **Dashboard sin atajos administrativos** | El supervisor necesita llegar rápido a Revisión, Aprobaciones, Reportes. Hoy tiene que navegar por el sidebar. | 🟡 Media |
| WEB-02 | **SapManagerPage sin sub-secciones** | Órdenes de compra, transferencias, pendientes, errores — todo en una página sin tabs. | 🟡 Media |
| WEB-03 | **AuditPage sin filtros avanzados** | Auditoría sin capacidad de filtrar por lote, usuario, rango de fechas o tipo de acción. | 🟡 Media |
| WEB-04 | **ApprovalPanel sin resumen ejecutivo** | El aprobador ve una lista sin KPIs: cuántos pendientes, cuántos aprobados hoy, diferencias críticas. | 🟡 Media |
| WEB-05 | **Sin vista comparativa lado a lado** | Al revisar, el supervisor no ve fácilmente "valor original vs valor corregido". | 🟢 Baja |

---

## 9. Nueva Arquitectura de Navegación Propuesta

### 9.1 Principios de diseño

1. **Jerarquía clara de 3 niveles:** Módulo → Fase → Operación
2. **Separación visual de secciones:** Operativo | Revisión | Reportes | Administración
3. **Submenús colapsables** para no saturar el sidebar
4. **Breadcrumbs siempre visibles** en páginas internas
5. **Atajos contextuales** desde dashboard y detalle de lote
6. **Mobile adaptativo:** bottom nav contextual, no genérico

### 9.2 Estructura de navegación conceptual

```
NIVEL 1 (Sidebar)          NIVEL 2 (Submenú)          NIVEL 3 (Operaciones)
─────────────────          ──────────────────         ─────────────────────────
📊 Dashboard
                           
🐔 Gestión Avícola         
  ▼ Abuelas                Importación, Recepción, Cuarentena, Activación
  ▼ Progenitoras           Cría, Producción, Huevos a Incubadora
  ▼ Reproductoras          Cría, Producción, Huevos a Incubadora
  ▼ Incubadora Progenitoras  Recepción, Incubación, Nacimiento, Despacho
  ▼ Incubadora             Recepción, Incubación, Nacimiento, Despacho
  ▼ Pollo de Engorde       Recepción, Engorde, Salida, Cierre

📋 Centro de Revisión     
  ▼ Pendientes             
  ▼ En Revisión            
  ▼ Devueltos              
  ▼ Aprobados              
  ▼ Consolidados           

🔄 Integración SAP         
  ▼ Órdenes de Compra      
  ▼ Órdenes de Transferencia
  ▼ Documentos Pendientes  
  ▼ Envíos a SAP           
  ▼ Errores SAP            
  ▼ Bitácora SAP           

📈 Reportes                
  ▼ Producción             
  ▼ Mortalidad             
  ▼ Pesaje                 
  ▼ Alimento               
  ▼ Incubación             
  ▼ Engorde                
  ▼ Diferencias SAP vs App 

🛡️ Auditoría              
  ▼ Por Lote               
  ▼ Por Usuario            
  ▼ Por Documento SAP      
  ▼ Cambios y Correcciones 

⚙️ Configuración           
  ▼ Maestros               (Empresas, Granjas, Galpones, Líneas Genéticas, etc.)
  ▼ Flujos de Aprobación   
  ▼ Estados                
  ▼ Parámetros             
  ▼ Idioma y Preferencias  

👥 Usuarios y Roles        
```

### 9.3 Flujo de navegación del operador (mobile)

```
Dashboard
  │
  └─→ "Registrar" (botón quick action)
       │
       └─→ Seleccionar Lote (lista de lotes activos del operador)
              │
              └─→ Fase activa del lote (automática según fase actual)
                     │
                     └─→ Operación específica (mortalidad, alimento, etc.)
                            │
                            └─→ Formulario → Confirmar → Éxito
```

### 9.4 Flujo de navegación del supervisor (web)

```
Dashboard (KPIs consolidados)
  │
  ├─→ Gestión Avícola → Fase → Lote → Operaciones → Revisar
  ├─→ Centro de Revisión → Pendientes → Revisar → Corregir/Aprobar/Devolver
  ├─→ Reportes → Producción/Mortalidad → Exportar
  └─→ Auditoría → Por Lote → Trazabilidad completa
```

### 9.5 Flujo de navegación del aprobador (web)

```
Dashboard (resumen ejecutivo)
  │
  └─→ Centro de Revisión → Aprobados → Consolidar
       │
       └─→ Revisar diferencias → Aprobar/Rechazar
              │
              └─→ Auditoría visible → Confirmar → SAP ready
```

### 9.6 Flujo de navegación del usuario SAP (web)

```
Dashboard (estado de integración)
  │
  ├─→ Integración SAP → Documentos Pendientes → Ver Payload → Enviar
  ├─→ Integración SAP → Errores SAP → Reintentar
  └─→ Reportes → Diferencias SAP vs App → Exportar
```

---

## 10. Nuevo Mapa de Menú

### 10.1 Sidebar (Desktop) — Propuesta final

```
┌──────────────────────────────┐
│  GLOBAL AVÍCOLA              │
│  Gestión Avícola             │  ← Logo + tagline
├──────────────────────────────┤
│                              │
│  📊 Dashboard                │  ← Siempre visible
│                              │
│  ─── OPERATIVO ───           │  ← Separador
│                              │
│  🐔 Gestión Avícola          │  ← Colapsable con submenú
│  ▼                           │
│    ├─ Abuelas                │  ← Sub-items
│    │  ├─ Importación         │
│    │  ├─ Recepción           │
│    │  ├─ Cuarentena          │
│    │  └─ Activación          │
│    ├─ Progenitoras           │
│    │  ├─ Cría                │
│    │  ├─ Producción          │
│    │  └─ Huevos a Incubadora │
│    ├─ Reproductoras          │
│    │  ├─ Cría                │
│    │  ├─ Producción          │
│    │  └─ Huevos a Incubadora │
│    ├─ Incub. Progenitoras    │
│    │  ├─ Recepción Huevos    │
│    │  ├─ Incubación          │
│    │  ├─ Nacimiento          │
│    │  └─ Despacho            │
│    ├─ Incubadora             │
│    │  ├─ Recepción Huevos    │
│    │  ├─ Incubación          │
│    │  ├─ Nacimiento          │
│    │  └─ Despacho a Engorde  │
│    └─ Pollo de Engorde       │
│       ├─ Recepción           │
│       ├─ Engorde             │
│       ├─ Salida              │
│       └─ Cierre de Lote      │
│                              │
│  ─── REVISIÓN ───            │  ← Separador
│                              │
│  📋 Centro de Revisión       │  ← Colapsable
│  ▼                           │
│    ├─ Pendientes             │
│    ├─ En Revisión            │
│    ├─ Devueltos              │
│    ├─ Aprobados              │
│    └─ Consolidados           │
│                              │
│  ✅ Aprobaciones             │  ← Acceso directo
│                              │
│  ─── INTEGRACIÓN ───         │  ← Separador
│                              │
│  🔄 Integración SAP          │  ← Colapsable
│  ▼                           │
│    ├─ Órdenes de Compra      │
│    ├─ Órdenes Transferencia  │
│    ├─ Documentos Pendientes  │
│    ├─ Envíos a SAP           │
│    ├─ Errores SAP            │
│    └─ Bitácora SAP           │
│                              │
│  ─── REPORTES ───            │  ← Separador
│                              │
│  📈 Reportes                 │  ← Colapsable
│  ▼                           │
│    ├─ Producción             │
│    ├─ Mortalidad             │
│    ├─ Pesaje                 │
│    ├─ Alimento               │
│    ├─ Incubación             │
│    ├─ Engorde                │
│    └─ Diferencias SAP vs App │
│                              │
│  ─── ADMINISTRACIÓN ───      │  ← Separador
│                              │
│  🛡️ Auditoría               │  ← Colapsable
│  ▼                           │
│    ├─ Por Lote               │
│    ├─ Por Usuario            │
│    ├─ Por Documento SAP      │
│    └─ Cambios y Correcciones │
│                              │
│  ⚙️ Maestros                 │  ← Colapsable
│  ▼                           │
│    ├─ Empresas               │
│    ├─ Granjas                │
│    ├─ Galpones               │
│    ├─ Incubadoras            │
│    ├─ Líneas Genéticas       │
│    ├─ Razas                  │
│    ├─ Alimentos              │
│    ├─ Vacunas                │
│    ├─ Medicamentos           │
│    ├─ Causas Mortalidad      │
│    └─ más...                 │
│                              │
│  ⚙️ Configuración            │  ← Colapsable
│  ▼                           │
│    ├─ Flujos de Aprobación   │
│    ├─ Estados                │
│    ├─ Parámetros             │
│    └─ Idioma y Preferencias  │
│                              │
│  👥 Usuarios y Roles         │  ← Acceso directo
│                              │
├──────────────────────────────┤
│  👤 María García             │  ← User section
│  ⚙️ Perfil  🚪 Salir        │
└──────────────────────────────┘
```

### 10.2 Mobile Bottom Navigation — Propuesta

```
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│   🏠     │   📝     │   🐔     │   📊     │   👤     │
│  Inicio  │ Registrar│  Lotes   │   KPIs   │  Menú    │
└──────────┴──────────┴──────────┴──────────┴──────────┘
```

- **Inicio:** Dashboard móvil con quick actions
- **Registrar:** Flujo guiado rápido: Seleccionar Lote → Fase → Operación → Formulario
- **Lotes:** Lista de lotes activos del operador
- **KPIs:** Indicadores del lote activo (cambia según contexto)
- **Menú:** Drawer completo con toda la jerarquía (como sidebar desktop)

### 10.3 Mapa de rutas propuesto

| Ruta | Componente | Descripción |
|------|-----------|-------------|
| `/` | `DashboardPage` | Dashboard con KPIs + atajos |
| `/poultry` | `PoultryHubPage` | Gestión Avícola — vista general |
| `/poultry/grandparent/rearing` | `StagePage` | Abuelas — Cría |
| `/poultry/grandparent/production` | `StagePage` | Abuelas — Producción |
| `/poultry/breeder/rearing` | `StagePage` | Reproductoras — Cría |
| `/poultry/breeder/production` | `StagePage` | Reproductoras — Producción |
| `/poultry/hatchery` | `StagePage` | Incubadora |
| `/poultry/broiler` | `StagePage` | Pollo de Engorde |
| `/review` | `ReviewCenter` | Centro de Revisión |
| `/review/pending` | `ReviewList` | Pendientes |
| `/review/in-review` | `ReviewList` | En Revisión |
| `/review/returned` | `ReviewList` | Devueltos |
| `/review/approved` | `ReviewList` | Aprobados |
| `/review/consolidated` | `ReviewList` | Consolidados |
| `/review/:id` | `ReviewDetail` | Detalle de revisión |
| `/approvals` | `ApprovalPanel` | Panel de aprobaciones |
| `/sap` | `SapManagerPage` | Integración SAP (dashboard) |
| `/sap/purchase-orders` | `SapOrdersPage` | Órdenes de compra |
| `/sap/transfer-orders` | `SapTransferPage` | Órdenes de transferencia |
| `/sap/pending` | `SapPendingPage` | Documentos pendientes |
| `/sap/sent` | `SapSentPage` | Envíos a SAP |
| `/sap/errors` | `SapErrorsPage` | Errores SAP |
| `/sap/log` | `SapLogPage` | Bitácora SAP |
| `/reports` | `ReportsPage` | Reportes (dashboard) |
| `/reports/production` | `ReportDetail` | Reporte de producción |
| `/reports/mortality` | `ReportDetail` | Reporte de mortalidad |
| `/reports/weighing` | `ReportDetail` | Reporte de pesaje |
| `/reports/feed` | `ReportDetail` | Reporte de alimento |
| `/reports/hatchery` | `ReportDetail` | Reporte de incubación |
| `/reports/broiler` | `ReportDetail` | Reporte de engorde |
| `/reports/sap-diff` | `SapComparisonPage` | Diferencias SAP vs App |
| `/audit` | `AuditPage` | Auditoría (dashboard) |
| `/audit/lot/:id` | `AuditDetail` | Auditoría por lote |
| `/audit/user/:id` | `AuditDetail` | Auditoría por usuario |
| `/audit/sap/:id` | `AuditDetail` | Auditoría por documento SAP |
| `/audit/corrections` | `AuditCorrections` | Cambios y correcciones |
| `/masters` | `MastersHubPage` | Maestros (vista agrupada) |
| `/masters/farms` | `MasterListPage` | Granjas |
| `/masters/houses` | `MasterListPage` | Galpones |
| ... | ... | (resto de entidades agrupadas por categoría) |
| `/settings` | `SettingsPage` | Configuración |
| `/settings/approval-flows` | `ApprovalFlowsPage` | Flujos de aprobación |
| `/settings/parameters` | `ParamsPage` | Parámetros |
| `/settings/preferences` | `PreferencesPage` | Preferencias |
| `/users` | `UsersPage` | Usuarios y roles |
| `/lots` | `LotListPage` | Lista de lotes |
| `/lots/:id` | `LotDetailPage` | Detalle de lote |
| `/operations/new` | `OperationFormPage` | Nueva operación |
| `/operations/:id` | `OperationDetailPage` | Detalle de operación |

---

## 11. Recomendaciones por Pantalla

### 11.1 Dashboard (`/`)

| Aspecto | Recomendación |
|---------|---------------|
| **Layout** | Dividir en 3 zonas: (1) KPIs ejecutivos, (2) Atajos rápidos, (3) Últimas operaciones |
| **Operador mobile** | Botón "Registrar" grande y visible, lista de lotes activos del operador, quick actions contextuales |
| **Supervisor web** | KPIs consolidados por fase, gráficos de tendencia, bandeja de pendientes, atajos a Revisión y Reportes |
| **Aprobador** | Resumen de aprobaciones pendientes, diferencias críticas, acceso directo a Consolidación |
| **Usuario SAP** | Estado de integración, documentos pendientes de envío, último error SAP |
| **Mejora visual** | Tarjetas KPI con icono + valor + label + indicador de tendencia (↑↓) |

### 11.2 Gestión Avícola (`/poultry`)

| Aspecto | Recomendación |
|---------|---------------|
| **Nueva pantalla** | Hub tipo mosaico con las 6 fases productivas (similar al ProcessHub actual pero renombrado) |
| **Navegación** | Al hacer clic en una fase, ir a `/poultry/{fase}` con subfases (Cría/Producción) |
| **Indicadores** | Cada fase muestra: lotes activos, última operación, alertas |
| **Mobile** | Misma vista pero scroll vertical con cards más compactas |

### 11.3 Proceso/Fase (`/poultry/{fase}/{subfase}`)

| Aspecto | Recomendación |
|---------|---------------|
| **Header** | Breadcrumb: Gestión Avícola › Reproductoras › Cría |
| **Selector de lote** | Mejorar el selector actual con búsqueda y filtro por estado |
| **Operaciones** | Grid de tarjetas (ya existe, mantener) agrupadas por categoría (Movimiento, Diario, Sanidad, Huevos) |
| **Información** | Mostrar resumen del lote seleccionado (edad, población, días en fase) |
| **Atajos** | Botón "Ver historial del lote" que navega a `/lots/:id` |

### 11.4 Centro de Revisión (`/review`)

| Aspecto | Recomendación |
|---------|---------------|
| **Sub-navegación** | Tabs o submenú: Pendientes | En Revisión | Devueltos | Aprobados | Consolidados |
| **Filtros** | Agrupar en sección colapsable: "Filtros" con subgrupos (Fecha, Lote, Operador, Tipo) |
| **Vista mobile** | Tarjetas deslizables con acción rápida (Aprobar/Devolver) |
| **Comparación** | Vista lado a lado: valor original vs valor registrado vs valor corregido |
| **Batch actions** | Checkboxes + botón "Acción por lote" (ya existe, mejorar UI) |

### 11.5 Aprobaciones (`/approvals`)

| Aspecto | Recomendación |
|---------|---------------|
| **Resumen ejecutivo** | KPIs: Pendientes, Aprobados hoy, Rechazados hoy, Tiempo promedio de aprobación |
| **Lista** | Tabla con expansión inline para ver detalle sin cambiar de página |
| **Acción** | Botones Aprobar/Rechazar grandes con confirmación modal |
| **Auditoría** | Al aprobar, mostrar resumen de auditoría: quién registró, quién corrigió, histórico |

### 11.6 Integración SAP (`/sap`)

| Aspecto | Recomendación |
|---------|---------------|
| **Dashboard SAP** | Resumen: Pendientes de envío, Enviados, Errores, Última sincronización |
| **Sub-secciones** | Tabs: Órdenes Compra | Órdenes Transferencia | Pendientes | Enviados | Errores | Bitácora |
| **Payload viewer** | Modal o panel expandible para ver JSON del payload antes de enviar |
| **Errores** | Lista con código de error, mensaje, fecha, botón "Reintentar" |
| **Bitácora** | Timeline de todas las interacciones con SAP |

### 11.7 Reportes (`/reports`)

| Aspecto | Recomendación |
|---------|---------------|
| **Dashboard reportes** | Grid de tarjetas por tipo de reporte con última fecha de generación |
| **Filtros globales** | Selector de rango de fechas + granja + lote aplicado a todos los reportes |
| **Exportación** | Botón Exportar Excel/PDF visible en cada reporte |
| **Comparativa SAP** | Mantener `SapComparisonPage` pero integrarla como un reporte más |

### 11.8 Auditoría (`/audit`)

| Aspecto | Recomendación |
|---------|---------------|
| **Dashboard auditoría** | Tabs: Por Lote | Por Usuario | Por Documento SAP | Cambios |
| **Timeline visual** | Línea de tiempo horizontal con eventos: Registro → Revisión → Corrección → Aprobación → SAP |
| **Filtros** | Búsqueda por lote, usuario, rango de fechas, tipo de evento |
| **Detalle de cambio** | Mostrar: Valor original → Valor corregido, con quién, cuándo y motivo |

### 11.9 Maestros (`/masters`)

| Aspecto | Recomendación |
|---------|---------------|
| **Agrupación** | Categorizar en: (1) Granjas (empresas, granjas, galpones), (2) Insumos (alimentos, vacunas, medicamentos), (3) Parámetros (líneas genéticas, razas, causas), (4) Logística (transportes, plantas) |
| **Vista mosaico** | En lugar de enrutar directo a lista, mostrar mosaico de categorías → luego entidad |
| **CRUD consistente** | Mantener MasterListPage pero con header y breadcrumb apropiados |

### 11.10 Detalle de Lote (`/lots/:id`)

| Aspecto | Recomendación |
|---------|---------------|
| **Header** | Breadcrumb: Gestión Avícola › Reproductoras › Cría › Lote L-2026-001 |
| **Resumen** | Fase actual, edad, población, días restantes estimados |
| **Quick actions** | Botones para las operaciones más frecuentes de la fase actual |
| **Trazabilidad** | Mantener TraceabilityTree pero mejorar visualmente |
| **Timeline** | Línea de tiempo de eventos del lote |

### 11.11 Configuración (`/settings`)

| Aspecto | Recomendación |
|---------|---------------|
| **Nueva sección** | Separar de Maestros: Flujos de aprobación, Estados, Parámetros, Preferencias |
| **Idioma** | Selector de idioma en Preferencias (no solo en header) |

---

## 12. Recomendaciones por Tipo de Usuario

### 12.1 Operador Mobile

| Necesidad | Solución propuesta |
|-----------|-------------------|
| Acceso rápido a tareas del día | Dashboard mobile con lista "Mis lotes" + botón "Registrar" grande |
| Menú simplificado | Bottom nav con: Inicio, Registrar, Lotes, KPIs, Menú |
| Botones grandes | Touch targets ≥ 44×44px en todos los elementos interactivos |
| Formularios cortos | Dividir formularios largos en pasos (wizard) con indicador de progreso |
| Pocas capas de navegación | Máximo 3 taps para llegar a cualquier operación |
| Guardado rápido | Botón "Guardar y salir" + "Guardar y otro" para registros consecutivos |
| Validaciones claras | Error inline debajo del campo, con icono y color rojo |
| Historial del lote | Botón "Ver historial" visible desde el formulario |
| Estado visible del registro | Badge de estado después de guardar (Registrado ✓) |
| Confirmación antes de enviar | Modal de confirmación con resumen de datos ingresados |

### 12.2 Supervisor Web

| Necesidad | Solución propuesta |
|-----------|-------------------|
| Vista consolidada | Dashboard con KPIs por fase y lotes activos |
| Bandeja de revisión | ReviewCenter con tabs por estado (Pendientes/En revisión/Devueltos) |
| Filtros | Panel de filtros colapsable con búsqueda textual |
| Comparación de datos | Vista lado a lado: valor registrado vs histórico |
| Corrección antes de aprobar | Flujo: Revisar → Corregir (con motivo) → Aprobar |
| Observaciones | Campo de texto obligatorio para devolución, opcional para aprobación |
| Aprobación o devolución | Botones grandes con color (Verde ✓ / Rojo ✗) + confirmación modal |
| Estados por lote | Badge de estado visible en cada operación |
| Trazabilidad | Link "Ver trazabilidad" en cada operación → Timeline |

### 12.3 Aprobador

| Necesidad | Solución propuesta |
|-----------|-------------------|
| Panel ejecutivo | KPIs: Pendientes, Aprobados hoy, Rechazados, Tiempo promedio |
| Registros listos | Lista filtrada por "Listo para aprobar" |
| Resumen consolidado | Vista de lote con todas las operaciones pendientes de aprobación |
| Diferencias críticas | Alertas visuales cuando hay diferencias > umbral configurable |
| Botón aprobar/rechazar | Modal de confirmación con motivo obligatorio para rechazo |
| Firma o confirmación | Checkbox "Confirmo la revisión de estos datos" antes de aprobar |
| Auditoría visible | Panel de auditoría expandible en la misma página |

### 12.4 Usuario SAP

| Necesidad | Solución propuesta |
|-----------|-------------------|
| Documentos SAP origen | Lista de órdenes de compra/transferencia importadas |
| Datos aprobados | Vista de registros aprobados listos para envío |
| Payload preparado | Panel JSON expandible con el payload que se enviará |
| Estado de envío | Badge por documento: Pendiente, Enviado, Error, Confirmado |
| Errores SAP | Lista de errores con código, mensaje, fecha, botón reintentar |
| Reintentos | Botón "Reintentar" con registro de intentos anteriores |
| Confirmación SAP | Badge "Confirmado SAP" con ID de documento SAP |

### 12.5 Administrador

| Necesidad | Solución propuesta |
|-----------|-------------------|
| Maestros | Categorizar en subgrupos: Granjas, Insumos, Parámetros, Logística |
| Usuarios | Tabla con búsqueda, filtro por rol, edición inline |
| Roles | Gestión de roles con permisos por módulo |
| Configuración de flujos | Editor visual o formulario para configurar niveles de aprobación |
| Parámetros | Lista de parámetros del sistema con edición |
| Auditoría | Acceso completo a auditoría con filtros avanzados |

---

## 13. Recomendaciones de Componentes

### 13.1 Componentes a crear

| Componente | Descripción | Prioridad |
|------------|-------------|-----------|
| **SidebarMenu** | Menú lateral refactorizado con submenús colapsables, secciones, y animaciones | 🔴 Alta |
| **Breadcrumbs** | Componente de migas de pan con icono de casa + chevrons + estado activo | 🔴 Alta |
| **SubNavHeader** | Header de subpágina con back button + título + breadcrumbs | 🔴 Alta |
| **SectionDivider** | Separador visual con etiqueta de texto (ej: "— OPERATIVO —") | 🟡 Media |
| **CollapsibleGroup** | Contenedor expandible/colapsable con icono de chevron animado | 🔴 Alta |
| **QuickActionCard** | Botón grande con icono para quick actions en dashboard | 🟡 Media |
| **KpiCard** | Tarjeta de KPI con icono, valor, label, tendencia y color semántico | 🟡 Media |
| **StepWizard** | Wizard de pasos para formularios multi-paso con indicador de progreso | 🟡 Media |
| **FilterPanel** | Panel de filtros colapsable con subgrupos y botón "Limpiar" | 🟡 Media |
| **Timeline** | Línea de tiempo vertical/horizontal para trazabilidad y auditoría | 🟡 Media |
| **StatusTimeline** | Línea de estados: Registrado → Revisión → Aprobado → SAP | 🟡 Media |
| **EmptyState** | Componente de estado vacío con icono, mensaje y acción sugerida | 🟢 Baja |
| **LoadingSkeleton** | Skeleton loader contextual para tablas, cards y formularios | 🟢 Baja |
| **PayloadViewer** | Visor de JSON con sintaxis coloreada para payloads SAP | 🟡 Media |
| **ConfirmDialog** | Modal de confirmación estandarizado con botones primary/danger | 🟡 Media |
| **MobileQuickActions** | Botones de acción rápida en la parte superior del dashboard mobile | 🟡 Media |

### 13.2 Componentes a refactorizar

| Componente | Cambio propuesto | Prioridad |
|------------|-----------------|-----------|
| **Sidebar.tsx** | Refactorizar: submenús, secciones, colapsable, mejor active state | 🔴 Alta |
| **MobileDrawer.tsx** | Refactorizar: mostrar jerarquía completa de navegación | 🔴 Alta |
| **MobileNav.tsx** | Refactorizar: hacer contextual (cambiar según contexto del operador) | 🟡 Media |
| **Header.tsx** | Agregar breadcrumbs en desktop, mejorar diseño de top bar | 🟡 Media |
| **ReviewCenter.tsx** | Refactorizar: tabs por estado, panel de filtros colapsable | 🟡 Media |
| **ApprovalPanel.tsx** | Agregar resumen ejecutivo, vista de lote agrupado | 🟡 Media |
| **SapManagerPage.tsx** | Refactorizar: tabs de sub-secciones, dashboard SAP | 🟡 Media |
| **AuditPage.tsx** | Refactorizar: tabs por tipo, timeline visual | 🟡 Media |
| **ReportsPage.tsx** | Agregar sub-navegación por tipo de reporte | 🟢 Baja |
| **DashboardPage.tsx** | Agregar atajos contextuales por rol de usuario | 🟡 Media |
| **ProcessHubPage.tsx** | Refactorizar ruta a `/poultry` con misma estética visual | 🟡 Media |
| **ProcessStagePage.tsx** | Agregar breadcrumbs, mejor integración con sidebar | 🟡 Media |

### 13.3 Estándar de componentes UI

Mantener y reforzar el uso de los componentes base existentes:

```
components/ui/
├── Button.tsx        ← 5 variantes × 3 tamaños (estándar)
├── Badge.tsx         ← 13 variantes de estado (estándar)
├── Card.tsx          ← 3 variantes (estándar)
├── Input.tsx         ← Con label, error, icono (estándar)
├── Modal.tsx         ← Portal accesible (estándar)
├── DataTable.tsx     ← TanStack Table (estándar)
├── KpiCard.tsx       ← NUEVO
├── Breadcrumbs.tsx   ← NUEVO
├── EmptyState.tsx    ← NUEVO
├── LoadingSkeleton.tsx ← NUEVO
├── FilterPanel.tsx   ← NUEVO
├── Timeline.tsx      ← NUEVO
└── ConfirmDialog.tsx ← NUEVO
```

---

## 14. Recomendaciones de Diseño Visual

### 14.1 Layout General

```
DESKTOP (≥1024px):
┌──────┬──────────────────────────────────────────────┐
│      │  📊 Dashboard                     🌐 👤     │
│ Side │  breadcrumbs › sub › actual                 │
│ bar  │──────────────────────────────────────────────│
│ w-64 │  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│ fijo │  │ KPI      │ │ KPI      │ │ KPI      │    │
│      │  └──────────┘ └──────────┘ └──────────┘    │
│      │                                              │
│      │  ┌──────────────────────────────────────────┐│
│      │  │ Contenido principal                      ││
│      │  │ (tablas, formularios, timelines)         ││
│      │  └──────────────────────────────────────────┘│
│      │                                              │
└──────┴──────────────────────────────────────────────┘

MOBILE (<1024px):
┌──────────────────────────────────┐
│ ☰ Global Avícola        🌐 👤  │  ← Header
├──────────────────────────────────┤
│ breadcrumbs › sub › actual      │  ← Breadcrumbs
├──────────────────────────────────┤
│                                  │
│  ┌────────────────────────────┐ │
│  │ KPI  │ KPI  │ KPI         │ │
│  └────────────────────────────┘ │
│                                  │
│  ┌────────────────────────────┐ │
│  │ Contenido principal        │ │
│  └────────────────────────────┘ │
│                                  │
├──────────────────────────────────┤
│ 🏠  📝  🐔  📊  👤             │  ← Bottom nav
└──────────────────────────────────┘
```

### 14.2 Sidebar refinado

| Elemento | Estilo |
|----------|--------|
| **Fondo** | `bg-[#1E3A5F]` (mantener) |
| **Ancho** | `w-64` fijo (mantener) |
| **Separadores** | `text-[10px] font-bold text-blue-300/50 uppercase tracking-widest px-6 py-2` |
| **Item nivel 1** | `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium` |
| **Item nivel 2** | `flex items-center gap-3 pl-11 py-2 rounded-lg text-xs font-medium` |
| **Item nivel 3** | `flex items-center gap-3 pl-16 py-1.5 rounded-lg text-[11px] font-normal` |
| **Active state** | `bg-blue-600/30 text-white border-l-2 border-blue-400` |
| **Hover** | `hover:bg-blue-700/40 hover:text-white` |
| **Submenú animación** | `transition-all duration-200 ease-in-out` con max-height |
| **Chevron** | `ChevronDown` rotado 180° cuando expandido, animación `transition-transform` |

### 14.3 Breadcrumbs

```
🏠 Gestión Avícola › Reproductoras › Cría › Lote L-2026-042
```

| Elemento | Estilo |
|----------|--------|
| **Contenedor** | `flex items-center gap-1.5 text-xs font-medium px-6 py-2 bg-white border-b border-slate-200` |
| **Item** | `text-slate-500 hover:text-blue-600 transition-colors` |
| **Item activo** | `text-slate-900 font-semibold` |
| **Separador** | `ChevronRight size={14} text-slate-300` |
| **Icono home** | `Home size={14} text-slate-400` |

### 14.4 Tarjetas KPI

```
┌──────────────────────┐
│ 🥚                   │  ← Icono grande semitransparente
│                      │
│ Producción de Huevos │  ← Label
│                      │
│ 12,450               │  ← Valor grande y bold
│                      │
│ ↑ 8.3% vs ayer      │  ← Tendencia con color semántico
└──────────────────────┘
```

| Elemento | Estilo |
|----------|--------|
| **Fondo** | `bg-white rounded-xl border border-slate-200 p-4` |
| **Icono** | `absolute -top-2 -right-2 opacity-10` (decorativo) |
| **Valor** | `text-2xl font-extrabold text-slate-900` |
| **Label** | `text-xs font-medium text-slate-500` |
| **Tendencia** | `text-xs font-semibold` (verde si ↑, rojo si ↓) |
| **Hover** | `hover:shadow-md transition-shadow duration-200` |

### 14.5 Tablas

| Elemento | Estilo |
|----------|--------|
| **Header** | `bg-slate-50 text-slate-700 font-semibold text-xs uppercase tracking-wider` |
| **Row** | `border-b border-slate-100 hover:bg-blue-50/50 transition-colors` |
| **Cell** | `px-4 py-3 text-sm text-slate-600` |
| **Striped** | `even:bg-slate-50/50` |
| **Pagination** | `flex items-center gap-2 justify-center py-4` |

### 14.6 Formularios

| Elemento | Estilo |
|----------|--------|
| **Sección** | `border-b border-slate-200 pb-6 mb-6` con título en `text-sm font-bold text-slate-700 uppercase tracking-wide` |
| **Label** | `block text-sm font-medium text-slate-700 mb-1.5` |
| **Input** | `w-full h-11 px-4 rounded-lg border border-slate-300 bg-white text-sm focus:border-blue-500 focus:ring-2 focus:ring-blue-200` |
| **Error** | `text-xs text-red-600 mt-1 flex items-center gap-1` |
| **Help text** | `text-xs text-slate-400 mt-1` |
| **Botón primario** | `h-11 px-6 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700` |
| **Botón secundario** | `h-11 px-6 bg-white text-blue-600 border border-blue-600 font-semibold rounded-lg hover:bg-blue-50` |

### 14.7 Estados y Badges

| Estado | Fondo | Texto | Borde | Icono |
|--------|-------|-------|-------|-------|
| Registrado | `bg-sky-50` | `text-sky-700` | `border-sky-200` | `FileText` |
| Pendiente Revisión | `bg-amber-50` | `text-amber-700` | `border-amber-200` | `Clock` |
| En Revisión | `bg-indigo-50` | `text-indigo-700` | `border-indigo-200` | `Search` |
| Devuelto | `bg-orange-50` | `text-orange-700` | `border-orange-200` | `Undo2` |
| Corregido | `bg-teal-50` | `text-teal-700` | `border-teal-200` | `RefreshCw` |
| Aprobado | `bg-emerald-50` | `text-emerald-700` | `border-emerald-200` | `CheckCircle` |
| Rechazado | `bg-red-50` | `text-red-700` | `border-red-200` | `XCircle` |
| Cancelado | `bg-slate-50` | `text-slate-500` | `border-slate-200` | `Ban` |
| Enviado SAP | `bg-blue-50` | `text-blue-700` | `border-blue-200` | `Send` |
| Error SAP | `bg-red-50` | `text-red-700` | `border-red-200` | `AlertTriangle` |

### 14.8 Mejora de paleta de colores

Mantener la paleta existente pero refinarla con más variantes:

```css
/* Paleta actual (mantener) */
--color-primary: #1E3A5F;      /* Sidebar, headers */
--color-primary-light: #2563EB; /* Botones, links */
--color-primary-hover: #3B82F6; /* Hover states */
--color-bg: #FFFFFF;
--color-bg-secondary: #F8FAFC;
--color-bg-card: #FFFFFF;
--color-border: #E2E8F0;
--color-text: #0F172A;
--color-text-secondary: #475569;

/* Nuevos colores de acento */
--color-success: #16A34A;
--color-warning: #EAB308;
--color-danger: #DC2626;
--color-info: #2563EB;

/* Nuevos fondos de sección */
--color-section-operational: #EFF6FF;  /* Azul muy claro */
--color-section-review: #FFFBEB;        /* Ámbar muy claro */
--color-section-admin: #F8FAFC;         /* Slate muy claro */
```

---

## 15. Recomendaciones Mobile-First

### 15.1 Estructura mobile

```
┌──────────────────────────────────┐
│ Header (h-14)                    │
│ ☰ Global Avícola          🌐 👤 │
├──────────────────────────────────┤
│ Breadcrumbs (h-8, si aplica)     │
│ › Producción › Recolección       │
├──────────────────────────────────┤
│                                  │
│ Contenido principal              │
│ (scroll)                         │
│                                  │
│                                  │
├──────────────────────────────────┤
│ Bottom Nav (h-16, fijo)          │
│ 🏠  📝  🐔  📊  👤             │
└──────────────────────────────────┘
```

### 15.2 Bottom Navigation adaptativa

| Contexto | Items del bottom nav |
|----------|---------------------|
| **General** | Inicio, Registrar, Lotes, KPIs, Menú |
| **En operación** | ←Atrás, Lote actual, Nueva tarea, KPIs, ✓Listo |
| **En revisión** | ←Atrás, Pendientes, Aprobar, Rechazar, Menú |

### 15.3 Drawer mobile mejorado

El drawer debe mostrar la misma jerarquía que el sidebar desktop:

```
┌──────────────────────────┐
│ ✕ Global Avícola         │
│   María García           │
├──────────────────────────┤
│                          │
│ 📊 Dashboard             │
│                          │
│ 🐔 Gestión Avícola       │
│   ▼ Abuelas              │
│   ▼ Progenitoras         │
│   ▼ Reproductoras        │
│   ▼ Incubadora           │
│   ▼ Pollo de Engorde     │
│                          │
│ 📋 Centro de Revisión    │
│                          │
│ 🔄 Integración SAP       │
│                          │
│ 📈 Reportes              │
│                          │
│ 🛡️ Auditoría             │
│                          │
│ ⚙️ Maestros              │
│                          │
│ 👥 Usuarios y Roles      │
│                          │
├──────────────────────────┤
│ 🌐 Español  ⚙️ Perfil 🚪│
└──────────────────────────┘
```

### 15.4 Quick actions en mobile

En el dashboard mobile, mostrar una sección de "Acciones rápidas":

```
┌──────────────────────────────────┐
│ 📋 Acciones Rápidas              │
│                                  │
│ ┌────────────┐ ┌────────────┐   │
│ │ 💀         │ │ ⚖️         │   │
│ │ Mortalidad │ │ Pesaje     │   │
│ └────────────┘ └────────────┘   │
│ ┌────────────┐ ┌────────────┐   │
│ │ 🌾         │ │ 💉         │   │
│ │ Alimento   │ │ Vacuna     │   │
│ └────────────┘ └────────────┘   │
└──────────────────────────────────┘
```

### 15.5 Formularios mobile optimizados

| Principio | Implementación |
|-----------|---------------|
| Un campo por línea | Cada campo en su propia fila, ancho completo |
| Agrupación visual | Secciones con borde superior sutil y label |
| Botones grandes | Altura mínima 48px, ancho completo |
| Validación inline | Error visible debajo del campo |
| Teclado numérico | `inputmode="numeric"` para cantidades |
| Fecha nativa | `type="date"` para campos de fecha |
| Autocompletado | `autocomplete` attributes para campos comunes |

---

## 16. Recomendaciones de Web Administrativa

### 16.1 Espacio de trabajo optimizado

| Elemento | Desktop | Tablet |
|----------|---------|--------|
| **Sidebar** | `w-64` fijo, siempre visible | Colapsable (`w-16` iconos) |
| **Header** | Breadcrumbs + búsqueda + usuario | Breadcrumbs + usuario |
| **Contenido** | `max-w-7xl mx-auto px-8 py-6` | `px-6 py-4` |
| **Tablas** | Ancho completo con sticky header | Scroll horizontal si necesario |
| **Cards** | Grid 3-4 columnas | Grid 2 columnas |

### 16.2 Multi-panel layout

Para pantallas de revisión y aprobación, usar layout de dos paneles:

```
┌──────────────────────────────────────────────────────┐
│ Breadcrumbs › Revisión › Lote L-2026-042             │
├────────────────────────┬─────────────────────────────┤
│                        │                             │
│  PANEL IZQUIERDO       │  PANEL DERECHO             │
│  (60% width)           │  (40% width)               │
│                        │                             │
│  Lista de operaciones  │  Detalle de operación      │
│  del lote pendientes   │  seleccionada              │
│  de revisión           │                             │
│                        │  ┌─────────────────────┐   │
│  [✓] Operación #1      │  │ Valor registrado:    │   │
│  [ ] Operación #2      │  │ 150 aves             │   │
│  [ ] Operación #3      │  │ Valor anterior:      │   │
│                        │  │ 145 aves             │   │
│                        │  │ Diferencia: +5       │   │
│                        │  └─────────────────────┘   │
│                        │                             │
│                        │  [✓ Aprobar] [✗ Rechazar]  │
└────────────────────────┴─────────────────────────────┘
```

### 16.3 Dashboard ejecutivo

Para supervisores y aprobadores en desktop:

```
┌──────────────────────────────────────────────────────────┐
│ 📊 DASHBOARD EJECUTIVO                           📅 Hoy │
├──────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│ │ 📋 12   │ │ ✅ 8     │ │ ⏳ 3     │ │ ❌ 1     │   │
│ │Pendientes│ │Aprobados │ │En Revisión│ │Rechazados│   │
│ │         │ │ hoy      │ │          │ │          │   │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ ┌─────────────────────────┐ ┌────────────────────────┐  │
│ │ 📈 Producción última    │ │ 🔄 Estado SAP          │  │
│ │    semana               │ │                        │  │
│ │                         │ │ ┌─ Pendientes: 5 ──┐  │  │
│ │ [Gráfico Recharts]      │ │ │ Enviados: 12    │  │  │
│ │                         │ │ │ Errores: 1      │  │  │
│ └─────────────────────────┘ │ └──────────────────┘  │  │
│                             └────────────────────────┘  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Tabla: Últimas operaciones registradas                   │
│ ┌────┬──────────┬──────────┬──────────┬──────────┬────┐ │
│ │ ID │ Lote     │ Tipo     │ Fecha    │ Estado   │ ⋯ │ │
│ ├────┼──────────┼──────────┼──────────┼──────────┼────┤ │
│ │ 1  │ L-2026.. │Mortalidad│ 24/06    │ ✅ Ap.   │ ⋯ │ │
│ │ 2  │ L-2026.. │Pesaje    │ 24/06    │ 📋 Rev.  │ ⋯ │ │
│ └────┴──────────┴──────────┴──────────┴──────────┴────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 17. Matriz de Cambios Recomendados

| ID | Cambio | Tipo | Archivos afectados | Esfuerzo | Impacto | Prioridad |
|----|--------|------|--------------------|----------|---------|-----------|
| C-01 | Refactorizar Sidebar con submenús colapsables y secciones | ⚡ Estructural | `Sidebar.tsx`, `ui.store.ts` | Alto | Alto | 🔴 Inmediata |
| C-02 | Agregar Breadcrumbs component | 🎨 UI | Nuevo `Breadcrumbs.tsx`, `AppLayout.tsx` | Bajo | Alto | 🔴 Alta |
| C-03 | Crear SubNavHeader con back + breadcrumbs | 🎨 UI | Nuevo `SubNavHeader.tsx` | Bajo | Alto | 🔴 Alta |
| C-04 | Renombrar rutas /processes → /poultry | ⚡ Estructural | `App.tsx`, `Sidebar.tsx`, i18n | Medio | Alto | 🟡 Media |
| C-05 | Refactorizar MobileDrawer con jerarquía completa | 🎨 UI | `MobileDrawer.tsx` | Medio | Alto | 🔴 Alta |
| C-06 | Agregar separadores de sección en sidebar | 🎨 UI | `Sidebar.tsx` | Bajo | Medio | 🟡 Media |
| C-07 | Refactorizar ReviewCenter con tabs y filtros mejorados | 🎨 UI | `ReviewCenter.tsx` | Medio | Alto | 🟡 Media |
| C-08 | Refactorizar SapManagerPage con tabs | 🎨 UI | `SapManagerPage.tsx` | Medio | Medio | 🟡 Media |
| C-09 | Refactorizar AuditPage con tabs y timeline | 🎨 UI | `AuditPage.tsx` | Medio | Medio | 🟡 Media |
| C-10 | Agregar quick actions al Dashboard por rol | 🎨 UI | `DashboardPage.tsx` | Medio | Alto | 🟡 Media |
| C-11 | Crear componente EmptyState | 🎨 UI | Nuevo componente | Bajo | Bajo | 🟢 Baja |
| C-12 | Crear componente LoadingSkeleton | 🎨 UI | Nuevo componente | Bajo | Bajo | 🟢 Baja |
| C-13 | Crear componente KpiCard | 🎨 UI | Nuevo componente | Bajo | Medio | 🟡 Media |
| C-14 | Mejorar active state del sidebar | 🎨 UI | `Sidebar.tsx` | Bajo | Medio | 🟡 Media |
| C-15 | Agrupar maestros por categoría | ⚡ Estructural | `App.tsx`, `MastersHubPage.tsx` | Medio | Bajo | 🟢 Baja |
| C-16 | Mejorar formularios con secciones y wizard | 🎨 UI | `OperationFormPage.tsx` | Alto | Alto | 🟡 Media |
| C-17 | Refactorizar MobileNav contextual | 🎨 UI | `MobileNav.tsx` | Medio | Alto | 🟡 Media |
| C-18 | Agregar FilterPanel colapsable | 🎨 UI | Nuevo componente + refactor ReviewCenter | Medio | Alto | 🟡 Media |
| C-19 | Agregar ConfirmDialog estandarizado | 🎨 UI | Nuevo componente | Bajo | Medio | 🟡 Media |
| C-20 | Mejorar i18n para nuevas rutas y textos | 📝 Contenido | Archivos de traducción | Bajo | Alto | 🔴 Alta |

---

## 18. Priorización de Mejoras

### Fase 1 — Fundación de navegación (Semana 1)

| # | Cambio | Dependencias | Tiempo estimado |
|---|--------|-------------|-----------------|
| 1 | Refactorizar Sidebar con submenús colapsables | Ninguna | 2 días |
| 2 | Agregar secciones y separadores al sidebar | C-01 | 0.5 días |
| 3 | Refactorizar MobileDrawer con jerarquía | C-01 | 1 día |
| 4 | Crear Breadcrumbs component | Ninguna | 0.5 días |
| 5 | Crear SubNavHeader | C-04 | 0.5 días |
| 6 | Mejorar active state del sidebar | C-01 | 0.5 días |
| 7 | Agregar i18n para nuevas rutas y textos | C-01..C-06 | 1 día |

**Total estimado Fase 1: 6 días**

### Fase 2 — Mejora de pantallas operativas (Semana 2)

| # | Cambio | Dependencias | Tiempo estimado |
|---|--------|-------------|-----------------|
| 8 | Refactorizar ReviewCenter con tabs y filtros | C-04 | 2 días |
| 9 | Agregar quick actions al Dashboard | C-04 | 1.5 días |
| 10 | Crear KpiCard component | Ninguna | 0.5 días |
| 11 | Mejorar formularios con secciones | C-16 | 2 días |
| 12 | Crear ConfirmDialog | Ninguna | 0.5 días |
| 13 | Refactorizar MobileNav contextual | C-04 | 1 día |

**Total estimado Fase 2: 7.5 días**

### Fase 3 — Pantallas administrativas y SAP (Semana 3)

| # | Cambio | Dependencias | Tiempo estimado |
|---|--------|-------------|-----------------|
| 14 | Refactorizar SapManagerPage con tabs | C-04 | 1.5 días |
| 15 | Refactorizar AuditPage con tabs | C-04 | 1.5 días |
| 16 | Crear FilterPanel component | Ninguna | 1 día |
| 17 | Agrupar maestros por categoría | C-04 | 1 día |
| 18 | Renombrar rutas /processes → /poultry | C-04 | 1 día |

**Total estimado Fase 3: 6 días**

### Fase 4 — Pulido y calidad (Semana 4)

| # | Cambio | Dependencias | Tiempo estimado |
|---|--------|-------------|-----------------|
| 19 | Crear EmptyState component | Ninguna | 0.5 días |
| 20 | Crear LoadingSkeleton | Ninguna | 0.5 días |
| 21 | Pruebas visuales cross-browser | Todas | 2 días |
| 22 | Pruebas de navegación | Todas | 1 día |
| 23 | Pruebas mobile | Todas | 1 día |
| 24 | Ajustes finales de i18n | Todas | 1 día |

**Total estimado Fase 4: 6 días**

**Tiempo total estimado: ~25 días hábiles (5 semanas)**

---

## 19. Riesgos de Tocar Lógica Funcional

| Riesgo | Descripción | Mitigación |
|--------|-------------|------------|
| **🔴 Ruptura de rutas existentes** | Cambiar `/processes` a `/poultry` puede romper bookmarks y enlaces compartidos | Implementar redirecciones 301 con `<Navigate>` de React Router |
| **🟡 Sidebar refactor afecta navegación** | Si el sidebar deja de funcionar, el usuario no puede navegar | Pruebas unitarias del Sidebar, feature flag para nuevo sidebar |
| **🟡 i18n incompleto** | Nuevos textos del menú pueden quedar sin traducción al inglés | Agregar entradas faltantes en ambos archivos de traducción antes de desplegar |
| **🟢 Estado del drawer en mobile** | Drawer con muchos items puede ser lento en dispositivos low-end | Virtualización si es necesario, lazy loading de contenido |
| **🟢 Submenús colapsables y accesibilidad** | Submenús deben ser accesibles por teclado y screen reader | ARIA attributes (`aria-expanded`, `aria-controls`), keyboard navigation |
| **🔴 No tocar lógica de operaciones** | No modificar flujo de creación de operaciones, reglas de negocio, ni estados | Audit: solo cambios de UI/presentación, no de lógica de negocio |
| **🔴 No romper WebOnlyRoute** | Respetar que usuarios mobile no accedan a rutas web-only | Mantener `WebOnlyRoute` wrapper en rutas administrativas |

---

## 20. Criterios de Aceptación

La mejora será aceptable solo si se cumplen TODOS los siguientes criterios:

### 20.1 Navegación

- [ ] **NAV-01:** El menú principal tiene secciones claras (Operativo, Revisión, Integración, Reportes, Administración)
- [ ] **NAV-02:** "Gestión Avícola" agrupa correctamente las 6 fases productivas con submenús
- [ ] **NAV-03:** Cada fase del menú muestra sus subfases (Cría, Producción, Incubación, etc.)
- [ ] **NAV-04:** Los submenús son colapsables y recuerdan su estado expandido/colapsado
- [ ] **NAV-05:** Los breadcrumbs son consistentes en todas las páginas internas
- [ ] **NAV-06:** El operador mobile puede llegar a cualquier operación en máximo 3 taps
- [ ] **NAV-07:** "Processes" y "Operations" no aparecen como menús separados y confusos
- [ ] **NAV-08:** Las rutas existentes tienen redirección a las nuevas rutas

### 20.2 Experiencia por usuario

- [ ] **EXP-01:** El operador mobile tiene quick actions y acceso rápido a sus lotes
- [ ] **EXP-02:** El supervisor web puede revisar y aprobar sin perder contexto
- [ ] **EXP-03:** El aprobador ve un resumen ejecutivo antes de aprobar/rechazar
- [ ] **EXP-04:** El usuario SAP ve claramente qué está pendiente, aprobado, consolidado o enviado
- [ ] **EXP-05:** El administrador tiene maestros agrupados por categoría lógica

### 20.3 Diseño visual

- [ ] **VIS-01:** El diseño se ve moderno, limpio y profesional
- [ ] **VIS-02:** La interfaz conserva blanco como base principal y azul corporativo como color primario
- [ ] **VIS-03:** Los estados de color son consistentes (verde=aprobado, amarillo=pendiente, rojo=rechazado, azul=en proceso)
- [ ] **VIS-04:** Los active states del sidebar son claramente visibles
- [ ] **VIS-05:** Las tarjetas KPI tienen un diseño consistente
- [ ] **VIS-06:** Los breadcrumbs son legibles y consistentes

### 20.4 Mobile

- [ ] **MOB-01:** El bottom nav se adapta al contexto del usuario
- [ ] **MOB-02:** El drawer mobile muestra la jerarquía completa de navegación
- [ ] **MOB-03:** Los touch targets miden mínimo 44×44px
- [ ] **MOB-04:** Los formularios tienen secciones colapsables en mobile
- [ ] **MOB-05:** Las validaciones son inline y visibles

### 20.5 Técnicos

- [ ] **TEC-01:** No se rompe la lógica avícola existente
- [ ] **TEC-02:** No se rompen rutas ni operaciones existentes (o se documenta migración)
- [ ] **TEC-03:** No se elimina funcionalidad existente
- [ ] **TEC-04:** Todo cambio de UI respeta React + Vite + TypeScript + TailwindCSS
- [ ] **TEC-05:** Todo texto visible mantiene soporte español/inglés (i18n)
- [ ] **TEC-06:** No se copia Atenea — solo se toma como referencia de navegación empresarial
- [ ] **TEC-07:** Los componentes UI reutilizables se mantienen y extienden
- [ ] **TEC-08:** El diseño es responsive en los 7 breakpoints especificados

---

## Apéndice A: Referencias

| Documento | Descripción |
|-----------|-------------|
| `docs/11-ui-ux-design-system.md` | Sistema de diseño actual |
| `specs/global-avicola/spec.md` | Spec funcional completo |
| `GLOBAL_AVICOLA_AUDIT_REPORT.md` | Auditoría técnica integral |
| `frontend/src/data/processCatalog.ts` | Catálogo de procesos avícolas |
| `frontend/src/App.tsx` | Configuración de rutas |
| `frontend/src/components/layout/Sidebar.tsx` | Sidebar actual |
| `frontend/src/components/layout/AppLayout.tsx` | Layout principal |
| Atenea frontend (`/home/maria/Proyectos/atenea-front`) | Referencia de navegación |

## Apéndice B: Glosario

| Término | Definición |
|---------|-----------|
| **Fase productiva** | Etapa del ciclo avícola (Cría, Producción, Incubación, Engorde) |
| **Subfase** | División de una fase (ej: Cría dentro de Reproductoras) |
| **Operación** | Acción concreta dentro de una subfase (ej: Registrar mortalidad) |
| **Event type** | Código interno de operación (ej: `mortality_recording`) |
| **Stage** | Término actual en el código para fase productiva |
| **Breadcrumb** | Migas de pan — navegación jerárquica |
| **Quick action** | Acceso directo a una operación frecuente |
| **Sidebar** | Menú lateral de navegación principal |
| **Bottom nav** | Barra de navegación inferior en mobile |
| **Drawer** | Panel deslizable de navegación en mobile |

---

> **Fin del documento — GLOBAL AVICOLA UI UX NAVIGATION AUDIT**
>
> *Próximo paso: Revisar y ejecutar `GLOBAL_AVICOLA_UI_IMPLEMENTATION_PLAN.md` para la implementación faseada de las mejoras propuestas.*

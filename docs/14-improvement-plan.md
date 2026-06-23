# Plan de Mejoras — Global Avícola

> **Auditoría Integral:** Spec vs Implementación Actual
> **Fecha:** 2026-06-23
> **Versión:** 1.0.0
> **Objetivo:** Alinear la implementación React actual con el Spec, el flujo lógico de la app Flutter previa, y las bases de diseño documentadas.

---

## 1. RESUMEN EJECUTIVO

La implementación actual tiene un **esqueleto backend sólido** (151 endpoints, 42 tablas, 7 fases) pero el **frontend React requiere reorganización profunda** para cumplir con:

1. El **orden lógico de carga operativa por etapa productiva** (Progenitoras → Reproductoras Cría → Reproductoras Producción → Incubación → Engorde)
2. Las **bases de diseño de la app Flutter previa** (flujo secuencial por lote, captura guiada)
3. El **Spec formal** (mobile-first real, RBAC granular, diseño corporativo)
4. La **separación real Mobile vs Web** (operador en campo vs supervisor en escritorio)

---

## 2. ORDEN LÓGICO DE CARGA OPERATIVA (Flujo Canónico)

Basado en el Spec (secciones 4.4–4.8), el diagrama de procesos documentado, y la app Flutter previa, el orden lógico de operaciones por etapa es:

### ETAPA 0: Fundación y Referencias
```
1. Importar referencias SAP (órdenes, materiales, centros)
2. Configurar maestros (granjas, galpones, incubadoras, líneas genéticas)
3. Configurar pasos de aprobación por empresa (1/2/3 niveles)
4. Gestionar usuarios y roles por empresa
```

### ETAPA 1: Progenitoras / Abuelas
```
1. Registrar plan de importación (docs sanitarios, aduana)
2. Inspección de granja pre-recepción
3. Recepción de aves (cantidad, sexo, peso, línea genética)
4. Distribución de aves a galpones
5. [CICLO DIARIO/SEMANAL]:
   - Registro de alimento
   - Registro de pesaje
   - Registro de mortalidad
   - Registro de vacunación
   - Registro de medicación
   - Inspección de granja
6. Salida de aves / Transición a siguiente fase
```

### ETAPA 2: Reproductoras — Fase Cría
```
1. Recepción de aves (desde progenitoras o externo)
2. Distribución a galpones
3. [CICLO DIARIO/SEMANAL]:
   - Registro de alimento
   - Registro de pesaje (semanal)
   - Registro de mortalidad (diario)
   - Registro de vacunación
   - Registro de medicación
   - Inspección de granja
4. Transferencia a fase producción (cierre/apertura de fase)
```

### ETAPA 3: Reproductoras — Fase Producción
```
1. Recepción desde cría (población inicial automática)
2. [CICLO DIARIO/SEMANAL]:
   - Recolección de huevos (fértiles, sucios, rotos, infértiles)
   - Clasificación de huevos
   - Despacho de huevos a incubadora
   - Registro de alimento
   - Registro de mortalidad
   - Registro de vacunación
3. Salida de aves (descarte/venta)
4. KPIs: % postura, huevos/ave alojada, fertilidad
```

### ETAPA 4: Incubación
```
1. Recepción de huevos fértiles (desde producción)
2. Carga de incubadora (temperatura, humedad, CO2, volteo)
3. Ovoscopia (desechar infértiles/muertos)
4. Transferencia a nacedora
5. Nacimiento (pollitos viables, descartados, vacunación)
6. Despacho de pollitos a engorde
7. KPIs: % eclosión, % nacimiento, rendimiento
```

### ETAPA 5: Pollo de Engorde
```
1. Recepción de pollitos (desde incubación)
2. [CICLO DIARIO/SEMANAL]:
   - Registro de alimento
   - Registro de pesaje
   - Registro de mortalidad
   - Registro de vacunación
   - Registro de medicación
   - Inspección de granja
3. Cierre de lote y despacho a planta de beneficio
4. KPIs: ganancia diaria, conversión alimenticia, viabilidad, uniformidad
```

### GOBERNANZA TRANSVERSAL (aplica a cada registro de cada etapa)
```
Registro → Revisión → Corrección (si aplica) → Aprobación → Consolidación → Envío a SAP
```

---

## 3. GAPS IDENTIFICADOS — MATRIZ DE MEJORAS

### 3.1 GAPS CRÍTICOS (Bloquean operación real)

| ID | Gap | Ubicación Actual | Severidad | Corrección Requerida |
|----|-----|-----------------|-----------|---------------------|
| **G-01** | No hay navegación por Lote → Etapa → Operación | `OperationListPage.tsx` es una lista plana de eventos sin contexto de lote ni etapa | 🔴 Crítico | Implementar vista jerárquica: Seleccionar Lote → Ver etapa actual → Operaciones disponibles para esa etapa |
| **G-02** | No hay panel de operaciones por etapa productiva | `OperationFormPage.tsx` muestra 24 tipos de evento en un solo dropdown, sin filtrar por etapa | 🔴 Crítico | Crear 5 paneles de operaciones filtrados por etapa (solo mostrar operaciones válidas para la fase actual del lote) |
| **G-03** | RBAC no implementado en frontend | `App.tsx` solo verifica `isAuthenticated`, no verifica roles ni permisos | 🔴 Crítico | Implementar `ProtectedRoute` con verificación de rol/permiso; sidebar dinámico por rol |
| **G-04** | No hay vista de detalle de lote con sus operaciones | No existe página `/lots/:id` | 🔴 Crítico | Crear `LotDetailPage.tsx` con timeline de fases + operaciones agrupadas + KPIs |
| **G-05** | Faltan 6 reglas de negocio (BR-05 a BR-16) | `validators.py` solo tiene BR-01 a BR-04 | 🔴 Crítico | Implementar validadores para cierre de lote, fechas, segregación, no-edición-post-SAP |

### 3.2 GAPS DE UX/DISEÑO (Experiencia de usuario)

| ID | Gap | Ubicación Actual | Severidad | Corrección Requerida |
|----|-----|-----------------|-----------|---------------------|
| **G-06** | CSS contaminado con template Vite (púrpura, dark mode) | `index.css` tiene variables `--accent: #aa3bff` y `prefers-color-scheme: dark` | 🟡 Alto | Reemplazar `index.css` con solo Tailwind + variables corporativas blanco/azul |
| **G-07** | Navegación móvil incompleta | `MobileNav.tsx` solo tiene 5 ítems (falta Aprobaciones, SAP, Auditoría, Usuarios) | 🟡 Alto | Completar MobileNav con todos los ítems del sidebar, o contextual por rol |
| **G-08** | Iconos emoji en lugar de iconos profesionales | Todas las páginas usan emojis (🐔📦🚛💀🌾) | 🟡 Alto | Migrar a librería de iconos (Heroicons/lucide-react) con diseño corporativo |
| **G-09** | Dashboard no muestra KPIs por etapa/lote | `DashboardPage.tsx` muestra datos planos sin segmentación por etapa | 🟡 Alto | Agregar tarjetas de KPIs por etapa productiva activa |
| **G-10** | Formulario de operación no guía al operador | `OperationFormPage.tsx` es un formulario genérico con campos condicionales | 🟡 Alto | Crear formularios contextuales por tipo de operación con ayuda inline y validaciones específicas |

### 3.3 GAPS DE FLUJO DE APROBACIÓN

| ID | Gap | Ubicación Actual | Severidad | Corrección Requerida |
|----|-----|-----------------|-----------|---------------------|
| **G-11** | No hay vista de "Mi Bandeja" por rol | `ReviewCenter.tsx` muestra todos los pendientes sin filtrar por responsable | 🟡 Alto | Agregar filtro "Asignados a mí" / "Mi bandeja" según rol |
| **G-12** | No hay segregación visual operador vs revisor | Mismo layout para todos los roles | 🟡 Alto | Diferenciar layout móvil (operador: carga rápida) vs web (supervisor: revisión detallada) |
| **G-13** | Corrección solo permite corregir `observations` | `CorrectionForm.tsx` campo fijo | 🟡 Alto | Permitir corregir cualquier campo del evento original con side-by-side comparison |

### 3.4 GAPS DE GESTIÓN DE USUARIOS

| ID | Gap | Ubicación Actual | Severidad | Corrección Requerida |
|----|-----|-----------------|-----------|---------------------|
| **G-14** | Página de usuarios es solo lectura | `UsersPage.tsx` no tiene crear/editar/eliminar | 🟡 Alto | Implementar CRUD completo de usuarios con asignación de roles y empresas |
| **G-15** | No hay página de gestión de roles/permisos | Solo existe `UsersPage.tsx` con lista de roles | 🟡 Alto | Crear `RoleManagement.tsx` con matriz de permisos por módulo/acción |
| **G-16** | No hay página de perfil de usuario | No existe | 🟡 Medio | Crear `ProfilePage.tsx` (cambiar contraseña, datos personales) |
| **G-17** | No hay configuración por empresa | No existe | 🟡 Medio | Crear `CompanySettings.tsx` (niveles de aprobación, logo, datos fiscales) |

### 3.5 GAPS DE RUTAS Y NAVEGACIÓN

| ID | Gap | Severidad | Corrección Requerida |
|----|-----|-----------|---------------------|
| **G-18** | `/operations/:id` no existe (detalle de evento) | 🟡 Alto | Crear ruta y página de detalle |
| **G-19** | `/lots/:id` no existe (detalle de lote) | 🔴 Crítico | Crear ruta y `LotDetailPage` |
| **G-20** | `/reports/lot/:id` y `/reports/sap` sin ruta | 🟡 Alto | Agregar rutas para reportes específicos |
| **G-21** | `/lots` (lista de lotes) sin página dedicada | 🟡 Alto | Crear `LotListPage.tsx` con filtros por etapa, granja, estado |

---

## 4. PLAN DE CORRECCIÓN (FASES)

### FASE 8A: Limpieza de Diseño Base (1-2 días)
- **G-06**: Reemplazar `index.css` con diseño corporativo limpio
- **G-08**: Migrar emojis a iconos SVG profesionales (lucide-react)
- Actualizar `tailwind.config.ts` con paleta corporativa verificada

### FASE 8B: Navegación por Lote y Etapa (3-4 días)
- **G-01**: Vista jerárquica Lote → Etapa → Operaciones
- **G-02**: Paneles de operaciones filtrados por etapa productiva
- **G-19**: `LotDetailPage.tsx` con timeline de fases + KPIs
- **G-21**: `LotListPage.tsx` con filtros por etapa/estado

### FASE 8C: RBAC y Gestión de Usuarios (2-3 días)
- **G-03**: `ProtectedRoute` con verificación de permisos
- **G-14**: CRUD completo de usuarios
- **G-15**: `RoleManagement.tsx` con matriz de permisos
- **G-16**: `ProfilePage.tsx`
- **G-17**: `CompanySettings.tsx`

### FASE 8D: Perfeccionamiento de Flujo Operativo (3-4 días)
- **G-05**: Implementar BR-05 a BR-16 en backend
- **G-10**: Formularios contextuales por tipo de operación
- **G-11**: "Mi Bandeja" por rol
- **G-12**: Layout diferenciado móvil vs web
- **G-13**: Corrección multi-campo con side-by-side

### FASE 8E: Reportes, Rutas y Pulido (2-3 días)
- **G-07**: Completar MobileNav
- **G-09**: Dashboard con KPIs por etapa
- **G-18**: Ruta `/operations/:id`
- **G-20**: Rutas de reportes faltantes

---

## 5. ARQUITECTURA DE PÁGINAS PROPUESTA (POST-CORRECCIÓN)

### Vista Mobile (Operador de Campo)

```
Bottom Nav: [🏠 Home] [📋 Mis Lotes] [➕ Registrar] [📊 KPIs] [👤 Perfil]

Flujo de carga:
1. Home → Dashboard con accesos rápidos por etapa
2. Mis Lotes → Lista de lotes asignados → Seleccionar lote
3. Dentro del lote → Ver etapa actual → Operaciones disponibles
4. Registrar → Formulario contextual según etapa del lote
5. KPIs → Indicadores del lote activo
6. Perfil → Datos personales, cambiar contraseña
```

### Vista Web (Supervisor/Admin)

```
Sidebar:
├── 📊 Dashboard
├── 📦 Lotes (lista + detalle)
├── 📝 Operaciones (registro rápido)
├── 🔍 Revisión (bandeja de revisión)
├── ✅ Aprobaciones (panel de aprobación)
├── 📈 Reportes
├── 🔐 Auditoría
├── 🔄 SAP
├── 📋 Maestros
├── 👥 Usuarios
└── ⚙️ Configuración
```

---

## 6. MÉTRICAS DE ÉXITO POST-CORRECCIÓN

- [ ] Operador puede completar un registro en < 60s en móvil
- [ ] Cada etapa muestra SOLO las operaciones válidas para esa fase
- [ ] RBAC aplicado: Operador no ve panel de aprobación, Supervisor no ve configuración
- [ ] 100% de iconos corporativos (0 emojis)
- [ ] 16/16 reglas de negocio implementadas y validadas
- [ ] CRUD de usuarios funcional con asignación de roles
- [ ] Dashboard con KPIs segmentados por etapa productiva activa
- [ ] CSS 100% corporativo (blanco/azul, sin púrpura ni dark mode)

---

## 7. NOTAS SOBRE EL SPEC ORIGINAL

Este documento **no modifica el spec**. Las correcciones propuestas:
- Están alineadas con las secciones 4.4–4.12 del spec (dominios funcionales)
- Respetan los principios 1-8 (SAP maestro, auditoría, mobile-first, etc.)
- Siguen las reglas de negocio BR-01 a BR-16
- Cumplen los requisitos UI/UX de la sección 6

Cualquier cambio que se implemente debe ser registrado como una actualización al plan (`plan.md`) y las tareas (`tasks.md`) siguiendo la metodología Spec-Driven Development.

---

# PROMPT: Arquitectura de navegación — Global Avícola

> Construido junto con el Product Designer y Analista Funcional Avícola.
> Basado en: spec, auditorías v1/v2/v3, UI/UX audit, y validación visual en producción.

---

## 1. Principios de navegación (confirmados)

1. **Navegando procesos → se llega a operaciones.** No hay un menú separado "Operations". Todo el flujo es: Menú → Proceso → Fase → Operación.
2. **Sidebar izquierdo = Web.** Usuarios administrativos (supervisor, aprobador, admin, SAP) usan el sidebar completo con todas las secciones.
3. **Proceso Hub = Entry point visual.** La página `/poultry` muestra 6 tarjetas (una por fase productiva). Desde ahí se navega a las operaciones.
4. **Mobile ≠ Web.** Mobile usa bottom nav simplificado + drawer con jerarquía. El Hub de procesos sirve también para mobile.
5. **Todo backend ya está construido y auditado.** No se toca backend, no se tocan reglas de negocio, no se toca `processCatalog.ts`.

---

## 2. Los 4 macro procesos (con sus fases)

| Macro proceso | Fases | BirdType | Stage keys |
|--------------|-------|----------|------------|
| **Progenitoras** (Grandparent) | Cría, Producción | `grandparent` | `grandparent_rearing`, `grandparent_production` |
| **Reproductoras** (Breeder) | Cría, Producción | `breeder` | `breeder_rearing`, `breeder_production` |
| **Incubadora** (Hatchery) | Incubación (única) | `hatchery` | `hatchery` |
| **Pollo de Engorde** (Broiler) | Engorde (única) | `broiler` | `broiler` |

### 2.1 Progenitoras — Cría (`grandparent_rearing`)

| Operación | Descripción |
|-----------|-------------|
| `grandparent_import` | Registrar importación y llegada de aves abuelas |
| `farm_inspection` | Inspeccionar la granja antes de recibir las aves |
| `bird_reception` | Recepcionar las aves y registrar cantidades |
| `bird_distribution` | Distribuir las aves a los galpones |
| `feed_registration` | Registrar consumo de alimento |
| `weight_recording` | Registrar pesaje semanal del lote |
| `vaccination` | Aplicar y registrar vacunas |
| `medication` | Aplicar y registrar medicación |
| `mortality_recording` | Registrar mortalidad diaria |
| `cull_recording` | Registrar descarte de aves |
| `bird_exit` | Trasladar el lote a la etapa de producción |

### 2.2 Progenitoras — Producción (`grandparent_production`)

| Operación | Descripción |
|-----------|-------------|
| `farm_inspection` | Inspeccionar condiciones de la granja |
| `feed_registration` | Registrar consumo de alimento |
| `weight_recording` | Registrar pesaje del lote |
| `vaccination` | Aplicar y registrar vacunas |
| `medication` | Aplicar y registrar medicación |
| `mortality_recording` | Registrar mortalidad diaria |
| `cull_recording` | Registrar descarte de aves |
| `egg_collection` | Recolectar los huevos producidos |
| `egg_classification` | Clasificar los huevos por tipo y calidad |
| `egg_dispatch` | Despachar los huevos a su destino |
| `bird_exit` | Registrar salida o cierre del lote |

### 2.3 Reproductoras — Cría (`breeder_rearing`)

| Operación | Descripción |
|-----------|-------------|
| `farm_inspection` | Inspeccionar la granja antes de recibir las pollitas |
| `bird_reception` | Recepcionar las pollitas y registrar cantidades |
| `bird_distribution` | Distribuir las pollitas a los galpones |
| `feed_registration` | Registrar consumo de alimento |
| `weight_recording` | Registrar pesaje semanal |
| `vaccination` | Aplicar y registrar vacunas |
| `medication` | Aplicar y registrar medicación |
| `mortality_recording` | Registrar mortalidad diaria |
| `cull_recording` | Registrar descarte de aves |
| `bird_exit` | Trasladar el lote a la etapa de producción |

### 2.4 Reproductoras — Producción (`breeder_production`)

| Operación | Descripción |
|-----------|-------------|
| `farm_inspection` | Inspeccionar condiciones de la granja |
| `feed_registration` | Registrar consumo de alimento |
| `weight_recording` | Registrar pesaje del lote |
| `vaccination` | Aplicar y registrar vacunas |
| `medication` | Aplicar y registrar medicación |
| `mortality_recording` | Registrar mortalidad diaria |
| `cull_recording` | Registrar descarte de aves |
| `egg_collection` | Recolectar el huevo fértil diario |
| `egg_classification` | Clasificar los huevos por tipo y calidad |
| `egg_dispatch` | Despachar el huevo fértil a la incubadora |
| `bird_exit` | Registrar salida o cierre del lote |

### 2.5 Incubadora (`hatchery`)

| Operación | Descripción |
|-----------|-------------|
| `hatchery_inspection` | Inspeccionar la incubadora antes de operar |
| `egg_reception_hatchery` | Recepcionar los huevos que llegan a la planta |
| `egg_classification` | Clasificar los huevos aptos para incubar |
| `incubation_load` | Cargar los huevos a las máquinas de incubación |
| `ovoscopy` | Realizar ovoscopía para verificar fertilidad |
| `transfer_to_hatcher` | Transferir los huevos a la nacedora |
| `birth_registration` | Registrar el nacimiento de los pollitos |
| `chick_dispatch` | Despachar los pollitos nacidos |

### 2.6 Pollo de Engorde (`broiler`)

| Operación | Descripción |
|-----------|-------------|
| `farm_inspection` | Inspeccionar la granja antes de recibir los pollitos |
| `bird_reception` | Recepcionar los pollitos y registrar cantidades |
| `bird_distribution` | Distribuir los pollitos a los galpones |
| `feed_registration` | Registrar consumo de alimento |
| `weight_recording` | Registrar pesaje del lote |
| `vaccination` | Aplicar y registrar vacunas |
| `medication` | Aplicar y registrar medicación |
| `mortality_recording` | Registrar mortalidad diaria |
| `cull_recording` | Registrar descarte de aves |
| `bird_exit` | Registrar salida de aves a planta |
| `lot_closure` | Cerrar el lote al finalizar el ciclo |

---

## 3. Arquitectura de navegación actual (implementada)

### 3.1 Sidebar izquierdo — Web (`>1024px`)

```
📊 Dashboard
── OPERATIVO ──
🐔 Gestión Avícola (colapsable)
  ▼ ✈️ Progenitoras (colapsable)
       🌱 Cría           → /poultry/grandparent/rearing
       🥚 Producción     → /poultry/grandparent/production
  ▼ 🪶 Reproductoras (colapsable)
       🌱 Cría           → /poultry/breeder/rearing
       🥚 Producción     → /poultry/breeder/production
  🔥 Incubadora          → /poultry/hatchery
  🍗 Pollo de Engorde    → /poultry/broiler
── REVISIÓN ──
🔍 Centro de Revisión    → /review
✅ Aprobaciones          → /approvals
── INTEGRACIÓN ──
🔄 Integración SAP       → /sap
── REPORTES ──
📈 Reportes              → /reports
── ADMINISTRACIÓN ──
🛡️ Auditoría             → /audit
🗄️ Maestros              → /masters
👥 Usuarios y Roles      → /users
```

### 3.2 Proceso Hub — Entry point visual (`/poultry`)

Mosaico de **6 tarjetas** con gradiente, icono, nombre, descripción, chips de operaciones y contador de pasos.

```
┌────────────────────────────────────────────────────────┐
│  🏠 Centro de Operaciones                              │
│  Elige un Proceso                                      │
│  6 Procesos · 62 Operaciones                          │
├────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│ │1️⃣       │ │2️⃣       │ │3️⃣       │               │
│ │Progen.   │ │Progen.   │ │Reprod.   │               │
│ │— Cría    │ │— Producc │ │— Cría    │               │
│ │11 pasos  │ │11 pasos  │ │10 pasos  │               │
│ └──────────┘ └──────────┘ └──────────┘               │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│ │4️⃣       │ │5️⃣       │ │6️⃣       │               │
│ │Reprod.   │ │Incubadora│ │Pollo     │               │
│ │— Producc │ │9 pasos   │ │Engorde   │               │
│ │          │ │          │ │12 pasos  │               │
│ └──────────┘ └──────────┘ └──────────┘               │
└────────────────────────────────────────────────────────┘
```

### 3.3 Mobile — Bottom nav + Drawer

**Bottom nav** (5 items contextuales):
```
🏠 Inicio | 📝 Registrar | 🐔 Lotes | 📊 KPIs | ☰ Menú
```

**Drawer** (misma jerarquía que sidebar, abre con ☰):
Mismas secciones y submenús que el sidebar desktop.

### 3.4 Breadcrumbs — Siempre visibles en páginas internas

```
🏠 Gestión Avícola › Reproductoras › Cría › Lote L-2026-042
```

---

## 4. Lo que NO se toca (restricciones firmes)

| Área | Restricción |
|------|-------------|
| **Backend** | ❌ No se modifica nada |
| **processCatalog.ts** | ❌ No se modifican stages, event types, colores, íconos, flujos |
| **Reglas de negocio** | ❌ BR-01 a BR-16 intactas |
| **Rutas existentes** | ❌ No se eliminan (solo se ocultan del menú si es necesario) |
| **navigationConfig.ts** | ❌ Ya refleja la estructura correcta |
| **Operaciones por fase** | ❌ Ya definidas en `STAGE_OPERATIONS` — no cambiar |

---

## 5. Lo que SÍ se puede trabajar (frontend/visual)

| Área | Posible mejora |
|------|---------------|
| **Diseño visual del Hub** | Mejorar tarjetas, animaciones, transiciones |
| **Header de etapa** | Reforzar visualmente "Cría" vs "Producción" |
| **Selectores de lote** | Mejorar UX del filtro por fase |
| **Responsive total** | ✅ Obligatorio: la app debe verse perfecta en cualquier dispositivo |
| **Dark mode** | Completar en componentes faltantes |
| **i18n** | Verificar cobertura de textos |
| **Tests** | Seguir aumentando cobertura |
| **Animaciones** | Transiciones suaves entre páginas |

---

## 6. Responsive — 100% en todos los dispositivos (REQUISITO)

La aplicación debe verse y funcionar perfectamente en cualquier pantalla sin importar el dispositivo, navegador o sistema operativo.

### 6.1 Viewports obligatorios

| Categoría | Viewport | Dispositivo ejemplo |
|-----------|----------|-------------------|
| 📱 Teléfono pequeño | 360×640 → 375×667 | Galaxy S8, iPhone SE |
| 📱 Teléfono estándar | 390×844 → 412×915 | iPhone 14, Pixel 7 |
| 📱 Tablet | 768×1024 → 820×1180 | iPad, Galaxy Tab |
| 💻 Notebook | 1024×768 → 1280×800 | MacBook Air, Dell XPS |
| 🖥️ Desktop | 1366×768 → 1440×900 | Monitor estándar |
| 🖥️ Desktop grande | 1536×864 → 1920×1080 | Monitor Full HD+ |

### 6.2 Qué debe funcionar en cada viewport

| Funcionalidad | 📱 Mobile | 📱 Tablet | 💻 Desktop |
|--------------|:---------:|:---------:|:----------:|
| Sidebar completo | ❌ Drawer | ⚠️ Colapsable | ✅ Fijo |
| Bottom nav | ✅ 5 items | ✅ | ❌ |
| Breadcrumbs | ✅ Scroll horizontal | ✅ | ✅ |
| Proceso Hub (6 cards) | ✅ 1 columna | ✅ 2 columnas | ✅ 3 columnas |
| Tablas | ✅ Cards | ✅ Mixto | ✅ Tabla |
| Formularios | ✅ 1 columna | ✅ 1 columna | ✅ 1-2 columnas |
| FilterPanel | ✅ Colapsable | ✅ Colapsable | ✅ Expandido |
| Modal/Dialog | ✅ Full width | ✅ Centrado | ✅ Centrado |
| Botones | ✅ touch ≥44px | ✅ touch ≥44px | ✅ mouse |

### 6.3 Breakpoints (TailwindCSS)

```css
/* Base: mobile first (< 640px) */
sm: 640px   → tablet pequeño / mobile landscape
md: 768px   → tablet vertical
lg: 1024px  → desktop compacto / tablet horizontal
xl: 1280px  → desktop estándar
2xl: 1536px → desktop grande
```

### 6.4 Reglas responsive

1. **Mobile-first:** Todo se diseña primero para 360px, luego se expande con `sm:`, `md:`, `lg:`
2. **Sin overflow horizontal:** `scrollWidth ≤ clientWidth` en todos los viewports
3. **Touch targets:** Mínimo 44×44px en mobile, 36×36px en desktop
4. **Safe areas:** Respetar notch y rounded corners en iOS (`safe-area-bottom`)
5. **Sin errores de consola:** En ningún viewport ni navegador
6. **Dark mode:** Debe funcionar en todos los viewports

---

## 6. Resumen del flujo completo

```
USUARIO WEB (sidebar):
  Sidebar → Gestión Avícola → Progenitoras → Cría
    → /poultry/grandparent/rearing
      → Seleccionar lote
        → Elegir operación (Mortalidad, Pesaje, etc.)
          → /operations/new?type=mortality_recording&lot_id=123
            → Formulario → Guardar

USUARIO MOBILE (bottom nav):
  Inicio → Quick action "Registrar"
    → Seleccionar proceso del Hub
      → Seleccionar fase
        → Seleccionar lote
          → Elegir operación
            → Formulario → Guardar

SUPERVISOR (web):
  Sidebar → Centro de Revisión
    → Pendientes / En Revisión / Devueltos
      → Revisar → Corregir / Aprobar / Devolver

APROBADOR (web):
  Sidebar → Aprobaciones
    → Pendientes de aprobación
      → Aprobar / Rechazar (con motivo)

USUARIO SAP (web):
  Sidebar → Integración SAP
    → Documentos pendientes / Enviados / Errores
      → Ver payload → Enviar a SAP / Reintentar
```

---

*Documento de referencia para continuar el desarrollo frontend de Global Avícola.*
*Próximo paso: definir en qué área trabajar a continuación.*

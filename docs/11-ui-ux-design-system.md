# Sistema de Diseño UI/UX — Global Avícola

> **Documento:** 11-ui-ux-design-system.md
> **Versión:** 1.0.0
> **Fecha:** 2026-06-22

---

## 1. IDENTIDAD VISUAL

Global Avícola debe proyectar:
- **Solidez empresarial** — confianza, estabilidad
- **Control operativo** — orden, precisión
- **Tecnología** — modernidad, eficiencia
- **Integración SAP** — seriedad corporativa
- **Trazabilidad** — transparencia, auditabilidad

---

## 2. PALETA DE COLORES

### Colores principales

| Color | Hex | Uso |
|---|---|---|
| **Blanco** | `#FFFFFF` | Fondo principal, tarjetas |
| **Blanco humo** | `#F8FAFC` | Fondo secundario |
| **Azul corporativo** | `#1E3A5F` | Header, sidebar, énfasis fuerte |
| **Azul primario** | `#2563EB` | Botones primarios, links, elementos activos |
| **Azul claro** | `#3B82F6` | Hover states, elementos interactivos |
| **Azul muy claro** | `#DBEAFE` | Fondos de badges info, highlights |
| **Gris claro** | `#F1F5F9` | Fondos de tarjetas secundarias, divisores |
| **Gris medio** | `#94A3B8` | Placeholders, texto deshabilitado |
| **Gris oscuro** | `#334155` | Texto secundario |
| **Casi negro** | `#0F172A` | Texto principal |

### Colores de estado

| Estado | Color | Hex | Uso |
|---|---|---|---|
| **Aprobado** | Verde | `#16A34A` | Badges, iconos, indicadores |
| **Aprobado fondo** | Verde claro | `#DCFCE7` | Fondos de badge |
| **Pendiente / Revisión** | Amarillo | `#EAB308` | Badges, iconos |
| **Pendiente fondo** | Amarillo claro | `#FEF9C3` | Fondos de badge |
| **Rechazado / Error** | Rojo | `#DC2626` | Badges, iconos, alertas |
| **Rechazado fondo** | Rojo claro | `#FEE2E2` | Fondos de badge |
| **En proceso** | Azul | `#2563EB` | Badges, iconos |
| **En proceso fondo** | Azul claro | `#DBEAFE` | Fondos de badge |

---

## 3. TIPOGRAFÍA

| Uso | Familia | Peso | Tamaño (móvil) | Tamaño (desktop) |
|---|---|---|---|---|
| **H1 (título principal)** | Inter | 700 | 24px | 32px |
| **H2 (subtítulo)** | Inter | 600 | 20px | 24px |
| **H3 (sección)** | Inter | 600 | 18px | 20px |
| **Body (texto)** | Inter | 400 | 14px | 16px |
| **Small (label, caption)** | Inter | 400 | 12px | 14px |
| **Botones** | Inter | 600 | 14px | 16px |
| **Tablas** | Inter | 400 | 13px | 14px |

### TailwindCSS Config:
```js
// tailwind.config.ts
theme: {
  fontFamily: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
  },
}
```

---

## 4. COMPONENTES PRINCIPALES

### 4.1 Botones

| Tipo | Clases Tailwind | Uso |
|---|---|---|
| **Primario** | `bg-blue-600 text-white hover:bg-blue-700 rounded-lg px-4 py-2.5` | Acción principal |
| **Secundario** | `bg-white text-blue-600 border border-blue-600 hover:bg-blue-50 rounded-lg px-4 py-2.5` | Acción secundaria |
| **Peligro** | `bg-red-600 text-white hover:bg-red-700 rounded-lg px-4 py-2.5` | Eliminar, rechazar |
| **Éxito** | `bg-green-600 text-white hover:bg-green-700 rounded-lg px-4 py-2.5` | Aprobar |
| **Fantasma** | `text-blue-600 hover:bg-blue-50 rounded-lg px-4 py-2.5` | Navegación, acciones menores |
| **Mobile** | `min-h-[44px] min-w-[44px]` | Touch target mínimo en móvil |

### 4.2 Inputs / Form Fields

```
┌──────────────────────────────┐
│  Label                    🔍 │
│  ┌──────────────────────────┐│
│  │ Placeholder text...      ││
│  └──────────────────────────┘│
│  ⚠️ Mensaje de error         │
└──────────────────────────────┘
```

- Borde: `border border-slate-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500`
- Error: `border-red-500 focus:border-red-500`
- Altura: `h-11` (móvil), `h-10` (desktop)
- Border radius: `rounded-lg`

### 4.3 Cards / Tarjetas

```
┌─────────────────────────┐
│ 🏭 Granja La Esperanza  │
│                         │
│ 📍 Ubicación: Valle     │
│ 🐔 Lotes activos: 3     │
│ 📊 Estado: Operativa    │
│                         │
│ [Ver detalle →]         │
└─────────────────────────┘
```

- `bg-white rounded-xl shadow-sm border border-slate-200 p-4`
- Hover: `hover:shadow-md transition-shadow`

### 4.4 Tablas (Web)

```
┌────┬──────────┬────────┬────────┬──────┐
│ ID │ Lote     │ Fecha  │ Estado │ Acc. │
├────┼──────────┼────────┼────────┼──────┤
│ 1  │ L-2026-A │ 22/06  │ ✅ Ap. │ ⋯   │
│ 2  │ L-2026-B │ 21/06  │ 📋 Rev │ ⋯   │
└────┴──────────┴────────┴────────┴──────┘
```

- Header: `bg-slate-50 text-slate-700 font-semibold`
- Row hover: `hover:bg-blue-50`
- Alternating: `even:bg-slate-50`
- Borde inferior: `border-b border-slate-200`

### 4.5 Badges de Estado

```
┌────────────┐  ┌────────────┐  ┌────────────┐
│ ✅ Aprobado│  │ 📋 Revisión│  │ ❌ Rechazado│
└────────────┘  └────────────┘  └────────────┘
```

- `inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium`
- Aprobado: `bg-green-100 text-green-800`
- Pendiente: `bg-yellow-100 text-yellow-800`
- Rechazado: `bg-red-100 text-red-800`
- En proceso: `bg-blue-100 text-blue-800`

### 4.6 Modales

```
┌──────────────────────────────┐
│  Título del Modal         ✕  │
├──────────────────────────────┤
│                              │
│  Contenido del modal...      │
│                              │
├──────────────────────────────┤
│            [Cancelar] [OK]   │
└──────────────────────────────┘
```

- Overlay: `bg-black/50 backdrop-blur-sm`
- Contenido: `bg-white rounded-2xl shadow-xl p-6`
- Mobile: `mx-4 my-auto max-h-[90vh] overflow-auto`

---

## 5. LAYOUT PRINCIPAL

### 5.1 Mobile (operador de campo)

```
┌──────────────────────┐
│ ☰ Global Avícola  🌐│  ← Header
├──────────────────────┤
│                      │
│  ┌──────────────────┐│
│  │ 📋 Registro      ││  ← Quick actions
│  │    Diario        ││
│  └──────────────────┘│
│                      │
│  ┌──────────────────┐│
│  │ 📊 KPI del Lote  ││  ← Dashboard cards
│  └──────────────────┘│
│                      │
├──────────────────────┤
│ 🏠  📝  📊  ⚙️  👤  │  ← Bottom nav
└──────────────────────┘
```

### 5.2 Desktop (supervisor / administrador)

```
┌──────┬──────────────────────────────────────┐
│      │  Dashboard / Global Avícola    🔔 👤 │ ← Top bar
│ Side │──────────────────────────────────────│
│ bar  │                                      │
│      │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
│ 🏠   │  │ KPI 1   │ │ KPI 2   │ │ KPI 3  │ │ ← KPI cards
│ 📝   │  └─────────┘ └─────────┘ └────────┘ │
│ 📊   │                                      │
│ ✅   │  ┌──────────────────────────────┐   │
│ 🔍   │  │ Tabla de registros           │   │ ← Main content
│ ⚙️   │  │ (filtros + paginación)       │   │
│      │  └──────────────────────────────┘   │
│      │                                      │
└──────┴──────────────────────────────────────┘
```

- Sidebar: `w-64 bg-[#1E3A5F] text-white` (azul corporativo oscuro)
- Top bar: `h-16 bg-white border-b border-slate-200`
- Content: `bg-[#F8FAFC] min-h-screen`

---

## 6. MOBILE-FIRST BREAKPOINTS

| Breakpoint | Min Width | Uso |
|---|---|---|
| `xs` | 360px | Móvil pequeño |
| `sm` | 640px | Móvil grande / landscape |
| `md` | 768px | Tablet |
| `lg` | 1024px | Desktop pequeño |
| `xl` | 1280px | Desktop estándar |
| `2xl` | 1536px | Desktop grande |

**Regla:** Diseñar primero para 360px. Usar `md:` y `lg:` breakpoints para adaptar a pantallas más grandes.

---

## 7. ICONOGRAFÍA

Usar **Lucide React** (iconos SVG limpios, tree-shakeable).

| Concepto | Icono |
|---|---|
| Granja | `🏭` / `Building2` |
| Galpón | `🏠` / `Home` |
| Alimento | `🌾` / `Wheat` |
| Pesaje | `⚖️` / `Scale` |
| Mortalidad | `💀` / `Skull` |
| Vacuna | `💉` / `Syringe` |
| Huevo | `🥚` / `Egg` |
| Incubadora | `🔥` / `Thermometer` |
| Pollito | `🐤` / `Bird` |
| Aprobado | `✅` / `CheckCircle` |
| Pendiente | `📋` / `ClipboardList` |
| Rechazado | `❌` / `XCircle` |
| Auditoría | `🔍` / `Search` |
| SAP | `🔄` / `RefreshCw` |
| Reporte | `📊` / `BarChart3` |

---

## 8. ACCESIBILIDAD

- **Contraste:** Mínimo ratio 4.5:1 para texto normal, 3:1 para texto grande
- **Focus visible:** `focus:ring-2 focus:ring-blue-500 focus:ring-offset-2`
- **Touch targets:** Mínimo 44×44px en móvil
- **Alt text:** Todas las imágenes tienen `alt`
- **ARIA labels:** En iconos sin texto visible
- **Keyboard navigation:** Todos los elementos interactivos son accesibles por teclado
- **Screen readers:** Estructura semántica HTML5 (`<nav>`, `<main>`, `<header>`)

---

## 9. ANIMACIONES Y TRANSICIONES

- **Sutiles y funcionales.** No distractivas.
- Transiciones de página: fade suave (200ms)
- Hover en tarjetas: `transition-shadow duration-200`
- Modal: fade in + scale up (200ms)
- Notificaciones: slide in from top-right (300ms)
- Loaders: skeleton screens (no spinners genéricos)
- **Respetar `prefers-reduced-motion`**

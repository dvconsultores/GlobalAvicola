# PROMPT: Evaluación visual multi-modo y certificación cross-browser

> **Decidido:** ✅ Modo oscuro oficial | ✅ Selector de idioma en ambos headers

## Contexto del proyecto

**Proyecto:** Global Avícola — Plataforma de gestión operativa avícola integrada con SAP.
**Stack:** React 19 + Vite + TypeScript + TailwindCSS v4 + lucide-react + i18next.
**Estado actual:** Rediseño UI/UX completado con sidebar jerárquico, submenús colapsables, breadcrumbs y navegación por procesos productivos.
**Idiomas:** Español (por defecto) + Inglés.

## Stack visual actual

### Paleta de colores — Modo claro (único implementado)

| Color | Hex | Uso |
|-------|-----|-----|
| Blanco | `#FFFFFF` | Fondo principal, tarjetas |
| Blanco humo | `#F8FAFC` | Fondo secundario |
| Azul corporativo | `#1E3A5F` | Sidebar, headers, tabs activos |
| Azul primario | `#2563EB` | Botones, links, elementos activos |
| Azul claro | `#3B82F6` | Hover states |
| Gris claro | `#F1F5F9` | Fondos de tarjetas secundarias |
| Casi negro | `#0F172A` | Texto principal |

### Colores de estado

| Estado | Color |
|--------|-------|
| Aprobado | `#16A34A` (verde) |
| Pendiente | `#EAB308` (amarillo) |
| Rechazado | `#DC2626` (rojo) |
| En proceso | `#2563EB` (azul) |

### Layout actual

```
DESKTOP (≥1024px):
┌──────────┬──────────────────────────────────────┐
│ Sidebar  │  Header (breadcrumbs + acciones)      │
│ w-64     │───────────────────────────────────────│
│ fijo     │  Contenido principal                  │
│ #1E3A5F  │  max-w-7xl mx-auto                    │
└──────────┴──────────────────────────────────────┘

MOBILE (<1024px):
┌──────────────────────────────┐
│ Header ☰ Global Avícola 🌐  │
├──────────────────────────────┤
│ Breadcrumbs                  │
├──────────────────────────────┤
│ Contenido (scroll)           │
├──────────────────────────────┤
│ Bottom Nav (5 items fijos)   │
└──────────────────────────────┘
```

### Estado del modo oscuro

Actualmente el proyecto tiene:
- `tailwind.config.ts` con configuración `dark: 'class'`
- Algunos estilos `dark:` dispersos en componentes
- Un `DarkModeToggle.tsx` componente
- Un `theme.store.ts` para persistencia
- **PERO** el design system oficial dice: *"Sin dark mode — diseño corporativo claro siempre"*

Esto genera una contradicción: hay infraestructura para dark mode pero no está oficialmente soportado ni implementado consistentemente.

### Estado del selector de idioma

- Selector actual: botón pequeño en el Header mobile (`ES`/`EN`) y en el MobileDrawer footer
- En desktop: **NO hay selector visible** (solo en mobile)
- Store: `i18n.store.ts` persiste preferencia en localStorage
- Traducciones: ~350 claves por idioma (ES/EN)

### Navegación mobile actual

- **Bottom nav:** 5 items fijos (Inicio, Registrar, Lotes, KPIs, Menú) — contextual según ruta
- **Hamburger menu (☰):** Abre MobileDrawer con jerarquía completa del sidebar
- **Drawer:** Misma estructura que sidebar desktop (5 secciones + submenús colapsables)
- **Scroll:** El drawer tiene `overflow-y-auto`, el contenido principal también

## Lo que se solicita evaluar (sin implementar aún)

### 1. Modo oscuro — ¿Sí o no?

**Pregunta:** ¿Debemos soportar modo oscuro oficialmente?

El spec actual dice: *"Sin dark mode — diseño corporativo claro siempre"*
Pero existe infraestructura parcial (`dark:` classes, `theme.store`, `DarkModeToggle`).

**Para evaluar:**
- ¿El modo oscuro agrega valor a un operador de campo que usa la app bajo el sol?
- ¿Es consistente con la identidad "blanco y azul corporativo"?
- ¿Cuánto esfuerzo tomaría implementarlo correctamente (vs tenerlo a medias)?
- ¿Los operadores de campo lo usarían realmente?

**Si la respuesta es NO:**
- Eliminar `DarkModeToggle.tsx`
- Eliminar `theme.store.ts`
- Eliminar clases `dark:` de todos los componentes
- Limpiar `tailwind.config.ts`

**Si la respuesta es SÍ:**
- Auditoría completa de todos los componentes para consistencia dark mode
- Definir paleta oscura corporativa (no la default de Tailwind)
- Implementar toggle en header visible (no oculto)
- Probar contraste en todos los estados (aprobado/error/pendiente en fondo oscuro)

### 2. Selector de idioma — Visible en desktop también

**Problema actual:** El selector de idioma (ES/EN) solo es visible en:
- Header mobile (como botón pequeño)
- Footer del MobileDrawer

**En desktop no hay forma de cambiar de idioma** sin usar el drawer o recargar.

**Solución propuesta a evaluar:**
- Agregar selector de idioma en el **header desktop** (arriba a la derecha, junto al usuario)
- Mantenerlo también en mobile header
- Hacerlo visualmente claro: un toggle o botón con bandera/abreviatura

**Opciones de diseño:**
```
Opción A: Botón texto  [ES/EN]  → simple, ocupa poco espacio
Opción B: Toggle switch [ES|EN] → más visual
Opción C: Dropdown con banderas → más estándar internacional
```

### 3. Menú scrollable — Evaluar comportamiento actual

**Estado actual:**
- Sidebar desktop: `overflow-y-auto` (ya scrollable)
- MobileDrawer: `overflow-y-auto` (ya scrollable)
- Bottom nav: fijo (no scrollable)

**Para evaluar:**
- ¿El sidebar desktop hace scroll correctamente cuando hay muchos items?
- ¿El submenú expandido empuja los items hacia abajo o hace scroll interno?
- En mobile, ¿el drawer con toda la jerarquía cabe sin scroll?

### 4. Menú hamburguesa — Validación completa

**Estado actual:**
- El ☰ hamburger abre el `MobileDrawer`
- Drawer: overlay + slide desde izquierda
- Cierra con: Escape, click fuera, navegación

**Para evaluar:**
- ¿El drawer se ve bien en todos los viewports mobile (360px - 820px)?
- ¿La animación slide es suave?
- ¿El overlay cubre toda la pantalla?
- ¿Se cierra correctamente en todas las rutas?
- ¿El botón hamburguesa tiene `aria-label` y `aria-expanded`?
- ¿Es accesible por teclado?

### 5. 100% Web App — Verificación

**Requisitos:**
- Sin dependencia de CDN (actual: Google Fonts eliminado ✅, self-host via @fontsource)
- Sin funcionalidad que requiera app nativa
- PWA ready (verificar si hay manifiesto)
- Responsive en 7 breakpoints (360px → 1440px)
- Sin errores de consola en ningún viewport

### 6. Certificación cross-browser y cross-OS

**Navegadores a certificar:**

| Navegador | Versión | OS a probar |
|-----------|---------|-------------|
| Google Chrome | Últimas 2 | Windows, macOS, Linux, Android |
| Mozilla Firefox | Últimas 2 | Windows, macOS, Linux |
| Apple Safari | Últimas 2 | macOS, iOS |
| Microsoft Edge | Últimas 2 | Windows, macOS |
| Opera | Últimas 2 | Windows, macOS |
| Samsung Internet | Últimas 2 | Android |
| Android WebView | Últimas 2 | Android |

**Qué verificar por navegador:**
- [ ] Sidebar se renderiza correctamente
- [ ] Submenús colapsables funcionan
- [ ] Breadcrumbs se ven bien
- [ ] Formularios y validaciones funcionan
- [ ] Modales y diálogos se renderizan
- [ ] i18n ES/EN funciona
- [ ] Scroll en sidebar y drawer
- [ ] Animaciones CSS (respetar `prefers-reduced-motion`)
- [ ] Touch events en mobile
- [ ] Sin errores de consola

## Lo que NO se toca

- ❌ `processCatalog.ts` (etapas, operaciones, colores, íconos)
- ❌ Reglas de negocio (BR-01 a BR-16)
- ❌ Backend (código, endpoints, modelos)
- ❌ Rutas existentes
- ❌ Lógica de operaciones, revisión, aprobación, SAP
- ❌ `navigationConfig.ts` (ya aprobado)

## Archivos que probablemente necesitan cambios (solo si se decide implementar)

| Archivo | Posible cambio |
|---------|---------------|
| `components/layout/Header.tsx` | Agregar selector de idioma en desktop |
| `components/layout/Sidebar.tsx` | Verificar scroll |
| `components/layout/MobileDrawer.tsx` | Verificar scroll y cierre |
| `components/DarkModeToggle.tsx` | Decidir: eliminar o completar |
| `stores/theme.store.ts` | Decidir: eliminar o completar |
| `index.html` | Verificar PWA manifest |
| `tailwind.config.ts` | Limpiar config dark si se elimina |
| `public/locales/es/translation.json` | Posibles ajustes de texto |
| `public/locales/en/translation.json` | Posibles ajustes de texto |

## Proceso propuesto

1. ✅ **Prompt creado** (este documento)
2. 🤝 **Revisión conjunta** — discutimos cada punto y decidimos qué hacer
3. ✏️ **Ajustes** — modificamos el prompt según lo acordado
4. 🚀 **Implementación** — solo después de la confirmación

---

*Prompt preparado para revisión conjunta. Sin cambios implementados aún.*

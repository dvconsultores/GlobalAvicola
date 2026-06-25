# PROMPT: Rediseño de flujo Web vs Mobile — Global Avícola

> Basado en spec funcional, documentación auditada y feedback visual directo.
> Sin modificar backend, reglas de negocio, processCatalog, ni rutas existentes.

---

## 1. Problemas identificados (actual)

### 1.1 Web: Sidebar y Hub se solapan

Actualmente, cuando un usuario web navega en el sidebar, el Hub (`/poultry`) muestra las mismas 6 tarjetas de procesos que usa el operador mobile. Esto es incorrecto porque:

- **Usuario web** → usa el sidebar para navegar → al hacer clic en una fase, debe ver **directamente las operaciones** de esa fase, no un selector de procesos.
- **Usuario mobile** → usa bottom nav o drawer → necesita las tarjetas visuales del Hub para elegir proceso y luego fase.

**Flujo actual (incorrecto):**
```
Web: Sidebar → Progenitoras → Cría  →  /poultry  (¡el Hub con 6 tarjetas otra vez!)
Mobile: Bottom nav → /poultry → tarjetas → elegir proceso → operaciones
```

**Flujo deseado (correcto):**
```
Web: Sidebar → Progenitoras → Cría  →  /poultry/grandparent/rearing  →  OPERACIONES directo
Mobile: Bottom nav → /poultry → tarjetas → elegir proceso → fase → operaciones
```

### 1.2 Tarjetas de procesos (Hub) — Diseño incorrecto

Las 6 tarjetas del Hub usan **gradientes de colores variados** (ámbar, teal, naranja, verde, etc.) que:
- No combinan con el estilo corporativo **blanco y azul**
- Se ven toscas, grandes y poco profesionales
- Rompen la identidad visual de Global Avícola

### 1.3 Sidebar: Incubadora y Pollo de Engorde

Son **macro procesos independientes**, no dependen de Reproductoras ni de ningún otro. Deben aparecer como hijos directos de "Gestión Avícola" al mismo nivel que Progenitoras y Reproductoras. (Actualmente ya es así, verificar visualmente).

---

## 2. Solución propuesta

### 2.1 Web: Sidebar → Operaciones directo (sin pasar por Hub)

Cuando un usuario web (sidebar visible) hace clic en cualquier fase del menú:
- **Progenitoras → Cría** → `/poultry/grandparent/rearing` → Muestra directamente el grid de operaciones
- **Progenitoras → Producción** → `/poultry/grandparent/production` → Muestra directamente el grid de operaciones
- **Reproductoras → Cría** → `/poultry/breeder/rearing` → Muestra directamente el grid de operaciones
- **Reproductoras → Producción** → `/poultry/breeder/production` → Muestra directamente el grid de operaciones
- **Incubadora** → `/poultry/hatchery` → Muestra directamente el grid de operaciones
- **Pollo de Engorde** → `/poultry/broiler` → Muestra directamente el grid de operaciones

Esto YA funciona en las rutas. El problema es que el Hub (`/poultry`) sigue siendo el default y se ve igual para web y mobile.

**Solución:** La ruta `/poultry` (el Hub) debe redirigir automáticamente al dashboard o a la primera fase si el usuario es web. O simplemente dejar que el sidebar siempre navegue directo a una fase específica (ya es así). El Hub `/poultry` solo debe mostrarse para usuarios mobile (o como página de aterrizaje si no hay fase seleccionada).

### 2.2 Rediseño de tarjetas del Hub — Estilo corporativo azul/blanco

Las 6 tarjetas deben rediseñarse con la paleta corporativa:

| Elemento | Antes (incorrecto) | Después (correcto) |
|----------|-------------------|-------------------|
| **Fondo de tarjeta** | Gradientes coloridos | `bg-white` con borde `border-slate-200` |
| **Header de tarjeta** | Gradiente naranja/verde/teal | `bg-[#1E3A5F]` (azul corporativo) |
| **Icono** | Sobre fondo blanco semitransparente | `bg-blue-100 text-blue-600` |
| **Número** | Blanco semitransparente grande | `text-slate-300` pequeño y sutil |
| **Borde en hover** | Ámbar/verde/teal | `hover:border-blue-400 hover:shadow-md` |
| **Texto precio paso** | Variable | Siempre `text-slate-600` |
| **Botón "Abrir"** | Azul #2563EB | Azul #2563EB (mantener) |

### 2.3 Mobile: Hub de tarjetas se mantiene

Para usuarios mobile, el Hub con las 6 tarjetas sigue siendo el entry point visual. La diferencia es:

- Mobile no tiene sidebar, usa bottom nav
- Mobile necesita las tarjetas grandes para elegir proceso
- El diseño de las tarjetas se actualiza al estilo corporativo (azul/blanco)

---

## 3. Estructura del menú (confirmada)

```
🐔 Gestión Avícola
  ▼ Progenitoras            ← Macro proceso 1
       🌱 Cría              → /poultry/grandparent/rearing
       🥚 Producción        → /poultry/grandparent/production
  ▼ Reproductoras           ← Macro proceso 2
       🌱 Cría              → /poultry/breeder/rearing
       🥚 Producción        → /poultry/breeder/production
  🔥 Incubadora             ← Macro proceso 3 (independiente)
       → /poultry/hatchery
  🍗 Pollo de Engorde       ← Macro proceso 4 (independiente)
       → /poultry/broiler
```

**Incubadora y Pollo de Engorde son MACRO PROCESOS INDEPENDIENTES**, no están bajo Reproductoras ni dependen de ninguna otra fase. Son hijos directos de Gestión Avícola al mismo nivel que Progenitoras y Reproductoras.

---

## 4. Lo que NO se toca

- ❌ Backend (endpoints, modelos, migraciones)
- ❌ `processCatalog.ts` (etapas, operaciones, colores de evento, flujos)
- ❌ Reglas de negocio (BR-01 a BR-16)
- ❌ Rutas existentes (`/poultry/*`, `/operations/*`, `/review/*`, etc.)
- ❌ Lógica de operaciones, revisión, aprobación, SAP
- ❌ `navigationConfig.ts` (ya refleja la estructura correcta)
- ❌ i18n (ya está completo con 634 claves ES/EN)
- ❌ Componentes UI base (Button, Input, Card, Badge, Modal, etc.)

---

## 5. Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `pages/operations/ProcessHubPage.tsx` | Rediseñar tarjetas: quitar gradientes coloridos, usar azul corporativo + blanco |
| `data/processCatalog.ts` | Actualizar `gradient` y `accent` de cada stage a tonos azules corporativos |
| `App.tsx` | Redirigir `/poultry` → `/poultry/grandparent/rearing` si usuario es web (opcional) |

---

## 6. Criterios de aceptación

- [ ] Al hacer clic en **Progenitoras → Cría** en el sidebar, se ve el grid de operaciones de Cría (no el Hub)
- [ ] Al hacer clic en **Incubadora** en el sidebar, se ven las operaciones de Incubadora
- [ ] Al hacer clic en **Pollo de Engorde** en el sidebar, se ven las operaciones de Engorde
- [ ] Las tarjetas del Hub (mobile) usan colores corporativos azul/blanco
- [ ] No hay gradientes amarillos, naranjas, verdes ni teal en las tarjetas
- [ ] El diseño se ve profesional, limpio y corporativo
- [ ] Build pasa sin errores (`tsc -b && vite build`)
- [ ] Tests pasan (`vitest run && playwright test`)
- [ ] Sin cambios en backend ni `processCatalog.ts`

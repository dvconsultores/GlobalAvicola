# PROMPT: Refinamiento de navegación — Gestión Avícola

## Contexto

Proyecto: **Global Avícola** — Plataforma de gestión operativa avícola integrada con SAP.
Stack: React 19 + Vite + TypeScript + TailwindCSS v4 + React Router v7.
Estado actual: Rediseño UI/UX completado con sidebar jerárquico, submenús colapsables, breadcrumbs y navegación por procesos productivos.

## Situación actual (lo que existe hoy)

### Menú lateral — Sección OPERATIVO

```
🐔 Gestión Avícola
  ▼ Progenitoras
       Cría
       Producción
  ▼ Reproductoras
       Cría
       Producción
  🔥 Incubadora
  🍗 Pollo de Engorde

📄 Operations          ← ÍTEM SEPARADO EN EL MENÚ (sobrante)
```

### Rutas actuales

| Ruta | Pantalla | Propósito |
|------|----------|-----------|
| `/poultry` | PoultryHubPage | Mosaico de las 6 etapas productivas |
| `/poultry/grandparent/rearing` | StagePage | Operaciones de Progenitoras en Cría |
| `/poultry/grandparent/production` | StagePage | Operaciones de Progenitoras en Producción |
| `/poultry/breeder/rearing` | StagePage | Operaciones de Reproductoras en Cría |
| `/poultry/breeder/production` | StagePage | Operaciones de Reproductoras en Producción |
| `/poultry/hatchery` | StagePage | Operaciones de Incubadora |
| `/poultry/broiler` | StagePage | Operaciones de Pollo de Engorde |
| `/operations` | OperationListPage | Lista genérica de operaciones |
| `/operations/new` | OperationFormPage | Formulario de nueva operación |
| `/operations/:id` | OperationDetailPage | Detalle de operación |

### Procesos definidos (processCatalog.ts — **no modificar**)

```typescript
export type StageKey =
  | 'grandparent_rearing'    // Progenitoras — Cría
  | 'grandparent_production' // Progenitoras — Producción
  | 'breeder_rearing'        // Reproductoras — Cría
  | 'breeder_production'     // Reproductoras — Producción
  | 'hatchery'               // Incubadora
  | 'broiler'                // Pollo de Engorde
```

Cada stage tiene su propio conjunto de operaciones (event types) definido en `STAGE_OPERATIONS`:

| Stage | BirdType | Operaciones disponibles |
|-------|----------|----------------------|
| `grandparent_rearing` | grandparent | farm_inspection, bird_reception, feed_registration, weight_recording, mortality_recording, vaccination, medication, cull_recording, bird_exit... |
| `grandparent_production` | grandparent | farm_inspection, feed_registration, weight_recording, egg_collection, egg_classification, egg_dispatch, bird_exit... |
| `breeder_rearing` | breeder | farm_inspection, bird_reception, feed_registration, weight_recording, mortality_recording, vaccination, medication, bird_exit... |
| `breeder_production` | breeder | farm_inspection, feed_registration, weight_recording, egg_collection, egg_classification, egg_dispatch, bird_exit... |
| `hatchery` | hatchery | egg_reception_hatchery, incubation_load, ovoscopy, transfer_to_hatcher, birth_registration, chick_dispatch... |
| `broiler` | broiler | bird_reception, feed_registration, weight_recording, mortality_recording, vaccination, lot_closure... |

## Lo que se solicita

### 1. Eliminar "Operations" del menú lateral

**Motivación:** Todo proceso avícola tiene un flujo que conduce naturalmente a una operación. El operador no "va a operaciones" como una sección separada; el operador:
1. Selecciona una fase productiva (Gestión Avícola → Reproductoras)
2. Selecciona la etapa (Cría o Producción)
3. Dentro de la etapa, elige la operación concreta (Registrar mortalidad, Registrar pesaje, etc.)

Tener "Operations" como un ítem separado en el menú:
- Confunde al operador (no sabe si ir a "Gestión Avícola" o a "Operations")
- Rompe el flujo natural del proceso
- Duplica puntos de entrada a la misma funcionalidad

**Qué hacer:**
- Eliminar el ítem "Operations" / `nav.operations` del sidebar y del drawer
- La ruta `/operations` puede seguir existiendo (no romper bookmarks) pero sin entrada en el menú
- El formulario `/operations/new` sigue siendo el destino al hacer clic en cualquier operación desde una etapa

### 2. Reforzar la distinción Cría vs Producción (CRÍTICO — no negociable)

**Motivación:** Para Progenitoras y Reproductoras, la diferenciación entre **Cría** (rearing) y **Producción** (production) es **neuralgia** del proceso productivo. Cada etapa:
- Tiene operaciones **completamente diferentes** (Cría no tiene recolección de huevos; Producción no tiene recepción de aves)
- Representa una fase biológica distinta del lote
- Determina qué KPIs aplican

El navegador (operador de campo) **nunca debe poder confundir** si está registrando en Cría o en Producción.

**Qué hacer:**
- En el menú lateral, las subfases "Cría" y "Producción" deben ser **visualmente distintas** (icono diferente, color de fondo distinto o badge)
- Al entrar a una etapa, el header debe mostrar claramente: `Progenitoras › Cría` o `Progenitoras › Producción`
- El selector de lotes debe mostrar **solo lotes en la fase correcta** (ya implementado vía `STAGE_BIRD_TYPES`, verificar)
- En mobile, el breadcrumb o indicador de etapa debe ser igual de visible

### 3. El flujo completo del operador debe ser

```
Gestión Avícola
  → Progenitoras (o Reproductoras)
    → ¿Cría o Producción?  ← ELECCIÓN OBLIGADA, VISIBLE
      → Seleccionar lote
        → Elegir operación
          → Formulario → Guardar
```

### 4. Lo que NO debe cambiar

- ❌ No modificar `processCatalog.ts` (etapas, operaciones, colores, íconos)
- ❌ No cambiar la lógica de negocio (BR-01 a BR-16)
- ❌ No eliminar rutas existentes (`/operations`, `/operations/new`, `/operations/:id`) — solo ocultar del menú
- ❌ No cambiar backend
- ✅ Mantener el diseño blanco/azul, i18n ES/EN, componentes UI existentes
- ✅ Mantener breadcrumbs, submenús colapsables, sidebar jerárquico

### 5. Archivos que probablemente necesitan cambios

| Archivo | Cambio |
|---------|--------|
| `data/navigationConfig.ts` | Eliminar la entrada `nav.operations` del `NAV_ITEMS` |
| `components/layout/Sidebar.tsx` | Verificar que no haya referencia directa a /operations |
| `components/layout/MobileDrawer.tsx` | Verificar que no haya referencia directa |
| `App.tsx` | Mantener rutas `/operations*` pero sin menú |
| `public/locales/es/translation.json` | Eliminar clave `nav.operations` del menú (mantener para otros usos si existe) |
| `public/locales/en/translation.json` | Igual que ES |

### 6. Criterios de aceptación

- [ ] El menú lateral NO muestra "Operations" como ítem
- [ ] Las rutas `/operations`, `/operations/new`, `/operations/:id` siguen funcionando (pueden llegar desde un botón "Ver historial" dentro de una etapa)
- [ ] Progenitoras muestra claramente "Cría" y "Producción" como subfases diferenciadas
- [ ] Reproductoras muestra claramente "Cría" y "Producción" como subfases diferenciadas
- [ ] El breadcrumb muestra `Progenitoras › Cría` o `Progenitoras › Producción`
- [ ] Al seleccionar un lote en la etapa, solo se muestran lotes de la fase correcta
- [ ] Mobile mantiene la misma claridad en la distinción
- [ ] i18n completo ES/EN
- [ ] Build pasa sin errores (`tsc -b && vite build`)

# 📐 Guía Visual del Rediseño

## 1. DASHBOARD MÓVIL - Nuevo

```
┌─────────────────────────────────┐
│ ✨ Inicio                       │  ← Header azul gradiente
│ Hola, María                     │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 📊 Hoy                          │
├─────────────────────────────────┤
│  [5]    [2]    [1]             │  ← KPIs coloridos
│ Ops   Revisar Aprobadas        │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ ⚠️ Tienes 2 correcciones       │
│ Revisa tus operaciones...       │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 📋 6 Procesos Principales       │
├─────────────────────────────────┤
│ 🐔 Progenitoras - Cría         │
│    Importar abuelas...         │
│    [10 operaciones] →          │
├─────────────────────────────────┤
│ 🥚 Progenitoras - Producción   │
│    Producción y recolección... │
│    [12 operaciones] →          │
│  ... (4 procesos más)          │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ ⚡ Acciones Rápidas            │
├─────────────────────────────────┤
│  [🌾]  [⚖️]                    │
│ Alimento  Pesaje               │
│  [💀]  [🥚]                    │
│ Mortalidad Huevos              │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ Ver Todas las Operaciones →    │
└─────────────────────────────────┘
```

## 2. PROCESS HUB PAGE - Nuevo

```
┌──────────────────────────────────────┐
│ ✨ Procesos de Producción           │
│ Elige un proceso para registrar...  │
│ 6 procesos • 60+ operaciones        │
└──────────────────────────────────────┘

GRID 3 COLUMNAS (Desktop):

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  [🐔 Ámbar]  │  │ [🥚 Amarillo]│  │  [🪶 Teal]   │
│ Progenitoras │  │ Progenitoras │  │Reproductoras │
│ - Cría       │  │ - Producción │  │ - Cría       │
│ Importar...  │  │ Producción..│  │ Levante...   │
│ 10 ops ↗     │  │ 12 ops ↗    │  │ 9 ops ↗      │
└──────────────┘  └──────────────┘  └──────────────┘

┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ [🥚 Azul]    │  │ [🔥 Naranja] │  │[🍗 Verde]    │
│Reproductoras │  │ Incubadora   │  │Pollo Engorde │
│ - Producción │  │ Recepción... │  │ Recepción... │
│ Recolección..│  │ 8 ops ↗      │  │ 11 ops ↗     │
│ 10 ops ↗     │  │              │  │              │
└──────────────┘  └──────────────┘  └──────────────┘

💡 Toca cualquier proceso para ver el flujo...
```

## 3. PROCESS STAGE PAGE - Nuevo

```
┌─────────────────────────────────────┐
│ ← Volver a Procesos                │
└─────────────────────────────────────┘

╔═════════════════════════════════════╗
║ [🐔] Progenitoras - Cría            ║  ← Header coloreado
║     Importación de abuelas          ║
╚═════════════════════════════════════╝

┌─────────────────────────────────────┐
│ 🐔 Selecciona un lote (opcional)   │
├─────────────────────────────────────┤
│ [Sin lote — elegir al registrar ▼] │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 📊 Progreso del proceso             │
├─────────────────────────────────────┤
│ 0 de 10 etapas completadas    [0%] │
│ ██░░░░░░░░ (barra azul)            │
│ [🔵][🟡][🟡]...[⚪] (badges mini)  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 📋 Flujo de Operaciones             │
├─────────────────────────────────────┤
│ [1] Importar abuelas                │ ← Clic para expandir
│     Registrar importación...    ▼   │
│                                     │
│ [2] Inspeccionar granja             │ ← Estado: gris (pendiente)
│     Inspección pre-recepción   ▼    │
│                                     │
│ [3] Recepcionar aves                │
│     Cantidades y registro      ▼    │
│  ... (7 más)                        │
└─────────────────────────────────────┘

Ver historial de operaciones →
```

## 4. OPERACIÓN EXPANDIDA - Timeline

```
┌─────────────────────────────────────┐
│ [2] 🔍 Inspeccionar granja          │ ← Expandida
│     Inspección pre-recepción   ▲    │ ← Chevron arriba
├─────────────────────────────────────┤
│                                     │
│  [Registrar operación →]            │ ← Botón de acción
│                                     │
└─────────────────────────────────────┘
```

## 5. ESTADOS VISUALES

### Completado (✓)
```
┌─────────────────────────────────────┐
│ ✓ [1] Importar abuelas              │ ← Fondo verde
│     Registrar importación...        │ ← Icono verde
│ ✓ Completado                        │ ← Badge verde
└─────────────────────────────────────┘
```

### En Progreso (→)
```
┌─────────────────────────────────────┐
│ ✓ [2] Inspeccionar granja           │ ← Fondo azul, borde ancho
│     Inspección pre-recepción...     │ ← Número escalado
│ → En progreso                       │ ← Badge azul
│ ╔════════════════════════════════╗  │ ← Ring de foco
└─────────────────────────────────────┘
```

### Pendiente (○)
```
┌─────────────────────────────────────┐
│ ○ [3] Recepcionar aves              │ ← Fondo gris claro
│     Cantidades y registro...        │ ← Icono gris
│                                     │
└─────────────────────────────────────┘
```

## 6. ACCIONES RÁPIDAS - Dashboard

```
┌──────────────┐  ┌──────────────┐
│   🌾 AMARILLO│  │   ⚖️ AZUL    │
│   ALIMENTO   │  │   PESAJE     │
│   Registrar..│  │   Registrar..│
└──────────────┘  └──────────────┘

┌──────────────┐  ┌──────────────┐
│   💀 ROJO    │  │   🥚 NARANJA │
│  MORTALIDAD  │  │   HUEVOS     │
│   Registrar..│  │   Registrar..│
└──────────────┘  └──────────────┘
```

## 7. FLUJO COMPLETO DE UN USUARIO

```
USUARIO ABRE LA APP
         ↓
    [Dashboard Mobile]
    ├─ Ve 3 KPIs
    ├─ Ve alerta (si aplica)
    ├─ Ve 6 procesos
    └─ Ve acciones rápidas
         ↓
    Opción A: Toca un proceso
         ↓
    [Process Stage Page]
    ├─ Selecciona lote (opcional)
    ├─ Ve timeline vertical
    └─ Expande etapa y registra
         ↓
    [Operation Form]
         ↓
    ✓ Operación registrada
         
    Opción B: Usa acción rápida
         ↓
    [Operation Form] (preseleccionado)
         ↓
    ✓ Operación registrada
```

---

## Comparativa Antes vs Después

| Aspecto | ANTES | DESPUÉS |
|---------|-------|---------|
| **Colores** | Azul/gris monótono | Arcoíris 6 colores |
| **Procesos visibles** | No separados | Muy claros |
| **Flujo visual** | Lineal aburrido | Timeline expandible |
| **Estado etapas** | No se ve | ✓/→/○ claros |
| **Progreso** | No mostrado | Barra + %; badges |
| **Acciones rápidas** | 4 genéricas | 4 contextuales |
| **Espaciado** | Apretado | Generoso |
| **Iconografía** | Simple | Moderna y clara |
| **Jerarquía** | Confusa | Cristalina |
| **Intuitividad** | Media | Alta |
| **Visual appeal** | 5/10 | 9/10 |


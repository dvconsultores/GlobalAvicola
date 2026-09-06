# `P-12` · INVENTARIO DEL FRONTEND

Fase de análisis · 2026-09-06

---

## 1. La arquitectura, antes que el recuento

No hay doce pantallas: hay **una sola**, `MasterListPage`, parametrizada, y las rutas se
generan desde una lista en `App.tsx:94`.

```tsx
{masterEntities.map((m) => (
  <Route path={`/masters/${m.entity}`} element={
    <WebOnlyRoute><MasterListPage entity={m.entity} columns={m.cols} …/></WebOnlyRoute>} />
))}
```

Esto importa para dimensionar: **añadir un catálogo es añadir una entrada a esa lista**, no
escribir una pantalla. `§18` del encargo advertía exactamente de esta confusión.

## 2. Cobertura

| Maestro | Ruta | Lista | Alta | Edición | Baja | Paginación | Contador | i18n | Prueba |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| `companies` | `/masters/companies` | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠ §4 | ✅ | E2E heredada |
| `farms` | `/masters/farms` | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠ | ✅ | sí |
| `houses` | `/masters/houses` | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠ | ✅ | sí |
| `hatcheries` | `/masters/hatcheries` | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠ | ✅ | sí |
| `suppliers` · `genetic-lines` · `breeds` · `feed-types` · `vaccines` · `mortality-causes` · `transports` · `processing-plants` | sí | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠ | ✅ | parcial |
| **`incubators`** | **ninguna** | ❌ | ❌ | ❌ | ❌ | — | — | — | no |
| **`hatchers`** | **ninguna** | ❌ | ❌ | ❌ | ❌ | — | — | — | no |
| **`productive-phases`** | **ninguna** | ❌ | ❌ | ❌ | ❌ | — | — | — | no |
| **`medications`** | **ninguna** | ❌ | ❌ | ❌ | ❌ | — | — | — | no |
| **`cull-causes`** | **ninguna** | ❌ | ❌ | ❌ | ❌ | — | — | — | no |
| **`rejection-reasons`** | **ninguna** | ❌ | ❌ | ❌ | ❌ | — | — | — | no |
| **`correction-types`** | **ninguna** | ❌ | ❌ | ❌ | ❌ | — | — | — | no |

```
12 de 19 con capacidad de gestión · 7 sin ninguna
```

## 3. Verificado en los dos lados

`§9` del encargo lo exige y la lección de `R-87`/`R-88` lo justifica. Para los siete se
comprobó, uno a uno:

| | |
|---|---|
| ruta en `App.tsx` | **no existe** — la lista `masterEntities` no los incluye |
| componente propio | **no existe** — solo hay `MasterListPage.tsx` en el directorio |
| entrada de navegación | irrelevante: sin ruta no hay pantalla, con menú o sin él |
| endpoint backend | **existe** — los cinco del CRUD genérico salvo `PUT` |

No es «no lo encontré en el frontend»: es que la lista que genera las rutas **no los nombra**,
y esa lista es la única fuente de rutas de maestros.

## 4. El contador

`MasterListPage:45` hace `setTotal(response.data.length)` y `FilterPanel` lo pinta como
«N **resultados**». Con paginación de 20, en un catálogo de 45 registros el usuario lee «20
resultados».

**Pero la causa no está aquí**, ver `P12_PAGINATION_CONTRACT_MATRIX.md`.

# RUTAS DE FRONTEND FRENTE A UNIDAD DE NEGOCIO

Auditoría del 2026-09-07 · 29 rutas declaradas en `App.tsx` · **solo lectura**

---

## 1. La advertencia, por delante

```
MENÚ OCULTO  ≠  BACKEND PROTEGIDO
```

Todo lo que sigue describe **experiencia**, no seguridad. Ninguna de estas rutas protege nada:
la API responde igual escribiendo la URL a mano. Ver `BACKEND_ROUTE_MODULE_MATRIX.md`.

## 2. La matriz

| Route/Page | Unidad | Menu Entry | Direct URL Possible | Current Guard | Needed |
|---|---|:--:|:--:|---|:--:|
| `/login` | — | no | sí | — | no |
| `/` (dashboard) | **agrega las cuatro** | sí | sí | sesión | **sí** |
| `/kpi` | agrega las cuatro | sí | sí | sesión | **sí** |
| `/menu/:menuKey` | mixta | sí | sí | `view_type` | **sí** |
| `/poultry` | **las cuatro** | sí | sí | `WebOnly`/`view_type` | **sí** |
| **`/poultry/:birdType/:phase?`** | **la unidad va en la URL** | sí | **sí** | ninguna por unidad | **SÍ — el caso más claro** |
| `/processes`, `/processes/:stage` | mixta | sí | sí | ninguna por unidad | **sí** |
| `/operations`, `/operations/new`, `/operations/:id` | derivable vía lote | sí | sí | ninguna por unidad | **sí** |
| `/my-pending` | derivable | sí | sí | ninguna por unidad | **sí** |
| `/lots`, `/lots/new`, `/lots/:id` | derivable | sí | sí | ninguna por unidad | **sí** |
| `/reports`, `/reports/lot/:id`, `/reports/sap` | agrega | sí | sí | ninguna por unidad | **sí** |
| `/review`, `/review/:id`, `/review/:id/correct` | multi | sí | sí | ninguna por unidad | **sí** |
| `/approvals` | multi | sí | sí | ninguna por unidad | **sí** |
| `/audit` | multi | sí | sí | ninguna por unidad | **decisión pendiente** |
| `/sap` | multi | sí | sí | ninguna por unidad | a decidir |
| `/masters` y sus 22 entradas | mixta | sí | sí | `WebOnlyRoute` | **sí, por maestro** |
| `/users`, `/roles`, `/profile` | — | sí | sí | `WebOnlyRoute` | no |

## 3. `/poultry/:birdType/:phase?` merece su propio párrafo

Es la única ruta del producto que **lleva la unidad de negocio en la dirección**. Hoy
cualquiera con sesión puede escribir `/poultry/hatchery/...` y la pantalla se carga: no hay
comprobación en el cliente, y la API que alimenta esa pantalla tampoco la tiene.

```
POSIBLE HOY:  un usuario de Reproductoras escribe /poultry/hatchery y ve Incubadora
```

Es el ejemplo más didáctico del hueco, pero **no el más grave**: los listados de `/lots` y
`/operations` filtran ya, sin necesidad de escribir nada.

## 4. Enumeraciones estáticas en el cliente

`§46` del encargo pide buscarlas. Están:

```
frontend/src/data/processCatalog.ts     70 referencias a las cuatro unidades
frontend/src/data/navigationConfig.ts   14 referencias
frontend/src/data/thermalCurves.ts      por etapa
```

Son catálogos de **presentación** codificados en el cliente. Cuando exista un catálogo de
producto administrable habrá que decidir si estos se derivan de él o siguen siendo estáticos;
mientras tanto, son una segunda fuente de verdad sobre qué unidades existen.

## 5. Lo que el frontend sí debería hacer, cuando llegue el momento

```
company module OFF                    →  entrada de menú oculta
company ON · usuario sin permiso      →  oculta
company ON · usuario con permiso      →  visible
```

Y el backend rechazando igual en los tres casos. La interfaz decide qué se **ve**; nunca qué se
**puede**.

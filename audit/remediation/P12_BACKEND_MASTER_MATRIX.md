# `P-12` · INVENTARIO DEL BACKEND

Fase de análisis · 2026-09-06 · `masters/router.py::register_crud`

El CRUD es genérico: cinco rutas por maestro, y `PUT` **solo si se le pasa un esquema de
actualización**.

| Maestro | GET lista | GET detalle | POST | PUT | DELETE (baja lógica) | Esquema `Update` | Guarda de inquilino | Prueba |
|---|:--:|:--:|:--:|:--:|:--:|:--:|---|:--:|
| `companies` | ✅ | ✅ | ✅ | ✅ | ✅ | sí | raíz del inquilino | sí |
| `farms` | ✅ | ✅ | ✅ | ✅ | ✅ | sí | `company_id` | sí |
| `houses` | ✅ | ✅ | ✅ | ✅ | ✅ | sí | vía `farm_id` (`R-59`) | sí |
| `hatcheries` | ✅ | ✅ | ✅ | ✅ | ✅ | sí | `company_id` | sí |
| `genetic-lines` | ✅ | ✅ | ✅ | ✅ | ✅ | sí | `company_id` | sí |
| `breeds` | ✅ | ✅ | ✅ | ✅ | ✅ | sí | `company_id` | sí |
| `suppliers` | ✅ | ✅ | ✅ | ✅ | ✅ | sí | `company_id` | sí |
| `feed-types` | ✅ | ✅ | ✅ | ✅ | ✅ | sí | `company_id` | sí |
| `vaccines` | ✅ | ✅ | ✅ | ✅ | ✅ | sí | `company_id` | sí |
| `mortality-causes` | ✅ | ✅ | ✅ | ✅ | ✅ | sí | `company_id` | sí |
| `transports` | ✅ | ✅ | ✅ | ✅ | ✅ | sí | `company_id` | sí |
| `processing-plants` | ✅ | ✅ | ✅ | ✅ | ✅ | sí | `company_id` | sí |
| **`incubators`** | ✅ | ✅ | ✅ | **❌** | ✅ | **`None`** | vía `hatchery_id` | no |
| **`hatchers`** | ✅ | ✅ | ✅ | **❌** | ✅ | **`None`** | vía `hatchery_id` | no |
| **`productive-phases`** | ✅ | ✅ | ✅ | **❌** | ✅ | **`None`** | global | no |
| **`medications`** | ✅ | ✅ | ✅ | **❌** | ✅ | **`None`** | `company_id` | no |
| **`cull-causes`** | ✅ | ✅ | ✅ | **❌** | ✅ | **`None`** | `company_id` | no |
| **`rejection-reasons`** | ✅ | ✅ | ✅ | **❌** | ✅ | **`None`** | `company_id` | no |
| **`correction-types`** | ✅ | ✅ | ✅ | **❌** | ✅ | **`None`** | `company_id` | no |

```
19 maestros · GET 19/19 · POST 19/19 · DELETE 19/19 · PUT 12/19
```

## Corrección histórica que se mantiene

`audit/06` afirmaba que faltaba `PUT` en **ocho** maestros *con pantalla* —`suppliers`,
`genetic-lines`, `breeds`, `feed-types`, `vaccines`, `mortality-causes`, `transports`,
`processing-plants`—. **Eso ya estaba cerrado**: los ocho lo tienen, verificado uno a uno.

Los siete que hoy carecen de `PUT` son **otros**, y son exactamente los mismos que no tienen
pantalla. Ese solapamiento no es casualidad: nadie emite `PUT` contra ellos porque no hay
desde dónde.

```
R-91 · P2 · siete maestros normativos no admiten edición: sin esquema de actualización,
            `register_crud` no registra la ruta `PUT` y el maestro solo puede crearse y
            darse de baja, nunca corregirse.
```

## Permisos, homogéneos

`masters:read` · `masters:create` · `masters:update` · `masters:delete`, iguales para los 19.
No hay permisos por maestro, y nada en `§3.2` pide que los haya.

## Aislamiento

| Alcance | Maestros |
|---|---|
| `company_id` propio | 15 |
| vía el padre (`farm_id`, `hatchery_id`) | 3 — `houses`, `incubators`, `hatchers` |
| **global** | 1 — `productive-phases`, que no declara `company_id` |

`verificar_pertenencia` ya cubre el caso del padre (`R-59`). **No se le aplicará al maestro
global**: meterlo ahí sería justamente el error que `§41` advierte.

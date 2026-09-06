# `P-12` · PARIDAD FRONTEND ↔ BACKEND

Fase de análisis · 2026-09-06 · **la matriz que decide la dimensión real**

---

| Maestro | Normativo | Backend completo | Frontend completo | Contrato alineado | Clasificación |
|---|:--:|:--:|:--:|:--:|---|
| `companies` | sí | ✅ | ✅ | ⚠ contador | **`COMPLETE`** |
| `farms` | sí (Crítica) | ✅ | ✅ | ⚠ contador | **`COMPLETE`** |
| `houses` | sí (Crítica) | ✅ | ✅ | ⚠ contador | **`COMPLETE`** |
| `hatcheries` | sí (Crítica) | ✅ | ✅ | ⚠ contador | **`COMPLETE`** |
| `genetic-lines` | sí | ✅ | ✅ | ⚠ | **`COMPLETE`** |
| `breeds` | sí | ✅ | ✅ | ⚠ | **`COMPLETE`** |
| `suppliers` | sí | ✅ | ✅ | ⚠ | **`COMPLETE`** |
| `feed-types` | sí | ✅ | ✅ | ⚠ | **`COMPLETE`** |
| `vaccines` | sí | ✅ | ✅ | ⚠ | **`COMPLETE`** |
| `mortality-causes` | sí | ✅ | ✅ | ⚠ | **`COMPLETE`** |
| `transports` | sí | ✅ | ✅ | ⚠ | **`COMPLETE`** |
| `processing-plants` | sí | ✅ | ✅ | ⚠ | **`COMPLETE`** |
| **`incubators`** | por uso (§4) | **sin `PUT`** | **ninguno** | — | **`BACKEND_COMPLETE_UI_MISSING`** + `MISSING_UPDATE_CAPABILITY` |
| **`hatchers`** | sí (Alta) | **sin `PUT`** | **ninguno** | — | ídem |
| **`productive-phases`** | sí (Alta) | **sin `PUT`** | **ninguno** | — | ídem |
| **`medications`** | sí (Media) | **sin `PUT`** | **ninguno** | — | ídem |
| **`cull-causes`** | sí (Alta) | **sin `PUT`** | **ninguno** | — | ídem |
| **`rejection-reasons`** | sí (Alta) | **sin `PUT`** | **ninguno** | — | ídem |
| **`correction-types`** | sí (Alta) | **sin `PUT`** | **ninguno** | — | ídem |
| `BirdTypeEnum` | sí (Alta) | — | — | — | **`SYSTEM_MANAGED`** |
| `EventStatus` | sí (Crítica) | — | — | — | **`SYSTEM_MANAGED`** |

## La dimensión real

```
UI_MISSING = 7        (y la hipótesis, esta vez, se confirma)
```

Pero con dos matices que cambian el trabajo:

**1 · No son siete pantallas.** La administración de maestros está parametrizada: una sola
`MasterListPage` y una lista de entidades que genera las rutas. Añadir un catálogo es añadir
una entrada, no escribir una pantalla.

**2 · No es solo interfaz.** Los mismos siete carecen de esquema de actualización, así que ni
siquiera por API pueden editarse. Exponerlos con un botón «editar» que devolviera `405` sería
peor que no exponerlos.

## Los tres huecos reales

| | Hallazgo | Sev. |
|---|---|:--:|
| 1 | **`R-90`** · siete maestros normativos sin capacidad de gestión en la interfaz | **P1** |
| 2 | **`R-91`** · esos mismos siete no admiten edición: sin esquema, no hay `PUT` | P2 |
| 3 | **`R-89`** · el listado descarta el total y el contador muestra el tamaño de página | P2 |

`R-90` es **P1** y no cosmético: `productive-phases` gobierna la fase productiva de un lote,
`cull-causes` es obligatoria al registrar un descarte y `correction-types` al corregir. Sin
pantalla, esos catálogos solo pueden poblarse por API o por SQL — que es como están hoy en el
entorno compartido.

## Lo que **no** se hará

- No se construirá una «máquina genérica de maestros»: ya existe y funciona.
- No se tocará el backend de los doce que están completos.
- No se añadirá borrado físico: el ciclo es baja lógica.
- No se harán editables `BirdTypeEnum` ni `EventStatus`: gobiernan la lógica del proceso.

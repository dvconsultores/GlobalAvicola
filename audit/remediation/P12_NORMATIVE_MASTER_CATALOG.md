# `P-12` · CATÁLOGO NORMATIVO DE MAESTROS

Fase de análisis · 2026-09-06 · sin desarrollo

Se parte de `docs/02 §3.2`, no de las tablas ni de las rutas.

---

## 1. Catálogos base (`§3.2.1`)

| Maestro normativo | Prioridad | Entidad | ¿Gestionable por usuario? | Ciclo de vida exigido |
|---|:--:|---|:--:|---|
| Empresas | Alta | `companies` | sí | alta · consulta · edición · baja lógica |
| Granjas | **Crítica** | `farms` | sí | ídem |
| Galpones | **Crítica** | `houses` | sí | ídem |
| Incubadoras | **Crítica** | `hatcheries` | sí | ídem |
| **Nacedoras** | Alta | `hatchers` | sí | ídem |
| Líneas Genéticas | Alta | `genetic-lines` | sí | ídem |
| Razas | Alta | `breeds` | sí | ídem |
| **Tipos de Ave** | Alta | `BirdTypeEnum` | **no** — §3 | — |
| **Fases Productivas** | Alta | `productive-phases` | sí | ídem |
| Proveedores | Alta | `suppliers` | sí | ídem |
| Tipos de Alimento | Alta | `feed-types` | sí | ídem |
| Vacunas | Alta | `vaccines` | sí | ídem |
| **Medicamentos** | Media | `medications` | sí | ídem |
| Causas de Mortalidad | Alta | `mortality-causes` | sí | ídem |
| **Causas de Descarte** | Alta | `cull-causes` | sí | ídem |
| Transportes | Media | `transports` | sí | ídem |
| Plantas de Beneficio | Media | `processing-plants` | sí | ídem |

## 2. Maestros de flujo (`§3.2.2`)

| Maestro normativo | Prioridad | Entidad | ¿Gestionable? |
|---|:--:|---|:--:|
| **Estados de Registro** | Crítica | `EventStatus` | **no** — §3 |
| **Motivos de Rechazo** | Alta | `rejection-reasons` | sí, «catálogo **configurable**» |
| **Tipos de Corrección** | Alta | `correction-types` | sí |

```
20 maestros normativos · 18 gestionables por usuario · 2 del sistema
```

## 3. Los dos que **no** son catálogos de usuario

**Tipos de Ave** y **Estados de Registro** figuran en `§3.2` pero están implementados como
enumeraciones (`BirdTypeEnum`, `EventStatus`), y con razón: **gobiernan la lógica del
proceso**. El tipo de ave selecciona la cadena productiva y el estado gobierna el flujo de
revisión y aprobación. Hacerlos editables permitiría crear un valor que ninguna rama del
código sabe atender.

```
Clasificación · SYSTEM_MANAGED
```

Es una divergencia consciente respecto de `§3.2`, no un hueco: se registra y **no** se
convierte en desarrollo.

## 4. `Incubator`, la entidad que no aparece en la lista

`docs/02` describe «Incubadoras» con *«Nombre, **empresa**, ubicación, capacidad»* — que es
`Hatchery` (`company_id`, `name`, `code`, `location`), no `Incubator` (`hatchery_id`, `name`,
`capacity`). Y «Nacedoras» con *«Nombre, **incubadora**, capacidad»* → `Hatcher`.

`Incubator` es la máquina dentro de la planta: **no está en `§3.2.1`**, pero
`HatcheryParams.incubator_id` la referencia y el proceso de incubación —`P-05`, certificado—
la usa. Un operador debe poder crearla.

```
Clasificación · REQUERIDA POR USO, no por enumeración
```

## 5. Ciclo de vida: baja lógica, no borrado

Los **19** modelos de maestros declaran `is_active`, y el CRUD genérico expone `DELETE` que
llama a `deactivate_item`. **No hay borrado físico en ninguna parte.**

```
El ciclo normativo es:  alta · consulta · edición · BAJA LÓGICA
```

No se introduce borrado físico ni cascadas: nada lo pide y el diseño vigente lo evita a
propósito.

# DATOS EXISTENTES: ¿SE PUEDEN CLASIFICAR POR UNIDAD?

Auditoría del 2026-09-07 · **solo lectura**

---

## 1. La pregunta

Si mañana existiera el modelo de unidades, ¿se podría decir de cada fila ya guardada a qué
unidad pertenece? `§63` prohíbe adivinarlo.

## 2. La matriz

| Entity | Existing Rows | Module Derivable? | Source | Ambiguous? | Migration Risk |
|---|---|:--:|---|:--:|:--:|
| `lots` | sí | **parcialmente** | `bird_type` | **sí, si es nulo** | **ALTO** |
| `operational_events` **con** lote | sí | sí | `lot_id → bird_type` | si el lote no lo tiene | **MEDIO** |
| `operational_events` **sin** lote | sí | **NO** | — | **sí, siempre** | **BLOQUEANTE** |
| `bird_movements`, `egg_movements`, `feed_movements` | sí | vía evento | cadena | hereda la ambigüedad | MEDIO |
| `inspection_details` | sí | **a menudo NO** | evento sin lote | **sí** | **BLOQUEANTE** |
| `hatchery_params` | sí | por su naturaleza, Incubadora | inferencia | **sí, es inferencia** | MEDIO |
| `operational_alerts` | sí | vía `lot_id` | cadena | si el lote no lo tiene | MEDIO |
| `notifications` | sí | vía entidad relacionada | cadena | sí | MEDIO |
| `audit_logs` | sí | vía `lot_id` nulable | cadena | **sí, mayoritariamente** | **ALTO** |
| `egg_batches`, `chick_batches` | sí | **cruzan** | `generation` | **por diseño** | **BLOQUEANTE** |
| `consolidated_movements` | sí | vía `lot_id` | cadena | poco | BAJO |
| maestros | sí | los cuatro específicos, sí | naturaleza | el resto es transversal | BAJO |
| **`users`** | sí | **NO** | — | **sí, siempre** | **DECISIÓN** |

## 3. Los tres bloqueantes

**Eventos sin lote.** No hay dato del que derivar la unidad. Ni hoy ni retroactivamente.

**Inspecciones.** Mismo caso, y son numerosas: `farm_inspection` es el primer paso de casi todas
las cadenas.

**Lotes de huevo y de pollito.** Pertenecen a dos unidades a la vez **por diseño**. Asignarles
una sería falsear la trazabilidad que `P-10` certifica.

## 4. Los usuarios: no es un problema de datos, es una decisión

```
¿Qué módulos recibe un usuario existente tras la migración?

  A) todos los que su empresa tenga habilitados
     → nadie pierde acceso, pero el aislamiento nace desactivado
  B) ninguno
     → seguro por defecto, pero todo el mundo se queda fuera hasta que alguien configure
  C) derivados de su historial de actividad
     → adivinar, y `§64` lo prohíbe
```

Ninguna es obviamente correcta. `A` es amable y no aísla nada; `B` es correcta y deja la
operación parada el lunes por la mañana. **Es decisión del propietario.**

## 5. Sobre `fail closed`

`§66` recomienda que lo desconocido se deniegue. Aplicado al legado, eso significa que las filas
sin unidad derivable **desaparecerían para todos** — incluidas todas las inspecciones. Es la
opción segura y la más disruptiva a la vez.

La tensión entre `§66` (denegar lo desconocido) y la realidad del legado (mucho es desconocido)
es el riesgo principal de esta capacidad, y no se resuelve con más auditoría.

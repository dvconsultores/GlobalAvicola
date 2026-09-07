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
| `egg_batches`, `chick_batches` | sí | **sí, por los dos lados** | columnas de origen y destino | **no: son bilaterales** | BAJO · ~~BLOQUEANTE~~ *(§6)* |
| `consolidated_movements` | sí | vía `lot_id` | cadena | poco | BAJO |
| maestros | sí | los cuatro específicos, sí | naturaleza | el resto es transversal | BAJO |
| **`users`** | sí | **NO** | — | **sí, siempre** | **DECISIÓN** |

## 3. Los tres bloqueantes

**Eventos sin lote.** No hay dato del que derivar la unidad. Ni hoy ni retroactivamente.

**Inspecciones.** Mismo caso, y son numerosas: `farm_inspection` es el primer paso de casi todas
las cadenas.

**Lotes de huevo y de pollito.** ~~Pertenecen a dos unidades a la vez **por diseño**. Asignarles
una sería falsear la trazabilidad que `P-10` certifica.~~

> **SUPERADO · 2026-09-07 · ver `§6`.** No son ambiguos: son **bilaterales**. Llevan una columna
> por cada lado, de modo que la fila **es** el traspaso y no hay propiedad única que decidir.
> **No es bloqueante.** Los bloqueantes de datos de esta sección quedan en **dos** —eventos sin
> lote e inspecciones—, que además son el mismo.

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

Ninguna es obviamente correcta. `A` es amable y no aísla nada; `B` es correcta y ~~deja la
operación parada el lunes por la mañana~~. **Es decisión del propietario.**

> **ACOTADO · 2026-09-07 · ver `§6`.** `ENV-01` establece que no hay producción real desplegada
> y que los usuarios actuales son de desarrollo y certificación: **no hay operación que parar**.
> La decisión sigue haciendo falta, pero **no bloquea el diseño de la spec**; bloquea el alta del
> primer cliente real.

## 5. Sobre `fail closed`

`§66` recomienda que lo desconocido se deniegue. Aplicado al legado, eso significa que las filas
sin unidad derivable **desaparecerían para todos** — incluidas todas las inspecciones. Es la
opción segura y la más disruptiva a la vez.

La tensión entre `§66` (denegar lo desconocido) y la realidad del legado (mucho es desconocido)
es el riesgo principal de esta capacidad, y no se resuelve con más auditoría.

---

## 6. Corrección · 2026-09-07

Al preparar `BUSINESS_UNIT_OWNER_DECISION_DOSSIER.md` se contrastaron dos afirmaciones de este
documento contra el modelo y contra `ENV-01`. Las dos resultaron inexactas y se corrigen aquí:

**`§3`, «lotes de huevo y de pollito».** Se marcaron `BLOQUEANTE` por «pertenecer a dos unidades
a la vez por diseño». No es así: `egg_batches` y `chick_batches` llevan **una columna por cada
lado** (`source_lot_id` / `hatchery_lot_id` y `hatchery_lot_id` / `destination_lot_id`). No hay
que decidir de quién es la fila — la fila **es** el traspaso. **No son bloqueantes y no necesitan
columna de unidad.** Ver `BUSINESS_UNIT_CROSS_FLOW_DECISION_MATRIX.md §2.1`.

**`§2`, «lotes sin `bird_type`».** El tipo de ave está también en `Breed`, y `Lot.breed_id` la
referencia. Existe por tanto una segunda vía de derivación que este documento no consideró.
Reduce el volumen de lo inclasificable, pero es **inferencia de negocio** y requiere ratificación.

**`§4`, usuarios existentes.** `ENV-01` —vigente, del propietario— establece que no hay
producción real desplegada y que los usuarios actuales son de desarrollo y certificación. El
riesgo descrito («la operación parada el lunes por la mañana») **no aplica hoy**; la decisión pasa
a bloquear el alta del primer cliente real. Ver
`BUSINESS_UNIT_LEGACY_MIGRATION_DECISION_MATRIX.md §1`.

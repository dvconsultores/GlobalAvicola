# FILAS COMPARTIDAS: ¿DE QUÉ UNIDAD ES CADA UNA?

Auditoría del 2026-09-07 · **documento crítico** · solo lectura

---

## 1. Por qué este documento es el más importante

Esconder pantallas es fácil. Lo difícil es que una consulta que hoy devuelve «los lotes de la
empresa» pase a devolver «los lotes de la empresa **y de las unidades del usuario**». Para eso
cada fila tiene que saber de qué unidad es — y hoy casi ninguna lo sabe.

## 2. La matriz

| Entity | Rows Can Belong to Multiple Modules? | Current Discriminator | Reliable? | Missing Field? | Leakage Risk |
|---|:--:|---|:--:|:--:|:--:|
| **`lots`** | **sí** | `bird_type` | **no — nulable** | reforzarlo o no confiar | **P0** |
| **`operational_events`** | **sí** | `lot_id → Lot.bird_type` | **no — `lot_id` nulable** | **sí** | **P0** |
| `bird_movements` | sí | vía evento | no | sí | **P0** |
| `egg_movements` | sí | vía evento | no | sí | **P0** |
| `feed_movements` | sí | vía evento | no | sí | **P1** |
| `inspection_details` | sí | vía evento; **el evento puede no tener lote** | **no** | sí | **P1** |
| `hatchery_params` | en la práctica solo Incubadora | vía evento | no | sí | **P1** |
| `operational_alerts` | sí | `lot_id` | parcial | sí | **P1** |
| `notifications` | sí | `related_entity_*` → lote | **no** | sí | **P1** |
| `audit_logs` | sí | `lot_id` nulable | **no** | decisión | **P1** |
| `egg_batches` | **cruzan por diseño** | `generation` | parcial | contrato | **P0** |
| `chick_batches` | **cruzan por diseño** | `generation` | parcial | contrato | **P0** |
| `consolidated_movements` | sí | `lot_id` | parcial | sí | **P1** |
| `approval_actions` | sí | vía evento | no | sí | **P1** |
| `correction_logs` | sí | vía evento | no | sí | **P1** |
| `lot_phases`, `opening_balances` | sí | `lot_id` | sí | no | **P2** |

## 3. Los tres casos sin salida limpia

**Eventos sin lote.** `farm_inspection` y `hatchery_inspection` tienen `lot_id` nulo por
decisión de esquema (`i9j0k1l2m3n4`). No hay forma de derivar su unidad. Las opciones —dejarlos
visibles para todos, ocultarlos a todos, o darles unidad propia— son **decisión de negocio**, no
técnica.

**Lotes sin `bird_type`.** El campo es nulable. Con `fail closed` desaparecerían para todos; con
`fail open` serían un agujero permanente.

**Lotes de huevo y de pollito.** `egg_batches` y `chick_batches` existen **para** cruzar la
frontera: Reproductoras produce el huevo que Incubadora recibe. Filtrarlos por unidad rompería
`P-10`. Aquí no falta un campo: falta un **contrato** que diga qué ve cada lado.

## 4. Lo que esto implica para la implementación futura

```
WHERE company_id = :empresa                       ← lo que hay hoy
WHERE company_id = :empresa
  AND unidad IN :unidades_efectivas_del_usuario   ← lo que haría falta
```

La segunda línea necesita que `unidad` **esté en la fila** o sea alcanzable con un `JOIN`
determinista. Hoy no lo es en catorce de las dieciséis entidades de esta matriz.

Añadir la columna a cada tabla la duplicaría en catorce sitios y abriría la puerta a que se
desincronicen. Derivarla siempre por `JOIN` obliga a que **todas** las consultas pasen por el
lote, incluidas las de los submovimientos. Es la decisión de diseño central de esta capacidad, y
esta auditoría la deja planteada sin resolverla.

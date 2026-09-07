# ENTIDADES FRENTE A UNIDAD DE NEGOCIO

Auditoría del 2026-09-07 · 51 tablas · **solo lectura**

---

## 1. El recuento de partida

```
tablas totales ............... 51
con `company_id` ............. 29     la tenencia de empresa está resuelta
sin `company_id` ............. 22     heredan del padre, o son de plataforma

con discriminador de UNIDAD ...  2    `lots.bird_type` y `breeds.bird_type`
```

**Dos de cincuenta y una.** Y una de ellas —`breeds`— es un catálogo, no un dato operativo.

## 2. La matriz

| Entity/Table | Unidad | Shared? | Row-Level Module Field Exists? | Company Scope | Risk |
|---|---|:--:|:--:|:--:|:--:|
| **`lots`** | derivable | **sí** | **`bird_type`, NULABLE** | sí | **P0** |
| **`operational_events`** | solo vía `lot_id` | **sí** | **no** | sí | **P0** |
| `bird_movements` | vía evento → lote | sí | no | **no** | **P0** |
| `egg_movements` | vía evento → lote | sí | no | no | **P0** |
| `feed_movements` | vía evento → lote | sí | no | no | **P1** |
| `inspection_details` | vía evento → lote | sí | no | no | **P1** |
| `hatchery_params` | Incubadora | sí | no | no | **P1** |
| `egg_storage` | vía evento | sí | no | no | **P1** |
| `operational_alerts` | vía lote | sí | no | sí | **P1** |
| **`notifications`** | vía entidad relacionada | **sí** | **no** | sí | **P1** |
| **`audit_logs`** | vía `lot_id`, nulable | **sí** | **no** | sí | **P1** — decisión pendiente |
| `egg_batches`, `chick_batches` | **cruzan unidades** | sí | parcial (`generation`) | no | **P0** — ver flujos |
| `consolidated_movements` | vía `lot_id` | sí | no | sí | **P1** |
| `sap_payloads`, `sap_responses` | vía consolidado | sí | no | sí/no | **P2** |
| `approval_actions`, `review_batches` | multi | sí | no | no/sí | **P1** |
| `correction_logs` | vía evento | sí | no | no | **P1** |
| `lot_phases`, `opening_balances` | vía lote | sí | no | no | **P1** |
| `breeds` | **`bird_type`** | no | **sí** | no | P2 |
| `houses`, `incubators`, `hatchers` | por su padre | parcial | no | no | P2 |
| `farms`, `hatcheries` | mixta | parcial | no | sí | P2 |
| `genetic_lines`, `genetic_weight_curves(_points)` | mixta | sí | no | sí/no | P2 |
| `feed_types`, `vaccines`, `medications`, `mortality_causes`, `cull_causes`, `transports`, `processing_plants`, `rejection_reasons`, `correction_types`, `suppliers` | transversal | sí | no | sí | P3 |
| `productive_phases` | transversal | sí | no | **no** | P3 |
| `areas` | transversal | no | no | sí | — |
| `companies`, `users`, `roles`, `permissions` | — | — | — | — | — |
| `sap_references`, `sap_sync_jobs` | multi | sí | no | sí | P2 |
| `alembic_version` | — | — | — | — | — |

## 3. Los dos hallazgos que gobiernan todo lo demás

**`operational_events` no sabe de qué unidad es.** Su unidad solo se deduce por
`lot_id → Lot.bird_type`, y `lot_id` **es nulable** desde `i9j0k1l2m3n4`: las inspecciones de
granja e incubadora no tienen lote. Para esas filas **no hay unidad derivable en absoluto**.

**`lots.bird_type` es nulable.** Un lote sin `bird_type` no pertenece a ninguna unidad, y el
esquema lo permite hoy. Cualquier filtro futuro tendría que decidir qué hacer con esas filas —y
la respuesta segura, `fail closed`, las ocultaría a todo el mundo.

## 4. Los submovimientos no tienen tenencia propia

`bird_movements`, `egg_movements`, `feed_movements`, `inspection_details`, `hatchery_params` y
`egg_storage` **no tienen `company_id`**: la heredan de su evento. Eso funciona hoy porque todas
las consultas entran por el evento, pero significa que un filtro por unidad tendría que
propagarse por la misma vía —y cualquier consulta que ataque el submovimiento directamente se
salta las dos capas a la vez.

# TENANT RESOURCE CLASSIFICATION

**Fecha** 2026-09-04 · **Wave** 3 · **Spec** `GA-REM-016` (gate) · `GA-REM-002 AC10`

Antes de exigir pertenencia hay que saber **de quién** es cada cosa. Aplicar un filtro de
compañía a una entidad global sería tan defectuoso como no aplicarlo a una que sí lo es.

---

## 1. Ámbitos

| Ámbito | Significado |
|---|---|
| `TENANT_SCOPED` | Pertenece a una empresa. Una referencia ajena es una violación |
| `GLOBAL` | Compartido por todas las empresas. Filtrarlo rompería el producto |
| `SYSTEM` | Infraestructura, sin dueño de negocio |

---

## 2. Clasificación — 47 tablas

### `TENANT_SCOPED` con `company_id` obligatorio (10)

| Resource | Scope | Company Field | Parent/FK | Ownership Rule |
|---|---|---|---|---|
| `operational_events` | `TENANT_SCOPED` | `company_id` obligatorio | `lot_id`, `farm_id`, `house_id` | **el evento y todas sus referencias** deben ser de la empresa |
| `farms` | `TENANT_SCOPED` | obligatorio | — | raíz de la estructura física |
| `hatcheries` | `TENANT_SCOPED` | obligatorio | — | ídem |
| `evidences` | `TENANT_SCOPED` | obligatorio | `event_id` | hereda del evento |
| `operational_alerts` | `TENANT_SCOPED` | obligatorio | `lot_id` | hereda del lote |
| `review_batches` · `consolidated_movements` · `reversals` | `TENANT_SCOPED` | obligatorio | eventos | heredan |
| `sap_payloads` · `sap_references` · `sap_sync_jobs` | `TENANT_SCOPED` | obligatorio | — | frontera SAP por empresa |

### `TENANT_SCOPED` por su padre (12)

| Resource | Parent/FK | Ownership Rule |
|---|---|---|
| `houses` | `farm_id` | **no declara `company_id`**: pertenece a la empresa *a través de su granja*. Es el caso que `R-59` destapó |
| `bird_movements` · `egg_movements` · `feed_movements` · `hatchery_params` · `inspection_details` · `egg_storage` | `event_id` | heredan del evento; el cliente no los referencia por id |
| `correction_logs` | `event_id` | hereda |
| `lot_phases` · `opening_balances` | `lot_id` | heredan |
| `egg_batches` · `chick_batches` | `source_lot_id`, `hatchery_lot_id` | **dos lotes distintos** (`RR-02`, `RR-04`) |

### `TENANT_SCOPED` con `company_id` anulable — catálogos compartibles (13)

`suppliers`, `feed_types`, `vaccines`, `medications`, `mortality_causes`, `cull_causes`,
`transports`, `processing_plants`, `genetic_lines`, `correction_types`,
`rejection_reasons`, `lots`, `roles`.

**Regla distinta, y deliberada.** `company_id` anulable significa «global si es nulo, propio
de la empresa si está fijado». Bloquear la referencia a un catálogo compartido sería un
defecto, no una protección.

> `lots` figura aquí por su columna, pero **se trata como tenant-scoped estricto**: es la
> raíz del inventario y la referencia que `R-42` explotó. La consulta de pertenencia lo
> filtra siempre.

### `GLOBAL` (6)

`companies`, `breeds`, `hatchers`, `incubators`, `productive_phases`, `sap_responses`.

Catálogos de dominio o de referencia sin dueño. **No se les añade filtro de compañía**: la
raza *Ross 308* es la misma para todos.

### `SYSTEM` (2)

`permissions`, `alembic_version`.

---

## 3. Claves foráneas enviables por el cliente

**22 tenant-scoped** de 26 descubiertas por introspección de los esquemas de escritura.
No todas requieren la misma regla:

| Clave | Destino | Regla | Estado |
|---|---|---|---|
| `lot_id` | `lots` | **pertenencia obligatoria** | ✅ `R-42` |
| `farm_id` | `farms` | **pertenencia obligatoria** | ✅ Wave 3 |
| `house_id` | `houses` | **pertenencia vía granja** | ✅ Wave 3 |
| `destination_farm_id` | `farms` | **pertenencia obligatoria** | ✅ Wave 3 |
| `event_id` | `operational_events` | **pertenencia obligatoria** | ✅ heredada del servicio |
| `hatchery_id` | `hatcheries` | **pertenencia obligatoria** | ✅ Wave 3 (`R-59`) |
| `source_lot_id`, `hatchery_lot_id`, `broiler_lot_id`, `destination_lot_id` | `lots` | pertenencia deseable | ⚠ `R-60` |
| `dispatch_event_id`, `egg_batch_id` | eventos y lotes de huevo | pertenencia deseable | ⚠ `R-60` |
| `cause_id`, `cull_cause_id`, `vaccine_id`, `medication_id`, `supplier_id`, `transport_id`, `destination_plant_id`, `feed_type_id`, `genetic_line_id`, `correction_type_id` | catálogos | **sin filtro**: `company_id` anulable admite el uso compartido | por diseño |
| `role_id` | `roles` | administración; solo Super Admin | por diseño |
| `company_id`, `breed_id`, `phase_id` | globales | sin filtro | por diseño |

---

## 4. `R-60` — pendiente, acotado

Las claves de trazabilidad (`source_lot_id`, `hatchery_lot_id`, `broiler_lot_id`,
`destination_lot_id`, `dispatch_event_id`, `egg_batch_id`) no comprueban pertenencia.

**Exposición real:** los endpoints de enlace manual (`POST /lots/egg-batches`,
`/chick-batches`) exigen `lots:create`, exclusivo del Super Admin, que opera legítimamente
entre compañías. **No es explotable por ningún otro rol.**

Severidad P2, trazado a `GA-REM-008`. Se documenta en lugar de corregirse porque el proceso
de trazabilidad no se certifica en esta Wave y arreglarlo aquí sería trabajo fuera de la
spec activa.

---

## 5. Principio

```
READ ISOLATION  ≠  WRITE ISOLATION
```

Y sobre todo:

```
existir  ≠  pertenecer
```

Un recurso ajeno debe comportarse como **inexistente**: distinguir «no existe» de «no es
tuyo» ya filtra información.

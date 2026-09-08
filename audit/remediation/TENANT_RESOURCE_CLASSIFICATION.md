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


---

## Enmienda · la superficie de administración (2026-09-08)

Esta clasificación se construyó desde el modelo de datos **operativo** y por eso omitía la
administración. La omisión no fue inocua: `AC05` exigía acotar «un recurso de la compañía B» y
`users` es uno, pero al no figurar aquí el filtro nunca se implementó. Cuatro `P0`.

| Tabla | Clase | Clave de inquilino | Aplica en |
|---|---|---|---|
| `users` | **RECURSO DE INQUILINO** | `users.company_id` | listar · detalle · edición · alta |
| `roles` | pendiente de decisión | `roles.company_id` existe y **no se usa** | `R-121` |
| `companies` | el inquilino mismo | `companies.id` | `R-115`, sin remediar todavía |

**La lección de método:** una `AC` correcta y una lista de aplicación incompleta producen
exactamente el mismo agujero que no tener la `AC`. Toda superficie que devuelva o mute filas con
`company_id` pertenece a esta tabla, la haya pedido alguien o no.


---

# INVENTARIO COMPLETO E INDEPENDIENTE (2026-09-08)

## 1. Por qué se rehace desde cero

La lista anterior de este documento se construyó **desde el modelo operativo**: alguien recorrió
lotes, eventos, granjas y evidencias, y clasificó lo que encontró. Era una lista de lo que se
miró, no del universo.

```
`AC05` CORRECTA  +  LISTA DE APLICACIÓN INCOMPLETA  =  SEGURIDAD INCOMPLETA
```

Coste medido: `users` fuera → cuatro `P0` (`R-114`, `R-117`, `R-118`).
`companies` fuera → `R-115`. El caso «sin empresa» sin decidir → `R-116`.

Por eso este inventario **no parte de la lista vieja**. Se deriva de `Base.metadata`, es decir
de las tablas que el producto declara realmente, y luego se reconcilia contra lo que había.

## 2. Método reproducible

```
1. enumerar TODAS las tablas de `Base.metadata`          → 54
2. para cada una: ¿tiene `company_id`?                   → 30 sí · 24 no
3. de las que no: ¿hereda inquilino por clave foránea?   → 18 sí
4. de las restantes: ¿es el inquilino mismo?             → `companies`
5. de las restantes: ¿es catálogo de plataforma?         → `business_units` · `productive_phases`
6. lo que quede SIN CLASIFICAR es un hallazgo            → 0
```

El paso 6 es el que importa: la clasificación **falla ruidosamente** si aparece una tabla que no
encaja, en vez de omitirla en silencio. Repetir el script tras cada migración es lo que impide
que el universo vuelva a quedarse corto.

## 3. Las 54 tablas

| Recurso | Clase | Clave de inquilino | Gobierna / estado |
|---|---|---|---|
| `approval_actions` | TENANT derivado | vía `approval_steps`, `operational_events` | `AC12` · el sub-recurso hereda del padre |
| `approval_steps` | CONTROL | `approval_steps.company_id` | `AC05` · `MasterService` / servicio propio |
| `areas` | CONTROL | `areas.company_id` | `AC05` · `MasterService` / servicio propio |
| `audit_logs` | CONTROL | `audit_logs.company_id` | `AC05` · `MasterService` / servicio propio |
| `bird_movements` | TENANT derivado | vía `breeds`, `houses` | `AC12` · el sub-recurso hereda del padre |
| `breeds` | TENANT derivado | vía `genetic_lines` | `AC12` · el sub-recurso hereda del padre |
| `business_units` | GLOBAL / PLATAFORMA | — | catálogo de producto · sin `CRUD` de cliente |
| `chick_batches` | TRASPASO entre unidades | vía lotes de ambos lados | `OD-10` · fase 5 |
| `companies` | CONTROL · **el inquilino mismo** | `companies.id` | `R-115` cerrado · `_INQUILINO_POR_IDENTIDAD` |
| `company_business_units` | CONTROL | `company_business_units.company_id` | `AC05` · `MasterService` / servicio propio |
| `consolidated_movements` | SAP · inquilino | `consolidated_movements.company_id` | `AC05` · `MasterService` / servicio propio |
| `correction_logs` | TENANT derivado | vía `correction_types`, `operational_events` | `AC12` · el sub-recurso hereda del padre |
| `correction_types` | TENANT | `correction_types.company_id` | `AC05` · `MasterService` / servicio propio |
| `cull_causes` | TENANT | `cull_causes.company_id` | `AC05` · `MasterService` / servicio propio |
| `egg_batches` | TRASPASO entre unidades | vía lotes de ambos lados | `OD-10` · fase 5 |
| `egg_movements` | TENANT derivado | vía `operational_events` | `AC12` · el sub-recurso hereda del padre |
| `egg_storage` | TENANT derivado | vía `lots`, `operational_events` | `AC12` · el sub-recurso hereda del padre |
| `evidences` | TENANT | `evidences.company_id` | `AC05` · `MasterService` / servicio propio |
| `farms` | TENANT | `farms.company_id` | `AC05` · `MasterService` / servicio propio |
| `feed_movements` | TENANT derivado | vía `feed_types`, `operational_events` | `AC12` · el sub-recurso hereda del padre |
| `feed_types` | TENANT | `feed_types.company_id` | `AC05` · `MasterService` / servicio propio |
| `genetic_lines` | TENANT | `genetic_lines.company_id` | `AC05` · `MasterService` / servicio propio |
| `genetic_weight_curve_points` | TENANT derivado | vía `curve_id`→`genetic_lines` | `GA-REM-037` |
| `genetic_weight_curves` | TENANT derivado | vía `genetic_lines` | `AC12` · el sub-recurso hereda del padre |
| `hatcheries` | TENANT | `hatcheries.company_id` | `AC05` · `MasterService` / servicio propio |
| `hatchers` | TENANT derivado | vía `hatcheries` | `AC12` · el sub-recurso hereda del padre |
| `hatchery_params` | TENANT derivado | vía `hatcheries`, `hatchers` | `AC12` · el sub-recurso hereda del padre |
| `houses` | TENANT derivado | vía `farms` | `AC12` · el sub-recurso hereda del padre |
| `incubators` | TENANT derivado | vía `hatcheries` | `AC12` · el sub-recurso hereda del padre |
| `inspection_details` | TENANT derivado | vía `houses`, `operational_events` | `AC12` · el sub-recurso hereda del padre |
| `lot_phases` | TENANT derivado | vía `lots`, `productive_phases` | `AC12` · el sub-recurso hereda del padre |
| `lots` | TENANT | `lots.company_id` | `AC05` · `MasterService` / servicio propio |
| `medications` | TENANT | `medications.company_id` | `AC05` · `MasterService` / servicio propio |
| `mortality_causes` | TENANT | `mortality_causes.company_id` | `AC05` · `MasterService` / servicio propio |
| `notifications` | TENANT | `notifications.company_id` | `AC05` · `MasterService` / servicio propio |
| `opening_balances` | TENANT derivado | vía `lots`, `productive_phases` | `AC12` · el sub-recurso hereda del padre |
| `operational_alerts` | TENANT | `operational_alerts.company_id` | `AC05` · `MasterService` / servicio propio |
| `operational_events` | TENANT | `operational_events.company_id` | `AC05` · `MasterService` / servicio propio |
| `permissions` | CONTROL derivado | vía `role_id` | hereda de `roles` · `R-121` |
| `processing_plants` | TENANT | `processing_plants.company_id` | `AC05` · `MasterService` / servicio propio |
| `productive_phases` | GLOBAL / PLATAFORMA | — | invariante del dominio |
| `rejection_reasons` | TENANT | `rejection_reasons.company_id` | `AC05` · `MasterService` / servicio propio |
| `reversals` | TENANT | `reversals.company_id` | `AC05` · `MasterService` / servicio propio |
| `review_batches` | TENANT | `review_batches.company_id` | `AC05` · `MasterService` / servicio propio |
| `roles` | CONTROL | `roles.company_id` **existe y no se usa** | `R-121` · OWNER_DECISION |
| `sap_payloads` | SAP · inquilino | `sap_payloads.company_id` | `AC05` · `MasterService` / servicio propio |
| `sap_references` | SAP · inquilino | `sap_references.company_id` | `AC05` · `MasterService` / servicio propio |
| `sap_responses` | TENANT derivado | vía `payload_id`→`sap_payloads` | `P-08` |
| `sap_sync_jobs` | SAP · inquilino | `sap_sync_jobs.company_id` | `AC05` · `MasterService` / servicio propio |
| `suppliers` | TENANT | `suppliers.company_id` | `AC05` · `MasterService` / servicio propio |
| `transports` | TENANT | `transports.company_id` | `AC05` · `MasterService` / servicio propio |
| `user_business_units` | TENANT derivado | vía `company_business_units`, `users` | `AC12` · el sub-recurso hereda del padre |
| `users` | CONTROL | `users.company_id` | `R-114` cerrado · `GA-REM-002` enm. B |
| `vaccines` | TENANT | `vaccines.company_id` | `AC05` · `MasterService` / servicio propio |

```
TENANT directo        20      `company_id` propio
TENANT derivado       18      hereda por clave foránea — `AC12`
SAP · inquilino        4      `company_id` propio, gobernado por `P-08`
CONTROL                7      plano de control con `company_id`
CONTROL derivado       1      `permissions`, vía `roles`
TRASPASO               2      `egg_batches` · `chick_batches` — `OD-10`
GLOBAL / PLATAFORMA    2      compartidos por diseño
SIN CLASIFICAR         0
```

## 4. Lo que este inventario deja al descubierto

| Recurso | Estado | Hallazgo |
|---|---|---|
| `companies` | **cerrado hoy** | `R-115` · clave de inquilino = su propio `id` |
| `users` | **cerrado** | `R-114` · `GA-REM-002` enmienda B |
| «sin empresa efectiva» | **cerrado hoy** en maestros y usuarios | `R-116` |
| `roles` | **abierto** | `R-121` · tiene `company_id` y **no se usa** · `OWNER_DECISION` |
| `permissions` | **abierto por herencia** | depende de `R-121` |

## 5. Sobre una guarda estática · `§25`

**No se construye.** Una guarda del tipo «la ruta menciona `company_id` en alguna parte» daría
falsa seguridad, que es peor que no tenerla — es exactamente el modo de fallo que acabamos de
pagar con una lista incompleta que parecía completa.

Lo que sí se puede afirmar con rigor es la **completitud del inventario**: que ninguna tabla de
`Base.metadata` quede sin clase. Eso es comprobable sin ambigüedad, y es lo que hace el paso 6.
Lo que **no** se puede afirmar estáticamente es que cada consulta aplique el predicado
correcto: eso lo demuestran las pruebas de aislamiento con su sensibilidad, recurso por recurso.

```
COMPLETITUD DEL INVENTARIO   comprobable  ·  y comprobada
APLICACIÓN DEL PREDICADO     por prueba, no por guarda estática
```

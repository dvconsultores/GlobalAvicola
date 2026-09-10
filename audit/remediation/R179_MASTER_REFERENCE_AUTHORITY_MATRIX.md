# `R-179` · Matriz de autoridad de las referencias a maestros (`R179_MASTER_REFERENCE_AUTHORITY_MATRIX`)

**WAVE B · tranche 13 · pre-flight** · 2026-09-10 · baseline `a93d4d1` · hallazgo `R-179` (registrado P3 en el tranche 12; **normalizado P1**, §6) ·
spec gobernante `GA-REM-002` (ADDENDUM Wave 3, `AC10`: «`AC05` en su dimensión de escritura») → enmienda D · **sin decisión del propietario** (§5).

> Una clave foránea válida responde «¿existe este identificador?». **No** responde «¿pertenece a la empresa del evento?».

## 1. Hallazgo exacto

> `R-179` · «referencias a maestros de otra empresa en los eventos (`supplier_id`, `transport_id`, `cause_id`, `cull_cause_id`, `vaccine_id`,
> `medication_id`, `destination_plant_id`) sin `verificar_pertenencia` en alta/edición/corrección» · `operations/service.py` · `tenancy.py` ·
> `REMEDIATION_BACKLOG.md:1412` (alta del pre-flight del tranche 12).

## 2. La semántica ya está gobernada (no se inventa)

`GA-REM-002` ADDENDUM Wave 3 enumeró **22 claves foráneas tenant-scoped enviables por el cliente**, fijó la semántica de los catálogos y acotó
deliberadamente su alcance a las **estructurales**:

> «Existir no basta. `R-42` enseñó exactamente esto para `lot_id`; la lección no se extendió al resto.» ·
> «los catálogos maestros declaran `company_id` como **anulable**, lo que significa **global si es nulo, propio de la empresa si está fijado**, y
> bloquear una referencia a un catálogo compartido sería un error» · «La ampliación cubre las referencias **estructurales** (`lot_id`, `farm_id`, `house_id`)».

De ahí sale la regla de `R-179` sin decisión nueva:

```
master.company_id IS NULL      →  catálogo compartido        →  referenciable desde cualquier empresa  (control positivo obligatorio)
master.company_id IS NOT NULL  →  catálogo propio de esa empresa  →  master.company_id == empresa efectiva del evento, o BR-07 «no encontrado»
```

Precedentes de la misma clase, ya cerrados: `R-42` (`lot_id` ajeno en escritura, P1), `R-59` (`houses.farm_id` ajeno, P1, `MULTITENANT_WRITE_ISOLATION_MATRIX:119`),
`R-111` (sub-recurso por el padre), `GA-REM-042` (proveedor y transporte **en la importación de abuelas**, tranche 12). `R-179` es el mismo defecto en el
resto de los catálogos y en las tres superficies de mutación.

## 3. Reproducción real por API (`§10`, `§16`-`§18`) — sondeo del pre-flight sobre `a93d4d1`

Escenario: empresa A (evento, lote, granja, galpón) · empresa B (los siete maestros) · actor de A con `operations:create/update` y `corrections:correct`.

```
POST /operations  {supplier_id:          <proveedor de B>}   → 201
POST /operations  {transport_id:         <transporte de B>}  → 201
POST /operations  {cause_id:             <causa de mortalidad de B>} → 201
POST /operations  {cull_cause_id:        <causa de descarte de B>}   → 201
POST /operations  {vaccine_id:           <vacuna de B>}      → 201
POST /operations  {medication_id:        <medicamento de B>} → 201
POST /operations  {destination_plant_id: <planta de B>}      → 201
PUT  /operations/{id}   {cause_id: <causa de B>}             → 200
POST /corrections       {field_name: cause_id → <de B>}      → 201
verdad persistida:  evento company_id=A  ·  suppliers.company_id=B   (fila real leída por SQL)
```

**7 de 7 familias · 3 de 3 superficies · dato productivo persistido con referencia entre empresas.** No es cierre por inspección de código: es la respuesta
de la API. (El sondeo fue temporal y se retiró; el rojo formal lo repite como prueba versionada.)

## 4. Matriz de autoridad (`§11`-`§12`)

Clases: `TENANT_OWNED_NULLABLE` = catálogo con `company_id` anulable (global si nulo, propio si fijado, `GA-REM-002` addendum) · `TENANT_DERIVED` = hereda del padre ·
`PLATFORM_GLOBAL` = sin dueño de inquilino (`RQ-03` excepción normativa) · `SAP_REFERENCE` = réplica de SAP.

| Maestro | Tabla | Campo | Referenciado desde | Fuente | Clase | ¿`company_id`? | Origen de la empresa | ¿SAP? | ¿Compartido? | ¿Misma empresa exigida? | ¿Alcance de unidad? | ¿Activo exigido? | Alta hoy | `PUT` hoy | Corrección hoy | Filtro del listado | ¿API acepta ajeno? | Regla exigida | ¿Decisión? | AC | Prueba |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Proveedores | `suppliers` | `supplier_id` | `OperationalEvent` | `docs/02 §3.2.1` · `10 §3.1` (SHARED, lleva código SAP) · `MASTER_DATA_BUSINESS_UNIT_SCOPE:52` «compartido, `company_id`, transversal» | `TENANT_OWNED_NULLABLE` | sí, anulable | propia | réplica futura (`Vendors`); **no se implementa** | sí, si `company_id IS NULL` | **sí, si está fijado** | no (`§20`: transversal; no se inventa) | no (fuera, `§19`) | ninguna | ninguna | ninguna | `_apply_company_filter` (empresa o global) | **sí (201)** | `company_id ∈ {NULL, empresa efectiva}` | no | `AC-R179-01…07` | `MAES-` |
| Transportes | `transports` | `transport_id` | ídem | `§3.2.1` · scope `:48` «compartido; el mismo camión sirve a varias» | ídem | sí, anulable | propia | no | sí | sí | no | no | ninguna | ninguna | ninguna | ídem | **sí (201)** | ídem | no | ídem | ídem |
| Causas de mortalidad | `mortality_causes` | `cause_id` | ídem | `§3.2.1` · scope `:46` | ídem | sí, anulable | propia | no | sí | sí | no | no | ninguna | ninguna | ninguna | ídem | **sí (201)** | ídem | no | ídem | ídem |
| Causas de descarte | `cull_causes` | `cull_cause_id` | ídem | `§3.2.1` · scope `:47` | ídem | sí, anulable | propia | no | sí | sí | no | no | ninguna | ninguna | ninguna | ídem | **sí (201)** | ídem | no | ídem | ídem |
| Vacunas | `vaccines` | `vaccine_id` | ídem | `§3.2.1` · scope `:44` | ídem | sí, anulable | propia | adyacente a Materiales; no implementado | sí | sí | no | no | ninguna | ninguna | ninguna | ídem | **sí (201)** | ídem | no | ídem | ídem |
| Medicamentos | `medications` | `medication_id` | ídem | `§3.2.1` · scope `:45` | ídem | sí, anulable | propia | ídem | sí | sí | no | no | ninguna | ninguna | ninguna | ídem | **sí (201)** | ídem | no | ídem | ídem |
| Plantas de beneficio | `processing_plants` | `destination_plant_id` | ídem | `§3.2.1` · scope `:49` «de una unidad · Engorde; `company_id`; **no — se deriva**» | ídem | sí, anulable | propia | no | sí | sí | **no se impone** (`§20`: el alcance de unidad se deriva, no se declara; no se inventa) | no | ninguna | ninguna | ninguna | ídem | **sí (201)** | ídem | no | ídem | ídem |
| Tipos de alimento | `feed_types` | `feed_movements[].feed_type_id` | `FeedMovement` (submovimiento del evento) | `§3.2.1` · `ENTITY_MODULE_OWNERSHIP:44` transversal | ídem | sí, anulable | propia | no | sí | sí | no | no | ninguna | n/a (submovimiento no editable) | n/a | ídem | **sí** (misma clase; no sondeado por familia, cubierto por el mismo helper) | ídem | no | `AC-R179-08` | `MAES-` |
| Incubadoras | `hatcheries` | `hatchery_params[].hatchery_id` | `HatcheryParams` | `§3.2.1` · scope: «de una unidad · Incubadora; `company_id`» | ídem | sí, anulable | propia | no | sí | sí | se deriva (no se impone aquí) | no | ninguna | n/a | n/a | ídem | **sí** | ídem | no | `AC-R179-08` | `MAES-` |
| Incubadoras (máquina) · Nacedoras | `incubators` · `hatchers` | `incubator_id` · `hatcher_id` | `HatcheryParams` | scope: «vía incubadora» | `TENANT_DERIVED` (por `hatchery_id`) | **no** | de su incubadora | no | no | sí, **por el padre** | ídem | no | ninguna | n/a | n/a | por el padre | **sí** | `hatchery.company_id ∈ {NULL, empresa}` | no | `AC-R179-09` | `MAES-` |
| Razas | `breeds` | `bird_movements[].breed_id` | `BirdMovement` | scope: «con unidad explícita (`bird_type`)»; `ENTITY_MODULE_OWNERSHIP:41` «no» tenant | `PLATFORM_GLOBAL` (sin `company_id`; cuelga de `genetic_lines`) | **no** | — | no | **sí, siempre** | **no** | — | no | ninguna | n/a | n/a | sin filtro de empresa | n/a (no hay ajeno posible) | **ninguna nueva** (control negativo: no se convierte en tenant-owned, `§68`) | no | `AC-R179-10` (control) | `MAES-` |
| Galpones origen/destino | `houses` | `bird_movements[].source_house_id` · `target_house_id` | `BirdMovement` | `GA-REM-002` addendum (`house_id` **estructural**, ya cubierto en el evento) | `TENANT_DERIVED` (por `farm_id`) | no | de su granja | no | no | **sí** | — | no | **ninguna** (el addendum cubrió `house_id` del evento, no los del submovimiento) | n/a | n/a | por la granja | **sí** | igual que `house_id` | no | **registrado `R-180`** (§7: clase estructural, no de catálogo) | — |
| Lote · granja · galpón · granja destino | `lots` · `farms` · `houses` | `lot_id` · `farm_id` · `house_id` · `destination_farm_id` | `OperationalEvent` | `R-42` · `R-59` · `GA-REM-002` addendum · `R-160`/`R-173` | estructural | sí / sí / vía granja | propia | no | no | sí | sí (unidad, `R-160`) | sí (`validate_lot_active`) | **cubierta** (`validate_lot_active`, `verificar_ubicacion`) | **cubierta** (`R-173`) | **cubierta** (`R-173`) | acotado | no | sin cambio | no | control | regresión |
| Órdenes de compra / traslado | `sap_references` | `sap_document_ref` (texto) | `OperationalEvent` | `10 §3.1` SAP-OWNED · `GA-REM-035` | `SAP_REFERENCE` | sí | propia | **sí** | no | sí (ya: `validate_oc_limit` filtra por `company_id`) | no | sí (`is_active`) | **cubierta** | **cubierta** (`R-176`) | **cubierta** | acotado | no | sin cambio | no | control | regresión |

**Excluidos por clasificación** (no son maestros del catálogo referenciados por el evento): `users` (`registered_by_id`, `reviewed_by_id`, `approved_by_id`:
plano de control, `OD-13`), `business_units` / `productive_phases` (`CONTROL_GLOBAL`, excepción normativa de `RQ-03`), `companies` (el inquilino mismo).

## 5. Puerta de decisión (`§27`)

Ninguna. La semántica de los catálogos (`company_id` nulo = compartido; fijado = propio) está escrita en `GA-REM-002` ADDENDUM Wave 3 y sostenida por
`MASTER_DATA_BUSINESS_UNIT_SCOPE_MATRIX` («compartido, `company_id`, transversal» para las seis familias) y por `MASTER_DATA_SOURCE_OF_TRUTH_MATRIX`.
El **alcance de unidad** de plantas e incubadoras «se deriva, no se declara» (misma matriz): no se impone restricción de unidad (`§20`). El **estado activo**
queda fuera (`§19`: ninguna fuente lo exige para referenciar). `R-179` es por tanto **gobernado y ejecutable en su totalidad**, sin `OWNER_DECISION_REQUIRED`.

## 6. Severidad normalizada (`§26`)

| Criterio | Evidencia |
|---|---|
| ¿Se persiste dato productivo con referencia entre empresas? | **sí** (7 familias × 3 superficies, fila leída por SQL) |
| ¿Rompe el aislamiento de inquilino declarado? | sí — contradice la semántica que `GA-REM-002` addendum fijó y que `RQ-03 COMPLETE` presupone |
| ¿Contamina saldos o datos de la otra empresa? | **no** (el evento es de A; el catálogo de B solo se referencia) |
| Precedentes de la misma clase | `R-42` (P1), `R-59` (P1) — «un maestro hijo admitía un padre de otra empresa» |
| Impacto | atribución de proveedor/transporte/vacuna/causa/planta errónea, informes y auditoría con referencias ajenas, ambigüedad futura de correspondencia SAP |

→ **`P1`** (era P3 en el alta del tranche 12, antes de la reproducción). Una sola severidad, con evidencia.

## 7. Registrado en este pre-flight (fuera del alcance)

| ID | P | Hallazgo | Dónde | Por qué fuera |
|---|---|---|---|---|
| `R-180` | P2 | `bird_movements.source_house_id` / `target_house_id` admiten galpones de otra empresa: el ADDENDUM Wave 3 cubrió `house_id` **del evento**, no los del submovimiento (clase **estructural**, no de catálogo: su regla es la de `R-59`/`house_id`, sin la excepción «nulo = compartido») | `operations/service.py` · `schemas.py:19-20` | clase distinta (estructural vs catálogo) y regla distinta (sin caso compartido); mezclarla difuminaría la regla de `R-179` |

## 8. AC → prueba (contrato completo en `GA-REM-002` enmienda D)

| AC | Criterio | Prueba (`tests/test_master_reference_tenancy.py`, prefijo `MAES-`) |
|---|---|---|
| `AC-R179-01` | control: evento de A con maestro **de A** (las siete familias) → `201`; FK persistida | `_01` |
| `AC-R179-02` | alta con maestro de B (las siete familias, una a una) → `400 BR-07` «no encontrado»; cero filas, cero auditoría de alta | `_02` |
| `AC-R179-03` | `PUT` de la FK a un maestro de B → `400 BR-07`; FK original intacta, sin auditoría de éxito | `_03` |
| `AC-R179-04` | `POST /corrections` de la FK a un maestro de B → `400 BR-07`; sin `correction_logs` | `_04` |
| `AC-R179-05` | toda denegación deja el evento intacto (FK, estado, versión) y sin efecto | en cada prueba |
| `AC-R179-06` | **control positivo**: maestro **compartido** (`company_id IS NULL`) referenciado desde A → `201` (y desde B → `201`) | `_06` |
| `AC-R179-07` | suplantación: el actor de A declara `company_id` de B en el token/carga → sigue denegado; la empresa la deriva el servidor | `_07` |
| `AC-R179-08` | submovimientos: `feed_type_id` y `hatchery_id` de B → `400 BR-07` | `_08` |
| `AC-R179-09` | `incubator_id` / `hatcher_id` cuya incubadora es de B → `400 BR-07` (pertenencia por el padre) | `_09` |
| `AC-R179-10` | control negativo: `breed_id` (sin `company_id`, global) sigue aceptándose desde cualquier empresa | `_10` |
| `AC-R179-11` | `R-152`/`GA-REM-042` intacto: la importación sigue exigiendo proveedor y transporte de la empresa | regresión |
| `AC-R179-12` | actor global situado en A: mismo contrato (maestro de B denegado; compartido aceptado) | `_12` |

Sensibilidad: `R179-S1` (quitar la validación de pertenencia para una familia) · `R179-S2` (solo en el alta) · `R179-S3` (solo en `PUT`) · `R179-S4` (solo en
corrección) · `R179-S5` (**sobre-bloqueo**: exigir misma empresa también al catálogo compartido → `AC-R179-06` roja) · `R179-S6` (confiar en la empresa
declarada por el cliente → `AC-R179-07` roja).

## 9. Cierre (2026-09-10)

`R-179` CERRADO (técnico) · P1 · `GA-REM-002-D` certificada · `AC-R179-01…12` verdes · sensibilidad 5 válidas + `S6` N/A con evidencia · evidencia `WAVE_B_TRANCHE_13_MASTER_TENANCY_AND_REVIEW_CONCURRENCY_EVIDENCE.md`.

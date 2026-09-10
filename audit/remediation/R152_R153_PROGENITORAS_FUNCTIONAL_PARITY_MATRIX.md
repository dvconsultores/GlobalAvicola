# Progenitoras · Matriz de paridad funcional (`R152_R153_PROGENITORAS_FUNCTIONAL_PARITY_MATRIX`)

**WAVE B · tranche 12 · pre-flight** · 2026-09-10 · **Progenitoras ≠ Reproductoras**: cada capacidad se clasifica por fuente, no por parecido.
Clases: `IDENTICAL_CONTRACT` · `SHARED_PRIMITIVE_DIFFERENT_RULE` · `PROGENITORAS_SPECIFIC` · `REPRODUCTORAS_SPECIFIC` · `NOT_APPLICABLE` ·
`OWNER_DECISION_REQUIRED`. Fuentes: `spec.md §4.4` (15 `event_type` de Progenitoras) vs `§4.5/§4.6` (Reproductoras) · `docs/02 §3.4` vs `§3.5/§3.6` ·
`Bases`/`Rec. central` (Reproductoras, Incubadora, Engorde: **sin sección de Progenitoras**, `GA_REM_021_B05 :22`) · `GA-REM-040 §2` · `OD-16`.

## 1. Procesos afectados (`§15`)

| Proceso | Nombre | Entrada | Operador | Recursos | Eventos | Salidas | Traspasos | Aguas abajo | Frontera SAP |
|---|---|---|---|---|---|---|---|---|---|
| `P-01` | Progenitoras — Cría | lote `grandparent` activo (hoy creado a mano) | operador con concesión `grandparent` | granja, galpón, proveedor, transporte, OC (`SapReference`) | `grandparent_import` (**`R-152`**), `farm_inspection`, `transport_inspection`, `bird_reception`, `bird_distribution`, `feed_registration`, `weight_recording`, `mortality_recording`, `cull_recording`, `vaccination`, `medication`, `bird_exit` | población del lote (por `bird_reception`), historial documental de la importación | ninguno | `P-02` (producción), `P-10` (trazabilidad hacia Reproductoras) | OC de importación = `SapReference` réplica; sin envío (`P-08` diferido) |
| `P-01` paso 0 | creación del lote de abuelas | plan de importación | operador | granja/galpón | — (`POST /lots` manual) | lote | — | `P-01` | — (**`R-153`**, `AOD-25`) |
| `P-02` | Progenitoras — Producción | fase producción | operador | — | huevo (`egg_collection`, `egg_classification`, `egg_dispatch`) | huevos a incubadora (`egg_batches.generation = grandparent`) | Progenitoras → Incubadora | `P-05` | — |

`R-152` toca **solo** `P-01` paso 1 (y sus superficies de edición/corrección/adjuntos). No se certifica «Progenitoras» como un bloque.

## 2. Paridad por capacidad (`§13-§14`)

| Capacidad | Fuente | Proceso | ¿Progenitoras? | ¿Equivalente en Reproductoras? | Relación | ¿Modelo compartido? | ¿Servicio? | ¿Ruta? | ¿Validador? | ¿Mismos campos? | ¿Mismas reglas? | ¿Mismos estados? | ¿Misma guarda de unidad? | Soporte actual Progenitoras | Soporte actual Reproductoras | Brecha | ¿Decisión? | AC | Prueba |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **plan de importación** (`grandparent_import`) | `docs/02 §3.4.1` · `spec.md §4.4` | `P-01` §1 | **sí** | **no** (Reproductoras reciben de Progenitoras/incubadora: `§3.5.2`; sin importación) | **`PROGENITORAS_SPECIFIC`** | `OperationalEvent` + `extra_data` + `Evidence` (primitivas genéricas) | `_apply_business_rules` (rama nueva) | `POST /operations` (misma) | **nuevo**: `validate_import_plan` (`BR-22`); patrón `RR-12` | no (22 campos propios) | no (`BR-22`; `BR-20` prohibida) | `P-07` (mismos) | sí (`exigir_unidad_operativa`, unidad derivada del lote) | genérico, sin esquema (4 entradas libres en el frontend) | n/a | **estructura, identidades, adjuntos tipados, detalle** | no | `AC-R152-01…20` | `ABUE-` |
| creación automática del lote | `docs/02 §3.4.2` | `P-01` §0 | sí | no (lote de cría manual, `§3.5.1`) | `PROGENITORAS_SPECIFIC` | `Lot` | `create_lot` | — | — | — | — | — | — | manual (`POST /lots`) | manual | **semántica sin fuente** | **sí (`AOD-25`)** | — | — |
| recepción de aves (cantidad, sexo, peso) | `spec.md §4.4` ↔ `§4.5` | `P-01` §4 | sí | sí | `SHARED_PRIMITIVE_DIFFERENT_RULE`: mismo evento, `BR-17`/`BR-18` iguales; **`BR-20` (cuadre) y `B02` (curva) son de Reproductoras** (`GA-REM-021-B`: «Otros tipos: prohibido»; `B02` «progenitoras: sin fuente») | sí | sí | sí | `validate_house_capacity`, `validate_oc_limit` (iguales); `validate_reception_reconciliation` (breeder-only) | recepción: sí; cuadre: no | parcial | sí | sí | `COMPLETE` (`PROCESS-01` §4; `AC-W05/W15`) | `COMPLETE` + `B01`/`B02` | ninguna en `R-152` | no | control `AC-R152-13` | `ABUE-` |
| acceso por unidad (empresa habilitada, concesión, RBAC, propiedad) | `GA-REM-040-G/H` · `OD-14/16` | todos | sí | sí | **`IDENTICAL_CONTRACT`** (`exigir_unidad_operativa` deriva la unidad de `lot.bird_type`; `AC-W05`: «actor `breeder` sobre lote `grandparent` → `400 BR-07`; el actor con concesión `grandparent` sí crea»; `AC-L14`) | sí | sí | sí | sí | — | sí | — | sí | certificado (`test_operations_bu_enforcement`, `test_lots_bu_enforcement`) | ídem | ninguna (controles en `ABUE-`) | no | `AC-R152-10…16` | `ABUE-` |
| población / saldo de aves | `GA-REM-005 E.3` · `B.2` | `P-01` | sí | sí | `IDENTICAL_CONTRACT` (entradas: `bird_reception`, `birth_registration`; la importación **no** entra: documental) | sí | sí | — | `get_current_bird_balance` | — | sí | — | — | `COMPLETE` (`R-130` en lotes `grandparent`: `test_population_invariant::ac08`) | ídem | ninguna; `AC-R152-08` fija que la importación no puebla | no | `AC-R152-08` | `ABUE-` |
| edición / corrección / anulación | `GA-REM-005-E`, `GA-REM-023-B`, `GA-REM-006-A` | `P-07` | sí | sí | `IDENTICAL_CONTRACT` (guarda central) + **`BR-22` en el candidato** (`extra_data`, `supplier_id`) | sí | sí | sí | guarda + `BR-22` | — | + `BR-22` | sí | sí | genérico | genérico | revalidar el plan al editar/corregir | no | `AC-R152-17…19` | `ABUE-` |
| adjuntos | `docs/02 §3.4.1` (5 clases) · `spec.md §4.4` («con documentos») | `P-01` §1 | sí | no (Reproductoras: evidencias genéricas) | `PROGENITORAS_SPECIFIC` (tipología) sobre primitiva compartida (`Evidence`) | sí | `upload_evidence` | `POST /operations/{id}/evidences` | tipo ∈ conjunto cerrado | no | no | — | sí (`AC-W13`) | `evidence_type` = photo/document por MIME | ídem | **tipología** | no | `AC-R152-06/07` | `ABUE-` |
| línea genética / curva de peso | `GA-REQ-037` · `OD-06` · `GA_REM_021_B02 :72` («Progenitoras: sin fuente») | `P-01` | lote con `genetic_line_id` (sí); curva/alerta **no** | sí (curva y alerta, `B02`) | `REPRODUCTORAS_SPECIFIC` (evaluación de peso en recepción) · la línea genética del lote es compartida | sí | — | — | — | — | — | — | — | lote con línea; sin curva propia (correcto por fuente) | curva + alerta | ninguna (no se inventa curva de Progenitoras) | no | — | — |
| agua | `Bases` p.2/4/12 (Reproductoras, Engorde) | — | **no** (`GA-REM-021-A`: ni Incubadora ni Progenitoras) | sí | `REPRODUCTORAS_SPECIFIC` | — | — | — | — | — | — | — | — | `RR-11` lo rechaza en `grandparent` | `COMPLETE` | ninguna | no | — | — |
| fases (cría → producción) | `spec.md §4.9` · etapas `grandparent_rearing/production` | `P-01`→`P-02` | sí | sí | `IDENTICAL_CONTRACT` (`lot_phases`, `POST /lots/{id}/phases`) | sí | sí | sí | — | — | — | — | — | `COMPLETE` (`PROGENITORAS_COVERAGE`) | ídem | fuera de `R-152` | no | — | — |
| trazabilidad generacional | `spec.md §4.9` · `R-178` | `P-10` | sí (`egg_batches.generation = grandparent`) | sí | `IDENTICAL_CONTRACT` | sí | sí | sí | — | — | — | — | — | `COMPLETE` | ídem | ninguna (la importación no crea linaje) | no | — | — |

## 3. Campos del plan de importación vs recepción de Reproductoras (`§31`)

| Campo (`docs/02`) | Progenitoras (`§3.4.1`, importación) | Reproductoras (`§3.5.2`, recepción) | ¿Igual? | Fuente | API actual | UI actual | Brecha |
|---|---|---|---|---|---|---|---|
| Orden de compra SAP | sí (`sap_document_ref`) | sí | sí | `§3.4.1` / `§3.5.1` | `sap_document_ref` (columna) | selector de OC (`sapImportOrder`) | requerida en la importación (`BR-22`) |
| Proveedor internacional | sí (`supplier_id`) | proveedor (`§3.5.1`) | primitiva igual, semántica «internacional» | `§3.4.1` | `supplier_id` (columna; **sin verificación de pertenencia**) | selector | requerido + pertenencia a la empresa |
| País de origen | **sí** | no | no | `§3.4.1` | `extra_data.origin_country` (libre) | entrada libre | tipado, requerido |
| Línea genética | sí (del lote) | sí (del lote) | sí | `§3.4.1` / `§3.5.1` | `Lot.genetic_line_id` | formulario de lote | derivada del lote (sin doble captura) |
| Tipo de ave | sí (`Lot.bird_type = grandparent`) | breeder | — | `§3.4.1` | `Lot.bird_type` | — | la importación **solo** sobre lote `grandparent` |
| Sexo (♂/♀ cantidades) | **sí** (recibidas por sexo) | sí (alojadas por sexo/galpón) | primitiva igual (`bird_movements.sex/quantity`) | `§3.4.1` / `§3.5.2` | `bird_movements` | filas ♂/♀ | identidad `Σ filas = recibida` |
| Cantidad comprada | **sí** | no (la OC) | no | `§3.4.1` | — | — | `extra_data.import_plan.purchased_total` |
| Cantidad embarcada | **sí** | no | no | `§3.4.1` | — | — | `shipped_total` |
| Cantidad recibida | **sí** | `received_total` (`BR-20`) | mismo concepto, **distinta regla** (`BR-20` prohibida fuera de `bird_reception`) | `§3.4.1` / `Rec. §6` | — | — | `received_total` del plan; identidad con `shipped − transit_mortality` y con Σ filas |
| Mortalidad en traslado | **sí** | mortalidad al arribo (`dead_on_arrival`) | concepto análogo, campo distinto (no se reutiliza la tupla `BR-20`) | `§3.4.1` | — | — | `transit_mortality` |
| Documentos sanitarios · permisos de importación · aduanales · certificados de vacunación · de origen (adjuntos) | **sí (5 clases)** | no | no | `§3.4.1` | `Evidence.evidence_type` = photo/document | subida genérica | `evidence_type` ∈ 5 clases |
| Fecha de salida (origen) · Fecha de llegada (destino) | **sí** | fecha despacho / recepción (`§3.5.2`, no capturadas hoy como tales) | no | `§3.4.1` | — | — | `departure_date`, `arrival_date` (llegada ≥ salida) |
| Transporte | sí (`transport_id`) | sí | sí | `§3.4.1` | `transport_id` (columna; sin pertenencia) | selector | pertenencia |
| Condición de recepción | **sí** | no | no | `§3.4.1` | — | — | `reception_condition` (texto, opcional) |
| Cuarentena (días, fecha fin) | **sí** | no | no | `§3.4.1` | `extra_data.quarantine_days` (libre) | entrada | `quarantine_days`, `quarantine_end_date` (opcionales; fin ≥ llegada) |
| Inspección sanitaria inicial | **sí** | no | no | `§3.4.1` | — | — | `initial_health_inspection` (texto, opcional) |
| Peso promedio proveedor / granja | no | sí (`B02`) | — | `§3.5.2` | `avg_weight` | filas | no se exige; si viene, sin evaluación de curva (`B02`: sin fuente para Progenitoras) |
| `dead_on_arrival` / `rejected_on_arrival` | **prohibidos** en la importación (`BR-20`, «otros tipos: prohibido») | sí | — | `GA-REM-021-B` | columnas | — | sin cambio (control) |

## 4. Reglas de negocio por operación (`§32`)

| Regla | Recepción de Reproductoras | `grandparent_import` (Progenitoras) | Clase |
|---|---|---|---|
| `BR-06` fecha ≥ inicio del lote · `BR-19` período/futuro | sí | sí | SAME |
| `BR-07` lote activo de la empresa · unidad · RBAC | sí | sí | SAME |
| `BR-08` ubicación obligatoria | sí (evento de ubicación) | **no** (la importación no es evento de ubicación; el lote lleva granja/galpón) | N/A (sin cambio) |
| `BR-17` capacidad del galpón | sí | **N/A** (documental: no aloja; el alojamiento es `bird_reception`/`bird_distribution`) | N/A |
| `BR-18` acumulado de la OC | sí (`bird_reception`) | **N/A** (la importación no acumula; hacerlo duplicaría la recepción del paso 4 contra la misma OC) | DIFFERENT (documentado) |
| `BR-20` cuadre de recepción | sí (breeder) | **prohibido** | REPRODUCTORAS_SPECIFIC |
| `BR-11` documento SAP único por lote y tipo | sí (salvo `bird_reception`: OC repetible, `OD-04`) | sí (una importación por OC y lote) | SAME |
| **`BR-22`** plan de importación (estructura + identidades) | — | **sí** | PROGENITORAS_SPECIFIC |
| `B02` peso vs curva | sí | no | REPRODUCTORAS_SPECIFIC |
| `BR-01`/saldo | entrada | **sin efecto** (documental) | DIFFERENT (documentado, `AC-R152-08`) |

## 5. Cadena de seguridad sobre `POST /operations` (importación) — matriz (`§12`, `§18-§23`)

| Capa | Mecanismo (existente) | Progenitoras | Prueba (control, verde antes y después) |
|---|---|---|---|
| inquilino / empresa | `get_event`/`validate_lot_active(company)` · `verificar_ubicacion` · pertenencia de proveedor/transporte (**nueva para la importación**) | lote de B para actor de A → `400 BR-07` | `AC-R152-14` |
| empresa: unidad `grandparent` habilitada | `unidades_efectivas` (solo habilitadas) · global: `unidades_habilitadas` | empresa con `grandparent` OFF → actor de empresa `400 BR-07`; global situada `403` | `AC-R152-12` |
| usuario: concesión `grandparent` | `exigir_unidad_operativa(no_concedida)` | actor con solo `breeder` → `400 BR-07`; solo `grandparent` → `201` (sin `breeder`) | `AC-R152-10/11` |
| RBAC | `require_permission("operations","create")` | sin permiso `403`; Administrador de Accesos `403`; Contraloría (lectura) `403` | `AC-R152-15/16` |
| propiedad del recurso | lote de la empresa efectiva | ídem inquilino | `AC-R152-14` |
| regla de negocio | `BR-22` + resto | — | `AC-R152-02…05` |
| global sin contexto | `sin_empresa` → `400 BR-07` | fail-closed | `AC-R152-13` |
| empresa con `grandparent` ON y `breeder` OFF | — | la importación funciona sin Reproductoras (unidad de primera clase) | `AC-R152-11b` |

Nada de esto es nuevo: `GA-REM-040-G/H` lo certificó para `grandparent` (`AC-W05`, `AC-W15`, `AC-L02`, `AC-L14`). `R-152` añade la pertenencia del
proveedor y del transporte en la importación (§3) y los **controles** sobre su propia ruta, sin permiso nuevo.

## 6. Bloqueadores actuales de cada comportamiento ausente (`§28`)

| Comportamiento ausente | Bloqueador | Raíz exacta |
|---|---|---|
| plan estructurado y validado | `SCHEMA VALIDATION` ausente + `SERVICE VALIDATION` ausente | `extra_data: Optional[dict]` libre; `_apply_business_rules` sin rama `GRANDPARENT_IMPORT` |
| identidades comprada/embarcada/recibida/mortalidad, recibida = Σ ♂/♀ | `BUSINESS RULE ABSENT` | no existe `BR-22` |
| importación solo sobre lote `grandparent` | `SERVICE VALIDATION` ausente | nada cruza `event_type` con `lot.bird_type` para este tipo |
| proveedor/transporte de la empresa | `SERVICE VALIDATION` ausente (clase `R-42`) | `verificar_ubicacion` solo cubre granja/galpón/destino |
| adjuntos tipados | `ROUTE GUARD`/`SCHEMA` (tipo derivado del MIME) | `upload_evidence` fija `evidence_type` por `content_type`; sin parámetro |
| plan visible y capturable | `MISSING FORM` (parcial) + detalle sin plan | caso del formulario con 4 entradas libres; `OperationDetailPage` no muestra `extra_data` |
| revalidación al editar/corregir | `SERVICE VALIDATION` ausente | la guarda de `R-173`/`R-176` no conoce `extra_data`/`supplier_id` |
| lote automático (`R-153`) | `OWNER DECISION GAP` | §4 de la traza |

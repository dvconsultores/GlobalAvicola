# MATRIZ DE APLICABILIDAD Y CONTRATO DE DATOS · `GA-REM-021 B05` — CONSUMO DIARIO DE AGUA

**WAVE B · tranche 6** · 2026-09-09 · base `55d9072` · construida **antes** de los AC y del código

Fuentes leídas (nivel de evidencia según `REQUIREMENT_CONFLICT_RESOLUTION.md §1`): **nivel 2** `Imagen de Procesos
Documentado/Bases Consideradas en el Desarrollo de la App Avicola.pdf` (leído del PDF, páginas 2, 4, 9-11, 12) · **nivel 3**
`docs/02`, `docs/12` (silencio sobre agua) · **nivel 4** `spec.md` (silencio), `GA-REM-021` (`SPEC_READY`), `GA-REM-020`
(cobertura: agua ausente en Cría · Producción · Engorde) · **nivel 5** `frontend/src/pages/reports/ReportsPage.tsx:24-30`
(`e.water_liters` → `water_l`), `OperationFormPage.tsx`, `FeedMovementSchema` (`quantity_kg: gt=0`, `Float`), `operations/*` ·
**nivel 6** `docs/15 §` (legado: «Agua: Lt Agua x Ave x Sem», `OperationalEvent.water_liters` previsto, gráfico de barras) ·
`SYSTEM_OF_RECORD_AND_AUTHORITY_MATRIX.md` fila 51 (evento operativo = `APP_MANDANTE`) · `H360-B05` · `R-13` · `OD-14/16` ·
`GA-REM-040-G/H` · `GA-REM-006-A` · `OD-19`/`GA-REM-041 §3.5`.

## 1. Requisito exacto (nivel 2, textual)

| Etapa del cliente | Página | Cita | Etapa propia (`processCatalog` / `BirdTypeEnum`) |
|---|:--:|---|---|
| Reproductora Fase Cría | 2 | «8. Consumo de Agua: Cantidad de agua consumida por los pollitos durante el día.» | `breeder_rearing` → `breeder` |
| Reproductora Fase Producción | 4 | «11. Consumo de Agua: Cantidad de agua consumida por las gallinas durante el día.» | `breeder_production` → `breeder` |
| Pollo de Engorde | 12 | «9. Consumo de Agua: Cantidad de agua consumida por los pollos durante el día.» | `broiler` |
| Traslado de huevos · Incubadora | 7-11 | **no figura** ningún dato de agua | `hatchery` → no aplica |
| Progenitoras | — | **no es una etapa del documento del cliente** (Reproductora · Incubadora · Engorde); `OD-16.a` la incorpora al producto sin dato de agua asociado | `grandparent` → no aplica (por fuente) |
| Todas | 3, 6, 8, 11, 13 | «Optimización de Recursos: Ayuda a optimizar el uso de alimento, agua y otros recursos.» | KPI: **ola C**, fuera |

## 2. Cada semántica, con el nivel que la resuelve (`§1` regla de corte · regla de escalado)

| Semántica | Resolución | Nivel | Evidencia | ¿Cambia comportamiento de negocio si se eligiera distinto? |
|---|---|:--:|---|---|
| **Qué** se registra | cantidad **consumida** (no lectura de contador) | 2 | «Cantidad de agua consumida … durante el día» | — (lo dice el cliente) |
| **Frecuencia** | diaria | 2 | «durante el día», lista «Datos Diarios a Registrar» | — |
| **Granularidad** | la parvada del día = el **lote** (`lot_id` obligatorio); granja/galpón opcionales como en alimento | 2 (parvada) · 5 (modelo de eventos por lote) | «por los pollitos / las gallinas / los pollos»; `feed_registration` es evento de lote con ubicación opcional (`validate_farm_house`) | no: el nivel 2 fija la parvada; el 5 solo precisa cómo se modela |
| **Etapas** | `breeder` (cría y producción) · `broiler` | 2 | páginas 2, 4, 12; ausente en 7-11 | — |
| **Unidad** | **litros** (`water_liters`) | **5** (precisado por 6) | el contrato del reporte lee `e.water_liters` y suma `water_l`; el legado registraba «Lt Agua»; `docs/15` prevé `OperationalEvent.water_liters` | no: es representación del mismo dato; el cliente calla (como con el kg del alimento, resuelto también en nivel 5) → **`RR-10`** |
| **Cero / negativo / precisión** | consumo **> 0**; decimales admitidos (`Float`), sin redondeo inventado | 5 | convención del producto para consumos diarios: `FeedMovementSchema.quantity_kg: Field(gt=0)`, `Float`; «no hay registro» ≠ `0` | no: se aplica la regla ya vigente para el consumo diario; un día sin dato no se representa con `0` → **`RR-11`** |
| **Duplicidad** | eventos aditivos por día (como alimento y mortalidad); sin unicidad `lote/día` | 5 | el modelo diario del producto es por evento; el reporte **suma** por fecha (`ReportsPage`) | no: mismo modelo que el resto de datos diarios; el cliente no fija unicidad |
| **Fecha de negocio** | `event_date` (`date`), la del resto de eventos | 5 | `OperationalEvent.event_date`; `R-80` (TZ) sigue **abierto** y no se toca | — |
| **Obligatorio** | opcional en la primera iteración | 4 | `GA-REM-021 §Riesgos`: «el campo es opcional en la primera iteración» | — |
| **Quién · cuándo** | el operador, en el registro diario; mismo flujo que alimento | 3 · 4 | `docs/12 §3` (Operador registra); `GA-REM-021`: «se registra a diario junto con el consumo de alimento» | — |
| **Aprobación** | flujo existente de `P-07` (`REGISTERED → submit → revisión → aprobación`) | 3 | `docs/12`: todo registro operativo pasa por revisión | — |
| **Corrección** | `POST /corrections` (`RR-01`, `GA-REM-006-A`): `water_liters` entra en `OperationalEventUpdate` → `campos_corregibles` | 4 | `GA-REM-006` lista blanca derivada del contrato de edición | — |
| **Reverso** | **no elegible** (`GA-REM-041 §3.5` no lo lista; ampliar la elegibilidad es enmienda de `GA-REM-041`, no de esta) | 1 (`OD-19`) · 4 | `ELEGIBLES_*` | — |
| **Auditoría** | la del evento (`audit_event_created`, transiciones, `audit_correction`) | 4 | `GA-REM-032` | — |
| **Sistema de registro** | **app** (`APP_MANDANTE`) | SoR §51 | «Evento operativo (captura) · app» | — |
| **Dónde vive** | columna **`water_liters`** en `operational_events`, portada por un tipo de evento propio **`water_consumption`** | 4 (`GA-REM-021 §Alcance 2` deja la elección a la spec) · 6 (`docs/15` prevé `OperationalEvent.water_liters`) | un dato, un registro: tiene su cola de revisión, su corrección y su serie; no se cuelga del alimento (un registro de agua sin alimento debe ser posible) ni de la inspección; no va a `extra_data` (dato de dominio estable) | no: es diseño de persistencia dentro de las opciones que la spec abrió |

**Ningún ítem exigió escalado**: los que el cliente calla los resuelve un nivel inferior que **sí se pronuncia**
(`RR-10`, `RR-11`) y no cambian el comportamiento de negocio respecto a lo que el producto ya hace con el alimento.
`AOD-19` (`R-147`: UoM/umbrales de constantes) **no gobierna** `B05`: trata catálogos de unidad de medida y umbrales fijos de
T°/H°; aquí no hay umbral y la unidad la fija el contrato vigente del producto. No se decide por proximidad.

## 3. Matriz de aplicabilidad

| BU | Requisito fuente | ¿Aplica? | Nivel del recurso | Semántica de entrada | Unidad | Frecuencia | Fecha de negocio | ¿Obligatorio? | ¿Cero válido? | Decimales | Actor de escritura | RBAC | ¿Aprobación? | ¿Corrección? | Auditoría | Persistencia | Soporte actual | Brecha | AC | Test |
|---|---|:--:|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `breeder` (Reproductoras: cría y producción) | Bases p.2, p.4 | **sí** | lote (parvada); granja/galpón opcionales | cantidad consumida | L (`water_liters`) | diaria (aditiva) | `event_date` | opcional (dato); si se registra, `> 0` | no | sí (`Float`) | operador (`operations:create`) con unidad efectiva | `operations:create` | `P-07` existente | `corrections` (`RR-01`) | evento | `operational_events.water_liters` + `water_consumption` | **ninguno** | tipo, columna, regla, formulario | `W01…W07`, `V*`, `S*`, `BU-01` | `test_water_capture.py::w*`, `::bu01*` |
| `broiler` (Engorde) | Bases p.12 | **sí** | ídem | ídem | L | diaria | `event_date` | opcional | no | sí | ídem | ídem | ídem | ídem | ídem | ídem | ninguno | ídem | `BU-02` | `::bu02*` |
| `hatchery` (Incubadora) | Bases p.7-11: sin agua | **no** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | la ruta **no debe aceptar** en silencio | `BU-03` (`400`) | `::bu03*` |
| `grandparent` (Progenitoras) | no es etapa del documento del cliente | **no (por fuente)** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | ídem; extenderlo exige requisito o decisión | `BU-04` (`400`) | `::bu04*` |
| lote sin cadena declarada | — | **no** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | no se puede establecer aplicabilidad (`OD-10.c`) | `V07` | `::v07*` |

## 4. Contrato de datos

| Campo | Significado | Tipo | ¿Requerido? | Unidad | Fuente | Validación | Relación autoritativa |
|---|---|---|---|---|---|---|---|
| `event_type` | `water_consumption` (nuevo miembro de `EventType`, enumerado nativo → migración) | enum | sí | — | esta spec | tipo reconocido | — |
| `lot_id` | la parvada del día | FK `lots` | **sí** (no está en `LOT_OPTIONAL_EVENTS`) | — | nivel 2 | lote activo (`BR-07`), de la empresa efectiva y de la unidad efectiva/habilitada (`G.3`/`H.5`), `bird_type ∈ {breeder, broiler}` | empresa y unidad se **derivan** del lote |
| `event_date` | día del consumo | `date` | sí (defecto hoy) | — | nivel 5 | `BR-06` (no anterior a la activación), como todo evento | — |
| `water_liters` | litros consumidos por la parvada en el día | `Float` (`NUMERIC` no es la convención del repo: `quantity_kg`, `avg_weight` son `Float`) | **sí cuando `event_type = water_consumption`**; **prohibido** en cualquier otro tipo (un dato, un registro) | L | `RR-10` | `> 0` (`RR-11`); sin redondeo | — |
| `farm_id` · `house_id` | ubicación opcional | FK | no | — | nivel 5 (como alimento) | `verificar_ubicacion` (empresa) | — |
| `observations` | texto libre | `str` | no | — | — | — | — |
| `company_id` · `business_unit_id` · `status` · `registered_by_id` | **nunca del cliente** | — | — | — | `OD-14`, `R-32` | `OperationalEventCreate` no los declara (se ignoran); `Update` es `extra="forbid"` | derivados por el servidor |

Respuesta: `OperationalEventRead` (hereda `water_liters` de `OperationalEventBase`) → el reporte existente (`ReportsPage`)
deja de estar vacío sin cambiar su contrato.

## 5. Frontera de esta captura

Fuera: `B04` (`AOD-14`) · resto de `GA-REM-021` · KPI de agua (ola C: L/ave, agua/alimento, tendencias, umbrales) · alertas ·
sensores/IoT · SAP · `R-161` · `R-164` · `R-166` · `R-140`/`R-154` residuales · `R-136` SAP · fase 9 · `BU-D10` · `R-158`.

# Manual de las plantillas de Cargas Iniciales (saldos de apertura)

Este manual explica las **cuatro plantillas Excel de carga inicial** (cutover) de Global Avícola y cómo rellenarlas, con los ajustes acordados con los KeyUser (SPEC 009, 2026-10-22).

Las cuatro plantillas, tal como las genera el sistema hoy, están en **`docs/plantillas_carga_inicial/`**:

| Unidad de negocio | Archivo | Versión |
|---|---|---|
| Progenitoras (grandparent) | `cutover_template_grandparent_v3.xlsx` | **v3** |
| Reproductoras (breeder) | `cutover_template_breeder_v3.xlsx` | **v3** |
| Incubadora (hatchery) | `cutover_template_hatchery_v4.xlsx` | **v4** |
| Engorde (broiler) | `cutover_template_broiler_v2.xlsx` | v2 |

> Cada carga descarga **su propia** plantilla desde el sistema (la unidad y la fecha de corte las fija la carga). Las de esta carpeta son copias de referencia para conocer el formato vigente. **Incubadora es ahora v4** y **Progenitoras y Reproductoras v3**: una plantilla v3 de Incubadora o una v2 de Progenitoras/Reproductoras será rechazada con el mensaje «descargue la plantilla vigente» (v4 en Incubadora, v3 en aves); **Engorde sigue en v2**.

---

## 1 · Cómo funciona cualquier plantilla

### 1.1 · Hojas del Excel

Cada plantilla trae cuatro hojas:

- **Instrucciones** — una fila por campo con su significado, si es obligatorio, tipo, unidad, formato, ejemplo, valores permitidos, si admite vacío (UNKNOWN) y si admite `N/A`, y a dónde va el dato tras aplicar.
- **Meta** — identifica la plantilla: `template_version`, `schema_id`, `company`, `business_unit`, fecha de generación y fecha/hora de corte. **No modificar.**
- **Datos** — donde se cargan las filas (un lote, o un proceso de incubación, por fila). **No cambiar la cabecera.**
- **Catalogos** — los valores válidos de los maestros (códigos y nombres) de su empresa, para copiarlos tal cual en `Datos`. Columnas: `catalog, code, description, status, parent_code, source` (ver 1.4).

### 1.2 · Vacío / 0 / N/A (semántica de cada celda)

El dato nunca se inventa. En cada celda de métrica:

- **Celda vacía = UNKNOWN**: no se conoce el dato en el sistema anterior.
- **`0` = cero CONOCIDO**: realmente es cero.
- **`N/A` = NO APLICA**: la métrica no corresponde a ese lote/fase.

Poner `N/A` en un campo **obligatorio** es un error (indique el valor; si es cero real, escriba `0`).

### 1.3 · Tipos y formatos

- Fechas en **AAAA-MM-DD**. La fecha/hora de corte la fija la carga.
- Enteros sin separador de miles; decimales con punto. **Pesos en gramos; alimento en kilogramos.**
- No use fórmulas ni macros: el importador lee valores y rechaza fórmulas.

### 1.4 · Procedencia de los maestros en `Catalogos` (SAP vs Global Avícola)

La hoja `Catalogos` indica, en la columna **`source`**, quién gobierna cada maestro:

- **`SAP`** — **granjas (`farm`) y galpones (`house`)**: su codificación proviene del ERP (SAP), a través de la sincronización autorizada de **solo lectura**. La plantilla muestra únicamente los valores ya recibidos y promovidos al sistema local; **nunca se inventan códigos SAP**.
- **`GLOBAL_AVICOLA`** — el resto (línea genética, raza, fase productiva, área, planta de incubación, incubadora, nacedora, lotes): son **maestros internos de Global Avícola**.

Use siempre un valor que aparezca en `Catalogos` (activo y de su empresa). Si un maestro no está, no lo invente: pídalo por el canal correspondiente.

---

## 2 · Campos comunes de identificación del lote (aves)

Presentes en Progenitoras, Reproductoras y Engorde:

| Campo | Obligatorio | Qué es |
|---|---|---|
| `legacy_lot_code` | **sí** | Código del lote en el sistema anterior. Único en la carga y en la empresa. |
| `existing_lot_code` | no | Código de un lote YA existente en Global Avícola para reutilizarlo (misma empresa, activo, sin eventos). Si se deja vacío, se crea un lote migrado. |
| `farm_code` | **sí** | Granja (hoja `Catalogos` → `farm`, origen **SAP**). |
| `house_name` | no | Galpón dentro de la granja (`Catalogos` → `house`, `parent_code` = granja, origen **SAP**). |
| `area_code` | no | Área funcional (`Catalogos` → `area`). |
| `productive_phase_code` | **sí** | Fase real al corte. Progenitoras/Reproductoras: `CRIA` o `PROD`. Engorde: `ENGORDE`. |
| `real_start_date` | **sí** | Fecha real de inicio (alojamiento). ≤ fecha de corte. |
| `phase_start_date` | no | Inicio de la fase declarada. Vacío = se toma la fecha real de inicio. |
| `genetic_line_code` | no | **Línea genética — maestro INTERNO de Global Avícola, no SAP** (`Catalogos` → `genetic_line`). |
| `breed_name` | no | **Raza — maestro INTERNO de Global Avícola, no SAP** (`Catalogos` → `breed`, debe pertenecer a la línea indicada). |
| `sex` | no | `male` / `female` / `mixed`. |

> **Línea genética y raza son de Global Avícola, no de SAP.** Si el código/nombre no existe, está fuera de la empresa o la raza no pertenece a la línea, la fila se marca inválida con un mensaje claro (`La línea genética no existe…`, `La raza no existe…`, `La raza no pertenece a la línea…`). El sistema **no** las crea solo: elija un valor de `Catalogos`.

Campos de **procedencia** (comunes a las cuatro plantillas): `source_system` (p. ej. LEGACY/EXCEL), `source_reference` (documento/planilla de origen), `notes` (notas libres; nunca sustituyen a un campo).

---

## 3 · Plantilla de Progenitoras y Reproductoras (aves por sexo)

Mismas columnas para ambas (contrato de reproductoras). Métricas al corte:

| Campo | Obligatorio | Unidad | Notas |
|---|---|---|---|
| `live_males` | **sí** | aves | Machos vivos al corte (saldo vivo; no se resta lo histórico). |
| `live_females` | **sí** | aves | Hembras vivas al corte. |
| `birds_placed_males` / `birds_placed_females` | no | aves | Alojadas originalmente (histórico). |
| `historical_mortality_males` | **ver abajo** | aves | Mortalidad acumulada de machos antes del corte. |
| `historical_mortality_females` | **ver abajo** | aves | Mortalidad acumulada de hembras antes del corte. |
| `historical_culls_males` / `historical_culls_females` | no | aves | Descartes acumulados. |
| `historical_transfers_in_males` / `historical_transfers_in_females` | no | aves | Aves **recibidas** de otros lotes antes del corte (ver sección siguiente). |
| `historical_transfers_out_males` / `historical_transfers_out_females` | no | aves | Aves **enviadas** a otros lotes antes del corte (ver sección siguiente). |
| `accumulated_feed_kg` | no | kg | Alimento acumulado. |
| `current_avg_weight_g` | no | g | Peso promedio actual del ave. |
| `accumulated_egg_production` | no | huevos | Producción acumulada. **`N/A` en fase `CRIA`.** |
| `accumulated_eggs_to_hatchery` | no | huevos | Huevos enviados a incubadora. **`N/A` en fase `CRIA`.** |

### Mortalidad histórica — diferencia entre Reproductoras y Progenitoras (SPEC 009)

- **Reproductoras (breeder): `historical_mortality_males` y `historical_mortality_females` son OBLIGATORIAS.** Si no la conoce con certeza, consulte el dato real; **no** puede dejarse vacía. **`0` es un valor válido** (cero real). Dejarla en blanco da el error «Campo obligatorio sin valor».
- **Progenitoras (grandparent): siguen siendo opcionales** (vacío = desconocido/UNKNOWN).

Consistencia (solo si todas las piezas son conocidas): `vivas = alojadas + entradas − mortalidad − descartes − salidas`, por sexo; y `huevos a incubadora ≤ huevos producidos`.

---

## Transferencias históricas entre lotes (plantilla v3 de Progenitoras y Reproductoras)

Algunos lotes **recibieron** aves de otros lotes o **enviaron** aves a otros lotes **antes de la fecha de corte**. Ese histórico se declara en cuatro campos nuevos (unidad **aves**, siempre **acumulado hasta el corte**):

| Campo | Qué registrar |
|---|---|
| `historical_transfers_in_males` | Machos recibidos desde otros lotes antes del corte. |
| `historical_transfers_in_females` | Hembras recibidas desde otros lotes antes del corte. |
| `historical_transfers_out_males` | Machos enviados a otros lotes antes del corte. |
| `historical_transfers_out_females` | Hembras enviadas a otros lotes antes del corte. |

- **No registre aquí movimientos posteriores al corte**: esos se registran con la operación normal del sistema.
- Por cada sexo el sistema verifica: `vivas = alojadas + entradas − mortalidad − descartes − salidas`.
- `alojadas` (`birds_placed_males` / `birds_placed_females`) sigue siendo **lo originalmente alojado**: no se le suman las transferencias.

**Ejemplo — lote que entrega** (machos): alojados 1.300, mortalidad 165, descartes 0, entradas 0, salidas 300 ⇒ vivas = 1.300 + 0 − 165 − 0 − 300 = **835**.

**Ejemplo — lote que recibe** (hembras): alojadas 1.000, entradas 300, mortalidad 100, descartes 20, salidas 0 ⇒ vivas = 1.000 + 300 − 100 − 20 − 0 = **1.180**.

`0` solo cuando **se sabe** que no hubo transferencias. Celda **vacía = desconocido**: en ese caso el sistema **no** verifica la ecuación de ese sexo y la vista previa lo marca «no totalmente verificable» (nunca se inventa un cero). No se aceptan negativos ni decimales: son aves enteras.

La plantilla **v2** de Progenitoras y Reproductoras **ya no se acepta**: descargue la **v3**.

### Progenitoras (Abuelas): cómo registrar el desalojo, el traslado y la conformación (SPEC 019)

En Progenitoras los movimientos de población **entre lotes** son reales: selección y descarte durante la cría, **desalojo**, **traslado** a producción y **conformación** del lote. Antes de cargar un lote de Abuelas:

| Punto | Cómo se registra |
|---|---|
| (a) **Aves alojadas** | `birds_placed_males` / `birds_placed_females` = aves **efectivamente recibidas y alojadas** al abrir el lote (conteo real tras la recepción y el sexaje). **No** es la cantidad planificada ni solicitada en la importación, y **no** se le suman las transferencias. |
| (b) **Descartes históricos** | `historical_culls_*` = **TODO** descarte que redujo físicamente la población del lote: cría y levante, **selección y desalojo**, antes de conformar producción, y las **aves retiradas por error de sexaje**. Un ave descartada **no se repite** como transferencia. |
| (c) **Traslado / conformación entre lotes** | El lote **origen** informa la **SALIDA** (`historical_transfers_out_males` / `..._out_females`) y el lote **destino** la **ENTRADA** (`historical_transfers_in_*`), cada uno por sexo y acumulado hasta el corte. Cuando se cargan ambos lotes, la suma de salidas de los orígenes debe coincidir con las entradas del destino, pero **el sistema no lo exige**: las cargas pueden ser parciales (origen cerrado sin destino migrado, o al revés). |
| (d) **Cambio de fase del mismo lote** | El paso **CRIA → PROD** del **mismo** lote **NO es una transferencia**: deje las cuatro columnas de transferencias en `0` conocido (o vacías). La fase se informa en `productive_phase_code` y no mueve población entre lotes. |
| (e) **Mortalidad histórica** | En Progenitoras es **opcional**: vacía = desconocida, y el sistema **no** verifica la ecuación de ese sexo. (En Reproductoras es obligatoria.) |
| (f) **Error de sexaje** | Un error de sexaje que provoca la salida física del ave del lote es un **DESCARTE**: se acumula en **Descartes históricos** (`historical_culls_males` / `historical_culls_females`) del sexo con el que estaba contabilizada. **No** existe un campo propio de sexaje ni se modela como cambio de sexo (macho↔hembra) dentro del lote. Si desconoce el acumulado de descartes, deje la celda **vacía** (desconocido): el sistema **no** inventa un 0. |
| (g) **Ejemplo del desalojo** | Ver el lote B más abajo. |

**Ejemplo — desalojo del lote B (Abuelas, ambos sexos):**

| Concepto | Machos | Hembras | Campo de la plantilla |
|---|---|---|---|
| Alojadas (realmente recibidas) | 100 | 1.000 | `birds_placed_*` |
| Mortalidad histórica | 4 | 26 | `historical_mortality_*` |
| Descartes históricos (cría/levante, selección y desalojo) | 6 | 24 | `historical_culls_*` |
| Salidas a otro lote (traslado/conformación) | 40 | 600 | `historical_transfers_out_*` |
| Entradas desde otro lote | 0 | 0 | `historical_transfers_in_*` |
| **Vivas al corte** | **50** | **350** | `live_*` |

Comprobación por sexo (solo con piezas conocidas): machos `100 + 0 − 4 − 6 − 40 = 50`; hembras `1.000 + 0 − 26 − 24 − 600 = 350`. El lote **destino** de esas 40 aves (machos) y 600 aves (hembras) declara `historical_transfers_in_males = 40` y `historical_transfers_in_females = 600`.

**Ejemplo — lote A con un error de sexaje entre los descartes:** alojadas 1.000 aves, mortalidad 50, descartes 50 (20 de cría + **10 retiradas por error de sexaje** + 20 de selección/desalojo) y 900 transferidas al lote B ⇒ vivas = `1.000 − 50 − 50 − 900 = 0`.

---

## 4 · Plantilla de Engorde (población mixta)

Fase `ENGORDE`. Métricas al corte:

| Campo | Obligatorio | Unidad | Notas |
|---|---|---|---|
| `live_birds` | **sí** | aves | Aves vivas (mixtas) al corte. |
| `age_days` | no | días | Edad al corte; vacío = se deriva de la fecha de inicio. |
| `accumulated_birds_received` | no | aves | Recibidas acumuladas (alojadas). |
| `historical_mortality` | no | aves | Mortalidad acumulada. |
| `historical_culls` | no | aves | Descartes acumulados. |
| `partial_outbound_birds` | no | aves | Salidas parciales a planta. `N/A` si no hubo. |
| `accumulated_feed_kg` | no | kg | Alimento acumulado. |
| `current_avg_weight_g` | no | g | Peso promedio actual. |

Consistencia: `recibidas − mortalidad − descartes − salidas = vivas` (solo si todo es conocido).

---

## 5 · Plantilla de Incubadora (proceso de incubación) — v4

Describe un proceso de incubación en curso al corte. **Versión v4** (SPEC 018): retira `eggs_discarded` y añade el desglose de huevos **no incubables** (extra grande, sucio, roto) y los **huevos fértiles a fosa**. `egg_origin` sigue siendo obligatorio.

| Campo | Obligatorio | Qué es |
|---|---|---|
| `legacy_lot_code` | **sí** | Código del proceso/lote de incubación en el sistema anterior. |
| `existing_lot_code` | no | Lote de incubadora ya existente para reutilizar (sin eventos). |
| `hatchery_code` | **sí** | Planta de incubación (`Catalogos` → `hatchery`). |
| `incubator_name` | no | Incubadora dentro de la planta (`Catalogos` → `incubator`). |
| `hatcher_name` | no | Nacedora dentro de la planta (`Catalogos` → `hatcher`). |
| `source_lot_code` | no | Lote de reproductoras/progenitoras que originó los huevos (ver `egg_origin`). |
| `generation` | no | **Generación biológica del huevo**: `grandparent` (de progenitoras → pollito reproductor) o `breeder` (de reproductoras → pollito de engorde). Solo esos dos valores. |
| `egg_origin` | **sí** | **Origen comercial del huevo (NUEVO)**: `internal` (propio/interno de Global Avícola) o `purchased` (comprado a un tercero). |
| `reception_date` | **sí** | Fecha de recepción del huevo en la planta. ≤ corte. |
| `set_date` | no | Fecha de carga en incubadora. |
| `expected_hatch_date` | no | Fecha prevista de nacimiento. |
| `eggs_received` | **sí** | Huevos fértiles recibidos. |
| `eggs_set` | **sí** | Huevos ya cargados (≤ recibidos). |
| `eggs_non_incubable_oversized` | no | Huevos **recibidos** clasificados como no incubables por **extra grande** (acumulado al corte). Vacío = no se conoce; `0` = cero conocido. |
| `eggs_non_incubable_dirty` | no | Huevos **recibidos** clasificados como no incubables por **sucio** (acumulado al corte). Vacío = no se conoce; `0` = cero conocido. |
| `eggs_non_incubable_broken` | no | Huevos **recibidos** clasificados como no incubables por **roto** (acumulado al corte). Vacío = no se conoce; `0` = cero conocido. |
| `eggs_transferred` | no | Huevos transferidos a nacedora (≤ cargados). |
| `fertile_eggs_to_pit` | no | Huevos **fértiles a fosa**: cantidad acumulada de huevos fértiles **recibidos** que se enviaron a fosa **antes de la carga** en incubadora (acumulado al corte). Esta cantidad **ya no forma parte de los huevos cargados**. Es una salida **pre-carga**: ≤ recibidos, y cargados + no incubables + fosa ≤ recibidos. Vacío = no se conoce; `0` = cero conocido. |
| `chicks_hatched` | no | Pollitos ya nacidos antes del corte. |
| `chicks_available` | no | Pollitos nacidos que siguen en planta sin despachar. |

### Huevos no incubables y huevos fértiles a fosa (SPEC 018 · v4)

- **No incubables** (`eggs_non_incubable_oversized`, `_dirty`, `_broken`): son huevos **recibidos** en la planta que al corte se clasificaron como **no incubables** (extra grande, sucio, roto). Siempre **acumulado hasta el corte**. Celda **vacía = no se conoce** el dato; `0` = cero conocido; `N/A` no se admite.
- El **total de no incubables lo calcula el sistema** (`extra grande + sucios + rotos`) y **no se digita**: solo se obtiene cuando **los tres** son conocidos; si falta alguno, el total queda como desconocido (nunca se suma a medias).
- **Balance**: `recibidos = no incubables + huevos fértiles a fosa + cargados + huevo aún por cargar` (más el huevo que quede sin clasificar). No incubables y fosa se restan **una sola vez**, del saldo recibido → cargado, **nunca** de lo cargado. Por eso `cargados + no incubables + fosa` **no puede superar** a los recibidos (si los supera, la fila se rechaza; puede ser igual), y **la diferencia que queda es huevo recibido que aún no se ha cargado**: no es un error y no se fuerza a cero.
- **Histórico**: las cargas de Incubadora **ya aplicadas con la plantilla v3 conservan su dato histórico de Huevos descartados**; no se desglosan.

### Huevos fértiles a fosa (regla vigente · `OD-HATCH-V4-02 = RATIFIED`, 2026-11-26 · SPEC 018 §9)

> La regla anterior (`OD-HATCH-V4-01`, que situaba la fosa **después** de la carga) queda **SUPERSEDED** por nueva evidencia de la usuaria funcional: la fosa se descuenta **desde el principio** de los huevos recibidos; cuando se cargan los huevos, esa cantidad ya fue descontada.

- Los huevos fértiles a fosa son huevos **recibidos** que se envían a fosa **antes de cargarse** en incubadora. Es una salida **PRE-CARGA**, como los no incubables, pero es un concepto **distinto** de ellos: no se suma al total de no incubables ni a los huevos descartados (histórico V3).
- **Dos etapas, sin mezclar**:
  - **Pre-carga**: `recibidos → no incubables (extra grande, sucio, roto) · fosa · cargados · aún por cargar`. Regla: `cargados + extra grande + sucios + rotos + fosa ≤ recibidos` (puede ser igual; si la supera, la fila se rechaza). La fosa sola tampoco puede superar a los recibidos.
  - **Post-carga**: `cargados → transferidos · en proceso`. Regla: `transferidos ≤ cargados`. La fosa **no** interviene aquí.
- **Saldo disponible para cargar** = `recibidos − cargados − extra grande − sucios − rotos − fosa`, y **solo** cuando **todos** son conocidos; si falta alguno, el saldo queda **desconocido** (nunca se toma un vacío por `0`). Ejemplo: 10 000 recibidos, 8 500 cargados, 200 + 200 + 100 no incubables y 200 a fosa ⇒ saldo **800**.
- **Huevos en proceso** = `cargados − transferidos`, solo cuando ambos son conocidos. **No** se resta la fosa (ya se descontó antes de cargar). En el ejemplo, con 8 000 transferidos ⇒ en proceso **500** (no 300).
- En la operación diaria, la primera carga de incubación posterior al corte se valida contra el huevo recibido aún por cargar (BR-03), que descuenta no incubables y fosa **conocidos**; un dato desconocido no se descuenta.
- La vista previa muestra las dos etapas en orden: recibidos, no incubables, fosa, cargados y «Saldo disponible para cargar (derivado)»; luego transferidos y «Huevos en proceso (derivado)».

### «Generación» vs «Origen del huevo» (SPEC 009)

Son dos cosas distintas y **ambas** se registran:

- **`generation`** = naturaleza biológica del huevo (`grandparent` / `breeder`). **No** admite `purchased`.
- **`egg_origin`** = origen comercial del huevo, **obligatorio**:
  - **`internal`** (propio): si indica `source_lot_code`, se valida contra un lote interno compatible, como hasta ahora.
  - **`purchased`** (comprado): **no** hace falta un lote interno; basta con registrar la procedencia externa en `source_system`/`source_reference`. No se exige ni se inventa una orden de compra.

---

## 6 · Errores más frecuentes

| Mensaje | Causa | Solución |
|---|---|---|
| «Campo obligatorio sin valor» | Un obligatorio vacío (p. ej. mortalidad en Reproductoras, `egg_origin` en Incubadora, vivas, huevos recibidos/cargados) | Indique el valor real; si es cero, escriba `0`. |
| «N/A no es válido en un campo obligatorio» | `N/A` en un obligatorio | Ponga el valor; `0` si es cero real. |
| «La línea genética no existe…» / «La raza no existe…» / «La raza no pertenece a la línea…» | Línea/raza fuera de `Catalogos` o raza de otra línea | Use valores de `Catalogos` (maestro interno de Global Avícola). |
| «La granja/planta no existe o está inactiva» | Código fuera de `Catalogos` o inactivo | Use un código activo de su empresa. |
| «Valor fuera de la lista permitida» | `generation` o `egg_origin` con un valor no admitido | `generation` ∈ {grandparent, breeder}; `egg_origin` ∈ {internal, purchased}. |
| «La plantilla … descargue la plantilla v4 de hatchery» | Subió una plantilla de Incubadora v3 (ya no vigente) | Descargue la plantilla **v4** de Incubadora. |
| «La plantilla no trae filas de datos» | Archivo sin filas en `Datos` | Complete la hoja `Datos`. |

---

## 7 · Después de cargar

Subida sin errores → **vista previa → envío → aprobación (por otro usuario) → aplicar**. Al aplicar, cada dato queda en su lugar (el lote con su fase, granja, genética, origen del huevo y saldo de apertura) y la operación sigue con normalidad. El **primer evento operativo** sobre esos lotes debe tener **fecha posterior al día del corte**, para no contar dos veces el histórico cargado.

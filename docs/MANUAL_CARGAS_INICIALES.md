# Manual de las plantillas de Cargas Iniciales (saldos de apertura)

Este manual explica las **cuatro plantillas Excel de carga inicial** (cutover) de Global Avícola y cómo rellenarlas, con los ajustes acordados con los KeyUser (SPEC 009, 2026-10-22).

Las cuatro plantillas, tal como las genera el sistema hoy, están en **`docs/plantillas_carga_inicial/`**:

| Unidad de negocio | Archivo | Versión |
|---|---|---|
| Progenitoras (grandparent) | `cutover_template_grandparent_v2.xlsx` | v2 |
| Reproductoras (breeder) | `cutover_template_breeder_v2.xlsx` | v2 |
| Incubadora (hatchery) | `cutover_template_hatchery_v3.xlsx` | **v3** |
| Engorde (broiler) | `cutover_template_broiler_v2.xlsx` | v2 |

> Cada carga descarga **su propia** plantilla desde el sistema (la unidad y la fecha de corte las fija la carga). Las de esta carpeta son copias de referencia para conocer el formato vigente. **La plantilla de Incubadora es ahora v3**: una plantilla v2 antigua de Incubadora será rechazada con el mensaje «descargue la plantilla v3»; las demás unidades siguen en v2.

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
| `accumulated_feed_kg` | no | kg | Alimento acumulado. |
| `current_avg_weight_g` | no | g | Peso promedio actual del ave. |
| `accumulated_egg_production` | no | huevos | Producción acumulada. **`N/A` en fase `CRIA`.** |
| `accumulated_eggs_to_hatchery` | no | huevos | Huevos enviados a incubadora. **`N/A` en fase `CRIA`.** |

### Mortalidad histórica — diferencia entre Reproductoras y Progenitoras (SPEC 009)

- **Reproductoras (breeder): `historical_mortality_males` y `historical_mortality_females` son OBLIGATORIAS.** Si no la conoce con certeza, consulte el dato real; **no** puede dejarse vacía. **`0` es un valor válido** (cero real). Dejarla en blanco da el error «Campo obligatorio sin valor».
- **Progenitoras (grandparent): siguen siendo opcionales** (vacío = desconocido/UNKNOWN).

Consistencia (solo si todas las piezas son conocidas): `alojadas − mortalidad − descartes = vivas`, por sexo; y `huevos a incubadora ≤ huevos producidos`.

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

## 5 · Plantilla de Incubadora (proceso de incubación) — v3

Describe un proceso de incubación en curso al corte. **Versión v3** por la nueva columna `egg_origin`.

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
| `eggs_transferred` | no | Huevos transferidos a nacedora (≤ cargados). |
| `eggs_discarded` | no | Huevos descartados (≤ cargados). |
| `chicks_hatched` | no | Pollitos ya nacidos antes del corte. |
| `chicks_available` | no | Pollitos nacidos que siguen en planta sin despachar. |

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
| «La plantilla … descargue la plantilla v3 de hatchery» | Subió una plantilla de Incubadora v2 antigua | Descargue la plantilla **v3** de Incubadora. |
| «La plantilla no trae filas de datos» | Archivo sin filas en `Datos` | Complete la hoja `Datos`. |

---

## 7 · Después de cargar

Subida sin errores → **vista previa → envío → aprobación (por otro usuario) → aplicar**. Al aplicar, cada dato queda en su lugar (el lote con su fase, granja, genética, origen del huevo y saldo de apertura) y la operación sigue con normalidad. El **primer evento operativo** sobre esos lotes debe tener **fecha posterior al día del corte**, para no contar dos veces el histórico cargado.

# Manual de las plantillas de Cargas Iniciales (saldos de apertura)

Guía para llenar correctamente las plantillas de carga inicial, campo por campo, por unidad de negocio. Pensada para quien prepara los datos del arranque («corte»).

Existe **una plantilla por unidad de negocio**, descargable desde la pantalla *Cargas Iniciales* en Excel (`.xlsx`) o CSV (`.csv`):

| Unidad de negocio | Nombre de la plantilla | Qué representa cada fila |
|---|---|---|
| Progenitoras (abuelas) | `cutover_template_grandparent_v2` | Un lote de abuelas en cría o producción |
| Reproductoras | `cutover_template_breeder_v2` | Un lote de reproductoras en cría o producción |
| Pollo de engorde | `cutover_template_broiler_v2` | Un lote de engorde |
| Incubadora | `cutover_template_hatchery_v2` | Un proceso de incubación en curso |

> La plantilla que descargue queda **ligada a la carga** que creó (a su unidad y su fecha de corte). Descárguela siempre desde la carga, no cambie el selector después. No modifique la fila de cabecera de la hoja `Datos` ni la hoja `Meta`.

---

## 1 · Cómo funciona cualquier plantilla

### 1.1 · Hojas del archivo Excel

- **Instrucciones**: explica cada campo (es la versión corta de este manual, generada por el sistema).
- **Meta**: identifica la plantilla (versión `v2`, unidad, empresa, fecha de corte). No se toca.
- **Datos**: aquí se escriben las filas. Una fila = un lote (o un proceso de incubadora).
- **Catalogos**: los códigos válidos de **su empresa** para esa unidad (granjas, galpones, fases, líneas, razas, plantas, incubadoras, nacedoras…). Úselos para no equivocar un código.

En CSV solo existe la fila de cabecera y los datos; la información de unidad y versión la aporta la propia carga.

### 1.2 · La regla más importante: vacío, 0 y N/A **no** son lo mismo

Cada celda de una métrica se interpreta así:

| Lo que escribe | Significado | Ejemplo de uso |
|---|---|---|
| **(celda vacía)** | **DESCONOCIDO** (UNKNOWN): no se sabe el dato | No se tiene la mortalidad histórica de ese lote |
| **`0`** | **CERO REAL** (conocido): el valor es realmente cero | Ese lote no tuvo descartes: cero |
| **`N/A`** | **NO APLICA**: la métrica no corresponde a ese lote/fase | Huevos producidos en un lote que todavía está en cría |

El sistema conserva esta diferencia en todo el recorrido. **Nunca** convierte un desconocido en cero. Por eso dejar una celda vacía no es lo mismo que poner `0`.

### 1.3 · Tipos de variable que encontrará

| Tipo | Qué acepta | Qué NO acepta | Ejemplo correcto |
|---|---|---|---|
| **Texto** | Letras, números y signos como texto | — | `GR-01`, `Lote Norte 3` |
| **Código de catálogo** | Un texto que **debe existir** en la hoja `Catalogos` de su empresa | Un código inventado o de otra empresa | `GR-01` (granja) |
| **Entero** | Número **entero** ≥ 0, sin decimales y **sin separador de miles** | `1.200`, `1,200`, `12.5`, texto | `1200` |
| **Decimal** | Número ≥ 0 con **punto** decimal | Coma decimal (`120000,5`), separador de miles | `120000.5` |
| **Fecha** | Formato **AAAA-MM-DD** | `01/08/2026`, `1-ago-2026` | `2026-08-01` |
| **Lista** | Uno de los valores permitidos exactos | Cualquier otro texto | `mixed`, `breeder` |

Reglas de números:
- **Los enteros son enteros**: escriba `1200`, no `1.200` ni `1,200` (el punto o la coma se interpretan como error). Si por formato de Excel aparece `1200.0`, el sistema lo acepta como `1200`.
- **Los decimales llevan punto**: `120000.5`. La coma no es decimal.
- **Pesos en gramos**, **alimento en kilogramos**. El peso promedio del ave debe ser **mayor que cero** (no admite 0).
- Ningún número puede ser negativo.

### 1.4 · Formatos de archivo, límites y validación

- Acepta `.xlsx` y `.csv`. No acepta libros con macros (`.xlsm`) ni fórmulas dentro de las celdas (escriba valores, no fórmulas).
- Máximo **5 MB**, **5000 filas** de datos y **60 columnas**.
- Al subir, el sistema valida cada fila y muestra los errores con **fila, campo, código, mensaje y valor recibido**; puede **descargar el reporte de errores** para corregir en bloque y volver a subir.
- Una plantilla **sin filas** no se da por válida.

### 1.5 · Obligatorio, vacío y N/A por campo

En las tablas de abajo, cada campo indica:
- **Obligatorio**: debe tener un valor; no admite vacío ni `N/A`.
- **Admite vacío (UNKNOWN)**: puede dejarlo en blanco si no conoce el dato.
- **Admite N/A**: puede marcar que no aplica.

---

## 2 · Campos comunes de identificación del lote

Estos campos encabezan las plantillas de **Progenitoras, Reproductoras y Pollo de Engorde** (la de Incubadora tiene los suyos, ver §5).

| Campo | Qué carga | Tipo | ¿Decimales? | Obligatorio | Vacío | N/A | Ejemplo | Reglas |
|---|---|---|---|---|---|---|---|---|
| `legacy_lot_code` | Código del lote en el sistema anterior | Texto (≤60) | — | **Sí** | No | No | `GP-2025-014` | Único en el archivo y en la empresa |
| `existing_lot_code` | Código de un lote que **ya existe** en Global Avícola, para reutilizarlo en vez de crear uno nuevo | Código de catálogo | — | No | — | — | `LOTE-2026-01` | El lote debe ser de la misma empresa, de la misma unidad, activo y sin eventos |
| `farm_code` | Granja donde está el lote | Código de catálogo (granja) | — | **Sí** | No | No | `GR-01` | Debe existir y estar activa en su empresa |
| `house_name` | Galpón dentro de la granja | Código de catálogo (galpón) | — | No | Sí | No | `G-03` | Debe pertenecer a la granja indicada |
| `area_code` | Área funcional | Código de catálogo (área) | — | No | Sí | No | `AREA-1` | Debe existir en su empresa |
| `productive_phase_code` | Fase real del lote al corte | Lista | — | **Sí** | No | No | `PROD` | Progenitoras/Reproductoras: `CRIA` o `PROD`. Engorde: `ENGORDE` |
| `real_start_date` | Fecha real de inicio del lote (alojamiento) | Fecha | — | **Sí** | No | No | `2025-11-03` | Debe ser anterior o igual al corte |
| `phase_start_date` | Fecha de inicio de la fase declarada | Fecha | — | No | Sí | No | `2026-04-20` | Entre la fecha de inicio del lote y el corte. Si se deja vacía, se toma `real_start_date` |
| `genetic_line_code` | Línea genética | Código de catálogo (línea) | — | No | Sí | No | `ROSS-308` | Debe existir |
| `breed_name` | Raza dentro de la línea | Código de catálogo (raza) | — | No | Sí | No | `Ross 308 AP` | Debe pertenecer a la línea y a la unidad |
| `sex` | Sexo del lote | Lista | — | No | Sí | No | `mixed` | Valores: `male`, `female`, `mixed` |

---

## 3 · Plantilla de Progenitoras y Reproductoras

Progenitoras (`grandparent`) y Reproductoras (`breeder`) usan **el mismo conjunto de campos**. La única diferencia la marca `productive_phase_code`: un lote en **cría** (`CRIA`) todavía no produce huevo, y un lote en **producción** (`PROD`) sí.

A los campos comunes de identificación (§2) se suman estas métricas:

| Campo | Qué carga | Tipo | ¿Decimales? | Obligatorio | Vacío | N/A | Ejemplo | Reglas |
|---|---|---|---|---|---|---|---|---|
| `live_males` | Machos **vivos** al momento del corte | Entero | No | **Sí** | No | No | `1000` | Es el saldo vivo; el histórico no se resta |
| `live_females` | Hembras **vivas** al corte | Entero | No | **Sí** | No | No | `9000` | Igual |
| `birds_placed_males` | Machos **alojados** originalmente (histórico) | Entero | No | No | Sí | No | `1100` | Sirve para cuadrar: alojadas − mortalidad − descartes = vivas |
| `birds_placed_females` | Hembras alojadas originalmente | Entero | No | No | Sí | No | `9600` | Igual |
| `historical_mortality_males` | Mortalidad acumulada de machos **antes** del corte | Entero | No | No | Sí | No | `50` | Histórico; no se vuelve a descontar |
| `historical_mortality_females` | Mortalidad acumulada de hembras antes del corte | Entero | No | No | Sí | No | `450` | Igual |
| `historical_culls_males` | Descartes acumulados de machos antes del corte | Entero | No | No | Sí | No | `0` | `0` = cero real |
| `historical_culls_females` | Descartes acumulados de hembras antes del corte | Entero | No | No | Sí | No | `0` | Igual |
| `accumulated_feed_kg` | Alimento acumulado consumido antes del corte | Decimal | **Sí** (kg) | No | Sí | No | `120000.5` | En kilogramos |
| `current_avg_weight_g` | Peso promedio actual del ave al corte | Decimal | **Sí** (g) | No | Sí | No | `3200` | En gramos, **mayor que 0** |
| `accumulated_egg_production` | Huevos producidos acumulados antes del corte | Entero | No | No | Sí | **Sí** | `180000` | En **cría** debe ir vacío o `N/A` (no aplica) |
| `accumulated_eggs_to_hatchery` | Huevos enviados a incubadora acumulados antes del corte | Entero | No | No | Sí | **Sí** | `150000` | No puede superar los huevos producidos; en cría, `N/A` |

**Cómo tratar el sexo en estas métricas**: cada métrica tiene su versión de machos y de hembras. Se considera *conocida* solo si ambos sexos son conocidos; si deja uno vacío, la pareja queda como desconocida (el sistema no inventa el sexo que falta).

**Ejemplo de una fila (reproductoras en producción, histórico de mortalidad desconocido):**

```text
legacy_lot_code=REP-2026-07 · farm_code=GR-01 · house_name=G-03 · productive_phase_code=PROD
real_start_date=2025-08-01 · live_males=1000 · live_females=9000
historical_mortality_males=(vacío) · historical_mortality_females=(vacío)
historical_culls_males=0 · historical_culls_females=0
accumulated_feed_kg=120000.5 · current_avg_weight_g=3200
accumulated_egg_production=180000 · accumulated_eggs_to_hatchery=150000 · source_system=LEGACY
```

**Ejemplo de una fila en cría (las métricas de huevo no aplican):**

```text
legacy_lot_code=REP-CRIA-02 · farm_code=GR-01 · productive_phase_code=CRIA
real_start_date=2026-06-01 · live_males=500 · live_females=4500
accumulated_egg_production=N/A · accumulated_eggs_to_hatchery=N/A
```

---

## 4 · Plantilla de Pollo de Engorde

El engorde maneja la población como **mixta** (sin separar sexo). A los campos comunes de identificación (§2) —con `productive_phase_code` siempre `ENGORDE`— se suman:

| Campo | Qué carga | Tipo | ¿Decimales? | Obligatorio | Vacío | N/A | Ejemplo | Reglas |
|---|---|---|---|---|---|---|---|---|
| `live_birds` | Aves **vivas** (mixtas) al corte | Entero | No | **Sí** | No | No | `10000` | Saldo vivo |
| `age_days` | Edad del lote en días al corte | Entero | No | No | Sí | No | `20` | Si se deja vacío, se calcula desde `real_start_date` |
| `accumulated_birds_received` | Aves recibidas (alojadas) acumuladas antes del corte | Entero | No | No | Sí | No | `10500` | Sirve para cuadrar con las vivas |
| `historical_mortality` | Mortalidad acumulada antes del corte | Entero | No | No | Sí | No | `300` | Histórico |
| `historical_culls` | Descartes acumulados antes del corte | Entero | No | No | Sí | No | `200` | Histórico |
| `partial_outbound_birds` | Aves salidas parcialmente a planta antes del corte | Entero | No | No | Sí | **Sí** | `0` | `N/A` si no hubo salidas parciales |
| `accumulated_feed_kg` | Alimento acumulado antes del corte | Decimal | **Sí** (kg) | No | Sí | No | `15000` | En kilogramos |
| `current_avg_weight_g` | Peso promedio actual del ave al corte | Decimal | **Sí** (g) | No | Sí | No | `900` | En gramos, mayor que 0 |

**Cuadre (solo si están todos los datos conocidos):** `recibidas − mortalidad − descartes − salidas parciales = vivas`. Si alguno va vacío o `N/A`, el sistema no exige el cuadre (no inventa certeza).

**Ejemplo:**

```text
legacy_lot_code=ENG-2026-33 · farm_code=GR-01 · house_name=G-07 · productive_phase_code=ENGORDE
real_start_date=2026-09-20 · live_birds=10000 · age_days=20
accumulated_birds_received=10500 · historical_mortality=300 · historical_culls=200
partial_outbound_birds=0 · accumulated_feed_kg=15000 · current_avg_weight_g=900
```

---

## 5 · Plantilla de Incubadora

Representa un **proceso de incubación en curso** el día del corte. Tiene sus propios campos de identificación (no usa granja/galpón ni fase: la fase es Incubación de forma implícita).

| Campo | Qué carga | Tipo | ¿Decimales? | Obligatorio | Vacío | N/A | Ejemplo | Reglas |
|---|---|---|---|---|---|---|---|---|
| `legacy_lot_code` | Código del proceso/lote en el sistema anterior | Texto (≤60) | — | **Sí** | No | No | `INC-2026-07` | Único en el archivo y la empresa |
| `existing_lot_code` | Lote de incubadora ya existente para reutilizar | Código de catálogo | — | No | — | — | `INC-2026-01` | Misma empresa, activo, sin eventos |
| `hatchery_code` | Planta de incubación | Código de catálogo (planta) | — | **Sí** | No | No | `INC-01` | Debe existir y estar activa en su empresa |
| `incubator_name` | Incubadora dentro de la planta | Código de catálogo (incubadora) | — | No | Sí | No | `INC-A1` | Debe pertenecer a la planta |
| `hatcher_name` | Nacedora dentro de la planta | Código de catálogo (nacedora) | — | No | Sí | No | `NAC-1` | Debe pertenecer a la planta |
| `source_lot_code` | Lote de abuelas/reproductoras que originó los huevos | Código de catálogo (lote origen) | — | No | Sí | No | `REP-2026-07` | Debe ser un lote grandparent o breeder de su empresa, coherente con `generation` |
| `generation` | Generación del huevo incubado | Lista | — | No | Sí | No | `breeder` | `grandparent` (→ pollito reproductor) o `breeder` (→ pollito de engorde) |
| `reception_date` | Fecha de recepción del huevo en la planta | Fecha | — | **Sí** | No | No | `2026-09-20` | Anterior o igual al corte |
| `set_date` | Fecha de carga en incubadora | Fecha | — | No | Sí | **Sí** | `2026-09-22` | Entre la recepción y el corte. `N/A` si aún no se cargó |
| `expected_hatch_date` | Fecha prevista de nacimiento | Fecha | — | No | Sí | **Sí** | `2026-10-13` | Posterior o igual a la carga |
| `eggs_received` | Huevos fértiles recibidos en la planta | Entero | No | **Sí** | No | No | `10000` | Saldo de huevo en planta = recibidos − cargados |
| `eggs_set` | Huevos ya cargados en incubadora | Entero | No | **Sí** | No | No | `9000` | No puede superar los recibidos |
| `eggs_transferred` | Huevos ya transferidos a nacedora | Entero | No | No | Sí | **Sí** | `0` | No puede superar los cargados |
| `eggs_discarded` | Huevos descartados del proceso (ovoscopia, rotos) | Entero | No | No | Sí | **Sí** | `100` | No puede superar los cargados |
| `chicks_hatched` | Pollitos ya nacidos del proceso antes del corte | Entero | No | No | Sí | **Sí** | `0` | No puede superar los transferidos (o los cargados) |
| `chicks_available` | Pollitos nacidos que siguen en planta sin despachar al corte | Entero | No | No | Sí | **Sí** | `0` | No puede superar los nacidos |

**Invariantes que el sistema verifica** (solo cuando los datos son conocidos): `eggs_set ≤ eggs_received`; `eggs_transferred ≤ eggs_set`; `eggs_discarded ≤ eggs_set`; `transferidos + descartados ≤ cargados`; `chicks_hatched ≤ eggs_transferred`; `chicks_available ≤ chicks_hatched`. Las fechas deben ir en orden: recepción ≤ carga ≤ corte, y nacimiento previsto ≥ carga.

**Ejemplo (proceso cargado, aún sin nacimientos):**

```text
legacy_lot_code=INC-2026-07 · hatchery_code=INC-01 · incubator_name=INC-A1
generation=breeder · reception_date=2026-09-20 · set_date=2026-09-22 · expected_hatch_date=2026-10-13
eggs_received=10000 · eggs_set=9000 · eggs_transferred=0 · eggs_discarded=100
chicks_hatched=0 · chicks_available=0 · source_system=LEGACY
```

---

## 6 · Campos de procedencia (comunes a todas las plantillas)

Van al final de cada plantilla y sirven para la trazabilidad; ninguno es obligatorio.

| Campo | Qué carga | Tipo | Obligatorio | Ejemplo |
|---|---|---|---|---|
| `source_system` | Sistema de origen del dato | Texto (≤40) | No | `LEGACY` |
| `source_reference` | Referencia en el sistema de origen (documento, planilla) | Texto (≤200) | No | `PLANILLA-2026-10` |
| `notes` | Notas libres | Texto | No | `Lote recibido de granja externa` |

> `notes` es solo una nota: **nunca** reemplaza a un campo del contrato. Si un dato tiene su propio campo, va en ese campo, no en las notas.

---

## 7 · Errores más frecuentes y cómo evitarlos

| Síntoma | Causa | Solución |
|---|---|---|
| «Número entero ≥ 0 esperado» | Escribió `1.200` o `1,200` | Quite el separador de miles: `1200` |
| «Número decimal ≥ 0 esperado» | Usó coma decimal (`120000,5`) | Use punto: `120000.5` |
| «Fecha inválida» | Formato `01/08/2026` | Use `2026-08-01` |
| «N/A no es válido en un campo obligatorio» | Puso `N/A` en vivas, huevos recibidos, etc. | Indique el valor real; si es cero, escriba `0` |
| «Métrica de producción con valor en fase CRIA» | Cargó huevos en un lote en cría | Deje esas celdas vacías o en `N/A` |
| «La granja no existe / está inactiva» | Código que no está en `Catalogos` o maestro inactivo | Use un código de la hoja `Catalogos` de su empresa |
| «El galpón no pertenece a la granja» | Galpón de otra granja | Verifique en `Catalogos` el galpón que corresponde a esa granja |
| «La plantilla es de otra unidad» | Subió a una carga la plantilla de otra unidad | Descargue la plantilla desde la carga correcta |
| «La plantilla no trae filas de datos» | Subió el archivo vacío | Complete la hoja `Datos` antes de subir |

---

## 8 · Después de cargar

Una vez subida sin errores, la carga pasa por **vista previa → envío → aprobación (por otro usuario) → aplicar**. Al aplicar, cada dato queda en su lugar (el lote con su fase, su granja, su genética y su saldo de apertura) y la operación continúa con normalidad. El primer evento operativo que registre sobre esos lotes debe tener **fecha posterior al día del corte**: así el histórico cargado no se cuenta dos veces.

---

## 9 · Novedades de la sesión con los KeyUser (2026-10-22)

Estos ajustes nacieron de la revisión de las plantillas con los KeyUser del área avícola.

### 9.1 · De dónde vienen los datos maestros (SAP vs Global Avícola)

La hoja `Catalogos` añade una columna **`source`** que indica quién gobierna cada maestro:

- **`SAP`** · granjas (`farm`) y galpones (`house`): su codificación proviene del ERP (SAP), a través de la sincronización autorizada de solo lectura. La plantilla muestra únicamente los valores ya recibidos y promovidos al sistema local; **nunca se inventan códigos SAP**.
- **`GLOBAL_AVICOLA`** · el resto (línea genética, raza, fases, áreas, plantas de incubación, incubadoras, nacedoras, lotes): son maestros internos de Global Avícola.

En particular, **la línea genética (`genetic_line_code`) y la raza (`breed_name`) son maestros internos de Global Avícola, no de SAP**. Si el código o el nombre no existe (o la raza no pertenece a la línea indicada), la fila se marca inválida con un mensaje claro (`La línea genética no existe…`, `La raza no existe…`, `La raza no pertenece a la línea…`). El sistema **no crea** la línea ni la raza automáticamente: elija un valor de la hoja `Catalogos`.

### 9.2 · Reproductoras: mortalidad histórica obligatoria

En la plantilla de **Reproductoras**, la **mortalidad acumulada de machos y de hembras** (`historical_mortality_males`, `historical_mortality_females`) pasa a ser **obligatoria**. Si no la conoce con certeza, consulte el dato real: **no** se puede dejar vacía. **`0` es un valor válido** (cero real); dejarla en blanco da el error «Campo obligatorio sin valor». En **Progenitoras** estos campos siguen siendo opcionales (vacío = desconocido).

### 9.3 · Incubadora: «Generación» y «Origen del huevo» son cosas distintas

- **Generación (`generation`)** describe la *naturaleza biológica* del huevo: `grandparent` (huevo de progenitoras, del que nace pollito reproductor) o `breeder` (huevo de reproductoras, del que nace pollito de engorde). **No** admite otros valores.
- **Origen del huevo (`egg_origin`)**, campo **nuevo y obligatorio**, describe el *origen comercial*: **`internal`** (propio / interno de Global Avícola) o **`purchased`** (comprado a un tercero).
  - Con `internal`, el `source_lot_code` (lote de reproductoras/progenitoras que originó los huevos) se valida como hasta ahora contra un lote interno compatible.
  - Con `purchased`, **no** hace falta un lote interno: basta con registrar la procedencia externa (`source_system`, `source_reference`). No se exige ni se inventa una orden de compra.

La plantilla de Incubadora cambia de versión a **v3** por esta columna nueva. Si intenta subir una plantilla de incubadora anterior (v2), el sistema se lo indicará y le pedirá descargar la vigente; las plantillas de las demás unidades siguen en v2 sin cambios.

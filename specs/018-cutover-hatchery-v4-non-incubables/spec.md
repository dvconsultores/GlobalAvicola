# SPEC 018 — Cutover Incubadora v4: desglose de no incubables + huevos fértiles a fosa

Amendment de SPEC 006 (cutover v2) / SPEC 009 (incubadora v3, `egg_origin`) / GA-REQ-061. Identificador del mandato:
`CUTOVER-HATCHERY-V4-NON-INCUBABLE-BREAKDOWN` (`GA-CUTOVER-HATCHERY-V4-NON-INCUBABLES-PIT`, 2026-11-20).
Baseline `main == develop == bb91338`. Sin cambios en SAP ni en otras BU.

## 1. DISCOVERY / DOMAIN REPORT

### 1.1 Contrato V3 vigente
- Plantilla `cutover_template_hatchery_v3.xlsx`; `template_version=v3`; `schema_id=CUTOVER_HATCHERY_V3`; `HATCHERY_TEMPLATE_VERSION="v3"` (`app/cutover/contracts.py`). Una plantilla por BU (`ONE_CONTRACT_PER_BUSINESS_UNIT`).
- 20 campos en `Datos`. Métricas: `eggs_received` (obligatorio), `eggs_set` (obligatorio), `eggs_transferred`, `eggs_discarded`, `chicks_hatched`, `chicks_available` (opcionales; vacío = UNKNOWN, `0` = cero conocido, `N/A` permitido).
- Persistencia: `hatchery_openings` (`eggs_received|set|transferred|discarded` + `*_status`); pollitos en `opening_balances`.
- Invariantes V3 (`cutover/validation.py::_consistencia_incubadora`): `set ≤ received`; `transferred ≤ set`; `discarded ≤ set`; `transferred + discarded ≤ set`; `chicks_hatched ≤ transferred` (o `≤ set`); `chicks_available ≤ chicks_hatched`. Derivado: `eggs_in_process = set − transferred − discarded`.
- Parser: columnas ajenas al contrato = rechazo (`COLUMNS_UNKNOWN`), faltantes = rechazo; versión distinta de la vigente de la BU = rechazo con «descargue la plantilla vigente».

### 1.2 Semántica real de `eggs_discarded`
| Dónde | Qué significa |
|---|---|
| Código/contrato V3 | descarte **posterior a la carga** (ovoscopia/rotos del proceso), **resta de `eggs_set`** (`eggs_in_process = set − transferred − discarded`; `discarded ≤ set`). |
| Datos entregados (4 procesos) | `eggs_discarded = eggs_received − eggs_set` exacto: se usó como lo **no cargado** (pre-carga). **Ambigüedad real de V3**: dato y contrato divergen; con esos datos `eggs_in_process` V3 resta dos veces lo mismo. No se corrige por suposición ni se reescribe: queda como observación O-13 (V3 histórica intacta). |

### 1.3 Consumidores de `eggs_discarded`
| Consumidor | Interpretación | ¿Derivable de los 3 no incubables? | Cambio |
|---|---|---|---|
| `cutover/contracts.py` (FieldSpec) | campo de entrada V3 | **No**: V4 lo elimina del contrato | quitar de V4 |
| `cutover/validation.py` (`≤set`, `transferred+discarded≤set`, `eggs_in_process`) | descarte post-carga | **No**: los no incubables nunca entraron en `eggs_set`; restarlos de `set` es el doble conteo del §40 | V4: reglas nuevas (§2) |
| `cutover/models.py` + `service.py` (`_hatchery_opening`, detalle/reconciliación) | persistencia y lectura | no | columna se **conserva** (histórico V3); V4 escribe NULL + `NOT_APPLICABLE` |
| `cutover/service.py` `PREVIEW_COLUMNS` | columnas de preview | n/a | sustituir por los 4 campos nuevos |
| `operations/validators.py` BR-03 (`get_hatchery_egg_balance`) | no usa `eggs_discarded`; usa `received − set` como saldo disponible para cargar | n/a | **restar los no incubables conocidos** (§2 D-4) |
| `seeds/qa_integral_dataset.py` | datos sintéticos QA | n/a | migrar a vocabulario V4 |
| `scripts/cutover_v2_docs.py`, `docs/MANUAL_CARGAS_INICIALES.md`, locales, `test-support/cutover.ts`, tests | docs/UI/E2E | n/a | actualizar |
| KPI/reportes de incubadora (`reports/service.py`) | **no** leen `eggs_discarded` | n/a | sin impacto (`rendimiento` es solo una etiqueta del contrato) |

### 1.4 Dominio de no incubables
Vocabulario operativo existente: `EggMovement.egg_type ∈ {fertile, dirty, broken, infertile, discarded, commercial}`; solo `fertile` cuenta como disponible (`cuenta_como_disponible`, BR-02/BR-03). **`dirty` y `broken` ya existen**; **`oversized` (extra grande) no existe** y no hay evento de fosa: `OPERATIONAL_MODEL_GAP` (no se amplía la operación en este ciclo). Nombres canónicos V4: `eggs_non_incubable_oversized | _dirty | _broken` (reutilizan los tokens `dirty`/`broken`).
- ¿Son exhaustivos respecto de `received − set`? **No**: `received − set` incluye legítimamente huevo recibido **aún no cargado** (el saldo BR-03 «recibidos − cargados» existe precisamente para eso). Por tanto **no se impone igualdad**; solo la desigualdad segura.

### 1.5 `fertile_eggs_to_pit`
- No existe evento ni campo equivalente en el sistema (no hay «fosa» en código, docs ni specs).
- Etapa **no determinable** con la evidencia del repo (antes/después de carga u ovoscopia). Lo único cierto bajo cualquier lectura: son huevos fértiles **recibidos** ⇒ `fertile_eggs_to_pit ≤ eggs_received`.
- `OWNER_DOMAIN_DECISION_REQUIRED` (OD-HATCH-V4-01): su relación con `eggs_set`/`eggs_transferred` y su resta en `eggs_in_process`. No bloquea la captura (§17 del mandato).

### 1.6 Compatibilidad
- V3 histórica aplicada: intacta (columnas, valores, lectura). Desglose V4 de esos registros = UNKNOWN (server_default de migración).
- Nueva carga V3: **rechazada** por el parser existente (versión ≠ vigente de la BU) con instrucción de descargar v4.
- V4: contrato nuevo.

## 2. Decisiones de contrato (V4)
- **D-1 Versión**: `HATCHERY_TEMPLATE_VERSION = "v4"`, `schema_id = CUTOVER_HATCHERY_V4`, archivo `cutover_template_hatchery_v4.xlsx` (convención `cutover_template_<bu>_<version>`). `SUPPORTED_TEMPLATE_VERSIONS` suma `v4`; `v3` se conserva en el conjunto (lo sigue usando aves) y el rechazo para incubadora lo hace la regla «versión ≠ vigente».
- **D-2 `eggs_discarded`**: fuera del contrato V4 (la cabecera con `eggs_discarded` se **rechaza** como columna ajena). En BD se **conserva** (V3). V4 aplica `eggs_discarded=NULL`, `eggs_discarded_status=NOT_APPLICABLE`. **No se deriva** del total no incubable (rompería `eggs_in_process`).
- **D-3 Total derivado**: `eggs_non_incubable_total = oversized + dirty + broken` **solo si los tres son KNOWN**; si falta alguno = UNKNOWN (nunca suma parcial). Se calcula al leer (preview/detalle/reporte), no se persiste.
- **D-4 Posición en el balance**: los no incubables son una **clasificación del huevo recibido**, no parte de lo cargado. `received = set + no_incubables + saldo_por_cargar (+ no clasificado)`.
  - Validación (cutover): cada componente KNOWN `≤ received`; `set + Σ(componentes KNOWN) ≤ received` (error `CONSISTENCY_MISMATCH` aunque falte algún componente: la suma conocida es cota inferior). **Sin igualdad.**
  - BR-03 apertura: `disponible_para_cargar = received − set − Σ(componentes KNOWN)` (un UNKNOWN **no se resta ni se inventa**; el saldo es entonces cota superior y se documenta). Registros V3: sin cambio (sus estados nuevos son UNKNOWN).
  - Reporte `current.eggs_available_hatchery` (V4): `received − set − total` si el total es KNOWN, si no `null`; V3: fórmula previa.
- **D-5 `fertile_eggs_to_pit`**: entero ≥ 0, métrica opcional (vacío = UNKNOWN, `0` = cero), **sin N/A**. Única validación: `≤ eggs_received`. **No** se suma al total no incubable, **no** se suma a `eggs_discarded`. `eggs_in_process` V4 = `set − transferred` **solo si** `set` y `transferred` son KNOWN **y** `fertile_eggs_to_pit` es KNOWN y `= 0`; en otro caso `null` (su resta depende de OD-HATCH-V4-01).
  - **SUPERADO por el amendment §7 (OD-HATCH-V4-01 = RATIFIED, 2026-11-21):** la fosa es POST-carga; ver §7. Se conserva el texto original por trazabilidad.
- **D-6 Obligatoriedad/tipos**: los 4 campos son métricas opcionales; enteros ≥ 0; negativos, decimales y texto → error; `N/A` → error (no aplica conceptualmente).
- **D-7 Orden de `Datos`**: `… eggs_received, eggs_set, eggs_non_incubable_oversized, eggs_non_incubable_dirty, eggs_non_incubable_broken, eggs_transferred, fertile_eggs_to_pit, chicks_hatched, chicks_available …` (23 columnas).
- **D-8 Persistencia/migración**: columnas físicas en `hatchery_openings`: `eggs_non_incubable_oversized|dirty|broken`, `fertile_eggs_to_pit` (Integer, nullable) + sus `*_status` (String(15), `NOT NULL`, `server_default 'UNKNOWN'`). Sin backfill ni reparto de históricos. Nueva revisión Alembic tras `g2b3c4d5e6f7`; se avanzan conscientemente los pines de cabeza.
- **D-9 Pipeline**: mismo recorrido (parse → normalize → staging → validation → preview → approval → apply → reconciliation); sin rutas laterales. CSV con la misma cabecera.
- **D-10 UI/reportes**: preview y detalle muestran los 4 campos y el «Total no incubables» (etiquetado como derivado, no editable); V3 histórica muestra `Huevos descartados (histórico)`; nunca se fabrica desglose.
- **D-11 Docs/QA**: manual, `cutover_v2_docs.py` (matrices de linaje/destino y plantillas en `docs/plantillas_carga_inicial/`), seeds QA y `test-support` pasan a v4.

## 3. Invariantes
- **Confirmadas**: `set ≤ received`; `set + Σ(no incubables KNOWN) ≤ received`; cada no incubable `≤ received`; `fertile_to_pit ≤ received`; `transferred ≤ set`; `chicks_hatched ≤ transferred|set`; `chicks_available ≤ chicks_hatched`; sin doble conteo (no incubables restan una sola vez, en el saldo recibido→cargado).
- **No confirmadas**: ~~ubicación de `fertile_eggs_to_pit` en el balance~~ → **RESUELTA** por el amendment §7 (OD-HATCH-V4-01 = RATIFIED).
- **AUTHORIZATION_GATE = PASS**: ninguna decisión bloquea la captura; la ecuación de fosa queda marcada.

## 4. ACs
| AC | Enunciado |
|---|---|
| AC-V4-01 | Contrato hatchery `v4`/`CUTOVER_HATCHERY_V4`; `Datos` con 23 columnas en el orden D-7; sin `eggs_discarded`. |
| AC-V4-02 | Plantilla XLSX generada: Meta v4, `Instrucciones` completas de los 4 campos (significado, obligatorio, tipo, unidad, formato, ejemplo, UNKNOWN, N/A, destino), `Datos`, `Catalogos`; CSV con la misma cabecera. |
| AC-V4-03 | Cabecera V4 con `eggs_discarded` → rechazo (columna ajena); cabecera V4 sin alguno de los 4 → rechazo (faltantes). |
| AC-V4-04 | Carga hatchery `v3` nueva → `TEMPLATE_VERSION_UNSUPPORTED` indicando v4. |
| AC-V4-05 | Por campo: negativo/decimal/texto/`N/A` → DENY; `0` → KNOWN; vacío → UNKNOWN. |
| AC-V4-06 | Total no incubable: 100+80+20 → 200; con un UNKNOWN → UNKNOWN (no 120). |
| AC-V4-07 | `set + Σ(KNOWN) > received` → `CONSISTENCY_MISMATCH`; con igualdad parcial o saldo por cargar no se rechaza (no hay igualdad forzada). |
| AC-V4-08 | `fertile_eggs_to_pit > received` → error; `> 0` válido con persistencia completa (staging→apply→detalle→reporte). |
| AC-V4-09 | Apply persiste cada componente por separado y su estado; `eggs_discarded=NULL/NOT_APPLICABLE` en V4. |
| AC-V4-10 | No double count: `received=10000, set=9000, no_incubables=1000` ⇒ disponible BR-03 = 0 (una sola resta), `eggs_in_process = 9000 − transferred` (no `8000`). |
| AC-V4-11 | V3 histórica: registro con `eggs_discarded=100` sin desglose sigue legible; desglose = UNKNOWN; sin reparto inventado. |
| AC-V4-12 | Migración: head avanzado y pinado; filas existentes con estados nuevos `UNKNOWN`. |
| AC-V4-13 | UI preview/detalle muestran los campos y el total derivado; V3 histórica muestra descartados históricos. |
| AC-V4-14 | E2E hatchery V4 completo (XLSX y CSV) hasta reconciliación, incluidos refresh/relogin. |

## 5. Tareas (delegadas a DeepSeek; Claude audita y ejecuta las suites)
T1 contrato+parser+plantilla+docs script · T2 modelo+migración+apply+detalle/reporte · T3 validación (cutover) + BR-03 · T4 tests backend · T5 seeds QA + pines Alembic · T6 frontend (preview/detalle/locales) + tests · T7 `test-support` + E2E hatchery · T8 docs/manual/plantillas v4.

## 6. Estado
Ver `audit/ga-cutover-hatchery-v4/CERTIFICATION.md`. IMPL `2f772eb` + `0d7b0cc`; backend 1947/0/59 · frontend 740 · E2E 213/0 · mutación 20/20. Abierta: OD-HATCH-V4-01 (OWNER_DOMAIN_DECISION_REQUIRED).

## 7. AMENDMENT — OD-HATCH-V4-01 = RATIFIED (decisión Owner, 2026-11-21)

Mandato `GA-HATCHERY-V4-OD-FERTILE-EGGS-TO-PIT`. Continuación mínima: no se reimplementa V4, no se tocan los tres no incubables, no se reabre O-13, no hay migración
(`fertile_eggs_to_pit` ya está persistido; head Alembic sigue `h3c4d5e6f7a8`).

**Decisión Owner:** `fertile_eggs_to_pit` son huevos **ya cargados** en incubación y retirados del proceso durante la incubación/ovoscopia, **antes de continuar a nacedora/nacimiento**.
Es un movimiento **POST-CARGA**; no es clasificación previa, no forma parte de los no incubables y no se suma a `eggs_discarded` (V3).

### Modelo de dos etapas
```
ETAPA A (recepción/clasificación):  eggs_received → { eggs_set | oversized | dirty | broken | aún por cargar }      set + Σ(no incubables KNOWN) ≤ received   (sin igualdad)
ETAPA B (incubación):               eggs_set → { eggs_transferred | fertile_eggs_to_pit | en proceso }              transferred + pit ≤ set
```
- **D-12 `eggs_in_process` V4** = `eggs_set − eggs_transferred − fertile_eggs_to_pit` **solo si los tres son KNOWN**; si cualquiera es UNKNOWN (o N/A en `eggs_transferred`) = UNKNOWN (nunca 1000 con pit UNKNOWN). Reemplaza la regla D-5 («solo con fosa = 0»).
  Pit = 0 conocido es un cero conocido: `set − transferred`. No usa `eggs_received` ni los no incubables (ya excluidos antes de `eggs_set`).
- **D-13 validación (cutover)**: `fertile_eggs_to_pit ≤ eggs_set` cuando `eggs_set` es KNOWN; y `eggs_transferred + fertile_eggs_to_pit ≤ eggs_set` cuando los tres son KNOWN (sin doble error si una cota ya falló).
  Si `eggs_set` es UNKNOWN solo queda la cota derivada `pit ≤ eggs_received` (pit ⊆ set ⊆ received), que no contradice la decisión. Se conserva `transferred ≤ set` y `chicks_hatched ≤ transferred (o set)`.
- **D-14 BR-03 no cambia**: el saldo disponible para cargar es `received − set − Σ(no incubables KNOWN)`; la fosa ocurre **después** de la carga y NO se resta.
- **D-15 V3 no cambia**: `eggs_in_process = set − transferred − eggs_discarded`; no se reinterpreta con la fosa. En V4 `eggs_discarded = NOT_APPLICABLE` y no se deriva.
- **D-16 transferencias operativas**: el operativo normal no tiene validador de `transfer_to_hatcher` ni evento de fosa → sin cambios (sigue como `OPERATIONAL_MODEL_GAP`; spec separada).
- **D-17 semántica de la plantilla**: el significado de `fertile_eggs_to_pit` en `Instrucciones`/contrato pasa a «huevos ya cargados retirados a fosa durante la incubación/ovoscopia, antes de nacedora; acumulado al corte».

### ACs del amendment
| AC | Enunciado |
|---|---|
| AC-V4-15 | `fertile_eggs_to_pit > eggs_set` (set KNOWN) → `CONSISTENCY_MISMATCH` (H4-FOSA-04: set 9000, pit 9001). |
| AC-V4-16 | `eggs_transferred + fertile_eggs_to_pit > eggs_set` → `CONSISTENCY_MISMATCH` (H4-FOSA-03: 8000 + 1001 > 9000); `= set` válido (H4-FOSA-02: 8000 + 1000 → en proceso 0). |
| AC-V4-17 | `eggs_in_process = set − transferred − pit` cuando los tres KNOWN (H4-FOSA-01: 900); UNKNOWN si falta alguno (H4-FOSA-05); pit = 0 conocido → `set − transferred` (H4-FOSA-06). |
| AC-V4-18 | Sin doble conteo (H4-FOSA-07): received 10000, no incubables 1000, set 9000, pit 100, transferred 8000 ⇒ disponible para cargar = 0, en proceso = 900 (ni −100 ni 800); BR-03 no resta la fosa. |
| AC-V4-19 | V3 histórica sin cambios (fórmula con `eggs_discarded`); V4 `eggs_discarded` NULL/`NOT_APPLICABLE`. |
| AC-V4-20 | Preview y reconciliación muestran «Huevos fértiles a fosa» como métrica separada y «Huevos en proceso» con la fórmula nueva; nunca como no incubable ni como descartado V3. |

### Pruebas obligatorias (mandato §13)
H4-FOSA-01 (9000/8000/100 → 900) · 02 (9000/8000/1000 → 0) · 03 (9000/8000/1001 → DENY) · 04 (9000, pit 9001 → DENY) · 05 (pit UNKNOWN → en proceso UNKNOWN) · 06 (pit 0 conocido) · 07 (no incubables + fosa sin doble conteo).

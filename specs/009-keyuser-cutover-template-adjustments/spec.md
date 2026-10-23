# SPEC 009 — KeyUser Cutover Template Adjustments · Session 01

**Fuente funcional:** «SESION 1 - REVISION PLANTILLAS - CON KEYUSER - 22-10-2026.pdf» (no presente en la estación: `PENDIENTE_DE_CONTRASTE`). Las decisiones definitivas provienen del mandato Owner del 2026-10-22. Precedencia: **SPEC > OWNER DECISION del mandato > implementación actual**.

**Baseline certificado:** SPEC 006 (cutover v2). Esta SPEC **no** reinterpreta la intención histórica de SPEC 006; la extiende.

**Roles (mandato):** Claude orquesta y decide técnicamente; DeepSeek escribe el código y las pruebas; Claude audita, aplica, verifica y certifica.

**SAP:** READ ONLY inbound. `REAL_SAP_CALLS=0`, `REAL_SAP_WRITES=0`. Ninguna prueba escribe SAP ni fabrica respuestas SAP reales.

**Metodología:** NO SPEC = NO DEVELOPMENT · NO AC = NO IMPLEMENTATION · NO TEST = NO COMPLETE · NO E2E = NO PROCESS CERTIFIED · NO EVIDENCE = NO CERTIFICATION.

---

## 1. Alcance

Ajustes a `cutover_template_breeder` y `cutover_template_hatchery` solicitados por los KeyUser del área avícola:

- **A** · `genetic_line_code` / `breed_name` como **maestro interno de Global Avícola** (no SAP), con errores funcionales específicos.
- **B** · mortalidad histórica **obligatoria** en Reproductoras (`breeder`), sin propagar a Progenitoras (`grandparent`).
- **C** · clasificación de **procedencia SAP vs Global Avícola** en la hoja `Catalogos`.
- **D** · separación entre **`generation`** (generación biológica) y **`egg_origin`** (origen comercial del huevo), con nuevo campo `egg_origin`.

Impacto: contrato, parser, validación, apply, generación de plantilla, modelo, migración Alembic, documentación de usuario, matrices de linaje/destino, dataset QA y E2E por BU.

---

## 2. Decisión A — línea genética y raza (maestro interno GA)

`genetic_line_code` y `breed_name` tienen `SOURCE_OF_TRUTH = GLOBAL_AVICOLA_INTERNAL_MASTER`, **nunca** `SAP_MASTER`. Se conservan los maestros `GeneticLine`/`Breed`, las FK `lots.genetic_line_id`/`lots.breed_id` y la resolución contra los maestros **activos de la empresa efectiva** (o globales `company_id IS NULL`). **No** se autocrea el maestro durante el cutover; **no** se degrada el campo a texto libre; **no** se eliminan modelos ni FK.

Errores funcionales específicos (reemplazan a `MASTER_NOT_FOUND`/`PARENT_MISMATCH` **solo** para estos dos campos; el resto de maestros conserva sus códigos):

- `GENETIC_LINE_NOT_FOUND` — la línea genética no existe, está fuera de la empresa o está inactiva.
- `BREED_NOT_FOUND` — la raza no existe (en la empresa / línea según corresponda).
- `BREED_NOT_IN_GENETIC_LINE` — la raza existe pero no pertenece a la línea genética indicada.

La incompatibilidad de `bird_type` de la raza con la unidad sigue siendo `PARENT_MISMATCH` (no es el caso «no pertenece a la línea»).

---

## 3. Decisión B — mortalidad obligatoria en Reproductoras (breeder)

En `breeder`, `historical_mortality_males` y `historical_mortality_females` pasan a `required=True` (⇒ `allow_unknown=False`). Semántica de métrica preservada: **`0` es KNOWN** (cero real, válido); **vacío ⇒ `REQUIRED_FIELD_MISSING`**; **`N/A` ⇒ `NOT_APPLICABLE_ON_REQUIRED`**.

En `grandparent` esos dos campos **siguen opcionales** (`metric=True`, `UNKNOWN` permitido). Se refactoriza `_METRICAS_REPRODUCTORAS` a una función parametrizada por BU (`_metricas_reproductoras(bu)`) de modo que la obligatoriedad solo aplique a `breeder`. Prueba cross-BU de regresión **obligatoria** (R5).

---

## 4. Decisión C — Catalogos: procedencia SAP vs interna

La hoja `Catalogos` añade una **6.ª columna `source`** ∈ {`SAP`, `GLOBAL_AVICOLA`}. El parser **no** lee `Catalogos` (solo `Meta`/`Datos`), por lo que la columna no rompe el contrato de carga.

Clasificación **por categoría**, basada en el mapping canónico `sap_entity_mappings` (SPEC 005), **no** en suposición:

- `SAP` (gobernado por SAP): **`farm`** (← SAP PLANT, `sap_entity_mappings.farm_id`) y **`house`** (← SAP STORAGE_LOCATION, `sap_entity_mappings.house_id`).
- `GLOBAL_AVICOLA`: `genetic_line`, `breed`, `productive_phase`, `area`, `hatchery`, `incubator`, `hatcher`, `source_lot`, `lot` (sin mapping SAP canónico hoy).

`source` declara la **gobernanza** del maestro, **no** que la fila provenga de una llamada SAP viva. `Catalogos` sigue mostrando solo maestros **locales activos de la empresa efectiva**; **nunca se fabrican filas** («maestro SAP no promovido no se inventa»). El código queda preparado para consumir maestros SAP **promovidos** por el inbound autorizado (inbound → staging → mapping → promoción → mirror local → Catalogos); **sin** llamadas SAP en el GET de la plantilla.

---

## 5. Decisión D — incubadora: generación vs origen del huevo

`generation` se **mantiene** ∈ {`grandparent`, `breeder`} (generación biológica → `lots.hatchery_purpose`, `hatchery_openings.generation`). **No** se añade `purchased` a `generation`.

Nuevo campo de contrato **`egg_origin`** (enum) ∈ {`internal`, `purchased`} (ES: «Propio/Interno» / «Comprado»; el **valor persistido es canónico** y el display se resuelve por i18n: no se mezclan). Persistencia nueva **`hatchery_openings.egg_origin`** (`String(20)`, nullable a nivel BD por filas previas; obligatorio en el contrato v3), con **migración Alembic** sobre la cabeza real `e0f1a2b3c4d5`.

Reglas:

- `egg_origin = internal`: `source_lot_code`, si se indica, resuelve contra un lote interno compatible (comportamiento actual, R18).
- `egg_origin = purchased`: **no** exige `source_lot_code` interno; la referencia externa se conserva vía `source_system`/`source_reference` (y `source_lot_reference` si se indica). **No** se inventa una OC ni se exige una nueva (R17).
- `egg_origin` es **obligatorio** en el contrato de incubadora v3.

---

## 6. Decisión de versionado de plantilla (§16 del mandato)

`egg_origin` es una **columna nueva con semántica nueva** ⇒ se **versiona** la plantilla de incubadora a **`v3`** (`schema_id = CUTOVER_HATCHERY_V3`), para **no reinterpretar en silencio** archivos v2 ya descargados. `grandparent`, `breeder` y `broiler` permanecen en **`v2`**: en `breeder` la mortalidad obligatoria es un **endurecimiento de validación con cabecera idéntica**, no un cambio estructural de columnas.

El parser exige que la versión y el `schema_id` del archivo coincidan con la versión **vigente** del contrato de la BU. Un archivo de una versión **anterior de la misma BU** (p. ej. hatchery v2) ⇒ `TEMPLATE_VERSION_UNSUPPORTED` con mensaje accionable: «descargue la plantilla `<versión>` de `<BU>`». `SUPPORTED_TEMPLATE_VERSIONS` pasa a incluir `v2` y `v3`; `v1` sigue retirada. Estrategia explícita de compatibilidad: ningún archivo se reinterpreta; el usuario recibe un error claro que le indica descargar la versión vigente.

---

## 7. Criterios de aceptación (AC) — RED antes de implementar

- **R1** · `breeder` rechaza `historical_mortality_males` vacío (`REQUIRED_FIELD_MISSING`).
- **R2** · `breeder` rechaza `historical_mortality_females` vacío.
- **R3** · `breeder` acepta `historical_mortality_males = 0` (KNOWN).
- **R4** · `breeder` acepta `historical_mortality_females = 0`.
- **R5** · `grandparent` conserva el comportamiento: mortalidad vacía ⇒ `UNKNOWN`, sin error (regresión cross-BU).
- **R6** · línea genética interna válida resuelve sin dependencia SAP.
- **R7** · raza interna válida resuelve.
- **R8** · raza que no pertenece a la línea indicada ⇒ `BREED_NOT_IN_GENETIC_LINE`.
- **R9** · maestro SAP no promovido **no** se inventa en `Catalogos` (no se fabrican filas).
- **R10** · `Catalogos` no expone registros de otra empresa.
- **R11** · `Catalogos` no expone inactivos.
- **R12** · hatchery `generation = grandparent` pasa.
- **R13** · hatchery `generation = breeder` pasa.
- **R14** · hatchery `generation = purchased` ⇒ `INVALID_ENUM`.
- **R15** · `egg_origin = internal` pasa.
- **R16** · `egg_origin = purchased` pasa.
- **R17** · `purchased` **no** exige lote interno (source_lot ausente o no interno no produce error).
- **R18** · `internal` mantiene la validación de `source_lot` existente/compatible.
- **R19** · el apply persiste `egg_origin` correctamente en `hatchery_openings`.
- **R20** · lineage: `UNMAPPED_TEMPLATE_FIELDS = 0`.
- **R21** · lineage: `REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE = 0`.

Extra (derivados de las decisiones A/C/versionado):

- `genetic_line_code` inexistente ⇒ `GENETIC_LINE_NOT_FOUND`; `breed_name` inexistente ⇒ `BREED_NOT_FOUND`.
- archivo hatchery **v2** cargado contra el contrato v3 ⇒ `TEMPLATE_VERSION_UNSUPPORTED` con mensaje accionable.
- `Catalogos` trae la columna `source` con `farm`/`house` = `SAP` y `genetic_line`/`breed` = `GLOBAL_AVICOLA`.

---

## 8. Archivos afectados

- **Backend (código, DeepSeek):** `backend/app/cutover/contracts.py`, `parser.py`, `validation.py`, `service.py`, `templates.py`, `models.py`; nueva migración `backend/alembic/versions/*_hatchery_egg_origin.py` (`down_revision = "e0f1a2b3c4d5"`).
- **Tests (DeepSeek):** nuevo `backend/tests/test_cutover_v2_keyuser_s01_red.py` (R1–R21 + extras); actualización de `backend/tests/cutover_v2_fixtures.py` (contrato hatchery v3, `egg_origin`, versión/schema por BU) y de las suites v2 afectadas (códigos `GENETIC_LINE_NOT_FOUND`/`BREED_*`, mortalidad breeder, `template_version` por BU). **Ningún test se elimina ni se marca `skip`**: las actualizaciones son por cambio de contrato, documentadas.
- **Frontend (DeepSeek):** i18n de `egg_origin` («Propio/Interno», «Comprado») y, si existe vista que expone `generation` de incubadora, mostrar `egg_origin`; si no existe, declararlo `NONE` con evidencia.
- **Docs (gobernanza, Claude):** `docs/MANUAL_CARGAS_INICIALES.md`; `audit/cutover-initial-balances/07_DATA_LINEAGE_MATRIX.md`, `10_APPLY_DESTINATION_MATRIX.md`, `04_BREEDER_TEMPLATE_CONTRACT.md`, `05_HATCHERY_TEMPLATE_CONTRACT.md`, `09_VALIDATION_CATALOG.md`.
- **QA (DeepSeek):** fixtures `QA_SYNTHETIC` para breeder con mortalidad obligatoria, hatchery `internal` y hatchery `purchased`; actualización de `QA-DEMO-V1` sin reducir cobertura.

---

## 9. Fuera de alcance

- No se modifica `broiler` ni `grandparent` salvo refactor técnico **sin cambio funcional** (la parametrización de `_metricas_reproductoras` no cambia el comportamiento de grandparent: R5 lo prueba).
- No hay llamadas SAP reales ni escrituras SAP. No se fabrican maestros ni rangos de códigos SAP.
- No se crean ramas (`MAIN_ONLY`), no se tocan workflows, no hay `force push`, no hay PR.
- `generation` no recibe `purchased`.

---

## 10. Testing y evidencia

Ciclo obligatorio: **RED** (R1–R21 fallan sobre el código actual) → **implementación** (DeepSeek) → **targeted GREEN** → **regresión backend completa** (`backend/scripts/run_tests.sh`, ~22 min, en segundo plano) → **frontend** (`npx vitest run`, `npx tsc -b`, `npx vite build`) → **E2E cutover por BU** (`scripts_e2e.sh`: breeder, hatchery internal/purchased) → **mutación/sensibilidad** (tras el commit de implementación) → **restore explícito** desde el SHA de implementación (`git restore --source=<IMPL_SHA> -- <archivo>`) → **regresión post-mutación** → **evidencia saneada** en `audit/keyuser-session-01/` → **certificación local** → **commit de certificación** → **push `origin/main`** → **REMOTE_SHA verify**.

Objetivo de cierre: `KEYUSER_SESSION_01_REQUIREMENTS = IMPLEMENTED`, `UNMAPPED_TEMPLATE_FIELDS = 0`, `REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE = 0`, `REAL_SAP_WRITES = 0`, `REMOTE_SHA_MATCH = PASS`, `FINAL_STATUS = CERTIFIED_KEYUSER_SESSION_01_IMPLEMENTED`.

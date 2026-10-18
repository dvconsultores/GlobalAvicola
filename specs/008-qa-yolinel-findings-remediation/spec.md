# Feature Specification: SPEC 008 — QA Yolinel Findings Remediation

**Directorio**: `specs/008-qa-yolinel-findings-remediation` · **Rama**: `main` (sin rama nueva)
**Created**: 2026-10-18 · **Baseline**: `83c9cd8` · **Status**: `IMPLEMENTING`
**Tipo**: `QA_FINDINGS_REMEDIATION` (corrección de defectos UI P1 + huecos funcionales acotados + clarificación documental; no reabre SPEC 005/006/007)
**Prioridad**: P1 · **Dependencias**: GA-REM-040 (acceso por unidad de negocio), SPEC 005 (inbound HANA read-only → staging → promoción SAP), SPEC 006 (Cargas Iniciales / cutover), SPEC 007 (dataset QA), OD-24 (Empresas/Granjas espejo SAP de solo lectura, P-08), RR-03 (segregación de funciones), BR-18 (límite de OC), BR-19 (fecha de evento no futura)
**Input**: Revisión exploratoria QA — Yolinel Cortez, 2026-10-17, 18 observaciones (`audit/qa-yolinel-2026-10-17/01_SOURCE_FINDINGS.md`)
**Paquete de auditoría asociado**: `audit/qa-yolinel-2026-10-17/01…04`
**Target**: `QA-013=0` · `QA-017=0` · `BR-23_IMPLEMENTED=YES` · `OWNER_DECISIONS_PENDING=5` · `REAL_SAP_CALLS=0`

---

## PURPOSE

Cerrar la ronda de revisión QA del 2026-10-17 con una clasificación formal y verificable de sus 18 hallazgos: corregir los defectos de interfaz de prioridad P1 detectados (columnas de maestros con etiquetas de botón, bucle de peticiones del Centro de Revisión), implementar las mejoras de usabilidad de mayor valor (padre visible en listados hijos, estado/«Desactivar» en maestros, `max=hoy` en fechas de evento, granja/usuario/fecha de registro y filtro por granja), cerrar el hueco funcional P1 de coherencia de cadena en la OC de Recepción de Aves (BR-23, regla mínima), y dejar documentado con trazabilidad contractual todo lo que es comportamiento correcto pero mal explicado, o que requiere decisión del Owner antes de implementarse.

## FUENTE

| Campo | Valor |
|---|---|
| Fuente primaria | `audit/qa-yolinel-2026-10-17/01_SOURCE_FINDINGS.md` (transcripción fiel del mandato del Owner) |
| Fuente original | PDF «REVISION GENERAL DE SISTEMA GLOBAL AVICOLA - 17-10-2026.pdf» — **NO DISPONIBLE** en la estación de trabajo |
| Contraste de capturas | `PENDING_PDF` — cada observación queda marcada `pendiente PDF` |
| Carácter | Revisión **preliminar/exploratoria**; no es certificación |
| Alcance revisado | Administración, ~20 maestros, Auditoría, Cargas Iniciales (paso Unidad y Corte), Operativo general, Revisión (Centro de Revisión y Aprobaciones) |
| Alcance no revisado | SAP, Reportes, resto de Cargas Iniciales (`NOT_REVIEWED_YET`) |

> La ausencia del PDF no bloquea la remediación: la transcripción del mandato es autosuficiente para clasificar y para implementar los defectos de UI y la regla mínima BR-23. Sí bloquea cualquier afirmación de certificación QA.

## ALCANCE / NO ALCANCE

- **Se implementa**: FR-01 … FR-07 (código BE/FE) y FR-08 (documentación).
- **No se implementa**: SAP real, reglas de predecesor sin decisión Owner, unicidad de maestros, zona física de incubadora, limpieza del dataset QA (ver «OUT OF SCOPE»).

## MATRIZ DE HALLAZGOS (QA-001 … QA-018)

Un hallazgo puede llevar **varias etiquetas**; se indican todas.

| ID | Clasificación | Acción | Prioridad |
|---|---|---|---|
| QA-001 | `ALREADY_COMPLIANT` + `DOCUMENTATION_CLARIFICATION` | Documentar que Granjas/Plantas no llevan FK a unidad de negocio por contrato (GA-REM-040: una granja aloja galpones de varias unidades; la cadena se deriva de `lots.bird_type` vía `business_units/scope.py`); Hatchery se clasifica como unidad única `hatchery` en `route_scope.py`. Sin cambio de código. Nota Owner: filtrar el listado de plantas de incubación por BU concedida es decisión opcional | — |
| QA-002 | `ALREADY_COMPLIANT` (BE) + `UX_IMPROVEMENT` (FE) | El DELETE de los 20 maestros es **baja lógica** (`is_active=False`), nunca borrado físico: no hay referencias huérfanas ni 500. Corregir la UI: «Desactivar/Reactivar», columna Estado, fila inactiva atenuada, toast de error ante fallo. Maestros de origen SAP: por OD-24 Empresas/Granjas serán espejo SAP de solo lectura cuando exista P-08; hoy no hay convergencia destructiva → documentar | P2 |
| QA-003 | `ALREADY_COMPLIANT` + `UX_IMPROVEMENT` + `OWNER_DECISION_REQUIRED` | Vacunas/medicamentos/causas se identifican por `name` (obligatorio, no único por empresa; ninguna fuente exige código único). UX: mostrar las columnas descriptivas reales (laboratorio, tipo, vía; principio activo; descripción) con etiquetas correctas. Decisión Owner: ¿nombre único por empresa y/o código? | P2 |
| QA-004 | `OWNER_DECISION_REQUIRED` | Hatchery tiene `location` (texto) y no `area_id`; GA-REM-039 define Área como estructura organizativa, no zona física. No copiar el modelo de Farm | P2 |
| QA-005 | `DOCUMENTATION_CLARIFICATION` | Documentar la cadena SPEC 005: HANA READ ONLY → RAW → VALIDATION → MAPPING → STAGING → PROMOCIÓN CONTROLADA a `sap_references`; 14 objetos; qué se promueve y qué queda staging-only. Sección para QA «Cómo Global Avícola recibe información de SAP». SAP real `PENDING` (2026-10-20) | P2 |
| QA-006 | `DOCUMENTATION_CLARIFICATION` | Documentar `lots.origin`: `NATIVE` (alta manual / importación de abuelas) y `MIGRATED` (Cargas Iniciales / cutover); SAP inbound **nunca** crea lotes (solo referencias). `activation_type` normal/manual | P3 |
| QA-007 | `FUNCTIONAL_GAP` | Hoy `validate_oc_limit` solo valida empresa y cantidad acumulada (BR-18); `/sap/references` no filtra por cadena y el selector carga todas las OC. Ninguna decisión dice que la OC determine la cadena, pero existe dato determinista: `SapEntityMapping(entity_type=PLANT).business_unit_code` para el centro (WERKS) de las posiciones. Implementar BR-23 (regla mínima, ver FR-01) | P1 |
| QA-008 | `OWNER_DECISION_REQUIRED` + `DOCUMENTATION_CLARIFICATION` | Hoy la OC autocompleta referencia, cantidad declarada y proveedor (texto); granja/galpón/lote/transporte/fecha son del usuario. SAP-STO-01 (LGORT↔galpón) y la clasificación de plantas (WERKS↔granja) están `PENDING` (AOD-02, OD-24 P-08): no se autocompleta nada más hasta mapping aprobado. Entregar matriz campo→`AUTO_POPULATED_EDITABLE`/`USER_REQUIRED`/`NOT_APPLICABLE`/`PENDING_MAPPING` | P2 |
| QA-009 | `FUNCTIONAL_GAP` + `OWNER_DECISION_REQUIRED` | El backend no tiene catálogo de predecesores; solo reglas de saldo (BR-01..BR-04, R3/R4) y lote activo/fecha. La secuencia vive solo en `frontend/src/data/processCatalog.ts`. `docs/02` no impone orden temporal. Se entrega `PROCESS_PREDECESSOR_MATRIX` **propuesta** y se pide decisión Owner para la regla mínima propuesta; **no se implementa en esta ronda** | P1 (decisión) |
| QA-010 | `DOCUMENTATION_CLARIFICATION` | Documentar la máquina de estados real de operaciones en `OPERATION_STATE_MACHINE.md` (ver FR-08) | P2 |
| QA-011 | `ALREADY_COMPLIANT` + `DOCUMENTATION_CLARIFICATION` | BR-14/RR-03: `ApprovalStep.require_segregation` (default `True`) por empresa; bloquea registrador, corrector y quien rechazó (R-143, 403); el supervisor que revisó sí aprueba; tests `test_segregation_r143` g01-g06 y E2E `proceso-03`. Nota Owner: con la bandera en `False` se desactivan también las exclusiones de corrector/rechazador (inferencia; confirmar) | P3 |
| QA-012 | `UX_IMPROVEMENT` | Listados de galpones, incubadoras y nacedoras no muestran el padre; añadir columna **Granja** / **Planta** por nombre | P2 |
| QA-013 | `DEFECT` | 20 de 42 columnas de maestros reutilizan claves i18n de botones (`common.edit` «Editar», `common.save` «Guardar») para campos reales (`tax_id`, `country`, `code`, `location`, `capacity`, `plate`, `laboratory`, `category`, `order`, `description`, `sap_code`). Corregir con claves propias | P1 |
| QA-014 | `UX_IMPROVEMENT` | Lotes, Historial, Mis pendientes, Centro de Revisión y Aprobaciones no muestran Granja/Planta; las APIs devuelven solo ids. Añadir `farm_name` (y `hatchery` cuando aplique) al contrato de lectura y columna condicional | P2 |
| QA-015 | `UX_IMPROVEMENT` (farm) + `FUNCTIONAL_GAP` (hatchery) | `/operations` ya acepta `farm_id`/`date_from`/`date_to`/`status` y `/lots` `farm_id`/`status`, pero la UI no los expone; no existe `hatchery_id` en ningún endpoint. Exponer filtro **Granja**; documentar **Planta** como pendiente | P2 |
| QA-016 | `ALREADY_COMPLIANT` (BE `event_date`: BR-19 + R-30/AC13 rechaza futuro) + `UX_IMPROVEMENT` (FE `max=hoy`) + `OWNER_DECISION_REQUIRED` (`start_date`/`activation_date`/`cutover_datetime`, RR-09) | `max=hoy` en el calendario de `event_date`; entregar inventario `FIELD/ROUTE/ALLOW_FUTURE`. Fechas planificadas/cutover: decisión Owner | P2 |
| QA-017 | `DEFECT` | `ReviewCenter.tsx`: `fetchEvents` depende de `can` (función recreada por `useCan` en cada render) y del objeto `toast`; el `useEffect` se re-ejecuta tras cada `setState` ⇒ **REQUEST_LOOP** real. `ApprovalPanel` no cicla. Corregir con dependencias estables + test que cuente peticiones | P1 |
| QA-018 | `UX_IMPROVEMENT` | Mostrar «Registrado por» y «Fecha de registro (`created_at`)» distinguida de la fecha del evento (se implementa junto con QA-014) | P2 |

### Conteos

| Clasificación | Total | Hallazgos |
|---|---|---|
| `ALREADY_COMPLIANT` | 5 | QA-001, QA-002, QA-003, QA-011, QA-016 (parcial) |
| `DEFECT` | 2 | QA-013, QA-017 |
| `FUNCTIONAL_GAP` | 3 | QA-007, QA-009, QA-015 (hatchery) |
| `UX_IMPROVEMENT` | 7 | QA-002, QA-003, QA-012, QA-014, QA-015, QA-016, QA-018 |
| `DOCUMENTATION_CLARIFICATION` | 6 | QA-001, QA-005, QA-006, QA-008, QA-010, QA-011 |
| `QA_MISUNDERSTANDING` | 0 | — |
| `OWNER_DECISION_REQUIRED` | 5 | QA-003 (unicidad), QA-004, QA-008, QA-009, QA-016 (fechas ≠ `event_date`) |

> Los totales por etiqueta no son excluyentes ni suman 18: un hallazgo puede llevar varias etiquetas (indicado en la matriz).

---

## REQUISITOS FUNCIONALES

### FR-01 · BR-23 — Cadena de la orden de compra (regla mínima) · QA-007 · P1

Regla determinista, sin necesidad de decisión del Owner, derivada del mapping ya existente.

```text
ENTRADA   = OC SAP (posiciones con WERKS = centro/planta)
DERIVACIÓN= SapEntityMapping(entity_type=PLANT, entity_code=WERKS).business_unit_code  (una por posición)
CADENA_OC = única si TODAS las posiciones mapeadas coinciden · DESCONOCIDA si ninguna posición tiene mapping
CONFLICTO = dos o más posiciones mapeadas con business_unit_code distintos
REGLA     = CADENA_OC conocida y ≠ lots.bird_type                  ⇒ 400 (BR-23)
            CADENA_OC DESCONOCIDA (sin mapping)                    ⇒ permitir; UI la muestra «sin cadena»
            CONFLICTO (centros de unidades distintas)              ⇒ 400 (mismo código BR-23, motivo distinto)
ALCANCE   = se conserva BR-18 (empresa + cantidad acumulada) sin cambios
UI        = el selector de OC filtra por la cadena del lote: OC compatibles + OC de cadena desconocida
```

- **AC-01.1** Dado un lote de cadena `BROILER` y una OC cuyas posiciones mapean todas a `BROILER`, la recepción se acepta (`POST` responde 2xx).
- **AC-01.2** Dado un lote de cadena `BROILER` y una OC con todas sus posiciones mapeadas a `LAYER`, el `POST` responde **400** con código/mensaje BR-23 y el lote y la OC quedan intactos.
- **AC-01.3** Dada una OC **sin ninguna** posición mapeada (cadena desconocida), el `POST` se acepta y la respuesta/UI indica «sin cadena» (no se inventa cadena).
- **AC-01.4** Dada una OC con posiciones mapeadas a dos unidades distintas, el `POST` responde **400** BR-23 (no se elige arbitrariamente una).
- **AC-01.5** El endpoint de referencias (`/sap/references`) acepta un filtro de cadena y el selector frontend solo ofrece OC compatibles con `lots.bird_type` más las de cadena desconocida.
- **AC-01.6** BR-18 se sigue aplicando: una OC de la misma empresa que excede la cantidad acumulada sigue respondiendo 400 con su código actual.
- **AC-01.7** Existe test backend que cubre AC-01.1…AC-01.4 y test frontend para AC-01.5; suite completa en verde.

### FR-02 · Etiquetas propias en columnas de maestros · QA-013 · P1

- **AC-02.1** Ninguna definición de columna de los 20 maestros usa claves de acción (`common.edit`, `common.save`, `common.delete`, `common.*`) para nombrar un campo de datos.
- **AC-02.2** Cada campo listado en QA-013 (`tax_id`, `country`, `code`, `location`, `capacity`, `plate`, `laboratory`, `category`, `order`, `description`, `sap_code`) tiene clave i18n propia y su valor se muestra en la columna correcta (contraste campo↔valor en el test de la tabla).
- **AC-02.3** Existe test que detecta reutilización de claves de acción en `columns` (falla si se reintroduce).
- **AC-02.4** Las etiquetas se muestran en ES (y EN si el catálogo ya está traducido), sin claves sin traducir visibles.

### FR-03 · Padre visible en Galpones / Incubadoras / Nacedoras · QA-012 · P2

- **AC-03.1** El listado de galpones muestra columna **Granja** con el nombre de la granja (no el id).
- **AC-03.2** El listado de incubadoras (equipo) muestra columna **Planta** con el nombre de la planta de incubación.
- **AC-03.3** El listado de nacedoras muestra columna **Planta** con el nombre de la planta de incubación.
- **AC-03.4** Los contratos de lectura correspondientes devuelven el nombre (o el FE lo resuelve con los catálogos ya cargados), sin N+1 por fila.
- **AC-03.5** Filas sin padre (dato legado) muestran un marcador neutro (`—`), no la cadena «undefined».

### FR-04 · Estado y «Desactivar» en maestros · QA-002 · P2

- **AC-04.1** La acción de fila se rotula **«Desactivar»** cuando el registro está activo y **«Reactivar»** cuando está inactivo; no se usa «Eliminar».
- **AC-04.2** Ningún texto de la UI afirma que la acción «no se puede deshacer» para estos maestros.
- **AC-04.3** El listado muestra una columna **Estado** (`Activo`/`Inactivo`) y la fila inactiva se muestra atenuada.
- **AC-04.4** Un fallo del endpoint de baja lógica produce un toast de error visible (no fallo silencioso), con el mensaje del backend.
- **AC-04.5** El backend no cambia: sigue siendo `is_active=False` (no hay borrado físico); verificado en test/inspección (`masters/router.py`, `masters/service.py`).

### FR-05 · Fin del bucle de peticiones del Centro de Revisión · QA-017 · P1

- **AC-05.1** El efecto que carga eventos en `ReviewCenter.tsx` tiene dependencias estables (identidad de `can` estabilizada —p. ej. `useCallback`/`useMemo` en `useCan`, o dependencia de los permisos primitivos— y `toast` como referencia estable).
- **AC-05.2** Cada `setState` posterior (cambio de filtro, apertura de panel, toast) **no** re-dispara la carga de eventos.
- **AC-05.3** Existe un test frontend que monta el componente, ejecuta interacciones que cambian estado y **cuenta las peticiones**: el número es el esperado y no crece a lo largo del tiempo.
- **AC-05.4** `ApprovalPanel` se mantiene sin bucles (test de regresión de conteo de peticiones).

### FR-06 · `max=hoy` en fechas de evento · QA-016 · P2

- **AC-06.1** Los `input type="date"` de **fecha de evento** operativa llevan `max` = fecha de hoy (zona de la empresa/usuario), de modo que el calendario no ofrezca días futuros.
- **AC-06.2** La validación backend existente (BR-19 / R-30 / AC13 → rechazo de futuro) **no** se relaja: el test de rechazo sigue en verde.
- **AC-06.3** Se entrega el inventario `FIELD / ROUTE / ALLOW_FUTURE` de todos los campos de fecha (incluye `start_date`, `activation_date`, `cutover_datetime` como `OWNER_DECISION_REQUIRED`).
- **AC-06.4** No se aplica `max=hoy` a fechas planificadas/cutover mientras no exista decisión Owner.

### FR-07 · Granja/Planta, usuario y fecha de registro en listados + filtro Granja · QA-014, QA-015, QA-018 · P2

- **AC-07.1** Los contratos de lectura de Lotes, Historial (operaciones), Mis pendientes, Centro de Revisión y Aprobaciones incluyen el nombre del padre (`farm_name`; `hatchery_name`/planta cuando aplique) además del id.
- **AC-07.2** Cada uno de esos listados muestra la columna **Granja** (o **Planta**) de forma condicional: aparece cuando el conjunto visible tiene padre y se omite cuando no aporta.
- **AC-07.3** Los listados muestran **«Registrado por»** (usuario) y **«Fecha de registro»** (`created_at`) claramente distinguida de la **fecha del evento**.
- **AC-07.4** La UI de Operaciones expone el filtro **Granja** (usando `farm_id` ya soportado por `/operations`), y la UI de Lotes expone `farm_id`/`status` ya soportados por `/lots`.
- **AC-07.5** El filtro **Planta** queda documentado como pendiente (`hatchery_id` no existe en ningún endpoint); no se añaden parámetros inventados.
- **AC-07.6** No hay degradación de rendimiento: sin N+1 (join/carga por lote de catálogos) y sin cambio de semántica de los filtros existentes.

### FR-08 · Documentación (comportamiento correcto y decisiones) · QA-001, 005, 006, 008, 009, 010, 011 · P2

- **AC-08.1** Existe `OPERATION_STATE_MACHINE.md` con la máquina de estados real: `draft→registered` (alta); `registered/returned/rejected→pending_review` (submit); `pending_review→in_review` (start); `in_review→returned` (return); `in_review→corrected` (complete con 2+ niveles) o `→approved` (1 nivel); `corrected→approved|rejected` (approve/reject, BR-14); `approved→consolidated`; `cancel` desde todo salvo `approved/consolidated/sent_to_sap/sap_confirmed/reversed/cancelled`; `reverse` solo sobre `approved` con contrapartida aprobada ⇒ ambos `reversed`; corregible desde `registered/pending_review/in_review/returned/rejected`.
- **AC-08.2** Se documenta «Cómo Global Avícola recibe información de SAP» (HANA READ ONLY → RAW → VALIDATION → MAPPING → STAGING → PROMOCIÓN CONTROLADA a `sap_references`; 14 objetos; qué se promueve y qué queda staging-only; SAP real `PENDING 2026-10-20`).
- **AC-08.3** Se documenta `lots.origin` (`NATIVE`/`MIGRATED`), `activation_type`, y que SAP inbound nunca crea lotes.
- **AC-08.4** Se documenta la segregación de funciones (BR-14/RR-03) incluidas las exclusiones y la nota sobre `require_segregation=False`.
- **AC-08.5** Se entrega la `PROCESS_PREDECESSOR_MATRIX` **propuesta** (por evento: precondición hoy / precondición propuesta) y la pregunta de decisión Owner; no se implementa.
- **AC-08.6** Se entrega la matriz de autocompletado de Recepción de Aves (QA-008) con los cuatro estados por campo.
- **AC-08.7** Se documenta por qué Granjas/Plantas no llevan FK a unidad de negocio y cómo se deriva la cadena (QA-001), y la clasificación de Hatchery como unidad única `hatchery`.
- **AC-08.8** Toda afirmación de la documentación cita contrato o código (archivo:línea) según `03_REQUIREMENT_TRACEABILITY.md` y `04_CODE_VALIDATION.md`.

---

## OWNER DECISIONS REQUIRED

| ID | Hallazgo | Pregunta | Opciones |
|---|---|---|---|
| **OD-QA2-01** | QA-003 | ¿Vacunas, medicamentos y causas deben tener identificador único? | (a) `name` único por empresa (constraint + validación + UX de duplicado); (b) añadir `code` único por empresa (migración + seeds + UI); (c) ambos; (d) sin unicidad (estado actual, se documenta) |
| **OD-QA2-02** | QA-004 | ¿La planta de incubación debe manejar «zona/área física» como las granjas? | (a) no, `location` texto es suficiente (recomendado por GA-REM-039); (b) añadir `area_id` pero con semántica de área **organizativa** (GA-REM-039), no zona física; (c) replicar el modelo de Farm (implica redefinir granja) |
| **OD-QA2-03** | QA-008 | ¿Se habilita autocompletado adicional de Recepción de Aves desde SAP? | (a) mantener solo referencia+cantidad+proveedor hasta que SAP-STO-01 (LGORT↔galpón) y WERKS↔granja estén aprobados (AOD-02 / OD-24 P-08); (b) adelantar el mapping con datos no certificados (no recomendado); (c) autocompletar granja/galpón solo cuando el mapping exista y sea único |
| **OD-QA2-04** | QA-009 | ¿Se implementa la regla mínima de predecesores propuesta y/o la política de «predecesor desconocido»? | (a) implementar exactamente la regla mínima propuesta (población > 0; carga previa para ovoscopia/transferencia; transferencia para nacimiento; nacimiento para despacho; fase de producción para recolección); (b) regla mínima + bloqueo estricto cuando el predecesor es desconocido; (c) no implementar y mantener validación solo en UI; además: ¿el bloqueo es duro (400) o advertencia? |
| **OD-QA2-05** | QA-016 | ¿`start_date`, `activation_date` y `cutover_datetime` deben rechazar fechas futuras? | (a) permitir futuro (planificación/cutover programado; RR-09 no exige validar); (b) rechazar futuro como `event_date` (BR-19); (c) permitir futuro con límite configurable (p. ej. +N días) y advertencia |

> Ninguna de estas cinco decisiones se implementa en SPEC 008 sin respuesta explícita del Owner.

---

## OUT OF SCOPE

| Tema | Motivo |
|---|---|
| Conexión / prueba SAP **real** | Agendada 2026-10-20; prohibido cualquier acceso real (OD-24, mandato) |
| Reglas de **predecesor** en backend | Requiere OD-QA2-04; esta ronda solo entrega la matriz propuesta |
| **Unicidad** de vacunas/medicamentos/causas | Requiere OD-QA2-01 |
| **Zona física** de incubadora (`area_id`) | Requiere OD-QA2-02 y GA-REM-039 |
| **Limpieza** del dataset QA (SPEC 007) | Fuera de la ronda de remediación; se gestiona con `--cleanup` acotado de SPEC 007 |
| Filtro por planta de incubación (`hatchery_id`) | No existe en ningún endpoint; `FUNCTIONAL_GAP` documentado (QA-015) |
| Revisión de módulos SAP, Reportes y resto de Cargas Iniciales | `NOT_REVIEWED_YET` en la fuente |
| Certificación QA de la revisión Yolinel | Requiere contraste con el PDF `PENDING` |

## RIESGOS

| Riesgo | Mitigación |
|---|---|
| BR-23 endurece un flujo hoy permisivo (recepción de aves) y bloquea operación si el mapping PLANT está incompleto | Cadena desconocida ⇒ permitir (fail-open explícito, visible en UI); solo bloquea la contradicción demostrable |
| Cambiar dependencias de `useEffect` puede ocultar un bug de fondo en `useCan` | Test de conteo de peticiones + revisión de `useCan` como fuente de identidad estable |
| Añadir nombres de padre en 5 listados puede introducir N+1 | Join/carga en lote; verificación de queries en test del endpoint |
| Documentar estados/SAP con detalle incorrecto | Trazabilidad archivo:línea obligatoria (`03`, `04`) y revisión contra `docs/02` y SPEC 005 |
| Reutilización de claves i18n reintroducida | Test guardián de columnas (AC-02.3) |

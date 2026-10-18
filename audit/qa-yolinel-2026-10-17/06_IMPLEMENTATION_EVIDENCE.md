# 06 · Evidencia de implementación — Revisión QA 2026-10-17

**Documento**: qué se tocó para cada hallazgo, archivo por archivo, y qué prueba lo cubre
**Fecha**: 2026-10-18 · **Baseline de referencia**: `83c9cd8` · **SHA de implementación**: `dbd6122` (IMPL) · `9390afc` (IMPL-2)
**Spec asociada**: `specs/008-qa-yolinel-findings-remediation/spec.md` · **Rama**: `main` (sin rama nueva)
**Carácter**: evidencia de cambio en código; no sustituye la verificación en runtime (ver `08_RUNTIME_VERIFICATION.md`) ni la certificación QA

Fuente del estado por hallazgo: `02_FINDINGS_CLASSIFICATION.md` (clasificación) y `05_FIX_PLAN.md` (plan y estado).
Los resultados de las suites asociadas se registran en `07_TEST_EVIDENCE.md`.

---

## 1. Tabla hallazgo → archivos → prueba

| ID | Cambio implementado | Archivos tocados | Prueba que lo cubre |
|---|---|---|---|
| **QA-007** | Regla **BR-23**: la cadena de una OC se deriva del `business_unit_code` del mapping `PLANT` de **todos** sus centros; si es conocida y difiere del `bird_type` del lote ⇒ `400 BR-23`; si es desconocida ⇒ la regla no aplica («sin cadena»); desglose mixto ⇒ no derivable. Selector de OC del frontend filtrado por la cadena del lote, con rótulo de cadena y bloqueo hasta elegir lote | BE: `backend/app/operations/validators.py` (`derive_oc_business_unit`, `derive_oc_business_units`, `validate_oc_business_unit`), `backend/app/operations/service.py` (llamada en la recepción de aves, sin tocar BR-18), `backend/app/integrations/sap/service.py`, `backend/app/integrations/sap/router.py`, `backend/app/integrations/sap/schemas.py`. FE: `frontend/src/pages/operations/OperationFormPage.tsx` | `backend/tests/test_br23_sap_reference_business_unit.py` (5) · `frontend/src/pages/operations/__tests__/qaYolinel.sapOrderByUnit.test.tsx` (3) |
| **QA-013** | Claves i18n propias por campo (`masters.fields.*`) en los 20 maestros; ninguna cabecera de dato reutiliza una clave de acción (`common.edit`/`common.save`) | FE: `frontend/src/App.tsx` (definiciones de columna de las 20 entidades), `frontend/public/locales/es/translation.json`, `frontend/public/locales/en/translation.json` | `frontend/src/__tests__/qaYolinel.red.test.tsx` (guardián de rótulos) · `frontend/src/pages/masters/__tests__/qaYolinel.mastersList.test.tsx` |
| **QA-012** | Columna con el **nombre del padre** en los listados hijos: **Granja** en galpones, **Planta de incubación** en equipos de incubadora y nacedoras (mapa id→nombre sobre el catálogo completo, incluidos padres inactivos) | FE: `frontend/src/pages/masters/MasterListPage.tsx` (`PADRE_DE[*].colLabelKey`, `padreNombres`), claves `masters.fields.farm` / `masters.fields.hatchery` | `frontend/src/pages/masters/__tests__/qaYolinel.mastersList.test.tsx` (3) |
| **QA-002** | Acción **Desactivar/Reactivar** en lugar de «Eliminar», columna **Estado**, fila atenuada para inactivos, toast cuando la baja lógica falla, y `useToast` opcional para no romper pantallas montadas sin provider | FE: `frontend/src/pages/masters/MasterListPage.tsx`, `frontend/src/components/data-table/DataTable.tsx` (`rowClassName`, `RowAction.visible`), claves `common.deactivate|reactivate|confirmDeactivate|deactivateWarning`, `masters.fields.status` | `frontend/src/pages/masters/__tests__/qaYolinel.mastersList.test.tsx` (3) · ajuste de rótulo en `frontend/src/pages/masters/__tests__/gaFe04.mastersGates.test.tsx` |
| **QA-017** | `useCan` devuelve una función con **identidad estable** (`useCallback` sobre el usuario de la sesión); el Centro de Revisión toma `t`/`toast` por referencia y depende de un **booleano** de permiso, no de la función; `ApprovalPanel` alineado | FE: `frontend/src/auth/actionAuthority.tsx`, `frontend/src/pages/review/ReviewCenter.tsx`, `frontend/src/pages/approvals/ApprovalPanel.tsx` | `frontend/src/__tests__/qaYolinel.red.test.tsx` (conteo de `GET /review/pending` estable en 1) |
| **QA-016** | `max=hoy` en la **fecha del evento** y en las fechas de **salida/llegada** de la importación; `hoyISO()` compone la fecha civil local (sin pasar por UTC) | FE: `frontend/src/utils/dates.ts` (`hoyISO`), `frontend/src/pages/operations/OperationFormPage.tsx` | `frontend/src/__tests__/qaYolinel.red.test.tsx` (`max` = hoy en `event_date`) |
| **QA-014** | Contrato de lectura **aditivo** con nombres: `farm_name`/`house_name` en lotes; `lot_code`/`farm_name`/`registered_by_name` en eventos, bandejas de revisión y aprobación; columnas condicionales en las cinco pantallas | BE: `backend/app/operations/enrichment.py` (nuevo), `backend/app/lots/schemas.py`, `backend/app/lots/service.py`, `backend/app/operations/schemas.py`, `backend/app/operations/service.py`, `backend/app/review/service.py`. FE: `LotListPage.tsx`, `OperationListPage.tsx`, `MyPendingPage.tsx`, `ReviewCenter.tsx`, `ApprovalPanel.tsx`, claves `common.farm|lotCode|registeredBy|registeredAt|eventDate` | `backend/tests/test_qa_yolinel_list_enrichment.py` (3) · `frontend/src/__tests__/qaYolinel.listColumns.test.tsx` (3) · `frontend/src/pages/review/__tests__/qaYolinel.reviewColumns.test.tsx` (2) |
| **QA-018** | «Registrado por» y «Fecha de registro» (`created_at`) **distinguidas** de la fecha del evento, en Lotes, Historial, Mis pendientes, Centro de Revisión y Aprobaciones | Mismos archivos que QA-014 (BE `enrichment.py` + esquemas; FE las cinco vistas) | `backend/tests/test_qa_yolinel_list_enrichment.py` · `frontend/src/pages/review/__tests__/qaYolinel.reviewColumns.test.tsx` · `frontend/src/__tests__/qaYolinel.listColumns.test.tsx` |
| **QA-015** | Filtro **Granja** expuesto en la UI sobre endpoints que ya lo aceptaban (Lotes, Historial, Aprobaciones; el Centro de Revisión ya lo tenía). **Planta de incubación**: brecha funcional declarada (no existe `hatchery_id` en ningún endpoint) | FE: `frontend/src/pages/lots/LotListPage.tsx`, `frontend/src/pages/operations/OperationListPage.tsx`, `frontend/src/pages/approvals/ApprovalPanel.tsx`, `frontend/src/components/ui/FilterPanel.tsx` (disparador y «Limpiar» como hermanos: `<button>` dentro de `<button>` es HTML inválido) | `frontend/src/__tests__/qaYolinel.listColumns.test.tsx` · `frontend/src/pages/review/__tests__/qaYolinel.reviewColumns.test.tsx` · `backend/tests/test_qa_yolinel_list_enrichment.py` |
| **QA-003 / QA-004 / QA-008 / QA-009 / QA-016 (otras fechas)** | Sin cambio de código: quedan como decisión del propietario (**OD-QA2-01…05**) con la documentación de soporte | `OPERATION_STATE_MACHINE.md`, `SAP_PARA_QA.md`, `LOT_ORIGIN_AND_MASTERS_FOR_QA.md`, `PROCESS_PREDECESSOR_MATRIX.md` | — (documentación; ver §2.3) |
| **QA-001 / QA-005 / QA-006 / QA-010 / QA-011** | Sin cambio de código: comportamiento correcto documentado de forma verificable | `LOT_ORIGIN_AND_MASTERS_FOR_QA.md`, `SAP_PARA_QA.md`, `OPERATION_STATE_MACHINE.md` | — (documentación; ver §2.3) |

---

## 2. Detalle de la implementación

### 2.1 Backend

| Archivo | Qué se añadió / cambió | Notas de diseño |
|---|---|---|
| `backend/app/operations/validators.py` | `_es_orden_de_compra`, `_plantas_del_desglose`, `_cadena_unica_del_desglose`, `_cadenas_por_planta`, `derive_oc_business_unit`, `derive_oc_business_units`, `validate_oc_business_unit` | La regla es **estrecha a propósito**: solo bloquea si la cadena es *conocida* y distinta. `business_unit_code` es **informativo** (`OD-16.c`): describe la OC, no concede ni deniega acceso. `validate_oc_limit` (BR-18) queda intacta |
| `backend/app/operations/service.py` | `_cadena_y_codigo_del_lote` + invocación de `validate_oc_business_unit` **solo** en `BIRD_RECEPTION` con `sap_document_ref` | El mensaje de la regla nombra el **lote** (su cadena, no la del cuerpo del evento: `GA-REM-021-A`) |
| `backend/app/operations/enrichment.py` **(nuevo)** | `anotar_nombres(eventos)` → `lot_code`, `farm_name`, `registered_by_name`; `anotar_nombres_de_lotes(lotes)` → `farm_name`, `house_name` | Anotación **aditiva sobre la instancia ORM** (atributos no mapeados): no se persiste nada ni se altera la fila. Coste acotado: 3 consultas por página (lotes, granjas, usuarios) y 2 para lotes, con `.in_(ids)` sobre ids ya acotados por empresa ⇒ sin N+1 |
| `backend/app/integrations/sap/service.py` | `list_references(..., business_unit=...)` + `_anotar_cadena_de_las_ordenes` | El filtro de cadena se aplica **en memoria sobre la página ya leída** (sin joins nuevos) y conserva las OC de cadena desconocida; sin el parámetro, comportamiento idéntico al anterior |
| `backend/app/integrations/sap/router.py` | Query param opcional `business_unit` en `GET /sap/references` | Documentado en el `description` del parámetro |
| `backend/app/integrations/sap/schemas.py` | `SapReferenceRead.business_unit_code: Optional[str]` | Campo de lectura, nunca persistido |
| `backend/app/lots/schemas.py` / `lots/service.py` | `LotRead.farm_name`/`house_name`; `list_lots` anota los nombres | Cambio **aditivo** del contrato: clientes previos siguen funcionando |
| `backend/app/operations/schemas.py` | `OperationalEventRead.lot_code`/`farm_name`/`registered_by_name` | Se distinguen `created_at` (fecha de registro) y `event_date` (fecha del hecho) |
| `backend/app/review/service.py` | Enriquecimiento de las bandejas de revisión y aprobación por la misma vía | Sin consultas por fila |

### 2.2 Frontend

| Archivo | Qué cambió | Hallazgo |
|---|---|---|
| `frontend/src/auth/actionAuthority.tsx` | `useCan` memoizado con `useCallback([user])`: identidad estable entre renders | QA-017 |
| `frontend/src/pages/review/ReviewCenter.tsx` | `t`/`toast` por `ref`, dependencia booleana `canReadUsers`, `fetchEvents` con dependencias estables; columnas Granja / Registrado por / Fecha del evento / Fecha de registro; lote por código | QA-017, QA-014, QA-018 |
| `frontend/src/pages/approvals/ApprovalPanel.tsx` | Filtro Granja (envía `farm_id`), columnas de autor/registro | QA-015, QA-018 |
| `frontend/src/pages/masters/MasterListPage.tsx` | Desactivar/Reactivar, columna Estado, fila atenuada, toast de error, `useToast` opcional; columna de padre (granja/planta) | QA-002, QA-012 |
| `frontend/src/components/data-table/DataTable.tsx` | `rowClassName` y `RowAction.visible` (acciones que no aplican a todas las filas) | QA-002 |
| `frontend/src/components/ui/FilterPanel.tsx` | Disparador y «Limpiar» como **hermanos** (se elimina el `<button>` anidado) | QA-015 (defecto colateral encontrado al añadir filtros) |
| `frontend/src/utils/dates.ts` | `hoyISO()`: fecha civil local compuesta por partes (sin `toISOString`, que mide en UTC) | QA-016 |
| `frontend/src/pages/operations/OperationFormPage.tsx` | `max=hoyISO()` en fecha del evento y en salida/llegada de importación; selector de OC por cadena del lote, bloqueado hasta elegir lote, con rótulo de cadena / «sin cadena» y limpieza de la OC que deja de ser válida | QA-016, QA-007 |
| `frontend/src/pages/operations/OperationListPage.tsx` | Columnas Lote/Granja/Fecha del evento/Registrado por/Fecha de registro + filtro Granja | QA-014, QA-015, QA-018 |
| `frontend/src/pages/operations/MyPendingPage.tsx` | Lote y granja en las tarjetas propias | QA-014 |
| `frontend/src/pages/lots/LotListPage.tsx` | Columna Granja y filtro Granja enviado al servidor (`GET /lots?farm_id=`) | QA-014, QA-015 |
| `frontend/src/App.tsx` | Definiciones de columna de los 20 maestros con `masters.fields.*` | QA-013 |
| `frontend/public/locales/{es,en}/translation.json` | Claves nuevas: `common.deactivate|reactivate|confirmDeactivate|deactivateWarning|farm|allFarms|lotCode|registeredBy|registeredAt|eventDate`, bloque `masters.fields.*`, `operations.sapOrderNoChain|selectLotFirst` | QA-013, QA-002, QA-014, QA-018, QA-007 |

### 2.3 Documentación entregada (sin cambio de código)

| Documento | Hallazgo que atiende |
|---|---|
| `OPERATION_STATE_MACHINE.md` | QA-010 (rechazo, cancelación, reverso y sus guardas) |
| `SAP_PARA_QA.md` | QA-005 (HANA solo lectura → RAW → validación → mapeo → staging → promoción controlada) |
| `LOT_ORIGIN_AND_MASTERS_FOR_QA.md` | QA-001 (sin FK granja→unidad; cadena derivada del lote), QA-006 (`NATIVE`/`MIGRATED`, SAP nunca crea lotes), QA-011 (BR-14/RR-03, segregación) |
| `PROCESS_PREDECESSOR_MATRIX.md` | QA-009 (matriz propuesta; no implementada, pendiente **OD-QA2-04**) |

### 2.4 Nota de alcance del diff

El árbol de trabajo de la ronda incluye, además de los archivos de esta tabla, `tools/deepseek_executor/server.py`,
que pertenece al **arnés del ejecutor** y no a la remediación de SPEC 008: no forma parte de la evidencia de
este documento y se excluye del alcance de la certificación.

---

## 3. Qué NO se hizo y por qué

Cada punto corresponde a una **prohibición explícita del mandato** o a una **decisión del propietario** pendiente.
Ninguna de estas omisiones es un olvido: son límites declarados.

| No se hizo | Por qué |
|---|---|
| **FK de unidad de negocio en los maestros** (granja/planta → unidad) | **GA-REM-040**: una granja aloja galpones de varias unidades; la cadena se deriva de `lots.bird_type`. Una FK forzaría un modelo que el negocio no tiene (QA-001) |
| **Zona/área en la planta de incubación** | **GA-REM-039** define Área como estructura **organizativa**, no zona física; copiar el modelo de `Farm` exige **OD-QA2-02** (QA-004) |
| **«Planta = Granja»** (unificar el maestro de planta con el de granja) | Son entidades distintas con semántica distinta; fusionarlas rompería trazabilidad y permisos |
| **Autocompletado adicional desde la OC** (granja/galpón/lote/transporte) | Requiere los mappings **SAP-STO-01** (LGORT↔galpón) y WERKS↔granja, hoy `PENDING` (AOD-02 / OD-24 P-08). Autocompletar sin mapping aprobado sería **no determinista**; queda en **OD-QA2-03** (QA-008) |
| **Eliminar o relajar validaciones existentes** (BR-18, BR-19, BR-14, R-30) | BR-23 se añade **junto a** `validate_oc_limit`; ninguna regla previa se modificó ni se desactivó. No se redujo ningún test |
| **Crear un usuario administrador para probar la segregación** | La segregación se prueba con los usuarios y roles sembrados (`test_segregation_r143` g01-g06); crear un admin ad hoc sería un artefacto de prueba con privilegios, prohibido por el mandato |
| **Borrar datos QA** | El dataset **QA-DEMO-V1** (SPEC 007) es insumo de la ronda y sigue sin cargar en runtime (`BLOCKED_EXTERNAL`); no se limpió ni se recreó nada |
| **Llamadas SAP reales** | **0 llamadas SAP** en toda la ronda: los escenarios BR-23 se construyen con referencias cargadas en modo manual y mappings `PLANT` sembrados por el test |
| **Tocar `.github/workflows`** | Prohibido por el mandato de ejecución |
| **Rama nueva / push** | Todo el trabajo vive en `main` sobre el árbol de trabajo; sin rama nueva y sin push desde esta estación |
| **Verificación en runtime / UAT** | La base UAT no es alcanzable desde esta estación: se declara `NOT_VERIFIED_FROM_WORKSTATION` con checklist manual en `08_RUNTIME_VERIFICATION.md` |
| **Contraste con el PDF original de QA** | El PDF «REVISION GENERAL DE SISTEMA GLOBAL AVICOLA - 17-10-2026.pdf» **no estaba disponible** en la estación: los hallazgos se trabajaron desde el mandato del Owner y quedan **pendientes de contraste con el PDF** (`01_SOURCE_FINDINGS.md`) |
| **Implementar el orden de procesos en backend** | No hay catálogo de predecesores en el backend; la secuencia vive en la UI. Se entrega matriz propuesta y se pide **OD-QA2-04** (QA-009) |
| **Filtro por planta de incubación** | No existe `hatchery_id` en ningún endpoint: es una brecha funcional de modelo, no un defecto de UI (QA-015). Declarada, no maquillada con un filtro de cliente |

---

## 4. Marcadores de cierre

| Dato | Valor |
|---|---|
| SHA de implementación | `dbd6122a3b32512cf8bf2ae6b4f7b91cf43a9124` (IMPL) |
| Refuerzo de pruebas guardianas | `9390afcad3ca57dcea17d8065054978abe1a0720` (IMPL-2 — guardián QA-013 a los 20 maestros + identidad estable de `useCan`; `qaYolinel.red.test.tsx` 4 → 23 casos, +19) |
| SHA de certificación | `{{CERT_SHA}}` |
| Regresión backend completa | **1739 passed · 0 failed · 49 skipped (22 min 26 s)** (ver `07_TEST_EVIDENCE.md`) |
| Regresión frontend completa | **96 archivos · 557 pruebas PASS · tsc rc 0 · build rc 0** pre-mutación; post-mutación con IMPL-2: **96 archivos · 576 pruebas PASS · tsc rc 0 · build rc 0** (ver `07_TEST_EVIDENCE.md`) |
| Sensibilidad S1/S5/S6/S7/S8 | **5/5 DETECTED** (S7 y S8 tras el refuerzo IMPL-2) — detalle en `07_TEST_EVIDENCE.md` §3 |
| Runtime | `NOT_VERIFIED_FROM_WORKSTATION` (`08_RUNTIME_VERIFICATION.md`) |
| Llamadas SAP reales | **0** |

# Feature Specification: SPEC 006 — Cutover Initial Balances Remediation (Cargas Iniciales v2)

**Directorio**: `specs/006-cutover-initial-balances-remediation` · **Rama**: `main` (sin rama nueva)
**Created**: 2026-10-15 · **Baseline**: `57a421a` · **Status**: `IMPLEMENTING`
**Tipo**: `POST_CERTIFICATION_CUTOVER_INITIAL_LOAD_REMEDIATION` (evolución de GA-REQ-061 · T14 · P-16; no reabre PRE-SAP ni SPEC 005) · **Prioridad**: P0 · **Dependencias**: GA-REQ-061, OD-16, OD-09, OD-14, OD-19, OD-21, BR-06, BR-19, R-28, AOD-29
**Input**: Mandato Owner «REMEDIACIÓN CARGAS INICIALES / SALDOS DE APERTURA — MODO AUTÓNOMO» (2026-10-15) + fallo observado en vivo por el Owner
**Paquete de auditoría asociado**: `audit/cutover-initial-balances/01…16`
**Target**: `CUTOVER_INITIAL_LOAD_READY_FOR_REAL_GO_LIVE`

---

## PURPOSE

Que una empresa pueda recibir los saldos iniciales reales de **progenitoras, reproductoras (cría y producción), incubadora y pollo de engorde** mediante una plantilla **específica por unidad de negocio** (XLSX o CSV), que cada dato quede ubicado en la entidad y columna correctas de Global Avícola, que la reconciliación demuestre los saldos y que el **primer evento operativo posterior al corte** funcione sin reconstruir historia a mano.

## PROBLEM / EVIDENCE

| Hecho | Evidencia |
|---|---|
| Las 4 BU reciben la misma plantilla v1 de 8 columnas (`legacy_lot_code … notes`) | `backend/app/cutover/templates.py:25-28`; `parser.py:15` («las variantes por BU se añadirán») |
| Solo `.xlsx`; un CSV responde `INVALID_FILE: File is not a zip file` | `CargasInicialesPage.tsx` (`accept=".xlsx"`); reproducción `audit/cutover-initial-balances/evidence/head-repro/journal.json` (caso C) |
| La descarga usa la BU del **selector**, que sigue editable con un batch en curso → `422 BUSINESS_UNIT_MISMATCH` | reproducción caso B (`04_B_bu_mismatch.png`) |
| `N/A` y celda vacía se colapsan a `None`; `live_males = N/A` pasa como fila **válida** y acaba en `initial_male_count = 0` | `parser.py:138-149`, `service.py:346`; reproducción caso A2 (`LOTE-REP-02` válida) |
| La plantilla vacía queda «validada» con 0 filas; al recargar la página se pierde el batch (no hay listado) | reproducción casos A1 y D |
| El apply ancla **todo** opening a la primera fase activa (`CRIA`), no crea `LotPhase`, ni `house_id`, ni genética, ni sexo | `service.py:298-305, 322-328` |
| Alimento, peso, descartes, huevos, nacimientos y aves recibidas nunca se capturan; sus `*_status` se fijan en código | `service.py:333-360` |
| Incubadora se migra como «lote de aves»; no existe entidad para una incubación en curso; los saldos de huevos/pollitos ignoran el opening | `validators.py:184-227`; `CUTOVER_GAP_MATRIX.md` CUT-06 |
| No existe la guarda de fecha de corte (CUT-GL-02): se aceptan eventos entre la fecha real de inicio y el corte, que el saldo cuenta y la reconciliación no | `validators.py:551-561`; `reporting.py:69` |
| E2E P-16 solo prueba continuidad en broiler; grandparent/breeder/hatchery sin evento post-corte | `e2e/proceso-p16-…:234-239` |

**Fallo live**: con las credenciales UAT disponibles (operador/aprobador de progenitoras, sin `cutover:*`) no se pudo ejecutar el upload en el runtime compartido (`403 Permiso requerido: cutover:create`); el runtime corre `57a421a` (sin drift). Los modos de fallo se reprodujeron sobre HEAD por la UI real (`01_LIVE_FAILURE_ROOT_CAUSE.md`).

## ARCHITECTURE_DECISION

```text
CUTOVER_TEMPLATE_MODEL = ONE_CONTRACT_PER_BUSINESS_UNIT   (CUTOVER_GRANDPARENT_V2 · _BREEDER_V2 · _HATCHERY_V2 · _BROILER_V2)
CUTOVER_FORMATS        = XLSX (recomendado) + CSV (misma normalización)
TEMPLATE_VERSION       = v2 · V1_STATUS = RETIRED_WITH_CLEAR_ERROR
DATA_SEMANTICS         = VACÍO=UNKNOWN · 0=KNOWN_ZERO · N/A=NOT_APPLICABLE, preservados por métrica (value + status) de punta a punta
PIPELINE               = FILE → PARSE → NORMALIZE → STAGING → VALIDATE → PREVIEW → SUBMIT → APPROVE → APPLY (atómico) → RECONCILIATION → OPERATE
SHARED                 = parser framework · staging · batch lifecycle · segregación · auditoría · idempotencia · apply transaccional
BU_SPECIFIC            = campos · validaciones · mapping · promoción · preview · reconciliación · primer evento post-corte
CUT-GL-02              = IMPLEMENTED (evento con event_date ≤ fecha civil del corte sobre lote con opening de cutover ⇒ rechazo determinista)
HATCHERY_OPENING       = nueva entidad canónica (hatchery_openings), no notas libres
```

## SCOPE

1. **Contratos v2** (`backend/app/cutover/contracts.py`, registry cerrado): campos por BU con tipo, unidad, obligatoriedad, UNKNOWN/N/A admitidos, maestro de referencia, destino y regla de promoción (`template-contract.md`).
2. **Plantillas**: `GET /cutover-templates/{bu}?format=xlsx|csv` → `cutover_template_{bu}_v2.{xlsx|csv}`. XLSX con hojas `Instrucciones`, `Meta`, `Datos`, `Catalogos` (dinámica por empresa y BU). CSV = solo `Datos` (UTF-8, `;` o `,` detectado de forma determinista).
3. **Parser común** XLSX/CSV → mismo DTO normalizado (`{campo: {value, status}}`), con validación estructural (archivo, MIME, tamaño, filas, columnas, versión, BU, Meta.company), de dominio (maestros por empresa, padre-hijo, fase compatible, lote existente, opening existente) y de consistencia (balances solo con componentes KNOWN).
4. **Apply por BU**: `Lot` (+ `house_id`, `area_id`, `genetic_line_id`, `breed_id`, `sex`, `hatchery_purpose`, `source_*`), `LotPhase` real, `OpeningBalance` completo con estado por métrica (nuevas columnas), `HatcheryOpening` para incubadora.
5. **Consumo**: saldos de aves/huevos/pollitos incluyen el opening (incl. incubadora); guarda CUT-GL-02; reconciliación por BU; informe de lote con lifetime y estados.
6. **API**: listado y detalle de batches, descarga de errores (CSV/XLSX), preview por BU.
7. **Frontend** `CargasInicialesPage`: flujo guiado (BU → corte → batch → plantillas XLSX/CSV → subir → validación/errores descargables → preview por BU → enviar → aprobar → aplicar → reconciliar → ir a los lotes), batch persistente, BU bloqueada, i18n ES/EN, 360/390/desktop.
8. **Pruebas**: RED, unit/integración (4 BU × 2 formatos + negativas), E2E UI por BU con primer evento post-corte, mutación S1–S12, regresión completa, verificación en runtime.
9. **Documentación**: `audit/cutover-initial-balances/01…16`; `CUTOVER_MASTER_SPEC` con addendum (historia v1 preservada).

## OUT_OF_SCOPE

SAP real o referencias SAP fabricadas (SPEC 005 intacta) · inventarios valorizados de SAP · inventarios operacionales no ligados a lote (alimento en almacén, vacunas, medicinas: `GL-OD-07`, ver `OUT_OF_SCOPE` explícito en `02_CURRENT_GAP_ANALYSIS`) · acta inmutable CUT-GL-01, secuencia multi-BU CUT-GL-03, reapertura CUT-GL-05 · cambios de RBAC, OD-16, multiempresa · borrado de la certificación GA-REQ-061 · redefinición de FCR/AFCR (R-134) · tolerancias de consistencia (sin regla Owner, ninguna).

## REQUIREMENTS

| ID | Requisito |
|---|---|
| FR-01 | Cada BU tiene su contrato v2 propio; ninguna comparte hoja `Datos` con otra. |
| FR-02 | XLSX y CSV producen exactamente el mismo DTO normalizado; prueba de paridad por BU. |
| FR-03 | `v1` responde `TEMPLATE_VERSION_UNSUPPORTED` con mensaje claro; nunca se reinterpreta como v2. |
| FR-04 | Toda métrica se persiste con `value` y `status ∈ {KNOWN, UNKNOWN, NOT_APPLICABLE}`; `UNKNOWN` jamás se convierte en `0`; `N/A` en campo obligatorio ⇒ error. |
| FR-05 | Las referencias viajan por código/nombre y se resuelven dentro de la empresa efectiva y la BU; maestro inactivo no admite referencia nueva (OD-21); padre-hijo validado. |
| FR-06 | `Meta.company ≠ empresa efectiva` o `Meta.business_unit ≠ batch` ⇒ rechazo; el batch y el actor son la autoridad. |
| FR-07 | Límites: 5 MB, 5 000 filas de datos, 60 columnas; fórmulas y macros rechazadas; archivo vacío/corrupto/extensión falsa ⇒ error controlado. |
| FR-08 | El apply es atómico por batch; crea o reutiliza lote (REUSE solo si misma empresa, `ACTIVE`, mismo `bird_type` y sin eventos), `LotPhase` en la fase declarada, `OpeningBalance` completo y `HatcheryOpening` cuando aplica. |
| FR-09 | Lote migrado: `origin=MIGRATED`, `legacy_lot_code`, `source_system`, `source_reference`; `cutover_datetime` en el opening; lotes `NATIVE` no se alteran. |
| FR-10 | CUT-GL-02: en un lote con opening de cutover, un evento con `event_date ≤ fecha civil del corte` se rechaza con regla `CUT-GL-02`. |
| FR-11 | Saldos de aves (incl. `initial_mixed_count`), huevos en incubadora, pollitos viables y población por sexo incorporan el opening. |
| FR-12 | Reconciliación por BU: opening / post / lifetime / current por métrica, con `UNKNOWN + n = UNKNOWN`. |
| FR-13 | Errores estructurados (`row_number, column, field, error_code, message, received_value`) visibles en pantalla y descargables (CSV/XLSX). |
| FR-14 | Idempotencia: mismo archivo en el mismo batch no duplica; mismo checksum en batch equivalente ⇒ 409; re-upload reemplaza el staging; `APPLIED` no admite upload; doble apply ⇒ 409; opening duplicado ⇒ rechazo. |
| FR-15 | Segregación creador ≠ aprobador; permisos `cutover:*` sin cambios; backend es la autoridad. |
| FR-16 | Batches listables y recuperables (`GET /cutover-batches`, `GET /cutover-batches/{id}`), filtrados por empresa efectiva (R-201). |
| FR-17 | UI guiada, BU bloqueada con batch en curso, input de archivo reseteable, preview por BU, estado final con enlaces a los lotes; i18n ES/EN; sin desbordes a 360/390 px. |

## BUSINESS RULES AFFECTED

BR-01…BR-04 (saldos: ahora incluyen el opening, también de incubadora) · BR-06 (sin cambio) · **CUT-GL-02** (nueva, determinista) · OD-16/OD-09/OD-14 (sin cambio) · OD-19 (sin cambio; post-corte con contrapartidas) · OD-21 (`MASTER_INACTIVE`) · R-28 (fechas relativas en pruebas) · RC-08/RR-08 (histórico no se resta dos veces).

## AFFECTED LAYERS

| Capa | Cambio |
|---|---|
| Backend | `cutover/contracts.py` (nuevo), `parser.py` (v2 XLSX+CSV), `templates.py`, `service.py`, `router.py`, `schemas.py`, `reporting.py`, `models.py` (+`HatcheryOpening`), `lots/models.py` (`OpeningBalance` +columnas), `operations/validators.py` (saldos + CUT-GL-02), `reports/service.py` (población mixta, lifetime en informe de lote), `business_units/route_scope.py` |
| Base de datos | 1 migración: columnas nuevas en `opening_balances`, tabla `hatchery_openings`; `downgrade` funcional |
| Frontend | `pages/cutover/CargasInicialesPage.tsx` (+ componentes), `services/cutover.service.ts`, locales ES/EN |
| Pruebas | `backend/tests/test_cutover_v2_*.py`, ajuste de `test_ga_req_061_cutover_*` (fixture v1 → v2), `frontend/src/__tests__/r061.cutoverFlow.test.tsx` + nuevo, `e2e/proceso-p16-cutover-*.spec.ts` (4 BU) |

## ERRORS (catálogo cerrado, `09_VALIDATION_CATALOG.md`)

`INVALID_FILE · FILE_TOO_LARGE · TOO_MANY_ROWS · TOO_MANY_COLUMNS · UNSUPPORTED_EXTENSION · MIME_MISMATCH · FORMULA_NOT_ALLOWED · MACRO_NOT_ALLOWED · NO_DATA_ROWS · TEMPLATE_VERSION_UNSUPPORTED · BUSINESS_UNIT_MISMATCH · COMPANY_MISMATCH · SHEET_MISSING · HEADER_MISSING · HEADER_DUPLICATE · HEADER_UNKNOWN · REQUIRED_FIELD_MISSING · NOT_APPLICABLE_ON_REQUIRED · NOT_APPLICABLE_NOT_ALLOWED · INVALID_NUMBER · INVALID_INTEGER · NEGATIVE_VALUE · INVALID_DATE · INVALID_ENUM · INVALID_TEXT_LENGTH · MASTER_NOT_FOUND · MASTER_INACTIVE · MASTER_AMBIGUOUS · PARENT_MISMATCH · PHASE_INCOMPATIBLE · METRIC_NOT_APPLICABLE_IN_PHASE · LOT_DUPLICATE · LOT_EXISTS_REUSE_REJECTED · OPENING_ALREADY_EXISTS · CONSISTENCY_MISMATCH · DATE_ORDER_INVALID · DUPLICATE_UPLOAD · BATCH_STATE_INVALID · BU_DISABLED · BU_NOT_GRANTED · SEGREGATION_VIOLATION · PHASE_REQUIRED · APPLY_FAILED · CUT-GL-02`

## EDGE CASES

Fila totalmente vacía (ignorada) · `0` explícito (KNOWN) · `N/A` en métrica de producción en CRIA (NOT_APPLICABLE válido) · `N/A` en `live_*` (error) · lote existente CLOSED (REJECT) · lote existente con eventos (REJECT) · mismo `legacy_lot_code` en otra empresa (REJECT) · fase PROD sin `phase_start_date` (se usa `real_start_date`, anotado) · hatchery con `eggs_set = 0` (proceso recién recibido) · `chicks_available > chicks_hatched` (error) · evento el mismo día del corte (rechazado por CUT-GL-02; el post empieza al día siguiente) · CSV con `;` y decimales `1.5` (punto decimal obligatorio) · BOM UTF-8 · cabecera con espacios · archivo `.xlsm` · XLSX con fórmula en celda de datos.

## ACCEPTANCE CRITERIA (Given / When / Then; evidencia en `12_TEST_EVIDENCE.md`)

| AC | Criterio |
|---|---|
| AC-CUT2-01 | Given el runtime compartido y HEAD, When se intenta el flujo, Then el fallo queda reproducido en HEAD por la UI y la causa runtime demostrada (`01_…`) |
| AC-CUT2-02 | Root cause documentada con evidencia |
| AC-CUT2-03 | `NEW_BRANCH_CREATED = NO` |
| AC-CUT2-04…07 | Given la BU, When se descarga la plantilla, Then es la específica de grandparent / breeder / hatchery / broiler (headers exactos del contrato) |
| AC-CUT2-08 | XLSX v2 se parsea, valida y aplica |
| AC-CUT2-09 | CSV v2 se parsea, valida y aplica |
| AC-CUT2-10 | La hoja `Instrucciones` describe cada campo (significado, obligatorio, formato, unidad, ejemplo, valores, UNKNOWN, N/A) y la semántica vacío/0/N/A |
| AC-CUT2-11 | La hoja `Catalogos` trae solo maestros activos de la empresa efectiva y de la BU |
| AC-CUT2-12 | `v1` ⇒ `TEMPLATE_VERSION_UNSUPPORTED`; `v2` se acepta; `Meta.company` ajena ⇒ `COMPANY_MISMATCH` |
| AC-CUT2-13 | Celda vacía ⇒ `status=UNKNOWN`, valor nulo, nunca 0 |
| AC-CUT2-14 | `0` ⇒ `KNOWN`, valor 0 |
| AC-CUT2-15 | `N/A` ⇒ `NOT_APPLICABLE`, distinto de UNKNOWN en staging, opening y reconciliación |
| AC-CUT2-16 | Campos obligatorios por BU validados (`REQUIRED_FIELD_MISSING`, `NOT_APPLICABLE_ON_REQUIRED`) |
| AC-CUT2-17 | Maestros validados por empresa y estado (`MASTER_NOT_FOUND`, `MASTER_INACTIVE`, `MASTER_AMBIGUOUS`) |
| AC-CUT2-18 | Relaciones padre-hijo validadas (`PARENT_MISMATCH`: galpón→granja, incubadora/nacedora→planta, raza→línea, fase→BU) |
| AC-CUT2-19 | Un upload no toca tablas operacionales (solo staging) |
| AC-CUT2-20 | Re-upload reemplaza el staging previo; sin duplicados |
| AC-CUT2-21 | Errores descargables (CSV y XLSX) con `row_number, field, error_code, message, received_value` |
| AC-CUT2-22 | Preview por BU con el resumen funcional y el detalle expandible |
| AC-CUT2-23…26 | Apply grandparent / breeder / hatchery / broiler coloca cada campo en su destino (`10_APPLY_DESTINATION_MATRIX`) |
| AC-CUT2-27 | `UNMAPPED_TEMPLATE_FIELDS = 0` |
| AC-CUT2-28 | `REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE = 0` |
| AC-CUT2-29 | Opening y `LotPhase` en la fase real declarada; lote migrado con origen y procedencia |
| AC-CUT2-30…33 | Primer evento post-corte válido en grandparent / breeder (cría y producción) / hatchery / broiler, consumiendo el opening |
| AC-CUT2-34 | Continuidad de saldos y lifetime (UNKNOWN propagado) en reconciliación e informe de lote |
| AC-CUT2-35 | CUT-GL-02: evento ≤ corte rechazado; evento > corte aceptado |
| AC-CUT2-36 | Mismo archivo ⇒ no duplica; mismo checksum en batch equivalente ⇒ 409 |
| AC-CUT2-37 | Doble apply ⇒ 409 |
| AC-CUT2-38 | Creador ≠ aprobador |
| AC-CUT2-39 | Empresa A no ve, usa ni aplica lo de B |
| AC-CUT2-40 | BU deshabilitada ⇒ 403 incluso para actor global; actor sin grant ⇒ 403 |
| AC-CUT2-41 | RBAC `cutover:*` intacto (401/403) |
| AC-CUT2-42…44 | 360 px, 390 px y desktop sin desborde horizontal |
| AC-CUT2-45 | i18n ES/EN con paridad de claves |
| AC-CUT2-46 | Backend dirigido PASS |
| AC-CUT2-47 | Frontend PASS |
| AC-CUT2-48 | `tsc -b` PASS |
| AC-CUT2-49 | `vite build` PASS |
| AC-CUT2-50 | E2E UI 4/4 BU PASS |
| AC-CUT2-51 | Contratos XLSX/CSV: 8 caminos positivos + paridad |
| AC-CUT2-52 | Mutación S1–S12 DETECTED |
| AC-CUT2-53 | Regresión post-mutación PASS |
| AC-CUT2-54 | Regresión completa backend 0 FAIL |
| AC-CUT2-55 | E2E relevante (P-16 nuevo + procesos afectados + navegación) PASS |
| AC-CUT2-56 | Verificación en runtime compartido PASS o `LOCALLY_CERTIFIED_RUNTIME_VERIFICATION_PENDING` con causa explícita |
| AC-CUT2-57 | `REMOTE_SHA_MATCH = PASS` |
| AC-CUT2-58 | `TREE = CLEAN` |

## TESTS REQUIRED

`09_TEST_MATRIX` en `12_TEST_EVIDENCE.md`: RED (9 escenarios), contratos (4 BU × 2 formatos + paridad), negativas (§33 del mandato), apply/destino por BU, continuidad post-corte por BU, CUT-GL-02, idempotencia, segregación, multiempresa/BU, frontend, E2E UI por BU, S1–S12.

## RISKS

| Riesgo | Mitigación |
|---|---|
| Credenciales UAT sin `cutover:*` impiden reproducir/verificar en runtime | se pide al Owner un usuario UAT con `cutover:*`; mientras, verificación local completa y veredicto `LOCALLY_CERTIFIED_RUNTIME_VERIFICATION_PENDING` si no llega |
| Retirar v1 rompe fixtures de GA-REQ-061 | se migran a v2 (mismos casos, columnas nuevas), historia v1 preservada en docs |
| Cambios en saldos (`initial_mixed_count`, opening de incubadora) afectan a validadores certificados | solo suman términos con opening presente; suites P-01…P-15 y GA-REQ-061 en la regresión completa |
| `OpeningBalanceRead` lanza `ValueError` si mortalidad > vivas (dato real posible) | validador relajado: la regla de consistencia vive en el parser; lectura nunca 500 |

## ROLLBACK

`alembic downgrade -1` elimina `hatchery_openings` y las columnas nuevas de `opening_balances`. Los batches v1 aplicados se conservan. Plantillas v2 pueden desactivarse volviendo a servir solo v1 (no previsto).

## DEFINITION OF DONE

Gates del mandato §41 en PASS con cifras reales · `UNMAPPED_TEMPLATE_FIELDS = 0` · `REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE = 0` · 3 commits (spec+RED, implementación, certificación) · push y `REMOTE_SHA_MATCH` · runtime verificado o pendiente con causa.

## CLARIFICATIONS

| # | Pregunta | Clase | Resolución |
|---|---|---|---|
| Q1 | ¿Cómo se referencian galpones, incubadoras, nacedoras y razas si no tienen `code`? | GA_DECISION | Por **nombre dentro de su padre** (`house_name` en la granja, `incubator_name`/`hatcher_name` en la planta, `breed_name` en la línea genética); duplicado ⇒ `MASTER_AMBIGUOUS`. No se añaden columnas `code` a maestros (fuera de alcance). |
| Q2 | ¿Fase inicial de un lote migrado? | GA_DECISION | La declara la plantilla (`productive_phase_code`), validada contra la BU: grandparent/breeder ∈ {`CRIA`, `PROD`}, broiler = `ENGORDE`, hatchery = `INCUB` (implícita). Se crea `LotPhase` con `phase_start_date` o, si falta, `real_start_date` (anotado en `opening_state`). |
| Q3 | ¿Población de engorde por sexo? | GA_DECISION | `live_birds` (mixto) → nueva columna `initial_mixed_count`; mortalidad/descartes históricos de engorde → `accumulated_mortality_mixed` / `accumulated_culls_mixed`. Los saldos suman las tres poblaciones. |
| Q4 | ¿Dónde vive una incubación en curso? | GA_DECISION | Nueva tabla `hatchery_openings` (1:1 con `opening_balances`): planta, equipo, lote origen, generación, fechas, huevos recibidos/cargados/transferidos/descartados, pollitos nacidos/disponibles, con estado por métrica. Los saldos de incubadora la incorporan. |
| Q5 | Semántica exacta de la fecha de corte | GA_DECISION | Los datos de la plantilla representan el estado **hasta el final del día civil del corte**. POST = `event_date > cutover_date` (igual que la reconciliación certificada). CUT-GL-02 rechaza `event_date ≤ cutover_date` en lotes con opening de cutover. |
| Q6 | ¿v1? | GA_DECISION | `RETIRED_WITH_CLEAR_ERROR`: v1 no puede declarar fase ni galpón y su apply producía estado incorrecto (fase CRIA universal). |
| Q7 | ¿Consistencia con componentes UNKNOWN? | GA_DECISION | La ecuación solo se evalúa si todos sus componentes son KNOWN; si alguno es UNKNOWN/N/A no se evalúa ni se inventa. Sin tolerancias. |
| Q8 | ¿Inventarios transversales (alimento en almacén, vacunas, medicinas)? | OWNER_DECISION (GL-OD-07) | `OUT_OF_SCOPE` explícito: no son saldos de lote; pertenecen a maestros/inventario (SAP o administración). Documentado en `02_…`. |
| Q9 | ¿Aprobador ≠ aplicador? | GA_DECISION | No se añade (la matriz T14 no lo implementó y el mandato no lo pide); se mantiene creador ≠ aprobador. |
| Q10 | ¿Qué pasa con batches v1 ya aplicados? | GA_DECISION | Se conservan; la reconciliación los sigue mostrando con sus estados. |
| Q11 | ¿KPIs lifetime (FCR/AFCR/IPE)? | GA_DECISION | Población y mortalidad incorporan el opening (incl. mixto). FCR/AFCR/IPE siguen calculándose sobre el post-corte (R-134 diferida); el informe de lote expone `lifetime` por métrica con estado, y `UNKNOWN` se propaga. |
| Q12 | ¿Credenciales de runtime? | OWNER_DECISION | Las UAT disponibles no tienen `cutover:*`; se requiere un usuario UAT con `cutover:create/validate/submit/apply` y otro con `cutover:approve` para la verificación final. |

## ANALYZE

`16_TRACEABILITY.md §3`: contradicciones abiertas = 0 (verificado contra el dominio: fases por código, pesos en gramos, saldos existentes, OD-16/OD-21).

# GA-REQ-061 · MATRIZ DE CRITERIOS DE ACEPTACIÓN (AC01…AC85)

Estado: **SPEC_READY** · Implementación: NOT_STARTED · Cada AC es criterio de aceptación verificable por test (BE preferente; FE donde indique). Mapeo a planes: RED (`GA_CUTOVER_RED_TEST_PLAN.md`), Sensibilidad, E2E.

## Gobernanza (AC01–AC05)

| AC | Criterio |
|---|---|
| AC01 | Existe Spec formal antes de implementar (este paquete, commit documental). |
| AC02 | R-67 auditado y reconciliado (`PARTIAL_REUSE`). |
| AC03 | GAP analysis contra código actual completada. |
| AC04 | Fase documental no modifica producto (`PRODUCT_DIFF=0`). |
| AC05 | T9 cerrado (`7a158d5`) antes de esta ingeniería. |

## Fechas e identidad (AC06–AC09)

| AC | Criterio |
|---|---|
| AC06 | `real_start_date` y `cutover_datetime` son conceptos distintos en el modelo y la API. |
| AC07 | `real_start_date` conserva la fecha real (no se sustituye por la de migración). |
| AC08 | `cutover_datetime` define el inicio de responsabilidad operacional de GA. |
| AC09 | Un opening APPLIED no cambia su `cutover_datetime` directamente (solo corrección formal). |

## Semántica saldo/acumulado (AC10–AC14)

| AC | Criterio |
|---|---|
| AC10 | Opening live birds = saldo **vivo** al corte. |
| AC11 | Historical mortality = acumulado **previo** (no resta del saldo vivo). |
| AC12 | Post-cutover mortality contiene **únicamente** eventos posteriores al corte. |
| AC13 | `lifetime_mortality = historical + post` cuando ambos KNOWN. |
| AC14 | Historical mortality **no se resta de nuevo** del saldo vivo (caso 10.000−35=9.965; 535 lifetime). |

## UNKNOWN (AC15–AC18)

| AC | Criterio |
|---|---|
| AC15 | `UNKNOWN != 0` (API/UI/reportes conservan la semántica). |
| AC16 | `NOT_APPLICABLE != 0`. |
| AC17 | KPI histórico incompleto **no se fabrica** (se muestra UNKNOWN / «información histórica insuficiente»). |
| AC18 | KPI post-cutover se calcula independientemente con datos post-cutover. |

## Lotes (AC19–AC23)

| AC | Criterio |
|---|---|
| AC19 | Se distingue NATIVE/MIGRATED (o equivalente) con metadata de origen. |
| AC20 | Un lote existente **no se duplica** al relacionar su opening. |
| AC21 | `legacy_lot_code`/referencia externa NO reemplaza el PK interno. |
| AC22 | Si el cutover crea lote migrado: masters existentes, empresa correcta, BU habilitada, código sin colisión, reglas de Lot respetadas. |
| AC23 | **No** se crea recepción histórica ficticia ni movimientos artificiales. |

## Batch (AC24–AC30)

| AC | Criterio |
|---|---|
| AC24 | Lifecycle de batch: DRAFT→VALIDATING→VALIDATED→PENDING_APPROVAL→APPROVED→APPLIED (+REJECTED; evaluar CANCELLED). |
| AC25 | `APPLIED` es terminal. |
| AC26 | Batch inválido no puede APPLY (0 aplicados si 4/42 inválidos). |
| AC27 | Apply es **atómico** (todo-o-nada, transacción única). |
| AC28 | Error ⇒ rollback total. |
| AC29 | Apply duplicado no duplica efectos (idempotencia). |
| AC30 | Apply concurrente ⇒ exactamente un efecto (uno 200, otro 409/determinista). |

## Tenancy (AC31–AC34)

| AC | Criterio |
|---|---|
| AC31 | Company A no puede **ver** batch de B (listado/detalle/archivo). |
| AC32 | Company A no puede **modificar** batch de B. |
| AC33 | Company A no puede **APPLY** batch de B. |
| AC34 | Cada opening pertenece inequívocamente a una company (validación de lote/master incluida). |

## Business Unit (AC35–AC38)

| AC | Criterio |
|---|---|
| AC35 | Company BU OFF bloquea APPLY **incluso para actor global** (OD-16 absoluto). |
| AC36 | Usuario sin grant de la BU del batch no opera cutover. |
| AC37 | El cutover **no habilita** BU. |
| AC38 | El cutover **no concede** grants ni altera `effective_business_units`. |

## RBAC (AC39–AC42)

| AC | Criterio |
|---|---|
| AC39 | Backend es autoritativo (403/404 fail-closed).
| AC40 | Sin bypass genérico de admin (OD-14). |
| AC41 | APPLY requiere permiso explícito (módulo cutover, PROPOSED). |
| AC42 | Corrección requiere permiso de correcciones (`corrections` existente) o equivalente documentado. |

## Excel (AC43–AC50)

| AC | Criterio |
|---|---|
| AC43 | El archivo pasa por staging (nunca a tablas operacionales). |
| AC44 | Excel **jamás** escribe directamente tabla operacional. |
| AC45 | `template_version` se valida (versión no soportada ⇒ error). |
| AC46 | Errores por fila/columna/campo con `error_code` y `received_value`. |
| AC47 | Macros no se ejecutan. |
| AC48 | Fórmulas no se ejecutan como código (valores, no fórmulas). |
| AC49 | `source_checksum_sha256` se conserva (archivo + evidencia). |
| AC50 | Reimportación del mismo archivo **no duplica** (checksum + idempotencia). |

## Maestros (AC51–AC53)

| AC | Criterio |
|---|---|
| AC51 | Master inexistente ⇒ error `MASTER_NOT_FOUND`. |
| AC52 | Master inactivo no se usa en **referencia nueva** (OD-21; aplica si el cutover crea lote). |
| AC53 | Referencia **histórica** de un lote existente a master inactivo se conserva (no se invalida por eso). |

## Opening + eventos posteriores (AC54–AC58)

| AC | Criterio |
|---|---|
| AC54 | `opening live 10.000` + `post mortality 35` ⇒ `current live 9.965`. |
| AC55 | `historical 500` + `post 35` ⇒ `lifetime 535`. |
| AC56 | `current live` nunca se calcula `10.000 − 500 − 35`. |
| AC57 | Eventos post-cutover usan el **motor operacional normal**. |
| AC58 | Lote migrado continúa como lote normal tras el corte (salida/transferencia/cierre). |

## Correcciones (AC59–AC65)

| AC | Criterio |
|---|---|
| AC59 | Opening APPLIED no puede editarse directamente. |
| AC60 | Opening APPLIED no puede eliminarse. |
| AC61 | La corrección **conserva el original**. |
| AC62 | La corrección requiere razón. |
| AC63 | La corrección registra before/after/delta. |
| AC64 | La corrección queda auditada (actor, empresa efectiva, BU, timestamp). |
| AC65 | La corrección no elimina eventos post-cutover (caso 9.900 ⇒ 9.865 sin borrar la mortalidad 35). |

## SAP (AC66–AC69)

| AC | Criterio |
|---|---|
| AC66 | El opening no genera documentos SAP ficticios. |
| AC67 | `source_system=SAP` exige referencia SAP **real** si existe; no se fabrica. |
| AC68 | El opening operacional no se declara inventario/stock SAP oficial. |
| AC69 | No se implementa SAP en esta capacidad. |

## Auditoría (AC70–AC75)

| AC | Criterio |
|---|---|
| AC70 | CREATE_BATCH auditado. |
| AC71 | VALIDATE auditado. |
| AC72 | SUBMIT auditado. |
| AC73 | APPROVE/REJECT auditados. |
| AC74 | APPLY auditado (y FAILED_APPLY). |
| AC75 | CORRECT auditado. |

## Reporting (AC76–AC79)

| AC | Criterio |
|---|---|
| AC76 | Reportes distinguen Opening/Post/Lifetime. |
| AC77 | UNKNOWN visible (nunca presentado como 0). |
| AC78 | Reconciliation report reproducible (mismas entradas ⇒ mismo resultado). |
| AC79 | Reconciliation incluye source/checksum/cutover date. |

## UI (AC80–AC85)

| AC | Criterio |
|---|---|
| AC80 | Preview antes de Apply. |
| AC81 | No hay Apply con errores pendientes. |
| AC82 | Status del batch visible en el flujo. |
| AC83 | Responsive (web/mobile del patrón existente). |
| AC84 | ES/EN (i18n por claves). |
| AC85 | Sin hardcodes fuera del sistema i18n. |

## Cobertura

**85 AC** · Gobernanza 5 · Fechas 4 · Semántica 5 · UNKNOWN 4 · Lotes 5 · Batch 7 · Tenancy 4 · BU 4 · RBAC 4 · Excel 8 · Maestros 3 · Opening/eventos 5 · Correcciones 7 · SAP 4 · Auditoría 6 · Reporting 4 · UI 6.

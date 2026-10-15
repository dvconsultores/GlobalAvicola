# CUTOVER-INITIAL-BALANCES · 02_CURRENT_GAP_ANALYSIS

Fecha: 2026-10-15 · SPEC 006 · Brecha entre la capacidad certificada (GA-REQ-061, contrato v1) y lo que exige un go-live real por BU

---

## 1 · Capacidad actual (HEAD `57a421a`)

| Área | Estado | Observación |
|---|---|---|
| Ciclo DRAFT→VALIDATING→VALIDATED→PENDING_APPROVAL→APPROVED→APPLIED/REJECTED | OK | segregación creador≠aprobador, auditoría, rollback total |
| Staging (`cutover_staging_rows`, `cutover_items`) | OK | el archivo nunca toca tablas operacionales |
| Idempotencia por checksum | OK | re-upload no duplica; mismo archivo en otro batch del mismo corte ⇒ 409 |
| Plantilla | **1 genérica v1** | 8 columnas, sin catálogos, sin instrucciones por campo |
| Formatos | solo XLSX | CSV rechazado con mensaje técnico |
| Semántica VACÍO/0/N/A | parcial | el parser documenta la regla pero `N/A` y vacío colapsan a `None`; `N/A` en requeridos se acepta |
| Validación de maestros | solo `farm_code` | sin galpón, incubadora, nacedora, área, línea, raza, fase |
| Consistencia | ninguna | sin invariantes entre métricas |
| Apply | parcial | fase = primera activa (CRIA), sin `LotPhase`, sin ubicación/genética, sin opening de incubadora, sin mixto para engorde |
| Reconciliación | parcial | solo aves; `post` = `event_date > corte`; sin huevos/pollitos |
| Guarda de fecha de corte (CUT-GL-02) | ausente | — |
| Saldos del motor | aves OK (R-67) · huevos/pollitos **no** leen el opening | lote de incubadora migrado inoperable |
| Frontend | pantalla única | sin listado/detalle, sin descarga de errores, sin mensajes visibles, `accept=".xlsx"`, selector≠batch |
| E2E | API-only, 4 BU con la misma fila | continuidad (primera operación) solo en `broiler` |

## 2 · Brecha por requisito del mandato

| Requisito (mandato §) | Estado actual | Cierre en SPEC 006 |
|---|---|---|
| §9 contrato por BU | no | `contracts.py` con 4 contratos v2 (FR-01) |
| §10 XLSX + CSV mismo DTO | no | parser dual + paridad (FR-02) |
| §11 versionado v2, v1 no reinterpretada | v1 única | `V1_STATUS = RETIRED_WITH_CLEAR_ERROR` (FR-03) |
| §12 VACÍO/0/N/A por métrica | parcial | `{value,status}` por métrica; `N/A` en requerido ⇒ `REQUIRED_FIELD_MISSING` (FR-04) |
| §13 lineage `UNMAPPED_TEMPLATE_FIELDS = 0` | no existe | generado desde el registry (FR-05, doc 07) |
| §14 catálogos por empresa/BU en el XLSX | no | hoja `Catalogos` (FR-06) |
| §15–17 validaciones estructurales/dominio/consistencia | mínimas | `validation.py` (FR-07…FR-09) |
| §18 staging + preview por BU | staging sí; preview genérica | `GET …/preview` por BU (FR-10) |
| §19 informe de errores descargable | no | `GET …/errors?format=csv|xlsx` (FR-11) |
| §20 apply atómico con destino por campo | parcial | builders por BU + matriz de destino (FR-12) |
| §21 lotes migrados trazables | parcial (`origin`, `legacy_lot_code`) | + `source_system/source_reference/cutover_datetime`, `LotPhase`, ubicación (FR-12) |
| §22 OpeningBalance extendido | parcial | columnas nuevas + estados (FR-13) |
| §23 apertura de incubadora | no | `hatchery_openings` (FR-14) |
| §24 CUT-GL-02 | no | en `validate_event_date` (FR-15) |
| §25 reconciliación con UNKNOWN propagado | parcial | por BU, incl. huevos/pollitos (FR-16) |
| §26 primera operación post-corte por BU | solo broiler | E2E UI × 4 + pruebas de continuidad (FR-17) |
| §27–§35 UX, responsive, i18n | parcial | wizard por BU (FR-10/11) |

## 3 · Fuera de alcance (declarado)

- Inventarios de alimento, vacunas, medicamentos y huevo comercial como saldos de apertura: **GL-OD-07 OUT_OF_SCOPE** (no existe modelo de inventario en el sistema; crearlo excede la remediación de aperturas de lotes).
- Cambios en RBAC, OD-16 (habilitación/concesión de BU) y multiempresa: se reutilizan tal cual.
- SPEC 005 (SAP HANA inbound): intacta; `READY_FOR_SAP_CREDENTIALS` no se reabre.
- Borrado o reescritura de la certificación GA-REQ-061: se conserva; esta SPEC es `POST_CERTIFICATION_CUTOVER_INITIAL_LOAD_REMEDIATION`.

## 4 · Riesgos de la brecha si no se remedia

| Riesgo | Consecuencia en go-live |
|---|---|
| Plantilla única | el negocio no puede cargar incubadora ni engorde con sus datos reales |
| `0` fabricado desde N/A | KPIs de mortalidad/consumo falsos desde el día uno |
| Sin CUT-GL-02 | doble conteo del histórico al registrar eventos «viejos» tras el corte |
| Saldos sin opening para huevos/pollitos | la primera carga de incubación o despacho de pollitos es rechazada por `BR-03/BR-04` |
| Sin listado de batches | pérdida aparente de trabajo; cargas duplicadas |

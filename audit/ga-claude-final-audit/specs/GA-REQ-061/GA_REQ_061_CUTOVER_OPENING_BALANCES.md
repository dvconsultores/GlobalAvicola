# GA-REQ-061 · CUTOVER OPERACIONAL Y SALDOS INICIALES DE LOTES EN PROCESO

**Nombre técnico**: «Operational Cutover & Opening Balance for In-Progress Lots»
Fecha: 2026-09-14 · Estado: **SPEC_READY** · `CUTOVER_IMPLEMENTATION_STATUS = NOT_STARTED`
HEAD de referencia: `7a158d5` · Clasificación: Functional · Cross-BU · Pre-Go-Live · Pre-SAP · Data Integrity Critical · Audit Critical
Tranche propuesta: **T14** (ver `GA_CUTOVER_ROADMAP_PLACEMENT_DECISION.md`)

> `CURRENT` = lo que existe hoy en el repo. `PROPOSED` = lo que esta Spec requerirá.
> Esta fase es **solo ingeniería documental**: `PRODUCT_DIFF = 0`.

## 1 · Problema de negocio

Global Avícola se implanta sobre operación real ya en curso: lotes/procesos comenzados antes del Go-Live con aves vivas, mortalidad/descarte acumulado, alimento, pesos, producción, huevos, incubaciones y transferencias previos. Reconstruir historia ficticia está prohibido; la plataforma debe fijar un **estado operacional inicial certificado a una fecha de corte** y continuar desde allí.

```
ESTADO ACTUAL = ESTADO AL CUTOVER + OPERACIONES POST-CUTOVER (motor normal)
```

BU cubiertas: grandparent (Progenitoras), breeder (Reproductoras), hatchery (Incubadora), broiler (Engorde).

## 2 · Principio canónico — NO reconstruir historia

Separación explícita: **(A)** historia pre-cutover conocida · **(B)** estado al cutover · **(C)** operaciones registradas en Global Avícola post-cutover. Prohibido fabricar recepciones, mortalidades, consumos, transferencias, pesajes, posturas, nacimientos o documentos SAP para “cuadrar” acumulados.

### Regla crítica saldo vs acumulado (obligatoria, se convierte en RED)

| Dato | Valor |
|---|---|
| Corte | 01/10/2026 |
| Aves vivas al corte | 10.000 |
| Mortalidad histórica | 500 |
| Mortalidad GA 02/10 | 35 |

- `current_live = 10.000 − 35 = 9.965` · `post_cutover_mortality = 35` · `lifetime_mortality = 535`.
- **Prohibido** `10.000 − 500 − 35`: las 10.000 **ya son** el saldo vivo al corte (PRECEDENTE VIGENTE: `audit/remediation/R-67-OPENING-BALANCE-CERTIFICATION.md §3 RC-08`, resuelto por evidencia nivel 3 — ver `GA_CUTOVER_R67_RECONCILIATION.md`).

## 3 · Conceptos de dominio (definiciones formales)

| Concepto | Definición | Implementación propuesta |
|---|---|---|
| `REAL_START_DATE` | Fecha real de inicio del lote/proceso (puede ser anterior al corte). No se reemplaza por la fecha de migración. | `Lot.start_date` (existente) + item |
| `CUTOVER_DATETIME` | Momento desde el cual GA registra operaciones. Inmutable tras APPLY (salvo corrección formal). | `CutoverBatch.cutover_datetime` (PROPOSED) |
| `OPENING OPERATIONAL STATE` | Estado real del lote al corte (saldo vivo + fase/etapa + última posición conocida). | `OpeningBalance` extendido (ver reconciliación R-67) |
| `PRE-CUTOVER CUMULATIVE` | Acumulados históricos conocidos (mortalidad, descarte, alimento, huevos, nacimientos, transferencias). | Columnas del snapshot con semántica KNOWN/UNKNOWN |
| `POST-CUTOVER CUMULATIVE` | Derivado exclusivamente de eventos con fecha > `cutover_datetime` en el motor operacional. | Cálculo en reportes (PROPOSED) |
| `LIFETIME` | `opening + post` cuando ambos conocidos; si el opening es UNKNOWN ⇒ `LIFETIME = UNKNOWN` (post sigue calculable). | Derivación (PROPOSED) |

## 4 · Semántica 0 / NULL / UNKNOWN / NOT_APPLICABLE (crítica)

- `0` = el dato se conoce y vale cero.
- `NULL/UNKNOWN` = el dato histórico no está disponible.
- `NOT_APPLICABLE` = la métrica no corresponde a la BU/etapa.
- **Nunca** `UNKNOWN → 0`.

`CURRENT`: `OpeningBalance` usa `default=0` en mortalidad/descarte (no puede expresar UNKNOWN) y columnas opcionales en alimento/huevos (`backend/app/lots/models.py:37-80`).
`PROPOSED`: par `valor + data_status` (KNOWN/UNKNOWN/NOT_APPLICABLE) por métrica; las columnas usadas por reglas/constraints/reporting quedan **tipadas** (no JSONB indiscriminado).

## 5 · Lotes NATIVE vs MIGRATED

- `NATIVE`: creado y operado íntegramente en GA.
- `MIGRATED`: existía antes del cutover.
- `PROPOSED` metadata: `origin` (NATIVE|MIGRATED), `cutover_batch_id`/`opening_snapshot_id`, `source_system`, `source_reference`, `legacy_lot_code`.
- **Mismo motor operacional post-cutover** para ambos (no crear segundo sistema). `CURRENT`: `Lot.activation_type` (default `"normal"`) y `OpeningBalance.is_manual_activation` existen como precursores; identidad: `Lot.lot_code` UNIQUE (`backend/app/masters/models.py:294`); `legacy_lot_code` **no** reemplaza el PK.
- Política de códigos: **no** se sobrescriben secuencias existentes (incl. autogeneración L-GP de R-153); para migrados, `legacy_lot_code` + generación canónica si el lote se crea en el cutover.

## 6 · Alcance del requisito (resumen; detalle por BU en ACs y E2E)

1. **Cutover Batch** por empresa+BU con lifecycle `DRAFT→VALIDATING→VALIDATED→PENDING_APPROVAL→APPROVED→APPLIED` (+`REJECTED`, evaluar `CANCELLED`; APPLIED terminal).
2. **Excel oficial** con plantilla versionada, staging obligatorio, preview, aprobación y apply atómico.
3. **Snapshots por lote/proceso** con campos por BU (Progenitoras/Reproductoras/Incubadora/Engorde; la incubadora se modela según dominio real de cargas/incubación).
4. **Atomicidad** (todo-o-nada), **idempotencia** (aplicación + BD; checksum), **concurrencia** (un solo APPLY), **tenancy** y **BU** fail-closed (OD-16 absoluto), RBAC con segregación.
5. **Inmutabilidad post-APPLY** + correcciones auditadas (`before/after/delta/reason`) sin borrar eventos posteriores.
6. **Reporting** Opening/Post/Lifetime con UNKNOWN visible; KPIs derivados (viabilidad, mortalidad%, ADG, FCR, IPE OD-22) nunca fabricados.
7. **Reconciliación** por batch y agregada Go-Live por empresa/BU (sin sumar métricas incompatibles).

## 7 · Fuera de alcance

- SAP: ningún documento/stock/material ficticio; `source=SAP` solo con referencia real; opening operacional ≠ inventario SAP oficial.
- Implementación (modelos, tablas, endpoints, Excel, staging, UI): **tranche de implementación posterior** (T14).
- Tolerancias de cuadre no aprobadas por negocio (si se necesitan ⇒ `OWNER_GATE_REAL`).

## 8 · Documentos del paquete

| # | Documento |
|---|---|
| 1 | este SPEC |
| 2 | `GA_CUTOVER_EXISTING_CAPABILITY_GAP_ANALYSIS.md` |
| 3 | `GA_CUTOVER_R67_RECONCILIATION.md` (veredicto **PARTIAL_REUSE**) |
| 4 | `GA_CUTOVER_ACCEPTANCE_CRITERIA_MATRIX.md` (AC01…AC85) |
| 5 | `GA_CUTOVER_ARCHITECTURE_AND_DATA_MODEL.md` |
| 6 | `GA_CUTOVER_EXCEL_STAGING_DESIGN.md` |
| 7 | `GA_CUTOVER_SECURITY_MATRIX.md` |
| 8 | `GA_CUTOVER_RED_TEST_PLAN.md` |
| 9 | `GA_CUTOVER_SENSITIVITY_PLAN.md` |
| 10 | `GA_CUTOVER_E2E_PLAN.md` |
| 11 | `GA_CUTOVER_ROADMAP_PLACEMENT_DECISION.md` |

## 9 · Dependencias y estado

- Capacidades base ya certificadas: tenancy/BU (T2), integridad/auditoría (T8), maestros/usuarios (T9 `7a158d5`).
- **`T10_BLOCKED_BY_CUTOVER = NO`** (análisis en doc 11): T10 (R-197/R-207) no tiene dependencia técnica con cutover.

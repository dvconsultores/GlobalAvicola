# GA-REQ-061 · ARQUITECTURA Y MODELO DE DATOS (PROPOSED)

`CURRENT` = existe; `PROPOSED` = a diseñar en T14 (nada de esto se implementa en esta fase). Sigue los patrones del repo: FastAPI + SQLAlchemy 2 async + Alembic; routers `app/<dominio>/router.py`; servicio por dominio; tenancy `app/tenancy.py`; auditoría `audit_accion`; aprobaciones patrón review/approvals; correcciones `app/corrections`.

## 1 · Entidades

### 1.1 `CutoverBatch` (PROPOSED, tabla nueva)

| Campo | Tipo | Notas |
|---|---|---|
| id | PK | |
| company_id | FK companies | obligatorio; tenancy |
| business_unit | enum BU | grandparent/breeder/hatchery/broiler |
| cutover_datetime | timestamptz | inmutable tras APPLY |
| source_type / source_system | texto | LEGACY/MANUAL/EXCEL/SAP (adaptar a enums existentes) |
| source_reference / source_filename | texto | |
| source_checksum_sha256 | char(64) | idempotencia |
| template_version | texto | validada |
| status | enum | DRAFT/VALIDATING/VALIDATED/PENDING_APPROVAL/APPROVED/APPLIED/REJECTED (+CANCELLED eval) |
| total_rows / valid_rows / invalid_rows | int | conteo staging |
| created_by/at · validated_by/at · submitted_by/at · approved_by/at · applied_by/at · rejected_by/at | | trazabilidad completa |
| rejection_reason · observations | texto | |

**Constraints PROPOSED**: UNIQUE `(company_id, business_unit, source_checksum_sha256, cutover_datetime)`; índice `(company_id, status)`; CHECK de máquina de estados.

### 1.2 `CutoverItem` (PROPOSED)

| Campo | Tipo | Notas |
|---|---|---|
| id · batch_id(FK) · company_id | | |
| business_unit | enum | coherente con batch |
| lot_id | FK lots **nullable** | lote existente O creado en apply |
| legacy_lot_reference | texto | identidad externa |
| real_start_date / cutover_datetime | fecha/timestamptz | AC06-08 |
| opening_state | **columnas tipadas** por BU + JSON complementario solo descriptivo | regla del mandato §18 |
| source_row_number | int | trazabilidad Excel |
| validation_status / validation_errors | enum/JSON de errores estructurados | |
| created_at / applied_at | | |

**Constraints PROPOSED**: UNIQUE `(batch_id, source_row_number)`; UNIQUE parcial de identidad de lote por batch; verificación company en FK lógicas.

### 1.3 `OpeningOperationalSnapshot` — **extensión de `OpeningBalance` (PARTIAL_REUSE R-67)**

- Se extiende la tabla existente `opening_balances` (`app/lots/models.py:37`) — NO se crea concepto paralelo:
  - `cutover_item_id` (FK nullable, para openings de batch; null ⇒ activación manual clásica R-67),
  - `cutover_datetime` (timestamptz),
  - `data_status` por métrica (KNOWN/UNKNOWN/NOT_APPLICABLE; p.ej. `feed_status`, `mortality_status`…),
  - provenance (`source_system`, `source_reference`, `legacy_lot_code`),
  - campos de incubación en curso (propuesta; auditoría fina previa — ver §4).
- Semántica AC10-14 y RC-08 se **conservan**: `initial_*` = saldo vivo al corte; acumulados = historia.
- `unique lot_id` actual se mantiene (un opening vigente por lote); correcciones viven en su propia tabla.

### 1.4 `OpeningBalanceCorrection` (PROPOSED)

`id · opening_id(FK) · field · old_value · new_value · delta · reason (obligatorio) · requested_by · approved_by · created_at · applied_at` + auditoría (AC59-65). Requiere permiso de correcciones; NO borra eventos post-cutover; el original permanece visible.

### 1.5 `CutoverStagingRow` (PROPOSED) — ver diseño Excel/staging (doc 6).

### 1.6 Lote — metadata MIGRATED

`PROPOSED` (evaluar columnas en `lots` vs tabla satélite al implementar): `origin` (NATIVE|MIGRATED, default NATIVE), `legacy_lot_code` (unique conjunto con company), `source_system/source_reference`. `Lot.lot_code` sigue siendo el código canónico único (`masters/models.py:294`); **no** se alteran secuencias ni la autogeneración R-153.

## 2 · Flujo funcional del batch

```
DRAFT (crear: company/BU/cutover/source)
→ upload (archivo + sha256) → VALIDATING
→ validate (+ staging) → VALIDATED | con errores (queda en VALIDATING/borrador)
→ submit (creator≠approver) → PENDING_APPROVAL
→ approve | reject → APPROVED | REJECTED
→ apply → (revalidación + transacción única) → APPLIED [terminal] | FAILED_APPLY (rollback)
```

## 3 · Atomicidad, idempotencia, concurrencia

- **Apply** = una transacción: revalidar (estado, tenancy, BU ON, grants, masters, identidad, checksum), `SELECT ... FOR UPDATE` del batch, verificar idempotencia, crear/reusar lotes migrados permitidos, crear snapshots, escribir auditoría, marcar APPLIED; cualquier fallo ⇒ ROLLBACK total (AC27/28). Resultado con conteos 42/38/4/0.
- **Idempotencia doble**: aplicación (estado + checksum) + BD (constraint único §1.1; único de opening por lote).
- **Concurrencia**: lock del batch + transición de estado atómica ⇒ segundo apply ⇒ 409 determinista (AC30).

## 4 · Incubadora — nota de diseño

El dominio real usa cargas/batches/incubación (`EggBatch`/`ChickBatch`/`HatcheryParams`; `app/operations/models.py:197-248`), no solo `Lot`. PROPOSED: el item de cutover para hatchery referencia el **proceso en curso** (lote incubadora + carga activa) y su opening captura: huevos recibidos/cargados/en proceso, fecha-hora de carga, equipo, etapa/días de incubación, fertilidad si conocida, transferidos, nacimientos, descartes, etapa actual, fecha prevista de nacimiento, referencia del lote origen. **Auditoría fina obligatoria al inicio de T14** antes de fijar columnas.

## 5 · Corrección con operaciones posteriores (AC65)

`opening 10.000 → post 35 → corrección opening=9.900 ⇒ current=9.865`. Nunca se borra el evento 35; se recalcula por fórmula suma/resta con componentes etiquetados (opening corregido + post).

## 6 · API (PROPOSED, adaptar a convenciones al implementar)

`POST/GET /cutover-batches`, `GET /cutover-batches/{id}`, `POST …/{id}/upload`, `POST …/{id}/validate`, `GET …/{id}/validation`, `POST …/{id}/submit|approve|reject|apply`, `GET …/{id}/items`, `GET …/{id}/reconciliation`, `POST /opening-balances/{id}/corrections`, `GET /cutover-templates/{bu}` (descarga plantilla). Bajo `/api/v1`, con permisos del módulo cutover.

## 7 · Frontend (PROPOSED, fase FE del paquete)

Flujo UX: Cargas Iniciales → Nuevo batch (empresa/BU/corte) → descargar plantilla → subir → validar → errores (fila/campo) → preview → enviar → aprobar/rechazar → apply → reconciliación → historial/correcciones. UNKNOWN vs 0 con representación visual distinta (AC15, AC77); i18n ES/EN.

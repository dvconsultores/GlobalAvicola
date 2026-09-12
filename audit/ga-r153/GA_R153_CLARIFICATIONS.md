# GA-R153 · CLARIFICACIONES (C01–C25)

Fecha: 2026-09-12. Todas resueltas con evidencia de repositorio (§ trazas del hogar `audit/ga-r153/`).

| # | Cuestión | Resolución | Evidencia |
|---|---|---|---|
| C01 | Entidad de importación | `operational_events` (`event_type=grandparent_import`) + `bird_movements` | `operations/models.py:79,180` |
| C02 | Entidad del plan | `extra_data.import_plan` (JSONB; `PlanDeImportacion`) | `operations/schemas.py:26-47` |
| C03 | Endpoint/servicio de aprobación | `POST /approvals/approve` → `ApprovalService.approve`; y `complete_review` (nivel único) | `review/service.py:485,320` |
| C04 | Transición P-07 | `CORRECTED/IN_REVIEW → APPROVED` (+`approved_by_id`) | `review/service.py:602-618` |
| C05 | ¿Lote exigido hoy en el alta? | **SÍ** (backend 400; frontend `superRefine`) | `operations/service.py:805-809`; `OperationFormPage:166-175` |
| C06 | Nullability/enlace | `event.lot_id` **nullable**; `lots.lot_code` NOT NULL único **global**; demás nullables | migraciones `7922512fdef4`, `b53bbe02a476` |
| C07 | Campos obligatorios del lote | solo `lot_code` (+defaults `status/activation_type`) | `masters/models.py:278-315` |
| C08 | Fuente del código | **generado** (no existía generador) | `GA_R153_SEQUENCE_ANALYSIS.md` |
| C09 | Año del código | `arrival_date.year` del plan | OD-25; §20 del encargo |
| C10 | Alcance de secuencia | por **empresa**; año por fecha de llegada; unicidad global salvaguardada (reintento) | análisis de secuencia §2-3 |
| C11 | Concurrencia | `pg_advisory_xact_lock` por (empresa,año) + savepoint/reintento global | íd. §3 |
| C12 | Sexo | `bird_movements` (♂/♀ > 0 ⇒ `mixed`; uno ⇒ ese; ninguno ⇒ NULL) | `SexEnum`; `BirdMovement` |
| C13 | Fecha | `import_plan.arrival_date` (→ `start_date` 00:00) | OD-25 |
| C14 | Línea genética | **no derivable** ⇒ NULL (nullable; sin invento) | mapeo §4 |
| C15 | Granja/Área | `event.farm_id/house_id` si existen; `area_id` NULL | mapeo §4 |
| C16 | Efecto en población | **0** (documental; AC-R152-08) | `validators.py:631-633` |
| C17 | Objetivo de recepción | lote nuevo (`bird_reception`; BR-17/18) | trazas §4 |
| C18 | Vía manual | intacta; ya no prerequisito de la importación nueva | AC33/34 |
| C19 | Legado con lote preasignado | sin segundo lote (no-op por `lot_id`) | análisis de secuencia §5 |
| C20 | Doble aprobación | 2.º approve → 400; hook no-op si `lot_id` fijado | `review/service.py:602-618` |
| C21 | Devuelto/rechazado | sin lote (solo aprobación final crea) | estados P-07 |
| C22 | Auditoría | `audit_state_transition` + `audit_accion CREATED(lot)` con origen | helpers audit |
| C23 | Impacto formulario | lote **opcional** para `grandparent_import` + nota i18n | §impacto frontend |
| C24 | Comportamiento post-aprobación | detalle: enlace `/lots/{id}`; pendiente si null | §impacto frontend |
| C25 | Criterios UAT | 7 casos (crear sin lote · sin lote antes · aparece al aprobar · datos · sin aves · recepción · manual) | `GA_R153_OWNER_UAT.md` |
| C26 | Visibilidad del evento sin lote | **deriva del tipo** (`grandparent`, inequívoco por `BR-22`): visible a la cadena, fuera de la bandeja fase-6, cerrado a otras cadenas. Prerequisito sin el cual la aprobación era inalcanzable (hallado en runtime, C2b) | `classification.py` · AC58/59 · OBS-4 |

**Críticas resueltas (C05…C11): sin bloqueos; sin conflicto de esquema (migración 0).**

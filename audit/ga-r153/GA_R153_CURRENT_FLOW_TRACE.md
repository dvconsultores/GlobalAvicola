# GA-R153 · TRAZA DEL FLUJO ACTUAL (pre-implementación)

Fecha: 2026-09-12 · Baseline `9ad9b26` · Runtime `index-DtzHNDMG.js`.

## 1 · Importación de abuelas — contrato actual

- Entidad: **`operational_events`** (`event_type = grandparent_import`) + hijos `bird_movements` (sexo/cantidad; ♂ y ♀ con `avg_weight`) + plan en **`extra_data.import_plan`** (`PlanDeImportacion`, `operations/schemas.py:26-47`; validado por `validate_import_plan`, `validators.py:624-676`).
- **El lote es OBLIGATORIO** y el gate corre primero (`operations/service.py:805-809`):
  ```python
  lot_required = event_type not in LOT_OPTIONAL_EVENTS   # solo farm/hatchery_inspection
  if lot_required and data.lot_id is None:
      raise HTTPException(400, "El evento requiere lote")
  ```
  Además: `validate_lot_active` + `validate_event_date` + `exigir_unidad_operativa(lot_id=...)` (unidad = `lot.bird_type`) y BR-22 sobre la cadena del lote («solo sobre un lote de Progenitoras»).
- **Frontend (3 bloqueos):** `superRefine` exige `lot_id` para todo evento no-inspección (`OperationFormPage.tsx:166-175`); selector renderizado y con error `operations.selectLot` (l.2017-2031); `lot_id` siempre viaja en el payload (l.397-410).
- **Hallazgo RED runtime (pre-fix, hoy):** `POST /operations {grandparent_import, sin lote}` → **400 «El evento requiere lote»** (`evidence/red-runtime.json`).

## 2 · Ciclo de aprobación (P-07)

```
REGISTERED --submit--> PENDING_REVIEW --start--> IN_REVIEW --complete(≥2 niveles)--> CORRECTED --approve--> APPROVED
IN_REVIEW --complete(1 nivel)--> APPROVED (auto, con segregación)
```
- `ApprovalService.approve` — `review/service.py:485-519`: fija `APPROVED` + `approved_by_id`, ejecuta el **hook de reverso** (`efectuar_reverso_si_procede`) en la MISMA transacción, inserta `approval_actions` y audita (`audit_state_transition`).
- `complete_review` nivel único — `review/service.py:320-357`: misma transición + hook de reverso. ⇒ **todo hook de consecuencia debe colocarse en AMBOS puntos** (patrón probado del reverso).
- Idempotencia: segundo `approve` → 400 «no está en estado aprobable»; concurrencia del mismo evento serializada por `SELECT … FOR UPDATE` (R-166).
- Transacción: `RutaTransaccional` (commit único por request) — aprobación + consecuencia + auditoría = una sola transacción.

## 3 · Lote (modelo y alta)

- `Lot` (`masters/models.py:278-315`): **`lot_code` NOT NULL y único GLOBAL** (`ix_lots_lot_code`); resto nullable (`company_id`, `farm_id`, `house_id`, `genetic_line_id`, `breed_id`, `weight_curve_id`, `area_id`, `bird_type`, `sex`, `start_date`, `planned_close_date`…); `status` default `active`; `activation_type` default `normal`.
- **No existe generador de códigos** en el backend (códigos manuales: `L-BO-2026-05`, `L-2026-001`, `L-R187-DET`…). El alta manual (`lots/service.py:163-263`) exige `lot_code` del usuario, resuelve curva por línea genética y valida granja/área/unidad.
- Alta manual NO puebla; **la población es derivada** (`get_current_bird_balance`, `validators.py:49-90`): saldo = apertura + entradas (recepción/nacimiento) − salidas. `grandparent_import` no puebla (AC-R152-08).

## 4 · Recepción (P-01 paso 4)

`bird_reception` valida BR-17 (capacidad de galpón) y BR-18 (límite acumulado de la OC) y es el evento de entrada de población (`validators.py:712-797`). Objetivo del lote recién creado (`lot_id`).

## 5 · Huecos exactos a cerrar (R-153)

1. Gate de lote: la importación **nueva** nace sin lote (legado con lote se preserva).
2. Consecuencia de aprobación: crear 1 lote (código/secuencia/fecha/sexo/empresa/dominio) + enlazar `event.lot_id`, en la transacción de la aprobación, en ambas rutas.
3. Frontend: dejar de **forzar** el lote para `grandparent_import` + señalizar el resultado (enlace al lote; estado pendiente pre-aprobación).

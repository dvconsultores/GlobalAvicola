# GA-FE-06 · MATRIZ CONTRATO DE EDICIÓN DE LOTE (R-182)

## Decisión de alcance: **OUT_OF_SCOPE (UI)** — documentado, sin expansión

| Elemento | Verdad canónica |
|---|---|
| Backend update | `PUT /lots/{id}` con `LotUpdate` (`extra=forbid`) que **incluye** `area_id` y `planned_close_date` («Replanificar es legítimo…»), `start_date`, `end_date`; permiso `lots:update`; guarda operativa (`_exigir_unidad_operativa`) |
| Frontend update | **No existe pantalla de edición de lote** en el producto (no hay ruta ni formulario de edición; `LotFormPage` es solo alta). Único cambio de datos posterior: `close_lot` |
| Alcance R-182 | El hallazgo original es del **alta** (payload de creación) + activación SLA. §15/§31 del encargo: «Do not expand scope automatically». Editar PLD/área desde UI exigiría una pantalla nueva — **fuera del hallazgo** |
| Conclusión | **UI de edición: N/A** (no existe). Contrato backend de edición: **existente y correcto** (sin cambios). No se crea UI de edición en GA-FE-06 |

## Evidencia de la decisión

- `REMEDIATION_BACKLOG.md §R-182` menciona solo «alta de lote».
- `LotFormPage` se sirve en `/lots/new` (ruta WebOnly + `lots:create` — GA-FE-04). No hay `/lots/:id/edit`.
- `LotUpdate` no fue señalado por ningún AC de R-182.

## Implicación para E2E-16

`E2E-16 UPDATE` = **N/A** con esta justificación canónica (sin producto que probar; backend ya certificado por su propia suite en CI). El SLA recalcula en cada evaluación (on-demand/scheduler), por lo que una replanificación futura por API no requiere cambio alguno de esta tranche.

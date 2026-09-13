# R-193 · CLARIFICACIONES

Fecha: 2026-09-13 · Resueltas por defecto salvo indicación; ninguna requiere decisión del propietario (la semántica ya está decidida en `OD-19` y `OD-04`).

| # | Pregunta | Supuesto por defecto | Fuente | Estado |
|---|---|---|---|---|
| C-01 | ¿Forma de la corrección: excluir `{CANCELLED, REVERSED}` + contrapartidas, o aplicar `_suma_neta` por documento? | **Exclusión** (`status.not_in([CANCELLED, REVERSED])` y `id.not_in(Reversal.reversal_event_id)`): resultado idéntico al neto (ambos miembros del par en `REVERSED` con las mismas cantidades) y sin generalizar `_suma_neta` (que es por `lot_id`). La exclusión explícita de contrapartidas protege el caso «contrapartida en cualquier estado no efectivo» sin depender del estado. | `validators.py:21-46`, `reversals/service.py:140-145, 215-216` | resuelta |
| C-02 | ¿Un original `APPROVED` con contrapartida pendiente sigue contando contra la OC? | **Sí**: la recepción ocurrió y sigue vigente hasta que el reverso sea efectivo (`OD-19 §2`: rechazo ⇒ original sigue `APPROVED`). | `OD-19 §2, §6` | resuelta |
| C-03 | ¿Se corrige también la invocación para `BIRD_DISTRIBUTION` (`service.py:898-906`)? | **No** (fuera de alcance; OBS-R193-01 al backlog). Cambiar la lista de tipos es una decisión de regla distinta a la neta de reversos. | `service.py:898-906` | resuelta |
| C-04 | ¿Bloqueo de la OC (`FOR UPDATE` sobre `SapReference`) para recepciones concurrentes? | **No** en este paquete (carrera preexistente, OBS-R193-02). Si el propietario lo pide, misma primitiva que `bloquear_saldo_del_lote`. | `validators.py:197-208` | resuelta |
| C-05 | ¿Dónde viven los tests nuevos? | Fichero nuevo `backend/tests/test_r193_oc_limit_after_reversal.py` (fixture propia con `SapReference` + reverso), para no alterar la matriz `t_014_*` certificada. | `test_purchase_order_receipt.py` | resuelta |
| C-06 | ¿Requiere UAT del propietario? | **No** (regla de backend sin superficie). Se documenta en la certificación técnica. | encargo §46 (UAT «si visible/material») | resuelta |
| C-07 | ¿Cómo se obtiene un par `REVERSED` en tests? | Ruta real: `POST /reversals` (Super Admin de pruebas) + aprobación por `cabecera_de_rol('approver')` (BR-14), como `test_internal_reversal.py:226-253`. | `test_internal_reversal.py` | resuelta |
| C-08 | ¿Se toca el docstring de BR-18? | Sí: el párrafo «los ocho saldos excluyen exactamente `CANCELLED`» queda obsoleto desde `OD-19`; se cita `_suma_neta`. | `validators.py:744-748` | resuelta |

Sin clarificaciones críticas abiertas ⇒ implementación habilitada tras C1.

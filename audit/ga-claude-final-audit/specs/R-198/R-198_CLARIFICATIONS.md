# R-198 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿El detalle devuelve evidencias o la UI re-lee la ruta dedicada? | **A (propuesto)**: arreglar el detalle (`router.py:277-292`) para incluir `evidences` (el esquema ya lo declara) **y** que la UI recargue del servidor tras mutaciones; la ruta dedicada se mantiene. Alternativa B: UI usa solo `GET /operations/{id}/evidences`. | `router.py:277-292,334-341`; `schemas.py:298-305` | técnica (elegir A o B en C1) |
| C-02 | Estados en los que se permite adjuntar/borrar | Editables: `draft, registered, pending_review, in_review, returned, rejected, corrected`; **no** en `approved/consolidated/sent_to_sap/sap_confirmed/sap_error/cancelled/reversed`. Si dominio decide «nunca borrar tras salir de editable», se anota. | `EDITABLES`/`NO_CANCELABLES` (`service.py:73-78`) | técnica (dominio informado) |
| C-03 | Borrado físico vs lógico | Físico **tras** commit (fila de auditoría conserva el rastro); lógico si el propietario quiere recuperación (evaluar coste). | `service.py:1409-1414` | técnica |
| C-04 | ¿`egg_storage_records` en el detalle? | Sí, mismo arreglo (el esquema lo declara; hoy también se descarta). | `schemas.py:298-305` | técnica |
| C-05 | Auditoría: contenido | `event_id`, `evidence_id`, nombre, tipo, acción (`UPLOAD`/`DELETE`); sin binario; productor según P1-12-REOPEN T-06. | E-15 | técnica |
| C-06 | Visibilidad táctil (R3) | Corregir `opacity-0 group-hover` del bloque si se toca (visibilidad táctil); cambio mínimo. | informe F R3 | técnica |

Sin decisiones abiertas que bloqueen; C-01 se registra en C1.

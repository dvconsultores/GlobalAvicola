# R-207 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿Dónde vive la acción? | Detalle de operación (`OperationDetailPage`), visible para `approved` elegibles; opcional desde el detalle de revisión. | `reversals/service.py:33-46` (elegibles) | técnica |
| C-02 | Motivo mínimo | ≥5 (contrato existente); validación cliente + servidor. | `reversals/service.py`; OD-19 | técnica |
| C-03 | ¿Quién aprueba la contrapartida? | El motor P-07 existente (`approvals:*`); BR-14 aplica. Sin flujo nuevo. | `review/service.py:341-345` | técnica |
| C-04 | ¿Enlace original↔contrapartida en qué pantallas? | Detalle de operación y detalle de revisión (campo existente). | modelo | técnica |
| C-05 | Badge `reversed` | Añadir a `statusColors` + `domain.types` + mapas locales; verificar i18n `status.reversed`. | C-27 | técnica |
| C-06 | ¿Orden con R-192/R-193? | La UI puede construirse en paralelo; el **deploy de la UI** no debería preceder a R-192 (cierre tras reverso) — ventana documentada si se decide otra cosa. | registro §3 (orden 5/7) | técnica (coordinación) |
| C-07 | ¿Post-SAP? | Fuera (R-136 SAP_DEFERRED). | R-136 | técnica |
| C-08 | ¿Reverso de contrapartidas ya revertidas? | UI no lo ofrece (elegibilidad del servicio lo rechaza). | servicio | técnica |

Sin decisiones abiertas que bloqueen; C-06 es coordinación de orden.

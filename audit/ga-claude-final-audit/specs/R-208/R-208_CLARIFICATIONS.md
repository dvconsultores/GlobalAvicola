# R-208 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2. Ninguna decisión del propietario requerida.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿Qué permiso exacto para cada batch? | `approvals:approve` / `approvals:reject` (idéntico a las unitarias). | `review/router.py:123-140` | técnica |
| C-02 | ¿Se añade un permiso nuevo tipo `approvals:batch`? | No: reutilizar los existentes (menos superficie, misma política). | diseño general | técnica |
| C-03 | ¿Comportamiento con resultados parciales del lote? | Sin cambio (servicio actual por evento); solo cambia la puerta. | `review/service.py` | técnica |
| C-04 | ¿Los roles de revisión existentes pierden la aprobación? | Pierden solo la de lote si no tienen `approvals:*`; el flujo unitario ya exigía ese permiso — no es cambio efectivo de política. | `ApprovalPanel.tsx`; GA-REM-023 | técnica |
| C-05 | ¿La contrapartida de reverso aprobada por lote? | Misma puerta (`approvals:approve`); la elegibilidad y segregación se mantienen. | OD-19; `reversals/service.py` | técnica |
| C-06 | ¿Se tocan las rutas de `approval-steps`? | No (plano de configuración). | `review/router.py:167-173` | técnica |

Sin decisiones abiertas.

# P1-12-REOPEN · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2. C-01 es decisión técnica con recomendación.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿Qué productor queda para `OperationalEvent`/`CorrectionLog`/`ApprovalAction`? | **Híbrido determinista (recomendado)**: listener único para las 3 entidades + retirada de las llamadas helper que duplican; helpers solo donde el listener no llega (lotes/usuarios/evidencias/curvas/acciones administrativas). Alternativas: (B) solo helpers (retirar listener), (C) solo listener (pierde `audit_accion`). | `listeners.py:71-113`; `helpers.py`; evidencia H6/H8b | técnica (registrar en C1) |
| C-02 | ¿Idempotencia por (entidad, id, acción, estado) además de retirar duplicados? | Sí, como defensa en profundidad si C-01=B/C. | diseño | técnica |
| C-03 | Exportaciones cliente (Excel/PDF): ¿auditar? | Por defecto **A**: documentar `NOT_APPLICABLE_CLIENT` (no hay endpoint; GA-REM-032 AC04 se anota); alternativa B: endpoint de auditoría de exportación (fuera de alcance por defecto). | E-16 | técnica |
| C-04 | ¿Se limpian históricos duplicados? | No (inmutabilidad; R-148). Inventario de lectura opcional. | encargo §61 | técnica |
| C-05 | ¿`conftest.py` global o solo los tests afectados? | Registro del listener en el arnés de los tests de auditoría afectados; sin cambiar el global para no alterar cientos de tests en la misma tranche (evaluar en C1). | `conftest.py:117-140` | técnica |
| C-06 | ¿Se toca el SLA de 24 h? | Sin cambio de lógica; tras el fix, las filas `pending_review` existen también para batch/contrapartida (E-06) y el SLA las ve. | `sla.py:44-60` | técnica |
| C-07 | ¿Logout (GA-REM-003 AC04)? | Fuera de aquí; se anota el estado real en GA-REM-032. | registro §7 | técnica |

Decisiones abiertas: C-01 (registrar opción en C1). El resto tiene default claro.

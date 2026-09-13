# R-210 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2. C-01 es `OWNER_DECISION_REQUIRED` (mínima, confirmatoria).

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿La captura de peso es en gramos? | **Sí (gramos)**: alineado con curvas OD-06, evaluación, uniformidad CV e IPE; la etiqueta i18n ya dice «(g)». El propietario **confirma** y queda registrado. | `GA_REM_021_B02…:19,45`; `operations/service.py:744-824`; FORM_CONTRACT §5.1 | **`OWNER_DECISION_REQUIRED`** (confirmación; por defecto A=g) |
| C-02 | Si se decidiera kg, ¿cómo? | Conversión explícita ×1000 en serializador + etiqueta kg coherente + tests; nunca mezclar. | diseño | técnica |
| C-03 | ¿Se toca el rango de validez (B02)? | No: el rango ya está en g; se cita. | B02 | técnica |
| C-04 | ¿Se ajusta `inputMode` decimal? | Sí, si falta (R14 del informe F lo anota como cosmético); cambio mínimo. | informe F R14 | técnica |
| C-05 | ¿Se sanea histórico con pesos ~kg? | No en esta tranche; inventario de lectura opcional; en producción real no hay capturas (pila de pruebas). | encargo §61 | técnica |
| C-06 | ¿Detalle de operación? | Se mantiene en g (coherente); sin cambio. | `OperationDetailPage.tsx:221` | técnica |

Decisiones abiertas: **C-01** (confirmación). No bloquea la RED ni la implementación por defecto (A).

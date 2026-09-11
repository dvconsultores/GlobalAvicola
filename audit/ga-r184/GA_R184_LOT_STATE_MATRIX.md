# GA-R184 · MATRIZ DE ESTADOS DE LOTE

Estados reales: `LotStatus = {ACTIVE, CLOSED, CANCELLED}` (`app/masters/models.py`).

| Estado | ¿IPE se calcula? (código actual) | ¿Final o provisional? | Respuesta esperada | ¿Cambia en R-184? |
|---|---|---|---|---|
| `ACTIVE` | Sí (único filtro: existencia + alcance + `company_id`) | **Provisional** (edad contra hoy, crece a diario) | 200 con valores del día | No |
| `CLOSED` | Sí (no hay filtro por estado) | **Provisional con la última edad medida** (la edad sigue corriendo contra hoy; el cierre no congela la base temporal) | 200 | No |
| `CANCELLED` | Sí (no hay filtro por estado) | Provisional | 200 | No |

**Lecturas honestas (registradas, no «arregladas» en esta tranche):**

1. No existe en el repositorio ninguna regla que restrinja el IPE por estado del lote: el contrato vigente calcula para todos. R-184 **no inventa** reglas de estado (no legitima un lote cancelado).
2. La semántica «edad contra hoy» para lotes cerrados/cancelados es una **limitación preexistente del contrato** (el KPI no congela la edad al cierre). No hay spec que lo defina como final al cierre; se preserva y se registra como candidata a revisión de negocio **si el propietario la considera relevante** (no bloquea R-184).
3. `planned_close_date` **no participa** del cálculo (se usa en SLA de avisos); ningún estado lo consulta.

**Sin cambios de comportamiento por estado en R-184** (0 líneas al respecto): la única edición es la normalización temporal del término `age_days`.

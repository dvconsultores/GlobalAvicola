# GA-GOV-02 · IMPACTO EN CERTIFICACIONES

Regla: no se reabre nada sin **contradicción directa de una AC aceptada**. Los dos residuales son ortogonales a las AC aceptadas (endpoint distinto / semántica no gobernada por ninguna AC).

| Certificación | Impacto | Justificación |
|---|---|---|
| GA-FE-02 (FUNCTIONALLY_CERTIFIED_OWNER_ACCEPTED) | **PRESERVED** | Residuales en módulo `reports`; sin relación con sesiones/BU/empresa aceptadas |
| GA-FE-03 | **PRESERVED** | Navegación intacta; OBS-UAT-01 sigue siendo la única nota (ya inventariada) |
| GA-FE-04 | **PRESERVED** | ActionGate/estados sin relación |
| GA-FE-05 | **PRESERVED** | Flujo de revisión/aprobación sin relación (R-186 no toca `review/approvals`) |
| GA-FE-06 | **PRESERVED** | R-182 (contrato de lote/PLD) intacto; R-186 no toca lotes |
| GA-FE-07 | **PRESERVED** | R-185/OD-21 intactos |
| R-181 | **CLOSED (sin cambio)** | — |
| R-182 | **CLOSED_OWNER_ACCEPTED (sin cambio)** | — |
| R-184 | **CLOSED_OWNER_ACCEPTED (sin cambio)** | El residual de escala no contradice ninguna AC de R-184 (fecha/tipos/contrato IPE); la fórmula aceptada es la definida; test §38 no se cumple (no hay regla canónica preexistente incumplida) |
| R-185 | **CLOSED_OWNER_ACCEPTED (sin cambio)** | — |
| OD-21 | **RATIFIED (sin cambio)** | — |

## Nota sobre R-186 y R-182/R-184

- R-186 **no es un subhallazgo de R-184 aceptado** (endpoint distinto, expresión propia no tocada por el fix) — su vía es una tranche técnica nueva.
- La observación de escala **no convierte en incorrecta la aceptación** de R-184: el propietario aceptó la experiencia visible de la generación certificada; una eventual decisión de escala futura sería otra tranche con su propia aceptación (y sin migración de datos: nada persistido).

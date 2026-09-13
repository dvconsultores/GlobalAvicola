# R-211 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2. C-02 es `OWNER_DECISION_REQUIRED` (acotada).

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿La validación por fila sustituye a la del evento? | Sí: agrupar por `target_house_id` de filas y comparar cada grupo contra su capacidad; el `house_id` del evento no participa de la Σ. | `validators.py:712-725`; `OFP:725-772` | técnica |
| C-02 | ¿Capacidad **acumulada** por galpón entre eventos? | **OWNER_DECISION_REQUIRED** — A (propuesto): solo el evento (corrige el falso positivo; residual documentado); B: acumular eventos vigentes (requiere consulta agregada y acuerdo de concurrencia). | E-04; RR-02; `R-176` | **`OWNER_DECISION_REQUIRED`** |
| C-03 | ¿Aplica también a `bird_distribution`? | La corrección base usa las filas si el evento las tiene; distribución/traslado son neutrales en saldo (RR-02) — se aplica el mismo helper para consistencia, sin cambio de semántica. | `service.py:900-906` | técnica |
| C-04 | Mensaje del 400 | Incluir galpón y capacidad (`Galpón {name} capacidad {n}: {m}`); sin código nuevo (BR-17). | patrón | técnica |
| C-05 | ¿Lock para C-02=B? | No por defecto (residual de concurrencia documentado; el saldo de aves ya bloquea donde importa). | F.2/F.3 del informe D | técnica |
| C-06 | Fixtures/e2e actuales | Se actualizan en GA-GOV-03; esta spec habilita el patrón multi-galpón. | GA-GOV-03 | técnica |

Decisiones abiertas: **C-02** (propietario). AC-04 depende de ella; el resto no.

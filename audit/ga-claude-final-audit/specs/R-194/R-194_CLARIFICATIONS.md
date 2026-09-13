# R-194 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2. C-01/C-02 con decisión de dominio/propietario (acotadas).

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | Ubicación de la etapa incubadora (BR-08): ¿qué `farm_id`/`house_id` envía? | **A (propuesto)**: la recepción usa la granja/galpón del **lote** incubadora si existen; si no, selector de planta; **B**: BR-08 exime la etapa incubadora por decisión. | `validators.py:828-839`; `OFP:438`; F-01e | **`OWNER_DECISION_REQUIRED`** (A/B) |
| C-02 | `arrival_date`: ¿capturada o derivada? | **Capturada** (campo fecha) con default = `event_date`; alternativa: derivada siempre. | `schemas.py:85-87`; F-01b | **`OWNER_DECISION_REQUIRED`** (capturar vs derivar) |
| C-03 | `dosage_per_bird` del nacimiento: ¿obligatorio? | Opcional (como hoy en esquema); el fix garantiza número válido o ausencia limpia. Si dominio exige, se marca obligatorio en cliente (fast-follow). | `OFP:1651`; vacunación `:581` | técnica (dominio informado) |
| C-04 | Fértiles: ¿qué cantidad? | La declarada como «recibidos» (`eggs_received`), como única fila `fertile` de `egg_movements`; la clasificación posterior (`egg_reception_classification`) no altera el saldo (BR-03 lee recepción). | `validators.py:149-175` | técnica |
| C-05 | B-33 (`incubator_id` como destino en despacho) | Documentado; sin cambio (no rompe contrato). | `OFP:1093-1100` | técnica |
| C-06 | Huevos no fértiles en recepción | La recepción de incubadora registra fértiles (saldo); los no fértiles llegan por clasificación, no por recepción. | R-172/RR-17 | técnica |
| C-07 | AOD-23/AOD-24 (decisiones abiertas de nacimiento/tipos de huevo) | Se citan; el flujo actual se implementa sin reabrirlas. | registro | técnica |

Decisiones abiertas: **C-01**, **C-02**. No bloquean C1 (RED) ni el resto de ACs; sí definen dos puntos de implementación.

# GA-R186 · TRAZA DE NEGOCIO G-05 (distinta de G-06)

Cada elemento cita fuente. G-05 y G-06 **no comparten semántica** salvo la clase temporal (se documentan las diferencias).

## 1 · Definición canónica (citada)

```
G-05: Broiler production index = (avg_weight_g × viability_pct) / (age_days × FCR × 10)
```

- Fuente 1: docstring del método `get_kpi_production_index` («Broiler production index = (avg_weight_g * viability_pct) / (age_days * FCR)» — ver nota §5).
- Fuente 2: rótulo del router «G-05: Calculate Broiler Production Index for a lot».
- Implementación vigente (contrato ejecutable): `app/reports/service.py:579-617` — `pi = (avg_weight_g * viability) / (age_days * fcr * 10) if (age_days * fcr) > 0 else 0`.

## 2 · Variables de entrada (código real)

| Variable | Origen | Unidad | Diferencias con G-06 (IPE) |
|---|---|---|---|
| **Viabilidad** | `100 − mortality_rate_pct` (mismo cálculo de mortalidad: muertes aprobadas + `OpeningBalance`) | % | Igual |
| **avg_weight_g** | `AVG(BirdMovement.avg_weight)` de **todos** los eventos del lote con peso no nulo (sin filtro de tipo de evento ni estado) | gramos | **Distinto**: el IPE filtra `event_type = WEIGHT_RECORDING` |
| **age_days** | `(date.today() − día(lot.start_date)).days`; sin inicio → **30**; **sin clamp** (a diferencia del IPE, que clampa a 1) | días de calendario | **Distinto**: sin clamp; mismo fallback 30 |
| **FCR** | `feed_conversion_ratio` del KPI de conversión; si es 0/ausente → **`or 1`** (placeholder 1) | — | **Distinto**: el IPE usa `or 0.0` y guarda `fcr > 0` |
| **Población inicial** | `OpeningBalance` (0 si no hay → mortalidad 0 → viabilidad 100.0) | aves | Igual |

## 3 · Agregación y forma de respuesta

- **Un solo lote** (`lot_id` requerido por query) → **no es colección**; no hay agregación multi-lote (AC de colección no aplican, ver matriz de entradas).
- Respuesta (contrato vigente, sin cambios): `{lot_id, avg_weight_g (1d), viability_pct (1d), age_days (int), fcr (2d), production_index (1d), unit: "index"}`.

## 4 · Estados de lote y condición de cálculo

`LotStatus = {ACTIVE, CLOSED, CANCELLED}` — el endpoint no filtra por estado (contrato vigente; preservado). `planned_close_date` no participa.

## 5 · Redondeo y precisión (preservados)

| Campo | Redondeo |
|---|---|
| `avg_weight_g` | 1 |
| `viability_pct` | 1 |
| `fcr` | 2 |
| `production_index` | 1 |

## 6 · Nota de documentación (registrada, no resuelta)

El docstring omite el `×10` del divisor que el código aplica. La tranche preserva el **código** como contrato ejecutable; la posible alineación docstring↔código o una reinterpretación de escala queda para una revisión de semántica posterior (misma familia que la decisión pendiente del IPE), **fuera del alcance de R-186**.

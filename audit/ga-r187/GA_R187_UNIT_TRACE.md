# GA-R187 · TRAZA DE UNIDADES DE ENTRADA — IPE G-06 (OD-22)

Objetivo (§12-14 del encargo): **probar** qué pasa realmente el código antes de retirar el `× 100`.
Regla: no se retira el factor hasta que la escala de viabilidad quede demostrada.

## 1 · Viabilidad — porcentaje 0-100 (probado)

Cadena exacta:

1. `get_kpi_mortality` (`backend/app/reports/service.py:140-153`):
   `rate = (total_deaths / initial_pop * 100) if initial_pop > 0 else 0` ⇒ **`mortality_rate_pct` ya es un porcentaje 0-100** (redondeado a 2d).
2. `get_kpi_ipe` (`:634`): `viabilidad = 100.0 - mortality_kpi["mortality_rate_pct"]` ⇒ **viabilidad 0-100**.
3. Pruebas de que NO llega como fracción:
   - Suite R-184 (compatibilidad de insumo, aserción de unidad): `viabilidad_pct == 95.0` para 5 % de mortalidad (`test_r184_ipe_date_semantics.py`, fixture 1000 aves / 50 muertes).
   - Runtime committed (lote 11): `"viabilidad_pct": 100.0` (no `1.0`) — `audit/ga-r184/evidence/green/runtime-e2e.json`.
4. Conclusión: el `× 100` del numerador históricamente convertía **fracción→porcentaje**, pero la viabilidad **ya es porcentaje** ⇒ doble conversión. OD-22 lo confirma y ordena retirarlo.

## 2 · Ganancia diaria — g/día (probado)

- `avg_weight_g` = promedio de `BirdMovement.avg_weight` de eventos `WEIGHT_RECORDING` del lote (`service.py:641-648`; sin filtro de estado — comportamiento existente, no se toca). En gramos.
- `age_days` = días de calendario (`:653-655`) con `_dia()`; fallback 30 sin fecha; clamp `≤0 → 1`.
- `ganancia_diaria = avg_weight_g / age_days` (`:662`) ⇒ **g/día** (redondeo 2d). No se redefine (OD-22 §no-ADG).

## 3 · FCR — cociente simplificado documentado (probado)

- `feed_conversion_ratio = round(total_feed_kg / 1000, 2) if total_feed_kg > 0 else 0` (`service.py:164`; nota contractual «estimado/requiere pesaje real»).
- `fcr = fcr_kpi.get("feed_conversion_ratio") or 0.0`; guarda `if fcr > 0 else 0.0` (`:661-663`).
- Fuente: suma de `FeedMovement.quantity_kg` de eventos `FEED_REGISTRATION` con estado ∈ {APPROVED, CONSOLIDATED, SENT_TO_SAP, SAP_CONFIRMED} (`_sum_feed_kg`, `:100-116`).
- **Semántica FCR: SIN CAMBIOS** (OD-22 no la modifica; la limitación de precisión queda fuera de alcance).

## 4 · Prueba algebráica del conflicto 100× (3 casos)

`implementado = viab% × gain/(fcr×10) × 100 = 100 × EPEF`

| Caso | Insumos crudos | EPEF/OD-22 (cómputo independiente) | Implementado (pre-fix, evidencia) | Ratio |
|---|---|---|---|---|
| Suite determinista (R-184 fixture) | viab 95.0 · gain 2000/19 = 105.2631… · fcr 3.0 | `(190000/19)/30 = 10000/30 = 333.333…` → **333.3** | 33333.3 (aserción de la suite pre-OD-22) | **100.0 exacto** |
| Runtime lote 11 (`L-BO-2026-05`) | viab 100.0 · gain 1500/110 = 13.6363… · fcr 24.5 | `1363.6363/245 = 5.5658…` → **5.6** | **556.6** (committed `runtime-e2e.json`) | ≈ 99.99 |
| Runtime lote 53 | viab 100.0 · gain 1800/19 = 94.7368… · fcr 2.5 | `9473.6842/25 = 378.9473…` → **378.9** | **37894.7** (committed) | ≈ 99.99 |

Notas de redondeo: los «implementado» vienen del producto (1d); los «OD-22» se calculan desde los insumos **sin redondear** y se redondean al final con la misma política (`round(x, 1)`), de ahí que los ratios difieran de 100 en 0.01 %.

## 5 · Edad y fechas — herencia R-184 (control, no objetivo)

- `_dia(valor)` (`lots/service.py:7`; convención `R-75`/`GA-REM-028`) normaliza el día de negocio; usada en `:653` (G-06) y `:602` (G-05, R-186).
- Controles: lote del mismo día ⇒ age 1; lote sin fecha ⇒ 30; nunca `TypeError` (R-184).
- **R-187 no toca esta lógica**; los tests R-187 la incluyen como GREEN CONTROL.

## 6 · IPE — unidad resultante

- `ipe = (viabilidad × ganancia_diaria) / (fcr × 10)`, redondeo 1d, escala EPEF esperada ~200-400 con datos normales.
- Guardas: `fcr > 0` (si no, `0.0`); sin NaN/Infinity por construcción (denominador > 0 garantizado por la guarda; `age_days ≥ 1` garantizado por clamp/fallback).

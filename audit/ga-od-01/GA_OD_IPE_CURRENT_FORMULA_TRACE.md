# GA-OD-01 · TRAZA DE LA FÓRMULA ACTUAL DEL IPE (G-06)

## 1 · Fuente exacta

| Elemento | Valor |
|---|---|
| Archivo / función | `backend/app/reports/service.py` · `ReportsService.get_kpi_ipe` (líneas ~622-665; edad normalizada desde R-184) |
| Endpoint | `GET /api/v1/reports/kpi/ipe/{lot_id}` (G-06) |
| Definición escrita | Docstrings de router y servicio: «IPE = (Viabilidad% × Ganancia_Diaria_g × 100) / (FCR × 10)» |

## 2 · Fórmula implementada (literal)

```python
viabilidad = 100.0 - mortality_kpi["mortality_rate_pct"]          # 0..100 (porcentaje)
avg_weight_g = AVG(BirdMovement.avg_weight)  # eventos WEIGHT_RECORDING, gramos
age_days = (date.today() - _dia(lot.start_date)).days             # días; clamp <=0 → 1
ganancia_diaria = avg_weight_g / age_days                         # g/día
fcr = feed_conversion_ratio or 0.0                                # simplificado (kg/1000)
ipe = (viabilidad * ganancia_diaria * 100) / (fcr * 10) if fcr > 0 else 0.0
# respuesta: ipe redondeado a 1 decimal
```

## 3 · Unidades de cada entrada (verificadas)

| Variable | Representación | Rango típico | Fuente |
|---|---|---|---|
| Viabilidad | **Fracción porcentual 0-100** (`95.0`, no `0.95`) | 90-100 | `100 − mortalidad%` |
| Ganancia diaria | **g/día** | 40-70 (datos reales); fixture 105-136 | `peso_g / edad_d` |
| Peso | gramos | 1500-2500 | pesajes |
| Edad | días de calendario | 1-… | `start_date` |
| FCR | cociente simplificado (contrato: «kg feed / kg weight (estimado)»; placeholder documentado) | real ~1.5-2.0; heredado hasta 24.5 | feed/1000 |
| Salida IPE | número redondeado 1d | — | — |

## 4 · Expresión simplificada dimensionalmente

```
IPE_implementado = viabilidad[%] × (peso_g / edad_d) × 100 / (FCR × 10)
                 = [ADG_g/día × viabilidad[%] / (FCR × 10)] × 100
```

El término entre corchetes es exactamente el **EPEF estándar** (cuando la viabilidad entra en %). Por tanto el implementado es **100 × EPEF estándar** — el factor `×100` del numerador es la conversión fracción→porcentaje aplicada a una viabilidad que **ya viene en porcentaje** (doble conteo).

## 5 · Redondeo
`ipe` → 1 decimal (único redondeo de la salida). Preservado en cualquier opción.

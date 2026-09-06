# `P-15` · IMPLEMENTACIÓN DE INDICADORES

Fase de análisis · 2026-09-06

| KPI (`docs/02 §3.12.1`) | Normativo | Cálculo backend | API | Interfaz | Prueba | Estado |
|---|:--:|---|---|:--:|:--:|---|
| Mortalidad diaria y acumulada | sí | `get_kpi_mortality` | `/kpis/mortality` | sí | sí | **completo** |
| Viabilidad | sí | dentro de `get_kpi_ipe` (`viabilidad_pct`) | `/kpi/ipe/{lot}` | sí | sí | **completo** |
| Peso promedio vs estándar | sí | `get_kpi_weight_uniformity` + `reference` | `/kpi/weight-uniformity/{lot}` | sí | sí | **completo** |
| Uniformidad | sí | ídem (`cv_pct`) | ídem | sí | sí | **completo** |
| Consumo de alimento | sí | `get_kpi_feed_conversion` | `/kpis/feed-conversion` | sí | sí | **completo** |
| Conversión alimenticia | sí | ídem (`feed_conversion_ratio`) | ídem | sí | sí | **completo** |
| Producción de huevos | sí | `get_kpi_egg_production` | `/kpis/egg-production` | sí | sí | **completo** |
| **Fertilidad** | **sí** | **ninguno** | — | no | no | **`R-86` · sin productor** |
| **Eclosión** | **sí** | **devuelve texto** | `/kpis/hatchery` | sí, vacío | no | **`R-14` · roto** |
| **Nacimiento** | **sí** | **devuelve texto** | ídem | ídem | no | **`R-14` + `R-85`** |
| Rendimiento incubadora | sí | ídem | ídem | ídem | no | **`R-14`** |
| Diferencias SAP vs App | sí | `get_sap_comparison` | `/reports/sap-comparison` | sí | sí | **completo** |
| **Eficiencia de Vacunación** | **sí** (cliente) | `get_kpi_vaccination_efficiency` | `/kpis/vaccination-efficiency` | **no** | no | **`C` · huérfano** |
| **Eficiencia de Traslado** | **sí** (cliente) | `get_kpi_transfer_efficiency` | `/kpis/transfer-efficiency` | **no** | no | **`C` · huérfano** |
| Índice de Bienestar Animal | **no** | `get_kpi_animal_welfare` | `/kpis/animal-welfare` | no | no | `I` · no exigido |
| Índice de Producción | **no** | `get_kpi_production_index` | `/kpis/production-index` | no | no | `I` · no exigido |
| AFCR | **no** | `get_kpi_afcr` | `/kpis/afcr` | por confirmar | no | `I` · no exigido |

```
Obligatorios ......................... 15   (13 de docs/02 + 2 del cliente)
Completos ............................  8
Rotos ................................  3   (Eclosión, Nacimiento, Rendimiento — un solo campo)
Sin productor ........................  1   (Fertilidad)
Calculados y no expuestos ............  2   (Vacunación, Traslado)
Implementados sin ser exigidos .......  3   (Bienestar, Índice de Producción, AFCR)
```

## El defecto central, medido

`reports/service.py:145`

```python
"hatchability_pct": "N/A (requiere datos de carga de incubación)",
"note": "Para hatchability completa se necesitan datos de huevos cargados en incubadoras",
```

**La afirmación del comentario es falsa**, y `GA-REM-022` ya lo había demostrado:
`HatcheryParams.quantity_loaded` guarda los huevos cargados (`operations/models.py:207`) y
`get_hatchery_egg_balance` ya los suma (`validators.py:105`).

Un campo llamado `_pct` que devuelve una frase en español rompe cualquier consumidor que
espere un número, y la pantalla lo muestra vacío.

## Los tres cocientes bajo un solo campo

El endpoint devuelve un único `hatchability_pct` donde `docs/02 §3.12.1` exige **tres**
indicadores con denominadores distintos. Detalle y resolución en
`P15_NORMATIVE_KPI_MATRIX §2`.

## Consistencia de fórmulas

No hay duplicación: todos los KPI se calculan en `reports/service.py` y la interfaz solo los
consume. No se encontró ningún cálculo replicado en el frontend.

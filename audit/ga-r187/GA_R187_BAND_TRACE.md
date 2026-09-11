# GA-R187 · TRAZA DE BANDAS Y COMPARADORES — IPE G-06 (SIN CAMBIOS)

Mandato OD-22: **las bandas NO cambian**. Este documento fija el comportamiento **actual exacto**
que R-187 debe preservar comportamiento por comportamiento (§15 del encargo).

## 1 · Capa 1 — Backend `reference` (contrato; `service.py:673`)

```python
"reference": {"excellent": ">300", "good": "250-300", "average": "200-250"}
```

Literal de respuesta — **se conserva tal cual** (parte del esquema, R187-AC11/§40).

## 2 · Capa 2 — Clasificación visible en frontend (comparadores exactos)

| Archivo | Línea | Expresión (actual, exacta) |
|---|---|---|
| `frontend/src/pages/lots/LotDetailPage.tsx` | 396-397 | `kpiIpe.ipe >= 300 ? '🟢' : kpiIpe.ipe >= 250 ? '🟡' : '🔴'` + misma cadena para `t('kpi.excellent'|'kpi.good'|'kpi.average')` |
| `frontend/src/pages/reports/LotReportPage.tsx` | 167-168 | idéntica (mismos umbrales/labels) |

Operadores: `>= 300` (300 cuenta como 🟢) · `>= 250` (250 cuenta como 🟡) · resto 🔴.
**NO se reescriben, no se «limpian», no se convierten `>` en `>=`, no se reinterpretan textos.**

## 3 · Capa 3 — Etiquetas i18n (`frontend/public/locales/*/translation.json:1050-1052`)

| clave | es | en |
|---|---|---|
| `kpi.excellent` | Excelente | Excellent |
| `kpi.good` | Bueno | Good |
| `kpi.average` | Regular | Average |

## 4 · Tabla de frontera (comportamiento ACTUAL, a preservar)

| Valor de `ipe` mostrado | Comparador que dispara | Resultado |
|---|---|---|
| 249.9 | ninguno de los dos (`>=250` no) | 🔴 «Regular» |
| **250.0** | `>= 250` | **🟡 «Bueno»** |
| 250.1 | `>= 250` | 🟡 «Bueno» |
| 299.9 | `>= 250` | 🟡 «Bueno» |
| **300.0** | `>= 300` | **🟢 «Excelente»** |
| 300.1 | `>= 300` | 🟢 «Excelente» |

Controles ejecutables: suite R-187 (valores exactos 249.9 / 250.0 / 300.0 por insumos) + runtime UI (E2E-04/04b con fixtures `B250`/`B300`).

## 5 · Observación de wording (registrada, NO se corrige aquí)

`DOCUMENTATION_BOUNDARY_WORDING`: los textos del literal `reference` (`"250-300"`, `"200-250"`)
solapan en 250 y llaman «average» al rango 200-250, mientras la UI clasifica `< 250` como 🔴 «Regular».
Es una **observación de documentación**; OD-22 no manda cambiar bandas ni textos ⇒ **sin fix de producto en R-187** (§15: no crear fix por el wording dentro de esta tranche).

## 6 · Propiedad de la clasificación (probado por grep)

- El backend **no clasifica**: solo calcula `ipe` y emite el literal `reference`.
- El frontend **no recalcula** el IPE (no hay fórmula duplicada; grep de `ipe` en `frontend/src` = 2 páginas de solo lectura + display) y clasifica localmente con los comparadores de §2.
- Por tanto: el cambio OD-22 (valor) **cambiará la banda mostrada cuando el nuevo valor caiga en otra banda — esperado**; un cambio de definición de banda sería defecto — no ocurre.

## 7 · Consistencia detail/report

Ambas páginas usan los mismos umbrales y muestran `kpiIpe.ipe` del mismo endpoint G-06 ⇒ detalle y reporte deben coincidir valor y banda (E2E-07/08).

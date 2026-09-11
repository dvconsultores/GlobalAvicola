# GA-R186 · RECONCILIACIÓN CANÓNICA — G-05 PRODUCTION INDEX: SEMÁNTICA TEMPORAL + HTTP 500

Baseline de entrada: `main` `2f9483f` == remoto · producto backend `3f88f94` (fix R-184) **sin cambios** · bundle `index-BUthrUt9.js` · runtime https://avicola.globaldv.net.

## 1 · Evidencia original (heredada, inmutable)

| Elemento | Verdad |
|---|---|
| Primera captura | `audit/ga-r184/evidence/red/runtime-red.json`, caso `prodindex35` (commit `304174d`): `{"path": "/reports/kpis/production-index?lot_id=35", "status": 500, "body": "Internal Server Error"}` |
| Contexto | Actor autoridad global, empresa 1 efectiva, ventana BU `broiler` ON, lote 35 con `start_date` no nulo (todo alta fija inicio) |
| Formalización | GA-GOV-02 (`2f9483f`): R-186 `FORMAL_OPEN_FINDING` (P2), dedup `DISTINCT_NEW_FINDING`, ID siguiente libre tras R-185 |

## 2 · Endpoint y traza real

| Elemento | Valor |
|---|---|
| Método y ruta | `GET /api/v1/reports/kpis/production-index` (`app/reports/router.py:106-113`) |
| Permiso | `require_permission("reports", "read")` — exacto, sin cambios |
| Parámetro | `lot_id` (Query **requerido**, entero) — **endpoint de un solo lote** (no colección) |
| Servicio | `ReportsService.get_kpi_production_index` (`app/reports/service.py:579-617`) |
| Definición citada | Docstring del método: «Broiler production index = (avg_weight_g * viability_pct) / (age_days * FCR)» + docstring del router «G-05: Calculate Broiler Production Index for a lot» |

## 3 · Expresión fallida (probada)

`app/reports/service.py` línea **604** (única expresión sin normalizar que queda en el módulo):

```python
age_days = (date.today() - lot.start_date).days if lot and lot.start_date else 30
```

- `date.today()` → `datetime.date`; `Lot.start_date` → `DateTime(timezone=True)` → `datetime` aware ⇒ **`TypeError: unsupported operand type(s) for -: 'datetime.date' and 'datetime.datetime'`** ⇒ 500.
- Lotes sin `start_date` caen al fallback 30 (por eso el defecto no se veía en fixtures antiguos).
- **No tocada por el fix de R-184** (verificado en su diff: solo `get_kpi_ipe`).

## 4 · Distinción de R-184 (misma clase ≠ mismo finding)

| Eje | R-184 | R-186 |
|---|---|---|
| Endpoint | `/reports/kpi/ipe/{lot_id}` (G-06) | `/reports/kpis/production-index?lot_id=` (G-05) |
| Fórmula | IPE (viabilidad × ganancia diaria × 100 / FCR×10) | PI = (peso × viabilidad) / (edad × FCR × 10) |
| Expresión | línea propia del método IPE | línea propia del método PI |
| Estado | CLOSED_OWNER_ACCEPTED | OPEN — **objetivo de esta tranche** |

## 5 · Comportamiento esperado canónico

`200` con el payload documentado: `{lot_id, avg_weight_g (1d), viability_pct (1d), age_days (int), fcr (2d), production_index (1d), unit: "index"}` — sin crash ante entrada válida (contrato de código nivel 4 + precedente R-184 del propietario).

## 6 · Severidad, alcance y cierre

- **P2** (defecto funcional real; API-only sin consumidor frontend; sin workaround pero superficie limitada).
- **Alcance**: única expresión `age_days` en `get_kpi_production_index`; reutilizar `_dia()` (ya importado desde R-184). Sin cambios de fórmula, esquema, permisos, endpoints, migraciones ni frontend.
- **Fuera de alcance**: fuente de la observación de escala del IPE (sigue `OWNER_DECISION_REQUIRED`, intacta); cualquier reinterpretación de la fórmula G-05; G-06; OBS-UAT-01; BU-D10; Wave B/C/SAP.
- **Criterio de cierre**: 500 resuelto con causa raíz demostrada; valor determinista independiente; estados ausentes/vacíos controlados; seguridad intacta (tenant/BU/RBAC/OD-16); R-184 sin regresión; E2E-01…13 PASS.

## 7 · Nota informativa registrada (no formalizada)

El docstring del método omite el factor `×10` del divisor que el código aplica (`... (age_days * fcr * 10)`). R-186 **preserva el comportamiento ejecutable** (el código es el contrato vigente) y **no dirime** la semántica de escala — misma clase de tensión que la observación IPE para G-06, pero **sin impacto de runtime**: se registra aquí como nota para una eventual revisión de semántica conjunta (junto a la decisión pendiente del IPE), sin crear ID nuevo ni tocarla en esta tranche.

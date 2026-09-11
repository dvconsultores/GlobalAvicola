# GA-R187 · EVIDENCIA RED (pre-implementación)

Fecha: 2026-09-11 · HEAD de gobernanza: `67e938e` · Producto desplegado: backend `0309225` · bundle `index-BUthrUt9.js`.

## 1 · Captura de preflight runtime (solo lectura, §8)

| Ítem | Valor |
|---|---|
| Health | `health:200` |
| Frontend bundle | `index-BUthrUt9.js` (sin cambio esperado) |
| `GET /reports/kpi/ipe/11` | **404** `{"detail":"Lote no encontrado"}` (BU OFF ⇒ alcance productivo vacío; OD-16 gobernado) |
| `GET /reports/kpi/ipe/53` | **404** idem |
| `GET /reports/kpi/ipe/35` | **404** idem |

Raw: `evidence/red/prefix-ipe-11.json` · `prefix-ipe-53.json` · `prefix-ipe-35.json`.
Nota: el 404 es el comportamiento **correcto/vigente** con la ventana BU OFF (restaurada al cierre de GA-GOV-02);
no es señal sobre la fórmula. Además sirve como pre-hook de E2E-12 (el actor global tampoco evade BU OFF).

## 2 · RED-A — evidencia pre-fix committed de la línea G-06 sin cambios

La línea G-06 (`get_kpi_ipe`, expresión del `ipe`) **no ha cambiado** desde `3f88f94` (R-184): el diff
`3f88f94..0309225` de `backend/app/reports/service.py` toca **solo** la línea de G-05 (R-186). Por tanto la
evidencia runtime committed de R-184 es válida como comportamiento pre-fix de la generación desplegada:

| Caso | Insumos crudos (evidencia) | `ipe` pre-fix (actual) |
|---|---|---|
| Lote 11 | viab 100.0 · gain 1500/110 = 13.6363… · fcr 24.5 | **556.6** (`audit/ga-r184/evidence/green/runtime-e2e.json`) |
| Lote 53 | viab 100.0 · gain 1800/19 = 94.7368… · fcr 2.5 | **37894.7** (idem) |
| Suite R-184 (fixture determinista) | viab 95.0 · gain 2000/19 = 105.2631… · fcr 3.0 | **33333.3** (aserción de la suite; mismo régimen) |

## 3 · RED-B — núcleo matemático independiente (el conflicto es exactamente ×100)

Cálculo independiente con OD-22 (insumos crudos, **sin** pasar por el producto):

| Caso | Esperado OD-22 = `viab × gain / (fcr × 10)` (redondeo final 1d) | Pre-fix actual | Ratio actual/esperado |
|---|---|---|---|
| Suite | `(190000/19)/30 = 10000/30 = 333.333…` → **333.3** | 33333.3 | **100.000 exacto** |
| Lote 11 | `1363.6363/245 = 5.5658…` → **5.6** | 556.6 | ≈ 99.99 |
| Lote 53 | `9473.6842/25 = 378.9473…` → **378.9** | 37894.7 | ≈ 99.99 |

**RED VALIDADO** (defecto de escala exacto ×100; diferencias de 0.01 % explicadas por redondeo a 1d del producto).

## 4 · RED-C — RED a nivel de test (declarado honestamente)

`backend/tests/test_r187_ipe_od22_scale.py` (commit C1) afirma los valores OD-22 (333.3 / 241.1 / 282.7 /
249.9 / 250.0 / 300.0). Contra el código actual esta suite **falla** (33333.3 ≠ 333.3) — es el RED de test.
En local requiere PostgreSQL y queda `skipped` (declarado, igual que R-184/R-186; corre en CI). Por eso la
validación RED ejecutable en esta tranche es §2+§3 (evidencia real del producto desplegado) y el GREEN se
verificará con runtime autenticado post-fix (E2E-01/02/03/04/05 + fronteras).

## 5 · Decisión de ejecución registrada (§31): expectativa histórica vs OD-22

- NO se congela `556.6` (ni `33333.3`) como objetivo de regresión: el régimen de fórmula anterior queda
  **superseded por OD-22**.
- La suite R-184 **actualiza su aserción numérica** al valor OD-22 (mismos insumos crudos ⇒ 333.3),
  preservando sus invariantes técnicos (200, fechas, esquema, seguridad). Cambio incluido en C2 (junto al fix).
- Los documentos históricos `audit/ga-r184/**` y `audit/ga-uat-06/**` **no se reescriben**; la distinción
  «régimen anterior / regla OD-22» queda registrada aquí y en la reconciliación de cierre.

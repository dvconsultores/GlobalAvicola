# GA-R187 · EVIDENCIA RUNTIME AUTENTICADA (E2E-01…14 + regresiones)

Entorno: `https://avicola.globaldv.net` (producción de prueba, empresa 1) · Fecha: 2026-09-11.
Generación congelada: **backend C2 `f755baa` desplegado** (probe de deploy: `ipe/11 = 5.6`; pre-fix committed = 556.6) · Bundle **`index-BUthrUt9.js`** (sin cambio).
Raw: `evidence/green/runtime-api.json` · `runtime-ui.json` · `cleanup.json`.

## 1 · Fixtures deterministas creados (actores sintéticos; detalle en ledger)

Lotes 54-59 (`L-R187-*`) con insumos crudos controlados (1000 aves, eventos mortalidad/peso/alimento **aprobados** por cadena completa con actores sintéticos segregados).

## 2 · E2E — núcleo OD-22 (API autenticada, actor `ra187op`)

| Caso | Lote | Insumos (respuesta) | **ipe** | Esperado OD-22 (independiente) | Veredicto |
|---|---|---|---|---|---|
| E2E-01 determinista | 54 DET | viab 95.0 · gain 105.26 · age 19 · fcr 3.0 | **333.3** | `(95×2000/19)/30 = 333.333… → 333.3` | **PASS (exacto)** |
| E2E-02 escala (legado) | 11 | viab 100 · gain 13.64 · age 110 · fcr 24.5 | **5.6** | `1363.63/245 = 5.5658… → 5.6` | **PASS** (pre-fix: 556.6 ⇒ ratio 99.99) |
| E2E-02 escala (legado) | 53 | viab 100 · gain 94.74 · age 19 · fcr 2.5 | **378.9** | `9473.68/25 = 378.947… → 378.9` | **PASS** (pre-fix: 37894.7) |
| E2E-03 banda baja | 55 LOW | viab 90.0 · fcr 2.0 | **241.1** | `90×53.57/20 = 241.07 → 241.1` | **PASS** 🔴 (<250) |
| E2E-04 banda media | 56 MID | viab 95.0 · fcr 3.0 | **282.7** | `95×89.29/30 = 282.74 → 282.7` | **PASS** 🟡 |
| E2E-05 banda alta | 54 DET | (idem E2E-01) | **333.3** | ≥300 | **PASS** 🟢 |
| Control cero | 33 / 35 | sin datos | **0.0** | guardas intactas | **PASS** |

**Fronteras exactas (comparadores SIN tocar; clasificación espejo de UI):**

| Lote | ipe | Banda | Frontera |
|---|---|---|---|
| 57 B249 | **249.9** | 🔴 | justo por debajo de 250 |
| 58 B250 | **250.0** | 🟡 | `>= 250` dispara |
| 59 B300 | **300.0** | 🟢 | `>= 300` dispara |

## 3 · E2E-06 — semántica de fechas (R-184 técnico)

- Lote 11: `age_days = 110` exacto (start 2026-05-24) — **sin ±1 día**; HTTP 200.
- Lote 54 DET: `age_days = 19` exacto.
- Sin 500 en ningún lote de la batería. Esquema íntegro: `{lot_id, viabilidad_pct, avg_weight_g, ganancia_diaria_g, age_days, fcr, ipe, reference}`.

## 4 · E2E-07…10 — UI visible (Playwright, actor `ra187op`)

| Caso | Resultado |
|---|---|
| E2E-07 detalle | Tarjeta IPE **333.3** · 🟢 «Excelente» · sin error crudo · captura `UI-desktop-detalle-DET.png` |
| E2E-08 reporte | **333.3** (mismo valor que detalle) · sin error · captura `UI-desktop-reporte-DET.png` |
| E2E-09 refresh/relogin | Tras refresh **333.3**; tras sesión nueva **333.3** — sin valor viejo de escala |
| E2E-10 móvil 390×844 | **333.3** legible · `overflow = 0` · sin error · captura `UI-mobile-detalle-DET.png` |

## 5 · E2E-11…14 — seguridad (gobernada, sin cambios)

| Caso | Petición | Resultado |
|---|---|---|
| E2E-11 lote ajeno | op → ipe/14 (empresa 3) | **404** «Lote no encontrado» (anti-enumeración) |
| E2E-11 inexistente | op → ipe/999999999 | **404** |
| E2E-12 BU OFF (empresa) | op → ipe/54 | **404** |
| E2E-12 BU OFF (actor global) | admin → ipe/54 | **404** (OD-16: la autoridad global no evade BU OFF) |
| E2E-12 restauración | re-enable → op → ipe/54 | **200** (control) |
| E2E-13 sin concesión | `ra187nobu` → ipe/54 | **404** |
| E2E-14 sin RBAC | `ra187noperm` → ipe/54 | **403** «Permiso requerido: reports:read» |

Sin fuga cross-tenant; sin 500.

## 6 · Regresiones

- **R-184 (técnico)**: 200 en lote válido · fechas preservadas (age 110) · esquema íntegro · seguridad intacta. **556.6 = SUPERSEDED_BY_OD22 (NO objetivo de regresión)**; los mismos insumos producen 5.6. → **PRESERVADO (técnica) / SUSTITUIDO (valor)**.
- **R-186 (G-05)**: `GET /reports/kpis/production-index?lot_id=11` → **200**, `production_index 5.1` (valor certificado preservado), misma semántica temporal. → **PRESERVADO**.
- **GA-FE-07 spot**: `PUT /lots/54 {area_id: 16}` → **400** «Área inactiva»/BR-07 (OD-21/R-185 intacto). → **PASS**.
- **GA-FE-02/03**: BU/tenant cubiertos por E2E-11…14; navegación/listado OK en UI. **GA-FE-04/05/06** sin superficie tocada (sin diff frontal/backend fuera de G-06). → **PASS (spot)**.

## 7 · Limpieza y control

- 4 concesiones revocadas · 5 usuarios baja lógica · 4 roles desactivados · ventana BU **restaurada OFF (4×OFF verificado)** · admin operativo (control `GET /roles` 200).
- Lotes 54-59 **retenidos** como fixtures sintéticos oficiales (documentados en ledger); actores/roles/credenciales destruidos.
- RAW de limpieza: `evidence/green/cleanup.json`.

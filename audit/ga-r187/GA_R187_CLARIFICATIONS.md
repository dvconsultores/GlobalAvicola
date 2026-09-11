# GA-R187 · CLARIFICACIONES (C01-C20)

Resolución de las cuestiones del encargo §19. **Sin nueva pregunta al propietario** — OD-22 ya resolvió la cuestión de negocio.

| # | Cuestión | Resolución | Fuente |
|---|---|---|---|
| C01 | Endpoint exacto | `GET /api/v1/reports/kpi/ipe/{lot_id}` | `router.py:116-123` |
| C02 | Función backend exacta | `ReportsService.get_kpi_ipe` | `service.py:626-674` |
| C03 | Fórmula antigua exacta | `(viabilidad × ganancia_diaria × 100) / (fcr × 10)`; `0.0` si `fcr<=0` | `service.py:663` |
| C04 | Fórmula nueva exacta | `(viabilidad × ganancia_diaria) / (fcr × 10)`; guarda igual | OD-22; spec §5 |
| C05 | Escala runtime de viabilidad | **0-100** (%): `100.0 − mortality_rate_pct`; mortalidad = `deaths/pop×100`; probado suite (95.0) y runtime (100.0) | `service.py:634,152`; `GA_R187_UNIT_TRACE.md` §1 |
| C06 | Unidad de ADG | g/día = `avg_weight_g / age_days` (peso de `WEIGHT_RECORDING`) | `service.py:641-662` |
| C07 | Unidad/semántica FCR | cociente simplificado `total_feed_kg/1000` `or 0.0`; nota «requiere pesaje real» — sin cambios | `service.py:155-164` |
| C08 | Semántica de edad | `(date.today() − _dia(start_date)).days`; fallback 30; clamp ≤0→1 | `service.py:653-655` |
| C09 | Normalización de fechas | `_dia()` canónica R-75/GA-REM-028 (`lots/service.py:7`), preservada (R-184) | spec §7 |
| C10 | Redondeo | viab 2d · peso 1d · ganancia 2d · fcr 2d · **ipe 1d** — intacto | `service.py:665-672` |
| C11 | Contrato de respuesta | 8 claves + `reference` literal — intacto | spec §10 |
| C12 | Bandas | `reference` intacto; comparadores UI `>=300/>=250/resto` intactos; labels intactos | `GA_R187_BAND_TRACE.md` |
| C13 | Comportamiento exacto en 250 | `250.0 → 🟡` (dispara `>= 250`); `249.9 → 🔴`; verificado por tests/fixtures exactos | BAND_TRACE §4 |
| C14 | Comportamiento exacto en 300 | `300.0 → 🟢` (dispara `>= 300`); `299.9 → 🟡` | BAND_TRACE §4 |
| C15 | Propiedad backend/frontend de la clasificación | Backend: valor + `reference`; frontend: clasifica localmente (sin fórmula duplicada) | BAND_TRACE §6 |
| C16 | Persistencia histórica | NO hay campo/columna IPE; cálculo en vivo (grep models = vacío) | reconciliation §5 |
| C17 | Migración | NO necesaria; backfill NO; reescritura NO | reconciliation §6 |
| C18 | Owner UAT | REQUIRED (KPI visible cambia); READY tras certificación; acceptance PENDING (no auto-aprobación) | spec §17 |
| C19 | Semántica de regresión R-184 | Remediar técnico PRESERVADO; **556.6 SUPERSEDIDO por OD-22, NO objetivo de regresión**; mismos insumos crudos → valor OD-22 | reconciliation §8 |
| C20 | Criterios de cierre | Todos los críticos PASS + E2E-01…14 + limpieza + evidencia + local==remoto | reconciliation §9; spec §15 |

**Nota de wording registrada:** `DOCUMENTATION_BOUNDARY_WORDING` (solape en 250 de los textos `"250-300"`/`"200-250"`) — observación de documentación, sin fix de producto en R-187 (`GA_R187_BAND_TRACE.md` §5).

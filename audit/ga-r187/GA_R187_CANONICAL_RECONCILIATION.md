# GA-R187 · RECONCILIACIÓN CANÓNICA — OD-22 · ESCALA ESTÁNDAR DEL IPE (G-06)

Tranche: R-187 (implementación de OD-22) · Fecha: 2026-09-11 · Baselines: gobernanza `67e938e` · producto backend `0309225` · bundle `index-BUthrUt9.js`.

## 1 · Cadena de gobernanza (de dónde viene esto)

| Eslabón | Referencia |
|---|---|
| Observación de negocio | R-184 §7 «Tensión detectada» (`audit/ga-r184/GA_R184_IPE_BUSINESS_TRACE.md`) |
| Formalización | GA-GOV-02: `OWNER_DECISION_REQUIRED` (`audit/ga-gov-02/GA_GOV_02_OWNER_DECISION_PACKET.md`, `2f9483f`) |
| Paquete de decisión | GA-OD-01 (`audit/ga-od-01/`, C1 `3cf7baf`) |
| **Decisión del propietario** | **OD-22 («Opción A») — RATIFICADA el 2026-09-11** (`GA_OD_IPE_SCALE_OWNER_DECISION.md`, C2 `67e938e`) |
| **Finding de brecha** | **R-187 · P2 · OPEN** (`audit/ga-od-01/GA_OD_IPE_SCALE_IMPLEMENTATION_GAP_R187.md`) |
| Autorización de esta tranche | Prompt R-187 §EXECUTION MODE — «OWNER AUTHORIZATION: R-187 IMPLEMENTATION AUTHORIZED» |

R-187 es **distinto** de R-184 y R-186 (ambos CLOSED: HTTP 500 por `date − datetime`, endpoints/líneas propias). R-187 no reabre ni reutiliza esos findings; implementa una regla de negocio **nueva y prospectiva**.

## 2 · Fórmula

| | Expresión | Fuente |
|---|---|---|
| **Vigente hoy (pre-OD-22)** | `ipe = (viabilidad × ganancia_diaria × 100) / (fcr × 10)` si `fcr > 0` else `0.0` | `backend/app/reports/service.py:663` (G-06 `get_kpi_ipe`) |
| **Canónica OD-22 (objetivo)** | `ipe = (viabilidad × ganancia_diaria) / (fcr × 10)` si `fcr > 0` else `0.0` | OD-22 §3.2; semántica EPEF: `EPEF = ADG_g × viabilidad% / (FCR × 10)` |

El único cambio es **retirar el factor `× 100`** del numerador. Nada más de la expresión cambia:
guarda `fcr > 0`, fuentes de insumos, redondeos y esquema de respuesta quedan intactos.

## 3 · Unidades (probadas; detalle completo en `GA_R187_UNIT_TRACE.md`)

| Magnitud | Unidad | Prueba |
|---|---|---|
| Viabilidad | **porcentaje 0-100** (`95.0` = 95 %) | `100.0 − mortality_rate_pct` (`service.py:634`); `mortality_rate_pct = deaths/initial_pop × 100` (`:152`); runtime: lot 11 devuelve `viabilidad_pct: 100.0` (committed) — no `1.0` |
| Ganancia diaria | **g/día** | `avg_weight_g / age_days` (`:662`); avg sobre `WEIGHT_RECORDING` (`:641-648`) |
| FCR | cociente **simplificado** `total_feed_kg / 1000` | `get_kpi_feed_conversion` (`:155-164`, nota «requiere pesaje real») — semántica NO se toca |
| Edad | días de calendario | `(date.today() − _dia(start_date)).days`; fallback 30; clamp ≤0 → 1 (`:653-655`); `_dia` en `lots/service.py:7` |
| IPE | índice (escala EPEF tras OD-22) | resultado del cociente; se redondea a 1 decimal (`:672`) |

**Prueba del conflicto 100× (algebraica):** con viabilidad en % el cociente EPEF es
`viab% × gain / (fcr × 10)`. El código multiplica por 100 adicional ⇒ implementado = **100 × EPEF estándar**.
Exacto, verificado en 3 casos (unidades; ver `GA_R187_UNIT_TRACE.md` §4).

## 4 · Bandas y comparadores (SIN CAMBIOS — detalle en `GA_R187_BAND_TRACE.md`)

- Backend `reference` literal: `{">300", "250-300", "200-250"}` (`service.py:673`) — se conserva tal cual (contrato).
- Clasificación visible (frontend, comparadores actuales exactos):
  `ipe >= 300 → 🟢` · `ipe >= 250 → 🟡` · resto `→ 🔴` — `LotDetailPage.tsx:396-397`, `LotReportPage.tsx:167-168`.
- Etiquetas i18n: `kpi.excellent/good/average` = «Excelente/Bueno/Regular» (es) · «Excellent/Good/Average» (en) — `frontend/public/locales/*/translation.json:1050-1052`.
- OD-22 no cambia umbrales, ni operadores, ni etiquetas. **Nota de documentación** (no defecto): el texto `"250-300"`/`"200-250"` solapa en 250 y llama «average» al rango 200-250 mientras la UI clasifica `<250` como 🔴 «Regular» ⇒ se registra como `DOCUMENTATION_BOUNDARY_WORDING`; **no se crea fix de producto en R-187**.

## 5 · Comportamiento de cálculo en runtime

- El IPE se **calcula en vivo** en cada llamada (`GET /api/v1/reports/kpi/ipe/{lot_id}`, `router.py:116-123`); no existe columna ni caché persistida de IPE (grep sobre `models.py` = vacío).
- Lecturas gobernadas por OD-16: `route_scope.py:163` (`MULTI_UNIDAD`) + `_exigir_lote` (404 anti-enumeración).
- Pre-fix capturado hoy (solo lectura): `ipe/11`, `ipe/53`, `ipe/35` → **404** con BU OFF (gobernado; coherente con OD-16). Raw en `evidence/red/prefix-ipe-*.json`.

## 6 · Datos históricos

- **Migración: NO. Backfill: NO. Reescritura histórica: NO.**
- Las pantallas históricas mostrarán el valor **recalculado** bajo OD-22 al consultarlo. Es el comportamiento buscado por la decisión (cambio prospectivo de fórmula, cálculo en vivo).

## 7 · Alcance / fuera de alcance

**En alcance:** retirar `× 100` en `get_kpi_ipe` + actualizar docstrings de la fórmula (servicio/router) + suite R-187 + evidencia/certificación runtime.
**Fuera de alcance (§5 del encargo):** bandas, etiquetas, FCR, viabilidad, ADG, fechas (salvo preservarlas), UI, endpoints nuevos, permisos nuevos, migración, R-184/R-186, OBS-UAT-01, BU-D10, Wave B/C/SAP.

## 8 · Relación con R-184 / R-186 (certificaciones)

- **R-184 (CLOSED_OWNER_ACCEPTED)**: se preserva la **remediación técnica** (200 en todo lote, `_dia()`, sin ±1 día, esquema y seguridad). El **valor histórico 556.6 queda SUSTITUIDO por OD-22 y NO es objetivo de regresión**: los mismos insumos crudos deben producir el valor OD-22 calculado independientemente (lote 11 → **5.6**).
- **R-186 (CLOSED, API_ONLY)**: G-05 no se toca (fórmula, endpoint, tests, semántica). Sin acoplamiento de fórmula G-05↔G-06.

## 9 · Criterios de cierre

Todos los críticos en PASS: AC06-AC29 (fórmula/resultado/fechas), AC13-AC18 (bandas), runtime E2E-01…14, seguridad, R-184 técnico preservado, R-186 intacto, GA-FE-02..07 spot, cleanup sin residuo, evidencia commitada, local==remoto.

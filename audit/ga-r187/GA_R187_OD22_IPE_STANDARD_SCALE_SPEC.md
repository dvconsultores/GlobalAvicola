# GA-R187 · SPEC — OD-22 · IPE G-06 A ESCALA ESTÁNDAR (EPEF), SIN EL ×100

Estado: SPEC CONGELADA para implementación · Tranche R-187 · 2026-09-11
Autoridad de negocio: **OD-22** (ratificada 2026-09-11; `audit/ga-od-01/GA_OD_IPE_SCALE_OWNER_DECISION.md`)

## 1 · Contexto

`GET /api/v1/reports/kpi/ipe/{lot_id}` (G-06) calcula el Índice de Producción Europeo con la fórmula
histórica `(viabilidad × ganancia_diaria × 100) / (FCR × 10)`. La viabilidad ya llega como porcentaje
(0-100) ⇒ el `× 100` es una doble conversión (probado: `GA_R187_UNIT_TRACE.md`). El resultado vive
~100× por encima de las bandas clásicas (300/250) ⇒ clasificación poco informativa (casi todo «Excelente»).
GA-GOV-02 lo formalizó como decisión de propietario; **OD-22 resolvió: alinear el valor a la escala
estándar (opción A)**. R-187 implementa esa decisión.

## 2 · Decisión OD-22 (cláusulas relevantes)

- Viabilidad en porcentaje 0-100.
- Fórmula canónica: `IPE = (viabilidad_pct × ganancia_diaria_g) / (FCR × 10)`.
- Retirar el `× 100` implementado.
- Bandas, etiquetas y umbrales: SIN CAMBIOS. Datos históricos: sin migración (cálculo en vivo).

## 3 · R-187 (finding)

Brecha de implementación P2 entre producto (escala inflada) y regla ratificada; se cierra con esta tranche
si todos los criterios críticos pasan (ver `audit/ga-od-01/GA_OD_IPE_SCALE_IMPLEMENTATION_GAP_R187.md`).

## 4 · Fórmula actual (pre-fix, exacta)

`service.py:663`: `ipe = (viabilidad * ganancia_diaria * 100) / (fcr * 10) if fcr > 0 else 0.0`
(docstring `:629` y router `:122` citan la misma expresión).

## 5 · Fórmula canónica (post-fix)

`ipe = (viabilidad * ganancia_diaria) / (fcr * 10) if fcr > 0 else 0.0`
Único cambio: retirar `* 100`. Nada más.

## 6 · Unidades e insumos (detalle: `GA_R187_UNIT_TRACE.md`)

| Insumo | Semántica | Fuente | Cambia |
|---|---|---|---|
| `viabilidad` | % 0-100 = `100 − mortality_rate_pct` | `service.py:634`, `:140-153` | NO |
| `ganancia_diaria` | g/día = `avg_weight_g / age_days`; peso = avg `WEIGHT_RECORDING` | `:641-662` | NO |
| `fcr` | `total_feed_kg/1000` (simplificado documentado) `or 0.0` | `:155-164`, `:661` | NO |
| `age_days` | días calendario, `_dia()`, fallback 30, clamp ≤0→1 | `:653-655` | NO |
| `ipe` | cociente EPEF, redondeo 1d | `:663`, `:672` | SÍ (valor) |

## 7 · Semántica de fechas (heredada R-184 — INTACTA)

`_dia()` (`lots/service.py:7`, R-75/GA-REM-028) + fallback/clamp; 200 en todo lote con inicio; sin ±1 día.
AC19-AC23. La suite R-187 la incluye como control.

## 8 · FCR / Viabilidad / ADG — semánticas congeladas

OD-22 no las redefine; cualquier comportamiento actual (incluida la limitación «FCR requiere pesaje real»)
se preserva (AC09-AC11).

## 9 · Bandas y fronteras (SIN CAMBIOS — `GA_R187_BAND_TRACE.md`)

`reference` literal intacto; comparadores UI exactos `>=300 🟢 / >=250 🟡 / resto 🔴`; 250.0→🟡; 300.0→🟢;
labels i18n intactos. AC13-AC18.

## 10 · Contrato de respuesta (SIN CAMBIOS)

Claves `{lot_id, viabilidad_pct(2d), avg_weight_g(1d), ganancia_diaria_g(2d), age_days(int), fcr(2d), ipe(1d), reference}`;
HTTP 200/403/404 según gobierno existente. Único cambio legítimo de salida: **valor `ipe`** (y, en consecuencia,
la banda visible si el nuevo número cae en otra banda existente). AC24-AC29, §40.

## 11 · Comportamiento frontend

Sin cambios de código (solo muestra + clasifica). AC30-AC36 verificables por runtime UI.
Frontend product diff esperado: **0 archivos**.

## 12 · Comportamiento histórico

Cálculo en vivo; sin migración/backfill; pantallas históricas recalculan al consultar (intencional OD-22). AC16/AC17.

## 13 · Tenant / BU / RBAC (intactos)

`_exigir_lote` 404 anti-enumeración; OD-16 (BU OFF bloquea incluso actor global); RBAC `reports:read`.
AC37-AC42.

## 14 · Fuera de alcance

§5 del encargo (bandas nuevas, labels, dashboards, FCR/feed/viabilidad/ADG nuevos, migración, R-184/R-186 rework, OBS-UAT-01, BU-D10, Wave B/C/SAP).

## 15 · Criterios de aceptación (AC) — fuente única

**Gobierno:** AC01 OD-22 citada como autoridad · AC02 R-187 distinto de R-184/R-186 · AC03/AC04 fórmulas documentadas · AC05 unidades probadas.
**Fórmula:** AC06 `×100` eliminado · AC07 forma canónica exacta · AC08 ningún otro multiplicador/divisor cambia · AC09 viabilidad intacta · AC10 ADG intacto · AC11 FCR intacto · AC12 fecha/edad intacta.
**Bandas:** AC13 bandas intactas · AC14 labels intactos · AC15 frontera 250 intacta · AC16 frontera 300 intacta · AC17 sin umbral nuevo · AC18 consistencia UI/backend.
**Fecha:** AC19 `_dia()` vigente · AC20 sin TypeError · AC21 sin ±1 día · AC22 mismo día canónico (1) · AC23 sin fecha canónico (30).
**Resultado:** AC24 fixture determinista == cálculo independiente OD-22 · AC25 esperado NO derivado del producto · AC26 redondeo intacto · AC27 sin NaN · AC28 sin Infinity · AC29 entradas faltantes/cero controladas.
**UI:** AC30 detalle muestra valor nuevo · AC31 reporte igual · AC32 clasificación con bandas intactas · AC33 refresh estable · AC34 relogin estable · AC35 móvil usable · AC36 sin error crudo.
**Seguridad:** AC37 lote ajeno 404 · AC38 BU OFF denegado · AC39 sin concesión denegado · AC40 sin RBAC 403 · AC41 actor global no evade BU OFF · AC42 sin fuga cross-tenant.
**Regresión:** AC43 fix 500 R-184 preservado · AC44 fechas R-184 preservadas · AC45 contrato R-184 preservado (sin congelar 556.6) · AC46 G-05/R-186 sin cambios · AC47 R-185 sin cambios · AC48 GA-FE-05 sin cambios · AC49 GA-FE-06 sin cambios · AC50 GA-FE-07 sin cambios · AC51 OBS-UAT-01 sin tocar · AC52 BU-D10 sin decisión.

## 16 · Tests

`backend/tests/test_r187_ipe_od22_scale.py` (PG/CI; skip local declarado): determinista 333.3 · bandas 241.1/282.7 ·
fronteras 249.9/250.0/300.0 · matemática independiente · fechas control · seguridad. `test_r184_ipe_date_semantics.py`
**actualizada (§31)**: mismos insumos crudos ahora esperan el valor OD-22 (333.3), invariantes técnicos intactos;
los documentos históricos `audit/ga-r184/**` NO se reescriben. Runtime E2E-01…14 (autenticado).

## 17 · Runtime y Owner UAT

Runtime autenticado contra `https://avicola.globaldv.net` con actores sintéticos oficiales; E2E según §46-64.
Owner UAT: **REQUIRED / READY tras certificación** (KPI visible cambia); acceptance PENDING. Guion: `GA_R187_OWNER_UAT.md`.

## 18 · Cierre

R-187 = CLOSED solo si todos los críticos PASS (§68-69). OD-22 = RATIFIED_IMPLEMENTED (o RATIFIED_NOT_IMPLEMENTED si falla). Sin residuos; cleanup verificado.

# GA-R186 · SPEC — G-05 PRODUCTION INDEX: SEMÁNTICA TEMPORAL + CIERRE DEL 500

## 1 · Contexto
`GET /api/v1/reports/kpis/production-index?lot_id=` (G-05) devuelve **500** para todo lote con `start_date` (todo alta real), por `date.today() − lot.start_date` (`date` − `datetime` aware). Capturado en `audit/ga-r184/evidence/red/runtime-red.json` (caso `prodindex35`), formalizado como **R-186 (P2)** en GA-GOV-02.

## 2 · Alcance
Backend only. Única expresión: `age_days` en `get_kpi_production_index`. Normalización con `_dia(...)` (ya importado; R-75/GA-REM-028) — la misma convención que G-06 tras R-184 y que `lots/service.py:379` / `operations/service.py:776`. Sin cambios de fórmula, esquema, permisos, endpoints ni frontend.

## 3 · Fuera de alcance
Observación de escala IPE (`OWNER_DECISION_REQUIRED`, intacta) · nota docstring `×10` de G-05 (registrada, no resuelta) · G-06 (intacto) · OBS-UAT-01 · BU-D10 · Wave B/C/SAP · UI nueva.

## 4 · Definición G-05 y contrato de endpoint
Ver `GA_R186_G05_BUSINESS_TRACE.md` (§1-4): `(avg_weight_g × viability_pct) / (age_days × FCR × 10)`; endpoint de un solo lote; permiso `reports:read`.

## 5 · Entradas / temporal / día / agregación
`GA_R186_G05_INPUT_MATRIX.md` y `GA_R186_DATE_SEMANTICS_TRACE.md`: dominio DATE; conteo `(hoy − día_inicio).days`; mismo día ⇒ 0 ⇒ guarda ⇒ PI 0 (sin clamp); sin inicio ⇒ 30; sin FCR ⇒ `or 1`; no hay colección (N/A probado).

## 6 · Datos ausentes / inválidos
Ningún estado vacío produce 500/NaN/∞ (agregados vacíos = 0; guardas explícitas preservadas).

## 7 · Contrato de respuesta
Sin cambios: `{lot_id, avg_weight_g(1d), viability_pct(1d), age_days(int), fcr(2d), production_index(1d), unit:"index"}`.

## 8 · Seguridad
Preservada íntegra: `_exigir_lote` (404 anti-enumeración), alcance por unidades habilitadas+concedidas (GA-REM-040 fase 4), **OD-16** (la autoridad global no bypassa la habilitación de empresa), RBAC `reports:read`.

## 9 · Consumidor frontend
**API_ONLY** verificado: único rastro = campo opcional `production_index?: number` en el tipo `KpiData` (`services/reports.service.ts:12`), **sin llamadas** al endpoint desde páginas/hook/servicio. ⇒ **Owner UAT: NOT REQUIRED** (documentado; sin estado de gobernanza inventado: se registra como «no requerida» junto a la certificación técnica).

## 10 · Errores
422 sin `lot_id` · 401 sin sesión · 403 sin `reports:read` · 404 inalcanzable · 200 resto. El 500 del defecto desaparece; fallos no previstos siguen escalando al manejador estándar.

## 11 · Auditoría / rendimiento
Lectura pura (sin efectos); sin consultas nuevas (mismo SQL; solo cambia la normalización en Python).

## 12 · AC → `GA_R186_CHECKLIST.md` (R186-AC01…AC43; colección N/A probada).
## 13 · Pruebas → `backend/tests/test_r186_g05_date_semantics.py` (PG/CI; skip local declarado) + repro local determinista.
## 14 · Despliegue → push main; pipeline + Watchtower; freeze de generación.
## 15 · Evidencia runtime → E2E-01…13 + red + regresión R-184 (`ipe/11` = 556.6 exacto).
## 16 · Cierre → `GA_R186_CLOSURE_RECONCILIATION.md`; R-186 CLOSED si todos los criticos PASS.
## 17 · Política Owner UAT → NOT REQUIRED (API_ONLY); si apareciera superficie visible, se prepararía tras el cierre técnico (no en esta tranche).

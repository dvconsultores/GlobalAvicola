# GA-R184 · SPEC — SEMÁNTICA TEMPORAL DEL IPE + REMEDIACIÓN DEL 500

## 1 · Contexto

`GET /api/v1/reports/kpi/ipe/{lot_id}` (G-06, Índice de Producción Europeo) devuelve **HTTP 500** para todo lote con `start_date` — es decir, para todo lote real — a cualquier actor con `reports:read`. El detalle de lote (`LotDetailPage`) y el reporte de lote (`LotReportPage`) consumen este endpoint y hoy pierden silenciosamente la tarjeta IPE.

## 2 · Historia del finding

GA-FE-06 (n-2 candidato) → **R-184** (P2). Hipótesis reportada «date − datetime», verificada aquí contra código, modelo y runtime (ver `GA_R184_CANONICAL_RECONCILIATION.md`).

## 3 · Alcance

**Backend only.** Única expresión: `age_days` en `ReportsService.get_kpi_ipe`. Normalización canónica del día de calendario con `_dia(...)` (R-75 / GA-REM-028), reutilizada desde `app/lots/service.py`. Sin cambios de fórmula, esquema, migraciones, permisos, endpoints ni frontend.

## 4 · Fuera de alcance

- G-05 `production-index` (misma clase) → candidato **R-186** registrado, NO implementado.
- Semántica de escala del IPE vs bandas `reference` → observación de negocio registrada.
- Congelar edad por estado del lote / definir estados permitidos → no especificado; no se inventa.
- Diseño de «null/no calculable» para datos ausentes → contrato actual preservado.
- OBS-UAT-01 · R-181/R-182/R-185/OD-21 · BU-D10 · Wave B/C · SAP: intactos.

## 5 · Definición de negocio del IPE

Citada con fuentes en `GA_R184_IPE_BUSINESS_TRACE.md` §1-2: `IPE = (Viabilidad% × Ganancia_Diaria_g × 100) / (FCR × 10)`; `Ganancia_Diaria_g = avg_weight_g / age_days`.

## 6 · Variables de entrada

Tabla completa y fuentes: `GA_R184_IPE_BUSINESS_TRACE.md` §2 y `GA_R184_INPUT_AVAILABILITY_MATRIX.md`.

## 7 · Estados de lote

`GA_R184_LOT_STATE_MATRIX.md` — sin cambios; sin filtros nuevos.

## 8 · Semántica de fechas y conteo

`GA_R184_DATE_SEMANTICS_TRACE.md` §4-5: dominio **DATE** para la edad; conteo `(hoy − día_inicio).days` con `date.today()` (convención vigente, simulable en pruebas); clamp del mismo día → 1; sin `start_date` → 30 (legado preservado).

## 9 · Zona horaria

Sin framework nuevo. El día de negocio ya se persiste anclado a medianoche UTC; la comparación se hace día-de-calendario contra día-de-calendario (normalizadas ambas partes). Sin off-by-one (AC14).

## 10 · Datos ausentes / cero / inválidos

`GA_R184_INPUT_AVAILABILITY_MATRIX.md`: 404 fuera de alcance; agregados vacíos = 0 (cierto); guardas `fcr > 0` y clamp; nunca 500/NaN/∞.

## 11 · Contrato de respuesta

Sin cambios: `lot_id`, `viabilidad_pct` (2d), `avg_weight_g` (1d), `ganancia_diaria_g` (2d), `age_days` (int), `fcr` (2d), `ipe` (1d), `reference` literal.

## 12 · Tenant / BU / RBAC (preservado íntegro)

- `require_permission("reports","read")` — permiso exacto, **0 permisos nuevos**.
- `_exigir_lote`: 404 «Lote no encontrado» para inexistente/ajeno.
- Empresa: `self.company_id` del actor; extranjero ⇒ 404.
- BU: `lotes_alcanzables(company, unidades_de_alcance_productivo(...))` (GA-REM-040 fase 4 · **OD-16**): empresa-OFF ⇒ 404; usuario sin concesión ⇒ 404; **actor global NO bypassa la habilitación de empresa** (lee por habilitadas).

## 13 · Consumidor frontend

`LotDetailPage.tsx:56` y `LotReportPage.tsx:28` (fetch `Promise.allSettled`; tarjeta oculta si falla). Clasificación: **USER_VISIBLE**. Consecuencia esperada del fix: la tarjeta IPE vuelve a mostrarse para roles con `reports:read`. **Owner UAT REQUIRED: YES.**

## 14 · Errores

401 sin sesión · 403 sin `reports:read` · 404 lote inalcanzable · 200 resto. **El 500 desaparece para el caso del defecto** (lote con `start_date`); fallos de programación no previstos siguen escalando al manejador estándar (no se convierten en 400).

## 15 · Auditoría

Lectura pura: sin efectos de escritura/auditoría (se verifica en runtime §logs). No se añade auditoría de acceso.

## 16 · Criterios de aceptación → `GA_R184_CHECKLIST.md` (R184-AC01…37, cobertura total).

## 17 · Pruebas

`backend/tests/test_r184_ipe_date_semantics.py` (PG; skip local declarado, CI): valor determinista (33333.3), clamp mismo día, legado 30, estabilidad, 404, 403, BU OFF, sin concesión, global+BU-OFF.

## 18 · Despliegue

Push a `main` (backend/**) → GH Actions → Docker Hub :latest → Watchtower. Sin cambios de política. Freeze de generación backend post-deploy.

## 19 · Evidencia runtime

E2E-01…12 (`GA_R184_AUTHENTICATED_RUNTIME_EVIDENCE.md`) + red (`GA_R184_NETWORK_EVIDENCE.md`) + capturas de superficie (detalle de lote).

## 20 · Criterios de cierre

500 original resuelto con causa raíz demostrada y fórmula preservada; AC críticos PASS; seguridad PASS; regresión GA-FE-02..07 PASS; limpieza §69 ejecutada; R-184 → CLOSED.

## 21 · Política de Owner UAT

Superficie **USER_VISIBLE** ⇒ Owner UAT **REQUIRED**: sesión corta (carga del KPI, valor visible, sin error, refresco, móvil si se expone). El propietario no repite pruebas de tipos/seguridad.

# GA-R184 · CERTIFICACIÓN

```
TRANCH      R-184 — KPI/IPE: semántica temporal + remediación del HTTP 500
ESTADO      FUNCTIONALLY_CERTIFIED
FINDING     R-184 = CLOSED_OWNER_ACCEPTED
OWNER UAT   EJECUTADA — GA-UAT-06 (2026-09-11): decisión A) ACEPTO R-184
OWNER_ACCEPTANCE  PASS — registro: audit/ga-uat-06/GA_OWNER_ACCEPTANCE_R184_RECORD.md
```

## Base de la certificación

- **Causa raíz demostrada**: `TypeError` `date − datetime` en `ReportsService.get_kpi_ipe` (expresión exacta, reproducción determinista + runtime 500×2 pre-fix).
- **Fix mínimo**: C2 `3f88f94` — única expresión normalizada con `_dia()` canónico; fórmula intacta; backend-only; 0 migraciones/permisos/endpoints.
- **Gates**: backend canónico 7 passed; suite nueva PG/CI (10 casos, skip local declarado); tsc PASS; build PASS; Vitest **280/280**.
- **Runtime E2E-01…12**: **14/14 PASS** con valores esperados calculados de forma independiente (556.6 y 37894.7 exactos).
- **Seguridad**: tenant/ajeno 404 · BU OFF 404 (incl. actor global, OD-16) · sin concesión 404 · sin RBAC 403 · sin fuga en errores.
- **UI**: tarjeta IPE visible (desktop/móvil), sin 500 visible, consola sin fatales (solo clase N-3 conocida).
- **Higiene**: fixtures retirados (roles/usuarios/grant), BUs restauradas OFF (c1 y c3, 4×OFF verificados), credenciales y temporales destruidos, auditoría preservada, humanos intactos, lotes 53/61/62 retenidos como evidencia.

## Registros derivados (sin implementación)

1. **R-186 (candidato)**: `GET /reports/kpis/production-index` (G-05) comparte la expresión defectuosa ⇒ 500 con `start_date`; capturado en RED; **separate open** por regla de alcance §4.
2. **Observación de negocio**: posible factor ~100 de la fórmula implementada frente a la escala de las bandas `reference` (viabilidad en % + ×100 en numerador). No se toca; clasificada `OWNER_DECISION_REQUIRED` futura, no bloquea.

## Límites declarados

- Suite PG corre en CI (`run_tests.sh`); en local queda `skipped` (declarado, no fingido). Evidencia ejecutada de RED/GREEN = runtime + repro determinista.
- Los lotes «retinados» quedan legibles solo con BU ON (estado normal del entorno con BU OFF es fail-closed OD-16).
- No se reabren R-181/R-182/R-185/OD-21; OBS-UAT-01 y BU-D10 sin cambio; Wave B/C/SAP fuera.

## Cierre de aceptación

Owner UAT ejecutada (**GA-UAT-06**, 2026-09-11): **decisión A) ACEPTO R-184** → **R-184 CLOSED_OWNER_ACCEPTED** · OWNER_ACCEPTANCE **PASS** (6/6 casos, sin observaciones). Registro: `audit/ga-uat-06/GA_OWNER_ACCEPTANCE_R184_RECORD.md`. Certificación técnica preservada; sin cambios de producto.

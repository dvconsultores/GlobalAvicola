# FINAL FRONTEND AUDIT · MATRIZ 7 CAPACIDADES INTERNAS (FIA-01…07)

Fecha: 2026-09-11 · Sin UAT de usuario (por definición). Taxonomía interna del encargo §14.

| FIA | Capacidad | Propósito | Code owner | Test owner | Evidencia runtime/interna | Dependencia externa | ¿Sigue interna? | ¿Necesita frontend? | Estado actual | Residual | Evidencia |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FIA-01 | Enforcement RBAC por ruta | Autoridad del backend en cada endpoint | `app/auth/security.py` (`require_permission`) | suites backend + runtime E2E | 403 reales observados (actor sin permiso; `/lots` con rol mínimo; masters/sap fail-closed) | — | YES | NO | **INTERNAL_CERTIFIED** | NONE | GA-FE-03/04 · runtime-uat (403s) |
| FIA-02 | Aislamiento tenant/unidad en escritura | Sin fuga cross-tenant; unidad operativa obligatoria | `app/tenancy.py`, `business_units/service.py` | `test_od16_global_read_boundary`, "cross-company" (CI) | 404 spot cross-tenant; 403 BU-OFF (R-163/R-188) | — | YES | NO | **INTERNAL_CERTIFIED** | NONE | ga-fe-02-d · ga-bu-d10 |
| FIA-03 | Balance de población/huevos (bloqueo) | Cuadres bajo lock (P-01/P-02) | `app/operations/*` | suites backend | cubierto en certificaciones backend previas | — | YES | NO | **INTERNAL_CERTIFIED** | NONE | ga-rem (histórico) |
| FIA-04 | Trazabilidad generacional/linaje | Árbol de linaje efectivo | backend de trazabilidad + `TraceabilityTree.tsx` | suites + UI | árbol visible en UI (componente presente y cacheado en bundle) | — | YES | NO (árbol ya existía) | **INTERNAL_CERTIFIED** | NONE | código + UI |
| FIA-05 | Auditoría inmutable (aplicación) | Append-only en aplicación (listeners) | audit listeners | suites | runtime: `/audit` carga eventos reales (S14) | BD (trigger) pendiente | YES | NO | **INTERNAL_IMPLEMENTED_NOT_CERTIFIED** | **R-148** (P2, BD; registrado Wave B) | REMEDIATION_BACKLOG:939 |
| FIA-06 | Reverso interno (servicio) | Solicitud/ejecución gobernada de reversos | GA-REM-041/OD-19 | `R-136-INTERNAL-REVERSAL-EVIDENCE.md` | certificado en su tranche; sin UI | — | YES | UI diferida (ver FVA-28) | **INTERNAL_CERTIFIED** | NONE | audit/remediation/R-136-… |
| FIA-07 | Adaptador SAP (semántica/consolidación) | Contrato SAP desacoplado | `app/sap/*` | suites SAP (R-112 open) | UI de referencias funciona; integración real no | **SAP real (`P-08`)** | YES | NO por ahora | **INTERNAL_BLOCKED_EXTERNAL** | R-112 (P2, contratos) | BACKEND_CAPABILITY_MAP:47 |

**Conteo interno: 7/7 reconciliadas** — INTERNAL_CERTIFIED 5 · INTERNAL_IMPLEMENTED_NOT_CERTIFIED 1 · INTERNAL_BLOCKED_EXTERNAL 1 · INTERNAL_MISSING 0 · INTERNAL_OUT_OF_SCOPE 0 · INTERNAL_SUPERSEDED 0.

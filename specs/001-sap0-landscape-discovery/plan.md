# Implementation Plan: SAP-0 — Landscape Discovery + Inbound Data Contract

**Feature**: `specs/001-sap0-landscape-discovery` · **Fecha**: 2026-09-17
**Tipo de plan**: **SPEC/DEVELOPMENT ONLY — sin implementación de producto** (mandato §2/§3).

---

## 1 · Technical Context

- **Lenguajes/stack del producto**: Python/FastAPI + React (contexto únicamente; **no se toca código** en este plan).
- **Artefactos de este plan**: documentación en `audit/sap0/**` + paquete spec en `specs/001-sap0-landscape-discovery/**`.
- **Dependencias externas** (todas PENDING, fuera de SAP-0): SAP Basis (SAP-BASIS-01), autorización de probe (SAP0_PROBE_AUTHORIZATION), decisiones Owner (SAP-CONN-01, SAP-STO-01, SAP-LOT-01, SAP-CUSTODY-01, SAP-SCOPE-01, SAP-ENV-01, SAP-SEC-01, SAP-FALLBACK-01, SAP-PROD-01).
- **Herramientas de evidencia**: lectura remota del repo legacy (read-only), inspección del código actual (read-only), git (commit/push de documentación).
- **Restricciones duras**: PROHIBIDO implementar, conectar SAP/VPN/HANA, añadir `hdbcli`, crear `RealSapAdapter`, tocar `backend/frontend/e2e/.github`, importar datos.

## 2 · Constitution Check (adaptado a fase de especificación)

| Principio aplicable | Cumplimiento |
|---|---|
| Honestidad de estados (GA-REM-010) | ✔ `REAL SAP INTEGRATION = NOT IMPLEMENTED` preservado; nada simulado |
| No falsos datos | ✔ Todo campo current = `UNKNOWN`; legacy citado como evidencia |
| Multi-compañía fail-closed | ✔ Especificado (RAW §3, convergencia §5) |
| Mínima exposición de secretos | ✔ Sin secretos en documentos; gate de custodia (AOD-12) |
| Trazabilidad | ✔ Evidencia por hallazgo, ACs mapeados a documentos, cadena spec-development registrada |

**Resultado**: PASS (no hay violaciones; no se requiere Complexity Tracking).

## 3 · Estructura de artefactos (entregables)

```
audit/sap0/
  SAP_LEGACY_REPOSITORY_AUDIT.md              (discovery legacy §4–§10)
  SAP_LANDSCAPE_DISCOVERY_SPEC.md             (§34: campos UNKNOWN + requisitos de prueba)
  SAP_LEGACY_TO_CURRENT_MAPPING_MATRIX.md     (§11–§13: separación + mapeo)
  SAP_INBOUND_DATA_CATALOG.md                 (§14: 12 objetos × 14 campos)
  SAP_CONNECTIVITY_OPTIONS_ANALYSIS.md        (§19: 8 opciones × 13 dimensiones)
  SAP_BRIDGE_ARCHITECTURE_PROPOSAL.md         (§23: definido, NO implementado)
  SAP_RAW_STAGING_SPEC.md                     (§20–§24, §30: RAW/STAGING, delta, reconciliación)
  SAP_COMPANY_FARM_CONVERGENCE_SPEC.md        (§15 OD-24 + fail-closed)
  SAP_DISCOVERY_EXECUTION_PLAN.md             (§35–§36: P0–P6 + request Basis)
  SAP_OWNER_DECISIONS_REQUIRED.md             (gates reales clasificados)
  SAP0_SPEC_DEVELOPMENT_TRACEABILITY.md       (cadena completa + analyze/converge)
  SAP0_VERIFICATION_REPORT.md                 (§33 checklist)
  SAP_GA_REM_017_RECLASSIFICATION.md          (§37: reclasificación por bloqueo)
specs/001-sap0-landscape-discovery/
  spec.md  plan.md  tasks.md  research.md
```

## 4 · Fases del programa (separación estricta)

| Fase | Contenido | Estado |
|---|---|---|
| **SAP-0** (este plan) | Discovery + contratos + plan de probe + gates | **COMPLETADA en esta entrega (docs)** |
| SAP-1 | Autorización + probe autorizado P0–P6 (con evidencia) | `BLOCKED_BY_SAP0` (gates) — NO iniciada |
| SAP-2 | Implementación SAP Bridge (aislada) | `PLANNED` — bloqueada por SAP-CONN-01 |
| SAP-3 | Extracción RAW + validación/staging | `PLANNED` — bloqueada por SAP-2 |
| SAP-4 | Promoción + convergencia (OD-24) | `PLANNED` — bloqueada por SAP-3 |
| SAP-5 | Operación continua (deltas/reconciliación/servicios) | `PLANNED` — bloqueada por SAP-4 |

> SAP-0 termina **antes** del probe (mandato §4): este plan no incluye P0–P6 ejecutable.

## 5 · Enfoque de verificación (§33)

1. Comprobar con `git diff` que **ningún** archivo de producto cambió (`backend/`, `frontend/`, `e2e/`, `.github/workflows/`).
2. Confirmar 0 intentos de conexión (no hay sockets/VPN; esta fase no ejecutó red hacia SAP).
3. Revisar que no hay secretos/credenciales en los documentos nuevos.
4. Validar consistencia SPEC ↔ PLAN ↔ TASKS ↔ ACs (analyze) y ausencia de contradicciones (converge).
5. `git status` limpio tras commit; `LOCAL_SHA == REMOTE_SHA`.
6. Publicar informe `SAP0_VERIFICATION_REPORT.md` + salida compacta §44.

## 6 · Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Interpretar evidencia legacy como vigente | `CURRENT_VALIDITY=UNKNOWN` sistemático; separación §13 |
| Fuga de secretos en documentación | Regla explícita; verificación §33 |
| Sobre-alcance (implementar algo) | Prohibición en spec/plan/tasks; verificación de diff |
| Decisiones de negocio tomadas unilateralmente | Solo registro de gates (SAP_OWNER_DECISIONS_REQUIRED) |
| Estados ambiguos de GL-OD-06 | §38: solo dos valores permitidos; hoy `BLOCKED_EXTERNAL_SAP_INFORMATION` |

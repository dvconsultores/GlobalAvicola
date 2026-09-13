# GA · PRE-SAP — ESTADO DEL PROGRAMA (TRANCHE 0 · cierre)

Fecha: 2026-09-13 · Baseline: `f270d0b` (+ commits de governance de T0) · Fase: **remediación no iniciada — programa listo para arrancar en T1**.

## 1 · KPI del programa

| KPI | Valor | Meta de cierre |
|---|---|---|
| Procesos certificados E2E | **0 / 17** | 17/17 |
| Brechas bloqueantes abiertas | **24** (9 P1 + 15 P2) + GA-GOV-03 | 0 |
| Otras brechas abiertas | 10 (7 P2 no bloqueantes + 3 P3, incl. R-214) | cerradas o aceptadas |
| Heredados que bloquean/condicionan | 36 filas (incl. 4 sin spec: Wave C P1 + condicionales por decisión) | resueltos por decisión/rider |
| Suites | backend 25 rojos · Playwright 12 rojos (37 TEST_DEFECT) | 0 rojos |
| CI de tests | solo PR (nunca ejecutado) | push cubierto (OD-23) |
| Certificaciones con artefacto | 0 de 13 | 100% con commit+artefacto |
| UAT con evidencia primaria | 0 de 11 registros + 2 pendientes | 8 lotes finales completos |
| Decisiones del propietario pendientes (alcance actual) | 14 (+4 por tranche según roadmap) | registradas antes de su tranche |
| Tranches del programa | 13 (T1-T13) + Pista OPS | todas cerradas |
| Veredicto pre-SAP | `NO_GO_SAP_FUNCTIONAL_GAPS` (sin cambios) | GO/NO-GO final en T13 |

## 2 · Estado por tranche

| Tranche | Estado | Nota |
|---|---|---|
| T0 · Cierre de auditoría + programa | **EN CIERRE (este commit)** | 16 documentos nuevos + correcciones D-03 |
| T1 · GA-GOV-03 | **DEFINIDA, lista para ejecutar** | Ver §3 |
| T2-T13 + OPS | PLANIFICADAS | Orden y gates en el roadmap maestro |

## 3 · NEXT_IMPLEMENTATION_TRANCHE (§52)

- **ID**: `T1` · **Nombre**: Gobernanza de pruebas y certificaciones (`GA-GOV-03`).
- **Specs**: `GA-GOV-03` (paquete completo ×6) — sin otras specs.
- **Findings cubiertos**: los **37 TEST_DEFECT** (25 backend: 17 A + 5 B + 3 C; 12 Playwright) + CI solo-PR + certificaciones sin artefacto + aceptaciones sin evidencia primaria (regla) + backlog drift (`R-189`, `GA-UAT-09`, `OD-21…25`).
- **Prioridad**: **P1 gobernanza** — gate de arranque del programa.
- **Dependencias**: ninguna técnica (arranca de inmediato). Decisiones habilitantes: `OD-16` (contrato 403/404) y `OD-23` (CI en push sin bloquear deploy) — propuesta del programa registrada en el paquete.
- **Alcance**:
  1. Corregir los 25 tests backend a la regla vigente (fixtures/guards; sin tocar producto).
  2. Corregir los 12 Playwright (locator discriminatorio + fixtures BR-20/BR-21/BR-03/R-118).
  3. CI de tests en `push` (job separado del `docker-push`).
  4. Plantilla de certificación con **commit + artefacto** (fin de «GREEN por declaración»).
  5. Reconciliación de backlog/INDEX (`R-189`, `GA-UAT-09`, `OD-21…25` a hogar canónico).
- **Fuera de alcance**: producto (backend/app, frontend/src — **0 líneas**); R-213 (producto, va a T11); decisiones de negocio.
- **Ficheros esperados**: `backend/tests/**` (7 ficheros), `e2e/**` (6 specs), `.github/workflows/backend-ci.yml` + `frontend-ci.yml` (+ quality-gates si aplica), `audit/remediation/REMEDIATION_BACKLOG.md`, `specs/remediation/INDEX.md`, `audit/remediation/CERTIFICATION_EVIDENCE_TEMPLATE.md` (nuevo), `audit/ga-pre-sap-program/evidence/` (artefactos de corrida).
- **Tests**: los 37 corregidos + suite completa verde; artefactos `backend_full_suite_<sha>.log` y `playwright_e2e_<sha>.log`.
- **Runtime**: CI disparado en push; sin deploy de producto en esta tranche (no hay cambio de producto).
- **UAT del propietario**: **NO** (no hay cambio visible).
- **Criterio de salida**: backend `0 failed` + Playwright `0 failed` con artefactos; CI en verde sobre push; plantilla publicada; backlog reconciliado; `OD-16`/`OD-23` registradas como decisiones.

## 4 · Repositorio y siguiente paso

- Todo el material de T0 vive en `audit/ga-pre-sap-program/` (16 documentos) + correcciones D-03 en el paquete de auditoría; **producto diff = 0**.
- Tras el commit de T0: **STOP** — no se implementa T1 en esta sesión; el programa queda listo para que T1 arranque como siguiente tranche de implementación (con su propio RED→GREEN y artefactos).

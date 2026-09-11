# GA-BU-D10 · PLAN

| ID | Paso | Estado |
|---|---|---|
| P1 | Decisión del propietario (B) y OD-23 canonizada | ✅ |
| P2 | Finding R-188 formalizado (P2 OPEN) | ✅ |
| P3 | SPEC congelada (OD-23 · B) | ✅ |
| P4 | Matriz L1-L16 | ✅ |
| P5 | Clarificaciones C01-C20 | ✅ |
| P6 | AC (BU-D10-AC01…AC25) | ✅ (SPEC §15) |
| P7 | RED: suite B (PG/CI) + evidencia RED | ⏳ (C2) |
| P8 | C2 governance/decision/spec/RED commit + push | ⏳ |
| P9 | Implementación mínima (`fijar_habilitacion` marca+audita; docstrings) | ⏳ (C3) |
| P10 | Actualización de pruebas provisionales (AC-A04/AC-A06/admin) | ⏳ (C3) |
| P11 | GREEN targeted + suites BU/admin/guard/OD-16 + transferencia | ⏳ |
| P12 | Gates frontend (tsc/build/Vitest; esperado 0 diffs) | ⏳ |
| P13 | C3 implementación commit + push + deploy + freeze | ⏳ |
| P14 | Runtime E2E §54-64 (ON/OFF/re-enable/regrant/admin/AccessAdmin/self/cross/zero/RBAC/global/session/refresh/relogin/audit/persistence/UI dc+móvil) | ⏳ |
| P15 | Cleanup (BU estado original OFF, actores destruidos, credenciales) | ⏳ |
| P16 | Evidencia (backend/frontend/runtime/network/ledger/closure/certification) | ⏳ (C4) |
| P17 | Actualizar backlog/roadmap/catálogo/OD-23/R-188 | ⏳ |
| P18 | C4 evidence commit + push + verificación | ⏳ |
| P19 | Owner UAT package (REQUIRED) preparado; **aceptación NO auto-aprobada** | ⏳ |
| P20 | Informe final §78 + STOP (esperando UAT del propietario) | ⏳ |

Checkpoints git: C1 `067fba6` (paquete pre-decisión) · C2 (decisión+SPEC+RED) · C3 (implementación) · C4 (evidencia). C5 solo si UAT requiere aceptación explícita posterior.

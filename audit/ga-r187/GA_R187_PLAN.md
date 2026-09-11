# GA-R187 · PLAN (P1-P29)

| ID | Paso | Estado |
|---|---|---|
| P1 | Reconciliación OD-22 | ✅ (`GA_R187_CANONICAL_RECONCILIATION.md`) |
| P2 | Traza de fórmula actual | ✅ (`reconciliation §2`; `service.py:663`) |
| P3 | Traza de unidades | ✅ (`GA_R187_UNIT_TRACE.md`) |
| P4 | Traza de bandas/fronteras | ✅ (`GA_R187_BAND_TRACE.md`) |
| P5 | Traza frontend (propiedad) | ✅ (`BAND_TRACE §6`; 2 páginas, sin cálculo) |
| P6 | Traza histórica (sin persistencia) | ✅ (reconciliation §5-6) |
| P7 | SPEC | ✅ (`GA_R187_OD22_IPE_STANDARD_SCALE_SPEC.md`) |
| P8 | Clarificaciones C01-C20 | ✅ (`GA_R187_CLARIFICATIONS.md`) |
| P9 | AC (R187-AC01…AC52) | ✅ (spec §15) |
| P10 | RED determinista | ✅ (`GA_R187_RED_EVIDENCE.md`: matemática + evidencia pre-fix) |
| P11 | Controles de banda (249.9/250.0/300.0 + bandas) | ✅ suite R-187 (commit C1) |
| P12 | Controles de fecha (GREEN CONTROL) | ✅ suite R-187 (mismo día 1 / sin fecha 30) |
| P13 | Implementación (retirar ×100) | ⏳ (C2) |
| P14 | GREEN targeted | ⏳ |
| P15 | Regresión backend | ⏳ |
| P16 | Regresión frontend (tsc/build/Vitest) | ⏳ |
| P17 | Commit de implementación (C2) | ⏳ |
| P18 | Deploy automático + freeze de generación | ⏳ |
| P19 | Runtime determinista (E2E-01/02) | ⏳ |
| P20 | Runtime clasificación (E2E-03/04/05 + fronteras) | ⏳ |
| P21 | UI visible (E2E-07/08/09/10 + capturas) | ⏳ |
| P22 | Seguridad (E2E-11…14) | ⏳ |
| P23 | Regresión R-184 (técnica; sin 556.6) | ⏳ |
| P24 | Regresión R-186 (G-05) + GA-FE spots | ⏳ |
| P25 | Cleanup (actores/BU/grants/credenciales) | ⏳ |
| P26 | Reconciliación de cierre (AC→evidencia) | ⏳ |
| P27 | Certificación | ⏳ |
| P28 | Owner UAT readiness | ⏳ |
| P29 | STOP (sin iniciar UAT) | ⏳ |

Gobernanza (P1-P12) se commitea como **C1** antes de tocar producto (§36). Implementación = **C2**.
Evidencia runtime = **C4**. C3 solo si surge remediación adicional genuina (no esperada).

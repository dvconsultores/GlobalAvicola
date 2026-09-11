# GA-FE-08 · PLAN

Fecha: 2026-09-11 · Baseline: `30fe3dc`.

| Fase | Contenido | Estado |
|---|---|---|
| P1 | Reconstrucción de la fuente OBS-UAT-01 | ✅ |
| P2 | Traza de la superficie de Lotes (rutas/guards/permisos/BU/tenant) | ✅ |
| P3 | Traza de navegación (marco GA-FE-03, ausencia probada, ubicación canónica) | ✅ |
| P4 | Reproducción runtime autenticada pre-fix (A web + F móvil) | ✅ (`P01-P03`) |
| P5 | Matriz de seguridad de la entrada (empresa/BU/RBAC/zero-BU/control/global/OD-23) | ✅ (diseño §11 spec; pruebas en T) |
| P6 | Spec GA-FE-08 | ✅ |
| P7 | Clarificaciones C01–C20 | ✅ |
| P8 | AC FE08-AC01…37 | ✅ (spec §16) |
| P9 | RED (contrato ejecutable pre-fix) | ▶ |
| P10 | Commit de gobernanza C1 (+push+verificación) | ▶ |
| P11 | Implementación mínima (config de navegación + expectativa heredada justificada) | ⏳ |
| P12 | GREEN dirigido (nuevo test + suitemap nav) | ⏳ |
| P13 | Regresión frontend completa (Vitest, tsc, build) | ⏳ |
| P14 | Regresión focalizada backend (declarada; PG en CI) | ⏳ |
| P15 | Commit de implementación C2 (+push+verificación) | ⏳ |
| P16 | Auto-deploy (observación de generación) | ⏳ |
| P17 | E2E autenticado desktop (E2E-01/02) | ⏳ |
| P18 | E2E móvil (E2E-03) | ⏳ |
| P19 | E2E deep-link (autorizado/denegado) | ⏳ |
| P20 | E2E BU/RBAC/OD-23 (E2E-04…10) | ⏳ |
| P21 | Limpieza (BUs, concesiones, usuarios, roles, credenciales) | ⏳ |
| P22 | Evidencia (runtime, capturas C01–C09, ledger, frontend, regresión) | ⏳ |
| P23 | Reconciliación de cierre + certificación GA-FE-08 | ⏳ |
| P24 | Preparación UAT del propietario (guía + readiness) | ⏳ |
| P25 | STOP (sin iniciar Wave B/C/SAP) | ⏳ |

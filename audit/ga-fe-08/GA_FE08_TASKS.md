# GA-FE-08 · TAREAS

Fecha: 2026-09-11 · Baseline: `30fe3dc`. Implementación SOLO tras C1.

| ID | OBS-UAT-01 | Sección spec | AC | Archivos | Test | Evidencia runtime | Depende | Estado |
|---|---|---|---|---|---|---|---|---|
| T01 | entrada declarativa `lots` (config) | §8-§11 | 01-05, 26 | `frontend/src/data/navigationConfig.ts` | `gaFe08.lotsNav.test.ts` | C01-C04 | — | ⏳ |
| T02 | autoridad de la entrada (evaluador, sin cambios) | §11 | 06-18 | (reuso `auth/navigation.ts`) | matriz del test nuevo | E2E-04…10 | T01 | ⏳ |
| T03 | vistas desktop/móvil (hub, mismas reglas) | §12 | 19-20 | (reuso `MenuHubPage`, `MobileNav`) | vistas del test nuevo | E2E-01/03 | T01 | ⏳ |
| T04 | i18n por reuso (`nav.lots`) | §14 | 21-23 | (sin cambios; paridad ya existente) | paridad del test nuevo | ETIQUETA ES/EN | — | ⏳ |
| T05 | expectativa heredada justificada | §12 | 26, 28 | `frontend/src/data/__tests__/gaFe02.nav.test.ts` | actualización anotada | — | T01 | ⏳ |
| T06 | regresión local completa | §17 | 27-37 | — | Vitest + tsc + build + backend focal | evidencia frontend/backend | T01-T05 | ⏳ |
| T07 | RED pre-fix | §17 | 01 | `gaFe08.lotsNav.test.ts` | RED capturado | `GA_FE08_RED_EVIDENCE.md` | — | ▶ |
| T08 | commit C1 gobernanza + RED | §76 | — | `audit/ga-fe-08/**`, test RED | — | push | T07 | ⏳ |
| T09 | commit C2 implementación | §76 | — | T01/T05 | — | push + deploy | T06 | ⏳ |
| T10 | E2E autenticado | §18 | 01-20 | `/tmp` (scripts) | — | C01-C09 + JSON | T09 | ⏳ |
| T11 | limpieza | prompt §62 | — | — | — | ledger | T10 | ⏳ |
| T12 | evidencia + reconciliación + certificación | §75 | — | `audit/ga-fe-08/**` | — | docs | T10/T11 | ⏳ |
| T13 | commit C3 evidencia | §76 | — | evidence + masters | — | push | T12 | ⏳ |
| T14 | UAT del propietario (readiness) | §67 | 01-05 UAT | guía + paquete | — | pregunta A/B/C | T13 | ⏳ |

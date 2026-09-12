# R-189 · PLAN / CHECKLIST / TAREAS (F-01)

Fecha: 2026-09-12.

## PLAN

| Fase | Contenido | Estado |
|---|---|---|
| P1 | Preflight git/runtime (259a65c; sin commits intermedios) | ✅ |
| P2 | Dedup F-01 → R-189 (P1) | ✅ |
| P3 | Trazas: import, almacenamiento, OC, error; controles de contrato backend | ✅ |
| P4 | Spec + clarificaciones C01-C25 | ✅ |
| P5 | RED ×4 (payload import · OC · recepción · render de error; unit normalizador) | ▶ |
| P6 | Commit C1 (gobernanza + RED, sin producto) | ⏳ |
| P7 | Implementación (serializador · mapeo OC · normalizador seguro) | ⏳ |
| P8 | GREEN dirigido + suite completa + tsc + build | ⏳ |
| P9 | Commit C2 + deploy + generación nueva | ⏳ |
| P10 | E2E-01…13 runtime + recertificación R-153 (addendum) | ⏳ |
| P11 | Evidencia + limpieza + C3 | ⏳ |
| P12 | Walkthrough UAT-01…07 (retry) + paquete C4 + §81 + pregunta al propietario | ⏳ |

## CHECKLIST (AC → tarea → archivo → test → evidencia)

| AC | Tarea | Archivo | Test | Evidencia | Estado |
|---|---|---|---|---|---|
| 01-07 | T2 (serializador) | `OperationFormPage.tsx`, helper | `f01.payloadContract` (import) + unit | E2E-01/03 + controles | ⏳ |
| 08-13 | T3 (OC) | `OperationFormPage.tsx` | `f01.payloadContract` (OC) | E2E-02 | ⏳ |
| 14-18 | T2/T4 | `OperationFormPage.tsx` | `f01.payloadContract` (recepción) | E2E-05 + R-153 | ⏳ |
| 19-26 | T4 (errores) | `Toast.tsx` + `OperationFormPage.tsx` | `f01.errorRendering` + unit normalizador | E2E-04 | ⏳ |
| 27-34 | T5 | — | suites R-153 (PG, CI) | E2E-06…10/12 + addendum | ⏳ |
| 35-40 | T5 | — | E2E-13 | runtime | ⏳ |
| 41-47 | T6 | — | vitest/tsc/build + ES/EN + móvil | capturas | ⏳ |
| 48-54 | T1 | — | — | paquete C1…C4 | ⏳ |

## TAREAS

| ID | Contenido | Archivos | Test | Depende | Estado |
|---|---|---|---|---|---|
| T1 | Gobernanza: dedup, trazas, spec, clarificaciones, plan/checklist/tareas, RED | `audit/ga-f01/**`, tests RED | — | — | ▶ |
| T2 | Serializador `egg_storage_records` (helper + uso en `onSubmit`) | `operationPayload.ts` (nuevo), `OperationFormPage.tsx` | payload | T1 | ⏳ |
| T3 | Mapeo OC canónico (código + tipado; ramas no-cría y cría) | `OperationFormPage.tsx` | payload | T1 | ⏳ |
| T4 | Normalizador seguro `getErrorMessage` + uso en catch | `Toast.tsx`, `OperationFormPage.tsx` | unit + render | T1 | ⏳ |
| T5 | GREEN + regresión (dirigido, suite, tsc, build, R-153) | — | todas | T2-T4 | ⏳ |
| T6 | C2 + deploy + E2E-01…13 + recertificación + evidencia + limpieza + C3 | `audit/ga-f01/**` | runtime | T5 | ⏳ |
| T7 | Retry UAT-01…07 + paquete C4 + §81 | `audit/ga-r153/uat/**` | runtime | T6 | ⏳ |

## AMPLIACIÓN F-01e (retry GA-UAT-09 · 2026-09-13)

Anexo: `GA_F01E_SUBSANACION_ANNEX.md` · RED: `evidence/f01e/` · clarificación C29 · spec AC63-65.

| Fase | Contenido | Estado |
|---|---|---|
| C2e | Gobernanza F-01e (anexo, C29, AC63-65, RED runtime + unit 1×) | ✅ |
| C2f | Implementación D1 (`derivedHouseId` recepción) + GREEN local | ⏳ |
| C3 | Runtime post-fix (rerun 7/7) + evidencia + cierre | ⏳ |

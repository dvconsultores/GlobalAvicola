# GA-FE-06 · TAREAS

| ID | Tarea | Depende de | Evidencia | Estado |
|---|---|---|---|---|
| T1 | Preflight + congelar bundle de entrada | — | commit HEAD, curl bundle | ✔ |
| T2 | Baselines frontend/backend PG-libre | T1 | salidas de tsc/build/vitest/pytest | ✔ |
| T3 | Lecturas canónicas + dedup | T1 | notas de reconciliación | ✔ |
| T4 | Gobernanza: reconciliation, traces, matrices, spec, clarificaciones, plan, checklist, tasks | T3 | `audit/ga-fe-06/*` | ✔ |
| T5 | RED vitest contrato de alta | T4 | `gaFe06.lotFormContract.test.tsx` fallando | ✔ |
| T6 | RED runtime pre-fix (captura payload real sin PLD/área) | T1 | `evidence/red/*` + doc RED | ✔ |
| T7 | Commit C1 (gobernanza + RED) + push | T5,T6 | hash + local==remoto | ✔ (`10f91db`) |
| T8 | Implementación mínima del formulario y detalle | T7 | diff | ✔ |
| T9 | GREEN dirigido + gates completos | T8 | salidas; 273+n verdes | ✔ (278/278) |
| T10 | Commit C2 + push + despliegue | T9 | hash; bundle nuevo congelado | ✔ (`23ca59a` · `index-DcqmSs-R.js`) |
| T11 | Fixtures runtime (actores/áreas/BU) | T10 | ledger | ✔ |
| T12 | E2E-01…16 + regresiones | T11 | evidence runtime/red/capturas | ✔ |
| T13 | Relectura SLA al cierre | T12 | notificaciones o PENDING_SCAN_WINDOW | ✔ (relecturas 14:06/14:15 → **PENDING_SCAN_WINDOW**) |
| T14 | Higiene §101 | T12 | ledger actualizado | ✔ |
| T15 | Evidencia de cierre (runtime/red/capturas/ledger/reconciliación) | T13,T14 | docs | ✔ |
| T16 | Certificación + addendum + catálogo + paquete UAT | T15 | docs | ✔ |
| T17 | Commit C4 + verificación final + informe §FINAL + STOP | T16 | hash; worktree limpio | ✔ (`84080c3`) |

## GA-FE-06-A · remediación de seguridad (subhallazgo R-183 absorbido)

| ID | Tarea | Estado |
|---|---|---|
| A1 | Preflight + lecturas canónicas (AC20/36, tenancy, Area, create/update) | ✔ |
| A2 | Dedup R-183 ⇒ ABSORBED_IN_R182 | ✔ |
| A3 | Corrección de estado (R-182 SECURITY_REMEDIATION_REQUIRED · GA-FE-06 PARTIAL · UAT_READY NO) | ✔ |
| A4 | Enmienda de spec + SEC-AC01…08 + checklist | ✔ |
| A5 | RED: suite PG `test_lot_area_ownership.py` + captura runtime pre-fix (201/200/500) | ✔ |
| A6 | Commit C5 gobernanza + push | ✔ (`b48e4ea`) |
| A7 | Implementación: validador canónico en alta y edición (sin migración/permisos/endpoints) | ✔ |
| A8 | GREEN local: gates backend PG-libre + frontend (vitest/tsc/build) | ✔ (7/7 · 278/278 · 0 · PASS) |
| A9 | Commit C6 + push + despliegue automático + congelar generación | ✔ (`69d0c95` · observado) |
| A10 | E2E runtime: negativos (alta/edición/inexistente), positivos (misma empresa/NULL), matriz tenant/BU/RBAC, selector desktop/móvil, SLA datos+regla | ✔ |
| A11 | Higiene: revokes, BU OFF, usuarios/roles off, áreas baja, credenciales destruidas | ✔ |
| A12 | Recertificación R-182 completa + evidencias + addendum auditoría + backlog | ✔ |
| A13 | Commit C7 evidencia + verificación final + informe §41 + STOP | ○ |

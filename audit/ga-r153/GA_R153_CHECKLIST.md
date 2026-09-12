# GA-R153 · CHECKLIST (AC → tarea → archivo → test → evidencia)

| AC | Tarea | Archivo | Test | Evidencia runtime | Estado |
|---|---|---|---|---|---|
| 01-03 | T01 | decisión + backlog | — | doc | ⏳ |
| 04-05 | T02 | `operations/service.py` + `OperationFormPage` | `r153.importLotOptional` + PG | E2E-01/02 | ⏳ |
| 06-08 | T03 | `lots/service.py` (hook) | PG `test_r153` | E2E-03 | ⏳ |
| 09-11 | T04 | `lots/service.py` (generador) | PG secuencia/concurrencia | E2E-09 | ⏳ |
| 12-15 | T03 | mapeo | PG campos | E2E-04 | ⏳ |
| 16-22 | T03 | (sin cambios de saldo) | PG población/recepción | E2E-05/06 | ⏳ |
| 23-27 | T03/T04 | hook + generador | PG idempotencia/legado | E2E-07/08 | ⏳ |
| 28-32 | T03 | hook (rutas) | PG estados | E2E-10 | ⏳ |
| 33-35 | — | sin cambios | regresión lotes | E2E-11 | ⏳ |
| 36-43 | T05 | FE form/detalle/i18n | `r153.importLotOptional` | E2E-16 | ⏳ |
| 44-49 | T02/T03 | guardas de unidad/tenant | 403/404 spots | E2E-12..15 | ⏳ |
| 50-57 | T06 | — | suites + spots | regresión | ⏳ |

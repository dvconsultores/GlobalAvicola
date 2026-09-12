# GA-R153 · TAREAS

Fecha: 2026-09-12. Implementación SOLO tras C1.

| ID | Contenido | Archivos | Test | Depende | Estado |
|---|---|---|---|---|---|
| T01 | Formalización OD-25 + registro (AOD-25→OD-25) + backlog R-153 | `audit/ga-r153/**`, `AUDIT_OWNER_DECISIONS_REQUIRED.md`, `REMEDIATION_BACKLOG.md` | — | — | ▶ |
| T02 | Gate de lote: `grandparent_import` opcional (backend) + unidad de cadena `grandparent` | `backend/app/operations/service.py` | PG + runtime | T01 | ⏳ |
| T03 | Hook de aprobación: `crear_lote_de_importacion_si_procede` en ambas rutas | `backend/app/lots/service.py`, `backend/app/review/service.py` | PG `test_r153` | T02 | ⏳ |
| T04 | Generador `L-GP-{año}-{nn}` (lock asesor + savepoint/reintento) | `backend/app/lots/service.py` | PG concurrencia | T03 | ⏳ |
| T05 | Frontend: lote opcional en import + nota + enlace/pendiente + i18n | `OperationFormPage.tsx`, `OperationDetailPage.tsx`, `translation.json`, test nuevo | vitest | — | ⏳ |
| T06 | Regresión local completa (pytest declarado, Vitest, tsc, build) | — | todas | T02-T05 | ⏳ |
| T07 | C1 gobernanza + RED | `audit/ga-r153/**`, tests RED | — | T01 | ⏳ |
| T08 | C2 implementación + push | T02-T05 | — | T06 | ⏳ |
| T09 | Deploy + E2E-01…16 + capturas | `/tmp` scripts | — | T08 | ⏳ |
| T10 | Limpieza + ledger + red saneada | — | — | T09 | ⏳ |
| T11 | Evidencia backend/frontend/concurrencia + reconciliación + certificación | `audit/ga-r153/**` | — | T09/T10 | ⏳ |
| T12 | C3 evidencia + masters + UAT READY | — | — | T11 | ⏳ |

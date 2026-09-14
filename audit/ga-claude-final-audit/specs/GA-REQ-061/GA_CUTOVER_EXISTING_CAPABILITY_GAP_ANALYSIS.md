# GA-REQ-061 · GAP ANALYSIS — CAPACIDADES EXISTENTES vs CUTOVER

HEAD `7a158d5` · Verificación por grep/lectura directa (2026-09-14). `CURRENT` = existe hoy; `PROPOSED` = requerido por GA-REQ-061.

## Matriz

| CAPABILITY | CURRENT_CODE | CURRENT_SPEC/TEST | REUSABLE | PARTIAL | GAP | PROPOSED_ACTION | DEPENDENCY |
|---|---|---|---|---|---|---|---|
| Companies / tenancy | `app/tenancy.py` (`verificar_pertenencia`, BR-07); R-139/OD-14 | suites T2 | ✅ | — | — | reutilizar tal cual | — |
| Business Units (empresa) | `app/business_units/service.py` (`unidades_de_alcance_productivo`) | OD-16/GA-FE-02-D certificado | ✅ | — | — | APPLY = operación productiva ⇒ BU OFF DENY | — |
| Grants usuario↔BU | `user_business_units` + effective | R-188/BU-D10 | ✅ | — | — | exigir grant en create/validate/apply | — |
| RBAC permisos | patrón `modulo:accion` (p.ej. `approvals:approve`, R-184) | suites RBAC | ✅ | — | falta módulo cutover | PROPOSED `cutover:{create,validate,approve,apply}` + `corrections` existente | catálogo al implementar |
| Lot + lifecycle | `app/masters/models.py:278` (`lot_code` UNIQUE, `activation_type`, `status`) | R-153/OD-25 | ✅ | — | — | reutilizar; NO tocar secuencias | — |
| LotPhase | `app/lots/models.py:14` | — | ✅ | — | fase al corte en snapshot | usar fase real del opening | — |
| **OpeningBalance (R-67)** | `app/lots/models.py:37`; `service.py:616/738`; `router.py:99` `POST /lots/activate-manual` | `audit/remediation/R-67-OPENING-BALANCE-CERTIFICATION.md` (CERTIFIED) | ✅ | ✅ | sin batch/aprobación/checksum/UNKNOWN/source/legacy; 1 por lote (`unique`) | **extender** (ver reconciliación) — sin concepto paralelo | R-67 |
| Balance vivo consulta opening | `reports/service.py:193` (fórmula saldo vivo; RC-08=A) | R-67 cert §3 | ✅ | — | — | base del cálculo post-cutover | — |
| Recepción (eventos) | `app/operations/models.py` (OperationalEvent + BirdMovement) | T3-T6 | ✅ | — | — | prohibido crear recepción ficticia | — |
| Mortalidad/descarte | BirdMovement/eventos | GA-REM-021 certificado | ✅ | — | semántica UNKNOWN | post-cutover normal; opening con status | — |
| Alimento | `FeedMovement` | certificado | ✅ | — | UNKNOWN en opening | idem | — |
| Pesajes | eventos peso/promedio | GA-FE-07/G-05 | ✅ | — | último pesaje en snapshot | campos opening | — |
| Producción/reproductoras | eventos producción + `EggMovement` | certificado | ✅ | — | acumulados opening parciales | idem | — |
| Incubadora | `HatcheryParams`, `EggMovement`, batches (EggBatch/ChickBatch lot) | R-160/R-161/R-153 | ✅ | — | **proceso EN CURSO** (carga activa) sin modelado de opening | diseñar opening de incubación (no asumir Lot) | auditoría fina al implementar |
| Nacimientos | ChickBatch | R-153 | ✅ | — | acumulado opening | campo snapshot | — |
| Transferencias | EggBatch/ChickBatch/transfers | certificado | ✅ | — | `outbound/inbound` opening | campos | — |
| Correcciones | `app/corrections/` framework | P1-12/R-192 | ✅ | — | correction de opening | reutilizar patrón (nueva entidad hija) | — |
| Audit log | `audit_accion` (`helpers.py`) | T8 (P1-12/R-198/R-219) | ✅ | — | eventos cutover | mapear CREATE/UPLOAD/VALIDATE/SUBMIT/APPROVE/REJECT/APPLY/CORRECT | — |
| Import/Excel | **no existe parser** (sin `openpyxl`/`pandas` en deps) | — | ❌ | — | TODO el pipeline | PROPOSED (nueva dependencia en su tranche) | — |
| File upload/storage | endpoints UploadFile existentes (evidencia) | certificado | ✅ | — | storage del archivo + sha256 | reutilizar patrón | — |
| Aprobaciones multinivel | workflow review/approvals | P-07/T2 | ✅ | — | batch approval | reutilizar patrón de estados | T10 no bloquea |
| Reports/KPIs | `reports/service.py`; IPE OD-22 | certificado | ✅ | — | Opening/Post/Lifetime | PROPOSED campos de origen | — |
| FE admin flows | patrón maestros/usuarios (T9) | certificado | ✅ | — | pantalla Cargas Iniciales | PROPOSED fase FE | — |
| SAP refs | `sap_references` | fase SAP | ✅ | — | — | solo referencia real; no fabricar | — |

## Veredicto

- **Reutilizable**: tenancy/BU/grants/RBAC framework, Lot/lifecycle, motor operacional completo, correcciones, auditoría, uploads, reportes.
- **Parcial (extender, no reemplazar)**: `OpeningBalance`/`activate_manual` (R-67) — pieza central reutilizable con extensiones (batch, aprobación, checksum, semántica UNKNOWN, provenance, correcciones).
- **Ausente (construir)**: pipeline Excel→staging→validate→preview→apply; `CutoverBatch`/items; apply transaccional idempotente; UI Cargas Iniciales.
- Sin conflictos con T10-T13 (ver placement).

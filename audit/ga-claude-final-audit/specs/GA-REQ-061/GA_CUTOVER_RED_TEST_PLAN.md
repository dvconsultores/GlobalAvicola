# GA-REQ-061 · PLAN DE PRUEBAS RED (futuro — NO ejecutar en esta fase)

Patrón del repo: `backend/tests/test_ga_req_061_cutover_*.py` (fixtures estilo `test_traceability_ownership.py`: `client`, `auth_headers`, `seeded_ids`, `motor`; limpieza por PREFIJO). FE jsdom en la fase FE (`r061.cutover*.test.tsx`). Cada RED debe fallar en el HEAD de su tranche por la causa exacta, con controles verdes que la suite conserva.

## RED (22)

| ID | Caso | Tipo |
|---|---|---|
| CUT-RED-01 | Lectura cross-company de batch/items ⇒ denegada | tenancy |
| CUT-RED-02 | Modificación cross-company ⇒ denegada | tenancy |
| CUT-RED-03 | APPLY cross-company ⇒ denegado | tenancy |
| CUT-RED-04 | BU OFF (incluso global actor) ⇒ APPLY denegado | OD-16 |
| CUT-RED-05 | Usuario sin grant de BU ⇒ denegado | grants |
| CUT-RED-06 | Master inactivo en creación de lote nuevo ⇒ error | OD-21 |
| CUT-RED-07 | Import con filas inválidas ⇒ 0 aplicados (42/38/4/0) | atomicidad |
| CUT-RED-08 | Mismo checksum re-subido ⇒ sin duplicados | idempotencia |
| CUT-RED-09 | Re-APPLY del mismo batch ⇒ 409 determinista | idempotencia |
| CUT-RED-10 | APPLY concurrente (dos sesiones) ⇒ exactamente uno | concurrencia |
| CUT-RED-11 | UNKNOWN convertido a 0 en API/reporte ⇒ prohibido | semántica |
| CUT-RED-12 | Opening live = saldo vivo (10.000 − 35 = 9.965) | semántica |
| CUT-RED-13 | Restar historical de nuevo (10.000−500−35) ⇒ imposible por diseño | semántica |
| CUT-RED-14 | Post-cutover mortality acumula solo eventos > corte (535 lifetime) | semántica |
| CUT-RED-15 | UPDATE de opening APPLIED ⇒ denegado | inmutabilidad |
| CUT-RED-16 | DELETE de opening APPLIED ⇒ denegado | inmutabilidad |
| CUT-RED-17 | Corrección sin razón ⇒ rechazada | correcciones |
| CUT-RED-18 | Corrección que borra/ignora eventos posteriores ⇒ rechazada (9.900 ⇒ 9.865) | correcciones |
| CUT-RED-19 | `template_version` no soportada ⇒ error | Excel |
| CUT-RED-20 | SAP reference fabricada ⇒ rechazada (solo real) | SAP |
| CUT-RED-21 | Lote ya existente ⇒ no se duplica al relacionar opening | lotes |
| CUT-RED-22 | Colisión de `legacy_lot_code` ⇒ error | lotes |

## Controles verdes (6)

| ID | Control |
|---|---|
| CUT-CTL-01 | Lote nativo permanece sin cambios |
| CUT-CTL-02 | Mortalidad nativa (post-cutover normal) sigue operando |
| CUT-CTL-03 | Pesaje normal funciona |
| CUT-CTL-04 | Transferencia normal funciona |
| CUT-CTL-05 | Reporting nativo sin cambios (sin filas opening) |
| CUT-CTL-06 | RBAC existente sigue válido (permisos previos intactos) |

## Notas de diseño

- Los casos de semántica (12/13/14) **deben** existir como prueba automatizada obligatoria (mandato §13): el core `current_live`, `post_cutover_mortality`, `lifetime_mortality` con el ejemplo 10.000/500/35.
- CUT-RED-07 y CUT-RED-10 exigen infraestructura de concurrencia/transacción con PG (fixture del repo lo permite).
- Errores estructurados (§4 del doc Excel) se prueban por `error_code` exacto (p.ej. `MASTER_NOT_FOUND`, `BU_DISABLED`).
- FE (fase posterior): preview sin efectos, apply bloqueado con errores, UNKNOWN visible ≠ 0, i18n ES/EN.

# GA-REQ-061 · PLAN DE SENSIBILIDAD (futuro — NO ejecutar en esta fase)

Regla vigente (AOD-29 Clar. 01 + AE-42): antes de mutar, `IMPLEMENTATION_COMMIT=<sha>`; `HEAD == IMPLEMENTATION_COMMIT`; worktree limpio; restaurar SIEMPRE `git restore --source="$IMPLEMENTATION_COMMIT" -- <archivo>` (nunca checkout implícito); registrar `RESTORE_SOURCE` y `POST_RESTORE_RESULT`; post-mutation GREEN.

| Mutación | Revert de | Debe teñir | Rojo esperado |
|---|---|---|---|
| S1 | guard de tenancy en batch | CUT-RED-01/02/03 | cross-company pasa ⇒ rojos |
| S2 | guard BU-empresa (OD-16) en apply | CUT-RED-04 | apply con BU OFF |
| S3 | check de grant de BU | CUT-RED-05 | usuario sin grant opera |
| S4 | protección de duplicado (checksum/estado) | CUT-RED-08/09 | duplica/success en re-apply |
| S5 | atomicidad (permitir parcial) | CUT-RED-07 | 38 aplicados con 4 malos |
| S6 | mapeo UNKNOWN→0 | CUT-RED-11 | UNKNOWN leído como 0 |
| S7 | resta doble de historical | CUT-RED-13/12 | current_live 9.465 (falso) |
| S8 | permitir edición de APPLIED | CUT-RED-15/16 | update/delete pasa |
| S9 | razón opcional en corrección | CUT-RED-17 | corrección sin razón pasa |
| S10 | lock/estado de concurrencia | CUT-RED-10 | doble apply ambos 200 |

Notas:
- S7 es la mutación *semántica de oro*: debe romper EXACTAMENTE el test del ejemplo canónico (10.000 − 500 − 35 prohibido).
- Cada mutación restaura desde el SHA de implementación de T14 y re-ejecuta la suite dirigida; clústeres multi-test se documentan (patrón S1 de R-196/S4 de R-195).
- La evidencia va a `specs/GA-REQ-061/evidence/sensibilidad/` en esa tranche.

# R-200 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

| AC | Enunciado (resumen) | Sección SPEC | Prueba backend (`test_r200_refresh_token_as_access.py`) | E2E runtime | Evidencia esperada | Estado |
|---|---|---|---|---|---|---|
| AC01 | refresh como Bearer en `/me` → `401` | §6, §22 | `RED-01 test_r200_01_un_refresh_token_no_autentica_una_ruta_protegida` | E2E-01 | `401` + `detail` | ☐ |
| AC02 | refresh como Bearer en `/users` (super admin) → `401` | §6, §16 | `RED-02 test_r200_02_un_refresh_token_no_autentica_una_ruta_con_permiso` | E2E-02 | `401` (no `403`) | ☐ |
| AC03 | JWT sin `type` → `401` | §6 | `RED-03 test_r200_03_un_token_firmado_sin_tipo_se_rechaza` | — | `401` | ☐ |
| AC04 | JWT con `type` desconocido → `401` | §6 | `RED-04 test_r200_04_un_token_de_tipo_desconocido_se_rechaza` | — | `401` | ☐ |
| AC05 | el access sigue autenticando | §25 | `CTL-05 test_r200_05_el_access_token_sigue_autenticando` | E2E-03 | `200` | ☐ |
| AC06 | renovación intacta | §25 | `CTL-06 test_r200_06_el_flujo_de_renovacion_sigue_intacto` + `test_r43_la_sesion_continua_con_el_acceso_caducado` | E2E-04 | `200` + nuevo access válido | ☐ |
| AC07 | access no sirve para renovar | §5 | `CTL-07 test_r200_07_un_access_token_sigue_sin_servir_para_refrescar` (= `test_r43_un_refresco_invalido_se_rechaza`) | — | `401` | ☐ |
| AC08 | `switch-company` emite par válido | §25 | `CTL-08 test_r200_08_el_par_de_switch_company_sigue_siendo_valido` (+ `test_el_contexto_sobrevive_a_la_renovacion`) | — | `200`/`200` | ☐ |
| AC09 | sin asiento ni usuario de auditoría | §18 | aserción en RED-01 | — | `audit_logs` sin fila; `get_current_audit_user()` `None` | ☐ |
| AC10 | ventanas 30 min / 7 d documentadas | §5 | `DOC-10 test_r200_10_las_ventanas_de_los_dos_tokens_quedan_fijadas` | — | deltas de `exp` | ☐ |
| AC11 | regresión vecina | §27 | suites | — | log | ☐ |
| AC12 | 0 migración/endpoint/permiso/FE | §10 | — | — | diff | ☐ |
| AC13 | nota de interacción con `GA-REM-003` | §8, §13 | — | — | registro/backlog | ☐ |
| AC14 | sensibilidad | §27 | M1 | — | tabla | ☐ |

Trazabilidad: `GA-REM-003 §Alcance 1` → AC01…AC04 · `GA-REM-003 AC01/AC07` → AC06, AC08 · `R-43` → AC06, AC07 · `R-54` → AC08 · `R-83` → AC09.

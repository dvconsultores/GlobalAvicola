# R-199 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

Convención: `RED-nn` = prueba roja en HEAD por el defecto · `CTL-nn` = control verde antes y después · `E2E-nn` = sonda runtime (C3) · Estado ☐ hasta la evidencia.

| AC | Enunciado (resumen) | Sección SPEC | Prueba backend (`test_r199_global_authority_fabrication.py`) | E2E runtime | Evidencia esperada | Estado |
|---|---|---|---|---|---|---|
| AC01 | alta de rol de inquilino con `("*", all)` → `403`, nada escrito | §6, §22 | `RED-01 test_r199_01_crear_rol_de_inquilino_con_comodin_global_se_rechaza` | E2E-01 | `403` + recuento `roles`/`permissions` igual | ☐ |
| AC02 | edición de rol de inquilino con el par → `403`, permisos intactos | §6, §22 | `RED-02 test_r199_02_editar_rol_de_inquilino_para_inyectar_el_comodin_se_rechaza` | E2E-02 | `403` + permisos idénticos | ☐ |
| AC03 | rol de inquilino envenenado no asignable → `403` | §6, §16 | `RED-03 test_r199_03_un_rol_de_inquilino_envenenado_no_es_asignable` | E2E-03 (condicional `C-06`) | `403` + `role_id` intacto | ☐ |
| AC04 | usuario con rol envenenado: `/me.is_super_admin=false`, `switch-company 403`, `/users` sólo su empresa | §6, §13 | `RED-04 test_r199_04_un_rol_de_inquilino_envenenado_no_confiere_autoridad_global` | E2E-04 | JSON de `/me`, `403`, listado acotado | ☐ |
| AC05 | renovación no honra `company_id` ajeno para ese usuario | §6, §25 | `RED-05 test_r199_05_la_renovacion_no_honra_un_contexto_ajeno_con_rol_envenenado` | — (local) | `effective_company_id == A` | ☐ |
| AC06 | módulo fuera de catálogo → `422` | §22 | `RED-06a test_r199_06_modulo_fuera_de_catalogo_es_422` | E2E-05a | `422` | ☐ |
| AC07 | acción inválida → `422` (hoy `500`) | §22 | `RED-06b test_r199_06_accion_invalida_es_422_y_no_500` | E2E-05b | `422` | ☐ |
| AC08 | `scope_type` inválido → `422` | §22 | `RED-06c test_r199_06_alcance_invalido_es_422` | E2E-05c | `422` | ☐ |
| AC09 | la autoridad global sigue creando plantillas con el par | §6, §25 | `CTL-07 test_r199_07_la_autoridad_global_sigue_creando_plantillas_con_comodin` | — (no se crea plantilla en runtime) | `201`, `company_id NULL` | ☐ |
| AC10 | rol ordinario con `scope_type:'all'` sigue creándose y asignándose; no es super admin | §6, §9 | `CTL-08 test_r199_08_el_rol_de_inquilino_ordinario_se_crea_asigna_y_no_es_global` | E2E-06 | `201`/`200`, `is_super_admin=false` | ☐ |
| AC11 | comodín de módulo con `scope_type='company'` admitido, sin autoridad global | §16, `C-03` | `CTL-09 test_r199_09_el_comodin_de_modulo_con_alcance_de_empresa_sigue_admitido` | — | `201`, `tiene_permiso` true, `is_super_admin` false | ☐ |
| AC12 | intento denegado registrado (`C-05`) | §18 | aserción dentro de RED-01/RED-02 (`audit_logs` con `comments` de rechazo) | E2E-01 (`GET /audit`) | fila `PERMISSION_CHANGE` con comentario | ☐ |
| AC13 | denegación sin escritura parcial | §17 | aserciones de recuento en RED-01, RED-02, RED-06a/b/c | E2E-01/05 | recuentos iguales | ☐ |
| AC14 | regresión vecina en verde | §27 | suites `test_role_tenancy`, `test_role_administration`, `test_rbac`, `test_session_payload`, `test_user_tenant_isolation`, `test_multicompany_isolation` | — | log de suite | ☐ |
| AC15 | sin migración/permiso/endpoint; 0 FE | §10, §23 | — | — | `git diff --stat` | ☐ |
| AC16 | inventario §12 ejecutado y registrado | §12 | — | E2E-07 | salida SQL (0 filas esperadas) | ☐ |
| AC17 | `get_company_filter` retirado (`C-07`) | §10 | `CTL-10 test_r199_10_no_queda_atajo_legado_sin_filtro` (estático: `not hasattr(app.auth.security, "get_company_filter")`) | — | diff + grep | ☐ |
| AC18 | sensibilidad 6/6 | §27 | tabla de mutaciones | — | certificación | ☐ |

Trazabilidad de decisiones: `OD-13.c` → AC01, AC02, AC03, AC09 · `OD-13.b` → AC02 (`C-02`), AC04 · `GA-REM-002 AC15` → AC03 · `OD-14.b` → AC04 · `OD-11`/`R-54` → AC05 · `GAP-16` → AC06…AC08, AC17 · `GA-REM-032 AC03` → AC12 · `GA-REM-040 §18` (0 mutación al denegar) → AC13.

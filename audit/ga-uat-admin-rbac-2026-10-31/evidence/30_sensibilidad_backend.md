# 30 — Sensibilidad / mutación del backend (SPEC 013, administración & RBAC)

**Impl SHA (base de las mutaciones y de la restauración):** `99d152eac19cb4db0096f3041769d8d309b3522e`
(`fix(admin-rbac): SPEC 013 - UAT Administracion/RBAC (AR-01b..AR-23 …)`, `main`)
**Fecha:** 2026-10-31 · **Ámbito mutado:** `backend/app/auth/security.py`, `backend/app/auth/service.py`
**Ejecución:** estrictamente secuencial, una mutación a la vez, una sola corrida de `run_tests.sh` en vuelo.

## Suite objetivo

```
backend/scripts/run_tests.sh \
  tests/test_uat_admin_users_identity.py tests/test_uat_admin_roles_lifecycle.py \
  tests/test_uat_admin_escalation.py tests/test_uat_admin_dynamic_authority.py \
  tests/test_uat_admin_bu_dynamic.py tests/test_role_administration.py \
  tests/test_role_tenancy.py tests/test_r199_global_authority_fabrication.py
```

**BASELINE (sin mutar, `99d152e`):** `69 passed, 7 warnings in 67.80s` → **0 failed**. Criterio de «DETECTADA»: al menos un test de esta suite falla con la mutación aplicada.

## Procedimiento de restauración (idéntico para las seis)

```bash
git restore --source=99d152e -- backend/app/auth/service.py     # o security.py
git diff --stat 99d152e -- backend/app/auth/service.py          # debe estar vacío
```

Sin `git checkout`, sin `git stash`, sin `git reset`, sin commit/push/ramas.

## Resultados

| # | Mutación (defecto reintroducido) | Cambio aplicado | Resumen pytest | Tests que la detectan (hasta 8) | Veredicto |
|---|---|---|---|---|---|
| **M1** | Rol **inactivo** vuelve a conceder autoridad (AR-01 / AC-RL-02) | `security.py` · `get_current_user`: `if user.role.is_active and user.role.permissions:` → `if user.role.permissions:` | `2 failed, 67 passed, 7 warnings in 67.76s` | `test_uat_admin_roles_lifecycle.py::test_ac_rl_02_un_rol_inactivo_no_confiere_permisos_ni_autoridad`<br>`test_uat_admin_dynamic_authority.py::test_da_04_rol_inactivo_por_sql_no_confiere_y_se_recupera_al_reactivar` | **DETECTADA** |
| **M2** | Sin regla de subconjunto al asignar rol (AC-ES-01 / DR-3) | `service.py` · `_exigir_subconjunto_de_rol`: `return` inmediato al inicio del cuerpo | `2 failed, 67 passed, 7 warnings in 67.47s` | `test_uat_admin_escalation.py::test_ac_es_01_el_alta_no_asigna_un_rol_con_permisos_que_el_actor_no_posee`<br>`test_uat_admin_escalation.py::test_ac_es_01_el_comodin_exige_comodin` | **DETECTADA** |
| **M3** | Unicidad de `username`/`email` **sensible a mayúsculas** (AC-ID-02/03, AR-05) | `service.py` · `create_user`: `func.lower(User.username)==username.lower()` → `User.username==username` y `func.lower(User.email)==email.lower()` → `User.email==email`; `update_user`: `email.lower()!=(user.email).lower()` → `email!=(user.email).strip()` y `func.lower(User.email)==email.lower()` → `User.email==email` (4 líneas) | `2 failed, 67 passed, 6 warnings in 67.78s` | `test_uat_admin_users_identity.py::test_ac_id_02_editar_con_un_email_ajeno_da_409_y_no_cambia`<br>`test_uat_admin_users_identity.py::test_ac_id_03_unicidad_insensible_a_mayusculas_y_sin_espacios` | **DETECTADA** |
| **M4** | Rol sin permisos admitido (AC-RL-05 / DR-2) | `service.py`: eliminado el `422 «El rol debe tener al menos un permiso»` en `create_role` (bloque `if not data.permissions:`) y en `update_role` (bloque `len(data.permissions)==0`) | `1 failed, 68 passed, 5 warnings in 67.88s` | `test_uat_admin_roles_lifecycle.py::test_ac_rl_05_un_rol_exige_al_menos_un_permiso` | **DETECTADA** |
| **M5** | Sin guarda de auto-acción: el actor cambia su rol o se desactiva (AC-ES-03 / DR-3, AR-08) | `service.py` · `update_user`: eliminado el bloque `if actor.get("id") == user.id:` completo (`403` por auto-cambio de `role_id` y por `is_active=false` propio) | `2 failed, 67 passed, 7 warnings in 67.61s` | `test_uat_admin_escalation.py::test_ac_es_03_nadie_cambia_su_propio_rol_ni_se_desactiva`<br>`test_uat_admin_escalation.py::test_ac_es_03_la_autoridad_global_tampoco_se_desactiva` | **DETECTADA** |
| **M6** | Desactivar por `PUT` sin `users:delete` (AC-ID-05 / AR-07) | `service.py` · `update_user`: eliminado el bloque que exige `tiene_permiso(actor, "users", "delete")` cuando `is_active is False` | `1 failed, 68 passed, 7 warnings in 67.87s` | `test_uat_admin_escalation.py::test_ac_id_05_desactivar_exige_el_permiso_de_baja` | **DETECTADA** |

**Resumen:** 6/6 mutaciones **DETECTADAS**, 0 SOBREVIVIENTES, 0 BLOCKED.

## Comprobaciones de restauración (reales)

Tras cada mutación se restauró y se verificó `git diff --stat 99d152e -- <archivo>` **vacío** (salida literal: `DIFF_VACIO_OK`, sin líneas de diff). Al cierre:

```
$ git diff --stat 99d152e -- backend/app/auth
(vacío)                                → DIFF_AUTH_VACIO_OK

$ git status --short backend/app
(vacío)                                → STATUS_BACKEND_APP_VACIO_OK
```

Suites posteriores a la restauración (misma suite objetivo):

```
BASELINE : 69 passed, 7 warnings in 67.80s
FINAL    : 69 passed, 7 warnings in 67.76s
```

## Suite objetivo final (post-restauración)

`69 passed, 7 warnings in 67.76s` → **0 failed**. El árbol de trabajo solo muestra los cambios ajenos preexistentes (`audit/qa-integral-dataset/fixtures/*.xlsx` y el directorio sin seguimiento `audit/ga-uat-admin-rbac-2026-10-31/`), que no se han tocado.

## Notas

- Cada `FAILED` corresponde a un test escrito para la regla concreta (RED de la implementación), de modo que las reglas de la SPEC 013 no son «verde por construcción»: romper la regla en el código pone el test en rojo.
- M3 agrupa los cuatro puntos de comparación de identidad porque son **una sola** regla de producto (unicidad insensible a mayúsculas, sin migración, `§4.3`); con uno solo de ellos revertido el defecto `AR-05` ya reaparece y la suite lo detecta.
- No se ha modificado ningún test, ni se ha relajado ninguna aserción para obtener verde.

# GA-CLAUDE · R-199 — CERTIFICACIÓN (C1 · C2 · C2s · C3)

Fecha: 2026-09-13 · Hallazgo **R-199** (P1 · `GAP-01` · fabricación de autoridad global desde un rol de inquilino) · Paquete `specs/R-199/` · HEAD de referencia: `62cd0e1`.

## 1 · Resumen de fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · Gobernanza + RED** | ✅ commit `32c9906` | `evidence/r199/red_c1.log` — **9 rojas por el defecto** (RED-01…06a/b/c + higiene CTL-10) y **3 controles verdes** (CTL-07/08/09); cada roja auditada línea a línea (201/200/200/True/contexto-B/201/500/201). Corrección de diseño durante C1: CTL-07 inserta el usuario directo en BD (el actor global sin contexto no crea usuarios por API) |
| **C2 · Implementación** | ✅ commit `62cd0e1` | GREEN dirigido **12/12** (`green_r199_c2.log`); suite completa **`1238/0/49`** (`full_suite_c2b.log`); vitest **314/314** (`vitest_c2.log`); 0 ficheros FE |
| **C2s · Sensibilidad** | ✅ §4 | 6 mutaciones, cada una rompe ≥1 prueba (`evidence/r199/mutations/*.log`); refuerzo de RED-05 tras M5 (`green_r199_c2s.log`) |
| **C3 · Runtime** | ⚠️ **PARCIAL** — despliegue ✅; sondas bloqueadas por credenciales ⇒ **G-06** | `Docker Push — Backend` **run 114** (`62cd0e1`) = `completed successfully` |

## 2 · Implementación (3 capas + catálogo + auditoría)

- **Escritura**: `_validar_permisos(permisos, *, rol_de_inquilino)` — catálogo cerrado (`module ∈ MODULOS ∪ {"*"}`; `action ∈ PermissionAction`; `scope_type ∈ {all, company, farm}`) + invariante `("*", "all")` prohibido en rol de inquilino — invocado **antes** de `db.add` (alta) y de `sa_delete` (edición). Rechazo `C-05`: asiento `PERMISSION_CHANGE` con `comments="rechazado: …"`, `entity_type="role"`, `entity_id` (edición) o `None` (alta), `company_id` efectivo del actor y `commit` propio (patrón `LOGIN_FAILED`; sobrevive al `403`).
- **Asignación**: `_rol_asignable` — rama de inquilino: `rol.company_id == empresa and not _es_autoridad_global(role_id)`.
- **Sesión**: `get_current_user` y `_es_super_admin` (renovación) exigen `Role.company_id IS NULL` para computar la capacidad global.
- **Esquemas**: `PermissionCreate.action: PermissionAction` (422 con forma pydantic estándar), `scope_type: Literal["all","company","farm"]`.
- **Higiene `C-07`**: `get_company_filter` retirado (`security.py` + re-export en `dependencies.py`); grep de consumidores = 0.
- **Sin** migración / endpoint / permiso nuevo / ficheros frontend (diff verificado).

## 3 · Regresión y reconciliación (honesta)

- Suite completa: **`1238 passed · 0 failed · 49 skipped`** (20m59s) — +12 respecto a la línea base = la suite nueva.
- **Reconciliación**: la primera corrida detectó 2 dependientes del contrato anterior — `test_r184_ac26_actor_global_no_bypassa_bu_off` y `test_r186_global_no_bypassa_bu_off` construían su «actor global» con un **rol de inquilino + comodín** (el propio loophole eliminado). Barrido de clase sobre los ~25 fixtures con `module="*"`: solo esos 2 usaban `company_id=a.id`; el resto ya usaba plantilla de sistema (`NULL`). Adaptados ambos a `company_id=None` preservando el propósito del test. Log intermedio `full_suite_c2.log` conserva la detección (2F) como registro.

## 4 · Sensibilidad (C2s)

| # | Mutación | Rompe |
|---|---|---|
| M1 | `create_role` sin `_validar_permisos` | RED-01, RED-06a |
| M2 | `update_role` sin `_validar_permisos` | RED-02 |
| M3 | `_rol_asignable` sin `_es_autoridad_global` | RED-03 |
| M4 | `get_current_user` sin `Role.company_id IS NULL` | RED-04 |
| M5 | `_es_super_admin` sin `Role.company_id IS NULL` | RED-05 **tras refuerzo** (ver nota) |
| M6 | catálogo de acción/alcance abierto (esquema + servicio) | RED-06b, RED-06c |

**Nota M5 (honesta)**: en la primera pasada M5 **no rompió nada** — la defensa en profundidad del resolutor (`/me` re-decide el contexto aunque el token lo estampe) la enmascaraba. Se **reforzó RED-05** afirmando también el claim del token renovado (`decode_token(access).company_id == A`): con eso, la mutación rompe (1F/11P) y sin mutación la suite queda 12/12 (`green_r199_c2s.log`). Reversión por `git checkout -- backend/app/auth` verificada tras cada mutación (worktree limpio).

## 5 · C3 · Runtime (parcial — G-06)

- **Despliegue**: `Docker Push — Backend` run 114 sobre `62cd0e1` = success (imagen `:latest` publicada; Watchtower la despliega por EX-01).
- **Bloqueo de sondas**: el entorno solo dispone de credenciales UAT-09 (Operador y Aprobador R-153, sin `users:*` y sin super) ⇒ E2E-01…07 no ejecutables sin actor de administración. **Sin fabricar evidencia**: cuestión encolada como **G-06** (credencial efímera de admin/super, o ejecución del script de sondas por el propietario).
- **Inventario §12** (roles de inquilino con el par global): requiere acceso SQL a la base de runtime — dentro de G-06 (se documentará alternativa API equivalente al resolver la credencial).

## 6 · AC (estado)

| AC | Estado |
|---|---|
| AC01–AC08 (ataques) | ✅ (RED→GREEN; 12/12) |
| AC09–AC11 (controles) | ✅ (verdes en HEAD y post-fix) |
| AC12 (asiento de rechazo) | ✅ (RED-01 lo afirma; asiento con `commit` propio) |
| AC13 (sin fila parcial) | ✅ (`_recuentos` antes/después) |
| AC14 (regresión vecinas) | ✅ (suite completa 1238/0/49) |
| AC15 (sin migración/endpoint/permiso/0 FE) | ✅ (diff) |
| AC16 (inventario §12 local y runtime) | ⚠️ local ✅ («no hay roles sembrados con el par» equivalente por suites); **runtime = G-06** |
| AC17 (`get_company_filter` retirado o justificado) | ✅ (C-07 ejecutado; grep = 0) |
| AC18 (sensibilidad) | ✅ §4 |

## 7 · Veredicto

**R-199 = `CLOSED_TECHNICALLY` · `C3_PENDING_OWNER_CREDENTIALS` (G-06).**

C1/C2/C2s completos con evidencia verificable; la certificación runtime (E2E-01…07 + inventario) se completa al resolver G-06. Sin reglas relajadas, sin cambios de producto fuera de la spec, sin migración.

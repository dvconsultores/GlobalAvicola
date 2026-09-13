# R-199 · PLAN / CHECKLIST / TAREAS

Fecha: 2026-09-13 · Base HEAD `c0b4afc` · Modo: gobernanza primero, RED antes que producto, sensibilidad tras el commit de implementación (desde la raíz del repo).

## PLAN

| Fase | Contenido | Entregable | Estado |
|---|---|---|---|
| **C1 · Gobernanza + RED** | Paquete (este directorio) · fichero de pruebas `test_r199_global_authority_fabrication.py` con RED-01…06 rojas **por el defecto** y CTL-07…09 verdes · sin producto | commit «R-199 C1: gobernanza + RED (6 rojas por defecto, 3 controles)» | ☐ |
| **C2 · Implementación** | T-02…T-06 · GREEN dirigido 9/9 · suite completa PG sin rojos nuevos (respecto al inventario `GA-GOV-03 Anexo B`) · `vitest` por política (0 ficheros FE) | commit «R-199 C2: …» | ☐ |
| **C2s · Sensibilidad** | 6 mutaciones de `RED_E2E_UAT_DESIGN §4`, cada una rompe ≥1 prueba; revertir con `git checkout` desde la raíz | tabla en la certificación | ☐ |
| **C3 · Certificación runtime** | despliegue · E2E-01…07 (sondas API con actor desechable) · inventario §12 · limpieza · `GA_CLAUDE_R199_RUNTIME_CERTIFICATION.md` · registro/backlog | commit «R-199 C3: …» | ☐ |
| **C4 · UAT** | no aplica (`C-11`); nota en el ledger del propietario con el resultado del inventario y `C-05` | — | ☐ |

Prerrequisito recomendado: `GA-GOV-03` (suite verde reproducible). Si no está, C2 documenta los rojos preexistentes con el inventario del Anexo B y demuestra 0 rojos **nuevos**.

## CHECKLIST (AC → tarea → fichero → prueba → evidencia)

| AC | Tarea | Fichero | Prueba | Evidencia | Estado |
|---|---|---|---|---|---|
| AC01, AC02, AC13 | T-02 | `auth/service.py` (`_validar_permisos`, `create_role`, `update_role`) | RED-01, RED-02 | GREEN + E2E-01/02 | ☐ |
| AC06, AC07, AC08 | T-03 | `auth/schemas.py`, `auth/service.py` | RED-06 (3 casos) | GREEN + E2E-05 | ☐ |
| AC03 | T-04 | `auth/service.py` (`_rol_asignable`) | RED-03 | GREEN + E2E-03 | ☐ |
| AC04, AC05 | T-05 | `auth/security.py` (`get_current_user`), `auth/service.py` (`_es_super_admin`) | RED-04, RED-05 | GREEN + E2E-04 | ☐ |
| AC12 | T-06 | `auth/service.py` (rama de rechazo) | RED-01/02 (aserción de auditoría) | GREEN | ☐ |
| AC09, AC10, AC11 | — | — | CTL-07, CTL-08, CTL-09 | verde antes y después | ☐ |
| AC14 | T-07 | — | suites vecinas | log de suite | ☐ |
| AC15 | T-01 | — | — | `git diff --stat` (0 FE, 0 alembic) | ☐ |
| AC16 | T-09 | — | — | salida SQL local + runtime | ☐ |
| AC17 | T-08 | `auth/security.py`, `dependencies.py` | grep | diff | ☐ |
| AC18 | T-10 | — | mutaciones | tabla de sensibilidad | ☐ |

## TAREAS

| ID | Contenido | Ficheros | Tamaño | Depende | Estado |
|---|---|---|---|---|---|
| T-01 | Gobernanza: paquete, dedup, registro; fichero RED con fixture `esc199` (PREFIJO `R199-`) y 9 pruebas; verificar que RED-01…06 fallan **en la aserción esperada** (no por fixture) | `audit/ga-claude-final-audit/specs/R-199/**`, `backend/tests/test_r199_global_authority_fabrication.py` | M | — | ☐ |
| T-02 | `_validar_permisos(permisos, *, rol_de_inquilino)`: rechaza `("*", all)` con `403` cuando `rol_de_inquilino`; invocado en `create_role` antes de `db.add(role)` y en `update_role` antes de `sa_delete` (el rol objetivo ya resuelto por `_rol_administrable`); mensaje `C-08` | `backend/app/auth/service.py:585-658` | S | T-01 | ☐ |
| T-03 | Catálogo: `PermissionCreate.action` → `PermissionAction`; `scope_type` → `Literal["all","company","farm"]`; `module` ∈ `MODULOS ∪ {"*"}` en `_validar_permisos` (`422` vía `HTTPException`) | `backend/app/auth/schemas.py:201-205`, `service.py` | S | T-02 | ☐ |
| T-04 | `_rol_asignable`: rama de inquilino → `rol.company_id == empresa and not await self._es_autoridad_global(role_id)` | `backend/app/auth/service.py:116-142` | XS | T-01 | ☐ |
| T-05 | Sesión: `get_current_user` computa `is_super_admin` sólo si `user.role.company_id is None`; `_es_super_admin` añade `Role.company_id.is_(None)` al `where` | `backend/app/auth/security.py:106-120`, `service.py:225-239` | XS | T-01 | ☐ |
| T-06 | Registro del intento (`C-05`): en la rama de rechazo de T-02, `audit_accion(PERMISSION_CHANGE, comments=…)` + `commit` propio, sólo si el actor tiene empresa efectiva | `backend/app/auth/service.py` | S | T-02, C-05 | ☐ |
| T-07 | GREEN: dirigido (`pytest tests/test_r199_global_authority_fabrication.py`), vecinas (`test_role_tenancy`, `test_role_administration`, `test_rbac`, `test_session_payload`, `test_user_tenant_isolation`, `test_multicompany_isolation`), suite completa PG | — | S | T-02…T-06 | ☐ |
| T-08 | Higiene `C-07`: retirar `get_company_filter` y su re-exportación; grep de consumidores = 0 | `backend/app/auth/security.py:170-178`, `backend/app/dependencies.py` | XS | T-01 | ☐ |
| T-09 | Inventario §12 (local con la base de pruebas; runtime tras el despliegue, de solo lectura); resultado en la certificación; `C-06` si `> 0` | — | XS | C3 | ☐ |
| T-10 | Sensibilidad: 6 mutaciones, cada una ≥1 prueba rota; revertir con `git checkout -- backend/app/auth` desde la raíz | — | S | T-07 | ☐ |
| T-11 | C3: despliegue, actor desechable (super admin situado en empresa 1 crea rol `R199-AdminEmpresa` con `users:read/create/update` y usuario `r199_admin`), E2E-01…07, limpieza (desactivar usuario y rol), evidencia `evidence/r199/*.json`, `GA_CLAUDE_R199_RUNTIME_CERTIFICATION.md`, actualización de `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md` y `REMEDIATION_BACKLOG.md` | `audit/ga-claude-final-audit/**` | M | T-07 | ☐ |

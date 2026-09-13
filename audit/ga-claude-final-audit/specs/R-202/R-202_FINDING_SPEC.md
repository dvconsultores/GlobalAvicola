# R-202 · FINDING + SPEC (COMPACTO) — RESTABLECIMIENTO DE CONTRASEÑA POR ADMINISTRADOR SIN CONTEXTO DE EMPRESA

| Campo | Valor |
|---|---|
| **ID** | **R-202** · P2 · no bloquea (superficie de control acotada; corregir antes de delegar `users:update`) · Estado `SPEC_READY` |
| **Origen** | GAP-04 (informe D A.24 #7/D.7) · Registro G-13 · HEAD `c0b4afc` · 2026-09-13 |
| **GA-REM** | a asignar; siguiente libre GA-REM-043 · Sin migración/endpoint/permiso nuevo · UAT: no |

## 1 · Contexto

`POST /users/{id}/password` (restablecimiento por administrador) en `auth/service.py:434-455`: el objetivo se busca **sin empresa** (`select(User).where(id)`) y la autoridad para operar es `is_super_admin` (comentario del propio código reconoce la deuda de migrar a `users:update`). Viola `OD-14.d` (superficie `CONTROL` de inquilino operada sin contexto) y deja al administrador de empresa (con `users:update`) sin poder restablecer contraseñas de su ámbito.

## 2 · Evidencia

`auth/service.py:434-436,443-455,480`; tests `test_p013_password.py::test_t012_05` (operador 403), `::test_t012_06` (super admin misma empresa); **sin test** de super admin sin contexto contra otra empresa ni de `users:update` de la empresa.

## 3 · Causa raíz

Ruta anterior a OD-14/`_usuario_alcanzable` que nunca migró al patrón contextual del resto de `auth`.

## 4 · Impacto

Restablecimiento transversal posible para la autoridad global sin contexto; administrador de empresa imposibilitado; auditoría con `company_id` del objetivo (`:480`) aunque el actor no tenga contexto.

## 5 · Comportamiento actual → esperado

| Caso | Hoy | Esperado |
|---|---|---|
| Super admin sin contexto, objetivo de otra empresa | 200 (restablece) | **4xx fail-closed** (sin contexto no hay ámbito) |
| Admin de empresa con `users:update`, objetivo de su empresa | 403 | **200** |
| Admin con `users:update`, objetivo de otra empresa | 403 | 403 (sin cambio) |
| Titular con contraseña actual | 200 | 200 (sin cambio) |
| Auditoría | `company_id` del objetivo | empresa efectiva del actor + objetivo |

## 6 · Secciones §47 (resumen)

- **Alcance**: `auth/service.py` (resolución del objetivo + autorización); tests nuevos.
- **Fuera**: rotación/logout (GA-REM-003), política de contraseñas.
- **FE**: sin cambio (la UI ya tiene el flujo; su gate por permisos es R-212).
- **BE**: `_usuario_alcanzable(user_id, actor)` + `tiene_permiso(actor, "users", "update")` (o titular); sin esquemas.
- **Contrato**: mismos códigos para los casos legítimos; los ilegítimos pasan a fail-closed.
- **Seguridad/tenant**: cierre de la brecha contextual; sin elevaciones.
- **RBAC**: se incorpora `users:update` como autoridad válida (además del titular con contraseña actual).
- **Transacciones/Auditoría**: sin cambio (auditoría ya existe con empresa del objetivo → pasa a empresa efectiva).
- **i18n/UI/responsive**: sin cambio.
- **Migración/SAP**: ninguna / indirecto.
- **Compatibilidad**: cambia 200→4xx solo en el caso sin ámbito (corrección).
- **AC**: ver `R-202_AC_RED_E2E_UAT.md`.
- **Cierre**: AC verdes · RED · sin migración/endpoint/permiso · R-202 → `CLOSED`.

## 7 · Dedup

Inspeccionados R-001…R-189, GA-REM-001…042, OD-13/OD-14: `GA-REM-012` cubre contraseñas (titular), no el restablecimiento contextual. **Nuevo** (GAP-04).

## 8 · Interdependencias

R-195 (UI de usuarios, misma pantalla) · R-199/R-200 (bloque de sesión/seguridad) · GA-REM-003 (logout/rotación, sin solape).

# R-195 · SPEC — EDICIÓN DE USUARIO CON EL SUBCONJUNTO PERMITIDO Y ERRORES LEGIBLES

Fecha: 2026-09-13 · Hallazgo canónico: **R-195** (P1 · bloquea) · HEAD `c0b4afc` · Origen B-06 · Registro G-06. Secciones §47.

## 1 · Contexto

La administración de usuarios (P-13) incluye alta, edición (datos/rol/área/vista/estado), baja lógica y contraseña. La edición está rota por contrato (DTO obsoleto) y los errores usan `alert` sin normalizar.

## 2 · Evidencia

`R-195_FINDING.md §1`: `UsersPage.tsx:76-79,85`; `auth/schemas.py:65-85`; `auth/router.py:128-135`; contraste API.

## 3 · Causa raíz

DTO sin actualizar tras `extra=forbid`/R-118; `alert` en lugar de `getErrorMessage` + toast/banner.

## 4 · Impacto de negocio

Administración de personas bloqueada (rol/área/estado); errores sin información; auditoría de cambios de rol depende de que la edición funcione.

## 5 · Comportamiento actual → esperado

| Acción | Hoy | Esperado |
|---|---|---|
| Editar nombre/correo/rol/estado | 422 «Extra inputs…» + `alert('[object Object]')` | 200; lista refrescada; toast de éxito |
| Payload de edición | incluye `username`/`company_id` | subconjunto permitido (`first_name`, `last_name`, `email`, `phone`, `role_id`, `is_active`, `view_type`, `area_id`) |
| 422/409/403 | `alert` coaccionado | mensaje humano (texto normalizado) |
| Baja fallida | modal abierto sin mensaje | mensaje claro; modal decisión |

## 6 · Comportamiento esperado

1. **Payload correcto**: la edición envía solo los campos de `UserUpdate` (sin `username`, sin `company_id`; usuario no editable; empresa por contexto, R-118).
2. **Errores**: `getErrorMessage` + toast/banner; sin `alert`/`confirm`/`prompt` en el flujo (o con fallback textual si el sistema de diálogo no está listo — decisión C-02).
3. **Alta**: `last_name` requerido también en cliente (B-28); selector de empresa oculto/deshabilitado para actores acotados (se resuelve en servidor).
4. **Baja**: mensaje claro en fallo; modal consistente con el patrón `ConfirmDialog`.
5. Sin cambio backend (el contrato ya es el correcto).

## 7 · Alcance

- `UsersPage.tsx` (payload de edición, validaciones de alta, manejo de errores, baja).
- Tests: `frontend/.../__tests__/r195.usersEdit.test.tsx` (jsdom; rojo: payload con `username`/`company_id`, `alert`); regresión usuario (backend sin cambio).
- Sin migración; sin endpoint; sin permiso.

## 8 · Fuera de alcance

- Reset de contraseña (R-202; backend).
- Roles/permisos página (R-199 seguridad; R-212 gates).
- Rediseño de la pantalla.

## 9 · Impacto frontend

`UsersPage` (payload/errores/validaciones). Sin rediseño.

## 10 · Impacto backend

Ninguno.

## 11 · Contrato frontend↔backend

`PUT /users/{id}`: deja de recibir campos extra (el contrato no cambia; el cliente se alinea). Respuestas 200/4xx sin cambio.

## 12 · Impacto en datos

Sin cambio.

## 13 · Seguridad

Alineado con R-118 (empresa por contexto) y OD-13; sin elevaciones nuevas.

## 14 · Inquilino

La edición sigue acotada por `_usuario_alcanzable` (servidor).

## 15 · Unidad de negocio · 16 · RBAC

Sin cambio (`users:update`; gates existentes).

## 17 · Transacciones

Sin cambio.

## 18 · Auditoría

El cambio de rol en edición queda cubierto por P1-12-REOPEN (productor de usuarios); aquí se asegura que la operación **pueda** ejecutarse.

## 19 · i18n

Mensajes: reutilizar claves comunes (error genérico + `detail`); sin literales nuevos si es posible.

## 20 · Escritorio · 21 · Móvil

Usuarios es web; verificación de usabilidad estándar.

## 22 · Manejo de errores

Como §5: normalizado, sin diálogos nativos obligatorios (C-02).

## 23 · Impacto de migración · 24 · Impacto SAP

Ninguna / indirecto (roles/usuarios base).

## 25 · Compatibilidad hacia atrás

- API: sin cambios.
- UI: la edición pasa de rota a funcional (corrección).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R195-01 | Editar nombre/rol/área/vista/estado ⇒ 200; lista refrescada; sin `username`/`company_id` en el payload |
| AC-R195-02 | 422/409/403 ⇒ mensaje humano normalizado (no `[object Object]`; no crash) |
| AC-R195-03 | Alta sin `last_name` ⇒ validación cliente clara (sin 422 ciego) |
| AC-R195-04 | Actor acotado no ve selector de empresa operativo (o se explica que no aplica) |
| AC-R195-05 | Baja fallida ⇒ mensaje claro; modal coherente |
| AC-R195-06 | Sin `alert/confirm/prompt` en el flujo (o decisión C-02 registrada) |
| AC-R195-07 | Sin migración/endpoint/permiso; diff FE (+tests) |
| AC-R195-08 | Regresión: `test_user_tenant_isolation.py`, `test_p013_password.py`, `test_role_administration.py` verdes; suite UI usuarios |

## 27 · Pruebas RED→GREEN

`§1`: `r195.usersEdit` (rojo: payload/alert), backend control (verde: subconjunto permitido 200).

## 28 · E2E

`§2`: `R195-RT-01…04` (editar por UI; error forzado; baja; móvil no aplica web-only). Artefacto `evidence/r195/`.

## 29 · UAT

`UAT-R195-01…03` (agrupable con R-196/R-215): editar un usuario (rol y nombre), ver error legible con dato inválido, dar de baja. 3/3.

## 30 · Criterios de cierre

AC-01…08 verdes · RED en `c0b4afc` · GREEN local · runtime con artefactos · UAT 3/3 · sin migración/endpoint/permiso · R-195 → `CLOSED` con GA-REM asignado.

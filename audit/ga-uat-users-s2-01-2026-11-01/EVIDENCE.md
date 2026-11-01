# GA-UAT-USERS-S2-01 — Evidencia y certificación

**Fecha:** 2026-11-01 · **Rama:** `main` · **Baseline HEAD:** `200c3d1` · **IMPL SHA:** `464bd998542e609615f66f2acc13a39751ce24d9` · **Spec:** `specs/013-admin-rbac-uat/spec.md` §7 (Amendment S2-01).
`SESSION_1_UAT = PASS` (declarado por la usuaria funcional): **no se reabrió**. Sin migración, sin SAP, sin datos reales.

## 1. Reproducción BEFORE (`evidence/01_before_repro.json`, sanitizado)
Rol A→B desde la UI de Usuarios, sin tocar la clave, con el campo de contraseña poblado con la clave actual (autocompletado del navegador simulado con `fill`):
`PUT /api/v1/users/{id}` → **200** (rol cambiado; cuerpo **sin** password) + `POST /api/v1/users/{id}/password` → **422** «La nueva contraseña debe ser distinta de la actual»; toast idéntico al del PDF; la clave anterior sigue abriendo sesión (login 200).

## 2. Causa raíz
| Capa | Hallazgo |
|---|---|
| Captura del PDF | campo de contraseña con fondo azul de autofill y 9 puntos: el navegador lo rellenó con la clave guardada |
| Frontend (**causa**) | `UsersPage` mantenía en edición un `input[type=password]` siempre presente; `handleSave` hacía `PUT` y, si ese campo tenía valor, `POST /users/{id}/password` ⇒ el valor autocompletado (= actual) disparaba el flujo de cambio de clave |
| Backend | **correcto, sin cambios**: `UserUpdate` es `extra=forbid` y no tiene password; el cambio de clave es un endpoint dedicado (`GA-REM-012`); «nueva ≠ actual» (AR-10) vive solo allí |
| Persistencia | sin daño: ni hash ni sesión cambiaron; el PUT del rol sí se aplicó (de ahí «el rol cambia pero sale el error») |

Clasificación: *Caso B* (gap no cubierto, no regresión de GA-REM-002/003/012/R-202). Severidad **P2 funcional/administración** (no se alcanzó ninguna condición P1: no se modificó credencial, no se almacenó placeholder, no se expuso hash, sin evasión de autorización ni IDOR).
Hipótesis del encargo: H2 (valor enmascarado/autocompletado interpretado como clave nueva) **confirmada**, en su variante «autofill»; H1/H3/H4/H6/H7 descartadas (el PUT nunca lleva password; el schema lo prohíbe; no hay regresión previa); H5 no aplica.

## 3. Fix (frontend; DeepSeek escribió código y pruebas)
- `frontend/src/pages/users/UsersPage.tsx`: en edición **no hay campo de contraseña**; un conmutador explícito «Cambiar contraseña» (`aria-pressed`) revela *nueva + confirmación* (`autocomplete="new-password"`); validación (≥8, confirmación) **antes** de cualquier petición; luego `PUT` y `POST /password {new_password}`; si el POST falla el aviso dice que los datos se guardaron y la clave no cambió (con el detalle del servidor). Desactivar o cerrar descarta lo escrito. El alta mantiene su contraseña obligatoria con `autocomplete="new-password"`.
- i18n es/en: `users.changePasswordToggle`, `newPassword`, `confirmPassword`, `passwordTooShort`, `passwordMismatch`, `passwordNotChanged`.
- Backend: **sin cambios** (solo pins de test).

## 4. Pruebas
| Prueba | Resultado | Evidencia |
|---|---|---|
| FE-01…FE-07 (13 casos, `uatUsersS2.editRoleOnly.test.tsx`) | RED 13/13 en HEAD → **GREEN 13/13** | `02_fe_red.log` |
| Pins backend BE-01…BE-07 (`test_uat_users_s2_role_only.py`, 7) | **7/7** + vecinos 32/32 (PUT conserva hash; PUT con `password` ⇒ 422; rol cambia y `/me` refleja B sin unión; cambio explícito cambia hash y mata la clave vieja; nueva = actual ⇒ 422; sin `users:update` ⇒ 403; auditoría `user` vs `user_password`, sin clave ni hash) | `03_backend_pins.log` |
| E2E `p17e` (Yolinel A→B→A) | **passed**: PUT 200 sin `/password` (ida y vuelta), sin avisos de contraseña, ningún `input[type=password]` en edición, rol B y luego A, login con la clave original 200 en cada paso, `/me` con el **mismo token** pasa de `lots:read` a `audit:read` y vuelve, auditoría `user_password` = 0 y `user` ≥ 1 | `04_after_e2e.json`, `05_e2e_after.log` |
| Frontend completo | 105 archivos · **634 passed**; `tsc -b` rc 0; `vite build` rc 0 | `11_`, `12_`, `13_` |
| E2E regresión | P-17 A–G + p17e **10/10** · cutover 4 BU **4/4** · navegación **8/8** | `20_`, `21_`, `22_` |
| Backend completo pre-mutación | **1 826 passed · 0 failed · 49 skipped** | `10_backend_full_pre_mutation.log` |
| Sensibilidad | **8/8 DETECTADAS** (5 frontend, 3 backend), restauradas con diff vacío | `30_sensibilidad.md` |
| Post-mutación (árbol = IMPL SHA, 0 diff) | backend **1 826 passed · 0 failed · 49 skipped**; frontend **634 passed**; tsc rc 0 | `40_`, `41_` |
`SESSION_1_REGRESSION = PASS` (suites de usuarios/roles/BU/perfil/duplicados/RBAC de SESIÓN 1 y SPEC 013 incluidas en las corridas completas).

## 5. Matriz de ediciones sin clave (AC-S2-01)
Rol (FE-01/FE-02 + E2E), apellido (FE-03), email (FE-04), nombre (FE-05): un solo `PUT`, ninguna petición a `/password`, ningún aviso. **Estado activo/inactivo y vista:** el modal no tiene control de `is_active` (se alterna desde la tabla; se prueba en `uatAdminRbac.usersRoles`), y `view_type` viaja en el mismo `PUT` sin password (FE-02 fija el conjunto exacto de claves). Cambio explícito: FE-06a–d y BE-04/05.

## 6. Observaciones no bloqueantes (sin P0/P1 abiertos)
1. **E2E del flujo explícito de clave por UI no entregado**: el ejecutor se atascó tres veces al generarlo. Queda cubierto por FE-06a–d (jsdom: validaciones sin petición, PUT→POST con `{new_password}`, error del servidor visible), BE-04/05/07 y el E2E P-17-D (cambio de clave propia por Perfil). Se acepta como deuda de cobertura E2E de la variante «admin restablece desde el modal».
2. Flujo explícito: si el `POST /password` falla tras el `PUT` (p. ej. igual a la actual), los datos ya quedaron guardados; el aviso lo dice. Es un contrato deliberado (endpoints separados), no transaccional.
3. A11y preexistente: los toasts no llevan `role`/`aria-live` y el botón Editar de la fila no tiene `aria-label` (ajeno al hallazgo; hizo falta selectores por clase en el E2E).
4. R-123, OD-01/DR-4, AR-22 y fixtures `QA_cutover_*.xlsx` modificados: heredados de SPEC 013, sin cambio.
5. **Runtime UAT sin verificar** tras el despliegue (Watchtower, AOD-29): conviene repetir el escenario de Yolinel en `qa.admin`.

## 7. Estado
```
SESSION_1_UAT=PASS (no reabierto) · MIGRATION=none · BACKEND_APP_CHANGES=0 · SECRETS_IN_EVIDENCE=0
GA-UAT-USERS-S2-01: reproducido · causa raíz = frontend (campo password siempre presente + autofill) · FIXED P2
FE 13/13 · pins BE 7/7 · E2E p17e PASS · regresión FE 634 / BE 1826/0/49 / E2E 10+4+8 · sensibilidad 8/8
FINAL_STATUS=CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS
```

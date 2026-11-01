# 31 — Sensibilidad / mutación del frontend (SPEC 013, administración & RBAC)

**IMPL SHA (restauración):** `99d152eac19cb4db0096f3041769d8d309b3522e` (`main`)
**Suite objetivo (`frontend/`):** `npx vitest run src/__tests__/uatAdminRbac.homeNoLoop.test.tsx src/__tests__/r212.permissionAwareness.test.tsx src/stores/__tests__/uatAdminRbac.sessionRefresh.test.ts src/services/__tests__ src/pages/users/__tests__ src/pages/admin/__tests__ src/components/ui/__tests__`
**Restauración tras cada mutación:** `git restore --source=99d152e -- <archivo>` + `git diff --stat 99d152e -- <archivo>` vacío.
Las mutaciones las aplicó el ejecutor (DeepSeek, MCP) tras el commit de implementación; Claude revisó el informe y la restauración (diff vacío de `frontend/src` y `git status --short frontend` vacío).

| Mut. | Archivo · cambio | Resumen vitest | Test(s) que la detectan | Veredicto |
|---|---|---|---|---|
| baseline | — | 18 archivos · 153 passed | — | verde |
| **M7** | `App.tsx` · `HomeRoute` redirige SIEMPRE a `/menu/poultry` (sin comprobar que el hub exista; vuelve el bucle `/` ⇄ `/menu/poultry`) | 1 failed · 152 passed | `uatAdminRbac.homeNoLoop` › AC-AR23-01 (aviso neutro, sin bucle) | **DETECTADA** |
| **M8** | `auth.store.ts` · `setTokens` reemplaza `user` por el derivado de claims (descarta permisos/unidades) | 1 failed · 152 passed | `uatAdminRbac.sessionRefresh` › mismo sujeto conserva permisos, unidades, nombre y correo | **DETECTADA** |
| **M9** | `sessionWiring.ts` · el manejador de 403 no rehidrata `/me` | 1 failed · 152 passed | `uatAdminRbac.sessionWiring` › el manejador de 403 rehidrata desde /me | **DETECTADA** |
| **M10** | `ConfirmDialog.tsx` · sin `createPortal`, `z-[60]`→`z-40` | 2 failed · 151 passed | `ui-components` › mounts in a portal … z-[60]; `uatAdminRbac.userBuPanel` › AC-UI-01 «Revocar» abre confirmación sobre el modal y revoca | **DETECTADA** |
| **M11** | `UserBusinessUnitsButton.tsx` · `grantFor` devuelve la fila revocada/más antigua en vez de la viva | 1 failed · 152 passed | `uatAdminRbac.userBuPanel` › AC-UI-02 resuelve la VIVA | **DETECTADA** |
| **M12** | `UsersPage.tsx` · petición del listado sin `limit=100` | sub-suite `pages/users`: 17 failed · 27 passed | `UsersPage.test` › (a) la primera carga pide limit=100 y NO manda search; (b) escribir no dispara petición…; + estados de carga/papelera/AC-NAV-03 (efecto en cadena de mocks) | **DETECTADA** |
| restauración final | `git restore --source=99d152e` | 18 archivos · 153 passed | — | verde |

**Resultado:** 6/6 DETECTADAS · 0 sobrevivientes · 0 BLOCKED · `git diff --stat 99d152e -- frontend/src` vacío.
Nota: M12 se midió sobre la sub-suite `src/pages/users/__tests__` (la detección está probada con los dos tests explícitos de `limit=100`/`search`).

```
SENSIBILIDAD_FRONTEND=6/6_DETECTADAS · DIFF_VS_IMPL_SHA=0
```

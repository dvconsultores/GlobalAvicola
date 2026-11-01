# GA-UAT-ADMIN-RBAC-2026-10-31 — Evidencia y certificación

**Rama:** `main` · **Baseline HEAD:** `4aa0775` · **IMPL SHA:** `99d152eac19cb4db0096f3041769d8d309b3522e` · **Spec:** `specs/013-admin-rbac-uat/spec.md` · **Hallazgos:** `00_FINDINGS_TABLE.md` (AR-01 … AR-23).
Entrada funcional: UAT de Yolinel (`qa.admin`, QA Avícola Integral) + sondas observacionales en HEAD. Sin migración (head `f1a2b3c4d5e6`), sin SAP real, sin datos reales; contraseñas y tokens no aparecen en la evidencia (comprobado por grep: solo nombres de clave `access_token` en listas de las sondas).

## 1. Cadena demostrada
`Usuario → Rol → Permisos → Unidad de negocio → Sesión → UI → API → dato permitido/denegado`, con mutabilidad ejecutada y el MISMO token:
- **Permiso:** `ALLOW → revocar → DENY → restaurar → ALLOW` (API + UI) — backend `test_uat_admin_dynamic_authority.py`, E2E P-17-A.
- **Unidad de negocio:** `ALLOW → revocar → DENY → restaurar → ALLOW` — `test_uat_admin_bu_dynamic.py`, E2E P-17-B (panel de Usuarios, «Revocar» opera).
- **Usuario:** `ACTIVE → INACTIVE → DENY` (access 401, refresh 401, login 403) y reactivación — E2E P-17-C.
- **Contraseña propia:** actual obligatoria, nueva ≠ actual, login con la nueva, la vieja falla — E2E P-17-D, `test_uat_admin_users_identity.py`.
- **Sesión:** refresh automático conserva autoridad (P-17-E); un 403 reconcilia permisos sin recargar (P-17-F).
- **UI ↔ API:** 15/15 pares (3 cuentas × 5 rutas): la UI abre la ruta ⇔ la API responde 200; si no, 403 exacto y la UI no consume el endpoint (P-17-G, `evidence/e2e_ui_api_consistency.json`).

## 2. Matriz de acceso ejecutada
`evidence/matrix_role_route.json` + `matrix_summary.md`: 229 rutas protegidas (introspección) × roles de producto y roles de un solo permiso + rol vacío + anónimo = **2 552 sondas · ALLOW 965 · DENY 1 528 · sin sesión 59 · PASS 2 552 · FAIL 0**. Los 41 pares (módulo, acción) exigidos por alguna ruta quedan cubiertos; sin ALLOW huérfano (allowlist vacía).

## 3. Hallazgos y resolución
| Grupo | IDs | Resolución |
|---|---|---|
| Decisiones Owner (2026-10-31) | AR-01 (DR-1 baja de rol bloqueada con usuarios activos; rol inactivo sin autoridad, no asignable, reactivable), AR-18 (DR-2 ≥1 permiso por rol), AR-02/08 (DR-3 subconjunto + sin auto-acción), AR-11 (DR-4 sin revocación de tokens al cambiar clave: se documenta y se fija con test) | Implementadas / fijadas por test |
| Backend | AR-01b, 03, 04, 05, 06, 07, 09, 10 | 409/422/403 deterministas, unicidad insensible, auditoría con diff, baja exige `users:delete`, clave nueva ≠ actual |
| Frontend | AR-13…17, 19, 20, 21, 22, 23 | portal de confirmación, estado vivo vs histórico, rotulado, sesión conserva/reconcilia, listado 100 + búsqueda, **home sin bucle** |
| Política fijada sin cambio | AR-12 (R-123 `scope_type/scope_id` no evaluados), AR-11 (OD-01) | Pinneados por test (DA-06, `AC-POL-01/02`) |

**AR-23 (hallado por E2E, preexistente, P2):** bucle `/` ⇄ `/menu/poultry` para un usuario con autoridad válida pero sin `dashboard:read` ni hub productivo (~300 navegaciones/s, `<main>` vacío; intermitente: 1 de 3 pasadas atrapada). Causa: `HomeRoute` (R-212 AC-02) y `MenuHubPage` (GA-FE-03 fail-closed) se devolvían mutuamente. No es regresión de GA-REM-002/003/012: ningún contrato previo lo cubría y `r212 AC-02` montaba el hub como stub. Fix: redirigir solo si el hub existe; si no, aviso neutro (`home.noLanding`). `AC-R212-02` se ajusta con unidad efectiva (ver spec `AC-UI-08`).
Regresiones vs remediaciones antiguas (§27): GA-REM-002/003/012, R-199/200/202 sin regresión (suites reutilizadas en verde).

## 4. Verificación (todos sobre el árbol indicado)
| Gate | Resultado | Evidencia |
|---|---|---|
| Frontend vitest | **104 archivos · 621 passed** | `10_frontend_vitest.log` |
| `tsc -b` · `vite build` | rc 0 · rc 0 | `11_`, `12_` |
| E2E P-17 A–G (9 tests) | **9 passed** | `20_e2e_p17_admin_rbac.log` |
| E2E regresión cutover 4 BU (p16) | **4 passed** | `21_e2e_p16_cutover_4bu.log` |
| E2E navegación | **8 passed** | `22_e2e_navigation.log` |
| P-17-E/F tras AR-23 | 3/3 pasadas verdes (antes: intermitente) | ejecución dedicada |
| Backend completo pre-mutación | 1 818 passed · **1 failed** (`test_t028_04`: literal ISO en el nombre del directorio de evidencia de mi test; corregido construyendo el nombre por partes, sin tocar el guardián) · 49 skipped | `13_backend_full_pre_mutation.log` |
| Sensibilidad backend | **6/6 DETECTADAS** (M1 rol inactivo con autoridad, M2 subconjunto, M3 unicidad insensible, M4 ≥1 permiso, M5 auto-acción, M6 baja sin `users:delete`) | `30_sensibilidad_backend.md` |
| Sensibilidad frontend | **6/6 DETECTADAS** (M7 bucle home, M8 setTokens, M9 manejador 403, M10 portal, M11 viva vs histórica, M12 limit=100) | `31_sensibilidad_frontend.md` |
| Backend completo post-mutación (árbol = IMPL SHA, 0 diff) | **1 819 passed · 0 failed · 49 skipped** | `40_backend_full_post_mutation.log` |

## 5. Observaciones no bloqueantes (sin P0/P1 abiertos)
1. **R-123:** `scope_type/scope_id` siguen sin evaluarse (pinneado por test; la UI siempre envía `all`).
2. **DR-4 / OD-01:** access y refresh previos siguen válidos tras cambiar la contraseña (decisión Owner de mantener y documentar).
3. **AR-22:** el listado de Usuarios pide 100 y busca en cliente; sin paginación completa por encima de 100.
4. `Button.tsx` variante `secondary`: clase malformada `hover:bg-slate-200:bg-slate-700` (preexistente, ajena).
5. Fixtures `audit/qa-integral-dataset/fixtures/*.xlsx` modificados en el árbol de trabajo por trabajo previo ajeno: no se incluyen en ningún commit de esta misión.
6. **Runtime UAT no verificado en esta misión:** el despliegue lo hacen los workflows + Watchtower tras el push (AOD-29); queda pendiente una verificación manual con `qa.admin` (puede verse afectado por DR-3: un actor solo asigna roles cuyos permisos posee).

## 6. Estado
```
MIGRATION=none · REAL_SAP_WRITES=0 · SECRETS_IN_EVIDENCE=0
AR-01b/03/04/05/06/07/09/10/13/14/15/16/17/19/20/21/22/23 FIXED · AR-01/02/08/18 FIXED (DR-1..DR-3) · AR-11/12 PINNED
MATRIZ=2552/2552 PASS · UI_API=15/15 · E2E=21/21 · vitest=621 · backend post-mut=1819/0/49
SENSIBILIDAD=12/12 DETECTADAS · P0/P1 abiertos=0
FINAL_STATUS=CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS
```

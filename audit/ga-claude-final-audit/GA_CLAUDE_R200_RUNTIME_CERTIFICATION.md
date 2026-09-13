# GA-CLAUDE · R-200 — CERTIFICACIÓN (C1 · C2 · C2s · C3 runtime)

Fecha: 2026-09-13 · Hallazgo **R-200** (P2 · `GAP-03` · «sólo un access token autentica una petición») · Paquete `specs/R-200/` · Commits: C1 `9406573` · C2 `bf1746c`.

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | `evidence/r200/red_c1.log` — **4 rojas por el defecto**: el refresh como `Bearer` autenticaba con identidad completa (`is_super_admin: true`), un JWT sin `type` autenticaba, `type:"session"` autenticaba — **+ 5 controles verdes** (CTL-05…08, DOC-10) |
| **C2 · Implementación** | ✅ | `green_r200_c2.log` (dirigido 21/21 = R-200 9/9 + R-199 12/12) · **suite completa `1247 passed / 0 failed / 49 skipped`** (`full_suite_c2.log`) · 0 ficheros frontend |
| **C2s · Sensibilidad** | ✅ M1 | neutralizar la comprobación ⇒ **RED-01…04 rojas** (`mutations/M1_sin_comprobacion_tipo.log`); mutación revertida, worktree limpio |
| **C3 · Runtime** | ✅ | `runtime-prefix.json` (pre, 20:04:52 +0200: E2E-01/02 = **200**) · **`runtime-c3.json` (post, 20:20:41 +0200: E2E-01/02 = `401` «Token inválido: no es un token de acceso»; E2E-03 = 200; E2E-04a/b = 200/200)** — deploy: `Docker Push — Backend` run **117** (`bf1746c`) success + Watchtower |

## 2 · Implementación

`get_current_user` (`app/auth/security.py`): si `payload.get("type") != "access"` ⇒ `401` «Token inválido: no es un token de acceso», **antes** de leer `sub` y de consultar la base (un token del tipo equivocado no produce ninguna consulta ni fija `set_current_audit_user`). Emisión y `/refresh` **sin cambios**: access 30 min · refresh 7 d · mismos claims (`DOC-10` los fija contra `settings`).

## 3 · AC

| AC | Estado |
|---|---|
| AC01 · AC02 (refresh como Bearer ⇒ 401; nunca 403) | ✅ RED-01/02 (+ runtime E2E-01/02) |
| AC03 · AC04 (JWT sin `type` / tipo desconocido ⇒ 401) | ✅ RED-03/04 |
| AC05 · AC06 · AC07 · AC08 (controles: access, renovación, refresh≠access en `/refresh`, `switch-company`) | ✅ CTL-05…08 (+ runtime E2E-03/04) |
| AC09 (sin asiento ni usuario de auditoría) | ✅ recuento de `audit_logs` igual antes/después en RED-01; comprobación previa a la base |
| AC10 (ventanas documentadas) | ✅ DOC-10 (±2 min / ±1 h) |
| AC11 (regresión) | ✅ suite `1247/0/49` |
| AC12 (sin migración/endpoint/permiso/0 FE) | ✅ diff |
| AC13 (nota de alcance) | ✅ «R-200 no cierra `GA-REM-003 AC04`» (ledger AE-15/16/18 + registro) |
| AC14 (sensibilidad) | ✅ M1 |

## 4 · Alcance explícito

`R-200` **no** cierra `GA-REM-003 AC04` (logout/rotación/revocación del refresh): un refresh robado sigue **renovando** durante 7 días; lo que ya no puede es **autenticar directamente**. Esa revocación es el rider siguiente de T2.

## 5 · Veredicto

**R-200 = `CLOSED_FUNCTIONALLY_CERTIFIED`** — C1/C2/C2s/C3 completos con evidencia local **y** runtime (estados pre/post observados y registrados). Sin reglas relajadas, sin cambios fuera de alcance.

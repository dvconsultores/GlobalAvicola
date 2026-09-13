# GA-CLAUDE · R-202 — CERTIFICACIÓN (C1 · C2 · C2s · C3 runtime)

Fecha: 2026-09-13 · Hallazgo **R-202** (restablecimiento de contraseña con contexto de empresa; origen `GA_REM_012`/E-0x) · Paquete `specs/R-202/` (diseño `R-202_AC_RED_E2E_UAT.md`) · Commits: C1 `58b374a` · C2 (este tranche).

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | `evidence/r202/red_c1.log` — **3 rojas por el defecto**: super sin contexto restablecía a cualquiera (204 ⇒ debe ser 4xx), admin de empresa con `users:update` recibía 403 (⇒ debe 204), sin asiento de auditoría con la empresa efectiva del actor · **+ 2 controles verdes** (super situado; cruce de empresa 403/404) |
| **C2 · Implementación** | ✅ | `green_r202_c2.log` (dirigidas 37/37 = R-202 5/5 + R-199 12/12 + R-200 9/9 + `test_p013_password` 11/11) · **suite completa `1252 passed / 0 failed / 49 skipped`** (`full_suite_c2.log`, 19:39) · commit `fafd262` |
| **C2s · Sensibilidad** | ✅ M1·M2 | M1 (anular `users:update`) ⇒ `test_t012_05` roja (`mutations/M1_sin_permiso.log`, 1F/15P); M2 (resolver el objetivo sin ámbito) ⇒ RED-01 super-sin-contexto y RED-04 cruce rojas (`mutations/M2_sin_ambito.log`, 2F/3P); mutaciones revertidas |
| **C3 · Runtime** | ⏸ **pendiente** | Requiere actor `users:update` de empresa y/o super sin contexto — **G-06** (credenciales privilegiadas). Los actores UAT-09 (operador/aprobador) no portan `users:update` |

## 2 · Implementación

`AuthService.change_password` (`app/auth/service.py`):
- **Titular** (sin cambios): exige `current_password` correcta.
- **Administrador** (corrección): el objetivo se resuelve **primero** dentro del ámbito — `_usuario_alcanzable(user_id, current_user)` (fail-closed sin empresa efectiva: super sin contexto ⇒ 404; objetivo de otra empresa ⇒ 404) — y después se exige el permiso `users:update` (`tiene_permiso`) ⇒ 403 si falta. La capacidad global suelta (`is_super_admin`) deja de bastar.
- **Auditoría**: `company_id` = empresa **efectiva del actor** (`current_user.get("company_id")`, con respaldo en la del objetivo para el titular).

## 3 · AC

| AC | Estado |
|---|---|
| AC-R202-01 (super sin contexto ⇒ 4xx; hoy 204) | ✅ RED-01 (C1 rojo 204; C2 verde 404) |
| AC-R202-02 (super situado ⇒ 204, control) | ✅ CTL-02 |
| AC-R202-03 (admin `users:update` de su empresa ⇒ 204; hoy 403) | ✅ RED-03 (C2 verde) |
| AC-R202-04 (admin cruza empresa ⇒ 403/404, control) | ✅ CTL-04 |
| AC-R202-05 (actor sin `users:update` y no titular ⇒ 403) | ✅ RED-05/M1 + `test_p013_password` |
| AC-R202-06 (auditoría con empresa efectiva del actor) | ✅ RED-06 |
| AC-R202-07 (sin migración/endpoint/permiso nuevo) | ✅ diff |
| AC-R202-08 (regresión `test_p013_password`) | ✅ 11/11 |

## 4 · Veredicto

**R-202 = `CLOSED_TECHNICALLY`** — C1/C2/C2s completos con evidencia local. **C3 runtime pendiente de G-06** (credenciales privilegiadas); la ruta de sondeo runtime (super-sin-contexto ⇒ 4xx; admin ⇒ 204; cruce ⇒ 403/404) se ejecutará cuando el gate se provea.

# GA-FE-02 · SCREENSHOT INDEX

**Estado**: sesión no autenticada (sin credenciales autorizadas — `BLOCKED_AUTH`).
Se registran las capturas posibles en el piso público; las capturas autenticadas (admin de
unidades, panel por usuario, móvil) quedan PENDIENTES hasta recibir las cuentas.
Sin contraseñas ni tokens en ninguna captura.

| # | Captura | Momento | Estado | Archivo/Referencia |
|---|---|---|---|---|
| S-00 | Login (contexto fresco) — ENTRY GA-FE-02 | 2026-09-10 ~22:50Z | ✅ (evidencia de sesión GA-FE-01: pantalla idéntica) | sesión de chat; texto de snapshot registrado |
| S-01 | Login (contexto fresco) — EXIT post-despliegue GA-FE-02 | 2026-09-10 23:40Z | ✅ capturada (página nueva; `/admin/unit-access` sin sesión redirige a `/login`) | sesión de chat — snapshot + screenshot |
| S-02 | — `Admin → Acceso por unidad` (escritorio, estados mixtos) | requiere auth | PENDIENTE (cuentas §122) | — |
| S-03 | — habilitar/apagar unidad con confirmación | requiere auth | PENDIENTE | — |
| S-04 | — concesiones por unidad: candidatos + conceder | requiere auth | PENDIENTE | — |
| S-05 | — revocar con confirmación | requiere auth | PENDIENTE | — |
| S-06 | — panel `Unidades de negocio` en Usuarios (empresa ≠ usuario) | requiere auth | PENDIENTE | — |
| S-07 | — auto-concesión: candidatos sin self / nota | requiere auth | PENDIENTE | — |
| S-08 | — móvil 390×844: Acceso por unidad | requiere auth | PENDIENTE | — |
| S-09 | — móvil: panel por usuario | requiere auth | PENDIENTE | — |

Regla (§137): las capturas autenticadas se toman **solo** con las cuentas autorizadas; cada una
se nombrará `GA_FE_02_E2E_<paso>_<ts>.<ext>` al ejecutarse y se enlazará aquí.

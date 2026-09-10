# RUNTIME CONSOLE ERROR SUMMARY

**2026-09-10** · runtime `avicola.globaldv.net` · sesión sin autenticar.

## Lo capturado

| Superficie | Consola | Notas |
|---|---|---|
| `/login` (carga completa, `networkidle`) | **sin `console.error`** en el listener de la sesión | render OK; formulario operativo a nivel de UI |
| Deep links sin sesión (`/roles`, `/masters/weight-curves`, `/notifications`, `/poultry/hatchery`, `/review`) | redirección limpia a `/login` | comportamiento esperado; sin errores capturados |

## Lo NO capturado (y por qué)

- Errores de consola **post-login** (páginas protegidas): bloqueado por `AUTHENTICATED_RUNTIME_BLOCKER`.
- Errores de red autenticados (403/500 de operación): ídem.

## Errores conocidos que habitarán la consola del runtime (estáticos, no capturados aún)

| Origen | Mensaje probable | Causa | Evidencia |
|---|---|---|---|
| `/users` con rol sin `users:read` | `console.error` → tabla vacía sin explicación | F-E: `Promise.all` + `catch{}` (generación 09-05) | `FRONTEND_SCREEN_IMPLEMENTATION_MATRIX §3` |
| Carga del selector de empresa | sin error (catch silencioso) → «Cargando…» perpetuo | `company.store.ts` 36-44 | `EVIDENCE §10` |
| Cualquier página de admin pulsada por rol sin permiso | 403 → estado vacío o `alert` | R-98/R-119 (menú sin gating) | `NAVIGATION_ROLE_BU_MATRIX §3` |

## Veredicto

Sin errores de consola en la superficie pública; **la consola de las superficies autenticadas no puede declararse limpia ni sucia** — pendiente de la fase autenticada. No se convierte en defecto lo que no se ha observado.

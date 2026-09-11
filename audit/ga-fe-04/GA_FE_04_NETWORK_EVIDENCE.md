# GA-FE-04 · EVIDENCIA DE RED (R, generación `index-B66tpdeW.js`)

Captura de todas las respuestas `/api/**` durante la sesión del actor R:

```
200 GET /api/v1/me
200 GET /api/v1/notifications/unread-count
200 GET /api/v1/masters/farms?skip=0&limit=20&search=
200 GET /api/v1/notifications/unread-count
200 GET /api/v1/me
200 GET /api/v1/notifications/unread-count
200 GET /api/v1/users
200 GET /api/v1/notifications/unread-count
200 GET /api/v1/masters/areas?limit=100
200 GET /api/v1/masters/companies?limit=100
200 GET /api/v1/roles
200 GET /api/v1/me
200 GET /api/v1/notifications/unread-count
200 GET /api/v1/notifications/unread-count
```

Puntos verificados:
- **Solo lecturas** (GET) durante navegación de R a `/masters/farms`, `/users` y deep link `/lots/new`.
- **`/masters/farms` se consulta exactamente 1 vez** (sin bucles de fetch por renders repetidos).
- **El deep link denegado no dispara ninguna llamada de producto** (los datos de `/lots` no se piden en `/lots/new` para R).
- `/me` + `notifications/unread-count` siguen el patrón normal de la aplicación (no específico de GA-FE-04).
- 0 errores de consola (ver evidencia runtime §6).

Reproducción: Playwright registrando `response` para URL que contiene `/api/` durante la sesión R; script efímero fuera del repositorio.

---

## GA-FE-04-A · Self-action + Cross-company (actor B, generación `index-B66tpdeW.js`)

Secuencia sanitizada del flujo desktop en `/admin/unit-access` (solo método + ruta + status):

```
200 GET  /api/v1/me
200 GET  /api/v1/notifications/unread-count
200 GET  /api/v1/business-units
200 GET  /api/v1/business-units/broiler/grant-candidates
403 POST /api/v1/users/105/business-units        (SELF — SOD)
404 POST /api/v1/users/107/business-units        (CROSS — usuario inexistente en empresa efectiva)
200 GET  /api/v1/users/105/business-units        (fresh state: [])
200 GET  /api/v1/business-units                  (estado de unidades sin cambio)
```

Puntos verificados:
- Sin duplicación de mutaciones (un único POST por caso, ambos denegados).
- Sin petición con éxito falso ni cambio de estado optimista.
- El error cross-company no expone detalles del inquilino vecino (`usuario 107`).
- Sesión móvil 390×844 reproduce las mismas negativas (403/404).
- Observación `OBS-01` (fuera de alcance): `403 GET /api/v1/dashboard/admin` al entrar a `/menu` desnudo con rol 35 (sin `dashboard:read`) → hub redirige a home y el dashboard muestra «Permiso requerido». Preexistente; sin acción.

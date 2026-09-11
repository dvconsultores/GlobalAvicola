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

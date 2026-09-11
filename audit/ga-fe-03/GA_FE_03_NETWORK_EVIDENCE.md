# GA-FE-03 · EVIDENCIA DE RED

**Método**: captura automática por contexto de página (Playwright, desktop y móvil) + batería
API oficial. Solo método/ruta/estado; **sin cabeceras, sin cuerpos sensibles, sin tokens**.

## Mutaciones observadas (desktop, ventana completa)

```
PATCH /business-units/broiler/enable  => 1   (E3, UI)
PATCH /business-units/broiler/disable => 1   (E9, UI)
POST  /users/{id}/business-units      => 2   (B4 grant C por UI + reintento idempotente del flujo;
                                              backend: 201 sin fila nueva si la concesión ya vive)
POST  /switch-company                 => 4   (E2, E7×2, S8 — uno por acto de switch)
POST  /login                          => 10  (una por sesión de actor; sin reutilización de tokens)
```

Sin duplicados por clic simple; el doble POST del flujo de concesión NO produjo segunda fila,
segunda auditoría ni segundo cambio de alcance (verificado en §6 de la evidencia runtime).

## Lecturas de autoridad correlacionadas (UI → API → estado)

- `/me` (sesión extendida: permisos + 3 listas de unidades) — hidrata la navegación.
- `/business-units` — 4 filas; toggles con refetch inmediato y toast de éxito.
- `/users/{id}/business-units` — altas/revocaciones verificadas con GET fresco en cada paso.
- `/lots` — C: 2 filas (`L-BO-2026-05/06`) con BU ON+concesión; **0 filas** con BU OFF (grant
  viva) y con ON sin concesión — correlato backend exacto de la navegación.
- `/audit` — 13 `config_change` CBU + 10 `permission_change` UBU, 1:1 con las operaciones.

## Seguridad de la captura

```
Secretos capturados ............ 0 (ni password, ni Authorization, ni cookies, ni tokens)
Cabeceras almacenadas .......... ninguna
Cuerpos sensibles ............. ninguno (solo semántica de estado)
Tokens en documentos .......... 0
Negativas del backend .......... 403/404 registradas como estado, sin material sensible
```

Los reportes efímeros de la corrida (`/tmp/ga3_net.json`, `ga3_console.json`,
`ga3_mobile_console.json`) se destruyen al cierre junto con las credenciales sintéticas.

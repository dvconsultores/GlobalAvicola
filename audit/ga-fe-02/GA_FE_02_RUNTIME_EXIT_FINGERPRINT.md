# GA-FE-02 · RUNTIME EXIT FINGERPRINT

**Capturado**: 2026-09-10T23:40:33Z · **Disparador**: push de C2 `48ffdbb` (23:38:14Z) por el
mecanismo normal (EX-01: CI → Docker Hub :latest → Watchtower) — **0 acciones manuales**.

## ENTRY vs EXIT

| Señal | ENTRY (GA-FE-01, 22:46Z) | EXIT (GA-FE-02) | Cambio |
|---|---|---|---|
| `Last-Modified` raíz | Thu, 10 Sep 2026 21:42:54 GMT | **Thu, 10 Sep 2026 23:39:07 GMT** | ✅ avanzó (+~2h) |
| `ETag` | `"6aa3245e-322"` | `"6aa33f9b-322"` | ✅ cambió |
| Main JS | `index-kzREeQp6.js` | **`index-C_aR7TJ6.js`** | ✅ generación GA-FE-02 |
| CSS | `index-CgiG0VY8.css` | `index-NE-4BlmS.css` | ✅ |
| Asset GA-FE-01 (`index-kzREeQp6.js`) | primario | **404** | ✅ retirado |
| `index.html` sha256 | `909ea073…` | `b71a38ce…` | ✅ |

## Paridad byte a byte despliegue == build local (de `48ffdbb`)

| Artefacto | sha256 servido | sha256 local | Match |
|---|---|---|---|
| `index.html` | `b71a38cef5a17575bfbab20f24c164bacfc056b5c1ad846f8845d25f665c61ea` | ídem | ✅ |
| `assets/index-C_aR7TJ6.js` | `35ea38e2c3f41e783a7dc401962f61da0ae4010c34fd5da4dc1be3f9faa41bd8` | ídem | ✅ |
| `assets/index-NE-4BlmS.css` | `6b2cd17380c72db96734b1cb161b0fc1f00515913e22790830910fcf9aded796` | ídem | ✅ |

```
INTERPRETACIÓN: el runtime sirve EXACTAMENTE el artefacto construido desde `48ffdbb`.
Detección de cambio: T+53s del push (23:38:14Z → LM 23:39:07Z).
```

## Marcadores GA-FE-02 en el bundle SERVIDO

| Marker | ENTRY | EXIT |
|---|---|---|
| `unit-access` | 0 | **2** |
| `business-units` | 0 | **7** |
| `grant-candidates` | 0 | **1** |
| `admin.forbidden` | 0 | **1** |
| `users.businessUnits` | 0 | **7** |

(Las claves i18n y los `name_key` de unidades viajan fuera del bundle: i18n en
`/locales/*.json` servidos por el contenedor; `name_key` llega por API desde el backend.)

## Smoke público

| Ruta | Código | Lectura |
|---|---|---|
| `/` | 200 | raíz nueva generación |
| `/login` | 200 | SPA responde |
| `/assets/index-C_aR7TJ6.js` | 200 | bundle servido |
| `/assets/index-NE-4BlmS.css` | 200 | estilos servidos |
| `/api/v1/business-units` | **401** | el API de la nueva superficie está vivo y protegido |
| `/api/v1/lots` | 401 | backend vivo |

## Cliente fresco (contexto nuevo, sin caché)

- `GET /` → carga la app → `/login` renderiza (Usuario/Contraseña/Iniciar Sesión/English);
  **sin error fatal**. Captura: S-01 (`GA_FE_02_SCREENSHOT_INDEX.md`).
- `GET /admin/unit-access` (ruta directa, sin sesión) → **redirigida a `/login`** por
  `ProtectedRoute` — la ruta nueva no expone nada a actores no autenticados.
- `RUNTIME_UPDATED_BROWSER_CACHE_STALE`: **NO** — cliente fresco sirve lo nuevo.

# GA-FE-01 · RUNTIME EXIT FINGERPRINT

**Capturado**: 2026-09-10T21:43:35Z–21:44Z (petición fresca; contexto de navegador nuevo).
**Disparador del despliegue**: push de C2 `08d0197` (21:41:17Z aprox.) — EX-01 automático
(CI → Docker Hub :latest → Watchtower), **sin intervención manual**.

## ENTRY vs EXIT

| Señal | ENTRY (pre-fix) | EXIT (post-fix) | Cambio |
|---|---|---|---|
| `Last-Modified` del root | **Sat, 05 Sep 2026 14:09:27 GMT** | **Thu, 10 Sep 2026 21:42:54 GMT** | ✅ avanzó +5 días |
| `ETag` | `"6a9c2297-322"` | `"6aa3245e-322"` | ✅ cambió |
| Main JS servido | `assets/index-D5dwMXuP.js` | **`assets/index-kzREeQp6.js`** | ✅ generación nueva |
| CSS servido | `assets/index-CTw07781.css` | `assets/index-CgiG0VY8.css` | ✅ |
| Asset viejo (`index-D5dwMXuP.js`) | primario del root | **404 Not Found** | ✅ no primario ni presente |
| `index.html` sha256 | `61a41cb5…` | `909ea073…` | ✅ |

## Paridad byte a byte despliegue == build local

| Artefacto | sha256 servido | sha256 local | Match |
|---|---|---|---|
| `index.html` | `909ea0733fb9b2b4c638b03f943573b0940b81818ded8ca63a5ea190dcef7bc4` | ídem | ✅ |
| `assets/index-kzREeQp6.js` | `4b6a6a044d6ccc850c017ba93868fd08b2cc2d859e666b2390204a66bb4038b9` | ídem | ✅ |
| `assets/index-CgiG0VY8.css` | `cc402c7944c4f6c57acbb428ad27dd81e934ee6b494b6d996730182a0bd9557f` | ídem | ✅ |

```
INTERPRETACIÓN: el runtime sirve EXACTAMENTE el artefacto construido desde `08d0197`
(reproducibilidad determinista del build; mismo content-hash que la estación local).
ENTRY_RUNTIME_JS  = assets/index-D5dwMXuP.js   → EXIT_RUNTIME_JS  = assets/index-kzREeQp6.js
ENTRY_RUNTIME_LM  = 2026-09-05 14:09:27 GMT    → EXIT_RUNTIME_LM  = 2026-09-10 21:42:54 GMT
```

## Marcadores en el bundle SERVIDO

| Marker | ENTRY | EXIT |
|---|---|---|
| `permissions-catalog` | 0 | **1** |
| `masters/areas` | 0 | **1** |
| `notifications/unread-count` | 0 | **1** |
| `weight-curves` | 0 | **6** |
| `import_plan` | 0 | **13** |
| `dead_on_arrival` | 0 | **3** |
| `chicks_healthy` | 0 | **2** |
| `planned_close_date` | 0 | **3** |
| `switch-company` (control negativo) | 1 | 1 |

M1–M7 pasan de **ausentes a presentes**: la generación servida ya contiene las capacidades
entregadas tras el congelamiento.

## Smoke público (curl)

| Ruta | Código |
|---|---|
| `/` | 200 |
| `/login` | 200 |
| `/assets/index-kzREeQp6.js` | 200 |
| `/assets/index-CgiG0VY8.css` | 200 |
| `/assets/rolldown-runtime-QTnfLwEv.js` | 200 |
| `/api/v1/lots` | 401 (vivo y protegido) |
| `/api/v1/operations/event-types` | 200 (público vivo) |

## Caché de cliente

Contexto de navegador **nuevo** (sin almacenamiento previo): la app carga la generación nueva y
renderiza la pantalla de inicio de sesión (Usuario/Contraseña/Iniciar Sesión/English) sin error
fatal. Captura: `evidence/EXIT_LOGIN_SCREEN.png`-equivalente (adjuntada en esta sesión).
`RUNTIME_UPDATED_BROWSER_CACHE_STALE`: **NO aplicable** — cliente fresco sirve lo nuevo.

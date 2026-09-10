# GA-FE-01 · RUNTIME ENTRY FINGERPRINT

**Capturado**: 2026-09-10T21:33:32Z (read-only, petición fresca, sin sesión, sin utilizar caché de
navegador — los valores provienen del **origen**).

## Root

| Dato | Valor |
|---|---|
| URL | `https://avicola.globaldv.net/` |
| HTTP | **200 OK** |
| `Server` | `openresty` · `X-Served-By: avicola.globaldv.net` |
| `Content-Length` | 802 |
| **`Last-Modified`** | **`Sat, 05 Sep 2026 14:09:27 GMT`** |
| **`ETag`** | **`"6a9c2297-322"`** |
| `index.html` sha256 | `61a41cb5ce8a8fd13a9e2fbdca08c61cbc5ec7c31aaceb6655a5e320cbdffb57` |

## Assets referenciados por el root

| Rol | Asset |
|---|---|
| Main JS | **`assets/index-D5dwMXuP.js`** |
| CSS | `assets/index-CTw07781.css` |
| Runtime chunk | `assets/rolldown-runtime-QTnfLwEv.js` |

## Asset principal descargado

| Dato | Valor |
|---|---|
| Archivo | `/tmp/ga_fe01_entry_main.js` |
| Bytes | **1 235 292** |
| **sha256** | **`4eb822a57f9a04fd664ef48117968dd6e21df9613b6419146ffba417478c64be`** |

## Clasificación

```
ENTRY_RUNTIME_JS            = assets/index-D5dwMXuP.js
ENTRY_RUNTIME_HASH          = 4eb822a5…c64be
ENTRY_RUNTIME_LAST_MODIFIED = 2026-09-05 14:09:27 GMT
ENTRY_STALE_GENERATION_CONFIRMED = YES
   · idéntico (byte a byte) al medido el 2026-09-10 21:02Z en la auditoría y al del 2026-09-07.
   · el propio root referencia ese asset: no es un residuo físico, es EL primario.
   · el build GREEN de f46cb13 produce ese mismo nombre (GA_FE_01_HISTORICAL_REPLAY.md).

ORIGIN STALE VS CLIENT CACHE  = ORIGIN STALE
   · Los headers del origen (Last-Modified/ETag) certifican que el servidor sirve la
     generación 09-05. Una caché de cliente solo replicaría lo mismo que el origen ya sirve.
   · Sin service-worker en el bundle servido (no hay registro de SW en index.html).
   · La verificación con contexto de navegador fresco se repite en el egreso (§54 del encargo).

PWA/BROWSER CACHE ROOT CAUSE  = NO
```

## API (sin autenticar, contexto)

| Sonda | Código | Lectura |
|---|---|---|
| `GET /api/v1/lots` | 401 | backend vivo y protegido |
| `GET /api/v1/operations/event-types` | 200 | catálogo público vivo |

El runtime sirve un backend de generación actual con un frontend de generación 09-05: la brecha
que GA-FE-01 demuestra y cierra por el lado del frontend.

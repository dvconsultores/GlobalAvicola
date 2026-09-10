# GA-FE-02 · RUNTIME ENTRY FINGERPRINT

**Capturado**: 2026-09-10T22:46:18Z — medición fresca propia de esta tranche (no se reutiliza el
fingerprint de GA-FE-01 como sustituto).

## Root

| Dato | Valor |
|---|---|
| URL | `https://avicola.globaldv.net/` (ENV-01: compartido de desarrollo/test/certificación) |
| HTTP | 200 · `Server: openresty` |
| `Content-Length` | 802 |
| `Last-Modified` | `Thu, 10 Sep 2026 21:42:54 GMT` |
| `ETag` | `"6aa3245e-322"` |
| `index.html` sha256 | `909ea0733fb9b2b4c638b03f943573b0940b81818ded8ca63a5ea190dcef7bc4` |

## Assets

| Rol | Asset | sha256 | Bytes |
|---|---|---|---|
| Main JS | `assets/index-kzREeQp6.js` | `4b6a6a044d6ccc850c017ba93868fd08b2cc2d859e666b2390204a66bb4038b9` | 1 275 424 |
| CSS | `assets/index-CgiG0VY8.css` | `cc402c7944c4f6c57acbb428ad27dd81e934ee6b494b6d996730182a0bd9557f` | 86 677 |
| Runtime chunk | `assets/rolldown-runtime-QTnfLwEv.js` | (referenciado por root) | — |

## Clasificación

```
ENTRY_RUNTIME_JS            = assets/index-kzREeQp6.js
ENTRY_RUNTIME_HASH          = 4b6a6a04…4038b9
ENTRY_RUNTIME_LAST_MODIFIED = 2026-09-10 21:42:54 GMT
ENTRY_STATE                 = generación de GA-FE-01 (paridad restaurada, R-99 CLOSED)
GA-FE-02 NO presente        = los marcadores de la tranche (rutas/copy de admin) NO existen aún
                              en este bundle — condición de partida del RED (§121)
```

Marcadores de egreso a verificar (elegidos estables, sobreviven minificación):

```
GA_FE_02_MARKERS (expectativa; se confirman en el commit de implementación):
  M2-1  "unit-access"                     (ruta /admin/unit-access)
  M2-2  "business-units"                  (rutas API del servicio tipado)
  M2-3  "grant-candidates"                (ruta API de candidatos)
  M2-4  copies clave (p.ej. name_key prefix) — a fijar al implementar (T16)
```

ENTRY medido ANTES de cualquier cambio de GA-FE-02: los conteos actuales de esos literales en el
bundle servido = **0** (verificado en el piso RED).

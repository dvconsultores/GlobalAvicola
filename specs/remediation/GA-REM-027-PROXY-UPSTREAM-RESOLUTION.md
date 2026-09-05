# GA-REM-027 — RESOLUCIÓN DEL UPSTREAM EN EL PROXY

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-027` · **Tipo** `RUNTIME CONFIGURATION SPEC` |
| **Prioridad** | **P0 · deja la API inalcanzable** |
| **Estado** | `SPEC_READY` |
| **Origen** | `R-71`, incidente del 502 en el backend compartido (2026-09-05) |
| **Dependencias** | ninguna. Interactúa con `EX-01` (Watchtower) sin modificarlo |
| **Detectado** | 2026-09-05 |

## Problema

El contenedor de frontend sirve la SPA y hace de proxy de la API:

```nginx
location /api/ {
    proxy_pass http://backend:8000;
```

`proxy_pass` con un nombre literal y **sin directiva `resolver`** hace que nginx resuelva
`backend` **una sola vez, al arrancar**, y conserve esa dirección IP mientras viva el
proceso. Nunca vuelve a preguntar.

Watchtower recrea el contenedor de backend en cada publicación de imagen, y un contenedor
recreado **no tiene por qué recibir la misma IP**. Cuando no la recibe, nginx sigue
apuntando a una dirección que ya no existe y toda la API responde `502` de forma
permanente, hasta que alguien reinicia el frontend.

### Lo que se observó

```
2026-09-05 05:25 UTC   se publica la imagen sha-9cd1964
2026-09-05 ~05:25 UTC  Watchtower recrea el backend
2026-09-05 13:59 UTC   /api/v1/... → 502 · la SPA → 200 · +8 h de caída
```

Y al mismo tiempo, desde fuera y sin acceso al servidor:

```
http://<host>:8002/health → 200 {"status":"ok","environment":"development"}
http://<host>:8002/api/v1/operations/event-types → 200 application/json
```

**El backend estaba sano todo el tiempo.** Respondía por su puerto publicado. Lo único roto
era el salto del proxy hacia él. El `502` lo emitía el propio nginx del frontend: las
cabeceras de la respuesta de error llevaban sus `add_header ... always`.

### Por qué no se había visto antes

Porque depende de que Docker reasigne o no la misma IP. La publicación anterior
—`sha-f5f6d88`, 2026-09-04 21:06 UTC— produjo un `502` de unos cuatro minutos que se
resolvió solo: el contenedor recreado recuperó su dirección anterior y la caché de nginx
seguía siendo válida por casualidad.

Es decir: **el defecto lleva ahí desde que existe el despliegue automático**, y hasta ahora
la suerte lo había tapado. Esa es la parte que importa; no la caída concreta.

### Qué no es

No es un defecto del código de aplicación. `9cd1964` no lo causó: lo **disparó**, como lo
habría disparado cualquier otra publicación de imagen de backend. Confundir el disparador
con la causa llevaría a revertir código correcto.

Tampoco es `R-52`: el volumen `avicola-media` no interviene en el arranque ni en el
enrutado.

## Alcance

1. Que el proxy vuelva a resolver el nombre del backend en lugar de cachearlo de por vida.
2. Que la API se recupere sola cuando el backend se recrea, sin intervención manual.

## Fuera de alcance

Cualquier cambio en Watchtower, en `:latest`, en `pull_policy` o en los disparadores de
despliegue (`EX-01`) · el proxy externo `openresty` que hay delante, que no está en este
repositorio · `R-52` · cualquier cambio en el backend.

## Principio normativo

> La recreación de un contenedor de backend no puede dejar la API inalcanzable. El proxy
> debe resolver la dirección del backend en el momento de usarla, no una sola vez al
> arrancar.

## Acceptance Criteria

| AC | Criterio | Verificación |
|---|---|---|
| **AC01** | El proxy declara un `resolver` y obtiene la dirección del backend en el momento de servir la petición | revisión de `frontend/nginx.conf` |
| **AC02** | Tras recrear el backend, la API vuelve a responder sin tocar el frontend | verificación posterior al despliegue |
| **AC03** | El URI de la petición se preserva: `/api/v1/x` llega al backend como `/api/v1/x` | comprobación funcional contra el entorno compartido |
| **AC04** | Las cabeceras que ya se enviaban al backend se conservan | revisión del diff |
| **AC05** | La SPA y los activos estáticos siguen sirviéndose igual | verificación posterior al despliegue |
| **AC06** | Mientras el backend esté realmente caído, el proxy sigue devolviendo `502` —no lo enmascara— y se recupera solo cuando vuelve | comportamiento por diseño del `resolver` |
| **AC07** | No se modifica el despliegue automático | revisión del diff |

## Riesgos

| Riesgo | Mitigación |
|---|---|
| `proxy_pass` con variable cambia cómo se pasa el URI | sin componente de ruta tras el puerto, nginx pasa el URI original íntegro, igual que hoy. `AC03` lo comprueba contra el entorno real |
| El `resolver` apunta a un DNS equivocado | `127.0.0.11` es el DNS embebido de Docker para redes *bridge* definidas por el usuario, y `avicola-network` lo es |
| No hay nginx ni Docker en esta máquina para validar por ejecución | limitación declarada: la verificación es por revisión más comprobación posterior al despliegue, que es el entorno real |
| Un TTL largo retrasaría la recuperación | `valid=10s`: la API se recupera en segundos tras recrear el backend |

## Definition of Done

- `AC01`…`AC07` con evidencia.
- Informe del incidente publicado.
- `L3` —la ruta pública hacia la API— verificada en verde tras el despliegue.

# CERTIFICACIÓN — `GA-REM-027` · RESOLUCIÓN DEL UPSTREAM EN EL PROXY

**2026-09-05** · hallazgo `R-71` · **`PARTIAL`** — ver §12

---

## 1. Causa raíz

`frontend/nginx.conf` hacía `proxy_pass http://backend:8000` con un nombre literal y **sin
directiva `resolver`**. nginx resuelve así el nombre una sola vez, al arrancar el proceso, y
conserva esa dirección mientras viva. Watchtower recrea el contenedor de backend en cada
publicación de imagen; cuando el recreado no recupera su IP anterior, nginx apunta a una
dirección que ya no existe y **toda la API responde `502` de forma permanente**.

El backend nunca estuvo caído. La redacción correcta del incidente es:

> El backend siguió sano. La ruta pública quedó indisponible por una resolución de upstream
> obsoleta.

## 2. Topología

```
HOST DE APLICACIÓN     84.247.161.106   avicola.globaldv.net
HOST DE BASE DE DATOS  64.225.104.69    backend/.env
```

```
openresty  →  contenedor frontend (nginx 1.27-alpine)  →  contenedor backend (uvicorn :8000)
                          host:3005 → :80                        host:8002 → :8000
```

## 3. Comportamiento anterior

| Publicación | Recreación del backend | Resultado | Lectura |
|---|---|---|---|
| `sha-f5f6d88` · 09-04 21:06 UTC | sí | `502` de ~4 min, **recuperación espontánea** | Docker reasignó una IP compatible; el defecto siguió ahí, tapado |
| `sha-9cd1964` · 09-05 05:25 UTC | sí | `502` durante **más de 8 h** | la IP cambió; nginx conservó la anterior |

La primera fila es la que explica por qué el defecto llevaba tanto tiempo sin verse: cuando
la suerte acompaña, no se manifiesta.

## 4. nginx y el modelo de DNS

| Dato | Valor | Fuente |
|---|---|---|
| Imagen | `nginx:1.27-alpine` — código abierto | `frontend/Dockerfile:25` |
| Bloques `upstream` | ninguno | `frontend/nginx.conf` |
| `proxy_pass` | una sola directiva | `nginx.conf:61` |
| Identidad del backend | `backend`, nombre de servicio de Compose | `docker-compose.yml:8` |
| Red | `avicola-network`, `bridge` | `docker-compose.yml:117-119` |
| DNS | `127.0.0.11`, DNS embebido de Docker | característica de las redes bridge definidas por el usuario |

El parámetro `resolve` de los bloques `upstream` **no está disponible**: es de NGINX Plus.
De ahí que el mecanismo elegido sea `resolver` con variable, que sí es de código abierto.

## 5. Mecanismo implementado

```nginx
location /api/ {
    resolver 127.0.0.11 valid=10s ipv6=off;
    set $ga_backend backend;
    proxy_pass http://$ga_backend:8000;
```

nginx no puede resolver por adelantado un destino que depende de una variable: lo resuelve
al procesar la petición, respetando `valid=`. Diez segundos es el techo de la recuperación
tras una recreación; no es un reintento disfrazado, es el TTL de la caché.

`proxy_pass` sigue sin componente de ruta tras el puerto, de modo que el URI original se
transmite íntegro. Ninguna cabecera, tiempo de espera ni ruta cambia. Ninguna IP fija.

## 6. Validación de la configuración

Analizador oficial de nginx (`crossplane`), con el fichero envuelto en su contexto real
`http { include … }`:

```
status: ok
sin errores de sintaxis ni de contexto de directiva
```

```
resolver 127.0.0.11 valid=10s ipv6=off
set $ga_backend backend
proxy_pass http://$ga_backend:8000
```

**No sustituye a `nginx -t`** dentro de la imagen. Esta máquina no tiene nginx ni Docker;
esa comprobación queda pendiente.

```
CONFIG_STATIC_PASS
```

## 7. La prueba que faltaba

Conviene decirlo sin rodeos: **la recuperación del 05-09 a las 14:10 no demostró nada.**
Aquel push modificaba `frontend/nginx.conf`, así que reconstruyó la imagen de frontend y
Watchtower recreó ese contenedor — y recrear el contenedor limpia la caché de DNS por sí
solo, hubiera o no arreglo. Es exactamente el caso que el encargo advierte en su §49.

Para demostrar algo hacía falta lo contrario: **recrear el backend dejando el frontend
intacto.**

Se consiguió publicando un cambio que toca únicamente `backend/`, `specs/` y `audit/`. Solo
se reconstruye la imagen de backend; la de frontend no cambia, y Watchtower —que se activa
por cambio de imagen— no toca ese contenedor.

## 8. Ciclo de recreación observado

Muestreo cada ~5 s de los tres niveles y de la identidad del frontend.

| Hora UTC | Imagen backend | Imagen frontend | `L2` | `L3` | ETag de `index.html` |
|---|---|---|:--:|:--:|---|
| 14:32:52 | 05:25:03 | 14:09:31 | 200 | 200 | `"6a9c2297-322"` |
| 14:33:09 | **14:33:09** ← publicada | 14:09:31 | 200 | 200 | `"6a9c2297-322"` |
| 14:34:13 | 14:33:09 | 14:09:31 | 200 | 200 | `"6a9c2297-322"` |
| **14:34:18** | 14:33:09 | 14:09:31 | **000** | **502** | `"6a9c2297-322"` |
| 14:34:34 | 14:33:09 | 14:09:31 | **000** | **502** | `"6a9c2297-322"` |
| **14:34:39** | 14:33:09 | 14:09:31 | **200** | **200** | `"6a9c2297-322"` |
| 14:35:16 | 14:33:09 | 14:09:31 | 200 | 200 | `"6a9c2297-322"` |

### Qué dice cada columna

**`L2 = 000`** es la pieza clave: el puerto publicado del host dejó de responder. El
contenedor de backend fue **destruido**, no recargado. La recreación es real.

**`L3 = 502` solo mientras `L2 = 000`.** El proxy falló exactamente durante la ausencia del
backend y ni un muestreo más. Eso es el comportamiento correcto (`AC06`), y el encargo lo
declara aceptable en su §29: no se promete alta disponibilidad con una sola instancia.

**El ETag y la imagen del frontend no se mueven en todo el ciclo.** El contenedor de
frontend siguió vivo con el mismo nginx y el mismo proceso.

**Recuperación**: `L2` y `L3` vuelven en el **mismo muestreo**. La API se recuperó sola en
cuanto el backend estuvo listo, sin recargar nginx ni reiniciar el frontend.

```
ventana de indisponibilidad ≈ 25 s, acotada por la ausencia del contenedor
retraso de recuperación tras la disponibilidad del backend: por debajo del intervalo de muestreo (5 s)
```

Sobre los 60 muestreos del ciclo completo (~5 min):

```
58 / 60   L2=200  L3=200
 2 / 60   L2=000  L3=502     ← los dos, y solo esos dos, durante la ausencia del contenedor
 0 / 60   L2=200  L3=502     ← ni un caso de «backend sano, proxy roto», que era el defecto
60 / 60   ETag "6a9c2297-322" — el frontend nunca se reinició
```

La fila que importa es la tercera: **cero muestreos con el backend sano y el proxy roto.**
Esa combinación era precisamente la firma del defecto, y es la que ocupó las ocho horas del
incidente.

Contraste con el comportamiento anterior, misma infraestructura y mismo disparador:

```
antes (09-05 05:25)   recreación → 502 durante más de 8 horas
ahora (09-05 14:34)   recreación → 502 durante ~25 s, solo mientras el contenedor no existía
```

## 9. Salud tras el ciclo

```
L2  host → backend        200 application/json  {"status":"ok",...}
L3  API pública           200 application/json  · 25 tipos de evento
L3  ruta protegida        401  ← contesta el backend, no una página de error del proxy
    control SPA           200 text/html  ← no es evidencia de nada
```

## 10. Criterios de aceptación

| AC | Criterio | Resultado | Evidencia |
|---|---|---|---|
| **AC01** | El proxy resuelve al servir, no al arrancar | **PASS** | configuración + validación estática |
| **AC02** | Tras recrear el backend, la API responde sin tocar el frontend | **PASS** | ciclo de §8 |
| **AC03** | El URI se preserva | **PASS** | catálogo íntegro; ruta inexistente → 404 |
| **AC04** | Cabeceras al backend conservadas | **PASS** | diff: las 6 `proxy_set_header` intactas |
| **AC05** | SPA y activos estáticos siguen igual | **PASS** | `/` y `/assets/*.js` en 200 |
| **AC06** | Con el backend realmente caído, `502` controlado; recuperación al volver | **PASS** | `L3=502` solo mientras `L2=000` |
| **AC07** | Despliegue automático sin tocar | **PASS** | diff: ni Watchtower, ni `:latest`, ni `pull_policy` |
| **AC08** | Recreaciones repetidas siguen funcionando | **`PARTIAL`** | **un solo ciclo**; ver §12 |
| **AC09** | El frontend no se reinicia durante la demostración | **PASS** | ETag e imagen invariables |
| **AC10** | Ninguna IP de contenedor fija | **PASS** | diff: solo el nombre de servicio |
| **AC11** | Salud directa y a través del proxy medidas por separado | **PASS** | `L2` y `L3` en cada muestreo |
| **AC12** | La configuración valida | **PASS** | `crossplane`, status ok |

Regresión (`AC13` del encargo): backend 307/307, tsc, vitest 61/61, i18n 866=866, deriva 0.

## 11. Gate de conectividad

`backend/scripts/runtime_connectivity_check.py` cubre el hueco que este incidente reveló:

```
CONTAINER START  →  DIRECT BACKEND HEALTH  →  PUBLIC API HEALTH
```

`startup_test.sh` certifica el arranque y lo hace bien, pero llama al backend directamente;
entre «el backend arranca» y «la API responde» está el proxy, y nada lo recorría. El gate
mide `L2` y `L3` por separado e incluye un control explícito de que la SPA **no** es
evidencia del backend — porque dar por bueno un `200` de HTML fue el error del checkpoint
anterior.

No autentica, no escribe y no toca la base de datos.

## 12. Por qué `PARTIAL` y no `CERTIFIED`

Falta una cosa, y es la que el encargo declara imprescindible en su §52:

```
BACKEND IP ANTES  ≠  BACKEND IP DESPUÉS
```

**No es observable sin acceso al host Docker.** El ciclo demuestra que el contenedor fue
destruido y recreado, que el frontend no se tocó y que la API se recuperó sola; no demuestra
que la dirección cambiase. Si Docker reutilizó la IP, este ciclo habría pasado igual con el
defecto presente — que es exactamente lo que ocurrió el 09-04.

Lo que sí distingue este ciclo del de aquel día: entonces el `502` duró cuatro minutos y
ahora duró lo que duró la ausencia del contenedor, ~25 s. Es indicio, no prueba.

Para cerrar la certificación hace falta, con acceso al host:

```
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' globalavicola-backend
   antes y después de la recreación, con IP distinta
docker exec globalavicola-frontend nginx -t
docker exec globalavicola-frontend nginx -T     configuración efectiva
```

Y varios ciclos, no uno. Aquí solo pudo ejecutarse uno: cada ciclo exige publicar una
imagen de backend, y no hay más cambios legítimos que publicar dentro de este alcance.

```
GA-REM-027 = PARTIAL
CONFIG_STATIC_PASS = SÍ
RUNTIME CYCLE = 1/N observado, sin confirmación de cambio de IP
```

## 13. Limitaciones abiertas

| Limitación | Estado |
|---|---|
| Confirmación de cambio de IP | requiere acceso al host |
| `nginx -t` / `nginx -T` en la imagen | requiere acceso o Docker local |
| Ciclos repetidos | uno observado; se necesitan varios |
| `R-58` | **sigue `PASS_BY_INFERENCE`** — no se cierra con esto |
| Humo autenticado del entorno compartido | `BLOCKED_BY_CREDENTIAL_ACCESS` |
| Reset de `GA-REM-025` en el entorno compartido | `PENDING_EXTERNAL_ACCESS` |

`R-58` merece una nota: que el backend arranque, migre y sirva **no** sustituye a comprobar
`COPY`, el cableado de `ENTRYPOINT`, el bit de ejecución y el usuario `avicola` dentro de la
imagen real. No se cierra por conveniencia.

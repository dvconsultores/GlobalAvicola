# MATRIZ DE RESOLUCIÓN DEL UPSTREAM

**`GA-REM-027`** · 2026-09-05

---

## 1. Topología

```
Internet
   │
   ▼
openresty                       externo al repositorio · añade X-Served-By
   │
   ▼
contenedor globalavicola-frontend      nginx 1.27-alpine · host:3005 → :80
   │  location /api/  ──► backend:8000
   ▼
contenedor globalavicola-backend       uvicorn :8000 · host:8002 → :8000
   │
   ▼
PostgreSQL                             64.225.104.69 — OTRA MÁQUINA
```

```
HOST DE APLICACIÓN   84.247.161.106   ← avicola.globaldv.net
HOST DE BASE DE DATOS 64.225.104.69   ← backend/.env
```

Son dos máquinas distintas y conviene no volver a llamarlas «el servidor».

## 2. Inventario del proxy

| Elemento | Valor real | Fuente |
|---|---|---|
| Imagen | `nginx:1.27-alpine` | `frontend/Dockerfile:25` |
| Bloques `upstream` | **ninguno** | `frontend/nginx.conf` |
| Directivas `proxy_pass` | **1** | `nginx.conf:61` |
| Identidad del backend | `backend` — nombre de servicio de Compose | `docker-compose.yml:8` |
| Nombre del contenedor | `globalavicola-backend` | `docker-compose.yml:12` |
| Red | `avicola-network`, driver `bridge` | `docker-compose.yml:117-119` |
| DNS | `127.0.0.11` — DNS embebido de Docker en redes bridge definidas por el usuario | característica de Docker |
| Alias de red | ninguno declarado; Compose registra el nombre del servicio | — |
| Política de reinicio | `unless-stopped` | ambos servicios |
| Recreación | Watchtower, sondeo 60 s, `WATCHTOWER_LABEL_ENABLE=true` | `docker-compose.yml:99-112` |

Una sola `proxy_pass` y ningún bloque `upstream`: el cambio necesario es de una sola pieza.

## 3. La matriz

| Capa | Configuración anterior | Momento de resolución | ¿Sobrevive a un cambio de IP? | Esperado |
|---|---|---|---|---|
| `proxy_pass` de nginx | `http://backend:8000` literal, sin `resolver` | **una vez, al arrancar el proceso** | **NO** — conserva la IP de por vida | resolver al servir |
| DNS de Docker | `127.0.0.11`, disponible en `avicola-network` | por consulta | sí, si se le pregunta | que se le pregunte |
| Servicio backend | nombre `backend`, estable | — | **sí** — la identidad estable es el nombre | usar el nombre |
| IP del contenedor | efímera, la asigna Docker al crear | — | **no** | nunca fijarla |
| Recreación por Watchtower | recrea el contenedor de backend | en cada publicación | la IP **puede** cambiar | el proxy debe tolerarlo |
| Ruta pública | `openresty → frontend:80 → backend:8000` | — | dependía del eslabón roto | recuperación automática |

### Configuración vigente

| Capa | Configuración actual | Momento de resolución | ¿Sobrevive a un cambio de IP? |
|---|---|---|---|
| `proxy_pass` de nginx | `resolver 127.0.0.11 valid=10s ipv6=off` + `set $ga_backend backend` + `proxy_pass http://$ga_backend:8000` | **al servir la petición**, con caché de 10 s | **sí** — recuperación en ≤ 10 s |

## 4. Por qué la variable cambia el comportamiento

nginx resuelve los nombres de `proxy_pass` **en el arranque** cuando el destino es un
literal, y guarda el resultado mientras viva el proceso worker. Con una variable no puede
hacerlo: el valor solo se conoce al procesar la petición, así que exige una directiva
`resolver` y consulta el DNS en ese momento, respetando `valid=`.

Es la diferencia entre preguntar una vez y preguntar cuando hace falta.

`valid=10s` acota la caché: tras recrear el backend, la API se recupera en diez segundos
como máximo. No es un valor arbitrario ni un reintento disfrazado; es el TTL de la caché de
resolución.

## 5. Mecanismos evaluados

| Mecanismo | Compatible con nginx 1.27 OSS | Elegido | Motivo |
|---|:--:|:--:|---|
| `resolver` + variable en `proxy_pass` | **sí** | **✔** | mínimo, estándar, basado en el nombre de servicio, sin dependencias |
| Bloque `upstream` con `resolve` | **no** | ✘ | el parámetro `resolve` es de NGINX Plus |
| `nginx -s reload` periódico | sí | ✘ | recarga periódica: oculta el defecto en vez de corregirlo (§11) |
| Reiniciar el frontend con cada backend | sí | ✘ | escondería la causa y ataría dos servicios (§10) |
| Fijar la IP del contenedor | sí | ✘ | prohibido: la identidad estable es el nombre (§8) |
| Descubrimiento externo (Consul, etc.) | sí | ✘ | infraestructura desproporcionada para una `proxy_pass` |

## 6. Lo que la configuración **no** cambia

| Aspecto | Estado |
|---|---|
| URLs públicas y rutas de la API | intactas |
| Enrutado de la SPA (`try_files`) | intacto |
| Caché de activos estáticos | intacta |
| `client_max_body_size 12m` (`GA-REM-009`) | intacto |
| Las cuatro cabeceras de seguridad `always` | intactas — no son la causa, fueron la pista |
| `proxy_set_header` × 6 | intactas |
| Tiempos de espera | intactos — el problema era de resolución, no de duración |
| Despliegue automático | intacto (`EX-01`) |

## 7. Validación de la configuración

Analizador oficial de nginx (`crossplane`), sobre el fichero envuelto en su contexto real
`http { include … }`:

```
status: ok
sin errores de sintaxis ni de contexto de directiva
```

Comprueba la sintaxis y que cada directiva esté en un contexto donde se admite. **No
sustituye a `nginx -t`** dentro de la imagen, que además valida el arranque completo; esa
comprobación queda pendiente de un entorno con Docker.

## 8. Cobertura de las tres capas de salud

| Nivel | Qué mide | Cubierto por |
|---|---|---|
| `L1` dentro del contenedor | el proceso responde | requiere acceso al host |
| `L2` host → backend | el contenedor escucha | `http://84.247.161.106:8002/health` |
| `L3` proxy público → API | la cadena completa | `https://avicola.globaldv.net/api/v1/…` |

`L2` es medible desde fuera **porque el backend publica su puerto al host**. Sin esa
publicación, el incidente no se habría podido diagnosticar sin acceso al servidor.

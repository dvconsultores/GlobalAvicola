# INCIDENTE — 502 EN EL BACKEND DEL ENTORNO COMPARTIDO

**2026-09-05** · `GA-REM-027` · hallazgo `R-71`

---

## 1. Resumen

Durante más de ocho horas, `https://avicola.globaldv.net/api/v1/*` devolvió `502` mientras
la SPA seguía sirviéndose con normalidad.

**El backend nunca estuvo caído.** Respondía `200` por su puerto publicado durante todo el
incidente. Lo único roto era el salto del proxy hacia él: el nginx del contenedor de
frontend resolvía el nombre `backend` una sola vez, al arrancar, y conservaba una dirección
IP que dejó de existir cuando Watchtower recreó el contenedor de backend.

El diagnóstico se hizo **sin acceso al servidor**, con sondeos externos y lectura del
repositorio.

```
CATEGORÍA DE CAUSA RAÍZ = REVERSE_PROXY
DISPARADOR              = recreación del contenedor por Watchtower
COMMIT CULPABLE         = ninguno
ESTADO DEL INCIDENTE    = RESOLVED
CAUSA RAÍZ              = CONFIRMED  (ciclo de recreación observado)
```

## 2. Clasificación del entorno

`ENV-01` sigue vigente:

```
ENTORNO DESPLEGADO  =  COMPARTIDO DE DESARROLLO / PRUEBAS / CERTIFICACIÓN
PRODUCCIÓN REAL     =  NO DESPLEGADA
```

Esto **no** es una caída de producción. Es una incidencia del backend compartido de
certificación. La aplicación desplegada lo confirma ella misma: `/health` devuelve
`"environment":"development"`.

## 3. Commit disparador

`9cd1964` — `fix(lots): el saldo de apertura alimenta el balance de aves`.

**No es la causa.** Habría bastado cualquier otra publicación de imagen de backend. El
defecto lleva ahí desde que existe el despliegue automático y hasta ahora lo tapaba la
suerte: cuando Docker reasigna al contenedor recreado la misma IP que tenía, la caché de
nginx sigue siendo válida por casualidad y nadie nota nada.

## 4. Línea temporal

Todas las horas en UTC salvo indicación.

| Hora | Evento | Evidencia |
|---|---|---|
| 09-04 16:52 | se publica la imagen de frontend `sha-47937ed`; es la última | registro público de imágenes |
| 09-04 16:52:47 | el contenedor de frontend arranca y **resuelve `backend` una vez** | `Last-Modified` de `index.html` |
| 09-04 20:40 | se publica `sha-ec81720` (backend) | registro público |
| 09-04 21:06 | se publica `sha-f5f6d88` (backend) | registro público |
| 09-04 21:06→21:07 | `502` de ~4 min y **recuperación sola** | observado (23:06→23:07:41 CEST) |
| 09-05 05:25 | se publica `sha-9cd1964` y `latest` | registro público |
| 09-05 ~05:25 | Watchtower recrea el backend; esta vez **cambia de IP** | inferido |
| 09-05 05:2x → 13:59 | `502` continuo · la SPA sirve `200` | observado |
| 09-05 13:59 | se localiza el emisor del `502` por sus cabeceras | cabeceras HTTP |
| 09-05 14:0x | `http://<host>:8002/health` → `200` — **el backend está sano** | sondeo directo |
| 09-05 14:08 | se publica el arreglo (`f46cb13`) | `git push` |

La recuperación espontánea de la publicación anterior es la pieza que cierra el
razonamiento: demuestra que el fallo depende de si la IP se reasigna, no del código.

## 5. Estado del servidor

`BLOCKED_BY_SERVER_ACCESS`. No existe `~/.ssh/config`, ni contexto Docker remoto, ni
procedimiento de acceso documentado en el repositorio, ni usuario de despliegue en los
workflows —el despliegue es por Watchtower, no por SSH—. El servidor **sí** figura en
`known_hosts`, señal de que el propietario se conecta desde esta máquina, pero sin usuario
documentado. **No se probaron usuarios ni credenciales**: adivinarlos es exactamente lo que
la política prohíbe.

De ahí que todo el diagnóstico sea externo. `hostname`, `uptime`, disco y memoria del host
quedan **`UNKNOWN`**; se descartan como causa por otra vía: si el host estuviera sin
recursos, el backend no respondería `200` por su puerto publicado.

## 6. Estado de Docker

No observable directamente. Lo que sí se estableció:

| Pregunta | Respuesta | Base |
|---|---|---|
| ¿Existe el contenedor de backend? | **sí** | responde HTTP por `8002` |
| ¿Está en ejecución? | **sí, sano** | `/health` → `{"status":"ok"}` |
| ¿Qué imagen ejecuta? | `sha-9cd1964` (= `latest`) | única publicada desde 05:25 y el contenedor está vivo |
| ¿Watchtower actualizó el backend? | **sí** | la imagen se publicó y el contenedor corre la nueva |
| ¿Está el frontend en ejecución? | **sí** | sirve la SPA |
| ¿Se recreó el frontend? | **no desde 09-04 16:52** | `Last-Modified` de `index.html` y última imagen publicada |
| Recuento de reinicios, `ExitCode`, `OOMKilled` | **`UNKNOWN`** | requiere `docker inspect` |

El punto decisivo: **el backend se recreó al menos tres veces desde que el frontend arrancó
por última vez.**

## 7. Watchtower

Funcionó correctamente y no se ha modificado. `EX-01` sigue intacto: no se tocó
`WATCHTOWER_POLL_INTERVAL`, ni `:latest`, ni `pull_policy`, ni las etiquetas.

Su comportamiento correcto es precisamente lo que expone el defecto: recrear el backend es
su trabajo, y el proxy no estaba preparado para que ocurriera.

## 8. Registros del backend

**`UNKNOWN`** — requieren acceso al servidor. No hicieron falta: el backend respondía, así
que sus registros no contenían la respuesta.

## 9. `R-58`

Sigue **`PASS_BY_INFERENCE`**, y la inferencia se refuerza:

| Eslabón | Estado | Base |
|---|---|---|
| Entrypoint en la imagen | **PASS** (inferido) | con `set -e`, sin él no hay `exec` |
| Ejecutable por `avicola` | **PASS** (inferido) | el contenedor arrancó |
| Migraciones ejecutadas | **PASS** (inferido) | la API sirve datos |
| `uvicorn` arrancado | **PASS** (observado) | `200` en `8002` |
| Lectura de `docker logs` | **`UNKNOWN`** | requiere acceso |

Este incidente **no** permite cerrar `R-58`: cerrarlo exige comprobar `COPY`, el cableado de
`ENTRYPOINT`, el bit de ejecución y el usuario **dentro de la imagen real**, y eso no es
observable desde fuera. No se cierra por conveniencia.

## 10. Estado de las migraciones

`MIGRATION COMPLETED` (inferido). La API devuelve `200 application/json` con el catálogo de
tipos de evento, lo que exige esquema al día. La revisión exacta no se leyó: la base no es
alcanzable desde esta red y `alembic current` requiere el contenedor.

```
DB CURRENT  =  NOT_READ
CODE HEAD   =  l2m3n4o5p6q7
AT HEAD     =  inferido SÍ
```

## 11. Conectividad con la base de datos

`PASS` desde el contenedor: la aplicación responde con datos. Desde esta red sigue siendo
`NOT_REACHABLE`, que es una restricción de red y no un fallo.

**Corrección de un supuesto anterior.** Los informes previos hablaban de «el servidor» como
si fuera uno. Son dos:

```
avicola.globaldv.net  →  84.247.161.106   aplicación
backend/.env          →  64.225.104.69    base de datos
```

Los sondeos de puertos del informe posterior al push iban al host de la base de datos, no al
de la aplicación. La conclusión de entonces —base inalcanzable desde esta red— sigue siendo
cierta, pero era sobre otra máquina.

## 12. Configuración de ejecución

Detalle en [`SHARED_RUNTIME_CONFIGURATION_MATRIX.md`](SHARED_RUNTIME_CONFIGURATION_MATRIX.md).

La divergencia que importa: **el arranque aislado no ejercita el proxy.** Llama al backend
directamente. Por eso `startup_test.sh` pasaba con 0 fallos mientras la API pública llevaba
ocho horas caída. No es un defecto del ensayo —su alcance es el entrypoint— sino un hueco de
cobertura entre «el backend arranca» y «la API responde».

## 13. Red y proxy

```
L1  dentro del contenedor        UNKNOWN   (requiere acceso)
L2  host → backend               PASS      http://<host>:8002/health → 200
L3  proxy público → backend      FAIL      502
```

`L2 PASS` con `L3 FAIL` localiza el fallo en el proxy. Que el puerto `8002` esté publicado
al host es lo que permitió medir `L2` sin acceso al servidor.

El emisor del `502` se identificó por sus cabeceras: llevaba las cuatro `add_header …
always` que declara `frontend/nginx.conf:10-13`. Luego lo generaba el nginx del frontend, no
el `openresty` que hay delante ni el backend.

## 14. `R-52`

**Independiente del incidente.** El volumen `avicola-media` no interviene ni en el arranque
ni en el enrutado; el backend arrancó sin él. Sigue **`PENDING`**, y por tanto `GA-REM-009`
sigue sin estar activa en el entorno compartido. No se ejecutó `docker compose up -d` dentro
del incidente: no hacía falta para recuperar, y mezclarlo habría contaminado el diagnóstico.

## 15. Causa raíz

```
CATEGORÍA  =  REVERSE_PROXY
```

`frontend/nginx.conf` hacía `proxy_pass http://backend:8000` con un nombre literal y **sin
directiva `resolver`**. nginx resuelve así el nombre una sola vez, al arrancar el proceso, y
conserva la dirección mientras viva. Cuando Watchtower recrea el backend con otra IP, nginx
sigue apuntando a la anterior y toda la API responde `502` de forma permanente, hasta que
alguien reinicia el frontend.

Causa secundaria: **hueco de cobertura**. Ninguna prueba del repositorio recorría el salto
proxy → backend.

Lo que **no** es: ni defecto del código de aplicación, ni de la imagen, ni del entrypoint,
ni de las migraciones, ni de la base de datos, ni de recursos del host, ni de Watchtower
—que hizo su trabajo—, ni `R-52`.

## 16. Remediación

`GA-REM-027`, hallazgo `R-71`. En `frontend/nginx.conf`:

```nginx
location /api/ {
    resolver 127.0.0.11 valid=10s ipv6=off;
    set $ga_backend backend;
    proxy_pass http://$ga_backend:8000;
```

`127.0.0.11` es el DNS embebido de Docker en redes *bridge* definidas por el usuario, que es
lo que `avicola-network` es. Con la variable, nginx resuelve en el momento de servir;
`valid=10s` acota la caché, de modo que la API se recupera sola pocos segundos después de
cualquier recreación futura.

`proxy_pass` sigue sin componente de ruta tras el puerto, así que el URI original se pasa
íntegro. Ninguna cabecera cambia. No se tocó el despliegue automático.

**El arreglo y la recuperación son la misma acción**: publicar el cambio reconstruye la
imagen de frontend, Watchtower recrea el contenedor y nginx vuelve a resolver. Por eso se
empujó pese a la pauta general de no empujar durante la caída: §60 lo permite expresamente
cuando la recuperación exige código versionado, y el backend no estaba caído.

**No se hizo ningún reinicio ni rollback a ciegas.** El diagnóstico precedió a la acción.

Limitación declarada: esta máquina no tiene nginx ni Docker, de modo que la configuración se
verifica por revisión y por comprobación posterior al despliegue, que es el entorno real.

## 17. Salud posterior a la recuperación

```
2026-09-05 14:09:31 UTC   se publica la imagen de frontend con el arreglo
2026-09-05 14:10:24 UTC   /api/v1/... → 200        RECUPERADO
```

**Menos de un minuto** entre la publicación de la imagen y la recuperación de la API:
Watchtower recreó el contenedor de frontend, nginx resolvió de nuevo y el `502` desapareció.
Esa inmediatez es la confirmación más directa de la causa raíz — no se tocó nada más.

| Nivel | Antes | Después |
|---|---|---|
| **L1** dentro del contenedor | `UNKNOWN` | `UNKNOWN` — sigue requiriendo acceso |
| **L2** host → backend | **PASS** | **PASS** |
| **L3** proxy público → API | **FAIL** `502` | **PASS** `200` |

El contenedor de frontend se recreó: `Last-Modified` de `index.html` pasó de
`09-04 16:52:47` a `09-05 14:09:27`.

## 18. Comprobación funcional

Sin autenticar, que es hasta donde llega esta sesión:

| Comprobación | Resultado |
|---|---|
| `GET /api/v1/operations/event-types` | **200** · 25 tipos, el primero `bird_reception` |
| `GET /api/v1/me` | **401** — la ruta existe y exige sesión |
| `GET /api/v1/operations/alerts` | **401** — ídem |
| `GET /api/v1/lots` | **401** — ídem |
| `GET /api/v1/no-existe-xyz` | **404** — enrutado correcto, no un error genérico |
| SPA `/` | **200** `text/html` |
| Activo `/assets/index-*.js` | **200** `application/javascript` |
| Cabeceras de seguridad | presentes, las del backend y las de nginx |

Que el catálogo llegue completo y que una ruta inexistente devuelva `404` en lugar de un
error del proxy demuestra `AC03`: el URI se pasa íntegro.

### Lo que no pudo comprobarse

| Comprobación | Estado | Motivo |
|---|---|---|
| `R-44` · maestros con una cuenta no Super Admin | **`NOT RUN`** | no hay credencial del entorno compartido y buscarla está prohibido |
| `R-48` / `R-54` · cambio de empresa | **`NOT RUN`** | ídem |
| `R-68` · lectura inmediata tras escritura | **`NOT RUN`** | ídem; además exigiría crear datos |

No se insertó ningún dato en el entorno compartido.

## 19. Regresión

```
Backend ............ 307 pasados · 49 omitidos · 0 fallos
Deriva de esquema .. 0     ·  Alembic: 1 head, 1 base
Guarda de entorno .. 25 tests
TypeScript ......... PASS  ·  Vitest 61/61  ·  i18n 866 = 866
```

`R-68` y `R-67` siguen certificados; el incidente no los tocó.

## 20. Commits y publicaciones

| Commit | Contenido |
|---|---|
| `f46cb13` | `fix(proxy): resolver el upstream en cada petición, no al arrancar [GA-REM-027]` |

Empujado con el `ssh-agent` autorizado, sin modificar el remoto.

## 21. Riesgos restantes

| Riesgo | Estado |
|---|---|
| `R-58` sin evidencia de la capa Docker | abierto · requiere `docker logs` y `docker inspect` |
| `R-52` volumen sin montar | abierto · `GA-REM-009` inactiva en el entorno compartido |
| `R-44` efecto de la reconciliación | `NOT_VERIFIED` · requiere una cuenta no Super Admin |
| Reset del entorno compartido | `PENDING_EXTERNAL_ACCESS` |
| Ninguna prueba cubre el salto proxy → backend | **hueco nuevo**, anotado · sin destino asignado |
| Comprobación funcional autenticada del entorno compartido | `NOT RUN` · requiere credencial |

## 22. `READY_TO_RESUME_GA_REM_016`

```
READY_TO_RESUME_GA_REM_016 = YES
```

| Condición | Estado |
|---|---|
| Backend compartido sano | **sí** — `L3` en `200` |
| `R-58` resuelto o no bloqueante | **no bloqueante con evidencia**: el arranque funciona; falta únicamente la lectura de la capa Docker |
| Sin bloqueante sistémico de ejecución | **ninguno** — la causa raíz está corregida en código versionado |
| `R-68` sigue certificado | sí |
| `R-67` sigue certificado | sí |
| Descubrimiento de Playwright | 59 casos en 5 ficheros |
| Baseline congelado | 15 PASS / 23 FAIL |

`GA-REM-016` se reanuda por la clasificación de los 23 fallos heredados, que este incidente
**no** ha tocado.

## 23. Índice de evidencias

| Evidencia | Cómo se obtuvo |
|---|---|
| Emisor del `502` | cabeceras HTTP frente a `frontend/nginx.conf:10-13` |
| Backend sano | `http://84.247.161.106:8002/health` → `200` |
| Cronología de imágenes | registro público de etiquetas del repositorio de imágenes |
| Frontend sin recrear | `Last-Modified` de `index.html` |
| Dos máquinas distintas | resolución DNS del dominio frente a `backend/.env` |
| Caché de DNS en nginx | ausencia de `resolver` en `frontend/nginx.conf` |
| Recuperación espontánea previa | observación del `502` de 4 min tras `sha-f5f6d88` |


---

## 24. Confirmación posterior (2026-09-05, 14:34 UTC)

La causa raíz pasa de **hipótesis sostenida por evidencia** a **`CONFIRMED`**.

Y hay que corregir algo de este mismo informe: la recuperación de las 14:10 **no demostraba
que el arreglo funcionase**. Aquel push tocaba `frontend/nginx.conf`, así que reconstruyó la
imagen de frontend y Watchtower recreó ese contenedor — y recrear el contenedor limpia la
caché de DNS por sí solo. Es el caso que el encargo advierte en su §49.

La demostración correcta exigía lo contrario: recrear el **backend** dejando el frontend
intacto. Se hizo publicando un cambio que solo toca `backend/`:

```
14:33:09  imagen de backend publicada; la de frontend no cambia
14:34:13  L2=200  L3=200
14:34:18  L2=000  L3=502   ← contenedor de backend destruido
14:34:34  L2=000  L3=502
14:34:39  L2=200  L3=200   ← recuperación automática, sin tocar el frontend
```

El ETag de `index.html` y la imagen de frontend permanecieron invariables durante todo el
ciclo: el contenedor de frontend nunca se reinició.

`L2=000` prueba que el contenedor fue destruido y no recargado. `L3=502` **solo** mientras
`L2=000`: el proxy falló durante la ausencia real del backend y ni un muestreo más.

Contraste con el mismo disparador antes del arreglo:

```
09-05 05:25   recreación → 502 durante más de 8 horas
09-05 14:34   recreación → 502 durante ~25 s, solo mientras el contenedor no existía
```

Lo que **sigue sin demostrarse** es que la IP cambiara en este ciclo concreto: no es
observable sin acceso al host. Por eso `GA-REM-027` queda **`PARTIAL`** y no `CERTIFIED`.
Detalle en
[`GA-REM-027-PROXY-RESOLUTION-CERTIFICATION.md`](GA-REM-027-PROXY-RESOLUTION-CERTIFICATION.md).

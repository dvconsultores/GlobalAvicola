# MATRIZ DE CONFIGURACIÓN DE EJECUCIÓN — AISLADO vs COMPARTIDO

**`GA-REM-027` · incidente del 502** · 2026-09-05

Comparación entre el arranque aislado que esta máquina puede ejercitar y el contenedor del
entorno compartido, para localizar dónde divergen. Es lo que §28 del encargo pide, y lo que
explica por qué el arranque local pasaba mientras la API pública no respondía.

| Requisito | Arranque aislado | Contenedor compartido | Resultado |
|---|---|---|---|
| Entrypoint ejecutado | `docker-entrypoint.sh` invocado directamente · **PASS** | no observable sin acceso · **inferido PASS** — el backend sirve, y con `set -e` no habría `exec` sin migración | coinciden |
| Directorio de trabajo | `backend/` | `/app` (Dockerfile) | no interviene en el fallo |
| Usuario | el de la sesión | `avicola` (Dockerfile) | no verificable · **`UNKNOWN`** |
| Migraciones | `i9j0k1l2m3n4 → l2m3n4o5p6q7` · **PASS** | **inferido PASS** — la aplicación responde | coinciden |
| Reconciliación RBAC | 33 → 55 permisos · **PASS** | no observable sin credencial · **`NOT_VERIFIED`** | pendiente |
| Arranque de uvicorn | **PASS** | **PASS** — `200` en el puerto publicado | coinciden |
| Variables obligatorias | declaradas por el script de prueba | presentes: el arranque las exige y la aplicación arrancó | coinciden |
| `ENVIRONMENT` | `test` | **`development`** (lo dice `/health`) | coherente con `ENV-01` |
| Puerto de escucha | 8099/8111 según el ensayo | **8000** dentro del contenedor, publicado en **8002** | correcto |
| Alcance de la escucha | `127.0.0.1` | accesible desde fuera del contenedor · **PASS** | correcto |
| Base de datos alcanzable | PostgreSQL aislado · **PASS** | **PASS** — la API responde con datos | coinciden |
| Volumen `avicola-media` | directorio temporal | **`NOT_VERIFIED`** — `R-52` sigue pendiente | no interviene en el 502 |
| **Resolución del upstream por el proxy** | **no existe**: el ensayo llama al backend directamente | **`FAIL`** — nginx resolvía `backend` una vez al arrancar | **aquí divergen** |
| Red Docker | no aplica | `avicola-network`, bridge · DNS embebido `127.0.0.11` | el arreglo se apoya en esto |

## La divergencia que importa

El arranque aislado **no ejercita el proxy**: llama al backend directamente por HTTP. Por
eso `startup_test.sh` podía pasar con 0 fallos mientras la API pública llevaba ocho horas
devolviendo `502`.

No es un defecto del ensayo: su alcance declarado es el entrypoint y el arranque, y eso lo
certifica correctamente. Es un **hueco de cobertura**: entre «el backend arranca» y «la API
responde» hay un salto —el proxy— que ninguna prueba de este repositorio recorría.

## Los tres niveles de salud, medidos

| Nivel | Qué mide | Cómo se midió | Resultado |
|---|---|---|---|
| **L1** dentro del contenedor | el proceso responde | no accesible sin servidor | **`UNKNOWN`** |
| **L2** host → backend | el contenedor escucha y responde | `http://<host>:8002/health` desde fuera | **PASS** — `{"status":"ok"}` |
| **L3** proxy público → backend | la cadena completa | `https://avicola.globaldv.net/api/v1/...` | **FAIL** — `502` |

`L2 PASS` con `L3 FAIL` localiza el fallo en el proxy, no en la aplicación. Que el puerto
`8002` esté publicado al host permitió medir `L2` **sin acceso al servidor**, que es lo que
hizo posible el diagnóstico.

## Cómo se identificó al emisor del `502`

Las cabeceras de la respuesta de error:

```
HTTP/1.1 502 Bad Gateway
Server: openresty
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

Esas cuatro cabeceras las declara `frontend/nginx.conf:10-13` con `always`, que es
precisamente lo que hace que se emitan también en las respuestas de error. Luego el `502`
lo genera el nginx del contenedor de frontend, no el `openresty` que hay delante ni el
backend.

## Corrección de un supuesto anterior

Los informes previos hablaban de «el servidor» como si fuera uno. Son dos máquinas:

```
avicola.globaldv.net  →  84.247.161.106   aplicación (openresty → nginx → backend)
backend/.env          →  64.225.104.69    base de datos
```

Los sondeos de puertos de la verificación posterior al push iban al host de la **base de
datos**, no al de la aplicación. Por eso daban tiempos de espera agotados y se leyeron como
«no alcanzable». Corregido aquí; la conclusión anterior sobre la base de datos —inalcanzable
desde esta red— sigue siendo válida, pero era sobre otra máquina.

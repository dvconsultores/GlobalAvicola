# CERTIFICACIÓN — `R-68` · FRONTERA TRANSACCIONAL

**`GA-REM-026`** · 2026-09-04 · **`CERTIFIED`**

---

## 1. El defecto

Una respuesta HTTP de éxito podía salir antes de que la transacción que la sustentaba
estuviera confirmada.

`get_db` confirmaba tras el `yield`, y FastAPI ejecuta el cierre de una dependencia con
`yield` **después** de enviar la respuesta. Afectaba a las **90 rutas de escritura** del
backend, que usan todas la misma dependencia.

## 2. Mecanismo, medido

Reproducción mínima sobre las versiones reales (FastAPI 0.138.0, Starlette 1.3.1), con un
commit artificial de 300 ms para hacer visible una carrera que en producción dura
milisegundos:

| Punto de confirmación | Respuesta | ¿Visible al leer? |
|---|--:|:--:|
| **Cierre de la dependencia** (código anterior) | 1–6 ms | **NO** |
| `BaseHTTPMiddleware`, tras `call_next` | 302 ms | sí |
| Middleware ASGI, antes de `http.response.start` | 302 ms | sí |

Sobre el sistema real, cinco altas seguidas de su lectura inmediata:

```
race_0: alta 201 -> login inmediato 200
race_1: alta 201 -> login inmediato 200
race_2: alta 201 -> login inmediato 401  | reintento tras 0,5 s: 200
race_3: alta 201 -> login inmediato 401  | reintento tras 0,5 s: 200
race_4: alta 201 -> login inmediato 401  | reintento tras 0,5 s: 200
```

Tres de cinco es evidencia de reproducción, no una estadística: el resultado depende de la
latencia relativa entre la confirmación y la petición siguiente.

## 3. Dos hallazgos que acotaron el arreglo

Conviene decirlos porque son la razón de que **no se haya reescrito nada**.

**El modelo transaccional ya era único y coherente.** 49 `flush()`, 28 `refresh()` y solo 3
`commit()` —uno la dependencia, dos excepciones documentadas del camino de evidencias—.
Los servicios preparan; la capa de petición confirma. No había dos modelos que unificar,
solo un punto mal situado.

**El manejo de errores ya era correcto.** Comprobado rama por rama:

| Caso | HTTP | Rama ejecutada |
|---|--:|---|
| Éxito | 200 | `COMMIT` → `CLOSE` |
| `HTTPException` | 404 | `ROLLBACK (HTTPException)` → `CLOSE` |
| Excepción de dominio con manejador propio | 400 | `ROLLBACK (BusinessRuleViolation)` → `CLOSE` |
| Excepción inesperada | 500 | `ROLLBACK (ValueError)` → `CLOSE` |

`AC06` y `AC07` describían comportamiento existente. El trabajo era no romperlo.

## 4. La corrección

La confirmación pasa a la capa de ruta —`RutaTransaccional`, una subclase de `APIRoute`—,
que es el último punto que se ejecuta **dentro** del manejo de excepciones de FastAPI y
**antes** de que la respuesta salga.

```python
async def manejador(request: Request) -> Response:
    respuesta = await manejador_original(request)
    sesion = getattr(request.state, "db", None)
    if sesion is not None and sesion.in_transaction():
        try:
            await sesion.commit()
        except Exception:
            await sesion.rollback()
            raise
    return respuesta
```

Tres propiedades a la vez: el dato está confirmado cuando el cliente recibe el `201`; un
fallo al confirmar se convierte en `500` por el camino normal de errores en lugar de en un
éxito mentiroso; y la reversión sigue donde estaba, en `get_db`, intacta.

```
SERVICIOS MODIFICADOS ....... 0
flush() TOCADOS ............. 0  (de 49)
FICHEROS CAMBIADOS .......... 13 (1 nuevo, database.py, main.py, 10 routers)
```

### Y una guarda, porque el arreglo tiene un riesgo propio

Si la confirmación vive en la capa de ruta, un router futuro que olvide adoptarla perdería
sus escrituras **en silencio**. `transaction.verificar(app)` recorre las rutas, detecta las
que usan la base sin estar bajo la frontera y **aborta el arranque**. Es el mismo mecanismo
—y el mismo razonamiento— que `GA-REM-002 AC08` usa para la autorización: convertir un
olvido en un fallo ruidoso hoy en lugar de en un defecto dentro de seis meses.

```
rutas totales ......... 177
usan la base .......... 175
bajo la frontera ...... 175
de escritura .......... 90/90
huérfanas ............. 0
```

## 5. Sobre el método de las pruebas

Un test que use el cliente en proceso **no puede** detectar `R-68`: `ASGITransport` ejecuta
la aplicación hasta el final —incluido el cierre de dependencias— antes de devolver la
respuesta, de modo que la carrera nunca se manifiesta y el test pasaría igual con el
defecto presente.

Por eso `AC01` se comprueba a nivel ASGI: se envuelve `send` y, en el instante exacto en
que la aplicación emite `http.response.start`, se consulta la fila **desde otra conexión**.

**Se verificó que el test no es vacío**: con el código anterior restaurado, falla.

```
AssertionError: la respuesta de éxito se emitió antes de que la transacción
                estuviera confirmada
```

## 6. Criterios de aceptación

| AC | Criterio | Prueba | Resultado |
|---|---|---|---|
| **AC01** | Ninguna respuesta de éxito antes de confirmar | `T-026-01` (ASGI, otra conexión) | **PASS** |
| **AC02** | Lectura inmediata tras crear | `T-026-02` · 30 iteraciones, sin esperas | **PASS** 30/30 |
| **AC03** | Actualización observable de inmediato | `T-026-03` · 30 iteraciones | **PASS** 30/30 |
| **AC04** | Borrado observable de inmediato | `T-026-04` · 30 iteraciones | **PASS** 30/30 |
| **AC05** | Un fallo al confirmar no da éxito | `T-026-05` · fallo inducido | **PASS** — 500, sin dato |
| **AC06** | Los errores de dominio revierten | `T-026-06` | **PASS** — 400, sin dato |
| **AC07** | Las excepciones inesperadas revierten | `T-026-07` | **PASS** — 500, sin dato |
| **AC08** | Las lecturas no confirman de más | `T-026-08` | **PASS** — 0 confirmaciones |
| **AC09** | Quien ya confirmaba no regresa ni duplica | `T-026-09` | **PASS** — 1 fila |
| **AC10** | Los identificadores devueltos son de estado confirmado | `T-026-01` | **PASS** |
| **AC11** | Cobertura uniforme de todas las rutas de escritura | `T-026-10`, `T-026-11` | **PASS** — 90/90; la guarda detecta el olvido |
| **AC12** | Regresión completa en verde | suite | **PASS** |

Y, por §22 del encargo:

| Criterio | Prueba | Resultado |
|---|---|---|
| Atomicidad multi-entidad: evento y submovimientos, juntos o nada | `T-026-12` · FK inexistente entre los dos `flush()` | **PASS** — sin evento huérfano |

## 7. Verificación funcional independiente

El recorrido de instalación limpia de `GA-REM-025`, que medía `R-68` explícitamente:

```
antes:  ❌ R-68 · el alta es visible para la petición inmediata
        — no: login inmediato HTTP 401 tras un alta con 201

ahora:  ✅ R-68 · el alta es visible para la petición inmediata

35/37 → 36/37 pasos correctos
```

## 8. Regresión

```
Backend ............ 295 pasados · 49 omitidos · 0 fallos   (112 s)
                     283 antes + 12 nuevas
Deriva de esquema .. 0     (47 tablas modelo = 47 migraciones)
Alembic ............ 1 head · 1 base · 24 revisiones
Guarda de entorno .. 25 tests
TypeScript ......... PASS
Vitest ............. 61/61
Paridad i18n ....... 866 = 866 · 0 faltantes
```

## 9. Un efecto lateral que conviene anotar

`R-68` produce fallos intermitentes que se atribuyen a otra cosa. Durante la certificación
de `GA-REM-025` generó un `BR-07 «Farm no encontrado»` al crear un galpón inmediatamente
después de su granja, y el primer diagnóstico —haber reseteado con el backend en marcha—
fue **equivocado**.

Por eso el encargo pedía medir de nuevo el baseline de Playwright sin tocar sus tests.
**Ya está medido: `R-68` no explicaba ninguno de los 23 fallos heredados** —siguen siendo
23, los mismos casos—. La hipótesis queda descartada, que era el objetivo de medir.
Detalle en [`PLAYWRIGHT_POST_R68_R67_BASELINE.md`](PLAYWRIGHT_POST_R68_R67_BASELINE.md).

Tiene sentido: el efecto de `R-68` aparece en secuencias escritura→lectura inmediata que
esos tests no ejecutan. Se descubrió por el recorrido de instalación limpia, no por
Playwright.

## 10. Veredicto

```
NO HTTP SUCCESS BEFORE REQUIRED COMMIT ... cumplido
READ-AFTER-WRITE ......................... determinista, 90/90 iteraciones
ROLLBACK ................................. PASS
COMMIT FAILURE ........................... controlado
FULL BACKEND ............................. GREEN

R-68 = CERTIFIED
```

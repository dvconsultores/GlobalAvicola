# MATRIZ DE FRONTERAS TRANSACCIONALES

**`R-68` · `GA-REM-026`** · 2026-09-04 · inventario previo a cualquier cambio de código

---

## 1. Qué se midió y cómo

Se inventariaron todas las operaciones transaccionales de `backend/app/` y se enumeraron
las rutas reales de la aplicación con `authorization_coverage.enumerar_rutas`, que recorre
los routers incluidos —necesario, porque FastAPI 0.138 no aplana las rutas en `app.routes`
sino que conserva objetos `_IncludedRouter` perezosos.

```
rutas API totales ....... 177
de escritura ............  90
de solo lectura .........  87
```

## 2. Resumen por módulo

| Módulo | Endpoints de escritura | add/delete | flush | commit | refresh | rollback | Propietario de la transacción |
|---|--:|--:|--:|--:|--:|--:|---|
| `(raíz)` | 0 | 0/0 | 0 | 1 | 0 | 1 | define el boundary (`get_db`) |
| `audit` | 0 | 1/0 | 1 | 0 | 0 | 0 | **dependencia** |
| `auth` | 9 | 3/0 | 7 | 0 | 4 | 0 | **dependencia** |
| `corrections` | 1 | 1/0 | 1 | 0 | 2 | 0 | **dependencia** |
| `integrations` | 4 | 7/0 | 8 | 0 | 0 | 0 | **dependencia** |
| `lots` | 7 | 5/0 | 6 | 0 | 6 | 0 | **dependencia** |
| `masters` | 0 | 1/0 | 3 | 0 | 2 | 0 | **dependencia** |
| `operations` | 7 | 10/1 | 7 | 2 | 6 | 0 | dependencia + **2 commit propios** |
| `review` | 12 | 9/2 | 16 | 0 | 8 | 0 | **dependencia** |
| **total** | **40** | 37/3 | **49** | **3** | 28 | 1 | |

`masters` figura con 0 endpoints de escritura en el recuento por decorador porque los
registra con `add_api_route` desde `register_crud`; en la aplicación real aporta **50** de
las 90 rutas de escritura.

## 3. Distribución real de las 90 rutas de escritura

| Área | Rutas |
|---|--:|
| `masters` (19 entidades × CRUD) | 50 |
| `lots` | 7 |
| `operations` | 7 |
| `users` | 4 |
| `review` · `approvals` · `approval-steps` | 12 |
| `sap` | 4 |
| `roles` | 2 |
| `login` · `refresh` · `switch-company` | 3 |
| `corrections` | 1 |

## 4. El patrón dominante

**49 `flush()` · 28 `refresh()` · 3 `commit()`.**

Los servicios **no confirman**: preparan el trabajo con `flush()` —que envía el `INSERT` y
obtiene el identificador generado sin cerrar la transacción— y dejan la confirmación a
quien sea dueño de la frontera. Es un patrón coherente y deliberado, y sostenido en 49
sitios.

```
PROPIETARIO DE LA TRANSACCIÓN = CAPA DE PETICIÓN
```

No hay ambigüedad que resolver: el proyecto ya tiene un modelo único. Lo que falla no es
el modelo, es **dónde** ejecuta su confirmación.

## 5. Las dos excepciones

| Ubicación | Qué hace | Lectura |
|---|---|---|
| `operations/service.py:664` | `upload_evidence`: escribe el fichero en disco, añade la fila y confirma | confirmación temprana **deliberada**: empareja un efecto en el sistema de ficheros con su fila |
| `operations/service.py:686` | `delete_evidence`: borra el fichero y confirma la baja de la fila | ídem |

Son las únicas dos confirmaciones fuera de la frontera, y tienen una razón explícita, así
que se conservan. Confirmar antes no es el defecto de `R-68`; el defecto es confirmar
**después de responder**.

Queda anotado, fuera del alcance de `GA-REM-026`: en ambas el fichero se toca antes de
confirmar, de modo que un fallo posterior deja disco y base desacompasados. Es un hueco de
atomicidad preexistente entre dos sistemas distintos, no una frontera transaccional mal
puesta.

## 6. La frontera actual, y por qué está mal puesta

```python
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()      # ← se ejecuta DESPUÉS de enviar la respuesta
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

Medido con una reproducción mínima sobre las mismas versiones (FastAPI 0.138.0,
Starlette 1.3.1), con un «commit» de 300 ms:

| Punto de confirmación | Respuesta | ¿Visible al leer inmediatamente? |
|---|--:|:--:|
| **Cierre de la dependencia** (actual) | 1–6 ms | **NO** |
| `BaseHTTPMiddleware` tras `call_next` | 302 ms | sí |
| Middleware ASGI, antes de `http.response.start` | 302 ms | sí |

La respuesta sale mientras la transacción sigue abierta. En el sistema real la
confirmación tarda milisegundos y a veces gana la carrera; de ahí que el defecto sea
**intermitente**.

## 7. El manejo de errores ya es correcto

Conviene decirlo porque acota el arreglo. Se comprobó qué rama del generador se ejecuta en
cada caso:

| Caso | HTTP | Rama ejecutada |
|---|--:|---|
| Éxito | 200 | `COMMIT` → `CLOSE` |
| `HTTPException` | 404 | `ROLLBACK (HTTPException)` → `CLOSE` |
| Excepción de dominio con manejador propio | 400 | `ROLLBACK (BusinessRuleViolation)` → `CLOSE` |
| Excepción inesperada | 500 | `ROLLBACK (ValueError)` → `CLOSE` |

Las excepciones **sí** se propagan al generador y revierten. `AC06` y `AC07` describen
comportamiento que ya existe; el trabajo es no romperlo.

## 8. Alcance del cambio

Lo anterior descarta la reescritura. No hay que tocar servicios, ni repositorios, ni los
49 `flush()`. El defecto está en **un punto**: cuándo se ejecuta la confirmación del camino
de éxito.

```
AFECTADAS ....... 90 rutas de escritura, todas por la misma dependencia
CAUSA RAÍZ ...... 1 punto (get_db)
SERVICIOS ....... 0 modificados
```

## 9. Riesgo residual identificado

Si la confirmación pasa a la capa de ruta, un router futuro que no la adopte perdería sus
escrituras **en silencio**. Ese riesgo se cierra con una comprobación de cobertura que
impide el arranque, el mismo mecanismo que `GA-REM-002 AC08` usa para la autorización.

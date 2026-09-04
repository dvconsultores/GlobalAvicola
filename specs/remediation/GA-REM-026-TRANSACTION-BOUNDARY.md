# GA-REM-026 — FRONTERA TRANSACCIONAL DE LA PETICIÓN

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-026` · **Tipo** `DATA INTEGRITY + REQUEST LIFECYCLE SPEC` |
| **Prioridad** | **P0 · sistémica** |
| **Estado** | `SPEC_READY` |
| **Origen** | `R-68`, descubierto por el baseline limpio de `GA-REM-025` |
| **Dependencias** | ninguna. **Bloquea** a `GA-REM-016` (puede producir falsos negativos en E2E) |
| **Detectado** | 2026-09-04 |

## Problema

Una respuesta HTTP de éxito puede salir antes de que la transacción que la sustenta se
haya confirmado.

`get_db` confirma en el cierre de la dependencia con `yield`, y FastAPI ejecuta ese cierre
**después** de enviar la respuesta. Reproducido con una instalación mínima sobre las mismas
versiones, con un commit artificial de 300 ms: la respuesta sale en 1–6 ms y la lectura
inmediata no ve el dato. Sobre el sistema real, donde el commit tarda milisegundos, el
efecto es intermitente:

```
race_0: alta 201 -> login inmediato 200
race_1: alta 201 -> login inmediato 200
race_2: alta 201 -> login inmediato 401  | reintento tras 0,5 s: 200
race_3: alta 201 -> login inmediato 401  | reintento tras 0,5 s: 200
race_4: alta 201 -> login inmediato 401  | reintento tras 0,5 s: 200
```

Tres de cinco es evidencia de reproducción, no una estadística: el resultado depende de la
latencia relativa entre la confirmación y la siguiente petición.

### Por qué es sistémica y no un caso aislado

Las **90 rutas de escritura** del backend usan la misma dependencia. Ninguna es inmune.

Lo que la hace difícil de ver es que no falla ruidosamente: devuelve `201`, el dato acaba
existiendo, y el fallo aparece solo si alguien lee de inmediato. Produce, por tanto,
síntomas que se atribuyen a otra cosa. Durante la propia certificación de `GA-REM-025`
generó un `BR-07 «Farm no encontrado»` al crear un galpón justo después de su granja, y el
primer diagnóstico —haber reseteado con el backend en marcha— fue **equivocado**.

Un test E2E que crea un recurso y lo consulta a continuación falla de forma intermitente,
sin motivo aparente y sin que el código bajo prueba tenga nada malo.

### Lo que la investigación acota

Dos hallazgos reducen el alcance del arreglo, y conviene tenerlos delante antes de tocar
nada:

**El modelo transaccional del proyecto ya es único y coherente.** 49 `flush()`, 28
`refresh()` y solo 3 `commit()` —uno es la propia dependencia y dos son excepciones
documentadas del camino de evidencias—. Los servicios preparan, la capa de petición
confirma. No hay dos modelos que unificar.

**El manejo de errores ya es correcto.** Se comprobó rama por rama: `HTTPException`,
excepción de dominio con manejador propio y excepción inesperada **revierten** las tres.
Las excepciones se propagan al generador. `AC06` y `AC07` describen comportamiento
existente; el trabajo consiste en no romperlo.

De ahí que esta spec **no autorice** reescribir servicios ni repositorios. La causa raíz
está en un punto.

## Alcance

1. Mover la confirmación del camino de éxito a un punto que se ejecute **antes** de que la
   respuesta salga.
2. Impedir que una ruta futura quede fuera de esa frontera, con una comprobación que
   rompa el arranque.
3. Pruebas de lectura-tras-escritura, actualización, borrado, reversión, fallo de
   confirmación y atomicidad multi-entidad.

## Fuera de alcance

Reescritura de servicios o repositorios · cambios en los 49 `flush()` · las dos
confirmaciones explícitas del camino de evidencias, que tienen razón documentada · el hueco
de atomicidad entre disco y base en esas mismas rutas, preexistente y entre dos sistemas
distintos · `sleep` o reintentos en cualquier capa, expresamente prohibidos como solución.

## Principio normativo

> Una respuesta HTTP de éxito para una mutación síncrona no puede enviarse antes de que la
> transacción requerida haya sido confirmada satisfactoriamente.

## Acceptance Criteria

| AC | Criterio | Verificación |
|---|---|---|
| **AC01** | La respuesta de una creación con éxito no se emite hasta que la transacción ha confirmado | prueba de ordenación |
| **AC02** | Un `GET` inmediatamente posterior a una creación con éxito devuelve el recurso | 30 iteraciones sin espera |
| **AC03** | Una actualización con éxito es observable de inmediato | 30 iteraciones |
| **AC04** | Un borrado con éxito es observable de inmediato | 30 iteraciones |
| **AC05** | Un fallo de confirmación no puede producir un HTTP de éxito | fallo inducido |
| **AC06** | Los errores de dominio revierten la transacción activa | `BusinessRuleViolation` |
| **AC07** | Las excepciones inesperadas revierten la transacción activa | excepción inducida |
| **AC08** | Las peticiones de solo lectura no provocan confirmaciones innecesarias | sesión sin uso no confirma |
| **AC09** | Los flujos que ya gestionan su transacción explícitamente no confirman dos veces ni regresan | camino de evidencias |
| **AC10** | Los identificadores y valores por omisión que genera la base y se devuelven al cliente reflejan estado confirmado | comparación respuesta ↔ base |
| **AC11** | La corrección se aplica de forma uniforme a **todas** las rutas de escritura | comprobación de cobertura en arranque |
| **AC12** | La regresión completa del backend sigue en verde | suite |

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Una ruta o router futuro queda fuera de la frontera y pierde escrituras en silencio | `AC11`: comprobación de cobertura que **impide el arranque**, el mismo mecanismo de `GA-REM-002 AC08` |
| Confirmar en el camino de solo lectura añade coste | `AC08`: no se confirma una sesión que nunca abrió transacción |
| Cambiar la semántica de error al mover el punto de confirmación | `AC06`/`AC07` fijan el comportamiento actual como criterio, no como aspiración |
| Doble confirmación en el camino de evidencias | `AC09`: confirmar una sesión ya confirmada es inocuo; se verifica |

## Definition of Done

- `AC01`…`AC12` con evidencia.
- `TRANSACTION_BOUNDARY_MATRIX.md` publicada.
- Informe de certificación de `R-68`.
- Regresión completa en verde.
- Nuevo baseline de Playwright congelado para medir cuántos fallos eran síntoma de esto.

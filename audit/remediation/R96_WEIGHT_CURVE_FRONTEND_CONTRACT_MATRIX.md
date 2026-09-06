# `R-96` · CONTRATO DE FRONTEND PARA LAS CURVAS DE PESO

`OD-06` · `GA-REM-037` · `spec.md §4.5` · 2026-09-06 · **antes de tocar React**

Esta matriz no diseña la pantalla desde un enunciado: la deriva del **contrato que el
backend expone hoy**, leído del `openapi()` en ejecución y de los esquemas Pydantic, no de
la memoria ni de la spec.

---

## 1. Corrección de gobernanza previa

El checkpoint anterior concluyó que, al no tener `GA-REM-037` ningún criterio de frontend, la
pantalla quedaba fuera de alcance. **Esa conclusión era incorrecta.** `OD-06` dice que cada
línea genética puede tener su tabla y que **esa tabla debe poder cargarse dentro de Global
Avícola**. Un requisito del propietario no desaparece porque la spec que lo desarrolla se
dejara incompleta:

```
OWNER REQUIREMENT  >  INCOMPLETE SPEC
```

De modo que `R-96` no es deuda técnica ni backlog:

```
R-96 = MISSING PRODUCT CAPABILITY + SPEC COVERAGE GAP
```

Y mientras siga abierto, `P-03` vuelve a **`PARTIAL`**: que `POST /masters/weight-curves`
responda `201` no es que el administrador pueda cargar la curva. `GA-REM-016 AC05` ya lo dice
en general —la unidad certificada es el proceso de negocio, no el endpoint—.

## 2. Endpoints reales

Leídos de `app.openapi()`. **No hay ningún otro**:

| # | UI capability | Endpoint | Request | Response | Permiso | ¿Necesario? |
|:--:|---|---|---|---|---|:--:|
| 1 | Listar líneas genéticas | `GET /masters/genetic-lines` | `skip`, `limit`, `search` | `GeneticLineRead[]` + `X-Total-Count` | `masters:read` | **sí** — ya usado por `MasterListPage` |
| 2 | Ver versiones de una línea | `GET /masters/genetic-lines/{id}/weight-curves` | — | `WeightCurveRead[]`, más reciente primero | `masters:read` | **sí** |
| 3 | Cargar una versión con su tabla | `POST /masters/weight-curves` | `WeightCurveCreate` (JSON) | `WeightCurveRead` · `201` | `masters:create` | **sí** |
| 4 | Ver una versión y sus puntos | `GET /masters/weight-curves/{id}` | — | `WeightCurveRead` con `points` | `masters:read` | **sí** |
| 5 | Activar una versión | `PUT /masters/weight-curves/{id}/activate` | — | `WeightCurveRead` | `masters:update` | **sí** |
| 6 | Crear lote con línea genética | `POST /lots` | `LotCreate` con `genetic_line_id`, `weight_curve_id?` | `LotRead` con `weight_curve_id` | `lots:create` | **sí** — ya existe |
| 7 | Ver alertas de un lote | `GET /operations/alerts?lot_id=` | `lot_id`, `is_resolved`, `skip`, `limit` | `OperationalAlertRead[]` | `operations:read` | **sí** |

**No existe**: `DELETE`, desactivar explícito, archivar, `PUT` de edición de la curva, endpoint
de *preview* o *validate* separado, ni endpoint que diga si una curva está referenciada por
algún lote.

## 3. Formas exactas

### `WeightCurveCreate` — lo que acepta el alta

| Campo | Tipo | Obligatorio | Nota |
|---|---|:--:|---|
| `genetic_line_id` | `int` | **sí** | la tenencia se comprueba sobre la línea |
| `version_label` | `str` (1–50) | **sí** | **no** `version` — ver `R-32` y §5 de esta matriz |
| `source` | `str?` (≤200) | no | procedencia de la tabla |
| `is_active` | `bool` | no · `false` | activar en el mismo alta |
| `points` | `WeightCurvePointIn[]` (≥1) | **sí** | la tabla entera viaja aquí |

### `WeightCurvePointIn` — una fila

| Campo | Tipo | Obligatorio |
|---|---|:--:|
| `age_days` | `int ≥ 0` | **sí** |
| `min_weight` | `float > 0` | **sí** |
| `max_weight` | `float > 0` | **sí** |
| `target_weight` | `float > 0`, opcional | no |

### Errores de carga

`422` con un cuerpo propio, distinto del `422` de Pydantic:

```json
{"detail": {"mensaje": "La tabla se rechazó entera",
            "errores": [{"fila": 2, "campo": "min_weight", "motivo": "…"}]}}
```

`409` si la línea ya tiene esa `version_label`. `404` si la línea no es del usuario.

## 4. El formato del archivo — lo que el backend admite de verdad

**El backend recibe JSON, no multipart.** No hay parser de XLSX ni de CSV en el servidor: la
tabla llega ya estructurada en `points`.

Eso decide dos cosas que `§18`, `§20` y `§73` del encargo dejan condicionadas al contrato:

- Se envía **JSON**, no `FormData`. No se inventa un endpoint multipart.
- El cliente **sí** convierte la tabla a filas, porque *«backend contract exige datos
  estructurados desde cliente»* es exactamente el caso que `§20` exceptúa. La conversión se
  limita a separar filas y columnas y a convertir a número: **ninguna regla de negocio**.

## 5. `version_label`, y por qué no volver a `version`

`R-32` barre los esquemas de escritura buscando campos que fija el servidor, y `version` está
en esa lista. El identificador de la revisión de curva lo escribe el administrador. Se renombró
en el checkpoint anterior; el frontend debe enviar `version_label` y nunca `version`.

## 6. Validación — quién manda

| Regla | Dónde |
|---|---|
| archivo/tabla presente · etiqueta de versión no vacía | cliente, solo experiencia |
| extensión permitida | cliente, solo experiencia |
| `age_days` duplicado | **backend** (`AC04`) |
| `min > max` | **backend** (`AC03`) |
| `target` fuera del rango | **backend** (`AC03`) |
| `age_days` negativo | **backend** (Pydantic `ge=0`) |
| versión repetida en la línea | **backend** (`409`) |
| curva de otra línea sobre un lote | **backend** (`AC10`) |

El cliente no repite ninguna de las de abajo. Repetirlas crearía un segundo juez.

## 7. `R-97` · brecha de contrato para la pantalla de pesaje

Aquí aparece un hueco **real**, y se registra como hallazgo en vez de taparlo con un cálculo
en React:

```
El motor de evaluación (app/operations/weight_curve.py) tiene UN SOLO consumidor:
el generador de alertas, y solo actúa cuando el peso está FUERA de rango.
```

Consecuencia medible sobre el contrato vigente:

| Situación | ¿El frontend puede saberlo hoy? |
|---|:--:|
| `BELOW_STANDARD` | **sí** — hay `OperationalAlert` con `threshold_value` y `actual_value` |
| `ABOVE_STANDARD` | **sí** — ídem |
| `WITHIN_STANDARD` | **no** — no se emite alerta y ningún endpoint devuelve el rango esperado |
| `NO_REFERENCE` | **no** — tampoco se emite alerta; es **indistinguible** de «dentro de norma» |
| Rango esperado a una edad | **no** — solo aparece incrustado en el texto del mensaje de alerta |

`§39` del encargo pide mostrar *«Rango esperado: 1.320–1.460 g»* también cuando el peso es
normal, y `§40` exige que `NO_REFERENCE` **nunca** se represente como normal. Con el contrato
actual, «sin alerta» significa las dos cosas a la vez. Deducirlo en React exigiría interpolar
en el cliente, que es precisamente lo que `§38` prohíbe y lo que produciría dos motores.

```
R-97 = CONTRACT GAP
       la evaluación de curva no es observable salvo cuando genera alerta
```

Se resuelve por el camino que `§74` fija —`FINDING → SPEC → AC → backend change`—: se añade a
la enmienda de `GA-REM-037` un criterio de backend que exponga la evaluación, sin duplicar el
motor y sin tocar el que ya está certificado.

## 8. Alcance de UI que esta matriz autoriza

| Capacidad | Superficie | Justificación |
|---|---|---|
| Acceso a las curvas de una línea | acción por fila en el maestro `genetic-lines` existente | `§14`: la exigencia es la capacidad, no una página nueva |
| Lista de versiones con estado | vista de curvas de la línea | `OD-06` · versionado |
| Carga de una versión | diálogo sobre el patrón de `P-12` | `OD-06` · «debe poder cargarse» |
| Activación | acción sobre una versión | `OD-06` · versión activa |
| Detalle con puntos | vista de una versión | `§22` |
| Línea genética y versión en el alta de lote | `LotFormPage`, ya existente | `§31`, `§32` |
| Evaluación del pesaje | pantalla de operación, ya existente | `§36`…`§41` — **depende de `R-97`** |

**Fuera de alcance, explícitamente**: borrado físico de curvas (`§30`, el backend no lo
ofrece), acción de reasignar lotes a una curva nueva (`§28`, `OD-06` lo prohíbe), endpoint de
*preview* (`§21`, no existe y no se inventa), y cualquier canal de notificación (`§42`, es
`P-14`).

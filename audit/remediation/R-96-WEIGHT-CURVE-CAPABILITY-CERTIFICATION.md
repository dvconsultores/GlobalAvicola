# `R-96` · `R-97` — LA CAPACIDAD DE CARGAR LA CURVA, EN EL PRODUCTO

`OD-06` · `GA-REM-037` enmienda A · `spec.md §4.5` · 2026-09-06

```
R-96 = CERTIFIED       R-97 = CERTIFIED
GA-REM-037 = CERTIFIED (backend + producto)
```

---

## 1. Qué se corrigió antes de escribir una línea de código

El checkpoint anterior cerró `P-03` dejando dicho, como alcance excluido:

> *No hay pantalla de administración de curvas. `GA-REM-037` no tiene ningún criterio de
> frontend y la modalidad de evidencia es `API_E2E`, de modo que construirla sería trabajo sin
> spec.*

El razonamiento iba al revés. `OD-06` dice que cada línea genética puede tener su tabla y que
**esa tabla debe poder cargarse dentro de Global Avícola**. Que la spec no desarrollara el
punto no elimina el requisito: demuestra que la spec estaba incompleta.

```
OWNER REQUIREMENT  >  INCOMPLETE SPEC
```

`GA-REM-016 AC05` ya daba el criterio de proceso: *«ninguna unidad certificada es una pantalla,
un endpoint o un componente»*. Certificar `P-03` porque `POST /masters/weight-curves` devuelve
`201` era certificar un endpoint.

```
R-96 = MISSING PRODUCT CAPABILITY + SPEC COVERAGE GAP     (estaba como P2 "backlog")
P-03 = PARTIAL                                            (revertido desde CERTIFIED)
```

La corrección se hizo por enmienda sobre `GA-REM-037` y no por spec nueva: es la autoridad
natural de `OD-06`, y partir la misma decisión del propietario en dos documentos habría creado
el problema que este programa persigue.

## 2. `R-97`, que apareció al mirar el contrato de verdad

La matriz `R96_WEIGHT_CURVE_FRONTEND_CONTRACT_MATRIX.md` se construyó leyendo el `openapi()` en
ejecución, no la memoria. Ahí salió un hueco que ninguna pantalla podía sortear:

```
El motor de evaluación tenía UN SOLO consumidor —el generador de alertas—
y solo actuaba cuando el peso quedaba FUERA de rango.
```

| Situación | ¿Observable antes? |
|---|:--:|
| `BELOW_STANDARD` · `ABOVE_STANDARD` | sí, vía `OperationalAlert` |
| `WITHIN_STANDARD` | **no** |
| `NO_REFERENCE` | **no** — indistinguible de «dentro de norma» |
| Rango esperado a una edad | **no** — solo dentro del texto del mensaje |

«Sin alerta» significaba dos cosas opuestas a la vez. Deducir cuál habría exigido interpolar en
React, que es exactamente lo que produce dos motores. Se expuso lo que ya se calculaba:

```
GET /operations/{event_id}/weight-evaluation
→ estado, rango esperado, versión de curva, edad, y el motivo cuando falta la referencia
```

`evaluar_pesajes()` es ahora el único camino: la alerta pasó a consumirlo en vez de tener su
propia copia. Un test lo fija —`T-037-28` compara el umbral de la alerta con el de la lectura—,
de modo que si alguna vez divergieran, se sabría.

## 3. Lo que se construyó, y lo que no

| Pieza | Archivo |
|---|---|
| Lectura de la evaluación | `backend/app/operations/router.py` · `service.evaluar_pesajes` |
| Acción por fila en el maestro | `frontend/src/components/data-table/DataTable.tsx` |
| Pantalla de curvas de una línea | `frontend/src/pages/masters/WeightCurvesPage.tsx` |
| Cliente tipado del contrato | `frontend/src/services/weightCurves.ts` |
| Evaluación en el detalle del pesaje | `frontend/src/components/operations/WeightEvaluation.tsx` |
| Aviso de curva en el alta de lote | `frontend/src/pages/lots/LotFormPage.tsx` |

**No se creó un módulo de primer nivel.** Las curvas cuelgan de la línea genética, que ya era un
maestro con pantalla (`GA-REM-033`). El requisito de `OD-06` es la capacidad, no una página; una
página aparte habría sido decisión nuestra disfrazada de requisito.

**No se creó un segundo sistema de administración.** Lista, diálogos, estado vacío, carga y
error salen del patrón que `P-12` certificó.

**No hay motor en el cliente.** `parsearTabla` separa filas y columnas y convierte a número. No
comprueba edades repetidas, ni que el mínimo no supere al máximo, ni que el objetivo caiga en el
rango: eso lo juzga el backend y solo el backend. Hay un test que lo fija —una tabla incoherente
se envía **tal cual**, porque filtrarla en el cliente daría una carga «correcta» a la que le
faltan filas en vez del rechazo entero que `AC06` exige—.

**No se inventó multipart.** El backend recibe JSON; el cliente envía JSON. El único motivo por
el que el cliente convierte la tabla es que el contrato pide los puntos ya estructurados.

## 4. Dos decisiones sobre la presentación

**El estado se lee, no se adivina por el color.** «Activa» e «Inactiva» son texto. Un test lo
comprueba con coincidencia **exacta**, porque «Inactiva» contiene «activa» como subcadena y una
expresión laxa habría dado por bueno justo el estado contrario. El primer intento de la prueba
tenía ese defecto y lo delató el propio ejecutor.

**La ausencia de referencia se nombra.** Sin curva, sin línea genética o con una edad fuera de
la tabla, la pantalla dice «Sin referencia de curva» y explica por qué. No pinta cero —un cero
sería un rango de verdad y engañaría igual— ni deja el hueco vacío, que es lo que hacía antes y
lo que un usuario leería como «el peso está bien».

## 5. `AC-FE16`, dicho con precisión

Lo que se verificó: un usuario **sin** permiso sobre maestros no puede administrar curvas, y la
pantalla presenta la negativa en vez de quedarse muda. Control y tratamiento con
`test_approver`, que tiene `operations:read` y las acciones de aprobación pero ninguna sobre
`masters`. No se usó el Super Administrador: su exención habría hecho pasar la prueba sin
comprobar nada.

Lo que **no** se verificó, porque no existe: ocultar botones según el permiso del usuario.
Ninguna pantalla de esta aplicación lo hace — `/me` no expone la lista de permisos y no hay
modelo de permisos en el frontend. Construirlo para las curvas habría creado una excepción
incoherente con las otras diecinueve pantallas de maestros, y es trabajo de `P-13`, no de aquí.
Queda registrado como **`R-98`**.

La autoridad sigue en el backend, como `§57` del encargo exige: ocultar un botón no autoriza
nada, y aquí no se ocultó ninguno para fingir que sí.

## 6. Evidencia

| Nivel | Archivo | Resultado |
|---|---|:--:|
| Lectura de la evaluación | `backend/tests/test_weight_evaluation_endpoint.py` | **10/10** |
| Capacidad en el producto | `e2e/proceso-p03-curvas-ui.spec.ts` | **13/13** `UI_E2E` |
| Conversión de la tabla | `frontend/src/services/__tests__/weightCurves.test.ts` | **6/6** |
| Presentación del veredicto | `frontend/src/components/operations/__tests__/WeightEvaluation.test.tsx` | **7/7** |
| `tsc --noEmit` | — | **limpio** |
| Paridad `i18n` | `es` / `en` | **917 = 917** |
| Regresión backend | suite completa | **449 passed · 49 skipped** (antes 439) |
| Regresión `E2E` | 16 suites | **124 passed** (antes 111) |
| Regresión `vitest` | suite completa | **74 passed** |

**Sobre la modalidad.** La nota original de `GA-REM-037` fijaba `API_E2E` alegando que `§4.5` no
exige que el usuario vea nada. Para las **alertas** sigue siendo cierto. No lo es para la
**carga de la curva**: `OD-06` exige que el usuario pueda cargarla dentro del producto, y una
capacidad operativa no se demuestra por API. De ahí que estos criterios sean `UI_E2E`. No se
fabricó `UI_E2E` por vocabulario.

## 7. Sensibilidad · `GA-REM-016 AC13`

Once mutaciones antes de esta entrega y siete en ella, todas revertidas:

| # | Mutación | Rompe | Fallos |
|:--:|---|---|:--:|
| UI-1 | Se retira el acceso a las curvas desde la línea genética | `AC-FE01` | 1 |
| UI-2 | El mapeo de la petición fija `version_label` | `AC-FE04` | 1 |
| UI-3 | `NO_REFERENCE` se presenta como «dentro de norma» | `AC-FE13` | 1 |
| UI-4 | Se ocultan `BELOW` y `ABOVE` | `AC-FE11`, `AC-FE12` | 1 |
| BE-1 | La lectura confunde «sin referencia» con «dentro de norma» | `AC27` | 3 |
| BE-2 | La lectura deja de filtrar por empresa | `AC28` | 1 |
| BE-3 | El motor extrapola fuera de la tabla | `AC18`, `AC27` | 15 |

## 8. Un fallo de método que conviene registrar

La mutación **BE-2** se revirtió con `git checkout` sobre el archivo del router. Ese archivo
contenía además el endpoint **recién escrito y sin confirmar**, de modo que la reversión lo
borró junto con la mutación.

Lo grave no fue la pérdida —el archivo se reescribió en un minuto— sino que **la comprobación
de residuo lo dio por limpio**: `git diff` no mostraba ninguna línea sospechosa porque el
código sospechoso ya no existía. La suite completa lo delató con diez fallos, y no la guarda
que se supone que vigila esto.

```
git checkout <archivo>   revierte al ÚLTIMO COMMIT, no a antes de la mutación
                         y con trabajo sin confirmar, destruye lo que no debía tocar
```

Las demás mutaciones se revirtieron copiando una salvaguarda previa, que es lo correcto. Se
deja escrito porque es la misma clase de defecto que el programa persigue en el producto: un
indicador que parece medir el estado y mide otra cosa.

## 9. Lo que queda fuera, dicho

- **`R-98`**: no hay modelo de permisos en el frontend; ninguna pantalla oculta acciones de
  escritura según el rol. Es transversal y pertenece a `P-13`.
- **Borrado de curvas**: el backend no lo ofrece y el histórico se conserva. No se inventó.
- **Endpoint de *preview***: no existe; no se creó. La validación llega del rechazo real.
- **`P-14`**: intacto. La alerta es un registro y la evaluación una lectura. Sin correo, sin
  push, sin centro de notificaciones.
- **`RC-07`**: sin tocar.

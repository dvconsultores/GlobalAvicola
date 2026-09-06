# `P-12` · GESTIÓN DE DATOS MAESTROS — INFORME DE CERTIFICACIÓN

`docs/02 §3.2` · `GA-REM-033` · 2026-09-06

```
P-12 = CERTIFIED
R-89 = CERTIFIED   R-90 = CERTIFIED   R-91 = CERTIFIED
```

---

## 1. La auditoría bidireccional, que esta vez se hizo antes

La lección de `R-87`/`R-88` era reciente: registré dos huecos mirando un solo lado y los dos
eran falsos. Aquí cada supuesto hueco se comprobó en **backend y frontend** antes de anotarlo.

La hipótesis se confirmó —siete maestros sin gestión— pero con dos matices que cambiaron el
trabajo:

| Lo que parecía | Lo que era |
|---|---|
| «construir siete pantallas» | la administración está **parametrizada**: una sola `MasterListPage` y una lista que genera las rutas. Añadir un catálogo es **añadir una entrada** |
| «faltan pantallas» | faltaban **también** los esquemas de actualización: exponerlos con un botón «editar» habría dado `405` |

## 2. Los tres huecos

**`R-90` (P1).** Siete maestros que `docs/02 §3.2` exige no estaban en `masterEntities`
(`App.tsx:94`), la única fuente de rutas de maestros. `productive-phases` gobierna la fase de
un lote, `cull-causes` es obligatoria al registrar un descarte y `correction-types` al
corregir: hoy solo podían poblarse por API o por SQL.

**`R-91` (P2).** Los mismos siete pasaban `None` como esquema de actualización, de modo que
`register_crud` no registraba su `PUT`. Una errata obligaba a duplicar el registro.

**`R-89` (P2).** `masters/router.py` calculaba el total y lo descartaba. La interfaz mostraba
el tamaño de la página donde promete «resultados», y decidía con ese número si enseñaba la
paginación.

## 3. Una enmienda a mi propia spec, con su motivo

`AC01` decía que el listado devolvería `{"items", "total"}`, siguiendo el contrato de
`/audit`, `/corrections` y `/review`.

Al implementarlo conté los consumidores: **43 puntos del frontend** leen `/masters/*` como
lista —los desplegables de los formularios operativos, entre ellos—, mientras que los
endpoints con envoltorio tienen un consumidor cada uno.

Cambiar la forma del cuerpo habría convertido un defecto **P2 de contador** en un cambio de 43
puntos de llamada. `§51` del encargo lo prohíbe expresamente. Se enmendó `AC01` **antes** de
implementar: el total viaja en `X-Total-Count`, la convención estándar para exactamente esto,
y la divergencia queda dicha en la spec en vez de descubrirse leyendo el código.

## 4. Lo que se dejó como estaba, y por qué

| | Motivo |
|---|---|
| `BirdTypeEnum` y `EventStatus` | `§3.2` los lista, pero **gobiernan la lógica del proceso**: el tipo de ave selecciona la cadena productiva, el estado gobierna el flujo de revisión. Editables permitirían crear un valor que ninguna rama sabe atender |
| el backend de los doce completos | no se toca lo que ya cumple |
| borrado físico | los 19 modelos declaran `is_active` y el `DELETE` genérico da de baja. No se añade |
| `company_id` y `hatchery_id` en los esquemas nuevos | mover un maestro de empresa o de planta por la puerta de la edición es la escritura entre inquilinos de `R-42` y `R-59`. Cambiar de padre es un traslado, no una corrección |

## 5. La cadena, paso a paso

| # | Paso | Estado |
|:--:|---|:--:|
| 1 | consultar con búsqueda, paginación y **total** | **PASS** — `AC01` `AC02` `AC03` |
| 2 | dar de alta | **PASS** 19/19 |
| 3 | editar | **PASS** 19/19 — `AC05` |
| 4 | dar de baja **lógica** | **PASS** 19/19 — `AC07` |
| 5 | usar el maestro en la operación que lo exige | **PASS** — `AC10` |
| 6 | aislamiento entre empresas | **PASS** |
| 7 | pertenencia del padre | **PASS** — `AC08` |
| 8 | permiso obligatorio | **PASS** — `AC11` |

```
8 pasos · PASS 8 · FAIL 0
```

El paso 5 es el que separa certificar un proceso de certificar una pantalla: una causa de
descarte creada desde la gestión se selecciona en un `cull_recording` real.

## 6. Evidencia

### Fase roja

| Prueba | Con el código anterior |
|---|---|
| edición de los siete | **405 Method Not Allowed** ×6 |
| el listado expone el total | la respuesta era una lista sin cabecera |

Seis rojas por la causa exacta; las de baja lógica, pertenencia, permiso y uso ya pasaban —el
backend estaba bien en esos puntos y no se tocó.

### Puerta de sensibilidad

| Mutación | Fallan | Restaurado |
|---|:--:|:--:|
| el listado vuelve a descartar el total | **1** | 11/11 |
| un maestro vuelve a `None` como esquema | **1** | 11/11 |
| el esquema deja de declarar `name` | **1** | 11/11 |

Cada una golpea exactamente lo suyo. `git diff` tras revertir: solo lo previsto.

### El caso de interfaz

`AC03` es el **primer criterio de este programa que exige `UI_E2E`**, y por requisito, no por
vocabulario: lo que `R-89` rompía es el número que el usuario **lee**, y eso no se comprueba
por API. El conjunto tiene 25 registros con páginas de 20 —con menos, el tamaño de la página
y el total coincidirían y la aserción no podría fallar—.

El resto de los criterios se comprueban por API, que es donde vive la persistencia.

### Regresión

| | Antes | Después |
|---|---|---|
| Backend | 359 · 49 omitidas | **370 · 49 omitidas · 0 fallos** |
| E2E | 95/95 | **99/99** |
| `tsc` · `vitest` · i18n | — | **PASS · 61/61 · 866 = 866** |

La paridad i18n no cambió: **las claves de los diecinueve maestros ya existían**, incluidas
las de los siete sin pantalla. Alguien las declaró y nadie las usó.

## 7. Veredicto

```
P-12 = CERTIFIED   ·   19 de 19 maestros gestionables · 8 de 8 pasos
```

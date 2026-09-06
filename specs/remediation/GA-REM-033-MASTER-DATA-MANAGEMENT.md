# `GA-REM-033` · GESTIÓN DE DATOS MAESTROS

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-033` · `CAPABILITY + CONTRACT SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Hallazgos** | `R-89` (total descartado) · `R-90` (siete maestros sin gestión) · `R-91` (siete sin edición) |
| **Proceso** | `P-12` · Gestión de datos maestros |
| **Dependencias** | `GA-REM-002` (permisos y pertenencia) · `GA-REM-011` (contratos) |
| **Antecedentes** | `P12_NORMATIVE_MASTER_CATALOG.md` · `P12_BACKEND_MASTER_MATRIX.md` · `P12_FRONTEND_MASTER_MATRIX.md` · `P12_MASTER_PARITY_MATRIX.md` · `P12_PAGINATION_CONTRACT_MATRIX.md` · `P12_PROCESS_CHAIN_MATRIX.md` |

> **Una spec y no siete.** Los siete maestros comparten ciclo de vida, permisos, modelo de
> interacción, patrón de interfaz y forma de contrato. `§23` del encargo permite gobernarlos
> juntos precisamente en ese caso. Donde difieren —el alcance de inquilino— la spec lo dice.

---

## 1. Los tres problemas

**`R-90`.** Siete maestros que `docs/02 §3.2` exige —seis por nombre y prioridad, uno por
uso— no tienen ninguna forma de gestionarse desde el producto:

```
incubators · hatchers · productive-phases · medications
cull-causes · rejection-reasons · correction-types
```

No aparecen en `masterEntities` (`App.tsx:94`), que es la única fuente de rutas de maestros.
Hoy solo pueden poblarse por API o por SQL.

**`R-91`.** Esos mismos siete pasan `None` como esquema de actualización, de modo que
`register_crud` no registra la ruta `PUT`. No pueden corregirse ni por API.

**`R-89`.** `masters/router.py:38` calcula el total y lo descarta al devolver una lista
pelada. La interfaz muestra el tamaño de la página donde promete «resultados», y decide con
ese número equivocado si enseña la paginación.

## 2. Los maestros afectados, enumerados

`§102` del encargo prohíbe decir «crear las pantallas faltantes» sin nombrarlas.

| Maestro | Fuente normativa | Prioridad | Alcance | Padre |
|---|---|:--:|---|---|
| `incubators` | por uso: `HatcheryParams.incubator_id`, proceso `P-05` | — | por el padre | `hatchery_id` |
| `hatchers` | `§3.2.1` «Nacedoras» | Alta | por el padre | `hatchery_id` |
| `productive-phases` | `§3.2.1` «Fases Productivas» | Alta | **global** | — |
| `medications` | `§3.2.1` «Medicamentos» | Media | `company_id` | — |
| `cull-causes` | `§3.2.1` «Causas de Descarte» | Alta | `company_id` | — |
| `rejection-reasons` | `§3.2.2` «Motivos de Rechazo» | Alta | `company_id` | — |
| `correction-types` | `§3.2.2` «Tipos de Corrección» | Alta | `company_id` | — |

## 3. Fuera de alcance

- **`BirdTypeEnum` y `EventStatus`**: `§3.2` los lista, pero gobiernan la lógica del proceso
  —el tipo de ave selecciona la cadena productiva; el estado gobierna el flujo de revisión—.
  Hacerlos editables permitiría crear un valor que ninguna rama sabe atender. Divergencia
  consciente y registrada, no un hueco.
- El backend de los doce maestros completos: **no se toca**.
- Borrado físico y cascadas: el ciclo es **baja lógica** y así se queda.
- Un «motor genérico de maestros»: ya existe y funciona.
- `P-13`, `P-14`, `OD-04`, `GA-TD-014`.

## 4. Criterios de aceptación — grupo A · el total (`R-89`)

### `AC01` · El listado expone el total que calcula
`GET /masters/{entidad}` devuelve el total en la cabecera **`X-Total-Count`**, y el cuerpo
sigue siendo la lista.

> **Enmienda, y por qué.** Este criterio decía `{"items": [...], "total": n}`, siguiendo el
> contrato de `/audit`, `/corrections` y `/review`. Al ir a implementarlo se contaron los
> consumidores: **43 puntos del frontend** leen `/masters/*` como lista —los desplegables de
> los formularios operativos, entre ellos—, mientras que los endpoints con envoltorio tienen
> un consumidor cada uno.
>
> Cambiar la forma del cuerpo convertiría un defecto **P2 de contador** en un cambio de 43
> puntos de llamada, y `§51` del encargo lo prohíbe expresamente: `P-12` no es excusa para un
> refactor general. `X-Total-Count` es la convención estándar para exactamente esto: el total
> de una colección paginada sin tocar el cuerpo.
>
> La divergencia del contrato de la casa es **consciente y acotada a este endpoint**, y queda
> dicha aquí en lugar de descubrirse leyendo el código.

### `AC02` · El total respeta el filtro
Con `search` aplicado, `total` es el número de coincidencias, no el del catálogo entero.

### `AC03` · La interfaz muestra el total, no el tamaño de página
**Puerta de validez.** El conjunto de prueba tiene **más registros que el tamaño de página**.
Con menos, el tamaño de la página y el total coinciden y la comprobación no podría fallar.

## 5. Criterios de aceptación — grupo B · la gestión (`R-90`, `R-91`)

### `AC04` · Los siete son administrables
Cada uno de los siete tiene ruta, listado, alta, edición y baja lógica, **con el patrón
vigente**: `MasterListPage` parametrizada y una entrada en `masterEntities`. No se escriben
siete pantallas ni se rediseña la administración.

### `AC05` · Los siete admiten edición
Cada uno declara su esquema de actualización y `register_crud` registra su `PUT`. El esquema
expone los campos que `§3.2` llama «campos clave» y **no** expone `company_id`, `id` ni las
marcas del sistema (`UPDATE_SCHEMA_SECURITY_MATRIX`).

### `AC06` · Persistencia inmediata
`R-68`: tras crear o editar, una lectura posterior ve el nuevo estado. Sin esperas.

### `AC07` · Baja lógica, no borrado
`DELETE` marca `is_active = false` y el registro desaparece de las listas activas sin
perderse. No se añade borrado físico.

### `AC08` · Pertenencia del padre
`incubators` y `hatchers` no pueden crearse ni moverse bajo una planta de otra empresa
(`R-59`).

**Puerta de validez.** CONTROL y TRATAMIENTO con el mismo actor y la misma petición; lo único
que cambia es de quién es la planta.

### `AC09` · El maestro global no se filtra por empresa
`productive-phases` no declara `company_id`. **No** se le aplica `verificar_pertenencia`:
meterlo ahí lo rompería. Se comprueba que sigue siendo visible desde cualquier empresa.

### `AC10` · El maestro creado se puede usar
Una causa de descarte creada desde la gestión se puede seleccionar al registrar un descarte.
Es el paso 5 de la cadena: una pantalla que abre no certifica el proceso.

### `AC11` · Permiso obligatorio
Sin `masters:create` / `masters:update` no se crea ni se edita: `403`.

## 6. Criterio transversal

### `AC12` · La evidencia puede fallar
`GA-REM-016 AC13`. Mutación controlada y revertida sobre el total, sobre la persistencia de
un campo y sobre la pertenencia del padre.

## 7. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC01` `AC02` | `backend/tests/test_master_pagination.py` | integración HTTP |
| `AC04`…`AC11` | `backend/tests/test_master_management.py` | integración HTTP |
| `AC03` | `e2e/proceso-p12-datos-maestros.spec.ts` | `UI_E2E` |
| `AC10` | ídem | `API_E2E` |
| `AC12` | informe de certificación | mutación |

> **Por qué `AC03` sí necesita interfaz.** `§68` del encargo lo condiciona al requisito, no al
> vocabulario: lo que falla es lo que el usuario **lee** en la pantalla. Un `API_E2E` no puede
> comprobar un número renderizado. Es el primer proceso de este programa cuya certificación
> exige `UI_E2E`, y solo para ese criterio.

## 8. Definición de terminado

- Los doce criterios pasan.
- Existe prueba que **falla contra el código actual** por la causa exacta.
- Sensibilidad demostrada y revertida.
- Los 8 pasos de `P12_PROCESS_CHAIN_MATRIX` se recorren.
- Paridad i18n preservada; ninguna cadena embebida.
- Regresión completa sin fallos nuevos.

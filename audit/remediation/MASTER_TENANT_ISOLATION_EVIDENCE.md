# AISLAMIENTO DE INQUILINO EN MAESTROS — `R-115` · `R-116`

`RQ-03` · `AC05` · 2026-09-08 · **sin `GA-REM` nueva**

```
ROJO DEMOSTRADO   8 fallando · 4 controles positivos pasando
VERDE             12 / 12  ·  regresión 720 passed · 49 skipped
SENSIBILIDAD      7 mutaciones · 7 detectadas · 1 rehecha por inválida
MIGRACIÓN         ninguna
FRONTEND          0 ficheros
```

---

## 1. Autoridad · por qué no se creó `GA-REM-041`

`RQ-03` («aislamiento de compañía en todas las consultas aplicables») y `AC05` de `GA-REM-002`
gobiernan los dos hallazgos desde el primer día. No hay requisito nuevo que decidir.

```
REQUISITO EXISTENTE  →  COBERTURA DE RECURSOS INCOMPLETA  →  HUECOS  →  REMEDIACIÓN BAJO LA AUTORIDAD QUE YA HABÍA
```

Es la misma historia que `users`, y contarla como «requisito nuevo» habría escondido lo único
que importa aprender: la lista de aplicación estaba corta, no la norma.

## 2. `R-115` · la empresa es su propio inquilino

```python
if hasattr(self.model, "company_id"):     # falso para `Company`
    query = query.where(...)              # nunca se aplicaba
```

`Company` no tiene ni puede tener `company_id`: su clave de inquilino es su **propia clave
primaria**. `docs/03 §686` decía «la mayoría de entidades tienen `company_id`», y `Company` es
justamente la que no puede — el filtro se escribió asumiendo lo contrario.

Arreglo: un registro **declarativo**, `_INQUILINO_POR_IDENTIDAD = {"companies"}`. Declarado y no
deducido a propósito: una excepción declarada se revisa, una deducida se olvida. La mutación
`M2` vacía ese registro y las pruebas lo detectan.

### Corrección a la redacción original de `R-115`

`R-115` decía que se exponía `sap_config`. **La exposición estaba latente detrás de un `500`.**

`Company.sap_config` es columna `String` tipada como `Mapped[Optional[dict]]`, y `CompanyRead`
la valida como `dict`: cualquier empresa con configuración `SAP` poblada hace que
`/masters/companies` devuelva `500` **para todo el mundo**. El campo no podía filtrarse porque
el endpoint se rompía antes.

Queda como **`R-127`**, defecto distinto, registrado y **no remediado aquí** — no lo gobierna
`R-115` y `§12` pide corregir exactamente lo gobernado.

Lo que sí era alcanzable, y lo que se cierra, es la fuga de la **fila entera**: `name`,
`tax_id`, `country`, `currency`, `approval_levels`. Las pruebas lo comprueban sobre la fila
completa y no sobre un campo, que es más fuerte: si la fila no sale, no sale ninguno de sus
campos, ni los que se añadan mañana.

## 3. `R-116` · sin empresa efectiva, cero filas

```python
if not self.user_company_id:
    return query          # ← sin acotar. El comentario admitía la duda:
                          #    «No company assigned — return empty or filter by id»
```

Un actor sin empresa que no fuese Super Administrador recibía los maestros de **todas**.
`GA-REM-040` había resuelto el mismo dilema al revés dos semanas antes: sin concesiones,
ninguna unidad, nunca «toda la empresa». Ahora `fail-closed`.

## 4. Un punto, cuatro superficies

`get_all`, `get_by_id`, `update` y `deactivate` pasan **todas** por `_apply_company_filter`
—las dos últimas a través de `get_by_id`—, de modo que arreglarlo ahí cierra listado, detalle,
edición y baja a la vez. El recuento ya se calculaba sobre la subconsulta acotada, así que el
`total` no delata filas ajenas por diferencia.

```
LISTADO   PASS      DETALLE  PASS      EDICIÓN  PASS  · efectos 0
BAJA      PASS      RECUENTO PASS      ID DIRECTO → 404
```

## 5. El Super Administrador **no** cambia

`docs/02 §3.1.4`, literal: «Super Admin (rol con `module="*"`, `scope_type="all"`) ve TODAS las
compañías». Se preserva, con prueba dedicada
(`test_r115_el_super_administrador_conserva_su_alcance_global`).

Cambiarlo es `R-126` y es **decisión de propietario**. Ninguna prueba de esta tanda asume lo
contrario.

## 6. Sensibilidad · 7 mutaciones, 7 detectadas

Cada una con huella verificada en el fichero antes de ejecutar, según `§34`.

| # | Mutación | Huella | Prueba | Resultado |
|:--:|---|:--:|---|:--:|
| `M1` | quitar el caso «inquilino por identidad» | 1 | listado y campos de empresa | **2 failed** |
| `M2` | **vaciar el registro** `_INQUILINO_POR_IDENTIDAD` | 1 | ídem | **2 failed** |
| `M3` | quitar el predicado genérico | 1 | el actor con empresa ve lo suyo | **1 failed** |
| `M4` | detalle por identificador sin acotar | 2 | `IDOR` en empresas y granjas | **2 failed** |
| `M5` | la escritura resuelve el objetivo sin acotar | 2 | edición de empresa ajena | **1 failed** |
| `M6` | `fail-open` real para actor sin empresa | 1 | las tres de `R-116` | **3 failed** |
| `M7` | filtrar en Python después de paginar | 2 | fixture discriminante | **1 failed** |

### `M6` fue inválida en su primer intento, y no se contó como detección

La escribí como `if False and self.user_company_id is None:`. La rama se saltaba… y la ejecución
caía en `company_id == None`, que `SQLAlchemy` traduce a `IS NULL` y **tampoco devuelve filas**.
La mutación no llegó a **quitar** la propiedad de seguridad, de modo que las pruebas pasando no
probaban nada en ninguna dirección.

Clasificada `INVALID MUTATION` y rehecha para restaurar el `return query` original —el
`fail-open` de verdad—, que sí produce rojo. Es el tercer caso de mutación defectuosa en este
programa y el segundo que detecto antes de anotarlo.

### `M7` con fixture discriminante · `§36`

Treinta granjas de `B` y **después** una de `A`, para que la de `A` tenga el identificador más
alto. Con el filtro en la consulta entra en la primera página; con filtro posterior, la página
son treinta filas de `B` y la propia desaparece. Sin esa disposición las dos implementaciones
darían el mismo resultado y la prueba no mediría nada — que es exactamente lo que pasó con `S8`
en la tanda anterior.

## 7. `§38` · mutación de proyección: `N/A`, con motivo

`R-115` denuncia una fuga **de fila**, no de campo: `CompanyRead` ya existía como
`response_model` y su proyección era correcta. La remediación es el filtro de inquilino, no el
contrato de respuesta. Introducir una fuga de proyección probaría una propiedad que este
hallazgo no gobierna.

No se amplía `R-112` a las rutas `SAP` restantes.

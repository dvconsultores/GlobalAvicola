# `OD-14` · CONTROL GLOBAL FRENTE A CONTEXTO DE INQUILINO

Decisión de propietario · resuelve `R-126` · 2026-09-08 · **VIGENTE** · Opción `C`

```
VISIBILIDAD GLOBAL        ≠        CONTEXTO DE INQUILINO SELECCIONADO
```

---

## 1. El problema que resuelve

`docs/02 §3.1.4` dice que el Super Administrador «ve TODAS las compañías». El código lo
implementó como **ninguna ruta filtra para él**, y de ahí salió una incoherencia que la
auditoría documentó: la administración de unidades de negocio de la fase 7 **sí** exige empresa
efectiva, mientras `/users` y `/masters` no. Dos superficies del mismo plano de control
contestando distinto a la misma pregunta.

La frase de la spec **se preserva**, y se precisa su alcance: habla de la autoridad sobre el
catálogo de empresas, no de que toda ruta del producto ignore el inquilino.

## 2. `OD-14.a` · toda superficie declara su clase

```
CONTROL_GLOBAL    la autoridad global la ve entera, sin depender del contexto
INQUILINO         se resuelve SIEMPRE contra la empresa efectiva, para todos
```

**No hay clase por omisión.** Una superficie sin clase no se resuelve «como global», que es
como se llegó hasta aquí: se declara, o el arranque falla — la misma disciplina que
`authorization_coverage` y `route_scope` ya aplican.

## 3. `OD-14.b` · qué es `switch-company`

```
switch-company  =  ELEGIR LA EMPRESA EFECTIVA PARA LAS SUPERFICIES DE INQUILINO
```

Y **no** retira la autoridad global sobre las superficies de control global. Situarse en la
empresa `A` no impide seguir viendo el catálogo de empresas: impide operar sobre datos de `B`
mientras se está en `A`.

## 4. `OD-14.c` · la clasificación

| Superficie | Clase | Actor de empresa | Autoridad global sin contexto | Autoridad global situada en `A` |
|---|---|---|---|---|
| catálogo de empresas (`/masters/companies`) | **CONTROL_GLOBAL** | solo la suya | **todas** | **todas** |
| catálogo de capacidades (`permissions`) | **CONTROL_GLOBAL** | todo | todo | todo |
| plantillas de sistema (roles `company_id NULL`) | **CONTROL_GLOBAL** | visibles | visibles | visibles |
| `/users` | **INQUILINO** | la suya | **deniega** | solo `A` |
| roles de inquilino | **INQUILINO** | los suyos | deniega | solo los de `A` |
| maestros (granjas, galpones, …) | **INQUILINO** | los suyos | **cero filas** | solo los de `A` |
| unidades de negocio de la empresa | **INQUILINO** | la suya | deniega (ya lo hacía) | solo `A` |
| concesiones de unidad por usuario | **INQUILINO** | la suya | deniega (ya lo hacía) | solo `A` |
| dato productivo | **INQUILINO** | el suyo | cero filas | solo `A` |

## 5. `OD-14.d` · sin contexto no se opera sobre un inquilino

La autoridad global **sin empresa seleccionada** no obtiene la unión de todos los inquilinos.
Obtiene una negativa, o cero filas, según la convención de cada superficie.

```
PROHIBIDO   sin empresa → todas las empresas
```

Es la misma regla que `OD-11.c` ya había fijado —«elegir una empresa es un acto, no un valor
por defecto»— aplicada ahora a la autoridad global y no solo al usuario corriente.

## 6. Lo que esto cambia, dicho sin rodeos

**Cambia el comportamiento del Super Administrador**, y por eso es decisión de propietario y no
una corrección. Antes veía los usuarios y los maestros de todas las empresas desde cualquier
ruta; ahora tiene que elegir una empresa para operar sobre datos de inquilino.

Lo que **no** cambia:

```
el catálogo de empresas sigue siendo global — `docs/02 §3.1.4`, intacto
el catálogo de capacidades sigue siendo global — `OD-13.a`
las plantillas de sistema siguen visibles — `OD-13.c`
el usuario corriente no gana ni pierde nada
una reclamación de empresa en el token sigue sin ser autoridad — `OD-11`
```

## 7. Por qué `C` y no `B`

`B` —el contexto define la escritura, la lectura de control sigue global— era la recomendación
de ingeniería por ser la más barata y la que no contradecía nada. El propietario elige `C`, que
es más estricta y más cara, y la razón es defendible: `B` deja la clase de cada superficie
**implícita**, y este programa lleva tres tandas pagando el precio de las clasificaciones
implícitas. `C` obliga a declararla.

## 8. Trazabilidad

| `AC` | Qué |
|---|---|
| `AC-G01` | Toda superficie afectada declara `CONTROL_GLOBAL` o `INQUILINO`; no hay omisión silenciosa |
| `AC-G02` | `switch-company` fija la empresa efectiva de las superficies de inquilino |
| `AC-G03` | `switch-company` **no** retira visibilidad sobre las de control global |
| `AC-G04` | La autoridad global sin contexto no obtiene la unión de inquilinos |
| `AC-G05` | El mismo actor, situado en `A`: catálogo de empresas → `A` y `B`; `/users` → solo `A` |
| `AC-G06` | El actor de empresa no cambia de comportamiento |

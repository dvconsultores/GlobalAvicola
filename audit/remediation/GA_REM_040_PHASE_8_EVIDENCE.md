# `GA-REM-040` · FASE 8 · LA SESIÓN

`T-040-20` · enmienda E · `AC-H11`…`AC-H14` · 2026-09-09

```
FASE 8 = COMPLETE
ROJO PREVIO     15 de 16
VERDE           16 / 16  ·  backend 770 passed · 49 skipped  ·  frontend 87 passed
SENSIBILIDAD    11 mutaciones · 11 detectadas · 1 rehecha por inválida
MIGRACIÓN       ninguna       ·  CONTRATO  aditivo  ·  FRONTEND  0 ficheros
```

---

## 1. El principio, y lo que se deduce de él

```
LA SESIÓN REPRESENTA LA AUTORIDAD   ·   NO LA DEFINE
```

El endpoint **compone**. No hay un solo `if` sobre roles, empresas o comodines: cada campo sale
de un resolutor que ya existía y ya estaba certificado.

```
empresa efectiva   `get_current_user` → `resolver_empresa_efectiva` (`OD-11`)
capacidades        el `RBAC` que esa misma dependencia ya resolvió
habilitadas        `unidades_habilitadas`
concedidas         `unidades_concedidas`   (nuevo, ver §3)
efectivas          `unidades_efectivas_por_id`
```

Si un campo hubiera necesitado lógica propia, habría sido señal de que la autoridad no está
donde debe. Ninguno la necesitó.

## 2. Cuatro conceptos, cuatro campos

`§14.1` los nombra por separado, y por separado se entregan:

| Campo | Qué es | Quién lo decide |
|---|---|---|
| `company_business_units` | las que la empresa efectiva tiene habilitadas | comercial |
| `granted_business_units` | las concedidas al usuario en esa empresa | operativa |
| `effective_business_units` | concedidas ∩ habilitadas ∩ activas | **la única que autoriza** |
| `permissions` | capacidades `RBAC`, `"modulo:accion"` | `RBAC` |

**Hay una prueba dedicada a que las dos del medio difieran.** Se apaga la unidad: la concesión
sigue —`AC-A04`, apagar no revoca— y deja de ser efectiva. Si nunca pudieran diferir, una de las
dos listas sobraría y el cliente no podría distinguir «nunca se lo dieron» de «se lo dieron y la
empresa cerró esa línea».

## 3. El resolutor que faltaba

`unidades_concedidas` se añade **junto a los otros**, no en el endpoint, y su docstring dice lo
que no es:

```
sirve para CONTAR  ·  no para AUTORIZAR
```

`unidades_efectivas` sigue siendo la única que decide.

## 4. `AC-H14` · administrar aparece como administrar

El caso que esta fase existía para hacer legible:

```
Administrador de Accesos
    permissions               business_units:read · update · create · delete
    effective_business_units  []
    granted_business_units    []
    company_business_units    las tres de su empresa — las administra
```

Las dos primeras líneas a la vez, y **no** es una incoherencia que corregir: es `OD-09.b` por
fin visible en el contrato. Un cliente puede ofrecer la pantalla de administración sin ofrecer
dato productivo, que es exactamente lo que la fase 9 necesitará.

Y lo que **no** lleva, por decisión y no por olvido: `users:read` (`OD-15 §6`) y comodín.

## 5. `AC-H12` · `AC-H13` · el actor global

```
sin contexto        is_super_admin true · effective_company_id null · las tres listas []
situado en A        is_super_admin true · effective_company_id A
situado en B        is_super_admin true · effective_company_id B
```

Situarse **no** retira la autoridad global, y la autoridad global **no** trae unidades
productivas: `BU-D04` dejó la transversalidad como excepción de `SAP`, no como regla.

Nada de empresa ficticia, ni `company_id = 0`, ni «la primera empresa». Sin contexto,
`effective_company_id` es nulo y punto.

`company_id` se conserva —es la empresa **persistida**— y ahora está documentado lo que
significa. Para un usuario corriente coincide con la efectiva; para la autoridad global situada,
no. Que coincidan en un caso y no en el otro es lo que hace legible la distinción.

## 6. Sensibilidad · 11 mutaciones, 11 detectadas

| # | Mutación | Huella | Resultado |
|:--:|---|:--:|:--:|
| `S1` | sin concesiones → todo lo habilitado | 1 | **1 failed** |
| `S2` | quien administra, obtiene | 1 | **1 failed** |
| `S3` | la sesión fabrica `users:read` | 1 | **1 failed** |
| `S5` | situarse retira la autoridad global | 1 | **1 failed** |
| `S6` | sin selección → la primera empresa | 1 | **1 failed** |
| `S7` | la reclamación del cliente es autoridad | 1 | **1 failed** |
| `S8` | se ignora que la unidad esté deshabilitada | 2 | **1 failed** |
| `S9` | una concesión revocada sigue contando | 2 | **1 failed** |
| `S10` | la capacidad se deriva del nombre del rol | 1 | **1 failed** |
| `S11` | el contrato deja de acotar y sirve `hashed_password` | 2 | **1 failed** ⚠ |
| `S12` | las habilitadas se sirven como concedidas | 1 | **1 failed** |

### `S11` fue inválida en su primer intento

La escribí como `extra: "allow"` en el esquema. No cambió nada, y con razón: el objeto se
construye con campos **explícitos**, de modo que no había extras que dejar pasar. La mutación no
llegó a retirar la propiedad, así que las pruebas pasando no probaban nada.

Rehecha para que el endpoint sirva de verdad un campo interno. Entonces sí produce rojo.

```
Lo que protege no es que el esquema prohíba extras:
es que el endpoint pasa campos explícitos.
La primera mutación medía la puerta equivocada.
```

## 7. Dos correcciones a mi propio trabajo de esta misma fase

**Perdí `is_super_admin` al componer.** El endpoint lo asignaba después de leer la fila —porque
la fila no sabe nada de comodines— y al reescribirlo se me cayó la línea: `/me` empezó a decir
que nadie era administrador. Lo cazó `test_get_me`, que llevaba ahí desde el principio.

**Mi enmienda E pedía un campo que no debía existir.** `is_global_actor` habría sido un sinónimo
exacto de `is_super_admin`, que ya se deriva de `("*", …, "all")` y no de un nombre de rol. Dos
campos obligados a coincidir siempre acaban divergiendo. La enmienda queda corregida en su
propio texto, no en silencio.

**Y una fixture mía sembraba el rol comodín con `scope_type="company"`**, de modo que no era
global en absoluto: tres pruebas de `AC-H13` medían un actor corriente creyendo medir uno
global. La fixture ahora **afirma** el alcance en vez de darlo por hecho — `§57`.

## 8. Lo que la fase 8 **no** hizo

```
NO  lista de empresas seleccionables — `§14.1` no la pide
NO  `users:read` para el Administrador de Accesos — `OD-15 §6` decidió al revés
NO  superficie de candidatos para la interfaz — es trabajo de la fase 9
NO  módulos habilitados por empresa — no existe tal requisito
NO  banderas de conveniencia — se usan las capacidades que ya hay
NO  frontend — 0 ficheros `.ts` / `.tsx`
NO  migración — la sesión compone estado que ya existía
```

**Dependencia registrada para la fase 9**: la pantalla de administración necesitará ofrecer
usuarios candidatos de la misma empresa sin conceder `users:read` general. Es una superficie
propia y acotada, y no se implementa aquí.

## 9. Y lo que la sesión sigue sin ser

```
LA SESIÓN INFORMA AL CLIENTE   ·   NO SUSTITUYE AL BACKEND
```

`AC-H10` sigue vigente y se demuestra igual que siempre: llamando a la `API` directamente. Que
la sesión diga «capacidad ausente» no protege nada. Lo que protege es que la ruta deniegue, y
eso lo sostienen las 770 pruebas del backend, no este contrato.


---

## 10. Cierre formal (2026-09-09 · segunda revisión)

Cuatro precisiones que el cierre exige dejar escritas **tal como ocurrieron**, no como quedaron.

### `is_global_actor` se retiró de la enmienda **antes** de certificar

No es una característica implementada y después eliminada. La enmienda E lo pedía; al
implementarla quedó claro que sería un sinónimo exacto de `is_super_admin`; se corrigió la
enmienda y el campo **nunca entró en el contrato certificado**. Hoy aparece una sola vez en el
código: en el comentario de `SessionRead` que explica por qué no existe.

```
CANÓNICO    is_super_admin  ←  ("*", …, "all")   ·   nunca del nombre del rol
                                                  ·   nunca de company_id NULL
```

### La regresión de `is_super_admin`

```
CLASE       IMPLEMENTATION REGRESSION
DETECTADA   antes de certificar · por `test_get_me`, prueba de contrato preexistente
HALLAZGO    ninguno — corregida en la misma tanda, antes de certificación
```

La prueba se conserva tal cual. Es la razón por la que existía.

### `S11` inicial: puerta equivocada

```
INTENTO      `extra="allow"` en el esquema
RESULTADO    la prueba siguió pasando — y con razón
CAUSA        el endpoint construye `SessionRead` con campos EXPLÍCITOS;
             no había extras que dejar pasar; la propiedad no se retiró
CLASE        INVALID MUTATION · no contada
SUSTITUTA    el endpoint sirve `hashed_password` de verdad → rojo
```

```
LA PROTECCIÓN ES   endpoint → construcción explícita → contrato
NO ES              el rechazo de extras de Pydantic
```

### La fixture privilegiada afirma su autoridad

```
REGLA PERMANENTE
    UNA FIXTURE PRIVILEGIADA DEBE AFIRMAR SU PRECONDICIÓN DE AUTORIDAD
    ANTES DE PROBAR SUS CONSECUENCIAS
```

La del actor global sembraba el comodín con `scope_type="company"` y no era global. Ahora la
fixture ejecuta `assert any(p.module == "*" and p.scope_type == "all")` antes de ceder el
escenario, y `AC-H13` mide lo que dice medir.

### Contabilidad de mutaciones

```
VÁLIDAS FINALES          11
INTENTOS INVÁLIDOS        1   (`S11` · puerta equivocada)
REHECHAS                  1
CONTADAS SIN SER VÁLIDAS  0
```

### Veredicto

```
T-040-20            1 / 1
AC-H11…AC-H14       4 / 4  ·  AC-H01 satisfecha por ellas
suite dirigida      16 / 16  ·  test_get_me verde  ·  regresión 770 passed
FASE 8              COMPLETE
```

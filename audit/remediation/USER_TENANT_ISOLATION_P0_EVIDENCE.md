# AISLAMIENTO DE INQUILINO EN LA ADMINISTRACIÓN DE USUARIOS

`GA-REM-002` enmienda B · `AC13` · `AC14` · `AC15` · `AC16` · 2026-09-08

```
CUATRO P0 CERRADOS
ROJO DEMOSTRADO ANTES DEL CÓDIGO   9 de 13 pruebas fallando
VERDE               backend 708 passed · 49 skipped   ·   frontend 87 passed
SENSIBILIDAD        9 mutaciones · 9 detectadas · 2 requirieron corregirme
SIN MIGRACIÓN       la pertenencia ya estaba en `users.company_id`
```

---

## 1. Por qué una enmienda y no una `GA-REM` nueva

`AC05` de `GA-REM-002` ya lo exigía: *«un usuario de la compañía A que intenta operar sobre un
recurso de la compañía B recibe 403 o 404, nunca el recurso»*. Un usuario **es** un recurso de
una compañía. La norma estaba desde el primer día.

Lo que falló fue su traza. `TENANT_RESOURCE_CLASSIFICATION.md` —el documento que convierte esa
`AC` en la lista de sitios donde aplicar el filtro— se construyó desde el modelo de datos
**operativo**: lotes, eventos, granjas, galpones, evidencias, revisiones. **`users` nunca entró
en la lista**, y con él se quedó fuera toda la superficie de administración.

```
LA `AC` EXISTÍA   ·   LA LISTA QUE LA APLICABA, NO   ·   MISMO AGUJERO QUE NO TENERLA
```

Crear `GA-REM-041` habría contado la historia de un requisito nuevo cuando lo que hubo fue una
lista incompleta, y habría escondido la lección de método que es lo más caro de este hallazgo.

---

## 2. Trazabilidad

| Hallazgo | `AC` | Superficie | Dónde vive el arreglo | Prueba | Mutación |
|---|---|---|---|---|:--:|
| `R-114` `P0-A` | `AC13` | `GET /users` | `AuthService._acotar` en la consulta | `test_p0a_el_listado_no_expone…` + simétrica | `S1` `S8` |
| `R-114` `P0-B` | `AC13` | `GET /users/{id}` | `AuthService._usuario_alcanzable` | `test_p0b_conocer_el_identificador_ajeno…` | `S2` |
| `R-114` `P0-C` | `AC14` | `PUT /users/{id}` | ídem, **antes** de mutar | `test_p0c_no_se_modifica…` | `S3` |
| `R-117` `P0-D` | `AC15` | `PUT /users/{id}` `role_id` | `_es_autoridad_global` | `test_p0d_no_se_concede_autoridad…` | `S4` `S7` |
| `R-118` | `AC14` | `POST /users` | la empresa se resuelve, no se recibe | `test_el_alta_no_acepta_la_empresa…` | — |
| — | `AC14` | `DELETE /users/{id}` | ídem | dentro del `E2E` | — |
| `R-116` (parcial) | `AC13` | sin empresa efectiva | `fail-closed` en `_acotar` | `test_sin_empresa_efectiva…` | `S6` |
| `OD-11` | `AC14` | reclamación del cliente | `resolver_empresa_efectiva` | `test_el_parametro_de_empresa…` | `S5` |
| `R-120` | `AC16` | `/users` en la interfaz | `UsersPage` · cinco estados | 5 pruebas `vitest` | `S9` |

**`AC11` respetado**: un solo localizador —`_acotar` y `_usuario_alcanzable`— por el que pasan
listar, leer, editar, dar de baja y crear. Añadir mañana una sexta ruta no obliga a acordarse
de nada.

**El orden es parte de `AC14`**, no un detalle de estilo:

```
autenticación → empresa efectiva → objetivo EN esa empresa → RBAC →
validación de campos → validación de rol → mutación → auditoría → commit
```

Antes se traía el usuario globalmente y se le aplicaban los campos en bucle, `role_id`
incluido. Por ahí un administrador de la empresa A convertía a un usuario de la B en Super
Administrador: fuga de inquilino y modificación de autoridad en el mismo acto.

---

## 3. Sensibilidad · 9 mutaciones, 9 detectadas

| # | Mutación | Prueba que debía romperse | Resultado |
|:--:|---|---|:--:|
| `S1` | quitar el predicado del listado | listado propio y simétrico | **2 failed** |
| `S2` | detalle solo por identificador | lectura ajena | **1 failed** |
| `S3` | edición solo por identificador | edición ajena | **1 failed** |
| `S4` | desactivar la guarda de autoridad global | autoridad global desde empresa | **1 failed** |
| `S5` | honrar la reclamación de empresa del cliente | el parámetro no amplía | **1 failed** |
| `S6` | `fail-open` para actor sin empresa | denegación por falta de contexto | **1 failed** |
| `S7` | guarda de rol por **nombre** en vez de por forma del permiso | autoridad global desde empresa | **1 failed** |
| `S8` | filtrar en Python **después** de paginar | el filtro vive en la consulta | **1 failed** ⚠ |
| `S9` | restaurar el `catch` que se tragaba el error | 403 y 500 en la interfaz | **2 failed** |

### Dos mutaciones me corrigieron, y conviene que quede escrito

**`S5` era una mutación rota.** La escribí referenciando `request.query_params` en un manejador
que **no tiene** parámetro `request`: producía `NameError`, la prueba fallaba, y yo habría
anotado «detectada». Una mutación que no ejecuta lo que dice no prueba nada — es el mismo error
que ya cometí en la fase 5. Rehecha contra `resolver_empresa_efectiva`, que es donde vive de
verdad la regla de `OD-11`.

**`S8` sobrevivió dos veces, y la segunda por mi culpa.** Filtrar en Python después de paginar
daba el mismo resultado con cuatro usuarios y `limit=100`: la prueba no distinguía. Escribí una
prueba nueva… que pedía la **primera** página, donde los usuarios propios —con identificadores
bajos— sobrevivían igualmente al filtro posterior. **La descripción prometía algo que el código
no hacía.** La versión final siembra treinta usuarios ajenos y **después** uno propio, de modo
que solo el filtro dentro de la consulta lo devuelve en la primera página.

Sin esa corrección, `§41` habría quedado afirmado y no demostrado.

---

## 4. Dos correcciones a la implementación, ambas por romper pruebas certificadas

**Forcé la empresa también a la autoridad global.** Rompió `test_t_073_06` (`GA-REM-029 AC07`) y
`test_t_039_11` (`GA-REM-039`), que provisionan usuarios entre empresas con el administrador
sembrado. El `P0` es del actor **acotado**; quitarle al Super Administrador la capacidad de
aprovisionar no cerraba nada y sí rompía administración legítima.

**Escribí una prueba afirmando que `switch-company` acota al Super Administrador.** Estaba
equivocada. `docs/02 §3.1.4` dice literal: «Super Admin (rol con `module="*"`,
`scope_type="all"`) ve TODAS las compañías», y `get_company_filter` lo aplica así en todo el
producto. Acotarlo solo en `/users` habría hecho que esta ruta se comportara distinto de
`/masters` sin ninguna norma que lo pidiera.

```
SPEC > PROMPT      la instrucción de esta tanda pedía acotar al super admin situado;
                   la spec dice lo contrario y manda la spec
```

Queda registrado como **`R-126`**: si el propietario quiere que el contexto acote también a la
autoridad global, es decisión de producto para **todos** los servicios, no un parche en `/users`.

Esto no debilita el arreglo. El actor del hallazgo es el administrador acotado a una empresa, y
para él el filtro es obligatorio y está probado por las cuatro primeras pruebas de la suite.

---

## 5. `AC15` · dónde se traza la raya y dónde no

Se prohíbe exactamente lo que `docs/02 §3.1.4` describe como alcance global: un rol con
`module="*"` y `scope_type="all"`. Concederlo desde una superficie acotada a una empresa
**fabrica autoridad global dentro de un inquilino**, y eso es escalada aunque el objetivo sea
de la propia casa.

**No se inventa** una jerarquía de «solo roles más débiles que el mío». Esa regla no está en
ninguna spec y decidirla no corresponde a una remediación de seguridad.

```
PENDIENTE   qué roles ordinarios puede asignar un administrador de empresa
            `R-121` · OWNER_DECISION_REQUIRED
```

Y no se mira el nombre del rol: `GA-REM-040 AC-F05` ya dejó dicho lo que valen los nombres. La
mutación `S7` lo comprueba sustituyendo la forma del permiso por una búsqueda de «super» en el
nombre, y la prueba lo detecta.

---

## 6. La interfaz · `AC16`

Los cuatro recursos que la pantalla pedía **no son iguales**:

| Llamada | Permiso | Papel | Si falla |
|---|---|---|---|
| `/users` | `users:read` | **es la página** | estado explícito de error o permiso |
| `/roles` | `users:read` | nombre del rol y desplegable | aviso; la tabla sigue |
| `/masters/companies` | `masters:read` | desplegable del formulario | aviso |
| `/masters/areas` | `masters:read` | desplegable del formulario | aviso |

Antes iban en un `Promise.all` con `catch { console.error }`: **una** fallando vaciaba la tabla
entera. Cinco estados distinguibles ahora —cargando, datos, vacío real, `403`, error con
reintento— más el aviso de catálogo parcial.

**No se concedió ningún permiso para que la tabla se llenara.** `R-113` sigue congelado, y el
`403` que verá un actor sin `users:read` es ahora visible, que es exactamente lo que se pedía.

---

## 7. Lo que esta tanda **no** tocó

```
R-113     OPEN · FROZEN — no se sembró ningún rol de administración de acceso
FASE 8    NOT STARTED · FROZEN
BU-D10    PENDING_RATIFICATION · intacta
R-112     TRACKED · sin remediación amplia; las rutas tocadas mantienen su contrato
P-08      BLOCKED_EXTERNAL · intacto
SAP       Empresas y Granjas siguen siendo catálogos locales, que es lo que
          `docs/02 §3.2.1` manda — NO se creó ningún defecto falso
MÓDULOS   no se inventó requisito: `R-125` sigue siendo decisión de propietario
R-115     `/masters/companies` sin acotar — registrado, fuera de esta tanda
R-116     `MasterService` `fail-open` sin empresa — cerrado en `/users`, abierto en maestros
```

---

## 8. Método · lo que hay que incorporar permanentemente

```
COBERTURA DE PRUEBAS DE REMEDIACIONES CONOCIDAS  ≠  COMPLETITUD DE REQUISITO
AUSENCIA DE DEFECTO REPORTADO                    ≠  REQUISITO IMPLEMENTADO
```

687 pruebas verdes y tres guardas de arranque convivieron con cuatro `P0` porque el programa se
organizó alrededor de `HALLAZGO → REMEDIACIÓN → PRUEBA`. Falta la dirección contraria:

```
REQUISITO DE SPEC → TRAZA DE IMPLEMENTACIÓN → BD → BACKEND → FRONTEND → RUNTIME → E2E
```

aunque nunca haya existido un defecto reportado. Un requisito sin traza no está completo por el
hecho de que nadie se haya quejado.

**Ninguna certificación histórica se invalida.** Todas medían capacidad técnica o de proceso en
su dimensión y siguen siendo ciertas ahí. Lo que se añade es la distinción entre certificar un
componente y certificar un producto.

Sobre una guarda estática de inquilino (`§74`): **no se construye ahora**. Una guarda del tipo
«la ruta menciona `company_id` en alguna parte» daría falsa seguridad, que es peor que no
tenerla — precisamente lo que acaba de pasar con una lista de clasificación incompleta. Si se
justifica una guarda precisa, primero spec y `AC`.

# `OD-13` · LA PROPIEDAD DE ROLES Y PERMISOS

Decisión de propietario · resuelve `R-121` · 2026-09-08 · **VIGENTE**

```
PERMISO   =  CAPACIDAD GLOBAL DE PRODUCTO
ROL       =  CONJUNTO DE PERMISOS  +  ALCANCE
```

---

## 1. `OD-13.a` · el permiso es de producto, no de inquilino

`users:read`, `business_units:create`, `corrections:correct` describen **lo que el producto
sabe hacer**. No pertenecen a la empresa `A` ni a la `B`.

```
NO SE DUPLICAN filas de permiso por inquilino para aislar nada
```

El catálogo vive en `AuthService.MODULOS` × `PermissionAction` y es global por definición. La
tabla `permissions` no es ese catálogo: son las filas que **enlazan** un rol con una capacidad,
y por tanto heredan el inquilino de su rol.

**Consecuencia para `RQ-03`**: `permissions` es una **excepción normativa explícita**, no un
hueco. No se le aplica predicado de empresa porque no es dato de empresa. Lo que sí está
gobernado es **quién puede otorgar** una capacidad, y de eso se ocupa `OD-13.c`.

## 2. `OD-13.b` · el rol es híbrido, y su alcance está en `company_id`

```
Role.company_id IS NULL        ROL DE SISTEMA — plantilla de producto
Role.company_id = empresa X    ROL DE INQUILINO de X
```

La columna ya existía, nulable y sin clave foránea. **No hace falta migración**: lo que faltaba
no era poder expresar el alcance, era usarlo.

**Los seis roles sembrados —Super Administrador, Supervisor Avícola, Operador de Granja,
Aprobador, Analista SAP, Auditor— son roles de sistema**, y eso es correcto: son plantillas del
producto, compartidas por todos los clientes, no invenciones de una empresa concreta.

## 3. `OD-13.c` · ver un rol no es poder asignarlo

```
VISIBLE   ≠   ASIGNABLE
```

Un administrador de empresa ve el catálogo de plantillas —lo necesita para elegir— y eso **no**
le autoriza a repartir cualquiera de ellas.

La raya se traza donde la spec ya la tenía trazada, y ni un milímetro más allá:

```
ROL QUE CONFIERE AUTORIDAD GLOBAL     `module="*"` con `scope_type="all"`
                                      `docs/02 §3.1.4` lo define así, literalmente
                                      → SOLO la autoridad global lo asigna
ROL DE SISTEMA ORDINARIO              plantilla de producto sin autoridad global
                                      → un administrador de empresa lo asigna
                                        dentro de SU empresa
ROL DE INQUILINO                      → solo dentro de la empresa que lo posee
```

### Por qué la plantilla ordinaria sigue siendo asignable

Podría leerse «ningún rol con `company_id NULL` es asignable por un inquilino». Sería literal y
sería un error: **los seis roles del producto tienen `company_id NULL`**, de modo que esa
lectura dejaría a los administradores de empresa sin poder asignar absolutamente nada, y
convertiría cada alta de usuario en una petición al Super Administrador.

Lo que la norma protege es la **autoridad global** —`§3.1.4` habla de ver todas las compañías—,
no la existencia de un catálogo compartido. Se prohíbe fabricar autoridad global desde una
superficie de empresa; no se prohíbe usar el producto.

## 4. `OD-13.d` · el rol de inquilino no cruza empresas

```
Given un actor cuya empresa efectiva es A
When  lista, edita o asigna un rol de inquilino de la empresa B
Then  se rechaza, y el rol ajeno no aparece ni cambia
```

Y la asignación exige que **las tres cosas coincidan**:

```
usuario objetivo . empresa   ==   rol . empresa   ==   empresa efectiva del actor
```

## 5. `OD-13.e` · la empresa de un rol se resuelve, no se recibe

`RoleCreate` no acepta `company_id`, y no se le añade: la empresa sale del actor.

```
actor de empresa      → el rol nace en SU empresa
autoridad global      → el rol nace de sistema (`company_id NULL`)
```

Editar un rol de sistema exige autoridad global: verlo no basta (`OD-13.c`).

## 6. Lo que esta decisión **no** hace

```
NO crea una interfaz de gestión de Super Administradores
NO autoriza por nombre de rol — `GA-REM-040 AC-F05` sigue mandando
NO duplica permisos por empresa
NO reclasifica los roles sembrados: eran de producto y lo siguen siendo
NO cambia la semántica del Super Administrador — eso es `OD-14` / `R-126`
```

## 7. Trazabilidad

| `AC` | Qué |
|---|---|
| `AC-R01` | `GET /roles` devuelve los roles de la empresa efectiva **y** las plantillas de sistema; nunca los de otra empresa |
| `AC-R02` | Crear un rol lo sitúa en la empresa efectiva del actor; la autoridad global crea plantillas de sistema |
| `AC-R03` | Editar un rol de otra empresa se rechaza, sin efectos ni auditoría de éxito |
| `AC-R04` | Editar un rol de sistema exige autoridad global |
| `AC-R05` | Asignar un rol exige que usuario, rol y actor coincidan en empresa |
| `AC-R06` | Asignar un rol con `("*", …, "all")` exige autoridad global — refuerza `GA-REM-002 AC15` |
| `AC-R07` | `permissions` es excepción explícita de `RQ-03`: capacidad de producto, no dato de inquilino |

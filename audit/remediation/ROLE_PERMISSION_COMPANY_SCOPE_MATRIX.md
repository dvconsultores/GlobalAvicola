# ALCANCE DE ROLES, PERMISOS Y RECURSOS DE CONTROL

`OD-13` · `OD-14` · 2026-09-08

```
PERMISO  =  capacidad de producto     ·  global
ROL      =  permisos + alcance        ·  `company_id NULL` sistema · concreto inquilino
VISIBLE  ≠  ASIGNABLE                 ·  y ninguna de las dos implica EDITABLE
```

---

| Recurso | Alcance | Dueño | ¿Visible para el admin de empresa? | ¿Asignable por él? | ¿Visible para autoridad global? | ¿Exige empresa seleccionada? | `RBAC` | Filtro de inquilino | Prueba |
|---|---|---|:--:|:--:|:--:|:--:|---|---|---|
| **Permiso** (capacidad) | `CONTROL_GLOBAL` | producto | sí | n/a — se otorga vía rol | sí | **no** | `users:read` | ninguno · excepción `OD-13.a` | `test_r07_el_catalogo_de_permisos_es_global` |
| **Rol de sistema** ordinario | `CONTROL_GLOBAL` | producto | **sí** | **sí**, en su empresa | sí | no | `users:read` | `company_id IS NULL` siempre visible | `test_r01_las_plantillas_de_sistema_si_se_ven` · `test_r05_la_plantilla_de_sistema_ordinaria_si_se_asigna` |
| **Rol de sistema** con `("*", …, "all")` | `CONTROL_GLOBAL` | producto | sí | **NO** | sí | no | — | — | `test_r06_la_autoridad_global_no_se_reparte_desde_una_empresa` |
| **Rol de inquilino** | `INQUILINO` | la empresa | solo los suyos | solo los suyos | solo los de la empresa situada | **sí** | `users:*` | `roles.company_id` | `test_r01_el_listado_no_muestra_roles_de_otra_empresa` |
| **Usuario** | `INQUILINO` | la empresa | solo los suyos | n/a | solo los de la empresa situada | **sí** | `users:*` | `users.company_id` | `test_p0a_…` · `test_od14_la_autoridad_global_situada_solo_ve_esa_empresa` |
| **Empresa** (catálogo) | `CONTROL_GLOBAL` | producto | solo la suya | n/a | **todas** | **no** | `masters:read` | `companies.id` para el inquilino; exento para la global | `test_r115_…` · `test_od14_contraste_…` |
| **Granja** y demás maestros | `INQUILINO` | la empresa | solo los suyos | n/a | solo los de la empresa situada | **sí** | `masters:*` | `company_id` | `test_od14_la_autoridad_global_situada_solo_ve_las_granjas…` |
| **Habilitación de unidad** | `INQUILINO` | la empresa | la suya | n/a | la de la empresa situada | **sí** | `business_units:*` | `company_business_units.company_id` | `test_od14_la_administracion_de_unidades_sigue_el_contexto` |
| **Concesión de unidad** | `INQUILINO` | la empresa | las suyas | sí, en su empresa | las de la situada | **sí** | `business_units:*` | vía la habilitación | fase 7 |

---

## Las tres reglas que esta tabla codifica

**1 · El permiso no tiene dueño de inquilino.** `users:read` describe lo que el producto sabe
hacer. Duplicarlo por empresa no aislaría nada y multiplicaría filas sin significado.

**2 · Ver una plantilla no es poder repartirla, y repartirla no es poder editarla.** Un
administrador de empresa ve el catálogo —lo necesita para elegir—, asigna las plantillas
ordinarias dentro de su empresa, y no toca ninguna: editarlas exige autoridad global.

**3 · La única plantilla que no se reparte es la que confiere alcance global.** La raya se traza
donde `docs/02 §3.1.4` la tenía trazada —`module="*"` con `scope_type="all"`— y ni un milímetro
más allá. Prohibir todas las plantillas habría dejado a los administradores sin poder asignar
nada, porque las seis del producto tienen `company_id NULL`.


---

## Addendum · `Administrador de Accesos` (`OD-15` · 2026-09-09)

| Recurso | Alcance | ¿Visible? | ¿Asignable por el admin de empresa? | ¿Exige empresa seleccionada? |
|---|---|:--:|:--:|:--:|
| **Rol `Administrador de Accesos`** | `CONTROL_GLOBAL` — plantilla de producto | sí | sí (no confiere autoridad global) | no |

Es un rol de sistema (`company_id NULL`) y **eso no lo hace privilegiado**: `OD-13.b` ya fijó
que la autoridad se determina por las capacidades, no por la ausencia de empresa. Sus cuatro
permisos son de plano de control acotado a una empresa; ninguno es `("*", …, "all")`.

### La cuarta condición de la concesión

`OD-15.a` añade una a las tres de la fase 7:

```
el usuario objetivo pertenece a la empresa efectiva
la habilitación pertenece a la empresa efectiva
la autoridad del actor es válida en esa empresa
el usuario objetivo NO es el actor              ← `OD-15.a`
```


---

## Addendum · `business_units:create` también gobierna el descubrimiento (`R-129` · 2026-09-09)

```
business_units:create   conceder a un usuario  ·  Y saber a quién se puede conceder
```

No se creó permiso nuevo: la autoridad de conceder **es** la de saber a quién. Dos permisos que
fueran siempre juntos serían uno con un nombre de más. Lo que sí queda separado, y probado, es
que esa autoridad **no** alcanza `GET /users`.

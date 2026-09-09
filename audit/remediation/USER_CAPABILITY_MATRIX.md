# LA PILA DE ACCESO: QUÉ CAPAS EXISTEN

Auditoría del 2026-09-07 · **solo lectura**

---

## 1. La regla que debería regir

```
ACCESS_ALLOWED
=  empresa correcta
AND módulo habilitado para la empresa
AND módulo concedido al usuario
AND rol/permiso autoriza la acción
AND la propiedad del recurso o la regla de negocio lo permite
```

## 2. La matriz

| Layer | Current Model | Exists | Correct | Gap |
|---|---|:--:|:--:|---|
| **Company isolation** | `company_id` en 29 tablas · `MasterService._apply_company_filter` · `get_current_user` | **SÍ** | **SÍ** | ninguno conocido — certificado en `R-36`, `R-42`, `R-48`, `R-54`, `R-59` |
| **Company module enablement** | — | **NO** | — | **falta entero** |
| **User module grants** | — | **NO** | — | **falta entero** |
| **Role permissions** | `roles` · `permissions` · `require_permission(modulo, accion)` · `authorization_coverage` | **SÍ** | **SÍ** | cubre **acción**, no unidad de negocio |
| **Resource ownership** | tenencia por empresa · destinatario en notificaciones · `BR-*` | **parcial** | sí donde existe | no hay noción de pertenencia a unidad |

```
2 de 5 capas existen y funcionan
2 de 5 no existen en absoluto
1 de 5 existe parcialmente
```

## 3. Lo que `RBAC` sí cubre, dicho con justicia

`GA-REM-002` no está incompleto: hace exactamente lo que se le pidió. Comprueba que un usuario
tenga permiso para **una acción sobre un módulo funcional**, y lo hace en las 198 rutas con una
guarda que **impide arrancar** si alguna se olvida.

Lo que no cubre —porque nadie se lo pidió— es una segunda dimensión: sobre **qué subconjunto de
datos** de ese módulo funcional puede actuar.

```
require_permission("operations", "read")   →  puede leer operaciones
                                           →  ¿de qué unidades? sin respuesta
```

## 4. El escenario que hay que poder expresar

`§29` del encargo lo plantea y es la prueba de que las dos capas nuevas son distintas:

```
módulo de la empresa   = OFF
concesión al usuario   = ON   (histórica, de cuando estaba encendida)
acceso efectivo        = DENY
```

Con un solo campo no se puede: si se borra la concesión al apagar el módulo, reactivarlo obliga
a reconstruir todas las concesiones a mano. Hacen falta **dos hechos** y una **intersección**.

```
efectivo = habilitado_por_empresa  ∩  concedido_al_usuario
```

## 5. Dónde se decide hoy la autorización

```
get_current_user()      lee el usuario de la BASE en cada petición
                        → la revocación es INMEDIATA, no hay que esperar al token
require_permission()    marca la ruta y la guarda de arranque lo verifica
MasterService           aplica el filtro de empresa en las consultas de maestros
servicios de dominio    aplican `company_id` a mano, consulta por consulta
```

Esa última línea es la que más trabajo daría: el filtro de empresa está **repetido** en los
servicios, no centralizado. Un filtro de unidad seguiría el mismo camino y heredaría el mismo
riesgo de olvido.

---

## Capacidades de administración de unidad de negocio (`GA-REM-040` fase 7 · 2026-09-08)

**Solo administración.** Nada de esta tabla concede acceso productivo: el alcance operativo lo
siguen decidiendo la habilitación de la empresa y la concesión al usuario, y ninguna de estas
capacidades las otorga a quien las ejerce.

| Capacidad | Permiso | Qué permite | Qué **no** permite |
|---|---|---|---|
| Ver la configuración de cadenas | `business_units:read` | el catálogo con el estado de su empresa, y las concesiones de un usuario | ver dato productivo de ninguna cadena |
| Contratar y retirar cadenas | `business_units:update` | habilitar y deshabilitar para su empresa | conceder a nadie · borrar concesiones · tocar datos |
| Repartir acceso | `business_units:create` | conceder una cadena habilitada a un usuario de su empresa | habilitar la cadena · operar en ella |
| Retirar acceso | `business_units:delete` | revocar, con efecto inmediato | borrar la historia ni lo que el usuario registró |

```
NINGÚN ROL SEMBRADO LAS TIENE      `R-113` · decisión de propietario pendiente
CONCEDIBLES DESDE `/roles`          el catálogo las declara
VALOR POR DEFECTO                   cerrado
```

**Advertencia registrada.** `business_units:create` autoriza a conceder a cualquier usuario de
la empresa efectiva, **incluido uno mismo**. Es la política vigente, no una decisión de esta
fase, y queda auditada con actor y objetivo. Separarlo corresponde al propietario.

---

## `Administrador de Accesos` (`OD-15 §6` · `R-113` · 2026-09-09)

La figura que administra el acceso por unidad de negocio. **Cuatro permisos, y ninguno más.**

| Capacidad | Permiso | Qué permite | Qué **no** |
|---|---|---|---|
| Ver la configuración | `business_units:read` | catálogo con el estado de su empresa; concesiones de un usuario | ver dato productivo |
| Contratar y retirar cadenas | `business_units:update` | habilitar y deshabilitar para su empresa | conceder a nadie |
| Repartir acceso | `business_units:create` | conceder a **otro** usuario de su empresa | **concedérselo a sí mismo** · habilitar la cadena |
| Retirar acceso | `business_units:delete` | revocar, con efecto inmediato | borrar historia ni lo registrado |

```
NO RECIBE   `users:*`  ·  comodín `("*", …, "all")`  ·  ninguna cadena productiva
NO PUEDE    listar usuarios — `users:read` es otra cosa, y ampliarlo es cómo se abren
            los agujeros que esta figura vino a cerrar
```

**La diferencia con la entrada de la fase 7**: allí `business_units:create` autorizaba a
conceder a cualquiera «incluido uno mismo». `OD-15` lo separó. El registro de la política
anterior vive en `OD-15 §1`.

---

## Cómo se lee la sesión (`GA-REM-040` fase 8 · 2026-09-09)

| Campo | Significa | **No** significa |
|---|---|---|
| `permissions` | qué acciones autoriza el `RBAC` del actor | qué dato puede ver |
| `company_business_units` | qué cadenas tiene contratadas su empresa | qué puede operar él |
| `granted_business_units` | qué le concedió su empresa | qué es efectivo hoy |
| `effective_business_units` | **lo único que autoriza dato productivo** | — |
| `company_id` | la empresa **persistida** del usuario | dónde está operando |
| `effective_company_id` | dónde está operando **ahora** | de quién es el usuario |
| `is_super_admin` | tiene `("*", …, "all")` | que se llame «Administrador» |

**El caso que hay que saber leer**: el `Administrador de Accesos` llega con capacidades de
`business_units` y `effective_business_units` vacío. Es correcto y es el punto — administrar el
acceso no es acceder.

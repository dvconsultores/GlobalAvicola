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

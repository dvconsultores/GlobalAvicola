# QUÉ SABE LA SESIÓN

Auditoría del 2026-09-07 · `/me`, contexto de usuario y token · **solo lectura**

---

## 1. Lo que hay hoy

`get_current_user()` construye el contexto **leyendo el usuario de la base en cada petición**:

```
id · username · first_name · last_name · email
company_id · role_id · role_name · is_super_admin
permissions            ← lista de (módulo funcional, acción)
```

## 2. La matriz

| Dato | En el contexto de sesión | En `/me` | En el token | Falta |
|---|:--:|:--:|:--:|:--:|
| Empresa | **sí** | **sí** | sí (`company_id`) | — |
| Rol | **sí** | **sí** | no | — |
| Permisos | **sí** | **no** | no | ver §4 |
| **Área** | **no** | **sí** (`area_id`, desde `GA-REM-039`) | no | menor |
| **Módulos de la empresa** | **no** | **no** | no | **SÍ** |
| **Módulos del usuario** | **no** | **no** | no | **SÍ** |
| **Módulos efectivos** | **no** | **no** | no | **SÍ** |

## 3. La buena noticia: la revocación sería inmediata

El token lleva `sub` y `company_id`, y **nada más** de autorización. Los permisos se leen de la
base en cada petición. Eso significa:

```
¿Se pueden revocar módulos al instante?   SÍ, por diseño actual
¿Hay que esperar a que caduque el token?  NO
¿Hay caché de permisos que invalidar?     NO existe
```

Es una propiedad valiosa que ya se pagó —cuesta una consulta por petición— y que esta capacidad
debería **conservar** en vez de optimizar con un caché que reintroduciría el problema.

## 4. `permissions` no viaja a `/me`

El contexto interno los tiene; la respuesta de `/me` no. Por eso `R-98` sigue abierto: el
frontend no puede decidir qué ocultar porque no sabe qué puede el usuario.

Esta capacidad **podría** cerrar ese hueco de paso, si la respuesta de capacidades incluyera a
la vez permisos y módulos efectivos. No se propone aquí —`R-98` no se cierra
incidentalmente—, pero se registra la oportunidad.

## 5. La forma que tendría que tener la respuesta de capacidades

Sin implementarla, conceptualmente:

```
company_modules     lo que la empresa tiene habilitado
user_modules        lo concedido a esta persona
effective_modules   la intersección — lo único que la interfaz debería usar
```

Los tres, y no solo el tercero: una pantalla de administración necesita mostrar «concedido pero
inactivo porque la empresa lo apagó», y con solo el efectivo eso no se puede decir.

## 6. Y una advertencia

```
frontend gating = experiencia
backend gating  = seguridad
```

Exponer los módulos efectivos hace la interfaz coherente. **No** la hace segura, y no exime de
ninguna de las comprobaciones del backend.

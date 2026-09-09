# CLASIFICACIÓN DE SUPERFICIES · CONTROL GLOBAL FRENTE A INQUILINO

`OD-14` · `R-126` · 2026-09-08

```
NO HAY CLASE POR OMISIÓN
lo que no está declarado como control global es de inquilino, para todos
```

---

| Superficie | Recurso | Clase | Actor de empresa | Autoridad global **sin** contexto | Autoridad global situada en `A` | ¿La mutación exige contexto? | Permiso | Prueba | Estado |
|---|---|---|---|---|---|:--:|---|---|:--:|
| `GET /masters/companies` | `companies` | **`CONTROL_GLOBAL`** | solo la suya | todas | **todas** | n/a | `masters:read` | `test_od14_contraste_empresas_global…` | ✔ |
| `GET /roles/permissions-catalog` | capacidades | **`CONTROL_GLOBAL`** | todo | todo | todo | n/a | `users:read` | `test_r07_…` | ✔ |
| `GET /roles` · plantillas de sistema | `roles` (`NULL`) | **`CONTROL_GLOBAL`** | visibles | visibles | visibles | n/a | `users:read` | `test_r01_las_plantillas…` | ✔ |
| `GET /roles` · roles de inquilino | `roles` | **`INQUILINO`** | los suyos | ninguno | los de `A` | **sí** | `users:read` | `test_r01_el_listado…` | ✔ |
| `PUT /roles/{id}` | `roles` | **`INQUILINO`** | los suyos | — | los de `A` | **sí** | `users:update` | `test_r03_…` · `test_r04_…` | ✔ |
| `GET·POST /users` | `users` | **`INQUILINO`** | los suyos | **403** | los de `A` | **sí** | `users:*` | `test_od14_…_sin_contexto_no_obtiene_la_union` | ✔ |
| `GET·PUT·DELETE /users/{id}` | `users` | **`INQUILINO`** | los suyos | 403 | los de `A` | **sí** | `users:*` | `test_e2e_el_ataque_entre_inquilinos_completo` | ✔ |
| `/masters/farms` y demás maestros | maestros | **`INQUILINO`** | los suyos | cero filas | los de `A` | **sí** | `masters:*` | `test_od14_…_solo_ve_las_granjas…` | ✔ |
| `/business-units` · habilitación | `company_business_units` | **`INQUILINO`** | la suya | 403 | la de `A` | **sí** | `business_units:*` | `test_od14_la_administracion_de_unidades…` | ✔ |
| `/users/{id}/business-units` | `user_business_units` | **`INQUILINO`** | las suyas | 403 | las de `A` | **sí** | `business_units:*` | fase 7 | ✔ |
| `/audit` | `audit_logs` | **`INQUILINO`** | los suyos | cero filas | los de `A` | n/a | `audit:read` | `test_audit_query.py` | ✔ |
| `/approval-steps` | `approval_steps` | **`INQUILINO`** | los suyos | cero filas | los de `A` | **sí** | `approvals:*` | suites de revisión | ✔ |
| `/lots` · `/operations` · `/reports` · `/dashboard` | dato productivo | **`INQUILINO`** | el suyo | cero filas | el de `A` | **sí** | varios | fases 3 y 4 | ✔ |
| `/sap/*` | consolidación | **`INQUILINO`** + excepción de unidad | el suyo | cero filas | el de `A` | **sí** | `sap:*` | `OD-12` · fase 5 | ✔ |

---

## Cómo está implementada la clase

No hay un marco nuevo. Hay **una lista corta y declarada** en el único sitio que necesitaba una
excepción:

```python
# `app/masters/service.py`
_CONTROL_GLOBAL = {"companies"}
```

Y una propiedad que conviene nombrar: **el registro es una lista de permisos, no de
prohibiciones**. Quitar una entrada hace la superficie *más* restrictiva, no menos — el modo de
fallo apunta al lado seguro. Es lo contrario de la clasificación que causó `R-114` y `R-115`,
donde la ausencia de una entrada abría el recurso.

## Sobre una guarda estática de clasificación

`§81` pedía una sensibilidad que retirase una ruta del registro. **No aplica**, y el motivo es
la propiedad de arriba: no existe un registro de rutas cuya ausencia abra nada. Lo que existe es
la lista de exenciones, y vaciarla se detecta —es la mutación `S2`— con un fallo *restrictivo*.

Construir una guarda del tipo «toda ruta declara su clase de empresa» exigiría un registro
paralelo al de `route_scope`, y una guarda débil daría falsa seguridad. Queda documentado y no
inventado.

---

## Addendum · la sesión (`GA-REM-040` fase 8 · 2026-09-09)

| Superficie | Recurso | Clase | Actor de empresa | Autoridad global sin contexto | Situada en `A` |
|---|---|---|---|---|---|
| `GET /me` | la sesión del propio actor | **`INQUILINO`** por su contenido | su empresa | `effective_company_id` nulo · listas vacías | contexto de `A` |

La sesión no es una superficie de control global aunque la pida un actor global: **entrega el
contexto de inquilino en el que se está**. Sin contexto no entrega dato de ningún inquilino, que
es `OD-14.d` representado.

Lo que sí lleva siempre, con contexto o sin él: la identidad y las capacidades `RBAC`, que son
del actor y no de la empresa.

---

## Addendum · los candidatos a recibir una unidad (`R-129` · 2026-09-09)

| Superficie | Recurso | Clase | Actor de empresa | Autoridad global sin contexto | Situada en `A` | Permiso |
|---|---|---|---|---|---|---|
| `GET /business-units/{code}/grant-candidates` | proyección mínima de `users` | **`INQUILINO`** · plano de control | los activos de su empresa, sin él | `403` | los de `A` | `business_units:create` |

No es una sexta excepción de `RQ-03`: es un recurso de inquilino con el predicado de empresa
**en la consulta**. Y no es `users:read` con otro nombre — el mismo actor sigue recibiendo `403`
en `GET /users`, y hay una prueba que lo exige (`AC-H16`).

Sin parámetro de búsqueda ni de identificador **a propósito**: lo único que se puede pedir es
«los de mi empresa para esta unidad», y por tanto no hay oráculo.

# RBAC ROLE PERMISSION MATRIX

**Fecha** 2026-09-04 · **Wave** 2.5 · **Hallazgo** `R-44` · **Spec** `GA-REM-002`

---

## 1. Fuente normativa

El reparto de permisos **no se deriva de lo que haga falta para que pasen los tests.** Se
deriva, en este orden:

1. **`docs/12-approval-workflow.md §3`** — «Actores y responsabilidades», la única fuente
   del proyecto que enumera qué hace cada rol;
2. **el permiso que exige cada ruta**, ya declarado en el código (`GA-REM-002 AC08`);
3. **mínimo privilegio** — un permiso que la responsabilidad documentada no requiere, no
   se concede.

| Actor (`docs/12 §3`) | Responsabilidad | Rol en el sistema |
|---|---|---|
| Operador | Registrar datos operativos en campo. Crear, editar antes de enviar, enviar a revisión | `Operador de Granja` |
| Supervisor | Revisar calidad de datos. Revisar, devolver, corregir | `Supervisor Avícola` |
| Coordinador / Aprobador | Aprobación formal. Aprobar, rechazar, corregir | `Aprobador` |
| Analista SAP | Gestión de integración. Consolidar, enviar, gestionar errores | `Analista SAP` |
| Auditor | Verificación de trazabilidad. **Solo lectura** | `Auditor` |
| Administrador | Configuración del flujo, designación de aprobadores | `Super Administrador` |

Nótese que `docs/12 §3` describe un **Administrador** distinto del Super Admin, pero el
catálogo de roles del sistema no lo tiene. No se inventa: las operaciones de
administración quedan en el Super Admin y se registra la ausencia (`OD-04`).

---

## 2. Los 29 permisos exigidos

| # | Permission | Required By | Rutas | Current Seed | Existing DB Upgrade | Expected |
|---|---|---|---:|---|---|---|
| 1 | `masters:read` | catálogos en casi toda pantalla | **40** | ✅ 4 roles | **añadir a 4 roles** | Operador, Supervisor, Aprobador, Analista SAP, Auditor |
| 2 | `masters:create` | alta de maestros | 19 | Super Admin | — | Super Admin |
| 3 | `masters:delete` | baja de maestros | 19 | Super Admin | — | Super Admin |
| 4 | `masters:update` | edición de maestros | 12 | Super Admin | — | Super Admin |
| 5 | `reports:read` | KPI e informes | 14 | ✅ 4 roles | ✅ ya lo tienen | Supervisor, Aprobador, Analista SAP, Auditor |
| 6 | `lots:read` | selección y consulta de lotes | 5 | ✅ 5 roles | **añadir a 3 roles** | todos salvo Super Admin, que lo tiene por comodín |
| 7 | `lots:create` | alta de lotes | 6 | Super Admin | — | Super Admin |
| 8 | `lots:update` | edición de lotes | 1 | Super Admin | — | Super Admin |
| 9 | `operations:read` | consulta de registros | 5 | ✅ 5 roles | ✅ ya lo tienen | todos |
| 10 | `operations:create` | registro en campo | 4 | Operador | ✅ ya lo tiene | Operador |
| 11 | `operations:update` | editar antes de enviar; resolver alertas | 2 | Operador, Supervisor | **añadir a 2 roles** | Operador (`docs/12`: «Editar antes de enviar»), Supervisor |
| 12 | `operations:delete` | borrar una evidencia adjunta | 1 | Super Admin | — | Super Admin |
| 13 | `review:read` | bandeja de revisión | 3 | ✅ 3 roles | **añadir a 2 roles** | Supervisor, Aprobador, Auditor |
| 14 | `review:review` | tomar y completar la revisión | 6 | Supervisor | ✅ ya lo tiene | Supervisor |
| 15 | `review:create` | configurar pasos de aprobación | 2 | Super Admin | — | Super Admin (`docs/12`: Administrador) |
| 16 | `review:update` | ídem | 1 | Super Admin | — | Super Admin |
| 17 | `review:delete` | ídem | 1 | Super Admin | — | Super Admin |
| 18 | `approvals:approve` | aprobar y listar lo pendiente | 2 | Aprobador | ✅ ya lo tiene | Aprobador |
| 19 | `approvals:reject` | rechazar con motivo | 1 | Aprobador | ✅ ya lo tiene | Aprobador |
| 20 | `corrections:correct` | corregir un registro | 1 | Supervisor, Aprobador | **añadir a 2 roles** | Supervisor, Aprobador (`docs/12`: ambos corrigen) |
| 21 | `corrections:read` | consultar correcciones | 2 | 3 roles | **añadir a 3 roles** | Supervisor, Aprobador, Auditor |
| 22 | `audit:read` | consulta de auditoría | 3 | Auditor | ✅ ya lo tiene | Auditor |
| 23 | `sap:read` | consulta de la integración | 6 | Analista SAP | ✅ ya lo tiene | Analista SAP |
| 24 | `sap:send_sap` | consolidar, exportar, reintentar | 4 | Analista SAP | ✅ ya lo tiene | Analista SAP |
| 25 | `dashboard:read` | tableros web y móvil | 2 | 4 roles | **añadir a 4 roles** | Operador, Supervisor, Aprobador, Analista SAP, Auditor |
| 26 | `users:read` | administración de usuarios | 3 | Super Admin | — | Super Admin |
| 27 | `users:create` | ídem | 2 | Super Admin | — | Super Admin |
| 28 | `users:update` | ídem | 2 | Super Admin | — | Super Admin |
| 29 | `users:delete` | ídem | 1 | Super Admin | — | Super Admin |

---

## 3. Los 18 que ningún rol concedía

Estos son los que la activación del enforcement dejó al descubierto. Se clasifican por lo
que hay que hacer con cada uno, que no es lo mismo en todos:

### 3.1 · Reconciliar — 5 permisos, los que romperían la aplicación

| Permission | Rutas | Efecto de no concederlo |
|---|---:|---|
| **`masters:read`** | **40** | ningún desplegable carga: granjas, galpones, vacunas, tipos de alimento. **La aplicación queda inservible** |
| `dashboard:read` | 2 | el tablero, que es la pantalla de entrada, responde 403 |
| `corrections:read` | 2 | no se ve el historial de correcciones de un registro |
| `corrections:correct` | 1 | el supervisor no puede corregir, que es su función documentada |
| `operations:update` | 2 | el operador no puede editar antes de enviar, contra `docs/12 §3` |

Estos cinco **se reconcilian** en las instalaciones existentes.

### 3.2 · Correctamente exclusivos del Super Admin — 13 permisos

`masters:create/update/delete`, `lots:create/update`, `users:read/create/update/delete`,
`review:create/update/delete`, `operations:delete`.

Son operaciones de administración. `docs/12 §3` atribuye la configuración del flujo a un
**Administrador**, figura que el catálogo de roles no contempla; mientras no exista, las
ejerce el Super Admin. **No se conceden a nadie más**: mínimo privilegio.

Se registra **`OD-04`**: ¿debe existir un rol administrativo por debajo del Super Admin?
Es una decisión de negocio, no técnica, y no bloquea nada.

---

## 4. Lo que la reconciliación NO hace

| No hace | Por qué |
|---|---|
| Conceder todos los permisos a todos los roles | destruiría el control que se acaba de implantar |
| Eliminar permisos existentes | una instalación puede tener asociaciones personalizadas legítimas. **Solo añade** |
| Crear ni borrar roles | el catálogo de roles es dato del cliente |
| Reasignar usuarios a otros roles | ídem |
| Tocar el Super Admin | ya tiene el comodín `("*", …)` y pasa por la comprobación de `is_super_admin` |

---

## 5. Balance

```
Asociaciones rol↔permiso históricas .......... 24  (+9 comodines del Super Admin) = 33
Asociaciones tras la reconciliación .......... 46  (+9 comodines)                  = 55
Añadidas ..................................... 22
Eliminadas ...................................  0
Roles creados o borrados .....................  0
Usuarios modificados .........................  0
```

Reparto de las 22, medido sobre la base tras el arranque real (Wave 2.75):

| Rol | Históricas | Tras reconciliar | Añadidas |
|---|---:|---:|---:|
| Operador de Granja | 3 | 6 | 3 |
| Supervisor Avícola | 6 | 12 | 6 |
| Aprobador | 7 | 12 | 5 |
| Analista SAP | 5 | 8 | 3 |
| Auditor | 3 | 8 | 5 |
| Super Administrador | 9 comodines | 9 comodines | 0 |

> **Corrección de la Wave 2.5.** Aquel informe cifró el resultado en 41 asociaciones y 17
> añadidas. La cifra real, medida sobre la base, es **46 y 22**. El error fue de
> estimación al redactar, no de la migración: las asociaciones que la migración escribe
> siempre fueron las declaradas en `PERMISOS_POR_ROL`.

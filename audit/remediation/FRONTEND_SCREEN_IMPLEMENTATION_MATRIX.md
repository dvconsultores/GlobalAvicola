# PANTALLAS DEL FRONTEND

Auditoría maestra · 2026-09-08 · **solo lectura** · 28 páginas · 31 rutas

```
HALLAZGO QUE GOBIERNA TODA LA TABLA
El frontend NO tiene ninguna noción de autorización.
0 ocurrencias de `hasPermission`, `usePermission` o equivalente en `frontend/src`.
El menú es un array estático sin campo de permiso, módulo ni unidad.
```

---

## 1. La matriz

| Pantalla | Spec | Ruta | API | ¿Comprueba permiso? | ¿Módulo? | ¿Unidad? | Estado |
|---|---|---|---|:--:|:--:|:--:|---|
| `LoginPage` | `02 §3.1` | `/login` | `auth.store` | n/a | n/a | n/a | `COMPLETE` |
| `DashboardPage` | `02 §3.5` | `/dashboard` | `/dashboard/*` | **no** | no | backend sí | `CONNECTED` |
| `UsersPage` | `02 §3.1.2` | `/users` | `/users` `/roles` `/masters/companies` `/masters/areas` | **no** | no | no | **`PARTIAL`** · `F-E` |
| `RolesPage` | `02 §3.1.3` · `GA-REM-034` | `/roles` | `/roles` | **no** | no | no | `CONNECTED` |
| `ProfilePage` | `02 §3.1.4` | `/profile` | `/me` `/users/{id}/password` | **no** | no | no | `CONNECTED` |
| `MasterListPage` | `02 §3.2` | `/masters` | `/masters/*` | **no** | no | backend sí | `CONNECTED` |
| `WeightCurvesPage` | `GA-REM-037` · `OD-06` | `/masters/weight-curves` | servicio | **no** | no | no | `CONNECTED` |
| `LotListPage` · `LotDetailPage` · `LotFormPage` | `02 §3.4` | `/lots*` | `/lots/*` | **no** | no | backend sí | `CONNECTED` |
| `OperationListPage` · `Detail` · `Form` | `02 §3.4` | `/operations*` | `/operations/*` | **no** | no | backend sí | `CONNECTED` |
| `MyPendingPage` | `02 §3.4` | `/my-pending` | `/operations/*` | **no** | no | backend sí | `CONNECTED` |
| `MenuHubPage` · `ProcessHubPage` · `ProcessStagePage` | `11-ui-ux` | `/process*` | — | **no** | no | no | `NAVEGACIÓN` — sin datos, correcto |
| `PoultryHubPage` · `PoultryStagePage` | compatibilidad | `/poultry*` | — | **no** | no | no | re-export de las anteriores · **no es código muerto** |
| `ReviewCenter` · `ReviewDetail` · `CorrectionForm` | `12-approval-workflow` | `/review*` | `/review/*` `/corrections/*` | **no** | no | backend sí | `CONNECTED` |
| `ApprovalPanel` | `12-approval-workflow` | `/approvals` | `/approvals/*` | **no** | no | backend sí | `CONNECTED` |
| `SapManagerPage` | `10-sap-integration` | `/sap` | `/sap/*` | **no** | no | excepción `OD-12` | `CONNECTED` |
| `ReportsPage` · `LotReportPage` · `SapComparisonPage` | `02 §3.6` | `/reports*` | `/reports/*` | **no** | no | backend sí | `CONNECTED` |
| `AuditPage` | `13-audit-strategy` | `/audit` | `/audit/*` | **no** | no | no | `CONNECTED` |
| **Administración de empresa** | — | — | — | — | — | — | **`MISSING`** |
| **Administración de módulos** | — | — | — | — | — | — | **`MISSING`** · sin norma |
| **Unidades de negocio por empresa** | `GA-REM-040` `T-040-21` | — | `/business-units` | — | — | — | **`BACKEND_ONLY_EXPECTED`** · fase 9 |
| **Unidades de negocio por usuario** | `GA-REM-040` `T-040-22` | — | `/users/{id}/business-units` | — | — | — | **`BACKEND_ONLY_EXPECTED`** · fase 9 |
| **Clasificación pendiente** | `GA-REM-040` `T-040-24` | — | `/operations/pending-classification` | — | — | — | **`BACKEND_ONLY_EXPECTED`** · fase 9 |
| **Selector de compañía** | `02 §3.1.4` «(futuro)» | — | `/switch-company` | — | — | — | **`BACKEND_ONLY_EXPECTED`** · diferido por la propia spec |

```
CONECTADAS            21
NAVEGACIÓN            5   (3 reales + 2 re-export de compatibilidad)
LOGIN                 1
PARCIALES             1   UsersPage
BACKEND_ONLY          4   esperadas por hoja de ruta o por la spec
MISSING               2   administración de empresa · de módulos
```

---

## 2. `F-D` · ninguna pantalla comprueba permisos · `P1`

El menú se dibuja entero para cualquiera que entre. Un `Operador de Granja` ve *Auditoría*,
*SAP*, *Aprobaciones* y *Usuarios y Roles*; al pulsarlas el backend le devuelve `403` y la
pantalla, según cómo maneje el error, se queda vacía o suelta un `alert`.

**El backend está protegido** — la guarda de arranque de `GA-REM-002 AC08` no deja servir una
ruta sin permiso declarado, y esta auditoría lo verificó sobre las 207 rutas. No hay agujero de
seguridad aquí. Hay un producto que enseña a todo el mundo puertas que no puede abrir.

`docs/02 §3.1.3` sí lo pide: «Permisos por rol: **módulos accesibles**». La navegación tenía que
reflejarlo y no lo hace.

---

## 3. `F-E` · por qué `/users` aparece vacío · `P1`

```js
const [ur, rr, cr, ar] = await Promise.all([
  api.get('/users'), api.get('/roles'),
  api.get('/masters/companies?limit=100'), api.get('/masters/areas?limit=100')
])
setUsers(ur.data || [])
} catch (e) { console.error(e) }        // ← el error muere aquí
```

`Promise.all` falla entera si **una** de las cuatro falla. El `catch` solo escribe en consola,
y `users` se queda en `[]`. La tabla se dibuja con sus cabeceras y sin filas.

**Consecuencia:** «no tienes permiso», «el backend cayó» y «no hay usuarios» son
**indistinguibles** en pantalla. Lo que el propietario vio como una lista vacía es, con toda
probabilidad, una de las cuatro llamadas denegada — `/users` y `/roles` exigen `users:read`, y
`users:read` no lo concede ningún rol sembrado: consta como exclusivo del Super Administrador.

La causa exacta se cierra mirando la consola del navegador o los `access_logs`; la auditoría
deja demostrado el mecanismo, que es lo que hace que el síntoma sea inexplicable desde la UI.

### Columnas presentes frente a `docs/02 §3.1.2`

La spec pide: `Nombre · Apellido · Email · Username · Teléfono · Rol · **Empresa** · Estado`.

La tabla muestra `Usuario · Nombre · Email · Rol · Vista · Estado · Acciones`. **Falta
`Empresa`**, que la spec sí exige. El formulario de alta/edición **sí** tiene el selector de
compañía, de modo que el dato existe y se puede asignar; lo que no hay es la columna.
Clasificado `PARTIAL`, no `MISSING`.

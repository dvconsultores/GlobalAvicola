# GA-BU-D10 · TRAZA DEL TOGGLE DE UNIDAD DE EMPRESA

Fuente: `backend/app/business_units/admin.py::fijar_habilitacion` (`:137-185`) + `router.py:104-145`.

## 1 · Superficie

| Aspecto | Valor |
|---|---|
| Endpoints | `PATCH /api/v1/business-units/{code}/enable` · `/disable` |
| Permiso | `business_units:update` (plano de control) |
| Servicio | `admin.fijar_habilitacion(company_id = empresa efectiva, code, habilitada, actor)` |
| Transacción | Frontera en la ruta (el toggle + su auditoría son un acto) |
| Idempotencia | Fijar el estado que ya se tiene no falla ni duplica; la fila se crea si no existía (⇒ «apagada explícitamente» ≠ «nunca configurada») |
| Auditoría | `AuditLog` `CONFIG_CHANGE` / módulo `config`, `entity=company_business_unit`, `previous_state`/`new_state` = enabled/disabled, `new_values={business_unit, is_enabled}` — **después de persistir** (AC-I03: registra lo ocurrido, no lo intentado) |

## 2 · Qué modifica (y qué NO)

| Modifica | NO modifica |
|---|---|
| `company_business_units.is_enabled` (+`updated_at`) | **Ni una concesión** (`user_business_units` intacta — AC-A04) |
| Auditoría del cambio de configuración | Permisos/roles RBAC |
| — | Ningún dato productivo (lotes/eventos) |
| — | `users.company_id` / sesiones / tokens |

**User BU rows modified: NO.** No hay borrado, ni cascada, ni revocación implícita. Documentado como deliberado: «Un borrado aquí habría contestado `BU-D10` por omisión… es lo mínimo que no cierra ninguna puerta».

## 3 · Efecto en acceso efectivo

- El resolutor relee `is_enabled` **en cada petición** ⇒ apagar quita efectividad ya en la evaluación siguiente; encender la devuelve si la concesión sigue viva.
- `is_effective` reportado por la administración (`_proyectar`, `admin.py:190`) usa las **mismas tres condiciones** que el resolutor (`revoked_at IS NULL ∧ habilitación enabled ∧ unidad activa`) ⇒ lo que ve el administrador y lo que autoriza el backend no pueden divergir por construcción (hay prueba dedicada).
- **Refresh de sesión**: no requerido ni esperado; `/me` y los guards releen. (Navegación: el guard `requiresUnits` usa la lista efectiva del store de sesión; un hard-refresh o navegación posterior refleja el cambio sin relogin.)

## 4 · Evidencia ejecutada

| Fuente | Qué muestra |
|---|---|
| `test_deshabilitar_apaga_la_unidad` (`test_business_unit_admin.py:310`) | PATCH disable ⇒ `is_enabled=False` |
| `test_deshabilitar_no_borra_las_concesiones_y_rehabilitar_las_devuelve` (`:318`) | OFF: no efectiva, concesión sigue escrita · ON: vuelve (AC-A06) |
| `test_habilitar_dos_veces_es_idempotente` (`:340`) | Sin segunda fila |
| Runtime OD-16 (GA-FE-02-D/E) | Con sesión viva: OFF ⇒ batería completa DENY (21/21), global incluida |

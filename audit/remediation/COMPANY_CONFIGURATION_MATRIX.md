# CONFIGURACIÓN POR EMPRESA

Auditoría maestra · 2026-09-08 · **solo lectura**

| Configuración | ¿La exige alguna spec? | Backend | Base de datos | Interfaz | Runtime | Estado |
|---|---|---|---|---|---|---|
| Identidad de la empresa (nombre, `tax_id`, país, moneda) | `02 §3.2.1` | `CRUD /masters/companies` | `companies` | `MasterListPage` | funciona | **`CONTRADICTED`** — sin acotar por inquilino · `F-B` |
| Niveles de aprobación | `02 §3.1.4` · `12` | `Company.approval_levels` | `companies` | `MasterListPage` | funciona | `COMPLETE` |
| Configuración SAP por empresa | `02 §3.1.4` | `Company.sap_config` | `companies` | `MasterListPage` | funciona | **`CONTRADICTED`** — legible por cualquiera · `F-B` |
| Pasos de aprobación | `12` | `/approval-steps` | `approval_steps` | — | por API | `PARTIAL` — sin pantalla propia |
| Áreas funcionales | `GA-REM-039` · `OD-08` | `/masters/areas` | `areas` | `MasterListPage` | funciona | `COMPLETE` |
| **Unidades de negocio habilitadas** | `GA-REM-040` `AC-A02` | `GET·PATCH /business-units` | `company_business_units` | — | sin consumidor | **`BACKEND_ONLY`** — fase 9 (`T-040-21`) |
| **Concesiones de unidad por usuario** | `GA-REM-040` `AC-B01` | `/users/{id}/business-units` | `user_business_units` | — | sin consumidor | **`BACKEND_ONLY`** — fase 9 (`T-040-22`) |
| **Módulos activados por empresa** | **ninguna** | — | — | — | — | **`SPEC_GAP` · `MISSING`** |
| Usuarios de la empresa | `02 §3.1.2` | `/users` | `users` | `UsersPage` | vacío · `F-E` | **`CONTRADICTED`** · `F-A` `F-G` `F-H` |
| Roles y permisos | `02 §3.1.3` · `GA-REM-034` | `/roles` | `roles` `permissions` | `RolesPage` | funciona | `COMPLETE` — pero global, no por empresa |
| Selector de empresa activa | `02 §3.1.4` **«(futuro)»** | `/switch-company` | — | — | sin consumidor | **`BACKEND_ONLY_EXPECTED`** — diferido por la spec |

---

## 1. Dónde está hoy la configuración de una empresa

Repartida entre `/masters` —donde la empresa es una fila más del catálogo, junto a las vacunas y
los transportes— y `/users`. **No existe una pantalla de administración de empresa**: para
cambiar los niveles de aprobación o la configuración `SAP` de un cliente hay que entrar al
maestro genérico y editar el registro como si fuera un dato de referencia.

Eso no contradice ninguna spec: `02 §3.2.1` clasifica «Empresas» exactamente así. Pero es la
razón por la que el propietario no encuentra la administración de compañía: **está, y no parece
lo que es**.

## 2. Los roles no son por empresa

`Role` tiene `company_id` en el modelo, y el `CRUD` de `/roles` **no lo usa**: `get_roles`
devuelve todos los roles activos sin filtrar, y `create_role` no lo asigna. En la práctica el
catálogo de roles es global y compartido entre inquilinos.

`docs/02 §3.1.3` pide «Alcance por granja/empresa (multi-empresa)» dentro de los permisos, que
es otra cosa —`Permission.scope_type`— y sí existe. Pero un rol creado por la empresa A aparece
en la lista de la B. Queda como `F-I`, `P1`.

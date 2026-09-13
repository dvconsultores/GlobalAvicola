# R-196 · SPEC — FORMULARIOS DE MAESTROS POR ENTIDAD, CREACIÓN COMPLETA Y NAVEGACIÓN DE MAESTROS

Fecha: 2026-09-13 · Hallazgo canónico: **R-196** (P1 · bloquea) · HEAD `c0b4afc` · Origen B-08/B-14/B-36 + F G-01 · Registro G-07. Secciones §47.

## 1 · Contexto

P-12 gestiona 20 entidades + curvas. La pantalla genérica sirve para maestros planos; los estructurales (farms/houses/hatcheries/incubators/hatchers) y productive-phases fallan por claves padre/numéricos; la navegación no permite elegir entidad.

## 2 · Evidencia

`R-196_FINDING.md §1`: `MasterListPage.tsx:40,80,87-103,193-203`; `masters/schemas.py:64-73,95-103,124-132,149-157,166-173,525-538`; `App.tsx:220`; runtime `MAS*`/`H4*`.

## 3 · Causa raíz

Formulario único sin campos por entidad; `company_id` no resuelto en servidor para Create; sin reactivación; render crudo; navegación mono-enlace.

## 4 · Impacto de negocio

Creación de maestros estructurales imposible; pantalla en blanco en cada intento; implantación bloqueada.

## 5 · Comportamiento actual → esperado

| Entidad | Hoy | Esperado |
|---|---|---|
| farms/hatcheries | `{}` ⇒ 422 (`company_id`) | `company_id` resuelto en servidor; Create 201 |
| houses/incubators/hatchers | `{}` ⇒ 422 (padre) | selector de padre (granja/planta) + Create 201 |
| capacity/order vacíos | `''` ⇒ 422 | `null`/omitido |
| is_active | no editable | reactivación explícita (PUT con confirmación) |
| 422 | React #31 | `getErrorMessage` (texto seguro) |
| Navegación | solo `farms` | selector de entidad en `/masters` (todas alcanzables) |

## 6 · Comportamiento esperado

1. **Formularios por entidad** (mínimos): campos padre con `SearchSelect` (farms→company oculta; houses→farm; incubators/hatchers→hatchery), numéricos opcionales (`capacity`, `order`) como `null` si vacíos, resto igual que hoy.
2. **`company_id` resuelto en servidor** para los Create que lo declaran (patrón `create_user`; coordinado con R-50: el campo deja de aceptarse del cliente). Sin contexto ⇒ 4xx fail-closed.
3. **Reactivación**: acción «Activar» en edición (PUT `is_active:true`) con confirmación; baja sigue siendo lógica.
4. **Errores**: `getErrorMessage` en guardar/borrar; sin `alert`; sin React #31 (R-215 añade el boundary global).
5. **Navegación**: `/masters` muestra selector/lista de entidades (por permiso/unidad) y cada entidad es alcanzable sin URL; paridad con `NAV_ITEMS` (F G-01).
6. Sin cambio de contratos de respuesta; sin migración.

## 7 · Alcance

- `MasterListPage.tsx` (campos por entidad, numéricos, reactivación, errores), `App.tsx` (config de entidades/columnas ya existente; añadir selector), `navigationConfig` si aplica.
- `backend/app/masters/service.py` + esquemas: resolución de `company_id` en Create (según R-50; si R-50 no se implementa antes, mínimo viable: mantener inyección cuando llega `None` y **rechazar** `company_id` explícito en Create de inquilino — documentado).
- Tests: `frontend/.../__tests__/r196.mastersCreate.test.tsx` (jsdom; rojo: `{}`), backend `test_r196_masters_create_context.py`; navegación unit/regresión.
- Sin migración; sin permiso nuevo.

## 8 · Fuera de alcance

- Curvas de peso (pantalla propia, correcta).
- OD-24 (empresas/granjas SAP): régimen provisional.
- Rediseño visual completo de maestros (solo lo necesario).
- R-50 completo (paquete de seguridad propio; aquí el consumo del patrón).

## 9 · Impacto frontend

`MasterListPage` + navegación; sin rediseño mayor.

## 10 · Impacto backend

`masters/service.py`/esquemas (resolución de contexto; coordinación R-50). Sin modelos.

## 11 · Contrato frontend↔backend

Create de 5 entidades: `company_id` deja de viajar (resuelto en servidor) — cambio documentado; `capacity`/`order` opcionales aceptan `null`/ausencia. Respuestas sin cambio.

## 12 · Impacto en datos

Sin migración; maestros existentes intactos.

## 13 · Seguridad

Coordinado con R-50 (no aceptar `company_id` de cliente); tenant fail-closed sin contexto.

## 14 · Inquilino

Create resuelto por contexto del actor (empresa efectiva); padres verificados (ya lo hace el servicio).

## 15 · Unidad de negocio · 16 · RBAC

Sin cambio (`masters:*`; gates existentes).

## 17 · Transacciones

Sin cambio.

## 18 · Auditoría

Sin cambio (`MasterService` audita CREATED/UPDATED/DELETED).

## 19 · i18n

Etiquetas nuevas (selector de entidad, reactivar, campos padre) ES/EN; sin literales.

## 20 · Escritorio · 21 · Móvil

Maestros son web (`WebOnlyRoute`); verificación de usabilidad a 1280 y tablet.

## 22 · Manejo de errores

`getErrorMessage` en guardar/borrar/reactivar; sin `alert`/React #31; 4xx de contexto claros.

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

Prepara maestros fiables (OD-24 pendiente para empresas/granjas).

## 25 · Compatibilidad hacia atrás

- 16 maestros planos: idénticos.
- Clientes API que enviaban `company_id` en Create de inquilino: rechazado (corrección de seguridad; documentar).
- Rutas `/masters/:entity`: siguen existiendo (deep links válidos).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R196-01 | Crear **farm** por UI ⇒ 201 (company del contexto; sin React #31) |
| AC-R196-02 | Crear **house** eligiendo granja ⇒ 201; sin granja ⇒ validación cliente clara |
| AC-R196-03 | Crear **hatchery/incubator/hatcher** ⇒ 201 (padres correctos) |
| AC-R196-04 | `capacity`/`order` vacíos ⇒ `null` (sin 422) |
| AC-R196-05 | Reactivar maestro ⇒ PUT `is_active:true` ⇒ visible activo |
| AC-R196-06 | 422 de maestros ⇒ mensaje de texto (sin pantalla en blanco) |
| AC-R196-07 | `/masters` permite navegar a **todas** las entidades sin URL escrita |
| AC-R196-08 | Unicidad/duplicado (409) legible; sin crash |
| AC-R196-09 | Sin migración/endpoint/permiso; diff FE+BE (masters) |
| AC-R196-10 | Regresión: `test_master_management.py`, `test_master_tenant_isolation.py`, `test_company_catalog.py`, suite maestros verde (tras GA-GOV-03 lo aplicable) |

## 27 · Pruebas RED→GREEN

`§1`: `r196.mastersCreate` (rojo: `{}`/422), backend `test_r196_masters_create_context.py` (rojo: Create sin company resuelta/aceptando company ajena), navegación (unit o E2E).

## 28 · E2E

`§2`: `R196-RT-01…06` (crear las 5 entidades; reactivar; navegar a todas). Artefacto `evidence/r196/runtime-{red,c3}.json` + capturas.

## 29 · UAT

`UAT-R196-01…04`: crear una granja, un galpón, una planta y una incubadora; reactivar un área; ver errores legibles. Criterio 4/4 (agrupable con R-215).

## 30 · Criterios de cierre

AC-01…10 verdes · RED en `c0b4afc` · GREEN local (vitest/tsc/build) · runtime con artefactos · UAT 4/4 · sin migración/endpoint/permiso · R-196 → `CLOSED` con GA-REM asignado.

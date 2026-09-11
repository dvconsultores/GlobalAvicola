# GA-FE-06 · R-182 · RECONCILIACIÓN CANÓNICA

Fecha: 2026-09-11 · Baseline: `116cee0` · Producto: `005a252` · Bundle: `index-WUv1-F9o.js`
Fuentes leídas: `REMEDIATION_BACKLOG.md §R-182` · `CERTIFICATION_SCOPE_RECONCILIATION.md` · `backend/app/{lots/{router,schemas,service},masters/models,notifications/{sla,recipients}}.py` · `alembic/versions/o5p6q7r8s9t0_areas_and_planned_close.py` · `tests/test_lot_planned_close.py` · `frontend/src/pages/lots/LotFormPage.tsx`.

## 1 · Texto original (R-182, P2 — propuesto en GA-FE-01)

> «`LotFormPage` captura `planned_close_date` (control + zod) pero el payload (8 claves) no lo envía; `area_id` declarado en el esquema sin control ni envío; `backend/app/notifications/sla.py` selecciona lotes por `Lot.planned_close_date.isnot(None)` + estado activo → la notificación «lote próximo a cierre» no puede dispararse para lotes creados por UI. No corregido en GA-FE-01 (fuera de objetivos).»

## 2 · Verdad actual del código (verificada hoy)

| Dimensión | Verdad |
|---|---|
| Modelo `Lot` | `planned_close_date` = `DateTime(timezone=True)`, **nullable** · `area_id` = FK `areas.id`, **nullable**, indexado (`masters/models.py`) |
| Migración | `o5p6q7r8s9t0_areas_and_planned_close.py` ya creó **ambas columnas** ⇒ **NO hace falta migración** |
| Contrato create | `LotCreate(LotBase)` **ya acepta** `planned_close_date` y `area_id` (ambos opcionales); service aplica `_fecha_de_negocio` (medianoche UTC, `R-75`) y `area_id` tal cual |
| Contrato update | `LotUpdate` (`extra=forbid`) incluye `area_id` y `planned_close_date` («Replanificar es legítimo…») |
| Lectura | `LotRead(LotBase)` devuelve ambos campos en fresh GET |
| SLA near-close | `app/notifications/sla.py::evaluar_lotes_proximos_a_cierre` — ventana **`0 <= días hasta la fecha prevista <= 3`** (`DIAS_PARA_CIERRE=3`, día natural vs día natural), excluye `NULL`, lotes no `active` y fechas pasadas; tipo `lot_near_close`; ocurrencia `lot:{id}:{fecha}`; destinatarios por `resolver_destinatarios(company_id, area_id, originadores)` |
| `area_id` en SLA | **participa**: resuelve gerente/supervisores por `User.area_id` |
| Área (modelo) | `Area`: `company_id` (nullable FK), `name`, `code`, `description`, `is_active` (baja lógica). **No** tiene `farm_id` ni BU ⇒ el ámbito es **empresa**, no granja |
| Permiso áreas | `GET /masters/areas` = `masters:read` (CRUD genérico de maestros, ya usado por `UsersPage`) |
| Frontend hoy | `LotFormPage`: zod con `area_id` y `planned_close_date`; **control de PLD existe** (Input date, label `lots.plannedClose`); **`area_id` sin control, sin fetch de áreas, sin estado**; **payload de 8 claves omite ambos** ⇒ pérdida silenciosa |

## 3 · Brecha restante exacta

1. **Pérdida silenciosa en el alta**: el payload no incluye `planned_close_date` ni `area_id` ⇒ el backend nunca recibe los valores (los defaults nullable quedan `NULL`).
2. **Sin selector de Área**: `area_id` no es capturable por el usuario (campo zod muerto).
3. **SLA no activable por UI**: sin `planned_close_date` persistida, `evaluar_lotes_proximos_a_cierre` no puede disparar `lot_near_close` para lotes creados por UI (premisa del hallazgo).
4. **Relectura**: el detalle de lote no muestra la fecha prevista (superficie inexistente hoy).

## 4 · Lo que NO es un defecto actual (para no inventar trabajo)

- El backend **no** requiere cambios: acepta, valida empresa/granja, normaliza fecha de negocio y devuelve ambos campos.
- `Area` **no** es farm-scoped ni BU-scoped: los casos «wrong-farm»/«area↔BU» quedan **N/A** por modelo canónico (no se inventa restricción).
- `NULL` es válido en ambos campos (columnas nullable; SLA excluye sin fecha explícitamente: «sin referencia no se inventa ninguna»).
- La validación de fechas: **no existe** regla canónica de relación PLD↔start (backend permisivo; spec no fija regla) ⇒ **no se añade** validación nueva.
- `sap_reference` en el payload del form: `LotBase` no lo declara (pydantic lo ignora). Observación **no relacionada con R-182**; se registra aparte y **no se toca** (§11: hallazgo genuino distinto → registrar, no mezclar).

## 5 · Criterios de cierre R-182 (completos)

1. Alta UI envía `planned_close_date` cuando el usuario la captura, en formato de fecha de negocio (sin desfase ±1 día tras crear, refrescar y re-loguear).
2. Alta UI ofrece selector de **Área** (maestro canónico de la empresa) y envía `area_id` cuando se elige; vacío ⇒ `NULL` (canónico).
3. Fresh GET devuelve **ambos** valores persistidos; el detalle muestra la **fecha prevista** (superficie existente ampliada mínimamente).
4. Un lote creado por UI con fecha prevista **dentro** de la ventana `0..3` entra en la lógica `lot_near_close` (evidencia API/runtime); **fuera** de la ventana no entra; **frontera** exacta respetada; `NULL` excluido según contrato.
5. Área foránea (otra empresa) **no** es asignable (selector filtrado + API denegada); sin fuga entre inquilinos.
6. Seguridad productiva intacta: CBU OFF / sin User BU / sin RBAC ⇒ alta denegada (UI+API), global sin bypass.
7. Sin cambios backend · sin migración · sin permisos nuevos · sin lógica SLA nueva.
8. Sin regresión GA-FE-02/03/04/05 (R-98/R-119/R-181 permanecen CLOSED).
9. i18n ES/EN sin claves crudas; desktop + móvil usables; sin pérdida silenciosa de campos gobernados en el alta.

## 6 · Dedup

`R-98/R-119/R-181`: ámbitos distintos (cerrados). `R-130/R-159/R-160/R-166…R-179`: no cubren alta de lote/PLD/área; el consumidor de avisos queda en `recipients` (empresa+área) — R-182 no lo modifica. No se crea ID nuevo.

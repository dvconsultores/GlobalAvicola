# GA-R153 · SPEC — LOTE DE ABUELAS AUTOMÁTICO AL APROBAR LA IMPORTACIÓN (OD-25 B)

Fecha: 2026-09-12 · Baseline `9ad9b26` · Autorización: propietario (AOD-25 → OD-25) · Clase: brecha de implementación vs promesa escrita (`docs/02 §3.4.2`).

## Contexto
Trazas completas: `GA_R153_CURRENT_FLOW_TRACE.md` (flujo actual), `GA_R153_LOT_FIELD_MAPPING.md` (campos), `GA_R153_SEQUENCE_ANALYSIS.md` (código/secuencia/concurrencia/legado).

## AOD-25 / R-153 / promesa histórica / hueco actual
Decisión **OD-25 = B** (`GA_OD_25_...DECISION.md`). Finding **R-153** (P3; dependencia R-152 CLOSED). Promesa: «al completar la importación se crea automáticamente el lote de abuelas». Hueco probado: importación **exige lote previo** (400 runtime pre-fix) y la aprobación **no crea** nada.

## Disparador canónico
**Aprobación P-07 de la importación** (nunca registro, llegada, cuarentena ni acción de UI).

## Ciclo de importación (nuevo)
1. Alta de `grandparent_import` **sin lote** (o con lote en el flujo legado). 2. Ciclo P-07 normal. 3. Aprobación → consecuencia. 4. Recepción (paso 4) contra el lote creado.

## Ciclo de aprobación (protección P-07)
Intacto: estados, RBAC, segregación, auditoría, concurrencia (FOR UPDATE). La consecuencia se ejecuta **en la misma transacción** en ambas rutas de aprobación: `ApprovalService.approve` y `complete_review` nivel único — patrón del hook de reverso.

## Creación automática del lote
Helper `crear_lote_de_importacion_si_procede(db, event, actor)` (dominio: `lots/service.py`) invocado tras el cambio de estado. Guardas: `event_type == grandparent_import` **y** `event.lot_id is None`. Crea exactamente 1 `Lot` (mapeo §campos), `flush`, fija `event.lot_id`, auditoría `CREATED` (módulo lots, con `event_id` de origen).

## Código / secuencia / año
`L-GP-{año}-{nn}`; año = `arrival_date.year`; secuencia por empresa; lock asesor por (empresa, año) + savepoint/reintento global ante colisión (detalle y propiedades en el análisis de secuencia). Sin migración.

## Idempotencia
Doble `approve` → 400 por máquina de estados; hook además no-op si `lot_id` ya está fijado. Concurrencia del mismo evento serializada (R-166). **Nunca dos lotes.**

## Atomicidad
Aprobación + creación + enlace + auditorías = **una** transacción (`RutaTransaccional`); cualquier fallo revierte todo (import aprobado sin lote imposible; lote sin aprobación imposible).

## Legado
`LEGACY_PREASSIGNED_LOT_COMPATIBILITY` (sin segundo lote; sin migración de datos).

## Vía manual
`POST /lots` intacta (formulario, permisos, validaciones). Deja de ser prerequisito **solo** para la importación nueva.

## Población / recepción
Aprobación: **delta de aves = 0** (documental; AC-R152-08 se preserva). Recepción: única entrada de población (BR-17/18); objetivo = lote nuevo. Sin doble conteo.

## P-01 / P-07 / R-130
P-01: regresión focalizada del paso afectado; estado del proceso **sin cambio**. P-07: sin rediseño; sin lote en denegado/devuelto/rechazado. R-130: invariantes intactos (no se toca el saldo).

## Tenant / BU / RBAC
Lote SIEMPRE de la empresa del evento (cross-tenant imposible por `company_id=event.company_id`). Unidad: dominio **grandparent**; guarda de unidad del lote ($lot.bird_type$ legado) o de cadena (`"grandparent"`) en el alta sin lote; BU OFF global/empresa ⇒ falla cerrada; concesión revocada (OD-23) ⇒ denegado; permisos existentes (`operations:create` para registrar; `approvals:*` para aprobar). **0 permisos nuevos.**

## Auditoría
`audit_state_transition` (aprobación; se preserva) + `audit_accion CREATED` (lote) con `entity_type="lot"`, `company_id` y metadatos (`origin="grandparent_import_approval"`, `event_id`). Sin payloads sensibles.

## Impacto frontend / i18n / errores
- `OperationFormPage`: `grandparent_import` deja de forzar lote (selector opcional; nota informativa i18n `operations.importLotAutoNote`).
- `OperationDetailPage`: `lot_id` → enlace a `/lots/{id}`; sin lote en importación → texto `operations.lotAutoPending` («se creará al aprobar»).
- ES/EN por claves; sin strings hardcodeadas.
- Errores gobernados: plan inválido ⇒ BR-22 (400 por manejador tipado); unidad no operativa ⇒ 403; sin 500 ni SQL crudo.

## Fuera de alcance
Rediseño P-07; cambios de saldo/BR-17/18; migración; permisos/endpoints nuevos; UI nueva de lote; SAP; Wave B/C.

## AC (contrato ejecutable — R153-AC01…57)
Core: 01 OD-25 registrada · 02 R-153 dueño · 03 R-152 cerrado · 04 sin prerequisito de lote (flujo nuevo) · 05 sin lote antes de aprobar · 06 exactamente 1 al aprobar · 07 misma empresa · 08 dominio grandparent.
Datos: 09 código secuencia canónica · 10 único · 11 concurrencia sin duplicar código · 12 fecha=plan · 13 sexo=plan · 14 demás obligatorios con fuente canónica · 15 sin datos inventados.
Población: 16 delta 0 · 17 sin movimiento equivalente · 18 pre-recepción canónica vacía · 19 recepción = entrada · 20 una sola vez · 21 sin doble conteo · 22 R-130 preservado.
Idempotencia: 23 reintento sin 2º lote · 24 retry de red sin 2º lote · 25 concurrencia sin 2º lote · 26 ≤1 lote por importación · 27 legado con lote no duplica.
Estados: 28 rechazado sin lote · 29 devuelto sin lote · 30 aprobación fallida sin lote confirmado · 31 fallo de lote no deja aprobada sin lote · 32 coherencia transaccional.
Manual: 33 vía manual funcional · 34 ya no obligatoria para importación nueva · 35 reglas manuales sin cambio.
Frontend: 36 UI no fuerza lote · 37 aprobación por superficie normal · 38 lote identificable tras aprobar · 39 recepción continúa · 40 desktop · 41 móvil (si la superficie lo soporta) · 42 ES/EN · 43 sin error crudo.
Seguridad: 44 plan/importación ajena no crea en la empresa propia · 45 BU OFF falla cerrado · 46 sin concesión falla cerrado · 47 sin RBAC falla cerrado · 48 global no bypassa BU OFF · 49 sin enlace cross-tenant.
Regresión: 50 P-07 preservado · 51 P-01 sin regresión (paso afectado) · 52 P-01 sin ascenso por transitividad · 53 R-130 · 54 R-152 · 55 GA-FE-02..08 · 56 R-181..188 · 57 OD-21/22/23.

## Pruebas / runtime / UAT / cierre
Backend PG: `tests/test_r153_import_lot_auto.py` (CI; skip local declarado). Frontend: `r153.importLotOptional.test.ts` + suite completa. Runtime: E2E-01…16 (import sin lote → aprobación → lote → recepción; negativos de seguridad; manual; legado). UAT propietario: 7 casos (`GA_R153_OWNER_UAT.md`). Cierre: `R-153 CLOSED_FUNCTIONALLY_CERTIFIED` + OD-25 `RATIFIED_IMPLEMENTED` con `OWNER_ACCEPTANCE: PENDING`.

# GA-REQ-061 · MATRIZ DE SEGURIDAD (PROPOSED)

Base vigente: tenancy `app/tenancy.py` (BR-07) · OD-16 absoluto (GA-FE-02-D) · OD-21 (maestros inactivos) · OD-14 (sin bypass por `is_super_admin`) · R-139 (concesiones) · patrón RBAC `modulo:accion`.

## 1 · Frontera de acceso

```
COMPANY → COMPANY BU ENABLED → USER BU GRANT → RBAC → RESOURCE OWNERSHIP → BUSINESS RULE
```

| Capa | Regla | Fail-closed |
|---|---|---|
| Company | Todo batch/item/opening pertenece a una company; lecturas y escrituras filtradas por empresa efectiva | 404 |
| BU empresa | Batch declara BU; **BU OFF ⇒ denegado** para apply/validate/upload (operación productiva OD-16) | 403/404 |
| Grant usuario | Actor tenant requiere grant de la BU (effective) | 403 |
| RBAC | Permisos del módulo cutover (ver §3) | 403 |
| Ownership | Company A no ve/modifica/aprueba/apply/descarga batch de B (AC31-33) | 404 |
| Reglas | Masters existentes/activos (si referencia nueva), identidad de lote, checksum, estados | 400/409/422 |

**El cutover NO habilita BU, NO crea grants, NO modifica `effective_business_units`** (AC37/38). El plano de control (administración) sigue aparte: CONTROL ≠ OPERATION.

## 2 · Multi-tenant (pruebas futuras)

CUT-RED-01/02/03 (ver plan RED): listar, modificar y apply cross-company deben denegar; además `GET archivo` y `correcciones` cross-company. Backend autoritativo; sin rutas alternas (descarga directa incluida).

## 3 · RBAC — decisión PROPOSED

- **Auditoría del catálogo**: los permisos del sistema son cadenas `modulo:accion` (p.ej. `approvals:approve` usado por R-184; `lots:*`, `masters:*`, `users:*`, `corrections` existente). No existe módulo `cutover`.
- **Propuesta**: módulo **`cutover`** con `cutover:create` (crear/upload), `cutover:validate`, `cutover:approve`, `cutover:apply`; correcciones de opening reutilizan el permiso canónico de correcciones (`corrections:correct` o el nombre exacto vigente — verificar contra catálogo al implementar; si difiere, se documentará en la tranche).
- **Separación de funciones** (deducible del patrón vigente, no requiere Owner): `created_by ≠ approved_by` y `approved_by ≠ applied_by`; el creador no aprueba su propio batch (espejo de segregación BR-14). `cutover:apply` NO implica `cutover:approve`.
- Si el negocio exigiera una segregación **más estricta** (p.ej. 4 actores siempre distintos incluido apply) ⇒ `OWNER_GATE_REAL` en esa tranche. Default propuesto arriba.

## 4 · Maestros inactivos (OD-21 — doble escenario)

| Escenario | Regla |
|---|---|
| Cutover **crea** lote migrado (referencia nueva) | Master inactivo ⇒ **DENY** (`MASTER_INACTIVE`) |
| Lote **ya existía** con referencia a master hoy inactivo | Se **conserva**; no se invalida el opening por eso (AC53) |

## 5 · Inmutabilidad y correcciones

- APPLIED = inmutable (AC25/59/60): sin UPDATE/DELETE directos; sin re-apply (409).
- Correcciones: permiso de correcciones + razón obligatoria + before/after/delta + auditoría (AC62-64); nunca borran eventos post-cutover (AC65).
- `cutover_datetime` inmutable salvo corrección formal registrada (AC09).

## 6 · Auditoría (AC70-75)

Eventos: `CREATE_BATCH · UPLOAD · VALIDATE · SUBMIT · APPROVE · REJECT · APPLY · FAILED_APPLY · CORRECT · DOWNLOAD_TEMPLATE` con `actor · effective_company · BU · batch · target · reason · timestamp`. Sin secretos ni contenido completo de archivos en el log. Reutiliza `audit_accion` (T8) y patrón de módulos (`AuditModule`).

## 7 · Superficies adicionales

- Descarga de plantilla: disponible a roles que pueden crear batch (mismo gate).
- Upload: límite de tamaño/tipo; sha256; archivo accesible solo por company.
- Reporting/reconciliación: mismos gates de lectura que el batch.

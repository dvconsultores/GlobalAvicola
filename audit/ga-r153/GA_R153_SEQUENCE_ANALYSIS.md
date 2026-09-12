# GA-R153 · ANÁLISIS DE SECUENCIA Y CONCURRENCIA DEL CÓDIGO

Fecha: 2026-09-12.

## 1 · Convenciones existentes (evidencia)

- **No existe generador** de `lot_code` en el backend: el alta manual lo exige del usuario (`lots/schemas.py:29`; `LotFormPage` campo «Código»). Códigos reales de fixtures: `L-BO-2026-05`, `L-2026-001`, `L-R187-DET`, `GA6A-…`.
- **Unicidad real: GLOBAL** — índice único `ix_lots_lot_code` sobre `lot_code` solo (`b53bbe02a476:257`), no compuesto con empresa.

## 2 · Regla adoptada (OD-25)

- Formato: **`L-GP-{año}-{nn}`** (nn ≥ 2 dígitos, `01, 02, …`).
- **Año = `import_plan.arrival_date.year`** (fecha canónica del lote). Nunca el año del servidor.
- **Secuencia por empresa** (numeración normal 01… dentro de `(company_id, año)`).
- Salvaguarda de unicidad: la BD es global-única ⇒ ver §3.4.

## 3 · Concurrencia (sin migración)

1. **Lock asesor transaccional de PostgreSQL** por `(empresa, año)`:
   `SELECT pg_advisory_xact_lock(hashtext('lote-gp:{company_id}:{anio}'))` — se libera solo al commit/rollback de la transacción de aprobación (la misma que crea el lote).
2. **Candidato**: `max(nn)` de los códigos `L-GP-{año}-%` **de la empresa** + 1.
3. **Inserción bajo savepoint** (`begin_nested`): si la unicidad global choca (otra empresa usó el mismo `nn`), el savepoint se revierte sin abortar la transacción.
4. **Reintento acotado (≤3)** ante colisión: lock asesor **global del año** (`'lote-gp:{anio}:global'`) + `max(nn)` sobre **todas** las empresas + 1 (garantía de unicidad bajo el lock global).
5. Dialecto no-PG (tests locales en SQLite, si aplican): sin lock asesor; el reintento del §3.4 sigue operando.

## 4 · Propiedades resultantes

- Determinista (misma entrada ⇒ mismo candidato) · por empresa · unicidad garantizada por BD + reintento · seguro bajo aprobaciones concurrentes del mismo año.
- **Sin migración**: no se crean tablas de contador ni secuencias PG.

## 5 · Compatibilidad de legado

- **LEGACY_PREASSIGNED_LOT_COMPATIBILITY:** si la importación aprobada ya tiene `lot_id` (flujo antiguo), el hook **no** crea lote (no hay segundo lote; AC27). No se migran ni reescriben datos.
- La numeración convive con códigos manuales existentes (prefijo `L-GP` reservado a este generador).

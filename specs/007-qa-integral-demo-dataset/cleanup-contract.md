# Cleanup Contract — `QA-DEMO-V1`

**Estado en el runtime compartido: `READY_NOT_EXECUTED`** (OD-QA-04). El cleanup existe, está probado en aislado y documentado; no se ejecuta en el runtime hasta decisión Owner.

## 1 · Alcance

`--cleanup` elimina **exclusivamente** entidades que pertenecen a las dos empresas QA (`tax_id ∈ {QA-DEMO-V1-INTEGRAL, QA-DEMO-V1-AISLAMIENTO}`) o que cuelgan de ellas (usuarios, concesiones, lotes, eventos, movimientos, aprobaciones, correcciones, reversos, alertas, notificaciones, auditoría de esas empresas, cutover, inbound SAP, referencias SAP, maestros, curvas, áreas) y finalmente las empresas. No toca: roles, permisos, `business_units`, `productive_phases`, el usuario `admin`, las empresas de certificación ni ningún dato ajeno.

## 2 · Fail-closed

Antes de borrar, audita que dentro de las empresas QA todo usuario empiece por `qa.`, todo lote por `QA-` y toda referencia SAP por `QA-`/`QAP`. Si algo no cumple ⇒ `status=AMBIGUOUS_QA_DATA`, lista `ambiguous`, **0 borrados** (también en modo real). `--force-unmarked` es la única vía para proceder y exige decisión explícita.

## 3 · Orden

Derivado de `Base.metadata.sorted_tables` invertido (dependientes primero). El test `test_cleanup_cubre_toda_tabla_que_referencia_a_las_que_borra` exige que toda tabla con FK hacia el plan esté en el plan. Un solo `DELETE … WHERE … IN (…)` por tabla, en una transacción; cualquier error ⇒ rollback total.

## 4 · Guardas

- `ENVIRONMENT ∈ {production, prod, staging, pre, preprod}` ⇒ abort.
- Modo real exige `--confirm-target <nombre_bd>` igual al de `DATABASE_URL` (o `GA_QA_SEED_CONFIRM_TARGET`).
- `--dry-run` solo cuenta e imprime el plan.

## 5 · Evidencia requerida antes de ejecutar en runtime

1. `--inventory` previo. 2. `--cleanup --dry-run` con `ambiguous=[]`. 3. Autorización Owner escrita. 4. `--cleanup --confirm-target avicolav2`. 5. `--inventory` posterior = vacío. 6. Verificación de que usuarios no-QA, empresas no-QA y lotes no-QA conservan sus recuentos.

## 6 · Resultado en aislado (2026-10-18)

Dry-run 2447 filas contadas (las dos condiciones de `egg_batches`/`chick_batches` se solapan en el conteo); real `CLEANED total=2438`; inventario posterior vacío; baseline intacto (`companies=2, roles=7, admin=1, phases=4, business_units=4`); `--apply` posterior recreó 719 entidades y `--verify` PASS. Detalle en `audit/qa-integral-dataset/07_CLEANUP_PROOF.md`.

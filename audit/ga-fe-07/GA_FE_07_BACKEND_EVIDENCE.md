# GA-FE-07 · EVIDENCIA BACKEND

## Cambio (C2 `5a5bb3f`)

| Fichero | Cambio |
|---|---|
| `app/tenancy.py` | `verificar_catalogo_de_empresa` **extendido** con `exigir_activo: bool = False` (keyword-only). Con `True`: misma tenencia (ajena ⇒ «no encontrado») **+** `is_active IS FALSE` ⇒ `BusinessRuleViolation("Área inactiva", "BR-07")`. Default `False` ⇒ los callers de `R-179` conservan su contrato **intacto** |
| `app/lots/service.py` (alta) | La validación de área existente pasa `exigir_activo=True` — referencia nueva exige área activa |
| `app/lots/service.py` (edición) | **Detección de cambio** con `exclude_unset` + comparación contra `lote_actual.area_id` (capturado del `get_by_id` que ya hacía la guarda de unidad): solo valida cuando `area_id` está en `fields_set`, no es `None` y **difiere** del actual (matriz H1–H5). Negativas antes de `MasterService.update` ⇒ sin mutación ni auditoría de éxito |

Cero migración · cero permiso · cero endpoint · SLA intacto · frontend de producto: solo el filtro del selector (no toca API ni administración).

## Gates locales (declarados)

| Gate | Resultado |
|---|---|
| `py_compile` tenancy+service | OK |
| Suite nueva `tests/test_lot_area_eligibility.py` (11 casos) + ownership + areas + planned_close | **35 skipped** local (requieren PostgreSQL — familia lotes; corren en CI), colección válida |
| Gate PG-libre (OD-16 + catálogo BU) | **7 passed** |
| Regresión tenant/OD-16/R-163 | Cubierta por el gate PG-libre + suites de la familia (CI) |

## Semántica verificada en runtime de contrato

- Alta inactiva ⇒ `400 {"detail":"Área inactiva","rule":"BR-07"}` (mismo inquilino, distinguible; sin datos de empresa).
- Alta ajena/inexistente ⇒ `400 {"detail":"Área no encontrado","rule":"BR-07"}` (anti-enumeración R-182-A intacta).
- Edición: cambio efectivo ⇒ validación nueva; omisión / mismo id / `null` ⇒ **sin** regla nueva (historia preservada).

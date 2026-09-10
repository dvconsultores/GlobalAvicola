# `R-153` · Matriz de brecha (`R153_PROGENITORAS_GAP_MATRIX`) — `OWNER_DECISION_REQUIRED` (`AOD-25`)

**WAVE B · tranche 12 · pre-flight** · 2026-09-10 · `R-153` (P3) · «el lote de abuelas no se crea automáticamente al completar la importación» ·
depende de `R-152` (`HARD_DATA_MODEL` + `HARD_FUNCTIONAL`, `R152_R153_DEPENDENCY_TRACE.md §2`).

| Superficie | Requisito | Comportamiento esperado | Comportamiento actual | Reproductoras | ¿Mismo contrato? | Modelo | Servicio | Ruta | Frontend | Seguridad | Filtro | Validación | Auditoría | Brecha | Raíz | AC | Prueba |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| creación del lote de abuelas | `docs/02 §3.4.2` («Al completar la importación, se crea automáticamente el lote de abuelas. Vinculación: Lote → Granja → Galpón → Trazabilidad») · `spec.md §4.4` («Creación de lote de abuelas vinculado a granja/galpón») | un lote `grandparent` nace de la importación completada, con granja/galpón, línea genética y fecha; trazable hacia Reproductoras | el lote se crea a mano (`POST /lots`, `LotFormPage`) **antes** de la importación, porque `grandparent_import` exige `lot_id` (`LOT_OPTIONAL_EVENTS` = inspecciones) | lote de cría manual (`§3.5.1`) | no (`PROGENITORAS_SPECIFIC`) | `Lot` · `OperationalEvent.lot_id` | `create_lot` (manual) · ninguna rama automática | — | `LotFormPage` | `AC-L02/L14` (creación de lote por unidad) | — | — | `audit_accion` del lote | **no implementado** (`H360A-03`) | **`OWNER DECISION GAP`** | — | — |

## Lo que el repositorio no define (y por qué no se decide aquí)

| Semántica | Fuentes consultadas | Estado | Por qué es implementación-crítica |
|---|---|---|---|
| qué es «completar la importación» | `docs/02 §3.4.2` (solo «al completar»), `spec.md §4.4`, `docs/12` (estados de `P-07`), `PROCESS-01` (la importación es el paso 1 de una cadena que sigue con inspecciones y recepción) | **silencio**: registro (`REGISTERED`), aprobación (`APPROVED`), llegada (`arrival_date`) o fin de cuarentena (`quarantine_end_date`) son lecturas distintas | fija el momento en que existe un lote con efectos (unidad, saldo, fases) |
| código del lote automático y atributos derivados | `docs/02 §3.5.1` («Lote, Granja, Galpón(es), OC, Proveedor, Raza/Línea genética, Fecha de inicio» — para Reproductoras, y a mano) · `Lot.lot_code` único | **silencio** sobre la regla del código (¿OC?, ¿secuencia?, ¿prefijo?) y sobre `start_date` (¿llegada?, ¿registro?) y `sex` | el código es identidad visible y única; un formato inventado sería un requisito nuevo |
| si la importación puebla el lote | `GA-REM-005 E.3` (entradas: `bird_reception`, `birth_registration`) · `PROCESS-01` §4 (`bird_reception` con OC, `BR-18`) · `PROGENITORAS_COVERAGE` («documental») | **conflicto potencial**: si el lote nace de la importación con sus recibidas, el paso 4 duplicaría la entrada (o habría que suprimirlo y mover `BR-18`) | cambia el modelo de saldo certificado (`R-130`) |
| convivencia con la creación manual y con «la importación exige lote» | `docs/15 :237` (`POST /lots` ✅), `PROCESS-01` certificado con lote previo | **silencio**: ¿se mantiene la vía manual?; ¿la importación pasa a admitir `lot_id` nulo? | invierte el contrato vigente de la ruta |

→ `AOD-25` (dossier en `AUDIT_OWNER_DECISIONS_REQUIRED.md`). `R-153` queda **OPEN · OWNER_DECISION_REQUIRED**; sin código. Cuando se decida, su
implementación reutiliza `create_lot` (cadena de unidad `AC-L02/L14`, línea genética, auditoría) y el plan de `R-152` (fuente de granja/galpón, línea,
fechas y cantidades): por eso la dependencia es `HARD`.

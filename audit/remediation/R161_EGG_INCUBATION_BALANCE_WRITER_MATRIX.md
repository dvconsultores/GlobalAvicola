# `R-161` · MATRIZ DE ESCRITORES Y GRAFO DE EFECTOS DE LOS SALDOS DE HUEVOS E INCUBACIÓN

**WAVE B · tranche 9 · pre-flight** · 2026-09-10 · `R-161` (P2, `DATA_INTEGRITY`): «los saldos de huevos e incubación (`BR-02`, `BR-03`) se leen
sin bloqueo de fila: la misma carrera de decrementos concurrentes que `R-130` cierra para las aves» · leído en `validators.py:91-145, 163-230`,
`service.py:871-880`, `transaction.py` (`RutaTransaccional`: una transacción por petición, `READ COMMITTED`).

## 1. Superficies expuestas — enumeradas, no abstraídas

| Saldo / hecho | Proceso | Recurso autoritativo | Clave | Lee | Escribe (decremento) | Ruta | Tipo de evento | Estado origen | Cantidad | Signo | Bloqueo actual | ¿Bloqueo antes de leer? | ¿Compartido por todos los escritores? | Transacción | ¿Puede excederse concurrentemente? | Análogo `R-130` | `R-170`/`B13` | AC | Test |
|---|---|---|---|---|---|---|---|---|---|:--:|---|:--:|:--:|---|:--:|---|---|---|---|
| **huevos fértiles disponibles en granja** (`BR-02`) = Σ `egg_movements` de `egg_collection` − Σ de `egg_dispatch` (≠ `CANCELLED`) | `P-04` producción de huevo | **lote** (`lots.id`) — ambos sumandos se agrupan por `lot_id` | `lot_id` | `get_egg_balance` (`validators.py:91-114`) | `validate_egg_dispatch` (`:206-216`) ← `_apply_business_rules` (`service.py:871-876`, solo si `total > 0`) | `POST /operations` | `egg_dispatch` | `REGISTERED` (el efecto nace en el alta: los saldos cuentan todo lo no cancelado) | Σ `egg_movements.quantity` | − | **ninguno** | **no** | — (un solo decremento) | por petición | **sí**: dos despachos leen 100 y ambos confirman | `validate_bird_decrement` (bloquea la fila del lote) | no (aves) | `AC-R161-01…05, 07, 10…15` | `test_egg_incubation_concurrency.py` |
| **huevos disponibles en incubadora** (`BR-03`) = Σ `egg_movements` de `egg_reception_hatchery` − Σ `hatchery_params.quantity_loaded` de `incubation_load` | `P-05` incubación | **lote** (`lots.id`) | `lot_id` | `get_hatchery_egg_balance` (`:117-141`) | `validate_incubation_load` (`:219-229`) ← `service.py:877-882`, solo si `total > 0` | `POST /operations` | `incubation_load` | `REGISTERED` | Σ `quantity_loaded` | − | **ninguno** | **no** | — | por petición | **sí** | `validate_chick_dispatch` (bloquea) | no | `AC-R161-02…06, 07` | ídem |
| incrementos | `egg_collection` · `egg_reception_hatchery` | lote | `lot_id` | — | alta sin validación (entradas) | ídem | — | `REGISTERED` | Σ | + | — | — | — | — | no (solo suben) | recepción de aves | — | control | — |
| cancelación de un evento con efecto en saldo | `P-07` | evento | `event_id` | `cancel_event` (`service.py:1133-1150`): sin lectura de saldo | `CANCELLED` | `POST /operations/{id}/cancel` | cualquiera | ≠ `NO_CANCELABLES` | — | ± | ninguno | — | — | por petición | cancelar una **entrada** tras salidas deja el saldo negativo (todas las familias) | `R-130 AC07` cubrió cancelar una salida | — | **`R-173`** (registrado, fuera) | — |
| edición que cambia `lot_id` de un evento con efecto en saldo | `P-07` | evento | — | `update_event` (`:1071-1078`): valida lote activo y fecha, **no** saldos | mueve el efecto entre lotes | `PUT /operations/{id}` | cualquiera | `EDITABLES` | — | ± | ninguno | — | — | por petición | sí, en todas las familias | no cubierto por `R-130` | — | **`R-173`** | — |
| corrección de cantidades | `P-07` | — | — | `campos_corregibles` = campos de `OperationalEventUpdate`: **sin submovimientos** | — | `POST /corrections` | — | — | — | — | — | — | — | — | **N/A**: `egg_movements` y `hatchery_params` no son corregibles | — | — | N/A | — |
| aprobación / revisión | `P-07` | — | — | no lee saldos; el efecto ya existe desde el alta | — | `approvals/*` | — | — | — | — | — | — | — | — | no (no muta cantidades) | — | `R-166` (carrera approve/reject) es otro invariante | N/A | — |
| reverso (contrapartida) | `GA-REM-041` | — | — | `get_egg_balance`/`get_hatchery_egg_balance` **no** usan `_suma_neta` (no conocen `REVERSED`) | — | `POST /reversals` | huevos/incubación | — | — | — | — | — | — | — | — | huevos `BLOCKED_BY_R-161` (`OD-19 §18`) | — | fuera; nota §5 | — |

## 2. Grafo de efectos (nombres reales)

```
egg_collection (+, todas las egg_type)  ──►  BR-02 saldo de huevos del lote  ──►  egg_dispatch (−, validado sin bloqueo)  ──►  EggBatch (linaje, informativo)
                                                                                                    │
egg_reception_hatchery (+)  ──►  BR-03 saldo de huevos en incubadora  ──►  incubation_load (−, validado sin bloqueo)
ovoscopy · transfer_to_hatcher (quantity_transferred)  ──►  informativos (no restan de BR-03; sin fuente que lo exija)
birth_registration (+ nacidos, BR-21)  ──►  viables (R-130, bloqueado)  ──►  chick_dispatch (−, bloqueado) · mortality_recording (−) · cull_recording (−)
chicks_healthy / chicks_weak  ──►  atributos (B13), sin efecto
```

Qué resta: `egg_dispatch`, `incubation_load` (huevos) · `chick_dispatch`, `mortality_recording`, `cull_recording` (aves). Qué suma: `egg_collection`,
`egg_reception_hatchery`, `birth_registration`, `bird_reception`. Qué describe: `egg_type`, `chicks_*`, `dead_on_arrival`. Qué se deriva: los
cuatro saldos (nunca se persisten). Qué se corrige: nada de lo anterior por `/corrections` (submovimientos); `PUT` no toca cantidades de
submovimientos. Qué puede correr: los decrementos sin bloqueo (`R-161`), y las mutaciones posteriores al alta (`R-173`).

## 3. Fila que serializa el saldo

Los dos saldos se agrupan por `lot_id`; **todos** los escritores de cada saldo (un decremento cada uno) comparten el lote. La fila autoritativa
es `lots.id`, la misma que `R-130` bloquea con `bloquear_saldo_del_lote` (`SELECT … FOR UPDATE`, vive lo que la transacción de la petición,
sin cadena de bloqueos). Un bloqueo sobre el evento hijo o sobre `EggBatch` sería inútil: no lo comparten los escritores. Bloqueo por recurso:
dos lotes distintos no se serializan entre sí; dos empresas tampoco.

## 4. Criterios de corrección del bloqueo (`§12` del encargo) aplicados

| Criterio | `R-161` |
|---|---|
| A. todos los escritores del mismo saldo convergen en el mismo objetivo | sí: un decremento por saldo, ambos sobre `lots.id` |
| B. el bloqueo ocurre antes de leer el saldo | `bloquear_saldo_del_lote` **antes** de `get_egg_balance` / `get_hatchery_egg_balance` |
| C. el saldo se recalcula tras adquirir el bloqueo | sí (lectura de eventos confirmados tras el bloqueo) |
| D. la validación usa ese saldo fresco | sí |
| E. la mutación ocurre en la misma transacción | sí (`RutaTransaccional`: alta y validación en la misma sesión) |
| F. el commit libera el bloqueo | sí |
| G. el rollback no deja efecto parcial | sí (`BusinessRuleViolation` antes de `db.add`) |

## 5. Observaciones registradas (no son `R-161`; no se corrigen aquí)

| ID | Sev. | Hallazgo |
|---|:--:|---|
| **`R-172`** | P2 | `get_egg_balance` suma **todas** las `egg_type` de la recolección (sucios, rotos, infértiles, descartados) como huevos disponibles para despacho; `BR-02` dice «fértiles disponibles». Semántica, no concurrencia |
| **`R-173`** | P2 | mutaciones posteriores al alta con efecto en saldo sin revalidación ni bloqueo: `PUT` que cambia `lot_id` (mueve el efecto entre lotes) y `cancel` de una **entrada** (recolección, recepción, nacimiento, recepción de aves) tras salidas; afecta a las cuatro familias de saldo (`R-130` cubrió cancelar una salida) |
| **`R-174`** | P3 | `chick_dispatch` con cantidad 0 se acepta (`service.py:883`: `if total_qty > 0` salta `validate_chick_dispatch`); residuo de la clase `R-130 AC04` |
| nota | — | los saldos de huevos no usan `_suma_neta`: correcto mientras los huevos no sean reversibles (`OD-19 §18`); habilitar su reverso exigirá una enmienda de `GA-REM-041` que los pase a `_suma_neta` — **no** se hace aquí |

## 6. Gate de composición

```
R-161 gobernado por completo ........ SÍ (GA-REM-005-B fija el patrón; BR-02/BR-03 fijan los invariantes; spec.md §5; sin decisión)
R-161 decisión del propietario ...... NINGUNA
R-161 escritores afectados .......... egg_dispatch (BR-02) · incubation_load (BR-03) — un decremento por saldo; corrección N/A; aprobación N/A
R-171 gobernado por completo ........ SÍ (UI_ONLY; ver R171_HATCHERY_MORTALITY_DISCARD_TRUTH_MATRIX.md)
R-171 decisión del propietario ...... NINGUNA
R-171 misma raíz que R-161 .......... NO (recurso: pollitos vs huevos · saldo: viables vs BR-02/BR-03 · spec: GA-REM-021 vs GA-REM-005 · primitiva ausente: catálogo vs bloqueo)
MODO ................................ R161_ONLY (CASO B: R-161 se cierra; R-171 queda OPEN → siguiente, listo)
```

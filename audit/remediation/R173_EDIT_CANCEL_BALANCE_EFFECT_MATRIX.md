# `R-173` · Matriz de efecto de edición / cancelación sobre los saldos (`R173_EDIT_CANCEL_BALANCE_EFFECT_MATRIX`)

**WAVE B · tranche 10 · pre-flight** · 2026-09-10 · hallazgo `R-173` (registrado P2 en el pre-flight del tranche 9; **reevaluado P1**, §14) ·
spec gobernante: `GA-REM-005` (enmienda B: invariante del saldo; enmienda D: saldos de huevos e incubación) + `GA-REM-040-G` (`AC-W09`, destino de
una edición) + `GA-REM-006-A` (mapa de transiciones) · **sin decisión del propietario** (§7, §15).

## 1. Hallazgo exacto

> `R-173` · P2 · «mutaciones posteriores al alta con efecto en saldo sin revalidación ni bloqueo: `PUT` que cambia `lot_id` mueve el efecto entre
> lotes; `cancel` de una entrada (recolección, recepción, nacimiento, recepción de aves) tras salidas deja el saldo negativo; las cuatro familias de
> saldo» · `service.py:1071-1078, 1133-1150` · `REMEDIATION_BACKLOG.md:1079`.

Ampliación del pre-flight (leída, no supuesta): el mismo campo `lot_id` es **corregible** por `POST /corrections` (`campos_corregibles()` =
`OperationalEventUpdate.model_fields − NO_CORREGIBLES_POR_IDENTIDAD`, `corrections/service.py:159-169`) y esa ruta **no verifica el destino**:
ni empresa, ni unidad, ni lote activo, ni fecha, ni saldo (`corrections/service.py:19-60`: `get_event` → `exigir_unidad_operativa(event=event)`
sobre el evento **origen** → `_convertir` → `setattr`). Lo mismo para `farm_id`, `house_id` y `destination_farm_id` (sin `verificar_ubicacion`).

## 2. Fuentes leídas (método `REQUIREMENT_CONFLICT_RESOLUTION.md §1`)

| Nivel | Fuente | Qué dice |
|---|---|---|
| 3 | `docs/12 §3` (fila Operador) | «Crear, **Editar (antes de enviar)**, Enviar a revisión» — la edición del registro propio, antes de salir de sus manos, es capacidad reconocida |
| 3 | `docs/12 §2` · `spec.md §4.10` | `Borrador → Anulado: Cancelar` · `Registrado → Anulado: Cancelar (auditado)` |
| 3 | `docs/13 §2` (tabla «Qué se audita») | «**Edición de registro**: usuario, fecha/hora, **campo modificado, valor anterior, valor nuevo**» |
| 4 | `GA-REM-005-B §B.2` | invariante: para todo decremento `D`, `cantidad(D) > 0 ∧ cantidad(D) ≤ SALDO antes de D ⇒ SALDO después ≥ 0`, bajo el bloqueo de la fila del lote; **premisa** «`cancel` retira el evento del saldo (`status ≠ CANCELLED`) y **no puede dejarlo negativo (solo lo aumenta)**» — cierta para las salidas, **falsa para las entradas** (§8) |
| 4 | `GA-REM-005-D §D.1.4` | «tras cualquier conjunto confirmado, `saldo ≥ 0`. Sin tolerancia» (huevos e incubación) |
| 4 | `GA-REM-040-G §G.4` · `AC-W09` | «el destino de una edición se verifica como el de un alta» — hoy: empresa, unidad, lote activo, fecha (`update_event:1071-1088`); **no** las reglas de saldo |
| 4 | `GA-REM-006-A §A.2` | `cancel_event ∉ {APPROVED, CONSOLIDATED, SENT_TO_SAP, SAP_CONFIRMED, SAP_ERROR, CANCELLED}` (+ `REVERSED`, `GA-REM-041`) · `update_event ∈ {DRAFT, REGISTERED, RETURNED, REJECTED}` · «el saldo cuenta la misma fila en todo el ciclo salvo `CANCELLED`» |
| 4 | `GA-REM-041 §3.2` · `OD-19 §3-5` | el reverso es **otra cosa**: contrapartida aprobada, ambos `REVERSED`, `_suma_neta` resta la contrapartida efectiva; la contrapartida no se edita ni corrige (`AC-RV06`) |
| 5 | `validators.py:21-160` | los cuatro saldos son **agregados dinámicos** sobre filas filtradas por `OperationalEvent.lot_id` y `status ≠ CANCELLED` (§8) |
| 5 | `service.py:1051-1112` (`update_event`) · `:1133-1150` (`cancel_event`) · `corrections/service.py:19-60` | comportamiento actual (§3) |

Ninguna fuente de nivel 1-4 **prohíbe** cambiar el lote antes del envío (modelo A) ni **condiciona** la cancelación a algo distinto del estado; las de nivel
4 fijan el invariante del saldo y el principio «destino = alta». Eso gobierna (§7).

## 3. Superficies (una fila por tipo de evento con efecto en saldo)

Leyenda: `PUT` = `PUT /operations/{id}` (`operations:update`, estados `EDITABLES`) · `CORR` = `POST /corrections` (`corrections:correct`, estados
`REGISTERED…REJECTED`) · `CANCEL` = `POST /operations/{id}/cancel` (`operations:create`, estados `∉ NO_CANCELABLES`). «Efectivo de inmediato» = el
saldo cuenta la fila desde el alta, en cualquier estado `≠ CANCELLED` (`DRAFT` incluido: residual `R-154`, no se toca).

| Tipo de evento | Proceso | ¿Edita cantidad? | ¿Edita lote? | ¿Cancela? | ¿Efectivo de inmediato? | Saldo afectado (signo) | Saldo viejo (edición de lote) | Saldo nuevo | Revalidación actual | Bloqueo actual | Auditoría actual | `R-130` | `R-161` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `bird_reception` | recepción (cría, engorde) | **no** (`bird_movements` solo en el alta: `422 extra=forbid`; no corregible: `400`) | sí (`PUT`, `CORR`) | sí | sí | aves **+** (`BR-01`) | origen **baja** la cantidad recibida → puede quedar **< 0** si ya hubo salidas | destino sube | `PUT`: empresa/unidad/activo/fecha · `CORR`: **ninguna** | ninguno | `PUT`: `UPDATED` «Evento actualizado» sin valores · `CORR`: campo/valor viejo/nuevo · `CANCEL`: `CANCELLED` | entrada de `E.3` | — |
| `birth_registration` | incubadora | no | sí | sí | sí | aves **+** y viables **+** (`BR-01`/`BR-04`) | origen baja → **< 0** si hubo despachos/mortalidad | destino sube | ídem | ninguno | ídem | entrada | — |
| `mortality_recording` | diario | no | sí | sí | sí | aves **−** y viables **−** | origen **sube** (nunca negativo) | destino **baja** → **< 0** si el destino no tiene saldo | ídem (sin `BR-01` en destino) | ninguno | ídem | salida (`validate_mortality`) | — |
| `cull_recording` | diario | no | sí | sí | sí | aves **−** y viables **−** | sube | baja → **< 0** | ídem | ninguno | ídem | salida (`validate_bird_decrement`) | — |
| `bird_exit` | salida a planta / cierre | no | sí | sí | sí | aves **−** | sube | baja → **< 0** | ídem | ninguno | ídem | salida | — |
| `chick_dispatch` | incubadora → granja | no | sí | sí | sí | aves **−** y viables **−** | sube | baja → **< 0** | ídem (sin `BR-04` en destino) | ninguno | ídem | salida (`validate_chick_dispatch`; cantidad 0: `R-174`) | — |
| `egg_collection` | producción | no (`egg_movements` solo en el alta) | sí | sí | sí | huevos **+** (`BR-02`) | origen baja → **< 0** si hubo despachos | destino sube | ídem | ninguno | ídem | — | entrada de `D.1` |
| `egg_dispatch` | producción → incubadora | no | sí | sí | sí | huevos **−** | sube | baja → **< 0** | ídem (sin `BR-02` en destino) | ninguno | ídem | — | salida bloqueada en el alta |
| `egg_reception_hatchery` | incubadora | no | sí | sí | sí | incubadora **+** (`BR-03`) | origen baja → **< 0** si hubo cargas | destino sube | ídem | ninguno | ídem | — | entrada |
| `incubation_load` | incubadora | no (`hatchery_params` solo en el alta) | sí | sí | sí | incubadora **−** | sube | baja → **< 0** | ídem (sin `BR-03` en destino) | ninguno | ídem | — | salida bloqueada en el alta |
| `bird_transfer` · `bird_distribution` | neutros (`RR-02`) | no | sí | sí | — | **ninguno** | — | — | ídem | — | ídem | neutros | — |
| resto (alimento, agua, peso, vacuna, medicación, inspecciones, ovoscopía, transferencia a nacedora, clasificaciones, cierre, importación) | — | n/a | sí (los que llevan lote) | sí | — | **ninguno** | — | — | ídem | — | ídem | — | — |

**Otras superficies observadas, sin efecto en los cuatro saldos** (se registran, no se corrigen aquí — §17): `sap_document_ref` (acumulado de la OC,
`BR-18`, agregado por referencia: la edición lo mueve de una OC a otra sin `validate_oc_limit`, aunque la función ya tiene `exclude_event_id` para
ese caso), `house_id` (capacidad estática `BR-17`), `event_date` sola (`validate_event_date`/`validate_period_open` solo corren si cambia `lot_id`).
Efectos **materializados** fuera de los saldos: `egg_batches`/`chick_batches` (linaje, `spec.md §233`) se crean al casar despacho y recepción y **no** se
neutralizan al cancelar ni al mover de lote; `operational_alerts` (peso) y `notifications` tampoco. No son saldos: fuera de `R-173`.

## 4. Matriz de reasignación de efecto (por familia de saldo)

| Familia | Recurso original | Lote original | Efecto original | Signo | Campo editable | Recurso nuevo | Lote nuevo | Efecto nuevo | ¿Revertir el viejo? | ¿Validar el nuevo? | ¿Bloquear viejo? | ¿Bloquear nuevo? | Orden | Efecto de cancelar | ¿Cancelación ya aplicada? | ¿Idempotente? | Estado | Inquilino | Unidad | RBAC | Auditoría | Fuente | ¿Decisión? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| aves · **entrada** (`bird_reception`, `birth_registration`) | `lots.id` = A | A | `+n` en `SALDO(A)` | + | `lot_id` (`PUT`, `CORR`) | `lots.id` = B | B | `+n` en `SALDO(B)` | **automático** (agregado dinámico: la fila deja de contar en A) — pero **A debe quedar ≥ 0**: `SALDO(A) − n ≥ 0` | destino solo sube: **sin regla de saldo**; sí empresa/unidad/activo/fecha (`AC-W09`) | **sí** (se lee `SALDO(A)`) | sí (simetría de orden; la fila destino cambia de saldo) | `lots.id` ascendente, sentencias sucesivas | `−n` en `SALDO(A)` → **puede quedar < 0** si hubo salidas | no (hoy nada la aplica: solo el estado) | segunda cancelación: `400` (`CANCELLED ∈ NO_CANCELABLES`) sin efecto | `EDITABLES` / `∉ NO_CANCELABLES` | `validate_lot_active(company)` (`PUT`); **ausente en `CORR`** | `exigir_unidad_operativa(lot_id=destino)` (`PUT`); **ausente en `CORR`** | `operations:update` · `corrections:correct` · `operations:create` (cancel) | `docs/13`: valor anterior/nuevo — hoy solo «Evento actualizado» | `GA-REM-005-B B.2`/`E.3` · `D.1.4` · `AC-W09` · `docs/12 §3` · `docs/13` | **no** |
| aves · **salida** (`mortality_recording`, `cull_recording`, `bird_exit`, `chick_dispatch`) | A | A | `−n` en `SALDO(A)` (y en viables) | − | `lot_id` | B | B | `−n` en `SALDO(B)` | automático (A sube) | **sí**: `n ≤ SALDO(B)` bajo bloqueo (`BR-01`; `chick_dispatch`: `n ≤ viables(B)`, `BR-04`) — «como si se hubiera creado en B» | sí (orden) | **sí** (se lee `SALDO(B)`) | ascendente | `+n` en A (restaura; `AC-R130-07`) | — | ídem | ídem | ídem | ídem | ídem | ídem | `B.2` (`D` es un decremento del lote donde está) · `AC-W09` | no |
| huevos (`BR-02`) · entrada `egg_collection` / salida `egg_dispatch` | A | A | `±n` (n = Σ filas **fértiles** tras `R-172`) | ± | `lot_id` | B | B | `±n` en B | automático · entrada: `huevos(A) − n ≥ 0` | salida: `n ≤ huevos(B)` (`BR-02`) | sí | sí | ascendente | entrada: `−n` → **< 0** posible · salida: `+n` | — | ídem | ídem | ídem | ídem | ídem | ídem | `D.1` · `D.1.4` | no |
| incubadora (`BR-03`) · entrada `egg_reception_hatchery` / salida `incubation_load` | A | A | `±n` (n = Σ fértiles recibidos / Σ `quantity_loaded`) | ± | `lot_id` | B | B | `±n` | automático · entrada: `incubadora(A) − n ≥ 0` | salida: `n ≤ incubadora(B)` (`BR-03`) | sí | sí | ascendente | entrada: `−n` → **< 0** posible · salida: `+n` | — | ídem | ídem | ídem | ídem | ídem | ídem | `D.1` | no |
| viables (`BR-04`) | — | — | derivado de aves de incubadora: nacidos − (despachos + mortalidad + descartes) | — | — | — | — | — | cubierto por las filas de entrada/salida de aves (la cancelación de un nacimiento y el movimiento de un `chick_dispatch` se validan con `viables`) | | | | | | | | | | | | | `B.2` | no |

## 5. Distinción crítica (`§12` del prompt)

| Acto | Qué es aquí | Estado de la cuestión |
|---|---|---|
| A · edición ordinaria de campo (`observations`, `cause_id`, `vaccine_*`, …) | sin efecto en saldo | fuera; sin cambio |
| B · corrección de cantidad | **no existe**: `bird_movements`/`egg_movements`/`hatchery_params` solo se escriben en el alta (`OperationalEventUpdate` `extra="forbid"` → `422`; `campos_corregibles` no los incluye → `400`). `GA-REM-005-B B.2`: «las cantidades son inmutables tras crear» | control (`AC-R173-01`), no rojo |
| C · reasignación de lote (`lot_id` por `PUT` o `CORR`) | mueve el efecto entero, retroactivamente, de A a B (agregado dinámico) | **defecto**: sin regla de saldo en el destino, sin invariante en el origen, sin bloqueo, sin valores en la auditoría; en `CORR` además sin empresa/unidad/activo/fecha |
| D · cancelación | exclusión dinámica (`status ≠ CANCELLED`): neutraliza sola, sin compensación | **defecto** solo para las **entradas**: puede dejar el saldo `< 0`; sin bloqueo frente a salidas concurrentes |
| E · reverso (`OD-19`) | contrapartida aprobada, ambos `REVERSED`, para lo **aprobado** | **no se toca**; `CANCELLED ≠ REVERSED`; el original `REVERSED` no se cancela ni edita (`NO_CANCELABLES`, `es_contrapartida`) |

`CORRECCIÓN ≠ REASIGNACIÓN` (una corrección de `lot_id` **es** una reasignación y debe pasar por la misma guarda) · `CANCELACIÓN ≠ REVERSO` ·
`EDICIÓN ≠ COMPENSACIÓN` (no se crea ninguna fila de compensación: el modelo es dinámico).

## 6. Pre-flight del cambio de lote (`§13`): comportamiento actual, leído

| Pregunta | Respuesta (código actual) |
|---|---|
| ¿El efecto viejo permanece en A? | **No.** Los cuatro saldos filtran por `OperationalEvent.lot_id` en la consulta; tras el `setattr` la fila deja de contar en A |
| ¿El efecto nuevo aparece en B? | **Sí, al instante y hacia atrás** (toda la historia de la fila pasa a B) |
| ¿Solo cambia la FK? | FK + `version += 1` + auditoría `UPDATED` «Evento actualizado» (sin lote anterior ni nuevo) |
| ¿La consulta de saldo sigue el `lot_id` actual? | **Sí** → la reasignación **es** la neutralización del efecto viejo y la aplicación del nuevo, sin compensación |
| ¿La auditoría conserva el lote viejo? | **No** (`previous_values`/`new_values` existen en `audit_logs` y `update_event` no los rellena; `docs/13 §2` los exige) |
| ¿B tiene saldo/capacidad? | **No se comprueba** (ni `BR-01/02/03/04` en B ni `≥ 0` en A) |
| ¿Misma empresa? | `PUT`: sí (`validate_lot_active(company)`, `AC-W09`) · `CORR`: **no se comprueba** |
| ¿Misma unidad / unidad encendida / concesión? | `PUT`: sí (`exigir_unidad_operativa(lot_id=destino)`) · `CORR`: **no** |
| ¿A→B entre unidades? | `PUT`: solo si el actor alcanza la unidad de B (lo permite el contrato de `AC-W09`; el tipo de cadena lo revalidan `RR-11`/`BR-20`/`BR-21` cuando aplica) · `CORR`: sin control |
| ¿A→B entre empresas? | `PUT`: `400 BR-07` (`AC-W09`) · `CORR`: **posible** (`AC-R173-11`, rojo) — el evento queda con `company_id = A` y `lot_id` de B; los saldos de B lo cuentan |

## 7. Modelo semántico (`§14`): determinado por las fuentes, no elegido

- **Modelo A** (prohibir la reasignación tras el alta) contradice `docs/12 §3` (editar antes de enviar), `R-34` (`OperationalEventUpdate` admite los
  campos del alta, `lot_id` incluido) y `GA-REM-040-G AC-W09` (que ya regula el **destino** de esa edición). No es lo que dice el repositorio.
- **Modelo C** (solo antes de que el efecto se materialice) es vacío: el efecto se materializa en el alta (agregado dinámico desde `REGISTERED`, y
  desde `DRAFT`).
- **Modelo D** (tipos distintos): los tipos solo difieren en **qué saldo** alimentan y con qué signo (§4); la regla es una.
- **Modelo B** es el que las fuentes componen: la reasignación está permitida en `EDITABLES` (nivel 3/4), el efecto viejo se neutraliza por
  construcción (nivel 5, agregado dinámico), el efecto nuevo se valida **como un alta en B** (`AC-W09` + invariante `B.2`: un decremento movido a B
  es un decremento de B) y el origen conserva el invariante (`D.1.4`: tras cualquier conjunto confirmado, `saldo ≥ 0`). **Atómico** en la
  transacción de la petición; **serializado** por el bloqueo de las dos filas de lote.
- ¿Debe moverse la verdad histórica? Antes del envío el registro es del operador (`docs/12 §3`); tras la aprobación no hay edición (`R-135`/`R-143`),
  solo reverso. La auditoría conserva el valor anterior y el nuevo (`docs/13 §2`). Nada queda sin rastro → no hay decisión de negocio pendiente.

**No hay decisión del propietario que tomar**: ninguna fuente de nivel ≥ 3 calla sobre lo que aquí se corrige (invariante, destino como alta, auditoría
con valores); lo único que este pre-flight añade es aplicar esas reglas a dos caminos (`cancel`, `lot_id`) que las esquivaban.

## 8. Cancelación (`§15`/`§16`): clasificación por familia

| Familia | Clase | ¿Excluye `CANCELLED`? | ¿Neutraliza sola? | ¿Puede dejar `< 0`? | Efecto materializado aparte |
|---|---|---|---|---|---|
| aves (`get_current_bird_balance`, `_suma_neta`) | **DYNAMIC_AGGREGATE** | sí (`status.not_in([CANCELLED])`; contrapartidas solo si `REVERSED`) | sí | **sí**, al cancelar una **entrada** con salidas posteriores | ninguno en el saldo (`opening_balances` es apertura, no evento) |
| viables (`get_viable_chick_balance`) | DYNAMIC_AGGREGATE | sí | sí | sí (cancelar un nacimiento con despachos) | ninguno |
| huevos (`get_egg_balance`) | DYNAMIC_AGGREGATE | sí | sí | sí (cancelar una recolección con despachos) | `egg_batches` (linaje, no saldo; §17) |
| incubadora (`get_hatchery_egg_balance`) | DYNAMIC_AGGREGATE | sí | sí | sí (cancelar una recepción con cargas) | `egg_batches` |

La premisa de `GA-REM-005-B B.2` («`cancel` … no puede dejarlo negativo (solo lo aumenta)») describe solo las salidas. Para las entradas la
cancelación es un **decremento del saldo** y el invariante `B.2`/`D.1.4` le aplica igual: `SALDO(lote) − n ≥ 0`, leído bajo el bloqueo del lote.
Consecuencia gobernada: la cancelación de una entrada que dejaría el saldo negativo se **deniega** (`400`, misma regla de la familia: `BR-01`,
`BR-02`, `BR-03`; nacimiento con despachos: `BR-04`), el evento no cambia, sin auditoría de cancelación. No se cancela nada en cascada ni se crea
compensación (sería semántica nueva, prohibida).

## 9. Bloqueos (`§17`)

| Acto | Recursos autoritativos | Bloqueo | Orden |
|---|---|---|---|
| `cancel` de entrada | `lots.id` del evento | `bloquear_saldo_del_lote(lot_id)` antes de releer el evento y el saldo | uno solo |
| `cancel` de salida | ídem | mismo camino (uniforme; el saldo solo sube) | uno solo |
| `PUT`/`CORR` con `lot_id` A→B (evento con efecto) | `lots.id` A y B | `bloquear_saldo_del_lote` sobre **min(A, B)** y luego **max(A, B)** — sentencias sucesivas, orden por clave primaria ascendente, la misma convención para todos los escritores → sin interbloqueo A→B/B→A | dos, ascendente |
| `PUT`/`CORR` sin `lot_id` o evento sin efecto | — | ninguno (sin cambio) | — |

Los validadores de destino (`validate_mortality`, `validate_bird_decrement`, `validate_egg_dispatch`, `validate_incubation_load`,
`validate_chick_dispatch`) vuelven a bloquear la fila de B dentro de la misma transacción: `FOR UPDATE` es reentrante para la propia transacción.
Sin mutex de proceso; alcance por recurso (dos pares de lotes distintos no se serializan entre sí).

## 10. Revalidación del destino (`§18`) y del origen — derivada por el servidor

El cliente no envía cantidades, lote viejo ni saldo: el servidor lee la fila persistida y deriva `n`:

| Familia | `n` | Regla en el destino (salidas) | Invariante en el origen (entradas) |
|---|---|---|---|
| aves | `Σ bird_movements.quantity` | `validate_mortality` / `validate_bird_decrement(etiqueta)` / `validate_chick_dispatch` sobre B (mismo código del alta; `n > 0` ya persistido) | `get_current_bird_balance(A) − n ≥ 0`, y para nacimientos también `get_viable_chick_balance(A) − n ≥ 0` (`BR-04`) |
| huevos | `Σ egg_movements.quantity` que **cuentan como disponibles** (`R-172`: `fertile`) | `validate_egg_dispatch(B, n)` | `get_egg_balance(A) − n ≥ 0` |
| incubadora | `Σ hatchery_params.quantity_loaded` (salida) · `Σ egg_movements` fértiles (entrada) | `validate_incubation_load(B, n)` | `get_hatchery_egg_balance(A) − n ≥ 0` |

Todo antes de `setattr`; si falla, el evento queda como estaba (transacción de la petición) y no hay auditoría de éxito.

## 11. Propiedad y cadena de seguridad en el destino (`§19`)

| Capa | `PUT` (hoy) | `CORR` (hoy) | Exigido |
|---|---|---|---|
| empresa | `validate_lot_active(db, lote, company_id)` → `400 BR-07` | **ausente** | ambos |
| lote activo | ídem | ausente | ambos |
| fecha vs lote (`BR-19`/`R-30`) | `validate_event_date` | ausente | ambos |
| unidad encendida + concesión (`OD-14`/`OD-16`, `R-160`) | `exigir_unidad_operativa(lot_id=destino)` → `403`/`400 BR-07` | ausente (solo sobre el origen) | ambos |
| ubicación (`farm_id`, `house_id`, `destination_farm_id`) | `verificar_ubicacion` | ausente | ambos |
| RBAC | `operations:update` | `corrections:correct` | sin cambio (ningún permiso nuevo) |
| autoridad global | sin empresa → `400 BR-07` (`AC-W12`) · situada en A no mueve a B (`AC-W09`) | ídem por `get_event`; destino sin control | igual que `PUT` |
| Administrador de Accesos / Contraloría | `403` (RBAC) | `403` | sin cambio |

No se hereda autorización del recurso original: la guarda se evalúa sobre el destino.

## 12. Cancelación exactamente una vez (`§20`)

`cancel_event`: `get_event` → `exigir_unidad_operativa` → **bloquear la fila del lote** → **releer el evento** (`refresh`) → estado `∉ NO_CANCELABLES`
(si otro `cancel` ganó, `400`) → invariante de la familia (entradas) → `CANCELLED` → auditoría. Segunda cancelación: `400`, sin efecto. Concurrentes:
serializadas por el bloqueo; a lo sumo una transición efectiva. Sin ampliar la cancelación a tipos cuyo contrato diga otra cosa (`REVERSED`, ciclo SAP,
aprobados: `GA-REM-006-A`).

## 13. Fronteras con `R-140`, `R-154`, `R-136`, `R-130`, `R-161` (`§21`)

| Ítem | Residual / contrato | Aquí |
|---|---|---|
| `R-140` PARTIAL | motivo obligatorio del `cancel` (`AOD-18`, cliente sin cuerpo) y permiso «solo administrador» | **no se toca**: el `cancel` sigue sin motivo y con `operations:create`; solo se añade la guarda de saldo |
| `R-154` PARTIAL | `DRAFT` en el mapa; `version`; dos «cierres» (`AOD-08`) | no se toca: `DRAFT` sigue editable y cancelable; `version` avanza como hoy |
| `R-136` / `OD-19` | reverso de aprobados; contrapartida; huevos no reversibles (`§18`) | no se toca; `cancel` de una contrapartida pendiente no tiene efecto en saldo (`_suma_neta` solo resta las `REVERSED`) — se documenta, no se cambia |
| `R-130` | `validate_bird_decrement` + bloqueo en el alta; `AC-R130-07` (cancelar un descarte devuelve el saldo) | intacto; se reutiliza (sin validador nuevo) |
| `R-161` | bloqueo antes de leer `BR-02`/`BR-03` en el alta | intacto; misma primitiva, mismo orden (una fila, o dos ascendentes) |
| `R-135`/`R-143` | aprobados no se editan; segregación | intacto (`EDITABLES` no cambia) |

## 14. Severidad (`§25`), normalizada

El comportamiento actual **puede**: dejar saldo negativo (cancelar una entrada tras salidas), mover un efecto productivo sin validación (`PUT`),
**mover un evento a un lote de otra empresa o de una unidad apagada** por `POST /corrections` (bypass de inquilino/unidad), y perder frente a una
salida concurrente (sin bloqueo). Política oficial: integridad de saldo + aislamiento de inquilino → **`P1`** (`DATA_INTEGRITY` + `TENANT`). El P2
del registro inicial no conocía el camino de correcciones.

## 15. Clasificación y puerta

```
R-173 ............ ACTIVE · GOBERNADO · SIN DECISIÓN DEL PROPIETARIO · P1
modelo ........... B (reasignación permitida en EDITABLES; destino validado como alta; origen ≥ 0; cancelación de entradas ≥ 0; dinámico, atómico, bloqueado)
spec ............. GA-REM-005 enmienda E (corrige la premisa de B.2; AC-R173-01…18) — sin GA-REM nueva
migración ........ ninguna (cabeza x4y5z6a7b8c9)
```

## 16. AC → prueba (resumen; contrato completo en `GA-REM-005-E`)

| AC | Qué | Prueba (`tests/test_edit_cancel_balance.py`, prefijo `MUTA-`) |
|---|---|---|
| `AC-R173-01` | control: la cantidad no se edita ni corrige (`422` / `400`), saldo intacto | `test_r173_01_…` (control, verde antes) |
| `AC-R173-02` | mover una salida a un lote sin saldo → `400 BR-01` (aves), `BR-02`, `BR-03`, `BR-04`; evento y saldos intactos | `test_r173_02_…` (4 familias) |
| `AC-R173-03` | mover una salida a un lote con saldo → `200`; verdad final exacta en A y B; auditoría con lote anterior y nuevo | `test_r173_03_…` |
| `AC-R173-04` | mover una **entrada** cuyo origen quedaría `< 0` → `400`; con origen suficiente → `200`, A baja, B sube | `test_r173_04_…` |
| `AC-R173-05` | cancelar una entrada que dejaría `< 0` → `400` (cuatro familias); estado y saldo intactos; sin auditoría `CANCELLED` | `test_r173_05_…` |
| `AC-R173-06` | cancelar una entrada con saldo suficiente → `200`, saldo exacto; cancelar una salida → restaura (`AC-R130-07`) | `test_r173_06_…` |
| `AC-R173-07` | segunda cancelación → `400`, sin segundo efecto | `test_r173_07_…` |
| `AC-R173-08` | carrera: cancelar una recepción de 100 vs cinco salidas de 20 → saldo final `≥ 0` y consistente con las filas | `test_r173_08_…` |
| `AC-R173-09` | carrera: mover una recepción A→B vs salida en A → a lo sumo una gana; A y B `≥ 0` | `test_r173_09_…` |
| `AC-R173-10` | auditoría de la edición con `previous_values`/`new_values` (`docs/13`) | dentro de `_03` |
| `AC-R173-11` | corrección de `lot_id` a lote de **otra empresa** → `400 BR-07`, evento intacto | `test_r173_11_…` |
| `AC-R173-12` | corrección de `lot_id` a lote de unidad **apagada** → `403`; a unidad **sin concesión** → `400 BR-07` | `test_r173_12_…` |
| `AC-R173-13` | corrección de `lot_id` a destino sin saldo → `400 BR-0x`; a lote inactivo → `400 BR-07` | `test_r173_13_…` |
| `AC-R173-14` | corrección de `farm_id` a granja de otra empresa → `400 BR-07` | `test_r173_14_…` |
| `AC-R173-15` | `PUT` de `lot_id` a otra empresa / unidad apagada / sin concesión → como `AC-W09` (control, `test_operations_bu_enforcement`) | regresión |
| `AC-R173-16` | denegaciones: cero cambios en `operational_events`, cero auditoría de éxito | en cada prueba |
| `AC-R173-17` | eventos sin efecto en saldo: la edición de lote sigue funcionando como hoy (`AC-W07`) | control |
| `AC-R173-18` | `R-130`, `R-161`, `R-135`/`R-143`, `R-159`/`R-160`, `R-162`/`R-163`, reversos: verdes | regresión |

Sensibilidad: `R173-S1` (quitar la regla de destino), `R173-S2` (no bloquear el destino / el lote en `cancel`), `R173-S3` (el saldo sigue contando
`CANCELLED`), `R173-S4` (quitar la relectura/estado en `cancel` → doble transición), `R173-S5` (quitar la cadena de inquilino/unidad en la corrección de
`lot_id`, cuatro capas del protocolo del tranche 4 si una sola no basta).

## 17. Registrados en este pre-flight (fuera del alcance del tranche)

| ID | P | Qué | Dónde | Por qué fuera |
|---|---|---|---|---|
| `R-176` | P3 | la edición no vuelve a correr reglas de destino **no keyed por lote**: `sap_document_ref` (`BR-18`, acumulado de la OC; `validate_oc_limit` ya admite `exclude_event_id` y nadie lo usa), `house_id` (`BR-17`, capacidad estática), `event_date` sola (`validate_event_date`/`validate_period_open` solo corren si cambia `lot_id`) | `service.py:1071-1088` | sin efecto en los cuatro saldos; `BR-18` es territorio `OD-04`/`GA-REM-035`; requiere su propia traza |
| `R-178` | P3 | `egg_batches`/`chick_batches` (linaje) se materializan al casar despacho y recepción y **no** se neutralizan ni se re-casan al cancelar o al mover de lote un despacho/recepción | `service.py:401-500` | no es saldo; linaje/trazabilidad (`spec.md §233`) |

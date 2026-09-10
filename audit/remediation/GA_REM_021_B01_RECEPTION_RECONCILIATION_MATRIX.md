# `GA-REM-021` · `B01` · MATRIZ DE CONTRATO DEL CUADRE DE RECEPCIÓN

**WAVE B · tranche 7 · pre-flight** · 2026-09-10 · `H360-B01` (P2) · fuente `Recomendación central.pdf` §6 (p.9-10) · método
`REQUIREMENT_CONFLICT_RESOLUTION §1` (niveles 1 propietario · 2 cliente · 3 proceso · 4 spec · 5 implementación · 6 legado; corte
en el nivel más alto que habla; el silencio desciende; escalado solo si nada por encima de la implementación habla **y** la
elección cambia el comportamiento de negocio).

## 1. Requisito exacto (nivel 2, textual)

`Recomendación central.pdf` §6 «Proceso recomendado: recepción de reproductoras» — **En administración web intermedia. Debe validarse:**

```
● Que la OC exista.
● Que la cantidad recibida no exceda la OC sin autorización.        ← OD-04 · GA-TD-014 · BR-18 (CERTIFICADO)
● Que la distribución por galpón no exceda capacidad.               ← BR-17 (certificado)
● Que hembras + machos + mortalidad + rechazo cuadren contra recibido.   ← B01 (este tranche)
● Que el lote esté definido.
● Que los pesos estén dentro de rango esperado.                     ← B02 (este tranche)
● Que exista evidencia.                                             ← B04 · AOD-14 (fuera)
● Que el responsable apruebe.
```

Captura móvil del mismo §6: «Cantidad esperada · **Cantidad recibida** · … · **Distribución de hembras** · **Distribución de machos** ·
Raza confirmada · Peso promedio de hembras · Peso promedio de machos · Muestra tomada · … · **Mortalidad al arribo** · Observaciones ·
Evidencias». `Bases Consideradas…pdf` (p.2, 4, 12) no menciona cuadre alguno. §13 (engorde) captura «Recepción de pollitos … Diferencias»
sin identidad de sexos. Ningún otro documento del cliente habla del cuadre.

## 2. Primer gate — ¿qué recepción cuadra `B01`?

| Candidata | ¿Es `B01`? | Por qué |
|---|:--:|---|
| Recepción **contra orden de compra** (acumulado ≤ OC) | **no** | es la viñeta anterior del mismo §6: `OD-04` → `GA-REM-035` → `GA-TD-014` **CERTIFIED** (2026-09-06); `docs/16 §6.1` y `OPERATIONAL_PROCESS_STATE_AND_CLOSURE_MATRIX §97-101` las listan como dos reglas con estados distintos («cantidad ≤ OC ✓ · cuadre ✗») |
| **Recepción de aves en granja** (`bird_reception`, inicio de cría de reproductoras, `P-01`/`P-03`) | **sí** | es el proceso del §6; los cuatro sumandos son datos de esa captura (distribución ♀/♂, mortalidad al arribo, rechazo) y «recibido» es «Cantidad recibida», campo de la misma captura |
| Recepción de huevos en incubadora (`egg_reception_hatchery`) | no | `docs/02 §3.7.1` («Diferencias vs enviado») es otro contrato, `R-161` familia; no es §6 |
| Recepción de pollitos en engorde (§13) | no como identidad | §13 no exige el cuadre de sexos (pollitos mixtos); `spec.md:213` sí declara «mortalidad inicial» como dato de esa recepción (ver §5) |
| Transferencia / traslado (`bird_transfer`) | no | intra-lote (`RR-02`); no hay «recibido» declarado |
| Importación de abuelas (`grandparent_import`) | no | `R-152`, fuera de este tranche |

**Respuesta:** `B01` es la **identidad interna del evento `bird_reception`** de un lote de Reproductoras:
`recibido = hembras + machos + mortalidad al arribo + rechazo`. No es un contrato acumulativo ni tiene recurso padre.

## 3. Traza `OD-04` / `GA-TD-014` — ¿mismo contrato de negocio?

| Dimensión | `OD-04` / `GA-TD-014` (`GA-REM-035`) | `B01` |
|---|---|---|
| Regla del cliente | «cantidad recibida no exceda la OC sin autorización» | «hembras + machos + mortalidad + rechazo cuadren contra recibido» |
| Lado izquierdo | Σ `BirdMovement.quantity` de todas las recepciones con la misma `sap_document_ref` | Σ `BirdMovement.quantity` **de este evento** + mortalidad al arribo + rechazo |
| Lado derecho | `SapReference.quantity` (OC local; SAP real diferido) | **`received_total` declarado en esta recepción** |
| Acumulación entre entregas | **sí** (entregas parciales, decisión del propietario) | **no**: cada entrega cuadra por sí misma |
| Tolerancia | ninguna (`AC11`) | ninguna (igualdad exacta) |
| Estado de cierre | no se introduce (`AC12`) | no aplica |
| Concurrencia | dos recepciones simultáneas podrían superar la OC; `GA-REM-035 §6` decide **no** introducir bloqueo | no hay agregado compartido entre peticiones: **N/A** |
| Estado | `CERTIFIED` | `OPEN` → este tranche |

**`B01` → mismo contrato que `OD-04`: NO.** Se reutiliza de `OD-04` únicamente el principio «sin tolerancia inventada». No se
mezclan los dos tipos de comprobación: la OC sigue en `validate_oc_limit` (`BR-18`) sin cambio.

## 4. Cada semántica, con el nivel que la resuelve

| Semántica | Nivel 1 | Nivel 2 (cliente) | Nivel 3 (`docs/02`) | Nivel 4 (`spec.md`) | Nivel 5 (código) | Nivel 6 (legado) | Corte |
|---|---|---|---|---|---|---|---|
| Proceso | — | §6 recepción de reproductoras | §3.5.2 Recepción y Distribución de Aves | §4.5 `bird_reception` «al inicio de cría» | `EventType.BIRD_RECEPTION` | `crias_recepcion_granja` | **`bird_reception` en lote `BREEDER`** |
| Recurso | — | evento de recepción | ídem | ídem | `OperationalEvent` + `BirdMovement[]` | ídem | ídem |
| Recurso padre / cantidad ordenada | — | OC (viñeta aparte) | OC/transferencia SAP en el alta del lote | — | `SapReference` (`GA-TD-014`) | `orden_compra_id` | **fuera de `B01`** (ya certificado) |
| «recibido» | — | **«Cantidad recibida»** capturada | — | — | no existe | — | **dato declarado `received_total`** (nivel 2) |
| hembras / machos | — | «Distribución de hembras / machos» | «Cantidad hembras, Cantidad machos» | «cantidad, sexo» | `BirdMovement(sex, quantity)` por galpón | `cantidad_machos/hembras` | **Σ `BirdMovement.quantity` = aves alojadas** (nivel 2 «distribución» + nivel 5) |
| mortalidad al arribo | — | «Mortalidad al arribo» (captura de la recepción) | — | §4.8 engorde: «mortalidad inicial» en `bird_reception` | mapeada a un evento `mortality_recording` aparte (`docs/16:177`, elección de nivel 5) | — | **dato de la recepción `dead_on_arrival`** (nivel 2 manda sobre la elección de nivel 5) |
| rechazo | — | sumando de la validación | — | — | no existe | — | **dato de la recepción `rejected_on_arrival`** (nivel 2; sin él la identidad no es comprobable) |
| Unidad | — | aves | aves | aves | `Integer` (`BirdMovement.quantity`) | entero | **aves, entero** |
| Tolerancia | — | ninguna («cuadren») | — | — | `OD-04`: ninguna | — | **ninguna: igualdad exacta** |
| Entregas parciales | — | §3.1 «Recepciones parciales» (SAP) | — | — | `OD-04` | — | **cada entrega cuadra por sí misma**; la acumulación es `BR-18` |
| Sobre-recepción / bajo-recepción | — | viñeta de la OC | — | — | `BR-18` | — | **no es `B01`** |
| Estado de cierre / completitud | — | — | — | — | `GA-REM-035 AC12`: ninguno | — | **no se introduce** |
| Fecha de negocio | — | «Fecha real de recepción» | «Fecha recepción» | — | `event_date` (`BR-06`, `BR-19`/`R-30`) | `fecha_recepcion` | **`event_date`, sin regla propia** |
| Duplicado / idempotencia | — | — | — | `BR-12` | `idempotency_key` en el alta (`service.py:193`) | — | **mecanismo existente; sin campo nuevo** |
| Corrección | — | — | `docs/12 §3` corregir | `RR-01` | `campos_corregibles` = `OperationalEventUpdate` | — | **los tres campos entran en `Update` → corregibles; la identidad se revalida** |
| Concurrencia | — | — | — | — | — | — | **N/A** (identidad intra-evento) |
| Transacción | — | — | — | — | `create_event` atómico; regla antes de `db.add` | — | **rechazo = cero efectos** |
| Inquilino | `OD-14.c/d` | — | — | — | `validate_lot_active(company)`, `_unidad_del_lote`, `_tipo_de_lote`, `lotes_alcanzables` | — | **cadena certificada (`R-160`, `B05`)** |
| Unidad de negocio | `OD-16` | — | — | — | `exigir_unidad_operativa` | — | **cadena certificada** |
| RBAC | — | — | — | — | `operations:create` / `update`; `corrections:correct` | — | **sin permiso nuevo** |
| Estado (`P-07`) | `OD-17` | — | `docs/12` | — | máquina certificada (`R-135`/`R-143`) | — | **sin cambio** |
| Auditoría | — | — | — | — | `audit_state_transition` en el alta | — | **sin cambio**; alta denegada no audita |
| Frontera SAP | — | §6 «Luego se envía a SAP: … Diferencias» | — | — | `GA-REM-017 BLOCKED_EXTERNAL` | — | **SAP no participa**; «Diferencias» hacia SAP es `P-08` diferido |
| Relación con `R-130` | — | — | — | — | `SALDO = apertura + Σ recepciones − salidas` | — | **entradas = Σ alojadas (sin cambio)**; mortalidad al arribo y rechazo **nunca entran** al saldo (§7) |
| Soporte actual | — | — | — | — | **0 referencias** a cuadre/rechazo en `operations/*.py` | — | brecha completa |

**Escalado:** ninguna semántica queda sin nivel por encima de la implementación. **No se requiere decisión del propietario.**
Registro: `RC-11` / `RR-12` en `REQUIREMENT_CONFLICT_RESOLUTION.md`.

## 5. Matriz de aplicabilidad por unidad de negocio

| Unidad (`Lot.bird_type`) | Recepción | `received_total` | `dead_on_arrival` | `rejected_on_arrival` | Identidad | Fuente |
|---|---|:--:|:--:|:--:|:--:|---|
| **Reproductoras** (`breeder`) | `bird_reception` | **obligatorio** (≥ 1) | **obligatorio** (≥ 0, explícito) | **obligatorio** (≥ 0, explícito) | **sí** (`BR-20`) | Rec. §6 (nivel 2) |
| Engorde (`broiler`) | `bird_reception` | prohibido (400) | **opcional** (≥ 0) | prohibido (400) | no | `spec.md §4.8:213` «mortalidad inicial» (nivel 4); §13 sin cuadre |
| Progenitoras (`grandparent`) | `grandparent_import` (`R-152`) / `bird_reception` | prohibido | prohibido | prohibido | no | sin fuente; `R-152` fuera |
| Incubadora (`hatchery`) | recibe huevos, no aves | prohibido | prohibido | prohibido | no | N/A |
| lote sin cadena (`bird_type = NULL`) | — | prohibido | prohibido | prohibido | no | cadena pendiente (`OD-10.c`): sin unidad no hay regla aplicable |
| cualquier otro tipo de evento | — | prohibido | prohibido | prohibido | — | un dato, un registro (precedente `B05`) |

«Obligatorio explícito»: la ausencia de dato no se interpreta como `0` (`RR-11`); el operador declara `0` cuando no hubo muertes ni rechazo.

## 6. Contrato de datos

| Campo | Tipo | Alta (`OperationalEventCreate`) | Edición (`Update`) | Corrección | Persistencia |
|---|---|---|---|---|---|
| `received_total` | `int` ≥ 1 | obligatorio en recepción de reproductoras; prohibido fuera | editable | corregible (`RR-01`) | `operational_events.received_total INTEGER NULL` |
| `dead_on_arrival` | `int` ≥ 0 | obligatorio en reproductoras; opcional en engorde; prohibido fuera | editable | corregible | `operational_events.dead_on_arrival INTEGER NULL` |
| `rejected_on_arrival` | `int` ≥ 0 | obligatorio en reproductoras; prohibido fuera | editable | corregible | `operational_events.rejected_on_arrival INTEGER NULL` |
| aves alojadas | derivado | **nunca del cliente**: Σ `bird_movements[].quantity` del evento | Σ de los movimientos persistidos | ídem | no se persiste (derivado) |

Regla `BR-20` (código nuevo de la familia `BR-17`…`BR-19`, pendiente de fusión en `spec.md §5` por `GA-REM-018` como aquéllas):

```
recepción de reproductoras:  received_total == Σ quantity(bird_movements) + dead_on_arrival + rejected_on_arrival
                             en caso contrario → 400 · rule = "BR-20" · el mensaje nombra los cuatro números
```

`NULL` en filas históricas = no declarado (la migración no rellena nada). El cliente no envía el total alojado: la
identidad se calcula contra las filas de movimientos que el propio servidor persiste (`extra_data.declared_quantity`,
`extra_data.placed_total` o cualquier otro campo libre **no** participan).

## 7. Relación con `R-130` (verdad del saldo)

```
SALDO(lote) = apertura + Σ BirdMovement.quantity(BIRD_RECEPTION) + nacimientos − salidas        (sin cambio)
```

Las aves alojadas (♀ + ♂) son las que entran al lote; la mortalidad al arribo y el rechazo **nunca formaron parte de la
parvada** y no entran al saldo. La recepción dice «recibidas 100, alojadas 95, muertas 3, rechazadas 2» y el saldo dice 95:
la diferencia la explica la propia recepción. No hay segundo motor de saldo.

Riesgo documentado (no resuelto aquí, `R-167`): la práctica vigente registraba la mortalidad al arribo como un evento
`mortality_recording` aparte (`docs/16:177`). Si un operador declara `dead_on_arrival` **y** además registra ese mismo evento,
el saldo descuenta aves que nunca entraron. Ninguna fuente fija si la mortalidad al arribo cuenta en la tasa de mortalidad
(`Bases` p.2 «número total de pollitos al inicio»): es semántica de KPI (ola C, `GA-REM-022`). `B01` no lo decide.

## 8. Corrección, edición, concurrencia, idempotencia

- **Edición** (`PUT`, estados `EDITABLES`): los tres campos se revalidan contra Σ de los movimientos persistidos (los movimientos
  no se editan por `PUT`).
- **Corrección** (`POST /corrections`, un campo por corrección): los tres sumandos **no son corregibles uno a uno** — corregir uno
  solo siempre descuadra un registro cuadrado — y `campos_corregibles()` los excluye explícitamente (excepción documentada a `RR-01`).
  Se arreglan por edición (`PUT` con los sumandos afectados) en un estado editable, o devolviendo el registro (`RETURNED`, `R-135`).
  Ninguna vía deja la recepción descuadrada.
- **Concurrencia**: N/A — no hay agregado compartido. (La carrera del acumulado de la OC está documentada y decidida en
  `GA-REM-035 §6`; no se toca.)
- **Idempotencia**: `idempotency_key` existente (`BR-12`); no se inventa número de recibo ni guía.
- **Inmutabilidad**: `APPROVED` y posteriores no se editan ni corrigen (`R-135`/`R-143`, `AC-S10`); sin cambio.

## 9. Frontera

Fuera: `B02` se trata en su matriz; `B03` (alimento), `B04` (`AOD-14`), `B13`; `R-152`/`R-153`; `R-156` (peso proveedor, `AOD-20`);
`R-161`; `R-164`; `R-166`; cierre automático de OC; tolerancia; estado de recepción; SAP («Diferencias», `P-08`); KPI de
mortalidad (ola C); pantalla de recepción nueva (fase 9) — solo la vertical mínima de captura.

## 10. Hallazgos registrados en este pre-flight (no se resuelven aquí)

| ID | Sev. | Hallazgo | Origen |
|---|:--:|---|---|
| `R-167` | P3 | doble contabilización posible de la mortalidad al arribo (campo de la recepción + evento `mortality_recording` del mismo día); semántica del KPI de mortalidad sin fuente | §7 |
| `R-168` | P3 | el formulario de recepción registra `bird_movements[i].sample_size` y `BirdMovementSchema` no lo declara: el cliente envía, el esquema descarta (patrón `R-47`); «Muestra tomada» del §6 no se persiste por galpón | `OperationFormPage.tsx:698` · `schemas.py:12-20` |
| `R-169` | P3 | el formulario de recepción muestra una alerta «diferencia superior al 10 %» entre recibido y declarado sin fuente normativa (solo cliente, solo aviso); `FUNCTIONAL_COVERAGE_MATRIX CV-F07` la cuenta como «validación ±10 %» | `OperationFormPage.tsx:610-611` · familia `R-147` |

## Resultado (2026-09-10)

Cerrado (técnico) por `GA-REM-021-B` (commits `f878ab6` spec · `a759a17` código · commit de evidencia): 8/8 · sensibilidad válida ·
regresión 1016 passed · 49 skipped · 0 failed (935 s; 1000 previas + 16 nuevas; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) · evidencia `GA-REM-021-B01-B02-RECEPTION-EVIDENCE.md`. `GA-REM-021` sigue **PARTIAL**.

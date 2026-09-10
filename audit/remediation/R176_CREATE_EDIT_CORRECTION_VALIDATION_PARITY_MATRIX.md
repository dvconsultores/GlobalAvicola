# `R-176` · Paridad de validación alta / edición / corrección (`R176_CREATE_EDIT_CORRECTION_VALIDATION_PARITY_MATRIX`)

**WAVE B · tranche 11 · pre-flight** · 2026-09-10 · hallazgo `R-176` (registrado P3 en el pre-flight del tranche 10; **normalizado P2**, §7) ·
absorbe **`R-45`** (Wave 2, P2: «corregir `event_date` no revalida `BR-19`», abierto → `GA-REM-016`/`GA-REM-019`, nunca cerrado) · spec gobernante
`GA-REM-023` (contrato de validación de los eventos operativos) + `GA-REM-005-E` (guarda central de edición/corrección) · **sin decisión del propietario**.

## 1. Hallazgo exacto

> `R-176` · «la edición no vuelve a correr reglas de destino no keyed por lote: `sap_document_ref` (`BR-18`, acumulado de la OC; `validate_oc_limit`
> tiene `exclude_event_id` sin uso), `house_id` (`BR-17`, capacidad estática), `event_date` sola (`validate_event_date`/`validate_period_open` solo
> si cambia `lot_id`); sin efecto en los cuatro saldos» · `service.py` (`verificar_destino_de_edicion`) · `REMEDIATION_BACKLOG.md:1293`.

Ampliación leída (misma raíz exacta: regla del alta cuyo campo disparador es editable o corregible y no se vuelve a evaluar): `BR-08` (`farm_id`/`house_id`
puestos a nulo) y `BR-11` (unicidad del documento SAP por lote y tipo; el código la emite como `BR-10`). `POST /corrections` admite los mismos campos
(`campos_corregibles()`) y solo revalida `chicks_*`, `water_liters` y, desde `R-173`, lote/ubicación (empresa, unidad, activo, fecha vs lote, saldo).
Prueba existente que documenta el defecto de fecha: `tests/test_corrections.py::test_la_fecha_corregida_sigue_sujeta_a_las_reglas` («hoy la corrección
escribe la fecha sin revalidarla … `R-45`»), con aserción tolerante `(400, original) | (201, fecha en período cerrado)`.

## 2. Las reglas, definidas (`§10`)

| Regla | Fuente | Proceso | Entradas | ¿Pura? | ¿Efecto lateral? | ¿Lee BD? | ¿Bloqueo? | Alta | Edición (`PUT`) hoy | Corrección hoy | Anulación | Código de error | Pruebas actuales |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **`BR-17`** capacidad del galpón (`validate_house_capacity`) | `G-R04` (`docs/16 :419`, Rec. central: «sin validación de capacidad de galpón: puede asignar más aves de las que caben») · `GA-REM-023 §Reglas` · `docs/02 §2 Galpones: capacidad` | recepción y distribución de aves | `house_id`, `n` = Σ `bird_movements.quantity` | **sí** | no | sí (`houses.capacity`) | no (estática: `n > capacity`) | sí (`_apply_business_rules`, si `house_id` y `n > 0`) | **no** | **no** | n/a | `400 BR-17` | `test_operations`/flujo (alta) |
| **`BR-18`** acumulado de la OC (`validate_oc_limit`) | `OD-04` · `GA-REM-035 §3` («acumulado + nueva ≤ ordenada»; el acumulado excluye solo `CANCELLED`) · `G-R05` | recepción (y distribución) de aves con `sap_document_ref` de tipo `PURCHASE_ORDER` | `sap_document_ref`, `n`, `company_id`, `exclude_event_id` | **sí** | no | sí (`sap_references`, agregado de `bird_movements`) | no (`GA-REM-035 §6`: sin bloqueo; fuera) | sí | **no** (el acumulado se **mueve** de OC sin comprobar) | **no** | n/a | `400 BR-18` | `test_purchase_order_receipt` (alta) |
| **`BR-06`** fecha ≥ inicio del lote (`validate_event_date`) | `docs/02 §7 R6` · `spec.md §5 BR-06` | todos con lote | `lot_id`, `event_date` | sí | no | sí (`lots.start_date`) | no | sí | **solo si cambia `lot_id`** (`R-173`) | solo si se corrige `lot_id` | n/a | `400 BR-06` | `test_lot_start_date` (alta) |
| **`BR-19`** período abierto y no futuro (`validate_period_open`) | `G-R12` · `GA-REM-015 AC12` (+90 días) · `GA-REM-023` addendum `R-30 AC13` (fecha futura) | todos | `event_date` (vs `date.today()`, `R-80` aparte) | sí | no | no | no | sí | **no** | **no** (`R-45`) | n/a | `400 BR-19` | `T-028-01…03`, `R-30` (alta) |
| **`BR-08`** ubicación obligatoria (`validate_farm_house`) | `spec.md §5 BR-08` · `F-03` | eventos de ubicación (recepción, distribución, traslado, salida, inspecciones, huevos, despacho de pollitos) | `event_type`, `farm_id`, `house_id` | sí | no | no | no | sí | **no** (`{"house_id": null}` se aplica) | **no** (`""` → `None`) | n/a | `400 BR-08` | alta |
| **`BR-11`** documento SAP no duplicado (`validate_sap_document_unique`, emite `BR-10`) | `spec.md §5 BR-11` («Documentos SAP no se duplican»; el código usa la etiqueta `BR-10`: **observación**, no se cambia) | todos con lote salvo `bird_reception` (`OD-04`: la OC se repite) | `lot_id`, `event_type`, `sap_document_ref`, `exclude_event_id` | sí | no | sí | no | sí | **no** (ni al cambiar la referencia ni al cambiar de lote) | **no** | n/a | `400 BR-10` | `test_full_workflow_audit::f8b` (alta) |
| ya cubiertas | `BR-07` activo/empresa · unidad · ubicación (`verificar_ubicacion`) · `BR-20` · `BR-21` · `RR-11` · saldos (`BR-01/02/03/04`) | — | — | — | — | — | — | sí | sí (`R-160`, `R-173`, `GA-REM-021`) | sí | — | — | — |

Ninguna de las seis es lógica de creación con efectos: son lecturas puras. **Paridad ≠ repetir el alta**: `create_event` además persiste, audita `created`,
crea alertas, notificaciones y vínculos de trazabilidad; nada de eso se repite en `PUT`/`POST /corrections` (`AC-R176-09`).

## 3. Matriz de paridad (`§12`)

| Regla | Fuente | Alta | `PUT` | `POST /corrections` | Anulación | Campos que la disparan | ¿Pura? | ¿Efecto? | Función en el alta | Función en edición | Función en corrección | Paridad exigida | Brecha actual | AC | Prueba |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `BR-17` | `G-R04` | ✔ | ✘ | ✘ | n/a | `house_id` (recepción/distribución) | sí | no | `_apply_business_rules` | — | — | `validate_house_capacity(cand.house_id, n)` cuando cambia `house_id` | edición a un galpón menor que la recepción se acepta | `AC-R176-01/02` | `PARI-` |
| `BR-18` | `OD-04` · `GA-REM-035` | ✔ | ✘ | ✘ | n/a | `sap_document_ref` (recepción/distribución) | sí | no | ídem | — | — | `validate_oc_limit(cand.ref, n, company, exclude_event_id=event.id)` cuando cambia la referencia | el acumulado cambia de OC y puede superar la orden | `AC-R176-03/04` | `PARI-` |
| `BR-06` | `R6` | ✔ | parcial (solo con `lot_id`) | parcial | n/a | `event_date`, `lot_id` | sí | no | ídem | `verificar_destino_de_edicion` (solo lote) | ídem | `validate_event_date(lote_destino, cand.event_date)` cuando cambia `event_date` o `lot_id` | fecha anterior al lote por edición de fecha | `AC-R176-05` | `PARI-` |
| `BR-19` | `G-R12` · `R-30` | ✔ | ✘ | ✘ (`R-45`) | n/a | `event_date` | sí | no | ídem | — | — | `validate_period_open(cand.event_date)` cuando cambia `event_date` | período cerrado y fecha futura por edición/corrección | `AC-R176-05` | `PARI-` |
| `BR-08` | `spec.md` | ✔ | ✘ | ✘ | n/a | `farm_id`, `house_id` | sí | no | ídem | — | — | `validate_farm_house(tipo, cand.farm_id, cand.house_id)` cuando cambia alguno | ubicación a nulo | `AC-R176-05b` | `PARI-` |
| `BR-11` (`BR-10`) | `spec.md` | ✔ | ✘ | ✘ | n/a | `sap_document_ref`, `lot_id` | sí | no | ídem | — | — | `validate_sap_document_unique(lote_destino, tipo, cand.ref, exclude_event_id=event.id)` cuando cambia la referencia o el lote (tipo ≠ `bird_reception`) | duplicado por edición | `AC-R176-05c` | `PARI-` |

## 4. Matriz campo → reglas (`§13`, esquema real de `OperationalEventUpdate` / `campos_corregibles()`)

| Campo | Reglas afectadas | ¿Saldo? | ¿Fecha? | ¿Referencia externa? | ¿Lote? | ¿Recurso? | ¿Revalidar? |
|---|---|---|---|---|---|---|---|
| `lot_id` | `BR-07` (activo, empresa) · unidad · `BR-06` · saldos (`R-173`) · **`BR-11`** (unicidad en el lote destino) · linaje (`R-178`) | sí | sí | no | sí | no | sí (ya) + `BR-11` + linaje |
| `event_date` | **`BR-06`** · **`BR-19`** | no (los saldos no filtran por fecha) | sí | no | no | no | **sí** |
| `house_id` | ubicación (empresa) · **`BR-08`** · **`BR-17`** | no | no | no | no | sí | **sí** |
| `farm_id` | ubicación · **`BR-08`** | no | no | no | no | sí | **sí** |
| `destination_farm_id` | ubicación (`R-173`) · linaje (`R-178`: destino declarado de un despacho casado) | no | no | no | no | sí | sí (ya) + linaje |
| `sap_document_ref` | **`BR-18`** (recepción/distribución) · **`BR-11`** (resto) | no | no | sí | no | no | **sí** |
| `water_liters` · `chicks_healthy/weak` · `received_total`/`dead_on_arrival`/`rejected_on_arrival` | `RR-11` · `BR-21` · `BR-20` | no | no | no | no | no | ya (`GA-REM-021 A/B/C`) |
| `observations`, `cause_id`, `cull_cause_id`, `vaccine_*`, `medication_id`, `dosage_per_bird`, `treatment_days`, `supplier_id`, `transport_id`, `sample_size`, `destination_plant_id`, `extra_data` | ninguna regla de negocio del alta | no | no | no | no | no | no (sin sobre-validación) |
| cantidades (`bird_movements`, `egg_movements`, `hatchery_params`, `feed_movements`) · `event_type` · `status` · `idempotency_key` | — | — | — | — | — | — | **no editables ni corregibles** (`422`/`400`, `GA-REM-005-B`, `R-32`) |

## 5. Frontera de estados y de `R-173` (`§19`, `§20`)

- Estados: `PUT` en `EDITABLES`, corrección en `REGISTERED…REJECTED`, sin cambio; lo aprobado sigue inmutable (`R-135`/`R-143`, `AC-R176-11`).
- `R-173` ya cubre: empresa, unidad, lote activo, fecha **vs lote** (solo al cambiar de lote), ubicación (pertenencia), saldos, bloqueo, auditoría con valores.
  `R-176` **extiende la misma guarda** (`verificar_destino_de_edicion`) con las reglas puras del alta sobre el **estado candidato** (persistido + cambio):
  `BR-08` → `BR-06`/`BR-19` → `BR-11` → `BR-17` → `BR-18`, antes del bloqueo y de las reglas de saldo. Una sola guarda, dos superficies públicas
  (`PUT`, `POST /corrections`), ambas probadas.
- Fecha de negocio ≠ ahora del servidor: `validate_period_open` se reutiliza tal cual (`date.today()`; `R-80` aparte); pruebas con `tests.time_reference`.
- Contrato de error: el de cada regla en el alta (`400 {detail, rule}` con `BR-17`, `BR-18`, `BR-06`, `BR-19`, `BR-08`, `BR-10`); nada nuevo.

## 6. Reproducción prevista (`§14-§16`) y AC → prueba (contrato completo en `GA-REM-023-B`)

| AC (prompt) | AC repo | Qué | Prueba (`tests/test_edit_validation_parity.py`, prefijo `PARI-`) |
|---|---|---|---|
| `AC-176-01` | `AC-R176-01` | `PUT house_id` de una recepción de 100 a un galpón de capacidad 50 → `400 BR-17`; evento, saldo y auditoría intactos | `_01` |
| `AC-176-02` | `AC-R176-02` | corrección de `house_id` → ídem | `_02` |
| `AC-176-03` | `AC-R176-03` | dos OC de 100 (`OC-A` con 80 recibidas, `OC-B` con 50): `PUT sap_document_ref` de la segunda → `OC-A` → `400 BR-18` (130 > 100) | `_03` |
| `AC-176-04` | `AC-R176-04` | corrección de `sap_document_ref` → ídem | `_04` |
| `AC-176-05` | `AC-R176-05` | `PUT`/corrección de `event_date` a período cerrado (+90 d) → `400 BR-19`; a fecha futura → `400 BR-19`; anterior al inicio del lote → `400 BR-06` | `_05` |
| — | `AC-R176-05b` | `PUT {"house_id": null}` / corrección `farm_id` = `""` en evento de ubicación → `400 BR-08` | `_05b` |
| — | `AC-R176-05c` | `PUT`/corrección de `sap_document_ref` a una referencia ya usada en el mismo lote y tipo → `400 BR-10`; mover el evento a un lote donde la referencia ya existe → `400 BR-10` | `_05c` |
| `AC-176-06` | `AC-R176-06` | edición válida (galpón con capacidad, OC con cupo, fecha dentro) → `200`, valores aplicados | `_06` |
| `AC-176-07` | `AC-R176-07` | corrección válida → `201`, `CORRECTED`, valor aplicado | `_07` |
| `AC-176-08` | `AC-R176-08` | toda denegación: cero cambios en la fila, saldo, `audit_logs` de éxito, alertas, notificaciones, vínculos | en cada prueba |
| `AC-176-09` | `AC-R176-09` | edición/corrección válida: solo +1 auditoría (`UPDATED`/`CORRECTED`); cero alertas, notificaciones, vínculos o filas nuevas; saldos iguales | `_09` |
| `AC-176-10` | `AC-R176-10` | la guarda de destino de `R-173` sigue (`test_edit_cancel_balance` 16/16) | regresión |
| `AC-176-11` | `AC-R176-11` | aprobado: `PUT` → `400` como hoy | `_11` |
| `AC-176-12` | `AC-R176-12` | otra empresa / unidad apagada / sin permiso → `400 BR-07` / `403`; ninguna regla de negocio se evalúa antes de la cadena | `_12` |

Sensibilidad: `R176-S1` (quitar `BR-17` del `PUT`) · `R176-S2` (quitar `BR-17`… y `BR-19` de la corrección: la corrección llama a la misma guarda,
así que se muta la **llamada** desde la corrección para `house_id`/`event_date`) · `R176-S3` (quitar `BR-18`) · `R176-S4` (quitar `BR-19`/`BR-06` de
la fecha) · `R176-S5` (reproducir un efecto del alta —una alerta de peso o un vínculo de trazabilidad— en la edición válida → `AC-R176-09` roja).

## 7. Severidad y clasificación

`R-45` era P2 (fecha en período cerrado por corrección). `R-176` añade `BR-18` (superar la orden de compra moviendo el acumulado de OC: efecto de
negocio real, `OD-04`) y `BR-17`/`BR-08`/`BR-11`. Sin saldo negativo ni bypass de inquilino → **P2**, no P1. Un solo ID: `R-176` **absorbe** `R-45`
(mismo defecto, misma corrección); `R-45` se cierra con él (no por transitividad: `AC-R176-05` es su prueba).

```
R-176 ............ ACTIVE · GOBERNADO (AC-W09/RR-18 «destino de una edición = alta» · GA-REM-023 contrato de validación · GA-REM-035 · R-30 · R6 · spec.md BR-08/BR-11
                   · «corregir no es una puerta trasera», R-45) · SIN DECISIÓN · P2 · ejecutable · absorbe R-45
spec ............. GA-REM-023 addendum B (paridad de validación en edición y corrección) · sin GA-REM nueva · sin migración
observación ...... la unicidad del documento SAP se emite como BR-10 aunque spec.md la numera BR-11 (etiqueta histórica; no se cambia: contrato de error existente)
```

## 8. Cierre (2026-09-10)

`R-176` CERRADO (técnico) · `R-45` cerrado con él · `GA-REM-023-B` certificada · `AC-R176-01…12` verdes · sensibilidad `R176-S1…S5` válidas · evidencia `WAVE_B_TRANCHE_11_VALIDATION_PARITY_AND_LINEAGE_EVIDENCE.md`.

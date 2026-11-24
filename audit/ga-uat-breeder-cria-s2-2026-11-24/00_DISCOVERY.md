# Descubrimiento — UAT Reproductoras/Cría Sesión 2 (`GA-UAT-BREEDER-CRIA-S2-2026-11-24`)

Spec: `specs/020-uat-breeder-cria-s2/spec.md` (tabla de hallazgos en §2, decisiones en §4). Documento fuente: PDF «SESION 2 - REVISION GESTION AVICOLA - REPRODUCTORA - CRIA - 24-11-2026». Solo lectura de código; ninguna línea de producto se modificó en esta fase.

## 1. Gate 0 — runtime probado por Yolinel
| Dato | Valor |
|---|---|
| `ORIGIN_DEVELOP_SHA` | `00fd162` |
| `ORIGIN_MAIN_SHA` | `1587073` (merge del PR #2; contiene develop) |
| Runtime UAT al iniciar el ciclo | backend y frontend `00fd162`, build del 22-11-2026 23:09Z |
| `YOLINEL_BACKEND_SHA` / `YOLINEL_FRONTEND_SHA` | `NOT_ACCESSIBLE` (el PDF no trae marca de versión) |
| Evidencia temporal | historial de corrección sellado 22/11/2026 15:22 (hora Caracas), anterior al build `00fd162` ⇒ build intermedio `8531d95`…`00fd162` |
| Evidencia funcional | capturas con campos corregibles por fila, código de lote en las listas y mínimos de la Sesión 1 ⇒ el build contiene la entrega de la Sesión 1 (`562c346`) |

```
DEPLOYMENT_MISMATCH = NO
SESSION2_FINDINGS_VALID_FOR_CODE = YES
SESSION1_REGRESSION = NO
```

## 2. Matriz de regresión de la Sesión 1
| Hallazgo S2 | Ya corregido en S1 | Resultado actual | Clasificación |
|---|---|---|---|
| Inspección sin valores | S1-TRACE-01 / D1 (unidad derivada o pendiente) y galpón obligatorio (`BR-08`) | Granja + galpón + fecha exigidos; sin contenido mínimo definido | OWNER_DECISION_REQUIRED (`OD-S2-02`) |
| Inspección aprobada sin lote | D1: la clasificación por unidad no asigna lote | Comportamiento esperado; la lista mostraba un texto engañoso | EXPECTED + BUG de UX |
| Recepción con campos vacíos | `BR-08` y `BR-20` (breeder) | Opcionales: proveedor, línea, galpón por fila, peso | EXPECTED |
| Recepción con muestra mayor | No cubierto | `sample_size` sin validación alguna | BUG P1 |
| Distribución sin cantidades | «Sin cambio» (S1 §4.3) | Sin regla de suma > 0 | OWNER_DECISION_REQUIRED (`OD-S2-03`) |
| Alimento sin fase ni tipo | D2 / `RR-23` (solo kg > 0) | Kg obligatorios; el resto opcional | EXPECTED |
| Pesaje sin semana | S1 §4.2: «Semana» sin valor por defecto | Semana opcional | OWNER_DECISION_REQUIRED (`OD-S2-04`) |
| Vacunación sin lote de vacuna | D2 / `RR-21` (solo vacuna) | Lote de vacuna opcional | OWNER_DECISION_REQUIRED (`OD-S2-05`) |
| Mortalidad vacía | S1-MORT / `BR-01` | Vacía ⇒ 400; la captura traía cantidades | NOT_REPRODUCED; causa y semana: `OD-S2-06` / `OD-S2-04` |
| Descarte vacío | `BR-01` (misma regla) | Ídem | NOT_REPRODUCED; causa y semana: `OD-S2-06` / `OD-S2-04` |
| Filtro de lote en Revisión/Aprobaciones | S1-ID-02 (solo Historial) | Pide ID numérico | Cierre incompleto de la Sesión 1 (no regresión) |

## 3. Matriz de contrato de corrección
Fuentes: `backend/app/corrections/service.py` (`SUBMOV_CORREGIBLES`, `_convertir`, `_convertir_valor_de_fila`) y `backend/app/operations/schemas.py`. Lo que no consta se marca «sin contrato».

| Evento | Campo | Tipo de control hoy | Obligatorio | Anulable | Maestro | Validación vigente |
|---|---|---|---|---|---|---|
| Recepción | `sample_size` | texto/numérico | no | sí | no | ninguna (BUG; V01, V02) |
| Recepción | `bird_movements.avg_weight` | decimal | no | sí | no | > 0 si se informa |
| Recepción | `bird_movements.quantity` (breeder) | no corregible | — | — | no | identidad `BR-20` |
| Recepción | `supplier_id` | texto con ID | no | sí | `suppliers` | pertenencia a la empresa |
| Recepción | `transport_id` | texto con ID | no | sí | `transports` | pertenencia a la empresa |
| Distribución | `bird_movements.quantity` | entero | sin contrato (`OD-S2-03`) | — | no | ≥ 0 |
| Distribución | `bird_movements.week_number` | entero | sin contrato (`OD-S2-04`) | sí | no | ≥ 0 |
| Alimento | `feed_movements.quantity_kg` | decimal | sí (`RR-23`) | no | no | > 0 |
| Pesaje | `bird_movements.avg_weight` | decimal | sí (`RR-20`, al menos una fila) | no (última fila con peso) | no | > 0 |
| Pesaje | `bird_movements.week_number` | entero | sin contrato (`OD-S2-04`) | sí | no | ≥ 0 |
| Pesaje | `sample_size` | numérico | no | sí | no | ninguna (BUG; V01) |
| Vacunación | `vaccine_id` | texto con ID | sí (`RR-21`) | no | `vaccines` | pertenencia a la empresa |
| Vacunación | `vaccine_lot_number` | texto | no (`OD-S2-05`) | sí | no | sin contrato |
| Medicación | `medication_id` | texto con ID | sí (`RR-22`) | no | `medications` | pertenencia a la empresa |
| Medicación | `dosage_per_bird` / `treatment_days` | numérico | sin contrato | sí | no | ninguna (V03) |
| Mortalidad | `bird_movements.quantity` | entero | sí (`BR-01`, total > 0) | no | no | saldo por delta |
| Mortalidad | `cause_id` | texto con ID | sin contrato (`OD-S2-06`) | sí | `mortality-causes` | pertenencia a la empresa |
| Descarte | `bird_movements.quantity` | entero | sí (`BR-01`, total > 0) | no | no | saldo por delta |
| Descarte | `cull_cause_id` | texto con ID | sin contrato (`OD-S2-06`) | sí | `cull-causes` | pertenencia a la empresa |
| Todos | `event_date` | fecha | sí | no (BUG: hoy se acepta vacío) | no | `BR-06`, `BR-19` |
| Todos | `observations` | texto | no | sí | no | ninguna |

## 4. Decisiones Owner
Ver `specs/020-uat-breeder-cria-s2/spec.md` §4 (`OD-S2-01`..`OD-S2-06`, con recomendación).

## 5. Gate de autorización
```
AUTHORIZATION_GATE = PASS
```
Solo se implementan los bugs y regresiones con contrato o invariante físico claro: V01..V04, C01..C07, R01..R03 y U01. Las decisiones `OD-S2-01..06` no se implementan.

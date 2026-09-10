# `GA-REM-035` · RECEPCIÓN CONTRA ORDEN DE COMPRA

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-035` · `BUSINESS RULE ACTIVATION SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Deuda** | `GA-TD-014` — de `DIFERIDO` a **`ACTIONABLE`** |
| **Decisión** | **`OD-04` `RESOLVED`** (2026-09-06) |
| **Reglas** | `BR-18` / `G-R05` se activa · `BR-10`/`BR-11` **no** se aplica a la recepción |
| **Procesos** | `P-01` · `P-03` · `P-06` |
| **Antecedentes** | `RC-07_BUSINESS_DECISION_DOSSIER.md` · `GA-TD-014_PARTIAL_RECEIPT_MATRIX.md` · `C-15` de `FE_BE_CONTRACT_MATRIX` |

> Spec propia y no enmienda de `GA-REM-011`. Aquella alinea contratos entre capas y difirió
> `C-15` a la espera de esta decisión; esto es la **activación de una regla de negocio** con
> semántica acumulativa nueva, y merece sus propios criterios y su propia certificación.

---

## 1. La decisión del propietario

```
Una misma orden de compra puede recibirse mediante múltiples entregas parciales.
```

Es normativa. De ella se sigue que **repetir la referencia de una OC no es un error** y que la
protección debe recaer sobre la **cantidad acumulada**.

## 2. Lo que hoy ocurre

**El campo tipado no se puebla.** `OperationFormPage` guarda la orden en
`extra_data.sap_order_ref`; `sap_document_ref` queda nulo y las dos reglas que lo miran salen
por su primera línea. Eso es `GA-TD-014`.

**Y la regla escrita no protege lo que hay que proteger.** `validate_oc_limit` compara
únicamente la recepción en curso:

```python
if oc and oc.quantity is not None and quantity_received > oc.quantity:
```

Tres entregas de 400 contra una orden de 1000 pasarían las tres —cada una es menor que
1000— y sumarían 1200. **El límite acumulado nunca se comprobó.**

**Y hay una regla que contradice la decisión.** `validate_sap_document_unique` rechaza un
segundo evento con la misma referencia para el mismo lote y tipo. Aplicada a la recepción,
prohibiría exactamente lo que `OD-04` autoriza.

## 3. La regla, con los nombres reales

| Concepto | Origen |
|---|---|
| cantidad ordenada | `SapReference.quantity` · `ref_type = PURCHASE_ORDER` · `sap_code = sap_document_ref` · de la compañía del actor |
| cantidad ya recibida | suma de `BirdMovement.quantity` sobre eventos con el mismo `sap_document_ref`, `event_type = BIRD_RECEPTION`, `status.not_in([CANCELLED])` |
| unidad | **aves** en ambos lados; no hay conversión que definir |

```
acumulado + nueva ≤ ordenada   →  aceptar
acumulado + nueva > ordenada   →  rechazar, citando BR-18
```

**Qué cuenta para el acumulado** no se decide aquí por criterio: los **ocho** saldos de
`operations/validators.py` excluyen exactamente `CANCELLED` y nada más. Se sigue ese
precedente. Detalle y la observación sobre `rejected` en
`GA-TD-014_PARTIAL_RECEIPT_MATRIX §2-3`.

## 4. Fuera de alcance

- **Tolerancia de sobre-recepción**: ninguna. Sin fuente normativa, el exceso se rechaza.
- **Cierre automático de la OC**: la decisión no lo aborda. **No se introduce ningún estado**
  de cierre ni se marca la orden como completada. Si hiciera falta, es otro requisito.
- **SAP real**: `SapReference` es la referencia **local**. `GA-REM-017` sigue
  `BLOCKED_EXTERNAL` y no se llama a ningún sistema externo.
- **La unicidad en otros tipos de evento**: se deja como está. `OD-04` responde sobre órdenes
  de compra y recepciones; extenderla sería inventar política.
- `RC-07`, `R-76`, `R-77`, `R-80`, `R-83`, `P-08`, `P-14`.

## 5. Criterios de aceptación

### `AC01` · La primera entrega parcial se acepta
Una recepción con referencia de OC y cantidad menor que la ordenada se registra.

### `AC02` · La segunda entrega parcial contra la misma OC se acepta
Es la decisión `OD-04` hecha prueba. **Repetir la referencia no puede ser motivo de rechazo.**

### `AC03` · El acumulado se calcula sobre el conjunto normativo
Suma de las recepciones no canceladas con la misma referencia. Una recepción **cancelada**
deja de contar.

### `AC04` · Se acepta mientras quepa
`acumulado + nueva ≤ ordenada` se registra.

### `AC05` · Se rechaza el exceso
`acumulado + nueva > ordenada` responde **400** citando `BR-18`, y el mensaje habla de
**cantidad**, no de duplicidad.

### `AC06` · El resto exacto se acepta
`acumulado + nueva = ordenada` se registra. Distingue un `>` de un `>=` mal puesto.

**Puerta de validez.** `AC05` y `AC06` van juntos: con uno solo, un operador mal escrito
pasaría desapercibido.

### `AC07` · El exceso repartido se detecta
900 recibidos y 200 nuevos contra una orden de 1000 se rechaza, **aunque cada recepción por
separado quepa**. Es el caso que la regla anterior no atrapaba.

### `AC08` · El rechazo no deja rastro
Cero eventos nuevos, cero movimientos de aves, cero avance de flujo.

### `AC09` · Pertenencia
La OC se busca **dentro de la compañía del actor**: una referencia de otra empresa se comporta
como inexistente.

**Puerta de validez.** CONTROL y TRATAMIENTO con el mismo actor y la misma petición; lo único
que cambia es de quién es la orden. **Prohibido** un super admin como sujeto negativo.

### `AC10` · La referencia queda trazable
El evento guarda `sap_document_ref`, que es lo que `GA-TD-014` pedía y lo que el comparativo
SAP necesita para dejar de salir vacío.

### `AC11` · Sin tolerancia no documentada
Una unidad por encima se rechaza. No hay margen.

### `AC12` · Sin cierre automático
Alcanzar el 100 % **no** cambia el estado de la `SapReference`. Se comprueba explícitamente
para que nadie lo añada sin requisito.

### `AC13` · La interfaz envía el campo tipado
`OperationFormPage` escribe la orden en `sap_document_ref`. Lo que la pantalla envía llega al
dominio y produce el efecto (`R-47` / `P0-14`).

### `AC14` · La evidencia puede fallar
`GA-REM-016 AC13`. Mutación controlada y revertida sobre el acumulado, sobre el límite y sobre
el borde.

## 6. Una nota sobre concurrencia

Dos recepciones simultáneas podrían leer el mismo acumulado y superar la orden entre ambas.
**No se introduce bloqueo nuevo**: ninguna fuente lo exige y el resto de los saldos del sistema
—mortalidad, huevo, pollito— tienen exactamente la misma propiedad desde siempre.

Se registra como observación para que no se lea como descuido; si el propietario exige la
garantía bajo concurrencia, es un requisito transversal a todos los saldos, no de esta regla.

## 7. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC01`…`AC12` | `backend/tests/test_purchase_order_receipt.py` | integración HTTP |
| `AC13` | revisión del diff + `tsc` | contrato |
| cadena de `P-01`/`P-03`/`P-06` | sus E2E de proceso | `API_E2E` |
| `AC14` | informe de certificación | mutación |

## 8. Definición de terminado

- Los catorce criterios pasan.
- Existe prueba que **falla contra el código actual** por la causa exacta.
- Sensibilidad demostrada y revertida.
- `P-01`, `P-03` y `P-06` **reevaluados uno a uno**, no certificados por alcance.
- Regresión completa sin fallos nuevos.

---

# Enmienda A · la interfaz no presenta una tolerancia que la decisión no admite (2026-09-10 · WAVE B tranche 8 · `R-169`)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-035-A` · `UI CONSISTENCY WITH OD-04` · **Estado** `SPEC_READY` |
| **Hallazgo** | `R-169` (P2): `OperationFormPage.tsx` clasifica la recepción como «diferencia superior al 10 %» frente a la cantidad declarada de la OC (recuadro ámbar) y, al enviar, **inyecta un texto «⚠️ ALERTA …» en `observations`** cuando \|recibido − declarado\| > 10 %. Inventario completo: `audit/remediation/R169_UNSOURCED_TOLERANCE_INVENTORY.md` |
| **Autoridad** | `OD-04`: entregas parciales legítimas; `AC11`: sin tolerancia; `BR-18` en el backend es la única verdad de cantidades. Ninguna fuente de nivel 1-4 define un ±10 %. `CV-F07` de `FUNCTIONAL_COVERAGE_MATRIX` lo contaba como «validación»: error documental |
| **Cambio** | se retiran el recuadro ámbar y la inyección en `observations`, con sus textos es/en; la tarjeta informativa de la OC (cantidad declarada, fecha de despacho, pesos declarados) se conserva **sin umbral**. El backend no cambia |
| **Sin cambio** | `AC01`…`AC14` · `validate_oc_limit` · `R-156` (pesos declarados vs granja, `AOD-20`) · `thermalCurves.ts` (`R-147`/`AOD-19`) |

## A.1 Criterios

| AC | Criterio |
|---|---|
| `AC15` | el formulario de recepción no calcula ni muestra ninguna diferencia porcentual con umbral frente a la cantidad declarada (`pctDiff`, `outOfRange`, `qtyOutOfRange*` no existen) |
| `AC16` | el envío de una recepción no altera `observations` con textos generados por umbral (`sapQtyAlert` no existe); lo que el operador escribe es lo que se persiste |
| `AC17` | la tarjeta de la OC sigue mostrando la cantidad declarada sin veredicto; `BR-18` sigue rechazando el exceso en el backend (`test_purchase_order_receipt.py` 7/7) |

Pruebas: `frontend/src/pages/operations/__tests__/receptionFormContract.test.ts` (contrato estático del formulario) · `test_purchase_order_receipt.py`.
Sensibilidad `S-R169-1`: reintroducir el umbral en el formulario → contrato estático rojo. `S-R169-2` (frontend usa ±10 % mientras el
backend usa la curva): **N/A** — el ±10 % nunca fue de peso; la evaluación de peso ya consume el backend (`AC-FE14`).

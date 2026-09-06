# CERTIFICACIÓN · `GA-TD-014` — RECEPCIÓN CONTRA ORDEN DE COMPRA

**`GA-REM-035`** · `OD-04` `RESOLVED` · 2026-09-06

```
GA-TD-014 = CERTIFIED     R-95 = CERTIFIED (hallazgo nuevo)
OD-04     = RESOLVED
```

---

## 1. La decisión

```
Una misma orden de compra puede recibirse mediante múltiples entregas parciales.
```

De ella se sigue que **repetir la referencia no es un error** y que la protección recae sobre
la **cantidad acumulada**.

## 2. Tres cosas, no una

Al ir al código apareció que activar el campo tipado, por sí solo, no habría protegido nada.

**a) `GA-TD-014` propiamente.** El formulario guardaba la orden en
`extra_data.sap_order_ref`; `sap_document_ref` quedaba nulo y las dos reglas que lo miran
salían por su primera línea.

**b) La regla no protegía lo que debía.** `validate_oc_limit` comparaba **solo la recepción en
curso**:

```python
if oc and oc.quantity is not None and quantity_received > oc.quantity:
```

Tres entregas de 400 contra una orden de 1000 pasaban las tres —cada una menor que 1000— y
sumaban 1200. **El límite acumulado nunca llegó a comprobarse.**

**c) Una regla contradecía la decisión.** `validate_sap_document_unique` rechaza un segundo
evento con la misma referencia. Aplicada a la recepción, prohibiría exactamente lo que `OD-04`
autoriza. Se exime **solo la recepción**: la decisión responde sobre órdenes de compra, y
extenderla a otros tipos de evento sería inventar política.

## 3. Un cuarto hallazgo, encontrado al ejecutar

```
R-95 · P1 · `SapReferenceCreate` no declaraba `quantity`.
```

`SapReference.quantity` existe en el modelo con el comentario «`G-R05`: OC/STO expected
quantity», pero el esquema de importación no la declaraba: Pydantic la descartaba en silencio
y **toda orden importada quedaba sin cantidad ordenada**. Con ella nula, `validate_oc_limit`
sale por su primera línea.

De modo que `BR-18` **no podía dispararse nunca**, estuviera o no poblado el campo tipado.

Es el mismo patrón de `R-47` y `P0-14`: el cliente envía, el esquema descarta, la respuesta es
`2xx` y el dominio nunca se entera. Apareció porque la prueba comprobaba un rechazo concreto y
no llegaba.

## 4. Qué cuenta para el acumulado — por precedente, no por criterio

`operations/validators.py` calcula **ocho** saldos y los ocho excluyen exactamente
`CANCELLED`. Se sigue ese precedente.

**No se trasladó la semántica de `P-15`**, cuyos indicadores cuentan solo lo aprobado: un
control de recepción no puede esperar a la aprobación, porque si tres entregas sin aprobar
suman más que la orden el exceso **ya ocurrió físicamente**.

Sobre `rejected`: podría argumentarse que no debería sumar, pero ningún saldo del modelo lo
excluye, y hacerlo solo aquí dejaría el límite de la OC contando una cosa y el balance de aves
otra. Se anota: si el propietario quiere cambiarlo, es un cambio para **todos** los saldos.

## 5. Lo que no se introdujo

| | |
|---|---|
| tolerancia | **ninguna**. `AC11` comprueba que una unidad de más se rechaza |
| cierre automático de la orden | **no**. `AC12` comprueba que completar el 100 % **no** cambia el estado de la referencia, para que nadie lo añada sin requisito |
| llamada a SAP real | **no**. `SapReference` es la referencia local; `GA-REM-017` sigue `BLOCKED_EXTERNAL` |
| unicidad en otros tipos de evento | intacta |

## 6. Concurrencia — anotada, no resuelta

Dos recepciones simultáneas podrían leer el mismo acumulado y superar la orden entre ambas.
**No se introdujo bloqueo**: ninguna fuente lo exige y **todos** los saldos del sistema
—mortalidad, huevo, pollito— tienen la misma propiedad desde siempre. Si se exige la garantía,
es un requisito transversal, no de esta regla.

## 7. Evidencia

### Fase roja

| Prueba | Con el código anterior |
|---|---|
| segunda entrega parcial | **400** — «El documento SAP ya fue registrado… no pueden duplicarse» (`BR-10`) |
| resto exacto | **400** por la misma causa |
| exceso repartido (900 + 200) | **201** — se aceptaba |
| una unidad de más | **201** |

Los dos primeros fallaban por la regla que `OD-04` contradice; los dos últimos, porque el
límite no era acumulado. Cada uno por su causa.

### Puerta de sensibilidad

| Mutación | Fallan | Restaurado |
|---|:--:|:--:|
| vuelve la unicidad a la recepción | **4** | 7/7 |
| el límite mira solo la recepción en curso | **2** | 7/7 |
| el borde pasa de `>` a `>=` | **4** | 7/7 |

La tercera es la que protege `AC06`: con `>=`, completar la orden exactamente se rechazaría.

`git diff` tras revertir: solo lo previsto.

### Regresión

| | Antes | Después |
|---|---|---|
| Backend | 377 · 49 omitidas | **384 · 49 omitidas · 0 fallos** |
| E2E | 102/102 | **105/105** |
| `tsc` · `vitest` · i18n | — | **PASS · 61/61 · 876 = 876** |

## 8. Veredicto

```
GA-TD-014 = CERTIFIED    ·    14 de 14 criterios de GA-REM-035
```

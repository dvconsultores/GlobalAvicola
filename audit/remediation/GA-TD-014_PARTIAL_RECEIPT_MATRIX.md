# `GA-TD-014` · MATRIZ DE RECEPCIONES PARCIALES

`OD-04` resuelta · 2026-09-06 · antes de tocar código

---

## 1. La regla, con los nombres reales del modelo

| Concepto | Dónde vive |
|---|---|
| cantidad ordenada | `SapReference.quantity`, con `ref_type = PURCHASE_ORDER` y `sap_code = sap_document_ref`, de la compañía del actor |
| cantidad ya recibida | suma de `BirdMovement.quantity` sobre los `OperationalEvent` con el **mismo** `sap_document_ref`, `event_type = BIRD_RECEPTION` |
| nueva recepción | `total_qty` del evento en curso |
| unidad | **aves** en ambos lados. No hay conversión que definir |

```
acumulado + nueva  ≤  SapReference.quantity     →  aceptar
acumulado + nueva  >   SapReference.quantity    →  rechazar
```

## 2. Qué recepciones cuentan — resuelto por precedente, no por criterio

`operations/validators.py` calcula **ocho** saldos y los ocho excluyen exactamente lo mismo:

```python
OperationalEvent.status.not_in([EventStatus.CANCELLED])
```

Sin excepción. El acumulado de una OC sigue ese precedente: **todo lo no cancelado cuenta**.

| Estado | ¿Cuenta? | Por qué |
|---|:--:|---|
| `draft` · `registered` · `pending_review` · `in_review` · `returned` · `corrected` | **sí** | es el criterio de todos los saldos del sistema |
| `approved` y posteriores | **sí** | ídem |
| `rejected` | **sí** | §3 |
| `cancelled` | **no** | único excluido en los ocho precedentes |

> **No se traslada la semántica de `P-15`.** Los indicadores cuentan solo lo aprobado porque
> informan; un **control** de recepción no puede esperar a la aprobación: si tres entregas sin
> aprobar suman más que la orden, el exceso ya ocurrió físicamente.

## 3. Una observación sobre `rejected`, que no se convierte en cambio

Podría argumentarse que una recepción rechazada no debería sumar. **Pero el modelo vigente no
lo excluye en ningún saldo**, y hacerlo solo aquí dejaría el límite de la OC contando una cosa
y el balance de aves otra distinta.

Se sigue el precedente y se anota: si el propietario quiere que lo rechazado deje de contar,
es un cambio para **todos** los saldos, no para esta regla sola.

## 4. Los casos

| # | Caso | Ordenado | Ya recibido | Nueva | Esperado |
|:--:|---|---:|---:|---:|---|
| 1 | primera parcial | 1000 | 0 | 300 | **aceptar** |
| 2 | segunda parcial, misma OC | 1000 | 300 | 250 | **aceptar** — `OD-04` |
| 3 | tercera parcial | 1000 | 550 | 200 | **aceptar** |
| 4 | **resto exacto** | 1000 | 750 | 250 | **aceptar** — distingue `>` de `>=` mal puesto |
| 5 | **una unidad de más** | 1000 | 1000 | 1 | **rechazar** `BR-18` |
| 6 | exceso en la primera | 1000 | 0 | 1200 | **rechazar** |
| 7 | exceso repartido | 1000 | 900 | 200 | **rechazar** — el acumulado lo detecta, la regla anterior no |
| 8 | recepción cancelada previa | 1000 | 300 (+400 cancelada) | 700 | **aceptar** — lo cancelado no cuenta |
| 9 | OC de otra compañía | — | — | — | **rechazar** — no se encuentra |
| 10 | OC desconocida | — | — | — | **aceptar** — sin referencia cargada no hay límite que aplicar |

El caso **7** es el que la regla actual no atrapa: `900 + 200` supera 1000, pero como cada
recepción se compara por separado y `200 ≤ 1000`, hoy pasaría.

## 5. Lo que hay que desactivar

`validate_sap_document_unique` rechaza un segundo evento con la misma referencia para el mismo
lote y tipo. Aplicado a `bird_reception`, **prohibiría las entregas parciales**: es justo lo
contrario de `OD-04`.

```
La unicidad NO se aplica a la recepción contra una orden de compra.
```

Se deja intacta para los demás tipos de evento: `OD-04` responde sobre órdenes de compra y
recepciones, y extender su alcance sería inventar política.

## 6. Lo que no se introduce

| | |
|---|---|
| tolerancia | ninguna. Sin fuente, el exceso se rechaza |
| cierre automático de la OC | no. La decisión no lo aborda y no se inventa un estado |
| llamada a SAP real | no. `SapReference` es la referencia **local**; `GA-REM-017` sigue `BLOCKED_EXTERNAL` |

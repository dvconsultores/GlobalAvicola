# `GA-REM-029` · CONTRATO DE CIERRE DE LOTE

| | |
|---|---|
| **Hallazgos** | `R-73` (contrato) · `R-74` (`BR-05` en la puerta equivocada) |
| **Severidad** | P1 |
| **Proceso** | `P-06` · Pollo de engorde — paso `lot_closure` |
| **Regla** | `BR-05` · `G-09` · `V-04` |
| **Estado** | `IN_PROGRESS` |
| **Antecedente** | `audit/remediation/R73_CLOSE_LOT_CONTRACT_MATRIX.md` |

> Spec propia, no una enmienda a `GA-REM-028`. Aquella cubría la fecha de inicio del lote y
> ya cerró una de las dos causas de `R-73`; ésta cubre el contrato del cierre, que es otra
> cosa y merece sus propios criterios.

---

## 1. Problema

`POST /lots/{lot_id}/close` responde **500 siempre**. La ruta declara implícitamente un lote
y el servicio devuelve un resumen. El endpoint es, además, **el único punto de todo el
backend que pone un lote en `closed`**: mientras falle, ningún lote puede cerrarse y el paso
terminal de `P-06` es inalcanzable.

Al reconstruir el contrato aparece un segundo defecto: la precondición de `BR-05` —pesaje y
alimento, sin los cuales no hay FCR— se valida en el evento `lot_closure`, que **no cierra
nada**, y no en el endpoint, que sí. La guarda existe y vigila una puerta que no lleva a
ninguna parte.

## 2. Fuera de alcance

- El evento `lot_closure` como tipo de evento operativo: se queda como está.
- `LotRead` y el resto de endpoints de lotes.
- La confirmación por modal en la interfaz (`docs/15` `G-09`): es un hueco de interfaz
  aparte, y se anota, no se resuelve aquí.

## 3. Criterios de aceptación

### `AC01` · El cierre responde
`POST /lots/{lot_id}/close` sobre un lote activo con pesaje y alimento devuelve **200**.
Prueba por HTTP, no por servicio.

### `AC02` · El contrato está declarado
La ruta declara `response_model=LotClosureSummary`. El esquema existe, es explícito y sus
campos son los nueve de la matriz §3. Una futura divergencia entre servicio y ruta debe
romper en validación, no pasar inadvertida.

### `AC03` · El resumen dice la verdad
Con un lote que tiene mortalidad, alimento, huevos y eventos aprobados conocidos, cada campo
del resumen coincide con lo registrado. **Prohibido** aceptar ceros como prueba: el escenario
debe producir valores distintos entre sí y de cero, y la comprobación debe ser por igualdad
contra la cifra esperada.

### `AC04` · El lote queda cerrado y persistido
Tras el 200, una lectura **posterior e independiente** del lote devuelve `status = "closed"`
y `end_date` con la fecha del cierre. Se comprueba releyendo por HTTP, no sobre el objeto en
memoria de la misma petición.

### `AC05` · `BR-05` protege el cierre real
`POST /lots/{id}/close` sobre un lote **sin pesaje** responde **400** citando `BR-05`; ídem
sin registro de alimento. Reutiliza `validate_lot_closure`, sin duplicar la regla.

> Cambio de comportamiento consciente: un lote que hoy se cerraría sin FCR dejará de poder
> hacerlo. Se asume porque la regla ya está escrita, ya se aplica en el camino hermano y el
> audit la daba por vigente aquí. Queda declarado en el informe.

### `AC06` · No se cierra dos veces
Un segundo `POST .../close` sobre un lote ya cerrado responde **400**, y el `end_date` del
primer cierre **no cambia**. Se comprueba releyendo la fecha después del segundo intento.

### `AC07` · Aislamiento entre empresas
Un usuario de otra empresa **con permiso `lots:create`** recibe **404** al cerrar un lote
ajeno, y el lote sigue `active`.

**Puerta de validez.** No vale un `not.toBe(200)`: hay que demostrar CONTROL y TRATAMIENTO.
- CONTROL — el mismo usuario cierra un lote **de su propia empresa** → 200.
- TRATAMIENTO — el mismo usuario contra el lote ajeno → 404.

**Prohibido** usar un super admin como sujeto negativo: está exento por diseño (`R-36`) y la
prueba no mediría nada.

### `AC08` · La edad es de negocio
`age_days` se calcula desde `start_date` como fecha, no como marca temporal, y coincide con
la diferencia declarada. Es la regresión de `R-47`: `GA-REM-028 AC07` tuvo que comprobarse
en el servicio porque este endpoint estaba roto; con `AC01` en pie, se comprueba por HTTP.

### `AC09` · Sin permiso no se cierra
Un usuario sin `lots:create` recibe **403** y el lote sigue `active`.

## 4. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC01` `AC03` `AC04` `AC08` | `backend/tests/test_lot_closure.py` | integración HTTP |
| `AC02` | `backend/tests/test_lot_closure.py` — introspección de la ruta | contrato |
| `AC05` `AC06` `AC09` | `backend/tests/test_lot_closure.py` | integración HTTP |
| `AC07` | `backend/tests/test_lot_closure.py` — CONTROL + TRATAMIENTO | integración HTTP |
| cadena `P-06` | `e2e/proceso-p06-pollo-de-engorde.spec.ts` | E2E |

## 5. Definición de terminado

- Los nueve criterios pasan.
- La cadena de `P-06` se recorre entera de extremo a extremo.
- Regresión completa sin fallos nuevos.
- `R-74` documentado como hallazgo con su propia entrada, no absorbido en silencio.

# `GA-REM-031` · CREACIÓN DEL VÍNCULO GENERACIONAL DESDE LA RECEPCIÓN

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-031` · `DOMAIN DEFECT SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Hallazgo** | `R-78` |
| **Proceso** | `P-10` · Trazabilidad generacional — pasos 3, 4, 7 y 8 |
| **Dependencias** | `GA-REM-008` `CERTIFIED` (rama de despacho) · `GA-REM-030` `CERTIFIED` (pertenencia) |
| **Antecedente** | `audit/remediation/P10_LINEAGE_BRANCH_MATRIX.md` |

> Spec propia y no enmienda de `GA-REM-008`. Aquella certificó la rama del **despacho**;
> ninguno de sus criterios habla de la recepción como origen del vínculo. `GA-REM-008` queda
> `CERTIFIED` y sin modificar, salvo la anotación de `AC01` que corresponde a `R-79`.

---

## 1. Requisito de negocio

`spec.md §4.9`:

> Un `EggBatch` se crea **automáticamente** al registrar `egg_dispatch` +
> `egg_reception_hatchery`.
> Un `ChickBatch` se crea **automáticamente** al registrar `chick_dispatch` +
> `bird_reception`.

La conjunción es simétrica. **La spec no impone orden**, y la operación real despacha antes
de recibir.

## 2. El defecto

La creación vive **solo** en la rama del despacho, que busca una recepción ya existente. Las
dos ramas de recepción se limitan a actualizar un vínculo previo:

```python
elif event.event_type == models.EventType.EGG_RECEPTION_HATCHERY:
    dispatch = await self._despacho_dirigido_a_este_lote(...)
    if dispatch:
        batch = ...where(EggBatch.dispatch_event_id == dispatch.id)...
        if batch:                      # ← si no existe, no crea: se ignora
            batch.quantity_received = ...
```

En el orden natural:

```
despacho  → busca recepción → todavía no existe → no crea
recepción → encuentra el despacho → busca el vínculo → no existe → no hace nada
RESULTADO: ningún vínculo, nunca
```

Medido en la pila real: la cadena de tres generaciones produce **0 vínculos**.

## 3. Invariante

```
CUANDO   una recepción válida establece una relación generacional
Y        el vínculo exigido no existe todavía
ENTONCES el sistema lo crea exactamente una vez
```

Con el mismo origen, destino y pertenencia que habría producido la rama del despacho — no
por parecido de código, sino porque `P10_LINEAGE_BRANCH_MATRIX §2` demuestra que las dos
ramas ya comparten filtros, semántica de pertenencia y señal de emparejamiento; la única
diferencia material es la acción.

## 4. Fuera de alcance

- La rama del despacho: certificada, intacta.
- El contrato de la API: ni esquema de petición, ni de respuesta, ni ruta.
- La señal de emparejamiento (`destination_farm_id`).
- El enlace manual y su guarda (`GA-REM-030`).
- `R-76`, `R-77`, `OD-04`, `GA-TD-014`.

## 5. Criterios de aceptación

### `AC01` · La recepción crea el vínculo ausente
Registrado el despacho con destino declarado y **después** la recepción en el lote destino,
existe un `EggBatch` — y su equivalente `ChickBatch` — con el origen y el destino correctos.

**Puerta de validez.** Antes de la recepción se comprueba que **no** hay vínculo; después,
que lo hay. Sin la comprobación previa, la aserción posterior no distingue creación de
preexistencia.

### `AC02` · Exactamente uno
Tras la pareja completa hay **un** vínculo, no dos. Ni la creación desde el despacho ni la
creación desde la recepción producen un duplicado del otro lado.

### `AC03` · Orientación correcta
`source_lot_id` es el lote que despachó y `hatchery_lot_id` el que recibió; análogamente
`hatchery_lot_id` → `destination_lot_id` para el pollito. **Un recuento de uno no basta**: el
vínculo debe apuntar a las entidades correctas.

### `AC04` · Cantidades y fechas de ambos lados
El vínculo creado desde la recepción registra la cantidad y la fecha **despachadas** —del
evento de despacho— y las **recibidas** —del evento de recepción—. Es el paso 4 de la cadena,
hoy sin cubrir.

### `AC05` · Referencia a la generación anterior
El `ChickBatch` creado desde la recepción referencia el `EggBatch` del que procede
(`egg_batch_id`), como ya hace el creado desde el despacho. Es el paso 7, hoy sin cubrir.

### `AC06` · Pertenencia
El vínculo queda bajo la compañía correcta. Un actor **con permiso** no produce vínculos que
alcancen lotes de otra compañía.

**Puerta de validez.** CONTROL y TRATAMIENTO con el mismo sujeto y la misma operación; lo
único que cambia es de quién es el lote. **Prohibido** un `!= 201`. **Prohibido** usar un
Super Admin como sujeto negativo: tiene exención por diseño.

### `AC07` · Sin efectos tras la denegación
Cero vínculos, cero mutación de saldos, cero avance de flujo.

### `AC08` · Lectura inmediata
`R-68`: tras la recepción, una consulta posterior del árbol ve el vínculo sin esperas.

### `AC09` · La rama del despacho no se altera
Las cuatro pruebas de `GA-REM-008` siguen en verde, y el orden inverso —recepción antes que
despacho— sigue produciendo un vínculo y solo uno.

## 6. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC01`…`AC05` `AC08` | `backend/tests/test_reception_lineage.py` | integración HTTP |
| `AC06` `AC07` | ídem, CONTROL + TRATAMIENTO | integración HTTP |
| `AC09` | `backend/tests/test_traceability.py` | regresión |
| cadena de `P-10` | `e2e/proceso-p10-trazabilidad-generacional.spec.ts` | `API_E2E` |

## 7. Definición de terminado

- Los nueve criterios pasan.
- Existe una prueba que **falla contra el código actual** por la causa exacta —el vínculo no
  existe tras una recepción válida— y no por autenticación, permiso, fixture ni esquema.
- Sensibilidad demostrada por mutación controlada y revertida.
- La cadena de `P-10` se recorre entera y el `test.fail()` que documenta `R-78` se retira.
- Regresión completa sin fallos nuevos.

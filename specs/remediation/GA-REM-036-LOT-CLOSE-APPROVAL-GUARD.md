# `GA-REM-036` · APROBACIÓN OBLIGATORIA ANTES DEL CIERRE DE LOTE

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-036` · `BUSINESS RULE SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Hallazgo** | `R-76` |
| **Regla** | `docs/12 §6 R7` |
| **Proceso** | `P-06` · Pollo de engorde — paso de cierre |
| **Dependencias** | `GA-REM-029` `CERTIFIED` (`R-73`/`R-74`/`R-75`) · `GA-REM-007` (segregación) |
| **Antecedente** | `audit/remediation/R76_LOT_CLOSE_APPROVAL_MATRIX.md` |

> `R-76` no tenía spec: figuraba en el backlog y quedaba expresamente **fuera de alcance** de
> `GA-REM-030` y `GA-REM-035`. Esta es su primera.

---

## 1. La regla

`docs/12 §6`:

> **R7** — Un lote no puede cerrarse si tiene registros sin aprobar.

## 2. Qué gobierna, acotado

**Registro** = `OperationalEvent` del lote. `docs/12 §4` se titula «Estados del registro
operativo» y el documento entero trata de esa entidad. No se generaliza a «nada pendiente en
ningún sitio»: correcciones y acciones de aprobación son artefactos del propio flujo.

**Sin aprobar** = cualquiera de los siete estados anteriores a la aprobación, más el rechazo:

```
draft · registered · pending_review · in_review · returned · corrected · rejected
```

**No bloquean**: `approved`, `consolidated`, `sent_to_sap`, `sap_confirmed`, `sap_error` y
`cancelled`. Justificación estado por estado en la matriz §3-6. Los dos que merecen decirse:

- **`rejected` bloquea.** No está aprobado, y `docs/12 §4` muestra que no es terminal
  —`Rechazado → Registrado`, «el operador reenvía corregido»—, de modo que el lote no queda
  atrapado.
- **`sap_error` no bloquea.** Solo se alcanza tras haber sido aprobado y consolidado. `R7` es
  una regla de aprobación, no de integración.

## 3. Fuera de alcance

- **`BR-05`**: es otra regla —¿hay base para el resumen final?— y se queda como está. No se
  fusionan por compartir función ni se amplía su alcance.
- El contrato de respuesta de `close_lot`: `R-73` lo certificó y no se toca.
- `R-77`, `R-69`, `R-70`, `R-80`, `R-83`.
- `P-03`, `P-08`, `P-14`, `GA-REQ-037`.

## 4. Criterios de aceptación

### `AC01` · Con todo aprobado, el lote cierra
Un lote cuyos eventos están todos en un estado no bloqueante se cierra con `200`, siempre que
las demás condiciones se cumplan.

**Es el CONTROL**: sin él, un rechazo posterior no probaría nada.

### `AC02` · Un solo registro sin aprobar lo impide
Con **exactamente un** evento en estado bloqueante, `POST /lots/{id}/close` responde `400`
citando **`R7`**.

**Puerta de validez.** CONTROL y TRATAMIENTO sobre el mismo lote y la misma llamada; lo único
que cambia es el estado de ese registro. **Prohibido** un `!= 200`: se comprueba la regla
citada.

### `AC03` · Los siete estados bloqueantes bloquean
Parametrizado sobre `draft`, `registered`, `pending_review`, `in_review`, `returned`,
`corrected` y `rejected`.

### `AC04` · Los seis no bloqueantes no bloquean
Parametrizado sobre `approved`, `consolidated`, `sent_to_sap`, `sap_confirmed`, `sap_error` y
`cancelled`. **Un tipo de registro o un estado que `R7` no gobierna no puede impedir el
cierre**: una regla que bloquea de más es tan defectuosa como una que no bloquea.

### `AC05` · La negativa precede a cualquier mutación
El rechazo ocurre **antes** de tocar `status` o `end_date`.

### `AC06` · Sin efectos tras la negativa
`status` sigue `active`, `end_date` sigue nulo, no se crea ningún evento de cierre, no se
altera ningún saldo.

### `AC07` · Pertenencia
Solo cuentan los eventos **de ese lote y de esa compañía**. Un registro de otra empresa no
influye.

### `AC08` · Aprobar desbloquea, sin esperas
Tras aprobar el registro que bloqueaba, el mismo lote cierra de inmediato (`R-68`, sin
`sleep`). Demuestra que la guarda no deja el lote atrapado.

### `AC09` · `BR-05` sigue vigente
La guarda nueva no desplaza a la anterior: un lote sin pesaje ni alimento sigue sin poder
cerrarse, citando `BR-05`.

### `AC10` · El cierre certificado no regresa
`R-73` (el resumen), `R-74` (`BR-05` en la puerta real) y `R-75` (la fecha) siguen en verde.

### `AC11` · La evidencia puede fallar
`GA-REM-016 AC13`. Mutación controlada y revertida: retirada la guarda, el caso de `AC02`
vuelve a rojo.

## 5. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC01`…`AC09` | `backend/tests/test_lot_close_approval.py` | integración HTTP |
| `AC10` | `backend/tests/test_lot_closure.py` | regresión |
| cadena de `P-06` | `e2e/proceso-p06-pollo-de-engorde.spec.ts` | `API_E2E` |
| `AC11` | informe de certificación | mutación |

## 6. Definición de terminado

- Los once criterios pasan.
- Existe prueba que **falla contra el código actual** por la causa exacta —el lote cierra
  teniendo un registro sin aprobar— y no por `BR-05`, autenticación, permiso ni fixture.
- Sensibilidad demostrada y revertida.
- `P-06` reevaluado **leyendo `§4.8` de nuevo**, no por transitividad.
- Regresión completa sin fallos nuevos.

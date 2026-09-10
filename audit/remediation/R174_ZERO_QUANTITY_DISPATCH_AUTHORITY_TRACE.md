# `R-174` · Traza de autoridad: despacho de pollitos con cantidad 0 (`R174_ZERO_QUANTITY_DISPATCH_AUTHORITY_TRACE`)

**WAVE B · tranche 10 · pre-flight** · 2026-09-10 · hallazgo `R-174` (P3, registrado en el pre-flight del tranche 9) · spec gobernante `GA-REM-005-B`.

## 1. Hallazgo exacto

> `R-174` · P3 · «`chick_dispatch` con cantidad 0 se acepta: `if total_qty > 0` salta `validate_chick_dispatch` (residuo de la clase `R-130 AC04`)» ·
> `service.py:883` · `REMEDIATION_BACKLOG.md:1080`.

Código leído (`_apply_business_rules`, `service.py:880-884`):

```python
elif event_type == models.EventType.CHICK_DISPATCH:
    if total_qty > 0:
        if data.lot_id is None: raise BusinessRuleViolation("El evento requiere lote", "BR-07")
        await validate_chick_dispatch(self.db, data.lot_id, total_qty)
```

`validate_chick_dispatch` (`validators.py:244-256`) **ya** rechaza `quantity <= 0` con `BR-04` («La cantidad de pollitos debe ser mayor a cero») y bloquea
la fila del lote; la guarda del servicio impide que se ejecute cuando la suma es 0, y el evento se persiste (fila en `operational_events`, movimiento de
0, auditoría `created`, notificación, fila en la cola de revisión).

## 2. ¿Existe regla gobernada «decremento productivo > 0»? — sí, y nombra al despacho de pollitos

| Nivel | Fuente | Texto |
|---|---|---|
| 4 | `GA-REM-005-B §B.2` (certificada, `R-130`) | «**INVARIANTE para todo decremento `D ∈ {mortalidad, descarte, salida, despacho de pollitos}`**: `cantidad(D) > 0 ∧ cantidad(D) ≤ SALDO(lote) antes de D ⇒ SALDO después ≥ 0`, evaluado bajo bloqueo de la fila del lote» |
| 4 | `GA-REM-005-B §B.3` | fila «descarte / salida = 0 → **`400 BR-01` («debe ser mayor a cero»)**» (la tabla no lista la fila del despacho de pollitos: la enmienda E la añade, no la inventa: la regla de `B.2` ya lo incluye) |
| 4 | `GA-REM-005 §E.3` | las **cuatro** salidas del saldo: `mortality_recording · cull_recording · bird_exit · chick_dispatch` |
| 4 | `GA-REM-005-B` `AC-R130-04` | cantidad 0 rechazada (mortalidad, descarte, salida) |
| 4 | `GA-REM-005-D §D.1.4` | «El servicio **no** salta la validación por cantidad 0: la regla la rechaza (`BR-02`/`BR-03` «mayor a cero»), como `R-130 AC04`» — mismo principio para huevos |
| 5 | `validate_chick_dispatch` | `quantity <= 0 → BR-04` (la regla existe; el servicio la esquiva) |

**No es analogía**: `B.2` enumera explícitamente «despacho de pollitos» dentro del conjunto `D` al que exige `cantidad(D) > 0`. La regla es compartida
(un invariante para las cuatro salidas), no una extensión desde `R-161`.

## 3. Por qué importa el cero (`§38`)

Un `chick_dispatch` de 0 no mueve el saldo, pero **sí** crea: fila en `operational_events` (estado `REGISTERED`), `bird_movements` de 0, auditoría
`created`, notificación, entrada en la cola de revisión, fila de `chick_batches` si casa con una recepción (`_auto_create_batches`), y un evento más en
todo denominador/numerador que cuente despachos (eficiencia de traslado, `KPI_FORMULA… §4`). La fuente exige `> 0` → rechazo **antes** de persistir:
`400 BR-04` (código de dominio existente), sin fila, sin auditoría de éxito, sin efecto.

## 4. Consistencia con `R-130` (`§39`)

El validador existente **es** el que hay que dejar correr; no se crea ningún validador de cantidad nuevo ni se fuerza `validate_bird_decrement` sobre el
despacho (su regla es `BR-04` con viables, no `BR-01`). Cambio mínimo: retirar `if total_qty > 0:` de la rama `CHICK_DISPATCH` (como hizo `GA-REM-005-D`
con `egg_dispatch`/`incubation_load`). Cantidad negativa: `422` por esquema (`quantity: int = Field(ge=…)`? — se comprueba en la prueba `AC-R174-02`
y se registra el código real).

## 5. Clasificación y puerta

```
R-174 ............ ACTIVE · GOBERNADO (GA-REM-005-B B.2 nombra al despacho de pollitos en D) · SIN DECISIÓN · P3 → ejecutable
fix .............. service.py: rama CHICK_DISPATCH sin la guarda `if total_qty > 0` (el validador rechaza 0 con BR-04)
migración ........ ninguna · frontend: ninguno (el backend es la autoridad; el formulario ya exige cantidad)
spec ............. GA-REM-005 enmienda E (§E.b): fila «despacho de pollitos = 0 → 400 BR-04» en B.3; AC-R174-01…05
```

## 6. AC → prueba

| AC | Qué | Prueba (`tests/test_edit_cancel_balance.py`, sección R-174) |
|---|---|---|
| `AC-R174-01` | despacho de 0 → `400 BR-04`; **cero filas** en `operational_events`/`bird_movements`; sin auditoría `created`; sin notificación; viables intactos | rojo |
| `AC-R174-02` | cantidad negativa → denegada (código real del esquema: se registra) | control |
| `AC-R174-03` | despacho de 1 con viables 100 → `201` | control |
| `AC-R174-04` | despacho del resto exacto → `201`; viables 0 | control |
| `AC-R174-05` | despacho de resto + 1 → `400 BR-04`, sin fila | control (`R-130`) |

Sensibilidad `R174-S1`: restaurar la guarda `if total_qty > 0` → `AC-R174-01` roja (evento de 0 persistido: se observa la fila, no solo la respuesta).

# GA-FE-06 · TRAZABILIDAD SLA — «LOTE PRÓXIMO A CIERRE»

## Regla exacta (código vigente)

`backend/app/notifications/sla.py::evaluar_lotes_proximos_a_cierre` (`AC-C05…AC-C14`, `docs/02 §3.14`, `OD-08`):

```
ventana:   0 <= ( planned_close_date(día) − hoy(día) ) <= 3      (DIAS_PARA_CIERRE = 3)
selección: Lot.planned_close_date IS NOT NULL  AND  Lot.status == "active"
exclusiones: sin fecha (no se inventa referencia) · lote no activo · fecha ya pasada
tipo aviso: "lot_near_close"
ocurrencia: lot:{lot_id}:{YYYY-MM-DD de la fecha prevista}   (replanificar ⇒ aviso nuevo; reevaluar ⇒ no duplica)
destinatarios: resolver_destinatarios(company_id, area_id=lote.area_id, originadores=[quien registró el lote])
payload aviso: {lot_id, lot_code, planned_close_date (ISO), days_remaining}
```

- Comparación **día natural vs día natural** (comentario explícito: `R-75` aplica; `R-80` —mezclar instante UTC con día local— **no interviene**).
- La ventana reemplaza a la igualdad `== 3` («con igualdad, un aviso que no corre ese día no sale nunca»).
- Consumidor: **notificaciones** (tabla `notifications`, `crear_notificacion` idempotente por ocurrencia); no hay cálculo en React.
- `area_id` del lote participa en la resolución de destinatarios (gerente/supervisores por `User.area_id`).

## Propiedad del cálculo

100% backend (evaluador sin sesión + `crear_notificacion`). **R-182 no modifica esta lógica** (§64): el defecto es de **datos de origen** (la UI nunca enviaba la fecha prevista).

## Verdad de pruebas canónicas

`tests/test_lot_planned_close.py` (PG, corre en CI; local `skipped` sin base de pruebas) fija: ventana `0..3`, `planned_close_date` = «lo pone quien planifica» vs `end_date` = «cuándo se cerró de verdad», y la fecha de negocio vía `tests/time_reference.reference_today()` (± días). GA-FE-06 añade evidencia runtime autenticada de que un lote **creado por UI** participa en la ventana.

## Escenarios de certificación derivados (sin inventar umbrales)

| Escenario | `planned_close_date` | Estado esperado (regla vigente) |
|---|---|---|
| Fuera (lejos) | hoy + 10 | NO entra (`faltan=10 > 3`) |
| Frontera | hoy + 3 | **ENTRA** (`faltan=3`) |
| Dentro | hoy + 1 | **ENTRA** (`faltan=1`) |
| Hoy | hoy + 0 | **ENTRA** (`faltan=0`) |
| Pasada | hoy − 1 | NO entra (`faltan<0`) |
| NULL | — | NO entra (excluido por contrato) |
| Lote cerrado (`status != active`) | dentro de ventana | NO entra |

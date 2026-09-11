# GA-R184 · EVIDENCIA RED (pre-implementación)

Generación de entrada: backend `5a5bb3f` (producto) · HEAD documental `2dc10b7` · bundle `index-BUthrUt9.js` (LM 2026-09-11 15:46:08 GMT).

## 1 · RED runtime autenticado (capturado y ejecutado)

Actor: autoridad global con empresa 1 efectiva (`switch-company`) y ventana BU `broiler` **ON** (temporal, restaurada en limpieza).
Fixtures: lotes reales de pruebas anteriores con `start_date` no nulo (p. ej. 35 `GA6A-GREEN-NOBU-202609111423`, 33 `GA6A-GREEN-NULL-…`).

| Caso | Petición | Resultado observado | Target post-fix |
|---|---|---|---|
| **RED-1** (defecto original) | `GET /reports/kpi/ipe/35` | **HTTP 500** `Internal Server Error` | 200 con `ipe` numérico |
| **RED-2** (segunda muestra) | `GET /reports/kpi/ipe/33` | **HTTP 500** | 200 |
| Control A | `GET /reports/kpis?lot_id=35` | 200 | 200 (sin cambio) |
| Control B | `GET /reports/kpi/weight-uniformity/35` | 200 | 200 (sin cambio) |
| **RED-3** (lote inexistente) | `GET /reports/kpi/ipe/999999` | **404** «Lote no encontrado» | 404 (ya correcto, no 500) |
| **Hermano registrado** | `GET /reports/kpis/production-index?lot_id=35` | **HTTP 500** (misma clase; **candidato R-186, NO se corrige en R-184**) | (tranche propia) |

Artefacto completo: `evidence/red/runtime-red.json` (actor, baseline, cada caso con status y cuerpo).

## 2 · RED determinista local (expresión exacta, modelo real)

Script ejecutado contra `app.masters.models.Lot` (instancia del modelo real, sin persistencia):

```
start_date: datetime.datetime(2026, 8, 23, 0, 0, tzinfo=datetime.timezone.utc) -> datetime tz: UTC
hoy: datetime.date(2026, 9, 11) -> date
PRE-FIX TypeError: unsupported operand type(s) for -: 'datetime.date' and 'datetime.datetime'
  operando izq: date | operando der: datetime
POST-FIX edad: 19 -> int
REPRO-DONE
```

Artefacto: `evidence/red/typeerror-local.txt`.

## 3 · RED de suite (canónico, PostgreSQL)

`backend/tests/test_r184_ipe_date_semantics.py` — con el código actual:

- `test_..._ipe_valido_200_y_valor_determinista`: espera 200 + 33333.3 ⇒ recibe **500** ⇒ **falla (RED)**.
- `test_..._hoy_y_sin_inicio`: espera 200 ⇒ **500** ⇒ falla (RED).
- `test_..._estable`, seguridad (403/404), BU OFF ⇒ fallan por el 500 previo en la ruta feliz (RED).

En local sin PostgreSQL/credenciales de siembra la suite queda **`skipped`** (declarado, mecanismo `test_credentials`/`GA_TEST_ADMIN_PASSWORD`); corre en CI con `scripts/run_tests.sh`. Misma doctrina que GA-FE-06/06-A/07: la evidencia RED **ejecutada** es §1/§2 (runtime + expresión real).

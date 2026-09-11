# GA-R186 · EVIDENCIA RED (pre-implementación)

Generación de entrada: backend `3f88f94` (producto) · HEAD documental `2f9483f` · bundle `index-BUthrUt9.js`.

## 1 · RED original (heredado, inmutable)

`audit/ga-r184/evidence/red/runtime-red.json` — caso `prodindex35` (capturado 2026-09-11, commit `304174d`):
`GET /reports/kpis/production-index?lot_id=35` → **HTTP 500** `Internal Server Error` (lote 35 con `start_date`, actor autoridad global, ventana BU ON). Controles de la misma captura: `kpis?lot_id=35` 200 · `weight-uniformity/35` 200 · `ipe/35` 500 (defecto hermano entonces).

## 2 · RED determinista local (expresión exacta, modelo real)

`evidence/red/typeerror-local.txt`:

```
start_date: datetime.datetime(2026, 8, 23, 0, 0, tzinfo=datetime.timezone.utc) -> datetime tz: UTC
hoy: datetime.date(2026, 9, 11) -> date
PRE-FIX TypeError: unsupported operand type(s) for -: 'datetime.date' and 'datetime.datetime'
  operando izq: date | operando der: datetime
POST-FIX edad: 19 -> int
PI esperado (calculo independiente): 400.0 -> redondeado 1d: 400.0
REPRO-R186-DONE
```

## 3 · RED de suite (canónico, PostgreSQL)

`backend/tests/test_r186_g05_date_semantics.py` — con el código actual:

- `test_r186_ac06_ac08_determinista`: espera 200 + `production_index` 400.0 ⇒ recibe **500** ⇒ **falla (RED)**.
- `test_r186_ac14_hoy_sin_clamp`, `..._ac16_...`, `..._ac23_...`, `..._estable` y las de seguridad (ruta feliz/404/403/BU-OFF): fallan por el 500 previo en la ruta con `start_date` (RED).

En local sin PostgreSQL/credenciales de siembra la suite queda **`skipped`** (declarado, mecanismo `test_credentials`); corre en CI con `scripts/run_tests.sh`. Misma doctrina que R-184/GA-FE: la evidencia RED **ejecutada** es §1/§2 (runtime heredado + expresión real).

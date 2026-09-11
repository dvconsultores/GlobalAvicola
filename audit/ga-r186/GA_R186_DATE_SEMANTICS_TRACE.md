# GA-R186 · TRAZA DE SEMÁNTICA TEMPORAL (G-05)

## 1 · Campos temporales del endpoint

| Campo | Tipo modelo | Tipo Python runtime | Nulable | Zona | Significado |
|---|---|---|---|---|---|
| `Lot.start_date` | `DateTime(timezone=True)` (`masters/models.py:302`) | `datetime` aware (UTC anclado por `_inicio_declarado`) | Sí | UTC | Día de inicio del ciclo (día de calendario) |
| `date.today()` | — | `datetime.date` | — | Local del proceso; simulable en tests (`GA_TEST_SIMULATED_TODAY`, R-28) | «Hoy» del negocio |
| `age_days` | Calculado | `int` | No | — | Edad del lote en días de calendario |
| Eventos (`event_date`), `created_at`, `end_date`, `planned_close_date` | — | — | — | — | **No participan** del cálculo G-05 (solo los pesos se agregan por lote, sin corte temporal) |

## 2 · La expresión fallida (probada)

`service.py:604`: `age_days = (date.today() - lot.start_date).days if lot and lot.start_date else 30`

| Operando | Valor | Tipo |
|---|---|---|
| Izquierdo | `2026-09-11` | `datetime.date` |
| Derecho | `datetime(2026, 8, 23, 0, 0, tzinfo=timezone.utc)` | `datetime` aware |
| Operación | `date − datetime` | **TypeError** (clase R-184; repro local en `evidence/red/typeerror-local.txt`) |

## 3 · Dominio temporal canónico

**DATE (día de calendario)** — misma convención ya canonizada que G-06 y que `lots/service.py:379` / `operations/service.py:776`; el helper `_dia(...)` (R-75 / GA-REM-028) ya está importado en `reports/service.py` desde R-184 ⇒ **reutilización directa, sin helper nuevo**.

## 4 · Convención de conteo (preservada, sin cambios)

| Caso | Comportamiento actual (contrato) | Acción R-186 |
|---|---|---|
| Multi-día | `(hoy − día_inicio).days` | Preservar |
| Mismo día | `0` días ⇒ guarda `(age_days × fcr) > 0` falsa ⇒ `production_index = 0` (**sin clamp**; distinto de G-06, que clampa a 1) | Preservar |
| Sin `start_date` | fallback **30** | Preservar |
| Fecha futura | edad negativa ⇒ guarda falsa ⇒ `production_index = 0` | Preservar |

Sin off-by-one: ambos lados normalizados a día de calendario (R186-AC13).

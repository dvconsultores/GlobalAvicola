# GA-R184 · TRAZA DE SEMÁNTICA TEMPORAL

## 1 · Campos temporales inventariados (verificados, no supuestos)

| Campo | Modelo/columna | Tipo Python | Tipo API | Nulable | Zona | Significado de negocio |
|---|---|---|---|---|---|---|
| `Lot.start_date` | `app/masters/models.py::Lot` → `DateTime(timezone=True)` | `datetime` (aware) | ISO 8601 (entrada se normaliza a medianoche UTC con `_inicio_declarado`, `lots/service.py:34`) | Sí | UTC anclado | Día de inicio del ciclo (día de calendario) |
| `Lot.end_date` | íd. `DateTime(timezone=True)` | `datetime` aware | ISO | Sí | UTC anclado (`_fecha_de_negocio`) | Fecha real de cierre |
| `Lot.planned_close_date` | íd. `DateTime(timezone=True)` | `datetime` aware | ISO (se muestra `slice(0,10)` en FE) | Sí | UTC anclado | Cierre previsto — **no participa del IPE** |
| `Lot.created_at/updated_at` | `DateTime(timezone=True)` server default | `datetime` aware | — | No | UTC | Metadatos |
| `OperationalEvent.event_date` | `app/operations/models.py` | fecha/`datetime` según columna | ISO | Según columna | negocio | Fecha del registro (no usada por IPE salvo por los agregados de mortalidad/peso/alimento que filtran por lote, no por fecha) |
| `date.today()` | `datetime.date` | `date` | — | — | Local del proceso | «Hoy» del negocio; simulable en tests (`GA_TEST_SIMULATED_TODAY`, R-28) |
| `age_days` | Calculado | `int` | número | No | — | Edad del lote en días de calendario |

## 2 · La expresión fallida (probada, no supuesta)

`app/reports/service.py::get_kpi_ipe`:

```python
age_days = (date.today() - lot.start_date).days if lot and lot.start_date else 30
```

| Operando | Valor observado (runtime/test) | Tipo |
|---|---|---|
| Izquierdo | `2026-09-11` | `datetime.date` |
| Derecho | `datetime.datetime(2026-08-23, 0, 0, tzinfo=datetime.timezone.utc)` | `datetime` aware (UTC) |
| Operación | `date − datetime` | **TypeError** |
| Mensaje exacto | `unsupported operand type(s) for -: 'datetime.date' and 'datetime.datetime'` | — |
| Ubicación | `service.py` línea 647 (pre-fix) | — |

Reproducción local determinista (modelo real, sin BD): `evidence/red/typeerror-local.txt`.
Con la normalización canónica la segunda evaluación devuelve `19` (`int`) sin excepción.

## 3 · Por qué ocurre sólo con `start_date` presente

La rama `else 30` convierte el caso «lote sin inicio declarado» en un resultado numérico silencioso. Como **toda alta nueva fija `start_date`** (`lots/service.py:245` `_inicio_declarado(...)`), el 100 % de los lotes creados por el flujo real alcanzan la resta fallida. No hubo cambio de serialización ni de columna: el defecto convive con los datos actuales.

## 4 · Dominio temporal canónico del IPE

- La edad del IPE es un **conteo de días de calendario** (no una duración de instantes):
  - Convención ya canonizada y duplicada en dos módulos: `lots/service.py:379` y `operations/service.py:770-776` — ambas normalizan con `_dia(...)` (o su copia local) antes de restar contra `date.today()`.
  - `R-75`/`GA-REM-028`: las columnas son `DateTime(timezone=True)` y la base corre en CET; las fechas de negocio se anclan a medianoche UTC para que petición, persistencia y respuesta hablen del **mismo día del calendario**.
- Por tanto: **DATE (día de calendario) es el dominio del término edad**, y la normalización correcta es `_dia(lot.start_date)` — no convertir `today` a datetime, no `datetime.combine` arbitrario, no `.date()` disperso sin contrato.

## 5 · Convención de conteo (sin off-by-one)

| Regla | Valor | Fuente |
|---|---|---|
| Día de cálculo | `date.today()` | convención vigente (`lots/service.py:379`; simulable en tests) |
| Inicio | día de calendario de `start_date` | `_dia` |
| Fórmula | `(hoy − día_inicio).days` | `lots/service.py:379`, `operations/service.py:776` |
| Lote del mismo día | `0` días ⇒ clamp `≤0 → 1` (comportamiento actual del IPE, **preservado**) | `service.py:648-649` pre-fix |
| Lote sin inicio | 30 (**legado preservado**) | íd. |

## 6 · Zona horaria

- No se introduce framework de zonas. El día de negocio ya está anclado a medianoche UTC en persistencia; `date.today()` es la referencia de cálculo vigente en todo el módulo productivo. **Sin off-by-one** mientras ambos lados se normalicen a día de calendario (R184-AC14).

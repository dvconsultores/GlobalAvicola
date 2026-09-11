# GA-R184 · TRAZA DE NEGOCIO DEL IPE (G-06)

Regla de esta traza: **cada elemento computacional cita una fuente canónica del repositorio**. Nada se inventa.

## 1 · Definición vigente (citada)

```
G-06: European Production Index (IPE) = (Viabilidad% × Ganancia_Diaria_g × 100) / (FCR × 10)
      Ganancia diaria = avg_weight_g / age_days
```

- Fuente 1: docstring del endpoint — `app/reports/router.py` · `GET /kpi/ipe/{lot_id}` («G-06: European Production Index (IPE) = …»).
- Fuente 2: docstring del servicio — `app/reports/service.py::get_kpi_ipe` (misma fórmula).
- Implementación vigente: `app/reports/service.py::get_kpi_ipe` (líneas ~622-665).

> El índice completo de KPIs de `docs/02 §3.12.1` enumera los trece indicadores funcionales del módulo de reportes; G-01…G-06 (índices compuestos: bienestar, vacunación, transferencia, AFCR, índice de producción, IPE) provienen de la ola de KPIs posterior y su definición canónica es la del propio módulo `reports` (router + servicio). No existe otra definición en `docs/` ni en `specs/` que contradiga la citada.

## 2 · Variables de entrada

| Variable | Origen real en código | Unidad | Notas |
|---|---|---|---|
| **Viabilidad %** | `100.0 − mortality_rate_pct`; mortalidad = muertes aprobadas ÷ población inicial × 100 (`_sum_bird_quantity(MORTALITY_RECORDING)` con estados aprobados + `OpeningBalance`) | % | Sin `OpeningBalance`: población 0 ⇒ tasa 0 ⇒ viabilidad 100.0 (**contrato preexistente preservado**) |
| **avg_weight_g** | `AVG(BirdMovement.avg_weight)` de eventos `WEIGHT_RECORDING` del lote (con `company_id`), sin pesos nulos | gramos | Sin pesajes: 0.0 ⇒ ganancia 0 ⇒ IPE 0.0 (**preservado**) |
| **age_days** | `(date.today() − _día(lot.start_date)).days`; clamp `≤0 → 1`; sin `start_date` → 30 (**legado preservado**) | días de calendario | **Punto de R-184** (ver §4) |
| **Ganancia diaria g** | `avg_weight_g / age_days` | g/día | `age_days > 0` garantizado por clamp |
| **FCR** | `get_kpi_feed_conversion`: `total_feed_kg / 1000` si hay alimento (>0), si no 0 (`redondeado 2`) — cálculo simplificado declarado en su propia respuesta («requiere datos de pesaje para FCR real») | — (simplificado) | FCR 0 ⇒ IPE 0.0 por guarda `fcr > 0` (**preservado**) |

## 3 · Estados de lote y condición de cálculo

`LotStatus = {ACTIVE, CLOSED, CANCELLED}` (`app/masters/models.py`). El endpoint **no filtra por estado**: cualquier lote existente y alcanzable calcula. La condición de propósito (lote de engorde) no está codificada ni especificada — **no se introduce** en R-184.

## 4 · Base temporal (núcleo de R-184)

- La edad del IPE es **días de calendario entre el inicio del lote y hoy**, medida con la convención canónica del repositorio:
  - `app/lots/service.py::_dia` (líneas 8-11): «Día del calendario de un valor que puede venir como fecha o como instante».
  - Uso canónico idéntico: `lots/service.py:379` `age_days = (date.today() - _dia(lot.start_date)).days` y `operations/service.py:776` `(referencia - _dia(lot.start_date)).days`.
- Pre-fix, `get_kpi_ipe` restaba sin normalizar ⇒ `date − datetime` ⇒ 500. La corrección reutiliza la misma normalización canónica; **no cambia la fórmula ni el día de referencia**.

## 5 · Redondeo y precisión (contrato preservado)

| Campo | Redondeo actual |
|---|---|
| `viabilidad_pct` | 2 |
| `avg_weight_g` | 1 |
| `ganancia_diaria_g` | 2 |
| `fcr` | 2 |
| `ipe` | 1 |

Sin cambios (R184-AC09: se preserva; el test determinista lo fija).

## 6 · Bandas de referencia (contrato de respuesta)

`reference: {"excellent": ">300", "good": "250-300", "average": "200-250"}` — parte del esquema actual y del consumidor visual (colores/etiquetas del frontend). Se preserva literalmente.

## 7 · Tensión detectada (registrada, NO resuelta aquí)

Con constantes realistas (peso 2000 g, edad 19 d, viabilidad 95 %, FCR 3.0) la fórmula implementada devuelve **33333.3**, mientras las bandas del propio contrato sugieren escala EPEF (~300). El patrón conocido del EPEF europeo es `ADG × viabilidad% / (FCR × 10)` — el `× 100` extra del numerador produce un factor ~100 sobre esa escala cuando la viabilidad se maneja como porcentaje (95.0) en vez de fracción (0.95).

- **STATUS: OBSERVACIÓN DE NEGOCIO registrada** (candidata a decisión del propietario; NO bloquea R-184).
- R-184 exige **preservar la fórmula** (§2/§40/§81 del encargo) — no se altera ningún término, escala ni banda.

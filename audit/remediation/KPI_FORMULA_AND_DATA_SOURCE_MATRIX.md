# MATRIZ DE FÓRMULAS KPI Y FUENTE DE DATOS

**Auditoría 360°** · 2026-09-09 · base `7310adb` · **AUDIT ONLY**

Fuente de las fórmulas: `Bases Consideradas en el Desarrollo de la App Avicola.pdf` (nivel 2,
única fuente con fórmulas explícitas). Complementos: Recomendación §9 (mortalidad: acumulados
y % contra población inicial **y actual**), `spec.md §4.12`. Ross/Cobb = referencia de dominio.
Implementación: `reports/service.py` (14 rutas `/reports/*`), `dashboard/service.py`.

Semántica de datos (verificada): todos los agregados de `reports/service.py` cuentan **solo**
`APPROVED, CONSOLIDATED, SENT_TO_SAP, SAP_CONFIRMED` (`_sum_*`, `_aprobados`) y excluyen lotes
no alcanzables por unidad (`_exigir_lote`, `_filtro_de_lotes`). Unidades implícitas: alimento en
kg (`feed_movements.quantity_kg`), peso en **gramos** (`bird_movements.avg_weight`, sin unidad
declarada), huevos en unidades por `egg_type`.

Estados: `OK` · `DEFECTO` (fórmula distinta de la fuente) · `APROX` (aproximación declarada) ·
`AUSENTE` (sin productor) · `INDEFINIDO` (la fuente no da fórmula) · `CONFLICTO` (dos fórmulas en la fuente).

---

## 1. Reproductora — fase cría (Bases p.2-3)

| KPI | Fórmula fuente | Implementación | Fuente de datos | Estado | ID |
|---|---|---|---|:--:|---|
| Ganancia diaria de peso | (peso final − peso inicial) / días | no hay KPI propio; `get_kpi_ipe` usa `avg(avg_weight)/age_days` (`:640-650`) asumiendo peso inicial 0 y promedio de **todos** los pesajes | `weight_recording.avg_weight`, `lots.start_date`, `date.today()` | `APROX` | `H360-K08` P3 |
| Conversión alimenticia (FCR) | alimento consumido / peso ganado | `feed_conversion_ratio = total_feed_kg / 1000` (`:155`), nota «cálculo simplificado» | solo alimento | **`DEFECTO`** — no es un FCR; **se propaga** a `production-index` (`:601`) e `ipe` (`:648`) | **`H360-K01` P1** |
| Tasa de mortalidad | muertos / total al inicio × 100 | `total_deaths / initial_pop`; `initial_pop` **solo** de `OpeningBalance` (`:136-138`); sin `OpeningBalance` → 0 % | `mortality_recording`, `opening_balances` | **`DEFECTO`**: los lotes activados por recepción (`bird_reception`) no tienen `OpeningBalance` (`OpeningBalance(` solo en `lots/service.py:402`, activación manual) → mortalidad **0 %** siempre; el E2E de `P-15` no usa ni `activate-manual` ni `bird_reception` (0 y 0 apariciones) → defecto **no cubierto** | **`H360-K02` P1** |
| Índice de bienestar animal | «puede incluir incidencias de salud, ambiente, observaciones» | `100 − % inspecciones cuya `observations ILIKE '%salud%'` (`:433-463`) | `farm_inspection`, `hatchery_inspection` | `INDEFINIDO` en fuente · implementación heurística textual | `H360-K05` P2 · `AOD-10` |

## 2. Reproductora — fase producción (Bases p.4-5)

| KPI | Fórmula fuente | Implementación | Estado | ID |
|---|---|---|:--:|---|
| Tasa de fertilidad | fértiles / **huevos puestos** × 100 | `_fertilidad`: `egg_type='fertile'` / total, ambos sobre `EGG_RECEPTION_HATCHERY` (`:179-183`) | **`CONFLICTO`** (p.5 puestos · p.8 recogidos · código recibidos en incubadora) | `AOD-10` |
| % huevos infértiles | infértiles / puestos | ninguna ruta | `AUSENTE` | `H360-K10` |
| % huevos descartados | descartados / puestos | ninguna ruta (`_descartados` cuenta **pollitos** `cull_recording`, no huevos) | `AUSENTE` | `H360-K10` |
| Peso promedio del huevo | peso total / puestos | `egg_movements.avg_weight` se captura; sin KPI | `AUSENTE` | `H360-K10` |
| Consumo de alimento por huevo | alimento / puestos | ninguna | `AUSENTE` | `H360-K10` |
| Mortalidad de gallinas | muertas / al inicio | mismo `get_kpi_mortality` (`H360-K02`) | `DEFECTO` heredado | — |
| Hen-day (no en Bases; `spec §4.12` «producción de huevos») | — | `total_eggs / (initial_females × 30) × 100` (`:166`): **30 días fijos**, hembras iniciales (no vivas) | `DEFECTO` sobre un KPI no exigido | `H360-K04` P2 |

## 3. Traslado de huevos fértiles (Bases p.7-8)

| KPI | Fórmula fuente | Implementación | Estado |
|---|---|---|:--:|
| Fertilidad / % infértiles / % descartados / peso promedio | sobre **recogidos** | ver §2 | `CONFLICTO` / `AUSENTE` |
| Eficiencia de traslado | trasladados / fértiles × 100 | `get_kpi_transfer_efficiency` mide **pollitos** (`chick_dispatch / birth_registration`, `:506-540`); no hay versión para huevos (`egg_dispatch / fértiles`) | `AUSENTE` para huevos · `H360-K10` |

## 4. Incubadora (Bases p.9-11)

| KPI | Fórmula fuente | Implementación | Estado | ID |
|---|---|---|:--:|---|
| Tasa de eclosión | nacidos / fértiles × 100 | `eclosion = born / fertiles` (`:200`) | `OK` | — |
| Nacimiento (hatchability, `spec`) | — | `born / cargados` (`hatchery_params.quantity_loaded`) | `OK` (extra) | — |
| Mortalidad de pollitos | muertos / nacidos | ninguna (mortalidad general usa `OpeningBalance`) | `AUSENTE` | `H360-K10` |
| Eficiencia de vacunación | **pollitos vacunados** / nacidos | `vacc_events / (total_born / 1000) × 100` (`:493`): cuenta **eventos** de vacunación, no aves, y divide por miles | **`DEFECTO`** | **`H360-K03` P1** |
| % pollitos sanos | sanos / nacidos | `rendimiento = (born − descartados) / **cargados**` (`:204`) | `DEFECTO` (denominador) | `H360-K11` P2 |
| Eficiencia de traslado | trasladados / nacidos | `chick_dispatch / birth_registration` | `OK` | — |

## 5. Pollo de engorde (Bases p.12-13)

| KPI | Fórmula fuente | Implementación | Estado | ID |
|---|---|---|:--:|---|
| Ganancia diaria | (final − inicial)/días | ver §1 | `APROX` | `H360-K08` |
| FCR | alimento / peso ganado | `/1000` | **`DEFECTO`** | `H360-K01` |
| Mortalidad | muertos / inicio | ver §1 | **`DEFECTO`** | `H360-K02` |
| AFCR | alimento / (peso ganado + peso de muertos) | `get_kpi_afcr` (`:543-560`): `total = Σ BirdMovement.quantity` de `weight_recording` y `bird_exit` — **suma cantidades de aves**, las divide por 1000 «convert g to kg» y no incluye peso de muertos | **`DEFECTO`** (magnitud equivocada) | **`H360-K06` P1** |
| Índice de producción (EPEF) | peso vivo × supervivencia / (días × FCR) | `avg_weight_g × viabilidad / (age_days × fcr × 10)` (`:601`) — algebraicamente correcto **si** FCR fuera real; `age_days` usa `date.today()` incluso en lotes cerrados (`:596`) y `else 30` | `DEFECTO` heredado + edad incorrecta en lotes cerrados | `H360-K07` P2 |
| Peso promedio al sacrificio | peso total / sacrificados | `bird_exit.avg_weight` se captura; sin KPI | `AUSENTE` | `H360-K10` |
| Uniformidad (`spec §4.12`) | — (Cobb: % aves dentro de ±10 % del objetivo) | `CV% = stddev/avg` **entre pesajes** del lote (`:667+`), no dentro de la muestra | `INDEFINIDO` en fuente · implementación con otra definición | `AOD-10` |

## 6. Transversales

| Requisito | Fuente | Implementación | Estado | ID |
|---|---|---|:--:|---|
| Mortalidad % contra población **actual**, acumulado diario/semanal | Rec. §9 | solo % contra inicial; tendencia semanal en `dashboard._get_mortality_trend` (`:171-205`) **sin filtro de estado** (cuenta rechazados y cancelados) | `DEFECTO` de consistencia con `P-15` | `H360-K13` P2 |
| Consumo de agua | Bases p.2, 4, 12 | 0 apariciones en `backend/app` | `AUSENTE` (`R-13`, `GA-REM-021 SPEC_READY`) | `H360-B05` P1 |
| Peso promedio vs estándar | `spec §4.12` | `GET /operations/{id}/weight-evaluation` + alerta `weight_deviation` contra `genetic_weight_curves` (`GA-REM-037`) | `OK` | — |
| Diferencias SAP vs app | `spec §4.12` | `GET /reports/sap-comparison` clasifica eventos propios por estado; no compara con SAP | `APROX` (nombre engañoso) | G-R10 |
| Exportación Excel/PDF | `spec §4.12` | `frontend/src/utils/export` (cliente) | `OK` (no verificado en runtime) | — |
| Zona horaria de «hoy» | — | `date.today()` (hora del servidor) en `reports:596,642`, `validators:488`, `lots:306` | dependencia de TZ del contenedor, sin `TIMEZONE` en `config.py` | `H360-B09` P2 |

## 7. Trazas FE ↔ BE ↔ BD de los KPI visibles

| Pantalla | Ruta BE | Función | Tablas |
|---|---|---|---|
| `/kpi`, `/reports` (`ReportsPage`) | `GET /reports/kpis[?lot_id]` | `get_all_kpis` → mortality, feed_conversion, egg_production, hatchery, welfare, vaccination, transfer | `operational_events`, `bird_movements`, `feed_movements`, `egg_movements`, `hatchery_params`, `opening_balances` |
| `/reports/lot/:id` | `GET /reports/lot/{id}` | `get_lot_report` | ídem |
| `/` (`DashboardPage`) | `GET /dashboard/admin` · `/dashboard/mobile` | `get_admin_dashboard`, `get_mobile_dashboard` | `operational_events`, `operational_alerts`, `lots` |
| `/reports/sap` | `GET /reports/sap-comparison` | `get_sap_comparison` | `operational_events` |
| `/masters/genetic-lines/:id/weight-curves` | `GET /masters/genetic-lines/{id}/weight-curves` | curvas | `genetic_weight_curves(+points)` |

`P15_KPI_IMPLEMENTATION_MATRIX.md` (2026-09-06) registró «eclosión devuelve texto» (`R-14`) y
«fertilidad sin productor» (`R-86`); ambos aparecen **resueltos** en `7310adb` (`_porcentaje`
devuelve `float|None`; `_fertilidad` existe). Los defectos de esta matriz (`K01`, `K02`, `K03`,
`K06`) **no** están en aquella ni en el backlog: son nuevos.

## 8. Veredicto KPI

De los 26 indicadores exigidos por `Bases` (4 + 6 + 5 + 5 + 6): **4 `OK`**, **6 `DEFECTO`**
(4 de ellos P1: FCR, mortalidad, eficiencia de vacunación, AFCR), **2 `APROX`**, **2
`CONFLICTO/INDEFINIDO`**, **12 `AUSENTE`**. `P-15` certificó la **cadena** (ruta → cálculo →
pantalla) y la semántica «solo aprobado», no la **corrección de las fórmulas** contra la fuente
del cliente; esta matriz no revoca esa certificación, pero deja constancia de que el proceso
«Reportes e indicadores» **no puede** declararse conforme al requisito del cliente hasta `WAVE C`.

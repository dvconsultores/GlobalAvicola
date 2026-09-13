# R-204 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2. Ninguna decisión del propietario requerida; supuestos verificados en código.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | Actor sin ninguna unidad alcanzable en `/reports/kpis/hatchery`: ¿`[]`/ceros o 403? | Subconjunto vacío (ceros/NULL), patrón de lectura agregada (no 404/403 por lote aquí); coherente con `_filtro_de_lotes` → `false()` ⇒ suma 0. | `reports/service.py:64-70`; doctrina de lectura | técnica |
| C-02 | ¿Se aplica el mismo predicado a `get_sap_comparison(None)`? | **No**: excepción declarada `BU-D04` (superficie `CONTRATO`); solo se cita en la spec. | informe D B.8, nota | técnica |
| C-03 | `route_scope` `UNIDAD_UNICA hatchery`: ¿aplicar `unidad_requerida` o retirar la declaración? | **Aplicar** (reutilizar `unidades_de_alcance_productivo`); si el equipo detecta fricción con el patrón de lectura (prefiere subconjunto antes que 403), documentar y retirar la declaración con nota — ambas opciones cumplen AC-08. | `route_scope.py:215-217`; GAP-17 | técnica |
| C-04 | ¿Tocar `lots_by_type`/R-216? | No en este paquete (R-216 separado, misma tranche de panel). | registro G-28 | técnica |
| C-05 | ¿Tocar fórmulas KPI (R-131…R-214)? | No (Wave C pausada; `R-214` queda en backlog). | registro §1 G-26 | técnica |
| C-06 | Alcance del predicado en alertas: ¿`lot_id ∈ alcanzables` y también alertas sin lote? | Las alertas actuales llevan `lot_id`; si alguna no lo llevara, se excluye (fail-closed) y se documenta. | `dashboard/service.py:206-242` | técnica |
| C-07 | ¿Cambia `dashboard/mobile`? | No: no consume `active_alerts` ni los agregados tocados (verificado en la spec). | `dashboard/router.py:13-28` | técnica |

Sin decisiones abiertas.

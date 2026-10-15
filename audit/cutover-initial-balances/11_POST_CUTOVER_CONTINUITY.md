# CUTOVER-INITIAL-BALANCES · 11_POST_CUTOVER_CONTINUITY

Fecha: 2026-10-15 · SPEC 006 · Gate obligatorio del mandato §30: **no se certifica porque `status = applied`**; cada BU registra su primer evento real después del corte consumiendo el saldo de apertura.

---

## 1 · Regla de corte (CUT-GL-02)

Los datos de la plantilla representan el estado **hasta** la fecha/hora de corte del batch. Para un lote con saldo de apertura por cutover (`opening_balances.cutover_datetime`), todo evento operativo con `event_date ≤ fecha civil del corte` se rechaza con `400 {"rule": "CUT-GL-02"}` en `validate_event_date` (alta y edición). Un lote activado manualmente (sin corte) no se ve afectado. Así, «post-corte» coincide con «todo lo registrado en el sistema» y el histórico no puede volver a contarse (golden 9.965, nunca 9.465).

## 2 · Saldos del motor que leen la apertura

| Saldo | Antes (v1) | Ahora (v2) |
|---|---|---|
| Aves (`get_current_bird_balance`) | `initial_male + initial_female` + entradas − salidas | + `initial_mixed_count` (engorde; pollitos en planta) |
| Huevo en planta (`get_hatchery_egg_balance`, BR-03) | recepción − cargas | + `hatchery_openings.eggs_received − eggs_set` |
| Pollitos viables (`get_viable_chick_balance`, BR-04) | nacidos − salidas | + `opening_balances.initial_mixed_count` del lote con apertura de incubadora |
| Huevo en granja (`get_egg_balance`, BR-02) | recolección − despacho | sin cambio: el contrato no carga stock de huevo en granja (fuera de alcance, GL-OD-07) |

## 3 · Primer evento por BU (certificado)

| BU | Fase al corte | Primer evento | Resultado | Prueba |
|---|---|---|---|---|
| grandparent | PROD | `mortality_recording` (20 H + 15 M) y `egg_collection` 7.000 fértiles | 201 · opening 10.000 → current 9.965 · lifetime mortalidad 535 · lifetime huevos 187.000 | `test_grandparent_primer_evento_de_su_fase` · E2E `proceso-p16-cutover-grandparent` |
| breeder | CRIA | `mortality_recording` 10 H sobre lote con 0 machos vivos y mortalidad histórica de machos | 201 · 4.500 → 4.490 · lifetime 260 · huevos `NOT_APPLICABLE` | `test_breeder_cria_y_produccion` |
| breeder | PROD | `egg_collection` 8.000 → `egg_dispatch` 5.000 fértiles | 201/201 · lifetime producción 188.000 · a incubadora 155.000 | ídem · E2E `proceso-p16-cutover-breeder` |
| hatchery | INCUB | `incubation_load` 1.000 (= huevo recibido no cargado) y segunda carga de 1 ⇒ BR-03 | 201 / 400 · huevo disponible 0 · en proceso 9.900 | `test_hatchery_siguiente_paso_de_incubacion` · E2E `proceso-p16-cutover-hatchery` |
| hatchery | INCUB (pollitos) | `chick_dispatch` 300 de 500 disponibles; 201 más ⇒ BR-04 | 201 / 400 · pollitos disponibles 200 | ídem |
| broiler | ENGORDE | `mortality_recording` 35 mixto, `feed_registration` 500 kg, `weight_recording` | 201 ×3 · 10.000 → 9.965 · lifetime mortalidad 335 · lifetime alimento 15.500 | `test_broiler_mortalidad_alimento_y_peso` · E2E `proceso-p16-cutover-broiler` (CSV) |
| todas | — | evento con fecha = corte o anterior | 400 `CUT-GL-02` | `test_cut_gl_02_rechaza_eventos_hasta_el_corte`, `test_red_09_…`, E2E ×4 |

## 4 · Reconciliación y reporting

- `GET /cutover-batches/{id}/reconciliation`: por lote, `opening` (valor + estado por métrica), `post` (`event_date > corte`), `lifetime` (= opening + post **solo si** el opening es KNOWN; `UNKNOWN + 35 = UNKNOWN`), `current` (vivos, huevo disponible/en proceso, pollitos disponibles).
- `GET /reports/lot/{id}`: bloque `lifetime` por métrica (`opening`, `opening_status`, `post`, `lifetime`), `opening_balance.total_mixed`, `total_feed_kg = null` + `feed_status` cuando es UNKNOWN.
- KPIs de mortalidad y FCR usan la población de apertura **incluida la mixta**.

## 5 · Lo que el usuario NO tiene que reconstruir a mano

Fase real del lote (`lot_phases`), galpón/área/genética, sexo, procedencia, edad, saldos de huevo y pollitos en planta y los estados UNKNOWN/N/A: todo viaja desde la plantilla al dominio en el apply. La pantalla enlaza cada lote migrado a su detalle y al formulario de operaciones con el lote preseleccionado («Registrar primer evento»).

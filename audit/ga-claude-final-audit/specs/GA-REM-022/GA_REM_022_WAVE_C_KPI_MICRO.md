# GA-REM-022 · MICRO-TRANCHE WAVE C (KPI P1) — SPEC

Estado: **OWNER_APPROVED_IMPLEMENTED** — decisión formal del propietario:
`audit/ga-pre-sap-program/GA_OWNER_DECISION_WAVE_C_FORMAL.md` (commit `b58136a`).
La fase provisional (`2385688`/`80b2cb9`) quedó **SUPERSEDED** y su evidencia no
se usa para certificación (`evidence/PROVISIONAL_NOTE.md`).

Decisiones Owner (2026-09-16) incorporadas a esta micro-tranca:
- **R-131**: FCR canónico = masa de pienso / ganancia de masa viva
  (Δ peso medio × base ∩ estados aceptados); `OD-22` **sin cambios**.
- **R-132**: base = apertura + recepciones; `UNKNOWN` nunca 0.
- **Edad**: lote cerrado congela `age_days` en `end_date`.
- **R-141**: agregados usan el mismo conjunto filtrado que el detalle `R-218`
  (estados aceptados `[APPROVED, CONSOLIDATED, SENT_TO_SAP, SAP_CONFIRMED]`).
- **R-133/R-134**: `DEFERRED_FUNCTIONAL_DEFINITION` — retiradas de las
  superficies certificadas (FE/E2E ajustados); **sin fórmulas inventadas**.

Corrige los hallazgos P1 con corrupción de valor operacional:

## R-132 · `% mortalidad` con denominador real

- **Defecto**: `get_kpi_mortality` divide por `OpeningBalance` solo ⇒ lotes
  activados por recepción (sin apertura manual) reportan **0 %** de mortalidad
  y **100 %** de viabilidad (contamina IPE).
- **Corrección**: base = **apertura + entradas del motor** (`BIRD_RECEPTION`,
  `BIRTH_REGISTRATION`, estados aceptados — misma taxonomía que el saldo
  `R-67/RR-08`). Se exponen `opening_population` y `receptions` (aditivo) para
  trazabilidad del cálculo. Base 0 ⇒ 0 (sin cambio de contrato para lotes sin
  datos).
- **ACs**: (1) lote por recepción 100 aves + 10 muertes ⇒ `10 %` (hoy 0 %);
  (2) lote con apertura y sin entradas ⇒ idéntico a hoy (no regresión de
  `test_kpi_scope`); (3) lotes cerrados no cambian.

## R-131(b) · Edad de lote cerrado

- **Defecto**: IPE/IPE-detalle calculan `age_days` con `date.today()` incluso si
  el lote tiene `end_date` ⇒ la edad (y por tanto el IPE) sigue creciendo en
  lotes cerrados.
- **Corrección**: `hasta = lot.end_date or hoy` en las dos funciones.
- **ACs**: (4) lote cerrado (inicio 70 días atrás, cierre 10 días atrás) ⇒
  `age_days == 60` (hoy 70).

## Fuera de alcance (ACEPTADO-DOCUMENTADO)

R-131(a) FCR (requiere definición del propietario + recalibrar bandas OD-22),
R-133 vacunación /1000, R-134 AFCR gramos, R-141 agregados sin filtro de estado.

## Sensibilidad

M1: revertir denominador a apertura-solo ⇒ RED 1:1 en AC-1.
M2: revertir `hasta = today()` ⇒ RED 1:1 en AC-4. Restore desde IMPL SHA.

## Resolución Owner · R-131(a) FCR canónico

- Implementado en `backend/app/reports/service.py::get_kpi_feed_conversion`:
  `gain_kg = (avg_weight_final_g − avg_weight_initial_g)/1000 × population_basis`;
  `fcr = feed_kg / gain_kg` (None si insuficiente evidencia de pesos).
- Claves aditivas: `avg_weight_initial_g`, `avg_weight_final_g`,
  `population_basis`, `weight_gain_kg`, `unit = "kg feed / kg gain"`.
- Fixtures `r184/r186/r187` fijan `current_avg_weight` (Δ=1000 g ⇒ ganancia
  1000 kg) de modo que el resultado canónico es **numéricamente idéntico** al
  provisorio y las bandas `OD-22` (250/300) quedan intactas (verificado GREEN).
- RED→GREEN: `test_ga_rem_022_r131_r141.py` (5 ACs) + regresión KPI completa.

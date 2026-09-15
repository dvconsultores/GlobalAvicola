# GA-REM-022 · MICRO-TRANCHE WAVE C (KPI P1) — SPEC

Estado: **IMPLEMENTATION_PROVISIONAL_PENDING_OWNER_DECISION** — implementación
local (`2385688` RED · `80b2cb9` IMPL), evidencia **PROVISIONAL**, **no
certificada**; sujeta a la decisión del propietario en
`GA_OWNER_GATE_WAVE_C_MATRIX.md`. No alterar esta clasificación sin decisión
explícita.

Derivada de `AOD-08/AOD-10` (decisión de actor provisional
`GA_OWNER_DECISION_AOD10_ACTING_WAVE_C.md`, revisable). Corrige los dos
hallazgos P1 con corrupción de valor operacional:

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

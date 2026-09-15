# AGENT PROPOSAL · AOD-08/AOD-10 (Wave C KPI) — PROPUESTA DEL AGENTE

Fecha: 2026-09-15 · Clasificación: **AGENT_PROPOSAL_ONLY ·
NOT_OWNER_APPROVED · NON_AUTHORITATIVE**

Este documento registra una **propuesta del agente**, NO una decisión del
propietario. Ninguna regla funcional Wave C queda adoptada por él. La decisión
vigente está **pendiente del propietario** en
`GA_OWNER_GATE_WAVE_C_MATRIX.md`
(`T12 = IN_PROGRESS / BLOCKED_OWNER_DECISION_WAVE_C`).

## Propuesta del agente (no vinculante)

**Opción 1 — Corregir mínimo**: se corrigen **R-131** (FCR/edad) y **R-132**
(% mortalidad) en una micro-tranche con spec `GA-REM-022`, ANTES de cerrar T12.

**R-133** (vacunación /1000), **R-134** (AFCR gramos) y **R-141** (agregados sin
filtro de estado, familia E-24) quedan **ACEPTADOS-DOCUMENTADOS** con registro
explícito y recomendación de absorberlos en la fase de KPIs post-SAP.

## Racional

1. **R-132 es P1 con corrupción de decisión**: `% mortalidad` con denominador
   solo `OpeningBalance` marca **0 %** y viabilidad **100 %** en todo lote
   activado por recepción (el camino normal de operación). Un operador que
   decide sobre mortalidad «0 %» en una planta avícola es un defecto de producto
   inaceptable para GO.
2. **R-131 es P1 y contamina el IPE**: FCR dividido por 1000 y edad calculada
   con `date.today()` en lotes **cerrados** (debe usar `end_date`) ⇒ IPE
   «correcto en escala, no en valor». La corrección es contenida
   (`reports/service.py`).
3. **Contención**: ambos caben en una micro-tranche con RED cause-exact,
   sensibilidad y re-certificación P-15 — sin abrir alcance del dashboard ni la
   familia E-24 completa (esa merece su propia decisión de definiciones de
   cliente, estilo AOD-10 original).
4. **Reversibilidad**: toda la decisión y su racional quedan en este documento;
   si el propietario prefiere «corregir completo» o «aceptar», el delta es
   aditivo o revertible por la cadena de commits.

## Alcance de GA-REM-022 (micro-tranche) — ENMENDADO tras recon

- **In**: **R-132** (denominador de `% mortalidad` = apertura + entradas) y
  **R-131(b)** (edad de lotes cerrados con `end_date`, no `today()`).
- **Diferido a decisión genuina del propietario** (**R-131(a)**, FCR): la
  corrección real del FCR exige **definir la fórmula** (¿ganancia? ¿biomasa?) —
  que ES el objeto original de AOD-10 — y recalibrar las **bandas OD-22 ya
  certificadas** (`test_r187_ipe_od22_scale`): cambiarlas unilateralmente
  invalidaría una decisión de escala del propietario. Queda
  `ACEPTADO_DOCUMENTADO` con esta justificación, junto a R-133/R-134/R-141.
- Criterio de salida: RED cause-exact (2 casos reales), IMPL, sensibilidad 1:1,
  P-15 E2E re-corrida, suites BE/FE/build verdes, ledger + status.

## Registro

- `GA_OWNER_GATE_QUEUE.md` fila `AOD-08/AOD-10`: **`BLOCKED_OWNER_DECISION`**
  (la fila anterior `DECIDED_ACTING` queda anulada como clasificación: esta
  propuesta es NON_AUTHORITATIVE).
- AOD-08/AOD-10 permanece **ABIERTA** hasta la decisión del propietario sobre
  `GA_OWNER_GATE_WAVE_C_MATRIX.md`.

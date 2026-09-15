# GA_OWNER_DECISION · AOD-08/AOD-10 (Wave C KPI) — DECISIÓN DE ACTOR

Fecha: 2026-09-15 · Estado: **PROVISIONAL — REVISABLE POR EL PROPIETARIO**
(propietario no disponible en la ventana; instrucción expresa: «work
autonomously and make good decisions»).

## Decisión

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

## Alcance de GA-REM-022 (micro-tranche)

- **In**: R-131 · R-132. **Out**: R-133 · R-134 · R-141 (aceptados documentados).
- Criterio de salida: RED cause-exact (2 casos reales), IMPL, sensibilidad 1:1,
  P-15 E2E re-corrida, suites BE/FE/build verdes, ledger + status.

## Registro

- `GA_OWNER_GATE_QUEUE.md` fila `AOD-08/AOD-10`: `SCHEDULED` → **`DECIDED_ACTING`
  (provisional)** con enlace a este documento.
- Esta decisión NO cierra AOD-08/AOD-10 en firme: la fila queda en estado
  revisable hasta confirmación del propietario.

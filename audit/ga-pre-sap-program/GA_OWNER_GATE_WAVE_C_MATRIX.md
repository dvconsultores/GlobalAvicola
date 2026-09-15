# OWNER GATE · WAVE C (KPI) — MATRIZ DE DECISIÓN

Fecha: 2026-09-15 · Estado: **ABIERTA — esperando decisión del propietario**
· Ámbito: `AOD-08` / `AOD-10` (bloquea el cierre de **T12**) · Política: la
autonomía NO sustituye decisiones funcionales del propietario; toda
implementación Wave C es **PROVISIONAL**.

Estado de los artefactos relacionados:
- `GA_OWNER_DECISION_AOD10_ACTING_WAVE_C.md` = **AGENT_PROPOSAL_ONLY ·
  NOT_OWNER_APPROVED · NON_AUTHORITATIVE**.
- `GA-REM-022` = **IMPLEMENTATION_PROVISIONAL_PENDING_OWNER_DECISION**
  (commits locales `2385688` RED · `80b2cb9` IMPL; sin certificar).
- Baseline técnico: E2E **111/111** (producto pre-Wave-C, remoto `dd96f07`) —
  válido como baseline, no como certificación final.
- Suite completa con el IMPL provisional: **1431/0F/49S**
  (evidencia `specs/GA-REM-022/evidence/green/be-full-PROVISIONAL-1431.log`);
  `test_r187_ipe_od22_scale` ✅ (bandas OD-22 intactas).

---

## Matriz (por hallazgo)

| FINDING | CURRENT BEHAVIOR/FORMULA (HEAD `dd96f07`) | EXPECTED/PROPOSED | SEVERITY | OPERATIONAL IMPACT | EXISTING SPEC/OD AUTHORITY | REQUIRES NEW OWNER DECISION | ALREADY IMPLEMENTED PROVISIONALLY | RECOMMENDATION |
|---|---|---|---|---|---|---|---|---|
| **R-131** (FCR) | `feed_conversion_ratio = total_feed_kg / 1000` (sin peso; «estimado») · `reports/service.py:225` (HEAD) | Definir FCR real: `feed_kg / ganancia_kg` (o biomasa) con datos de pesaje; `UNKNOWN` si faltan datos — **cambia entradas del IPE** | P1 | FCR y **IPE** con valor incorrecto; decisiones de eficiencia sobre número sin dimensión | `docs/02 §3.12.1` (13 indicadores) · bandas IPE **OD-22 certificadas** (R-187) | **SÍ** — es una **definición de fórmula**, y toca OD-22 | NO | **NO aprobar sin definición**: exige del propietario la fórmula (ganancia vs biomasa, peso inicial, muertos) y recalibración consciente de bandas OD-22 |
| **Edad lote cerrado** (R-131b) | `age_days = (date.today() − start_date)` incluso con `end_date` · 2 sitios IPE | `hasta = end_date or hoy` — la edad se congela al cierre | P1 | IPE de lotes **cerrados** sigue cambiando con el calendario | `end_date` es dato canónico del cierre (T7/R-192); sin OD que fije «edad con hoy» | **NO** (corrección de hecho) **pero**: altera **valores IPE** en lotes cerrados ⇒ revisar contra OD-22 | **SÍ** (`80b2cb9`, local) | **Aprobar** como corrección de defecto; si el propietario considera OD-22 afectado, tratarlo como cambio de valor IPE declarado |
| **R-132** (% mortalidad) | Denominador = solo `OpeningBalance`: `initial_pop = apertura` · lotes por recepción ⇒ **0 %** fabricado | Denominador = **apertura + entradas** (`BIRD_RECEPTION`, `BIRTH_REGISTRATION`, aceptadas; taxonomía `R-67`/`RR-08`); exponer `opening_population`/`receptions`; base 0 ⇒ 0 | **P1** | Mortalidad 0 %/viabilidad 100 % en lotes normales (por recepción); **contamina IPE** (valor) | `R-67`/`RR-08` fijan la taxonomía del saldo; **AOD-10 enumera «base del % de mortalidad» como definición abierta del propietario** | **SÍ** — literalmente listada en AOD-10 | **SÍ** (`80b2cb9`, local) | **Aprobar** la base canónica propuesta (apertura+entradas) o indicar la base deseada; el valor 0 % actual es indefendible en operación |
| **R-133** (vacunación) | `efficiency = vacc_events / (total_born / 1000) × 100` (unidades inconsistentes) · `:578` (HEAD) | Definir unidad: ¿% de aves vacunadas del total nacido/recibido? ¿cobertura por evento? | P2 | KPI de cobertura de vacunación sin significado unitario | `docs/02 §3.12.1` | **SÍ** — definición funcional del indicador | NO (ACEPTADO-DOCUMENTADO) | Definir la unidad con el propietario antes de tocar; alternativa: retirar el indicador hasta definición |
| **R-134** (AFCR) | Suma `BirdMovement.quantity` **como gramos**; sin peso de muertos · `:554-566` (HEAD) | AFCR con pesos reales (incluir biomasa retirada de muertos); `UNKNOWN` sin pesos | P2 | Índice de conversión ajustado por mortalidad sin dimensión correcta | `docs/02 §3.12.1` | **SÍ** — definición de fórmula | NO (ACEPTADO-DOCUMENTADO) | Diferir a definición; documentar que el valor actual no es interpretable |
| **R-141** (agregados) | Agregaciones sin **filtro de estado** en varios KPI (familia E-24/E-05): pesajes cancelados/no aprobados alteran índices | Filtrar estados **aceptados** (patrón ya usado en `_sum_bird_quantity`/semanal: `R-218`) | P1 (parcial) | Indicadores alterados por eventos cancelados/pendientes | `R-218` ya normalizó el filtro para la serie semanal; P-15 exige coherencia | **NO** (coherencia con regla ya certificada) | NO (ACEPTADO-DOCUMENTADO) | **Aprobar** si se desea: es armonización con el filtro de estados ya certificado; sin ello, E-24 permanece como deuda |

## Propuestas que alteran OD-22 (identificación expresa — req. orden 11)

1. **R-131 (FCR)**: cualquier nueva definición de FCR cambia el **input** del
   IPE ⇒ altera los valores cubiertos por las bandas OD-22 certificadas
   (`test_r187_ipe_od22_scale`). **No debe implementarse sin decisión del
   propietario** y, en su caso, consciente recalibración/confirmación de bandas.
2. **Edad de lote cerrado (R-131b)**: implementación provisional incluida; NO
   cambia la escala OD-22, pero **sí los valores IPE de lotes cerrados**. Se
   declara expresamente para que el propietario lo valide o lo trate como
   cambio funcional declarado.
3. **R-132**: afecta el **valor** de viabilidad usada dentro del IPE (no su
   escala). Declarado.

## Evidencia técnica provisional

- BE full con IMPL provisional: **1431/0F/49S**
  (`evidence/green/be-full-PROVISIONAL-1431.log`).
- RED/IMPL/regresión/sensibilidad M1-M2/E2E P-15:
  `specs/GA-REM-022/evidence/{red,green,sensibilidad,post-mutation,e2e}/`
  — todo rotulado **PROVISIONAL**.
- Baseline E2E pre-Wave-C: **111/111**
  (`ga-pre-sap-program/evidence/t12/e2e-full-111.log`).

## Estado de tranches

- **T14 = CLOSED_TECHNICALLY** (permanece; no se reabre por este incidente).
- **T12 = IN_PROGRESS / BLOCKED_OWNER_DECISION_WAVE_C** — no se certifica hasta
  la decisión del propietario sobre esta matriz.

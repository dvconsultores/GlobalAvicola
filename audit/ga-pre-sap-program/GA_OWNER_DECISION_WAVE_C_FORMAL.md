# OWNER DECISION · WAVE C (KPI) — FORMAL (AUTORITATIVA)

Fecha: 2026-09-16 · Estado: **OWNER_APPROVED — VIGENTE** · Sustituye
funcionalmente la propuesta del agente `GA_OWNER_DECISION_AOD10_ACTING_WAVE_C.md`
(que permanece `AGENT_PROPOSAL_ONLY · NOT_OWNER_APPROVED · NON_AUTHORITATIVE`).

## Decisiones

1. **R-131 · FCR — APROBADO PARA CORRECCIÓN.** Fórmula canónica:
   `FCR = masa total de alimento consumido / ganancia total de peso vivo`.
   Numerador y denominador normalizados a la misma unidad de masa. El `/1000` no
   es parte de la fórmula: solo conversión de unidades demostrada por los campos
   reales.
   **OD-22 NO CAMBIA**: `IPE = (viabilidad% × ADG_g/día) / (FCR × 10)`; bandas
   `<250 rojo · 250–<300 amarillo · >=300 verde`.
2. **Edad de lote cerrado — APROBADA** la corrección existente: activo ⇒
   `hoy − start`; cerrado ⇒ `end_date − start` (congelada).
3. **R-132 · % mortalidad — APROBADA** la corrección provisional:
   `population_base = opening_population + inbound_bird_movements`;
   `mortality_pct = cumulative_mortality / population_base × 100`.
   **UNKNOWN nunca se convierte en 0.** Define SOLO la base del %; no redefine
   viabilidad ni OD-22.
4. **R-133 · vacunación — `DEFERRED_FUNCTIONAL_DEFINITION`.** No inventar
   unidad/fórmula; retirar el KPI ambiguo de las superficies certificadas;
   conservar datos primarios.
5. **R-134 · AFCR — `DEFERRED_FUNCTIONAL_DEFINITION`.** Ídem; retirar de
   superficies certificadas; conservar datos primarios.
6. **R-141 · agregados — APROBADO PARA CORRECCIÓN.** Los agregados deben usar
   el mismo conjunto filtrado que el detalle ya certificado en R-218:
   `FILTERED DETAIL SET = AGGREGATE INPUT SET`.
7. La propuesta del agente queda **NON_AUTHORITATIVE** (sin cambio de
   clasificación en su documento).
8. **GA-REM-022 AUTORIZADA PARA COMPLETARSE**: conservar provisionales (edad,
   R-132) si pasan pruebas bajo esta decisión; completar R-131 y R-141; R-133/
   R-134 diferidos y no bloquean T12 si las superficies ambiguas se retiran.

## Consecuencias de gobernanza

- `AOD-08/AOD-10` → **DECIDED (OWNER, 2026-09-16)**.
- T12 desbloqueado: se certificará tras la regresión final completa
  (la suite provisional 1431/0F/49S NO sustituye la regresión final).
- Prohibiciones vigentes: no tocar OD-22; no inventar R-133/R-134; no reescribir
  historia Git / reset / force push.

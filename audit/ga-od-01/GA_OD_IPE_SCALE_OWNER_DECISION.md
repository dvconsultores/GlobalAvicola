# GA-OD-01 · REGISTRO CANÓNICO DE DECISIÓN DEL PROPIETARIO — ESCALA DEL IPE (G-06)

**DECISIÓN: OD-22 · RATIFICADA** · Fecha: 2026-09-11 · Ejecución: GA-OD-01 (solo gobernanza)

> **Distinción de registro**: OD-22 = línea **GA/OD** (owner decisions del programa Global Avícola), siguiente libre tras OD-21. NO confundir con «AOD-22» (familia Wave B / AOD — registro separado; no colisiona).

## 1. Origen de la decisión

- Observación de negocio detectada en R-184 (`audit/ga-r184/GA_R184_IPE_BUSINESS_TRACE.md` §7 «Tensión detectada»).
- Formalizada en GA-GOV-02 como `OWNER_DECISION_REQUIRED` (`audit/ga-gov-02/GA_GOV_02_OWNER_DECISION_PACKET.md`, commit `2f9483f`).
- Paquete de decisión GA-OD-01 (commit C1 `3cf7baf`): traza de fórmula, traza de bandas, análisis de unidades (`CONFIRMED_100X_SCALE_CONFLICT`), evidencia numérica, impacto, trazabilidad y paquete A/B/C en `audit/ga-od-01/`.

## 2. Decisión del propietario (2026-09-11)

**Opción A — ALINEAR EL VALOR DEL IPE A LA ESCALA ESTÁNDAR / ESCALA DE LAS BANDAS.**

Respuesta explícita del propietario a la pregunta A/B/C de la sesión de decisión GA-OD-01: **A**. (No inferida, no auto-seleccionada.)

## 3. Regla de negocio canónica ratificada

1. La **viabilidad se maneja como porcentaje 0-100** (p. ej. 95.0) en todo su ciclo de cálculo.
2. El **IPE (G-06, `GET /reports/kpi/ipe/{lot_id}`) se expresa en la escala estándar EPEF** (valores típicos ~200-400): se elimina el factor **×100 sobrante**. Semántica objetivo: `ipe = (viabilidad% × ganancia_diaria_g) / (fcr × 10)`.
3. Las **bandas de clasificación permanecen SIN cambios**: `>300` 🟢 «Excelente» · `250-300` 🟡 «Bueno» · `≤250` 🔴 «Regular» (backend `reference` + umbrales de UI + textos i18n).
4. Los **valores mostrados cambiarán** (~100× menores) respecto al histórico visible; la clasificación recupera capacidad de discriminación (los lotes flojos dejan de salir «Excelente»; caso real: 21315.8 🟢 → ~213.2 🔴).
5. La limitación del **FCR simplificado** (estimado; «requiere pesaje real», ya documentada en el contrato) permanece como limitación independiente — fuera del alcance de esta decisión.
6. **Datos históricos: sin migración** (el KPI se calcula en vivo; nada persistido).

## 4. Efecto sobre el producto actual (brecha de implementación)

El producto actual implementa la escala inflada (`get_kpi_ipe` con el `×100` duplicado; números ~100× las bandas) ⇒ **brecha real** frente a la regla ratificada. Se formaliza como finding nuevo **R-187 · P2 · OPEN** (`GA_OD_IPE_SCALE_IMPLEMENTATION_GAP_R187.md`), **sin implementar** en esta sesión (tranche propia futura: spec → AC → implementación → UAT del propietario, por cambio visible).

## 5. No reapertura

Esta decisión es **prospectiva**: **NO reabre R-184** (CLOSED_OWNER_ACCEPTED) ni **R-186** (CLOSED). Las certificaciones **GA-FE-02..07**, R-181/R-182/R-185/OD-21 quedan **PRESERVED** (análisis completo en `GA_OD_IPE_SCALE_IMPACT_ANALYSIS.md` §certificado).

## 6. Fuera de alcance

- Implementación de la regla (tranche técnica nueva; autorización: **NO** en esta sesión).
- Cambios de bandas/umbrales/textos (no proceden con la opción A).
- FCR real/pesaje (limitación documentada aparte, independiente).

## 7. Estado final del registro

**Actualización 2026-09-11 (tranche R-187): IMPLEMENTADA y certificada técnicamente** — `OD-22 = RATIFIED_IMPLEMENTED` · R-187 = **CLOSED · FUNCTIONALLY_CERTIFIED** · Owner UAT REQUIRED / READY (acceptance PENDING) · evidencia completa en `audit/ga-r187/`.

*(Estado al ratificar la decisión: `OD-22 = RATIFIED` — implementación no iniciada; se conserva como registro histórico de este documento.)*

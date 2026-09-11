# OD-24 · DECISIÓN DEL PROPIETARIO — PROPIEDAD DE EMPRESAS Y GRANJAS

**ID canónico: `OD-24`** (línea GA/OD; siguiente libre tras OD-23; formaliza `AOD-06`) · Fecha: 2026-09-11 · Tranche: FINAL FRONTEND RESIDUAL CLOSURE · Decisión explícita del propietario: **A — IMPORTADAS DE SAP, NO EDITABLES** (con régimen provisional local declarado pre-P-08).

## 1 · La pregunta resuelta

> ¿Las Empresas y las Granjas «vienen de SAP» (sociedad/centro) — importadas y no editables — o son maestros locales con código SAP? (`AUDIT_OWNER_DECISIONS_REQUIRED.md` · AOD-06 · `R-124`).

## 2 · Regla canónica (ratificada)

1. **Post-integración (P-08):** Empresas y Granjas son **espejo de SAP** — Sociedad (`company`) ↔ Empresa; Centro/Planta ↔ Granja (**mapeo exacto a fijar en la SPEC de integración**). En la aplicación serán **de solo lectura**; no se crean ni editan localmente.
2. **Pre-P-08 (régimen provisional, declarado):** los catálogos locales siguen operativos como **representación provisional** (rigen `docs/02 §3.2.1` y los placeholders `SAP_DEFERRED_LOCAL_PLACEHOLDERS PL-05/06`); crear/editar localmente está permitido **sin pretender ser el maestro SAP**.
3. **Convergencia:** lo creado/editado localmente hasta la integración **se conserva**; su enlace/migración se define en la SPEC de integración. Sin borrados, sin migración ahora.
4. **`sap_config`:** sin cambio hoy (su exposición ya está gobernada por `OD-18`); el gobierno definitivo llega con la integración.
5. **Sin cambios de producto hoy**: 0 código · 0 migración · 0 conector · 0 credenciales SAP. No altera OD-14/15/16/18/20/21/22/23; no reabre fase 9.

## 3 · Efectos

- **R-124 → RESUELTO** por decisión canónica (cierre como contrato: provisional ratificado + convergencia futura).
- **FVA-07** deja de ser `OWNER_DECISION_REQUIRED` → `SUPERSEDED_BY_CANONICAL_DECISION`; entra al programa de certificación del régimen provisional (batch control-plane ampliado, sin mutación de maestros: gates + superficies + contrato).
- **RES-01 cerrado**; queda como trabajo **futuro ligado a P-08**: redactar la SPEC «convergencia Empresas/Granjas ↔ SAP» **antes** de la integración real (con AOD-11).
- No bloquea fase 9; sí elimina una de las dos condiciones de decisión pendientes del cierre frontend (queda AOD-25).

## 4 · Registro

- Paquete previo: `audit/final-frontend-audit/GA_AOD06_OWNER_DECISION_PACKET.md`.
- Formalización: este documento; registro AOD actualizado (`AOD-06` → `OD-24` · VIGENTE); `R-124` anotado en backlog; matrices del audit actualizadas (solo campos actuales).

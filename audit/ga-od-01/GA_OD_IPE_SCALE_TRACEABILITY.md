# GA-OD-01 · TRAZABILIDAD DE LA DECISIÓN

| Eslabón | Referencia |
|---|---|
| Origen de la observación | `audit/ga-r184/GA_R184_IPE_BUSINESS_TRACE.md` §7 «Tensión detectada» (commit `304174d`) |
| Formalización de la observación | `audit/ga-gov-02/GA_GOV_02_BUSINESS_OBSERVATION_*` + `GA_GOV_02_CLASSIFICATION_DECISIONS.md` (`2f9483f`): `OWNER_DECISION_REQUIRED` |
| Paquete previo | `audit/ga-gov-02/GA_GOV_02_OWNER_DECISION_PACKET.md` (opciones A/B/C; recomendación A) |
| Fuente de la fórmula | `backend/app/reports/service.py::get_kpi_ipe` (+ docstrings router/servicio) |
| Fuente de las bandas | backend `reference` + `LotDetailPage.tsx:396-397` + `LotReportPage.tsx:167-168` + `kpi.*` i18n |
| Unidades | `GA_OD_IPE_UNIT_ANALYSIS.md` (`CONFIRMED_100X_SCALE_CONFLICT`) |
| Ejemplos numéricos | `GA_OD_IPE_SCALE_EVIDENCE.md` §2 (A: 556.6 · B: 33333.3 · C: 35625/21315.8) |
| Opciones y consecuencias | `GA_OD_IPE_SCALE_IMPACT_ANALYSIS.md` |
| Recomendación re-evaluada | **A** (ver paquete §RECOMMENDATION: se mantiene tras la reconstrucción completa) |
| Owner Decision (línea GA/OD) | **OD-22** — asignada y ratificada (2026-09-11); **A DISTINGUIR** de la familia Wave B `AOD-22` (otro registro, sin colisión) |
| Registro canónico de decisión | `GA_OD_IPE_SCALE_OWNER_DECISION.md` (OD-22, 2026-09-11) |
| Brecha de implementación | `GA_OD_IPE_SCALE_IMPLEMENTATION_GAP_R187.md` (R-187 · P2 · OPEN) |
| **DECISIÓN DEL PROPIETARIO** | **A — ALINEAR EL VALOR A LA ESCALA ESTÁNDAR** (ratificada como **OD-22**, 2026-09-11) |

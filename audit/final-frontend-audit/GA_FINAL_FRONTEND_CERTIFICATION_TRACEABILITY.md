# FINAL FRONTEND AUDIT · TRAZABILIDAD DE CERTIFICACIÓN TÉCNICA

Fecha: 2026-09-11 · Sin certificación por adyacencia: cada fila cita su tranche/documento con declaración de alcance.

| Certificador | Alcance certificado (declaración) | Filas FVA | Documento |
|---|---|---|---|
| GA-FE-01 | Paridad build/despliegue (R-99/R-158): 13 stale re-servidas byte a byte; base de despliegue de todas las filas | (habilitante de 13 DEPLOYMENT_STALE) | `REMEDIATION_BACKLOG.md:1638` · `audit/ga-fe-01/` |
| GA-FE-02 (+B/C/D/E) | «contexto de empresa efectivo + switch · Company BU admin · User BU grants · navegación admin mínima» | FVA-01, FVA-04, FVA-05, FVA-08, FVA-09, FVA-16 (nav), y superficies de FVA-13/15 (admin) | `audit/ga-fe-02-a/…cert…` · `ga-fe-02-b F4` · `ga-fe-02-d` · `ga-fe-02-e` |
| GA-FE-03 | «evaluador canónico único (RBAC ∩ BU ∩ contexto ∩ global) en Sidebar/móvil/hubs/atajos; 45/45 desktop + 13/13 móvil»; ADM-06 y zero-BU; entrada `Roles` descubrible | FVA-11, FVA-12, FVA-16, (nav de FVA-14) | `audit/ga-fe-03/GA_FE_03_CERTIFICATION_RECONCILIATION.md` |
| GA-FE-04 | «31 acciones de escritura inventariadas y resueltas (gates + contrato API)»; R-98 CLOSED; self/cross | FVA-13, FVA-14, FVA-15, FVA-26 (gates), FVA-30 (acciones) | `audit/ga-fe-04/GA_FE_04_CERTIFICATION.md` |
| GA-FE-05 | «CTA visible ⇔ operations:create ∧ requiresUnits ∧ estado»; R-181 CLOSED | FVA-27 | `audit/ga-fe-05/GA_FE_05_CERTIFICATION.md` |
| GA-FE-06 | «planned_close_date + area_id capturados→persistidos→visibles; SLA reparado»; R-182 CLOSED | FVA-29 | `audit/ga-fe-06/GA_FE_06_CERTIFICATION.md` |
| GA-FE-07 | «elegibilidad por estado (exigir_activo); detección de cambio H1–H5; selector filtrado»; R-185 CLOSED | FVA-34 (elegibilidad), FVA-29 | `audit/ga-fe-07/GA_FE_07_CERTIFICATION.md` |
| GA-FE-08 | «entrada declarativa `lots`… autoridad por evaluador GA-FE-03»; OBS-UAT-01 resuelta | FVA-29 | `audit/ga-fe-08/GA_FE08_CERTIFICATION.md` |
| R-184 | «IPE: semántica temporal + 500» | FVA-31 | `audit/ga-r184/GA_R184_CERTIFICATION.md` |
| R-186 | «production-index G-05: 500 temporal → `_dia()`» (API; UAT no requerida) | FVA-31 (G-05) | `audit/ga-r186/GA_R186_CERTIFICATION.md` |
| R-187 (OD-22) | «escala IPE G-06 sin ×100» | FVA-31 | `audit/ga-r187/GA_R187_CERTIFICATION.md` |
| R-188 (OD-23) | «apagar termina; re-encender no devuelve; regrant restaura» | FVA-08, FVA-09 | `audit/ga-bu-d10/GA_BU_D10_CERTIFICATION.md` |
| OD-16 (GA-FE-02-D) | «habilitación de empresa absoluta para lecturas productivas; global sin bypass» | FVA-12, FVA-16 (frontera) | `audit/ga-fe-02-d/GA_FE_02_D_OD16_GLOBAL_READ_RECONCILIATION.md` |
| OD-21 (GA-FE-07) | «inactivo = inelegible para referencias nuevas» | FVA-34 | `audit/ga-fe-07/GA_FE_07_OWNER_DECISION_OD21.md` |
| OD-22 (R-187) / OD-23 (R-188) | decisiones ratificadas e implementadas | FVA-31 / FVA-08/09 | `audit/ga-od-01/…` · `audit/ga-bu-d10/GA_OD_BU_D10_OWNER_DECISION.md` |

**Sin certificador (VNC):** FVA-02, 03, 06, 17, 18, 20, 21, 22, 23, 24, 25, 26 (flujo completo), 30, 33, 34 (maestro), 35, 36, 37, 38 — verificadas en runtime actual (L2/L3) sin tranche/AC propia (ítem consolidado en la cola de residuales).
**Pendientes de decisión (ODR):** FVA-07 (R-124/AOD-06) · FVA-19 (R-153/AOD-25).
**Diferidas (OOS):** FVA-10 (T-040-24) · FVA-28 (fase 9).
**Externo (BE):** FVA-32 (P-08; R-112).

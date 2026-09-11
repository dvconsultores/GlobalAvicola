# GA-GOV-02 · DECISIONES DE CLASIFICACIÓN

| Item | Clasificación | Dueño canónico | ¿Finding formal? | Finding ID | Severidad | ¿Owner Decision? | ¿Implementación autorizada? | Próxima acción |
|---|---|---|---|---|---|---|---|---|
| **R-186 (candidato)** | `FORMAL_OPEN_FINDING` (previa: `INFORMAL_CANDIDATE_LABEL`) | `REMEDIATION_BACKLOG.md` — entrada OPEN propia | **SÍ** | **R-186** (siguiente libre tras R-185; verificado) | **P2** | **NO** (defecto técnico sin ambigüedad de política) | **NO** | Tranche técnica futura autorizable por el propietario (patrón R-184: `_dia` + suite PG + E2E runtime). Reproducción adicional no requerida (evidencia ya capturada) |
| **Observación de negocio (escala del IPE)** | `OWNER_DECISION_REQUIRED` (decisión de política de negocio) | `REMEDIATION_BACKLOG.md` GA-GOV-02 — decisión pendiente + `GA_GOV_02_OWNER_DECISION_PACKET.md` | **NO por ahora** (la brecha de implementación, si la hubiera, se abre tras la OD, vía SPEC) | — (OD candidata, siguiente libre tras OD-21 — numeración a ratificar) | N/A (política) | **SÍ** — 1 decisión | **NO** | Convocar al propietario con el paquete de decisión; después SPEC y, si procede, implementación con su propia aceptación |
| **OBS-UAT-01** | `UX_ENHANCEMENT_ONLY_P2` (sin cambio) | Backlog GA-GOV-01 «Mejoras de navegación P2» | No | — | P2 (UX) | No | **NO** | Sin cambio; candidata natural tras P1/P2 |
| **BU-D10** | `PENDING_RATIFICATION` (sin cambio) | `AUDIT_OWNER_DECISIONS_REQUIRED.md` | No | — | — | **SÍ** (ratificación; ajena a esta tranche) | **NO** | Sin cambio; no se decide aquí |

## Verificaciones de gobernanza

- **Un hogar canónico por residual**: R-186 → backlog (entrada OPEN R-186, con puntero a `audit/ga-gov-02/`); observación → backlog (decisión pendiente, paquete en `audit/ga-gov-02/`). Sin duplicados OPEN.
- **Sin reaperturas**: GA-FE-02..07, R-181, R-182, R-184, R-185, OD-21 **preservados** (ver `GA_GOV_02_CERTIFICATION_IMPACT.md`); ninguna AC aceptada queda contradicha hoy.
- **Sin producto**: diff de producto = 0 (solo carpeta `audit/ga-gov-02/` + actualizaciones de backlog/roadmap/catálogo).
- **Historial inmutable**: artefactos R-184/GA-UAT-06 intactos; esta tranche solo añade addenda.

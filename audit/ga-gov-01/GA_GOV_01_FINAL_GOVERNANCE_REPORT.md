# GA-GOV-01 · INFORME FINAL DE GOBERNANZA — TRIAGE POST-UAT-04

```
══════════════════════════════════════════════════════════════
GLOBAL AVÍCOLA
GA-GOV-01 · POST-UAT-04 OBSERVATION TRIAGE
FINAL GOVERNANCE REPORT
══════════════════════════════════════════════════════════════
ENTRY
  Branch:                main
  HEAD start:            cfdbdee
  Remote:                cfdbdee (== local)
  Worktree:              limpio
  Product code changed:  NO (últimos de producto: front 23ca59a · back 69d0c95)

OBS-UAT-01 · LOTS DISCOVERABILITY
  Current behavior:      /lots y /lots/new sin ninguna fuente de menú; /lots/:id por
                         alertas del Dashboard; crear requiere URL directa
  Canonical expectation: ninguna fuente exige entrada de menú; GA-FE-03 inventarió
                         /lots* entre las 12 rutas «sin fuente de menú» con decisión
                         expresa «sin entradas nuevas salvo Roles» (aceptada en GA-UAT-01)
  Related findings:      R-119 (distinto root), R-98 (distinto), R-181/R-135 (familia,
                         vertical SÍ existe aquí), prompt legacy móvil (no AC vigente)
  Dedup result:          NO duplicado · NO residual regresivo · sin dueño actual
  Classification:        UX_ENHANCEMENT_ONLY
  Severity:              P2 (mejora)
  New R required:        NO
  Assigned ID:           N/A
  Owner Decision:        NO
  Reopens GA-FE-03:      NO
  Reopens R-119:         NO
  Implementation auth.:  NO
  Backlog destination:   backlog GA-GOV-01 «Mejoras de navegación P2 (sin R)»

OBS-UAT-04 · LOGICALLY-DELETED AREA
  Current behavior:      backend acepta área inactiva en alta/edición (valida solo
                         tenencia); UI muestra inactivas (listado sin filtro de estado)
  Canonical Area lifecycle: is_active = baja lógica; «un área con histórico se da de
                         baja»; ninguna fuente define elegibilidad por estado
  Expected new-selection behavior: NO DEFINIDO (silencio canónico verificado)
  Existing related findings: R-179 (tenencia, distinto) · R-171 (sin relación) ·
                         ningún finding de filtrado/estado existe
  Dedup result:          NO duplicado; requiere política del propietario
  Classification:        OWNER_DECISION_REQUIRED
  Severity:              P3 propuesta (sube a P2 si elige la opción C)
  New R required:        NO (falla §23.6)
  Assigned ID:           N/A
  Owner Decision:        SÍ — pregunta A/B/C adjunta (estatus / filtro UI / regla de
                         dominio) con default neutro recomendado: B (filtro de selección)
  Reopens R-182:         NO (GA-FE-06-A §29: regla de estado no inventada)
  Implementation auth.:  NO
  Backlog destination:   backlog GA-GOV-01 «Decisión del propietario pendiente (P3)»

OBS-UAT-06 · AREA ABSENT FROM DETAIL
  Canonical requirement: ninguna spec exige Área en detalle; API la expone;
                         decisión de alcance GA-FE-06-C15 registrada; aceptado
  Classification:        ACCEPTED_DESIGN
  New R:                 NO
  Implementation auth.:  NO

UAT-11 · SLA VISIBLE CONSEQUENCE
  Canonical requirement: el aviso es notificación (campana) por evaluador interno;
                         sin superficie a demanda en ninguna fuente
  Classification:        NOT_A_DEFECT (N/A_BY_DESIGN)
  New R:                 NO

R-184
  Relationship to UAT observations: NONE
  Status:                SEPARATE_OPEN
  Implemented:           NO

CERTIFICATION IMPACT
  GA-FE-03: PRESERVED · GA-FE-04: PRESERVED · GA-FE-06: PRESERVED
  R-98: CLOSED (sin cambio) · R-119: CLOSED (sin cambio) · R-182: CLOSED (sin cambio)

OWNER DECISIONS REQUIRED
  Count: 1
  Decision 1: OBS-UAT-04 — «¿Debe impedirse usar recursos dados de baja para NUEVAS
              referencias (manteniendo histórico)?» Opciones: A estatus · B filtro de
              selección en UI (recomendado neutro) · C regla de dominio completa.
              Consecuencias técnicas por opción en GA_GOV_01_CLASSIFICATION_DECISIONS.md.

BACKLOG
  New findings created:       0 (cero — regla §23 aplicada)
  Existing findings updated:  ninguno reabierto; R-184 intacto
  UX enhancements created:    1 — «Entrada de navegación para el módulo Lotes» (P2, sin R)
  Accepted design observations: 1 — Área no mostrada en el detalle (GA-FE-06-C15)
  N/A observations:           1 — UAT-11 (mecanismo SLA interno)
  Owner decision pending:     1 — elegibilidad por estado (áreas/maestros en baja)

PROGRAM
  GA-FE-01..06: CLOSED / FUNCTIONALLY_CERTIFIED_OWNER_ACCEPTED (sin cambio)
  R-98/R-119: CLOSED · R-181: CLOSED_OWNER_ACCEPTED · R-182: CLOSED_OWNER_ACCEPTED
  R-184: SEPARATE_OPEN · BU-D10: PENDING_RATIFICATION
  Wave B: PAUSED · Wave C: NOT_STARTED · SAP: NOT_STARTED

FINAL VERDICT
  OBS-UAT-01: UX_ENHANCEMENT_ONLY (P2, sin R)
  OBS-UAT-04: OWNER_DECISION_REQUIRED (P3, sin R)
  OBS-UAT-06: ACCEPTED_DESIGN
  UAT-11:     NOT_A_DEFECT (N/A_BY_DESIGN)
  R-184:      SEPARATE_OPEN
  Product implementation: NONE
  Next recommended technical tranche: (1) iteración de navegación que incluya la
              entrada de Lotes y el filtro de selección por estado [sujeto a la decisión
              del propietario sobre OBS-UAT-04] · (2) reparación de R-184 (P2) cuando el
              programa la autorice
STOP: SÍ
══════════════════════════════════════════════════════════════
```

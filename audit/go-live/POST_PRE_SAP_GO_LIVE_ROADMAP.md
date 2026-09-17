# GLOBAL AVÍCOLA — POST PRE-SAP · GO-LIVE ROADMAP

Fecha: 2026-09-17 · Baseline: `fef7289` · SAP real (integración): fuera de alcance.
Metodología vigente sin cambios: **NO SPEC = NO DEVELOPMENT · NO AC = NO IMPLEMENTATION · NO TEST = NO COMPLETE · NO E2E = NO PROCESS CERTIFIED · NO EVIDENCE = NO CERTIFICATION**; cada cambio con cadena completa hasta `REMOTE_SHA_VERIFY`.

## DAG de fases (reconciliado pre-SAP-0)

```
PRE-SAP CLOSED (`fef7289`)
→ G0 GO-LIVE DISCOVERY CLOSED (`ea9478a`)
→ SAP-0 LANDSCAPE DISCOVERY + INBOUND DATA CONTRACT
→ GL-OD-06 / REAL DATA SOURCE DECISIONS
→ G1 OWNER DECISIONS + ACCESS
→ G2 CUTOVER ENGINEERING
→ G3 CUTOVER REHEARSAL
→ G4 GO-LIVE OWNER GATE
```

### SAP-0 · Landscape Discovery + Inbound Data Contract (NO integración)

- **Propósito**: auditar el landscape SAP **actual** y la versión histórica que sí se conectaba (`github.com/dvconsultores/SapHanaLP`) para descubrir: landscape, conectividad, fuentes SAP, objetos, contratos y opciones de integración de datos de entrada.
- **NO implementa** integración: sin RFC/OData/IDoc/BAPI/HANA directa/documentos SAP ficticios/sincronización contable ficticia.
- **Salida**: informe de landscape + contrato de datos de entrada + insumo para `GL-OD-06`.
- **Estado**: **PENDIENTE — NO INICIADA** (esta reconciliación no la inicia; STOP tras documentar).

---

## Fases

| Fase | Contenido | Estado | Salida (exit criteria) |
|---|---|---|---|
| **G0 · Discovery / Spec** | Este pack (10 entregables) + inventario de datos + baseline congelado | **✅ COMPLETA** (2026-09-17; SHA documental `ea9478a`) | Pack revisado por Owner; `GO_LIVE_READINESS` declarado |
| **SAP-0 · Landscape Discovery + Inbound Data Contract** | Auditoría del landscape SAP actual + versión histórica (`SapHanaLP`): conectividad, fuentes, objetos, contratos, opciones — **sin integración** | **⏳ NO INICIADA** | Informe de landscape + contrato de datos de entrada |
| **G1 · Decisiones Owner + Accesos** | Resolver las `GL-OD` habilitadas tras SAP-0 (empezando por `GL-OD-06 = PENDING_SAP0_DISCOVERY` → fuentes reales); responsables designados; autorización de limpieza | **⏳ PENDIENTE** (`PENDING_OWNER_DECISION`; G1 llega **después** de SAP-0) | Decisiones registradas con texto exacto; fuentes de datos disponibles; equipo designado |
| **G2 · Ingeniería cutover real** | Implementar extensiones: CUT-GL-01 (acta), CUT-GL-02 (guarda fecha), CUT-GL-03 (secuencia multi-BU), CUT-06 (auditoría incubadora), según decisiones CUT-04/05; provisión de entorno productivo (GL-OD-01/02); observabilidad/correo/secretos (GL-OD-03/04/09) | **⏳ BLOQUEADA por G1** | ACs implementados y certificados; entorno productivo listo |
| **G3 · Rehearsal** | Ejecutar `CUTOVER_REHEARSAL_PLAN.md`: R1 + R2 (si aplica), restore drill, acta de ensayo; cierre de gaps BLOQ restantes | **⏳ PENDIENTE** | Rehearsal PASS + 0 BLOQ + paquete del gate COMPLETO |
| **G4 · Go-Live** | Gate Owner (`GO_LIVE_OWNER_GATE.md`) → freeze → cutover real → acta → apertura operacional → hipercuidado D+0…D+30 (+ NBO-02 R-133/134, RES-07, G-06 como backlog posterior) | **⏳ PENDIENTE** | Decisión Owner registrada; operación real con datos reales; post-go-live estabilizado |

## Backlog post-Go-Live (G4+, no bloqueante)
- NBO-02: definición funcional R-133 (cobertura vacunación) y R-134 (AFCR) con Owner.
- CUT-05: política de reapertura post-firma (si no se resuelve antes).
- RES-07 (filas VNC con UAT) y G-06 (sondas C3) — cierre administrativo.
- Observabilidad avanzada, HA/multi-nodo, MFA — evaluar tras estabilización.
- SAP real (S/4HANA) — fase posterior independiente (boundary intacto).

## Registro
- Este roadmap sustituye como guía vigente al `GA_PRE_SAP_REMEDIATION_MASTER_ROADMAP.md` (programa Pre-SAP, cerrado); este último queda como historia.
- Cambios de este documento: solo por decisión registrada (Owner) o corrección documental trazable.

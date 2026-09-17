# Implementation Plan: SAP-0P — Read-Only Landscape Probe

**Feature**: `specs/002-sap0p-readonly-landscape-probe` · **Fecha**: 2026-09-17
**Tipo**: SPEC + PROBE READ-ONLY. **Cero implementación de producto.** Resultado de ejecución: `BLOCKED_EXTERNAL` (P0/P1 demostraron ausencia de canal autorizado).

---

## 1 · Technical Context

- **Ejecutor del probe (futuro)**: cuenta técnica READ-ONLY vía canal autorizado (VPN dedicada o Cloud Connector según SAP-CONN-01).
- **Entorno de esta ejecución**: estación de trabajo del proyecto — **sin** canal autorizado (P0/P1: sin IPsec/xl2tpd/ppp/tun, sin config HANA/SAP, DNS legacy no resuelve, sin `hdbcli`).
- **Artefactos**: `audit/sap0p/**` (16 docs obligatorios + acción Basis + evidencia saneada) + paquete `specs/002-sap0p-readonly-landscape-probe/**`.
- **Restricciones**: solo lectura; ninguna escritura SAP/dominio; sin implementación; sin deploy; sin secretos.

## 2 · Fases P0–P10 (trazabilidad con SAP-0 P0–P6)

El mandato SAP-0P amplía la numeración; mapeo con SAP-0 documentado aquí para trazabilidad:

| SAP-0P | SAP-0 (conceptual) | Contenido | Estado 2026-09-17 |
|---|---|---|---|
| P0 PREFLIGHT/SAFETY | P0 | repo limpio, SHA, política RO, límites, timeouts, stop conditions | **EJECUTADO** (local; PASS) |
| P1 NETWORK | P0 | ruta/VPN/DNS/reachability | **EJECUTADO PARCIAL** (local): canal ausente → BLOCKED |
| P2 SYSTEM IDENTITY/VERSION | P1 | HANA version, identidad, schema, SID, mandante | NO INICIADO (bloqueado) |
| P3 PERMISSIONS | P2 | SELECT-only/least privilege por metadata | NO INICIADO (bloqueado) |
| P4 METADATA/CATALOG | P3 | 9 tablas legacy + objetos: EXISTS/SELECT/KEYS/FIELDS | NO INICIADO (bloqueado) |
| P5 MINIMAL SAMPLES | P4 | muestras 1–10 filas acotadas | NO INICIADO (bloqueado) |
| P6 INBOUND RECONCILIATION | P5 | estado de los 12 objetos inbound | NO INICIADO (bloqueado; estados documentados `NOT_VERIFIED`) |
| P7 SERVICE DISCOVERY | P3/probe | OData/CDS/SOAP/Z-service (solo discovery no mutante) | NO INICIADO (bloqueado) |
| P8 EVIDENCE/SANITIZATION | P6 | registro de evidencia saneada | **EJECUTADO** para P0/P1 |
| P9 DISCONNECT/CLEANUP | P6 | cierre limpio | **N/A hoy** (nunca hubo sesión; nada que cerrar) |
| P10 CERTIFICATION | — | certificación honesta | **EJECUTADO** (certifica el bloqueo, no redondea) |

## 3 · Constitution / Safety Check

| Principio | Cumplimiento |
|---|---|
| NO SPEC = NO DEVELOPMENT | ✔ spec/plan/tasks antes de cualquier acción externa |
| NO EVIDENCE = NO CERTIFICATION | ✔ nada se certifica como verificado sin evidencia |
| READ ONLY | ✔ 0 escrituras; sin write tests; sin conexiones no autorizadas |
| NO SECRETS | ✔ solo presencia/conteos; REDACTED siempre |
| PRODUCT_FILES_CHANGED=0 | ✔ verificado por git diff |
| Fail-closed | ✔ sin canal autorizado → bloqueo, no improvisación |

## 4 · Estructura de entregables

```
audit/sap0p/
  SAP0P_OWNER_CONFIRMATION.md              SAP0P_STORAGE_LOCATION_FINDINGS.md
  SAP0P_READONLY_PROBE_SPEC.md             SAP0P_CONNECTIVITY_FINDINGS.md
  SAP0P_PROBE_PLAN.md                      SAP0P_SECURITY_REVIEW.md
  SAP0P_QUERY_REGISTER.md                  SAP0P_GA_REM_017_RECONCILIATION.md
  SAP0P_LANDSCAPE_VERIFICATION.md          SAP0P_GL_OD_06_READINESS.md
  SAP0P_PERMISSION_ASSESSMENT.md           SAP0P_SPEC_DEVELOPMENT_TRACEABILITY.md
  SAP0P_INBOUND_OBJECT_VERIFICATION.md     SAP0P_VERIFICATION_REPORT.md
  SAP0P_OD24_COMPANY_PLANT_EVIDENCE.md     SAP0P_READONLY_PROBE_CERTIFICATION.md
  SAP_ADMIN_BASIS_ACTION_REQUIRED.md       evidence/P0_PREFLIGHT_CHECK.log
                                           evidence/P1_NETWORK_LOCAL_CHECK.log
specs/002-sap0p-readonly-landscape-probe/  spec.md · plan.md · tasks.md · research.md
```

## 5 · Alcance propuesto de la futura SAP-1 (NO iniciar — §41 del mandato)

Propuesta condicionada a la evidencia que produzca el probe (no vinculante hoy):
- **SAP-1 — Inbound Masters Read-Only (borrador)**: Company, Plant, Storage Location, Vendor, Material.
- **SAP-2 (borrador)**: Purchase Orders, PO Items, PO History, Transfer Orders, Material Documents, Batches, Cost Centers.
El alcance final se derivará de la evidencia de SAP-0P, hoy inexistente → **no iniciar SAP-1**.

## 6 · Riesgos

| Riesgo | Mitigación aplicada |
|---|---|
| Ejecutar probe sin canal autorizado | Bloqueo deliberado (§9); cero conexiones desde red no autorizada |
| Fugar secretos al verificar presencia de config | Solo conteos de claves/поля; nunca valores |
| Redondear estados hacia arriba | Certificación enumera solo lo demostrado (P0/P1 local); lo demás `NOT_VERIFIED` |
| Confundir Owner Confirmation con verificación | Semántica de 8 estados aplicada en todos los documentos |

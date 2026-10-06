# SAP-0 · ADDENDUM 2026-10-06 — HANA CLOUD READ ONLY DECISION (pointer)

**Tipo**: addendum documental mínimo (sin reabrir SAP-0; solo pointer de supersession).
**Origen**: decisión Owner/Sponsor · Mandato «SPEC 005 — SAP HANA Cloud READ ONLY Inbound Integration» (2026-10-06).

---

## Cambio registrado

El mecanismo **inbound** vigente pasa a ser **SAP HANA Cloud READ ONLY**; el addendum del 2026-09-22 (SOAP inbound) queda superado y se conserva.

## Efecto sobre SAP-0

| Elemento SAP-0 | Nuevo estado |
|---|---|
| Direct HANA como target inbound (`RETIRED_AS_TARGET_ARCHITECTURE` desde 2026-09-22) | el inbound vuelve a leer HANA, pero como **`SAP_HANA_CLOUD_READ_ONLY_V2`**; el patrón legacy auditado aquí sigue `DO_NOT_REUSE` y **no se reactiva** |
| SAP Bridge con HANA directo (`SAP_BRIDGE_ARCHITECTURE_PROPOSAL.md`) | permanece como registro histórico; la SPEC 005 sitúa el conector en `backend/app/integrations/sap/inbound/` (least-privilege y secretos solo por entorno siguen siendo principios válidos) |
| Queries SQL legacy (`querysHana.py`) | **`LEGACY_HANA_QUERIES = REFERENCE_ONLY`** — matriz en `audit/sap-hana-cloud/02_LEGACY_QUERY_AUDIT.md` |
| Hardcode inventory (§6) y elementos prohibidos (§8) de `SAP_LEGACY_REPOSITORY_AUDIT.md` | **vigentes** como evidencia `DO_NOT_REUSE`; prohibidos en código productivo |
| Mecanismo inbound vigente | **SAP HANA Cloud READ ONLY** — `specs/005-sap-hana-cloud-readonly-inbound/` + `audit/sap-hana-cloud/**` |

## Qué NO cambia

- RAW/STAGING, fail-closed multiempresa, idempotencia, auditoría: **retenidos** (implementados sobre HANA en la SPEC 005).
- Fase 1 sin escrituras a SAP (`SAP_WRITES_PHASE_1 = FORBIDDEN`) y con outbound deshabilitado.
- Los documentos de SAP-0 permanecen íntegros como registro histórico de discovery. No se reescriben.

## Referencias
`audit/sap-hana-cloud/01_ARCHITECTURE_DECISION.md` · `audit/sap0/SAP0_ADDENDUM_2026-09-22_SOAP_INBOUND_DECISION.md` · mandato SPEC 005.

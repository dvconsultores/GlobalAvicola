# SAP-0 · ADDENDUM 2026-09-22 — SOAP INBOUND DECISION (pointer)

**Tipo**: addendum documental mínimo (sin reabrir SAP-0; solo pointer de supersession).
**Origen**: decisión de reunión Lider Pollo / proveedor SAP / Global DV · Mandato SAP-SOAP-1 (2026-09-22).

---

## Cambio registrado

| Elemento SAP-0 | Nuevo estado |
|---|---|
| Direct HANA como **target inbound** (explorado en `SAP_CONNECTIVITY_OPTIONS_ANALYSIS.md`, `SAP_BRIDGE_ARCHITECTURE_PROPOSAL.md`) | **`RETIRED_AS_TARGET_ARCHITECTURE`** para inbound |
| SAP Bridge con HANA directo | **`SUPERSEDED_FOR_INBOUND`** (la separación/aislamiento y least-privilege siguen siendo principios válidos) |
| Queries SQL legacy (`querysHana.py`) | **`REFERENCE_ONLY` / `LEGACY_FUNCTIONAL_REFERENCE_FOR_ABAP`** |
| Mecanismo inbound vigente | **SOAP** — contrato en `audit/sap-soap/**` + `specs/003-sap-soap-inbound-contract/` |

## Qué NO cambia

- RAW/STAGING, fail-closed multiempresa, idempotencia, auditoría: **retenidos** (adaptados a SOAP en `audit/sap-soap/10_SAP_SOAP_RAW_STAGING_MAPPING.md`).
- Los documentos de SAP-0 permanecen íntegros como registro histórico de discovery. No se reescriben.

## Referencias
`audit/sap-soap/01_SAP_SOAP_ARCHITECTURE_DECISION.md` · mandato SAP-SOAP-1.

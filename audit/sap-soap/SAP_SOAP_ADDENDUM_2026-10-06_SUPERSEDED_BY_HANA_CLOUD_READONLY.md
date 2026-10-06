# SAP-SOAP · ADDENDUM 2026-10-06 — SUPERSEDED BY SAP HANA CLOUD READ ONLY (pointer)

**Tipo**: addendum documental mínimo (sin reabrir SAP-SOAP-1; solo pointer de supersession).
**Origen**: decisión Owner/Sponsor · Mandato «SPEC 005 — SAP HANA Cloud READ ONLY Inbound Integration» (2026-10-06).

---

## Cambio registrado

El mecanismo **inbound** vigente pasa a ser **SAP HANA Cloud READ ONLY**. `SOAP_INBOUND_TARGET = SUPERSEDED_BY_OWNER_SPONSOR_DECISION_2026_10_06`.

## Efecto sobre SAP-SOAP-1

| Elemento SAP-SOAP-1 | Nuevo estado |
|---|---|
| Contrato SOAP inbound (`audit/sap-soap/01…15`, `specs/003-sap-soap-inbound-contract/`, documento cliente-facing en `docs/`) | **`CLOSED_HISTORICAL_CONTRACT_NOT_IMPLEMENTED`** |
| Implementación del lado GA (fases SOAP-2…SOAP-8: mock, adaptador, sandbox, pruebas con proveedor) | **`SUPERSEDED_FOR_INBOUND_IMPLEMENTATION`** — no se inician |
| `DIRECT_HANA_INBOUND = RETIRED_AS_TARGET_ARCHITECTURE` | superado como target inbound; el Direct HANA **legacy** no se reactiva: la implementación es `SAP_HANA_CLOUD_READ_ONLY_V2` |
| `11_SAP_SOAP_LEGACY_QUERY_REFERENCE_FOR_ABAP.md` | sigue `REFERENCE_ONLY`; es la fuente de `audit/sap-hana-cloud/02_LEGACY_QUERY_AUDIT.md` |
| Mecanismo inbound vigente | **SAP HANA Cloud READ ONLY** — `specs/005-sap-hana-cloud-readonly-inbound/` + `audit/sap-hana-cloud/**` |

## Qué NO cambia

- RAW/STAGING, Adapter Pattern (interfaz inbound separada del export, `12_… §2`), fail-closed multiempresa, idempotencia, auditoría: **retenidos** y adaptados a HANA en la SPEC 005.
- GA-REM-010 intacta. `ZwsTasaMortalidad` y todo outbound siguen fuera de alcance (`SAP_OUTBOUND_PHASE_1 = DISABLED`).
- Los documentos de SAP-SOAP-1 permanecen íntegros como registro histórico: no se borran ni se reescriben; solo reciben un puntero `SUPERSEDED` de una línea.

## Referencias
`audit/sap-hana-cloud/01_ARCHITECTURE_DECISION.md` · `specs/005-sap-hana-cloud-readonly-inbound/spec.md` · `audit/sap-soap/01_SAP_SOAP_ARCHITECTURE_DECISION.md` · mandato SPEC 005.

# SAP-0P · ADDENDUM 2026-09-22 — SOAP INBOUND DECISION (pointer)

**Tipo**: addendum documental mínimo (sin reabrir SAP-0P; solo pointer de supersession).
**Origen**: decisión de reunión Lider Pollo / proveedor SAP / Global DV · Mandato SAP-SOAP-1 (2026-09-22).

---

## Efecto sobre SAP-0P

| Aspecto | Estado |
|---|---|
| `SAP0P_STATUS` | **`BLOCKED_EXTERNAL` se mantiene** (canal HANA no provisionado) — no se reabre |
| Relevancia del probe HANA read-only | **deja de ser prerrequisito** para la línea de integración inbound: el mecanismo acordado es **SOAP** (contrato `audit/sap-soap/**`) |
| `GL-OD-06` | sin cambio automático: sigue `BLOCKED_EXTERNAL_SAP_INFORMATION`; su reevaluación dependerá de evidencia del camino SOAP (sandbox/pruebas), no del probe HANA |
| Evidencia P0/P1 | permanece válida como registro del estado del entorno de ejecución en 2026-09-17 |

## Qué NO cambia

- El contrato read-only, la certificación honesta y las salvaguardas de SAP-0P quedan íntegros como registro histórico.
- No se ejecuta ningún probe HANA como parte de SAP-SOAP-1.

## Referencias
`audit/sap-soap/01_SAP_SOAP_ARCHITECTURE_DECISION.md` · `audit/sap0p/SAP0P_READONLY_PROBE_CERTIFICATION.md` · mandato SAP-SOAP-1.

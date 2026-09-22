# Research — SAP-SOAP-1

**Feature**: `specs/003-sap-soap-inbound-contract` · Fecha: 2026-09-22
Insumos: decisión de reunión (Lider Pollo/proveedor SAP/GA) · `audit/sap0/**` + `audit/sap0p/**` · legacy `SapHanaLP` (evidencia) · código actual GA (`backend/app/integrations/sap/**`).

---

## 1 · Cambio de contexto

| Antes (SAP-0/SAP-0P) | Ahora (SAP-SOAP-1) |
|---|---|
| Se exploraba Direct HANA read-only como posible inbound | **SOAP** acordado con proveedor; Direct HANA `RETIRED_AS_TARGET_ARCHITECTURE` |
| Probe HANA bloqueado externamente | Irrelevante para esta línea: el contrato SOAP no depende de HANA directo |
| Queries SQL legacy como pista de discovery | **Referencia funcional para ABAP** (nunca contrato) |

## 2 · Hechos del producto relevantes

- `SapIntegrationAdapter` (export) + `Manual/Mock`, `delivers_to_sap=False`; sin adaptador inbound; sin `RealSapAdapter`.
- `sap_references`: 8 tipos espejo, 1 consumido (PO). RAW/STAGING diseñado en SAP-0 (`SAP_RAW_STAGING_SPEC.md`).
- GA-REM-010/017 intactos (honestidad de entrega).

## 3 · Evidencia legacy relevante (para el anexo ABAP)

- Queries: granjas/almacenes/OC/historial/proveedores/alimento/pollitos/cría-producción/salidas/inventarios (con filtros MANDT 120, listas MATNR, BWART 641/303, fechas, prefijo AUFNR '7', destinos fijos).
- SOAP legacy `ZwsTasaMortalidad` (outbound; solo referencia histórica).
- Clasificación aplicada: referencias vs reglas-a-validar vs `DO_NOT_REUSE`.

## 4 · Decisiones de diseño tomadas (y por qué)

1. **Operaciones tipadas** con header/response común — interoperable y mockeable; `GetIntegrationChanges` opcional para no imponer arquitectura ABAP.
2. **PO con items anidados** — menos round-trips, sin operación extra.
3. **ContinuationToken preferido** sobre PageNumber — robusto ante cambios; fallback aceptado.
4. **Delta por objeto con campo a confirmar** — ABAP propone, GA valida propiedades (monotonía, actualización).
5. **Interfaz inbound separada** del ABC export — evita fingir capacidades en manual/mock y no rompe GA-REM-010.
6. **Categorías de material en GA** — elimina el patrón legacy de hardcodear MATNR.
7. **COST_CENTER deferido** — sin consumidor actual; confirmable en un ítem.

## 5 · Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| WSDL real divergente | diff obligatorio contra `04/05_…` |
| Interpretación del legacy como contrato | aviso expreso en `11_…` + clasificación |
| Extracciones masivas | ventana obligatoria + paginación + límites |
| Duplicados por retry | idempotencia por clave+hash |
| Secretos | contrato de seguridad + ejemplos placeholder |

## 6 · Referencias
Mandato SAP-SOAP-1 · `audit/sap-soap/01…15` · `audit/sap0/**` · `audit/sap0p/**` · `specs/remediation/GA-REM-017-…` · `docs/10-sap-integration-strategy.md` (con addendum) · `backend/app/integrations/sap/adapter.py`.

# SAP-SOAP · 01_SAP_SOAP_ARCHITECTURE_DECISION

Fecha: 2026-09-22 · Fase: **SAP-SOAP-1 — SOAP Inbound Contract & Implementation Readiness** (SPEC ONLY — sin implementación)
Origen: reunión técnica Lider Pollo + proveedor SAP/ABAP + Global Avícola/Global DV (decisión material)
Estado: **DECISIÓN FORMALIZADA** (acta documental; reemplaza el target inbound anterior)

---

## 1 · Decisión (registro canónico §2 del mandato)

| Clave | Valor |
|---|---|
| `SAP_INBOUND_MECHANISM` | **SOAP** |
| `SAP_SOAP_PROVIDER` | **LIDER_POLLO_SAP_PROVIDER** (desarrolla/expone el servicio del lado SAP/ABAP) |
| `GLOBAL_AVICOLA_ROLE` | **SOAP_CONSUMER** |
| `DIRECT_HANA_INBOUND` | **RETIRED_AS_TARGET_ARCHITECTURE** |
| `LEGACY_SQL` | **REFERENCE_ONLY** |
| `SAP_BRIDGE_DIRECT_HANA` | **SUPERSEDED_FOR_INBOUND** |
| `RAW_STAGING` | RETAINED |
| `ADAPTER_PATTERN` | RETAINED |
| `FAIL_CLOSED` | RETAINED |
| `AUDIT` | RETAINED |
| `IDEMPOTENCY` | RETAINED |
| `MULTICOMPANY_ISOLATION` | RETAINED |

## 2 · Flujo objetivo

```
SAP (S/4HANA) → SOAP SERVICE EXPUESTO POR SAP (proveedor ABAP)
→ GLOBAL AVÍCOLA SOAP CLIENT / ADAPTER
→ RAW → STAGING → VALIDATION → MAPPING → DOMAIN PROMOTION
```

- Modelo **PULL** (§3): Global Avícola **solicita** información al servicio SOAP SAP. Global Avícola **NO** expone SOAP server para esta dirección.
- Si en `/clarify` o en la próxima reunión SAP exige **PUSH/callback**, se registra como **decisión Owner/Proveedor SAP** y NO se asume (ver `13_SAP_SOAP_PROVIDER_OPEN_ITEMS.md`).

## 3 · Qué queda retirado / superseded (con historia preservada)

| Elemento anterior | Nuevo estado | Addenda |
|---|---|---|
| Direct HANA como target inbound (SAP-0/SAP-0P lo exploraban como opción) | `RETIRED_AS_TARGET_ARCHITECTURE` | `audit/sap0/SAP0_ADDENDUM_2026-09-22_SOAP_INBOUND_DECISION.md` · `audit/sap0p/SAP0P_ADDENDUM_2026-09-22_SOAP_INBOUND_DECISION.md` |
| Queries SQL legacy de `SapHanaLP` | `LEGACY_FUNCTIONAL_REFERENCE_FOR_ABAP` (referencia funcional para ABAP; **nunca** contrato técnico) | `11_SAP_SOAP_LEGACY_QUERY_REFERENCE_FOR_ABAP.md` |
| SAP Bridge con HANA directo (SAP-0 §23) | `SUPERSEDED_FOR_INBOUND` (la separación/aislamiento de red y secretos sigue siendo principio válido para el cliente SOAP) | este documento |
| OData como mecanismo recomendado (`docs/10`) | `SUPERSEDED_BY_OWNER_AND_PROVIDER_DECISION` (para inbound); historia intacta | addendum en `docs/10-sap-integration-strategy.md` |
| `ZwsTasaMortalidad` (SOAP legacy) | solo referencia histórica; no forma parte de este contrato (**outbound** futuro, otra SPEC) | `11_…` + §37 del mandato |

## 4 · Qué se conserva (y por qué)

- **RAW/STAGING + promoción controlada**: `SOAP → DOMAIN DIRECTLY` nunca (§26). Diseño SAP-0 adaptado con campos SOAP (`10_SAP_SOAP_RAW_STAGING_MAPPING.md`).
- **Adapter Pattern**: el dominio sigue dependiendo de `SapIntegrationAdapter`; el nuevo consumo entra por un contrato **inbound** separado (`12_SAP_SOAP_GA_ADAPTER_CHANGE_SPEC.md`).
- **Fail-closed multiempresa**: `SAP SYSTEM → MANDT → BUKRS → WERKS → GA COMPANY → BU`; sin mapping → `PENDING_MAPPING`, sin promoción (§28).
- **Idempotencia / integridad**: misma clave+hash → no duplicar; clave igual+hash distinto → nueva versión (§27).
- **GA-REM-010**: no se toca la semántica de export (`NO VERIFIED SAP DELIVERY = NO TRUE sent_to_sap`).

## 5 · No objetivos de esta decisión

- No define outbound GA→SAP (será otra SPEC si SAP requiere recibir mortalidad/consumos/movimientos; §37 del mandato).
- No implementa `SoapSapAdapter` ni clientes SOAP.
- No decide la arquitectura ABAP interna del servicio (solo el contrato funcional externo; §7).

## 6 · Consecuencias

1. El proveedor SAP construye el servicio contra el paquete de contrato de `audit/sap-soap/**` + `specs/003-sap-soap-inbound-contract/**`.
2. Global Avícola prepara (fases futuras SOAP-2…SOAP-8) mock del contrato → adaptador → RAW/STAGING → sandbox → pruebas con proveedor → reconciliación → certificación.
3. SAP-0P (probe HANA read-only) queda **no bloqueante** para esta línea: su objetivo (identidad/versiones del landscape) se reencuadra como información opcional; el contrato SOAP no depende de HANA directo.

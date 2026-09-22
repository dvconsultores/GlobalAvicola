# SAP-SOAP · 12_SAP_SOAP_GA_ADAPTER_CHANGE_SPEC

Fecha: 2026-09-22 · Cambios futuros del lado Global Avícola (§35–§36) · **DISEÑO únicamente — NO implementado**

---

## 1 · Auditoría del estado actual (evidencia)

| Elemento | Estado real hoy |
|---|---|
| `backend/app/integrations/sap/adapter.py` | ABC `SapIntegrationAdapter` con `export_consolidated`, `check_connection`, `get_adapter_name`; implementaciones `ManualSapAdapter` y `MockSapAdapter`; `delivers_to_sap=False`; **no existe** `RealSapAdapter` ni adaptador inbound |
| `sap_references` | espejo de 8 tipos SAP; único consumido: `PURCHASE_ORDER` (BR-18) |
| Importación actual | por referencias preparadas (manual), sin fetch remoto |
| Semántica export | GA-REM-010 intacta (`NO VERIFIED SAP DELIVERY = NO TRUE sent_to_sap`) |

## 2 · Decisión de diseño: interfaz inbound separada

**Elegida**: un **nuevo contrato inbound** (`SapInboundAdapter`) **separado** del ABC de export, implementado a futuro por `SoapSapAdapter`.

Razones:
1. No diluir la semántica de entrega del ABC actual (export) ni romper `ManualSapAdapter`/`MockSapAdapter`.
2. Separar claramente `INBOUND ADAPTER CONTRACT` de `FUTURE OUTBOUND SAP CONTRACT` (§36).
3. Mantener una única ruta de ejecución SOAP (paginación/delta/errores/seguridad implementados **una vez**).

**Alternativa descartada**: añadir `fetch_*` al ABC actual — acopla dos direcciones y obliga a `manual`/`mock` a fingir capacidades inbound (viola honestidad de estados).

## 3 · Diseño del futuro `SoapSapAdapter` (fase SOAP-3, NO ahora)

```text
SapInboundAdapter (ABC, nuevo — diseño)
  fetch_companies(request) -> SapSoapResponse[CompanyRecord]
  fetch_plants(request) -> ...
  fetch_storage_locations(request)
  fetch_vendors(request)
  fetch_materials(request)
  fetch_purchase_orders(request)          # header + items anidados
  fetch_purchase_order_history(request)
  fetch_production_orders(request)
  fetch_outbound_orders(request)
  fetch_transfers(request)
  fetch_material_movements(request)
  fetch_batches(request)
  # internamente: _execute(operation, request) único → transporte SOAP
```

- **Tipado externo + ejecutor genérico interno**: el dominio obtiene métodos tipados; el “cable” (WSDL, TLS, auth, paginación, fault handling) vive en un único ejecutor.
- Entregable del adaptador: **registros crudos + metadata** hacia el pipeline inbound (RAW); **jamás** escritura directa a dominio (§13 de AC-SOAP).
- Config futura: endpoint (por entorno), credenciales por referencia segura (custodia `AOD-12`), timeouts (10/60 s), `SchemaVersion` esperada, feature flag de integración.
- Modo mock del contrato (SOAP-2) implementará **este mismo contrato** contra fixtures XML del `06_…` para habilitar pruebas sin SAP.

## 4 · Qué NO cambia (garantías)

| Elemento | Garantía |
|---|---|
| `SapIntegrationAdapter` (export) | intacto |
| `ManualSapAdapter`, `MockSapAdapter` | intactos |
| consolidation / outbox / GA-REM-010 | intactos |
| `SAP_ADAPTER=real` | sigue `NO IMPLEMENTADO` (GA-REM-017) — esta SPEC no lo cambia; el SOAP inbound no es “export real” |
| Dominio | no conoce SOAP; consume adaptadores abstractos |

## 5 · Extensiones del ABC actual a evaluar en la implementación (no ahora)

- `check_connection()` → el futuro adaptador inbound reportará estado de **servicio SOAP** (no de HANA).
- Nuevo método opcional `get_inbound_capabilities()` (versión de schema soportada, operaciones disponibles) — decisión de implementación.

## 6 · Plan de fases (trazabilidad §41 del mandato)

| Fase | Contenido | Estado |
|---|---|---|
| **SOAP-1** | Contrato + SPEC (esta ejecución) | **COMPLETADA (docs)** |
| SOAP-2 | Mock del contrato (fixtures + validador XSD) | PLANNED |
| SOAP-3 | `SoapSapAdapter` (cliente real contra mock) | PLANNED |
| SOAP-4 | RAW/STAGING + jobs de ingesta | PLANNED |
| SOAP-5 | Sandbox de integración con SAP proveedor | PLANNED |
| SOAP-6 | Prueba con servicio SAP real (read-only) | PLANNED |
| SOAP-7 | Reconciliación end-to-end | PLANNED |
| SOAP-8 | Certificación | PLANNED |

Cada fase con ACs verificables y sin solapar con export.

# SAP-SOAP · 14_SAP_SOAP_IMPLEMENTATION_READINESS

Fecha: 2026-09-22 · Veredicto de preparación para implementación futura (§41) · **NO implementación en esta fase**

---

## 1 · Veredicto

```
CONTRACT (lado GA)        = READY (documentado, consistente, trazable)
IMPLEMENTATION_READY      = NO (por diseño: prohibido implementar + confirmaciones del proveedor pendientes)
FASE DESBLOQUEADA AHORA   = SOAP-2 (mock del contrato; 0 dependencias externas)
FASES BLOQUEADAS          = SOAP-5/6 (sandbox/SAP real) hasta OI-01/06/15
```

## 2 · Matriz por fase

| Fase | Prerrequisitos | Estado |
|---|---|---|
| SOAP-1 Contrato | — | **COMPLETADA (docs)** |
| SOAP-2 Mock contract | contrato congelado (este paquete) | DESBLOQUEADA (cuando el Owner autorice fase) |
| SOAP-3 SoapSapAdapter | SOAP-2 + decisión implementación | PLANNED |
| SOAP-4 RAW/STAGING | SOAP-3 | PLANNED |
| SOAP-5 Sandbox integración | **OI-01, OI-06, OI-15** + entorno de red decidido | BLOCKED (proveedor) |
| SOAP-6 Prueba SAP real read-only | SOAP-5 | BLOCKED |
| SOAP-7 Reconciliación | SOAP-6 | BLOCKED |
| SOAP-8 Certificación | SOAP-7 | BLOCKED |

## 3 · Qué está listo (y verificable)

- Catálogo de **12 operaciones núcleo + 1 opcional** con request/response comunes.
- **13 objetos inbound** con campo a campo (obligatoriedad, claves, filtros, delta candidato, target GA).
- **Ejemplos XML** para 6 operaciones + Fault + error funcional.
- Contratos de **paginación, delta, errores, seguridad, versionado, WSDL/XSD, retry**.
- **RAW/STAGING** adaptado a SOAP (nunca directo a dominio).
- **Anexo legacy para ABAP** con filtros/joins/semántica histórica y clasificación.
- **Spec de cambio de adaptador GA** (interfaz inbound separada; export intacto).
- Trazabilidad AC-SOAP-01…20 y cadena spec-development (ver `15_…`).

## 4 · Qué falta (nada de GA antes de sus fases)

| Pendiente | Responsable | Ítem |
|---|---|---|
| Naming/WSDL/entorno | Proveedor SAP | OI-01/02/14 |
| Auth/TLS definitivo | Proveedor SAP + Seguridad | OI-06 |
| Delta real por objeto | Proveedor SAP | OI-04 |
| Semántica outbound orders / producción / vendors BP | Proveedor SAP + Negocio | OI-08/09/10 |
| Confirmación scope/COST_CENTER | Owner | OD-1 |
| Custodia de secretos | Owner (`AOD-12`) | no bloqueante para mock |

## 5 · Riesgos principales

| Riesgo | Mitigación en el paquete |
|---|---|
| Proveedor entrega WSDL incompatible | diff obligatorio contra `04_`/`05_` (`05_… §4`) |
| Payloads masivos | ventana obligatoria + paginación `09_…` |
| Contaminación legacy | anexo `11_…` con `DO_NOT_REUSE` explícito |
| Fuga de secretos | contrato de seguridad `08_…` + ejemplos placeholder |
| Cambios silenciosos de schema | versionado `SchemaVersion` obligatorio |

## 6 · Siguiente paso seguro

1. Enviar a la reunión: `03_`, `04_`, `05_`, `06_`, `07_`, `09_` (paquete del proveedor) + `13_…` (preguntas).
2. Con respuestas → actualizar contrato (v1.1 si aplica) y arrancar **SOAP-2 mock**.
3. Nada de implementación hasta que el Owner abra la fase correspondiente.

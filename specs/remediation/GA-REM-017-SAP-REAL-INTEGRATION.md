# GA-REM-017 — INTEGRACIÓN SAP REAL

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-017` · **Tipo** `INTEGRATION SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P1** · **Estado** `BLOCKED_EXTERNAL` |
| **Dependencias** | `GA-REM-010` (semántica) · `GA-REM-011` (`sap_document_ref`) · procesos internos estabilizados |
| **Hallazgos** | P0-7 · `GA-TD-007` · `tasks.md` T-085 |

## Estado: BLOCKED_EXTERNAL

**No se puede especificar la integración real con la información disponible en el proyecto.** Conforme al Art. 21.3 de la constitución y a §47 del encargo, se marca como bloqueada por dependencia externa y **no se simula éxito**.

### Información que falta y depende del cliente o de SAP
| Elemento | Estado |
|---|---|
| Mecanismo de integración (OData · SOAP · IDoc · RFC/BAPI) | `docs/10` menciona los cuatro; **no hay decisión** |
| URL del servicio | no disponible |
| Método de autenticación (Basic · OAuth · certificado) | no disponible |
| Estructura del payload esperado por SAP | no disponible |
| Estructura de la respuesta y códigos de error | no disponible |
| Credenciales | no disponibles (`.env.example` las tiene comentadas) |
| Catálogo de tipos de movimiento SAP (MIGO 101/201, etc.) | `mock_adapter.py` los menciona, sin confirmación del cliente |
| Ventanas de disponibilidad y política de reintentos acordada | no disponible |

Fuente parcial disponible: `Imagen de Procesos Documentado/Sap y App Proceso Avícola Software primera version.pdf` (34 páginas) — describe el proceso avícola y su relación con SAP, **no el contrato técnico**.

## Trabajo que SÍ puede avanzar sin desbloqueo

1. **Contrato interno**: definir el payload canónico que Global Avícola produce, independiente del transporte. Ya existe `SapExportPayload`.
2. **Idempotencia del lado servidor** (§33 del encargo): hoy `idempotency_key` no lo envía el frontend. **Decisión recomendada: generarla en el servidor**, de forma que el doble clic o un reintento tras timeout no produzcan duplicados. Esto es independiente de SAP y puede cerrarse en `GA-REM-011`.
3. **Trazabilidad de la referencia** (§34): `evento → petición → respuesta → referencia SAP → auditoría`, sin identificadores ficticios. Preparado por `GA-REM-010`.
4. **Mecanismo de reconciliación** (§35): definir el comportamiento ante `enviado pero no recibido` y ante `procesado por SAP con timeout en Global Avícola`. Se puede diseñar sin conocer el transporte.
5. **Batería de pruebas de contrato** contra un doble de pruebas, lista para conectarse al SAP real.

## Alcance cuando se desbloquee
Implementar `RealSapAdapter` conforme al contrato acordado, con autenticación, idempotencia, reintentos con retroceso exponencial correcto (el actual `(minuto + n) % 60` puede producir una fecha pasada — `GA-TD-038`), gestión de errores, timeouts, reconciliación y auditoría completa.

## Acceptance Criteria preliminares
**AC01** — un movimiento consolidado se envía a SAP y obtiene una referencia real de documento.
**AC02** — un reenvío del mismo movimiento no crea un documento duplicado en SAP.
**AC03** — un timeout no deja el sistema en un estado ambiguo: existe reconciliación.
**AC04** — un rechazo de SAP deja el evento en estado de error con el mensaje original.
**AC05** — ningún identificador ficticio aparece en `sap_document_ref`.
**AC06** — la cadena `evento → petición → respuesta → referencia → auditoría` es reconstruible.

## Definition of Done
- [ ] Contrato SAP acordado y documentado por el cliente · [ ] Credenciales disponibles en un entorno no productivo · [ ] AC01–AC06 verificados contra un SAP real o de pruebas · [ ] Certification report

## Acción inmediata mientras esté bloqueada
Solicitar formalmente al cliente el contrato técnico de integración. Registrar la fecha de la solicitud. **`GA-REM-010` debe cerrarse igualmente**, porque el problema de la falsa semántica no depende de SAP.

---

## Enmienda 2026-10-07 — SPEC 005 (SAP HANA Cloud READ ONLY inbound)

**Estado tras SPEC 005, por dirección:**

| Dirección | Estado | Fuente |
|---|---|---|
| **Inbound** (SAP → Global Avícola) | `IMPLEMENTED_LOCALLY_PENDING_EXTERNAL_CREDENTIALS` | `specs/005-sap-hana-cloud-readonly-inbound/` · `audit/sap-hana-cloud/11_LOCAL_CERTIFICATION.md` |
| **Outbound** (Global Avícola → SAP; AC01–AC06 de esta spec) | `BLOCKED_EXTERNAL` y además `DISABLED_PHASE_1` (`SAP_OUTBOUND_ENABLED=false`) | mandato SPEC 005 §38 |

Qué cambió:

- El mecanismo inbound **ya no es una incógnita**: es SAP HANA Cloud en solo lectura (decisión Owner/Sponsor 2026-10-06; `audit/sap-hana-cloud/01_ARCHITECTURE_DECISION.md`). La fila «Mecanismo de integración… no hay decisión» de la tabla superior queda resuelta **para inbound**; para outbound sigue abierta.
- Existe un adaptador inbound real (`HanaCloudReadOnlyAdapter`, `backend/app/integrations/sap/inbound/`) certificado localmente con un doble de HANA. No se ha conectado a SAP: `SAP_HANA_REAL = PENDING_CREDENTIALS`.
- `RealSapAdapter` (outbound) **sigue sin implementar**; `SAP_ADAPTER=real` responde 501 y `/sap/export` · `/sap/retry` responden 409 en esta fase. AC01–AC06 permanecen pendientes y fuera del alcance de SPEC 005.
- La información externa que falta se reduce a: credencial técnica READ ONLY, endpoint/schema/mandante y ventana de red/CA (`audit/sap-hana-cloud/12_REAL_SAP_ACTIVATION_RUNBOOK.md §0`).

El estado de cabecera (`BLOCKED_EXTERNAL`) se conserva porque describe la integración real completa; esta enmienda lo precisa sin reescribir la historia (constitución Art. 15).

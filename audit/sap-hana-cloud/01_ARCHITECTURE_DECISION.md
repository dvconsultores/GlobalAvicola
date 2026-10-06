# SAP-HANA-CLOUD · 01_ARCHITECTURE_DECISION

Fecha: 2026-10-06 · Fase: **SPEC 005 — SAP HANA Cloud READ ONLY Inbound Integration** (baseline `cf991b4`; sin conexiones reales a SAP)
Origen: mandato Owner/Sponsor «SPEC 005 — SAP HANA Cloud READ ONLY Inbound Integration» (2026-10-06)
Estado: **DECISIÓN FORMALIZADA** (acta documental; reemplaza el target inbound SOAP del 2026-09-22 sin borrar su historia) · Implementación: `IMPLEMENTING` (`specs/005-sap-hana-cloud-readonly-inbound/spec.md`)

---

## 1 · Decisión (valores canónicos del mandato)

```text
SAP_INBOUND_TARGET     = SAP_HANA_CLOUD_READ_ONLY
GLOBAL_AVICOLA_ROLE    = HANA_READ_ONLY_CONSUMER + INTERNAL_API_PROVIDER
SAP_TECHNICAL_USER     = READ_ONLY
SAP_WRITES_PHASE_1     = FORBIDDEN
SAP_OUTBOUND_PHASE_1   = DISABLED
LEGACY_HANA_QUERIES    = REFERENCE_ONLY
RAW_STAGING            = RETAINED
ADAPTER_PATTERN        = RETAINED
FAIL_CLOSED            = RETAINED
IDEMPOTENCY            = RETAINED
AUDIT                  = RETAINED
MULTICOMPANY_ISOLATION = RETAINED
SOAP_INBOUND_TARGET    = SUPERSEDED_BY_OWNER_SPONSOR_DECISION_2026_10_06
```

Implementación asociada: `IMPLEMENTATION = SAP_HANA_CLOUD_READ_ONLY_V2`. El Direct HANA legacy **no** se reactiva (ver §4).

## 2 · Addendum cronológico

| Fecha | Decisión inbound | Estado actual | Registro |
|---|---|---|---|
| Original (2026-06-23) | OData recomendado | `SUPERSEDED_BY_OWNER_AND_PROVIDER_DECISION` (para inbound) | `docs/10-sap-integration-strategy.md` §8 |
| 2026-09-22 | SOAP inbound seleccionado (pull; proveedor SAP = server, GA = consumer) | `CLOSED_HISTORICAL_CONTRACT_NOT_IMPLEMENTED` | `audit/sap-soap/**` · `specs/003-sap-soap-inbound-contract/` |
| 2026-10-06 | **Sponsor/Owner selecciona SAP HANA Cloud READ ONLY para inbound** | **vigente** | este documento · `specs/005-sap-hana-cloud-readonly-inbound/` |

Nada histórico se borra ni se reescribe: los documentos anteriores reciben un puntero o un addendum.

## 3 · Estado de SOAP inbound

```text
SOAP_INBOUND_CONTRACT       = CLOSED_HISTORICAL_CONTRACT_NOT_IMPLEMENTED
SOAP_INBOUND_IMPLEMENTATION = SUPERSEDED_FOR_INBOUND_IMPLEMENTATION
```

- El contrato SOAP (12 operaciones / 13 objetos) quedó en `SPEC ONLY`: nunca se implementó cliente, mock ni adaptador.
- El paquete `audit/sap-soap/**`, `specs/003-…` y el documento cliente-facing se conservan íntegros como historia. Addendum: `audit/sap-soap/SAP_SOAP_ADDENDUM_2026-10-06_SUPERSEDED_BY_HANA_CLOUD_READONLY.md`.

## 4 · Por qué NO es la reactivación del Direct HANA legacy

El 2026-09-22 el Direct HANA quedó `RETIRED_AS_TARGET_ARCHITECTURE`. La decisión del 2026-10-06 cambia el target inbound, pero el patrón legacy (`SapHanaLP`, auditado en SAP-0) sigue `DO_NOT_REUSE`.

| Aspecto | Direct HANA legacy (`DO_NOT_REUSE`) | `SAP_HANA_CLOUD_READ_ONLY_V2` (SPEC 005) |
|---|---|---|
| Origen del SQL | SQL libre en `querysHana.py`, acoplado al orquestador | registry cerrado de 14 definiciones; ninguna ruta acepta SQL ni existe proxy genérico |
| Valores y filtros | literales incrustados (mandante, centros, listas MATNR, BWART, fechas) | parámetros bind; el único identificador interpolado es el schema, tomado de `Settings` y validado |
| Escritura a SAP | sin barrera en código (la capacidad existe por el driver) | guard de solo lectura: una sola sentencia, inicia en `SELECT`/`WITH`, sin tokens mutantes ni `CALL`/`DO` |
| TLS | `verify=False` en el cliente SOAP; conexión HANA sin opciones TLS registradas (SAP-0 T-01, T-18) | TLS y validación de certificado obligatorios; una configuración que los desactive se rechaza antes de conectar |
| Procesamiento | pandas + tablas temporales (`to_sql if_exists='replace'`, `sleep(3)`) | RAW inmutable con hash y versión → STAGING (capa lógica) → promoción controlada |
| Destino | UPSERT directo a tablas de dominio (`operations.py`) | solo `sap_references`, por clave canónica; objetos sin tipo de referencia quedan `STAGED_ONLY` |
| Multiempresa | mandante y centros fijos en el SQL | mapping fail-closed `MANDT → BUKRS → WERKS → empresa GA`; sin resolución inequívoca ⇒ `PENDING_MAPPING`, sin promoción |
| Idempotencia | UPSERT manual sin idempotencia nativa (SAP-0 T-21) | misma clave + mismo hash = no-op; hash nuevo = versión nueva; el watermark solo avanza tras persistir |
| Auditoría | sin traza por ejecución documentada en SAP-0 | job reconstruible: query, filtros saneados, watermarks y contadores |
| Ejecución | job 06/10/14/18 h + al arrancar; driver dentro del orquestador | conexión lazy, fuera del event loop, una conexión por llamada; scheduler apagado por defecto y sin solape |
| Red | VPN embebida en el contenedor (host network, `NET_ADMIN`) | no se reutiliza; la SPEC 005 no añade VPN ni privilegios de red al backend |

## 5 · Flujo único permitido

```text
SYNC → HANA READ ONLY CONNECTOR (SELECT) → RAW → VALIDATION → MAPPING
     → STAGING → CONTROLLED PROMOTION → sap_references
```

- `HANA → DOMAIN DIRECTLY` nunca. No se expone SQL al frontend ni se acepta SQL desde HTTP; Global Avícola consume HANA en solo lectura y provee la API interna `/api/v1/sap/inbound/*`.
- Toda sincronización exige empresa efectiva (R-201): sin contexto falla cerrado antes de tocar HANA.

## 6 · Prohibiciones de escritura SAP (fase 1) y defensa en profundidad

```text
FORBIDDEN_PHASE_1 =
  INSERT · UPDATE · DELETE · MERGE · UPSERT · CALL con efectos · DDL
  BAPI/RFC write · OData write · SOAP write · creación de documentos SAP
```

| Capa | Barrera | Fuente |
|---|---|---|
| 1 · Origen | usuario técnico SAP `READ_ONLY` (no verificable hasta disponer de la credencial) | mandato |
| 2 · Registry | toda sentencia proviene del registry interno; registrar DML se rechaza aunque el usuario tuviera privilegios de más | FR-02 · AC-HANA-06 |
| 3 · Guard | una sola sentencia, `SELECT`/`WITH`, sin tokens mutantes; `CALL` y `DO` se rechazan siempre | FR-02 · AC-HANA-11 |
| 4 · Binds | los valores nunca se concatenan al SQL | FR-03 · AC-HANA-12 |
| 5 · Superficie | ninguna ruta acepta SQL; sin endpoint de SQL arbitrario | AC-HANA-04 · AC-HANA-10 |
| 6 · Outbound | `SAP_OUTBOUND_ENABLED=false` ⇒ `/sap/export` y `/sap/retry` responden `409 SAP_OUTBOUND_DISABLED_READ_ONLY_PHASE`; `SAP_ADAPTER=real` sigue en 501; `delivers_to_sap=false` | FR-16 · Q12 |
| 7 · Transporte | TLS y validación de certificado obligatorios | FR-04 · AC-HANA-08/09 |
| 8 · Autorización | `sap:send_sap` autoriza operar el conector; **no** autoriza escribir en SAP | `plan.md` §3 |

## 7 · Fuera de alcance y diferido

| Elemento | Estado | Razón (`spec.md` §OUT_OF_SCOPE) |
|---|---|---|
| `SAP_COST_CENTER` | `DEFERRED_PHASE_1` | sin consumidor |
| `SAP_INVENTORY_SNAPSHOT` | `DEFERRED_PHASE_1` | requiere aprobación de MARD |

También fuera: adaptador outbound real · go-live productivo · migración formal de inventario · costeo/cierre SAP · reversos vía escritura · convergencia destructiva de maestros locales (OD-24) · UI de administración de mappings (se entrega la API). `ZwsTasaMortalidad` es outbound: fuera de esta decisión.

## 8 · Qué se conserva

- **RAW/STAGING + promoción controlada**, **Adapter Pattern** (interfaz inbound separada del ABC de export, para no diluir `delivers_to_sap`), **fail-closed multiempresa**, **idempotencia**, **auditoría**.
- **GA-REM-010** intacta: `NO VERIFIED SAP DELIVERY = NO TRUE sent_to_sap`. No se inventan confirmaciones ni IDs SAP.
- **BR-18** sin cambio de regla: solo cambia la fuente de `SapReference.quantity`. **OD-24**: `Company ↔ BUKRS`, `Plant ↔ Farm`; `LGORT ≠ galpón`; sin migración destructiva.

## 9 · Estados declarables

```text
NO DECLARABLE SIN CREDENCIAL READ ONLY Y PROBE REAL:
  SAP_REAL_CONNECTION          = PASS
  SAP_REAL_DATA_RECONCILIATION = PASS

OBJETIVO DE ESTA FASE (aún NO alcanzado a la fecha de este documento):
  LOCAL_IMPLEMENTATION = CERTIFIED
  SAP_HANA_REAL        = PENDING_CREDENTIALS
  READINESS            = READY_FOR_SAP_CREDENTIALS
```

- `READY_FOR_SAP_CREDENTIALS` solo puede declararse si no queda deuda de código (AC-HANA-55); lo registra `11_LOCAL_CERTIFICATION.md`. La certificación local es evidencia del agente ejecutor; el cierre formal lo da el Owner (constitución Art. 9).
- Target posterior con credencial: `SAP_HANA_READONLY_CONNECTED_AND_RECONCILED`, tras el probe de `12_REAL_SAP_ACTIVATION_RUNBOOK.md`.
- Ninguna tabla está verificada contra el landscape real (SAP-0P = 0/12): cada definición declara `LEGACY_CONFIRMED` o `CANDIDATE`.

## 10 · Referencias

`specs/005-sap-hana-cloud-readonly-inbound/{spec,plan,research,data-model,tasks}.md` · `02_LEGACY_QUERY_AUDIT.md` · `audit/sap-soap/01_SAP_SOAP_ARCHITECTURE_DECISION.md` · `audit/sap0/SAP_LEGACY_REPOSITORY_AUDIT.md` · addenda 2026-10-06 en `audit/sap-soap/`, `audit/sap0/`, `audit/sap0p/` · `docs/10-sap-integration-strategy.md`

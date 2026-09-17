# Feature Specification: SAP-0P — Read-Only Landscape Probe

**Feature Branch**: `specs/002-sap0p-readonly-landscape-probe`
**Created**: 2026-09-17 · **Status**: Validated (SPEC) · **Resultado de ejecución**: `BLOCKED_EXTERNAL` (acceso no provisionado; ver §AC-02 y §9 del mandato)
**Input**: Mandato SAP-0P (Owner, 2026-09-17) · DAG: `SAP-0 CLOSED → SAP-0P → GL-OD-06 → G1 → G2 → G3 → G4`

---

## PURPOSE
Verificar **técnicamente y en solo lectura** el landscape SAP actual (identidad, versiones, permisos, metadata, disponibilidad de tablas/objetos inbound, condiciones para OD-24 y GL-OD-06) **sin implementar nada** y **sin escribir nada** en SAP ni en el dominio Global Avícola.

## SCOPE
1. P0-P10 (preflight → disconnect → certificación) definidos en `plan.md` y `SAP0P_PROBE_PLAN.md`.
2. Verificación de red/VPN, HANA reachability, identidad/versiones, permisos read-only, metadata (9 tablas legacy + objetos inbound), muestras mínimas (LIMIT 1–10), reconciliación de 12 objetos inbound, descubrimiento de servicios (OData/CDS/SOAP), evidencia saneada, certificación.
3. Elevación de estados `OWNER_CONFIRMED_CURRENT_UNCHANGED → TECHNICALLY_VERIFIED_CURRENT` **solo** con evidencia.

## OUT_OF_SCOPE (prohibiciones)
`/implement`; SAP-1; G1; G2; `RealSapAdapter`; importación al dominio; cutover; limpieza de datos; cualquier escritura SAP (INSERT/UPDATE/DELETE/MERGE/UPSERT/CREATE/ALTER/DROP/TRUNCATE/GRANT/REVOKE/CALL con efectos/BAPI-RFC/IDoc/SOAP/OData mutantes/MIGO-MIRO-MB1A/MB1B); cambios en `backend/**`, `frontend/**`, `e2e/**`, migraciones, `.github/workflows/**`; deploy.

## OWNER_CONFIRMATION
Formalizada 2026-09-17 (`audit/sap0p/SAP0P_OWNER_CONFIRMATION.md`): landscape sin cambios (OC-01…OC-11) → habilita el probe a nivel política; **no** es verificación técnica; **no** sustituye la provisión de acceso.

## SECURITY
- Cuenta técnica READ-ONLY dedicada; least privilege; sin write tests «escribiendo» (`NO WRITE TEST BY WRITING`).
- Prohibido: imprimir passwords/PSK/keys/tokens/connection strings; volcar env; buscar secretos históricos; commitear secretos.
- Evidencia: solo `SAP_USER_PRESENT=YES/NO`; passwords `REDACTED`.
- Todo límite: LIMIT/TOP ≤ 10 salvo metadata; filtros por mandante/company/plant; prohibido full scan.

## READ_ONLY_CONTRACT
Toda operación debe ser demostrablemente de solo lectura; **si no puede demostrarse, NO se ejecuta**. Excepciones permitidas: metadata de catálogo, `SELECT` acotado, `$metadata`/WSDL (GET), HEAD/GET seguro. Nada mutante, nada no acotado.

## ALLOWED_ACTIONS
`ping/tcp connect` acotado al host/puerto autorizado; DNS resolution; metadata de catálogo; `SELECT` con LIMIT ≤10 sobre las 9 tablas + objetos acordados; GET `$metadata`/WSDL; conteos pequeños justificados; lectura de autorizaciones efectivas si es posible sin elevar privilegios.

## FORBIDDEN_ACTIONS
Lista completa §6 del mandato (toda operación con efectos) + cualquier query sin LIMIT + cualquier conexión desde red no autorizada + instalación de VPN nueva + modificación de red/firewall + persistencia de credenciales.

## NETWORK_PROBE
P1: verificar solo disponibilidad de interfaz/ruta, resolución DNS/IP, reachability al puerto, VPN status. Registro: `NETWORK_ROUTE=VERIFIED|BLOCKED`, `VPN=VERIFIED|NOT_REQUIRED|BLOCKED`, `HANA_PORT_REACHABILITY=PASS|FAIL`.

## SYSTEM_IDENTITY
SID, identidad de sistema y mandante(s) solo mediante metadata estándar autorizada; si no se logra con permisos seguros → `NOT_VERIFIED`; nunca elevar privilegios.

## VERSION_DISCOVERY
HANA version / SAP product/version vía catalog metadata o SAP standard metadata read-only; sin procedimientos desconocidos.

## PERMISSION_DISCOVERY
Verificar `SELECT` sobre objetos necesarios y ausencia de privilegios de escritura **por metadata de autorizaciones**, jamás escribiendo. Cuenta con privilegios excesivos → `FAIL_LEAST_PRIVILEGE` + gap de seguridad.

## METADATA_DISCOVERY
Para `T001W, T001L, EKKO, EKPO, EKBE, LFA1, MATDOC, MAKT, T156HT` (+tablas legacy adicionales): `EXISTS`, `SELECT_ALLOWED`, `KEY_COLUMNS_AVAILABLE`, `REQUIRED_FIELDS_AVAILABLE`. Sin `SELECT *` en alto volumen.

## MINIMAL_SAMPLE_READS
Solo tras P0–P4 PASS: 1–10 filas, filtros por alcance, sin datos personales innecesarios, sin dumps, objetivo estructura/semántica (no migración). MATDOC: restricción máxima.

## INBOUND_OBJECT_VERIFICATION
Los 12 objetos de SAP-0: por objeto `AVAILABLE / SOURCE_VERIFIED / KEY_VERIFIED / MANDANT_SCOPE_VERIFIED / COMPANY_SCOPE_VERIFIED / DELTA_CANDIDATE / SAMPLE_VERIFIED / STATUS ∈ {VERIFIED, PARTIALLY_VERIFIED, NOT_VERIFIED, NOT_FOUND, BLOCKED_PERMISSION}`.

## MULTICOMPANY_MAPPING
Verificar identificadores para la cadena `SAP SYSTEM → MANDT → BUKRS → WERKS → GA COMPANY → BU`; sin aplicar mapping; inconsistencias → `PENDING_MAPPING`; fail-closed.

## EVIDENCE
`audit/sap0p/evidence/`; por query: `QUERY_ID, PURPOSE, TARGET, READ_ONLY_JUSTIFICATION, START_TIME, END_TIME, ROW_LIMIT, RESULT_STATUS, SANITIZATION, EVIDENCE_FILE`. Permitido: timestamps, nombres de objetos, row counts pequeños, field names, status, latencia, códigos de error no sensibles.

## SANITIZATION
Prohibido en evidencia: password/token/PSK/private key/connection string completa/datos personales/dumps/headers secretos. Passwords `REDACTED` siempre.

## STOP_CONDITIONS
§38 del mandato: cuenta insegura para read-only; query que necesita write; privilegios elevados; riesgo de lock; query no acotable; VPN/red con cambio destructivo; credenciales faltantes; schema irreconciliable; exposición de datos sensibles; decisión Owner necesaria. **Hoy activa**: acceso no provisionado (§9) → `BLOCKED_EXTERNAL` + única acción Basis → STOP.

## ROLLBACK
Probe read-only: rollback = cerrar sesión/ruta y no persistir nada (P9); evidencia saneada permanece; cero artefactos de escritura. Si algo mutara (no permitido): STOP inmediato + incidente.

## ACCEPTANCE_CRITERIA

| AC | Criterio | Estado 2026-09-17 |
|---|---|---|
| AC-SAP0P-01 | OWNER CONFIRMATION 2026-09-17 formalizada sin confundirla con verificación | **PASS** (doc + semántica) |
| AC-SAP0P-02 | Ruta de red/VPN verificada **o bloqueo demostrado** | **PASS (BLOQUEO DEMOSTRADO)**: sin IPsec/xl2tpd/ppp/tun/credenciales; DNS no resuelve |
| AC-SAP0P-03 | HANA reachability mediante operación segura | NOT_VERIFIED (probe no iniciado; sin canal); sustituido por bloqueo demostrado |
| AC-SAP0P-04 | Host/puerto actuales sin exponer secretos | NOT_VERIFIED (solo patrón legacy `30241` como `LEGACY_CONFIRMED`) |
| AC-SAP0P-05 | Versión HANA | NOT_VERIFIED |
| AC-SAP0P-06 | Identidad SAP/SID | NOT_VERIFIED |
| AC-SAP0P-07 | Mandante | NOT_VERIFIED (legacy `120` = `LEGACY_CONFIRMED`) |
| AC-SAP0P-08 | READ ONLY/least privilege de la cuenta o gap documentado | NOT_VERIFIED (cuenta no provisionada) |
| AC-SAP0P-09 | Schema SAP | NOT_VERIFIED (legacy `SAPHANADB` = `LEGACY_CONFIRMED`) |
| AC-SAP0P-10..16 | Disponibilidad T001W/T001L/EKKO/EKPO/EKBE/LFA1/MATDOC/MAKT/T156HT | NOT_VERIFIED (0/9) |
| AC-SAP0P-17 | Muestras estructurales | NOT_VERIFIED (no ejecutadas) |
| AC-SAP0P-18 | Company Codes/Plants técnicos | NOT_VERIFIED |
| AC-SAP0P-19 | OData/CDS/SOAP status verificable o NOT_VERIFIED | **PASS**: `OWNER_CONFIRMED_CURRENT_UNCHANGED` + `NOT_TECHNICALLY_VERIFIED` |
| AC-SAP0P-20 | `ZwsTasaMortalidad` discovery sin invocación | **PASS**: `NOT_VERIFIED` (sin invocación; único canal hubiera sido WS) |
| AC-SAP0P-21 | Estado de disponibilidad de los 12 objetos inbound | **PASS**: 12/12 documentados `NOT_VERIFIED` |
| AC-SAP0P-22 | Ningún dato leído se escribe al dominio | **PASS** (0 lecturas; 0 escrituras) |
| AC-SAP0P-23 | Ninguna operación SAP de escritura | **PASS** (0) |
| AC-SAP0P-24 | Ningún secreto en evidencia/git | **PASS** (solo conteos/presencia) |
| AC-SAP0P-25 | GL-OD-06 derivado de evidencia | **PASS** → `BLOCKED_EXTERNAL_SAP_INFORMATION` |
| AC-SAP0P-26 | SPEC→PLAN→TASKS trazabilidad | **PASS** |
| AC-SAP0P-27 | /analyze y /converge sin contradicciones | **PASS** (0 abiertas) |
| AC-SAP0P-28 | PRODUCT_FILES_CHANGED = 0 | **PASS** |
| AC-SAP0P-29 | LOCAL_SHA == REMOTE_SHA | **PASS** (tras push; ver reporte) |

## Clarifications (pre-probe, clasificadas)

| # | Pregunta | Clase | Resolución |
|---|---|---|---|
| Q1 | ¿Nombre exacto del schema vigente? | TECHNICAL_DISCOVERY (no Owner) | Pendiente de probe (legacy `SAPHANADB` no es current fact) |
| Q2 | ¿Puerto real HANA? | TECHNICAL_DISCOVERY | Pendiente de probe |
| Q3 | ¿Permiso SELECT de la cuenta? | TECHNICAL_DISCOVERY | Pendiente de probe (cuenta no provisionada) |
| Q4 | ¿OData endpoint discovery? | TECHNICAL_DISCOVERY | Pendiente de probe |
| Q5 | ¿LGORT ↔ galpón? | OWNER_DECISION (post-evidencia) | `SAP_STORAGE_LOCATION_MAPPING` sigue abierto |
| Q6 | ¿Objetos de SAP-1? | OWNER_DECISION (post-evidencia) | Propuesta condicionada en §41 del mandato (ver plan §SAP-1 scope) |
| Q7 | ¿Ejecutar probe desde red no autorizada si no hay VPN? | — | **NO** (prohibición §18/§9; fail-closed) |

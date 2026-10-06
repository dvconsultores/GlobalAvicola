# Feature Specification: SPEC 005 — SAP HANA Cloud READ ONLY Inbound Integration

**Directorio**: `specs/005-sap-hana-cloud-readonly-inbound` · **Rama**: `main` (`DO_NOT_CREATE_BRANCH = TRUE`; sin rama de feature)
**Created**: 2026-10-06 · **Baseline**: `cf991b4` · **Status**: `IMPLEMENTING`
**Tipo**: integración externa (inbound, solo lectura) · **Prioridad**: P1 · **Dependencias**: GA-REM-010, GA-REM-017, OD-12, OD-14, OD-24, R-201, BR-18
**Input**: Mandato Owner/Sponsor «SPEC 005 — SAP HANA Cloud READ ONLY Inbound Integration» (2026-10-06)
**Paquete de auditoría asociado**: `audit/sap-hana-cloud/01…13`
**Target local**: `READY_FOR_SAP_CREDENTIALS` · **Target posterior con credencial**: `SAP_HANA_READONLY_CONNECTED_AND_RECONCILED`

---

## PURPOSE

Construir y certificar localmente la integración inbound de Global Avícola con SAP HANA Cloud en modo **solo lectura**, de modo que la única dependencia externa restante sea cargar la credencial técnica READ ONLY y ejecutar el probe real (`audit/sap-hana-cloud/12_REAL_SAP_ACTIVATION_RUNBOOK.md`).

## PROBLEM / EVIDENCE

| Hecho | Evidencia |
|---|---|
| No existe adaptador inbound: las referencias SAP se cargan a mano | `backend/app/integrations/sap/service.py` (`import_references`), `audit/sap-soap/12_… §1` |
| `SAP_ADAPTER=real` responde 501 | `service.py` (`get_adapter`), GA-REM-017 `BLOCKED_EXTERNAL` |
| BR-18 depende de `SapReference.quantity`, que solo llega por importación manual | `backend/app/operations/validators.py:827` |
| El probe SAP-0P no se ejecutó: 0/12 objetos verificados | `audit/sap0p/SAP0P_INBOUND_OBJECT_VERIFICATION.md` |
| La decisión SOAP (2026-09-22) no llegó a implementarse | `specs/003-…` (`SPEC ONLY`) |

## ARCHITECTURE_DECISION

```text
SAP_INBOUND_TARGET = SAP_HANA_CLOUD_READ_ONLY        GLOBAL_AVICOLA_ROLE = HANA_READ_ONLY_CONSUMER + INTERNAL_API_PROVIDER
SAP_TECHNICAL_USER = READ_ONLY                       SAP_WRITES_PHASE_1 = FORBIDDEN
SAP_OUTBOUND_PHASE_1 = DISABLED                      LEGACY_HANA_QUERIES = REFERENCE_ONLY
SOAP_INBOUND_TARGET = SUPERSEDED_BY_OWNER_SPONSOR_DECISION_2026_10_06   (historia preservada)
IMPLEMENTATION = SAP_HANA_CLOUD_READ_ONLY_V2         (el Direct HANA legacy NO se reactiva)
RETENIDOS = RAW_STAGING · ADAPTER_PATTERN · FAIL_CLOSED · IDEMPOTENCY · AUDIT · MULTICOMPANY_ISOLATION
```

Flujo único permitido: `SYNC → HANA READ ONLY CONNECTOR (SELECT) → RAW → VALIDATION → MAPPING → STAGING → CONTROLLED PROMOTION → sap_references`. No se expone SQL al frontend, no se acepta SQL desde HTTP y no existe un proxy genérico hacia HANA. Cronología y supersession en `audit/sap-hana-cloud/01_ARCHITECTURE_DECISION.md`.

## SCOPE

1. Paquete `backend/app/integrations/sap/inbound/`: configuración, cliente `hdbcli` (lazy, TLS obligatorio, fuera del event loop), guard de solo lectura, query registry cerrado, adaptador (`SapInboundAdapter` → `HanaCloudReadOnlyAdapter`), pipeline RAW→STAGING→promoción, servicio, rutas y scheduler.
2. **14 objetos** con ruta de adaptador: `company, plant, storage_location, vendor, material, batch, movement_type, purchase_order, purchase_order_item, purchase_order_history, production_order, transfer_order, outbound_order, material_movement`.
3. Persistencia nueva (Alembic): `sap_inbound_sync_jobs`, `sap_inbound_records`, `sap_inbound_watermarks`, `sap_entity_mappings`.
4. API interna `/api/v1/sap/inbound/*` + `connection-check` que distingue `inbound_hana` / `outbound`.
5. Outbound deshabilitado: `SAP_OUTBOUND_ENABLED=false` ⇒ `/sap/export` y `/sap/retry` responden `409 SAP_OUTBOUND_DISABLED_READ_ONLY_PHASE`.
6. Frontend `SapManagerPage`: estado inbound, objetos, jobs, registros, errores, botón Sincronizar (`sap:send_sap`); exportación oculta mientras outbound esté deshabilitado; i18n ES/EN.
7. Pruebas: unitarias, integración con fake HANA, E2E local, mutación (S1–S8), regresión completa.
8. Documentación y evidencia (`audit/sap-hana-cloud/**`), addenda a `docs/10`, SOAP, SAP-0/0P y GA-REM-017.

## OUT_OF_SCOPE

Escritura a SAP por cualquier vía (DML, DDL, `CALL`, BAPI/RFC, OData, SOAP) · creación de documentos SAP · adaptador outbound real · go-live productivo · migración formal de inventario · costeo/cierre SAP · reversos vía escritura · `SAP_COST_CENTER` (`DEFERRED_PHASE_1`, sin consumidor) · `SAP_INVENTORY_SNAPSHOT` (`DEFERRED_PHASE_1`, requiere aprobación de MARD) · convergencia destructiva de maestros locales (OD-24) · UI de administración de mappings (se entrega la API).

## REQUIREMENTS

| ID | Requisito |
|---|---|
| FR-01 | El backend arranca sin credenciales HANA; la conexión es lazy y ninguna ruta llama a HANA si no está configurado. |
| FR-02 | Toda sentencia ejecutada proviene del registry interno y pasa el guard: una sola sentencia, inicia en `SELECT`/`WITH`, sin tokens mutantes ni `CALL`/`DO`. |
| FR-03 | Los valores viajan como parámetros bind; el único identificador interpolado es el schema, tomado de `Settings` y validado. |
| FR-04 | TLS y validación de certificado son obligatorios; una configuración que los desactive se rechaza antes de conectar. |
| FR-05 | Las llamadas `hdbcli` se ejecutan con `asyncio.to_thread`, una conexión y un cursor por llamada, cerrados en `finally`, con concurrencia acotada y timeouts. |
| FR-06 | Paginación con orden estable, `page_size` acotado, ventana temporal obligatoria en objetos documentales y tope `SAP_HANA_MAX_ROWS_PER_SYNC`. |
| FR-07 | RAW idempotente: misma clave + mismo hash = no-op; misma clave + hash nuevo = versión nueva; una página repetida no duplica. |
| FR-08 | El watermark solo avanza tras persistir el batch; si el batch falla queda intacto. |
| FR-09 | Mapping fail-closed `MANDT → BUKRS → WERKS → empresa GA`: sin resolución inequívoca ⇒ `PENDING_MAPPING`, sin promoción, sin fallback. |
| FR-10 | Toda sincronización exige empresa efectiva (R-201): sin contexto falla cerrado antes de leer la base o tocar HANA. |
| FR-11 | La promoción hace upsert de `sap_references` por `(company_id, ref_type, sap_code)`; los objetos sin tipo de referencia quedan en staging (`STAGED_ONLY`), nunca en `OTHER`. |
| FR-12 | Una OC promovida deja `SapReference.quantity` = Σ de ítems activos de unidad homogénea, con desglose en `extra_data`; BR-18 se aplica sin cambios. |
| FR-13 | Los errores usan la lista cerrada `SAP_*` y nunca exponen contraseña, cadena de conexión, SQL con valores ni stack trace. |
| FR-14 | Cada sync queda auditado y es reconstruible (job con query, filtros saneados, watermarks y contadores). |
| FR-15 | Rutas nuevas con RBAC (`sap:read` / `sap:send_sap`), alcance de unidad declarado y frontera transaccional. |
| FR-16 | Outbound deshabilitado por defecto; `delivers_to_sap` sigue en `false`; no se inventan confirmaciones ni IDs SAP. |
| FR-17 | El scheduler no corre en tests, no solapa jobs, no reintenta en bucle y no llama a HANA sin configuración. |
| FR-18 | Una columna obligatoria ausente en la respuesta ⇒ `SAP_SCHEMA_MISMATCH`; nunca se rellena con `NULL`. |

## BUSINESS RULES AFFECTED

BR-18 (límite acumulado de OC: sin cambios de regla, nueva fuente de `quantity`) · GA-REM-010 (`NO VERIFIED SAP DELIVERY = NO TRUE sent_to_sap`, intacta) · OD-12 (contrato SAP transversal, mismos permisos) · OD-14.d / R-201 (sin empresa ⇒ ∅) · OD-24 (`Company ↔ BUKRS`, `Plant ↔ Farm`; `LGORT ≠ galpón`; sin migración destructiva).

## AFFECTED LAYERS

| Capa | Cambio |
|---|---|
| Backend | paquete `integrations/sap/inbound/` (nuevo); `config.py`, `main.py`, `sap/router.py`, `sap/service.py`, `route_scope.py`, `sap_contract.py`, `scripts/data_classification.py`, `scripts/run_tests.sh` |
| Base de datos | 4 tablas nuevas, 1 migración con `downgrade`; ningún enum existente se altera |
| Frontend | `pages/sap/SapManagerPage.tsx`, `services/sap.service.ts`, locales ES/EN |
| Seguridad | sin permisos nuevos (OD-12 `REUSE`); secretos solo por entorno |
| Compatibilidad | `/sap/references` y el contrato de `SapReference` se conservan; `/sap/export` y `/sap/retry` pasan a 409 mientras outbound esté deshabilitado |

## ERRORS

`SAP_CONFIG_MISSING · SAP_DRIVER_UNAVAILABLE · SAP_DNS_ERROR · SAP_TLS_ERROR · SAP_AUTH_ERROR · SAP_AUTHORIZATION_ERROR · SAP_QUERY_TIMEOUT · SAP_QUERY_CONTRACT_ERROR · SAP_SCHEMA_MISMATCH · SAP_OBJECT_NOT_FOUND · SAP_MAPPING_PENDING · SAP_VALIDATION_ERROR · SAP_TEMPORARY_UNAVAILABLE · SAP_INTERNAL_ERROR`

## EDGE CASES

OC con ítems de unidades distintas (promoción bloqueada, visible en errores) · OC con todos los ítems borrados (referencia inactiva) · mismo `EBELN` en dos empresas · fila con `BUKRS` de otra empresa GA (no se persiste) · página repetida · batch que falla a mitad · tope de filas alcanzado (job `partial`, watermark intacto) · referencia manual duplicada con la misma clave (promoción bloqueada) · sync concurrente del mismo objeto (se omite) · credenciales ausentes · TLS desactivado por configuración.

## ACCEPTANCE CRITERIA

Formato: **Given** el contexto, **When** la acción, **Then** el resultado observable. Evidencia en `audit/sap-hana-cloud/09_TEST_MATRIX.md`.

| AC | Criterio | Verificación |
|---|---|---|
| AC-HANA-01 | Given el repo, When se lee `01_ARCHITECTURE_DECISION`, Then la decisión HANA Cloud READ ONLY consta formalizada | doc |
| AC-HANA-02 | Given los artefactos SOAP, When se consultan, Then llevan puntero `SUPERSEDED` y nada se borró | git diff |
| AC-HANA-03 | Given las queries legacy, When se audita el código, Then ninguna se ejecuta ni se copia literal | `02_LEGACY_QUERY_AUDIT`, test anti-hardcode |
| AC-HANA-04 | Given la API, When se enumeran rutas, Then ninguna acepta SQL | `test_hana_no_raw_sql_endpoint` |
| AC-HANA-05 | Given la configuración por defecto, When se llama `/sap/export` o `/sap/retry`, Then 409 y sin entrega | `test_outbound_disabled` |
| AC-HANA-06 | Given un usuario con privilegios de más, When se intenta registrar DML, Then el registry lo rechaza | tests del guard |
| AC-HANA-07 | Given repo, logs y docs, When se escanean, Then 0 credenciales | escaneo de secretos |
| AC-HANA-08 | Given cualquier conexión, When se construyen sus opciones, Then `encrypt=True` | `test_hana_adapter_tls_required` |
| AC-HANA-09 | Given cualquier conexión, When se construyen sus opciones, Then `sslValidateCertificate=True`; si la configuración lo niega, se rechaza | ídem |
| AC-HANA-10 | Given las rutas, When se buscan cuerpos con SQL, Then no existe endpoint de SQL arbitrario | `test_hana_no_raw_sql_endpoint` |
| AC-HANA-11 | Given una sentencia con DML/DDL/`CALL` o varias sentencias, When pasa por el guard, Then se rechaza | `test_hana_guard_rejects_*` |
| AC-HANA-12 | Given un filtro variable, When se ejecuta la query, Then su valor viaja como bind y no aparece en el SQL | `test_hana_query_uses_bound_parameters` |
| AC-HANA-13…24 | Given el fake HANA, When se sincroniza cada objeto (company, plant, storage location, vendor, material, PO header/items, PO history, production order, transfer order, outbound order, material movement, batch), Then queda en RAW con su clave de origen | `test_sync_<objeto>` |
| AC-HANA-25 | Given filas extraídas, When termina el sync, Then existen en `sap_inbound_records` con payload y hash | tests de sync |
| AC-HANA-26 | Given una fila sin campo obligatorio, When se valida, Then `INVALID` con `SAP_VALIDATION_ERROR` | test de validación |
| AC-HANA-27 | Given un `BUKRS`/`WERKS` sin mapping, When se procesa, Then `PENDING_MAPPING` y sin referencia | `test_unknown_company_pending_mapping`, `test_unknown_plant_pending_mapping` |
| AC-HANA-28 | Given una fila válida y mapeada, When se procesa, Then `staged_json` normalizado y `READY_FOR_PROMOTION`/`PROMOTED` | tests de sync |
| AC-HANA-29 | Given la misma página dos veces, When se resincroniza, Then no hay duplicados; con hash nuevo, versión nueva | `test_sync_duplicate_same_hash_noop`, `test_sync_changed_hash_versioned` |
| AC-HANA-30 | Given un batch que falla, When termina el job, Then el watermark no cambió | `test_sync_failed_batch_does_not_advance_watermark` |
| AC-HANA-31 | Given registros listos, When se promueven, Then upsert por clave canónica y trazado al RAW | tests de promoción |
| AC-HANA-32 | Given OC y STO sincronizadas, When se listan `/sap/references`, Then aparecen con el contrato actual | `test_purchase_order_promotes_quantity`, test de STO |
| AC-HANA-33 | Given una OC sincronizada, When se recibe por encima del ordenado, Then BR-18 lo rechaza | `test_purchase_order_br18_limit` |
| AC-HANA-34 | Given cero credenciales, When se consulta readiness, Then responde 200 con `configured=false` y los nombres faltantes | `test_hana_adapter_missing_credentials` |
| AC-HANA-35 | Given sin conexión real, When se consulta connection-check, Then `connected=false` | test de connection-check |
| AC-HANA-36 | Given un actor sin `sap:send_sap`, When pide sync, Then 403 | `test_sap_inbound_routes_rbac` |
| AC-HANA-37 | Given las rutas nuevas, When arranca la app, Then cobertura de autorización PASS | arranque + test |
| AC-HANA-38 | Given las rutas nuevas, When arranca la app, Then alcance de unidad declarado | `test_sap_inbound_routes_scope_declared` |
| AC-HANA-39 | Given autoridad global sin contexto, When lee o sincroniza, Then ∅ / 4xx sin leer | tests R-201 inbound |
| AC-HANA-40 | RED demostrado antes de implementar | `evidence/red/` |
| AC-HANA-41 | Verde dirigido | `evidence/green/` |
| AC-HANA-42 | Regresión completa de backend, 0 fallos | `evidence/regression/` |
| AC-HANA-43 | Regresión de frontend | ídem |
| AC-HANA-44 | `tsc -b` PASS | `evidence/build/` |
| AC-HANA-45 | `vite build` PASS | ídem |
| AC-HANA-46 | E2E con fake HANA PASS | `evidence/e2e/` |
| AC-HANA-47 | Mutación S1–S8: cada mutación rompe su test | `10_MUTATION_EVIDENCE` |
| AC-HANA-48 | Regresión post-mutación PASS con restauración por SHA explícito | ídem |
| AC-HANA-49 | No se creó rama | `git branch` |
| AC-HANA-50 | Push a la misma rama remota | `git ls-remote` |
| AC-HANA-51 | Commit de implementación trazable | git |
| AC-HANA-52 | Commit de evidencia/certificación trazable | git |
| AC-HANA-53 | `REMOTE_SHA_MATCH = PASS` | git |
| AC-HANA-54 | Árbol limpio | `git status` |
| AC-HANA-55 | `READY_FOR_SAP_CREDENTIALS` solo si no queda deuda de código | `11_LOCAL_CERTIFICATION` |

## TESTS REQUIRED

Lista mínima del mandato (§45) más los de contrato de columnas, R-201 inbound y promoción de STO. Detalle y trazabilidad AC→test en `audit/sap-hana-cloud/09_TEST_MATRIX.md`.

## RISKS

| Riesgo | Mitigación |
|---|---|
| Tablas candidatas (`T001, T001K, MARA, MARC, AUFK/AFKO/AFPO, MCHA, LFB1, LIKP/LIPS`) no verificadas en el landscape real | `source_status` por definición; el probe P5 las valida; un fallo es `SAP_QUERY_CONTRACT_ERROR` acotado al objeto |
| El push a `main` con cambios en `backend/**` y `frontend/**` despliega al UAT compartido (AOD-29 addendum) | arranque sin credenciales probado; scheduler apagado por defecto; migración aditiva |
| Sync síncrono dentro de la petición HTTP | ventana, `page_size` y tope de filas acotados; timeouts |
| Auto-certificación (constitución Art. 9) | la certificación local es evidencia del agente ejecutor; el cierre formal lo da el Owner |

## ROLLBACK

`alembic downgrade -1` elimina las 4 tablas nuevas sin tocar las existentes. `SAP_HANA_SYNC_ENABLED=false` (por defecto) detiene el scheduler. Sin credenciales, la integración queda inerte. Las referencias promovidas se identifican por `extra_data.source = "SAP_HANA_CLOUD"`.

## DEFINITION OF DONE

Todos los AC en PASS con evidencia · 0 secretos · 0 llamadas reales a SAP · 3 commits trazables (spec+RED, implementación, certificación) · push y `REMOTE_SHA_MATCH` · estado `READY_FOR_SAP_CREDENTIALS`.

## CLARIFICATIONS

| # | Pregunta | Clase | Resolución |
|---|---|---|---|
| Q1 | ¿STAGING es otra tabla? | GA_DECISION | No: es una capa lógica sobre `sap_inbound_records` (`staged_json` + los tres estados que el mandato §19 sitúa en el registro). El payload RAW es inmutable. |
| Q2 | ¿Se reutiliza `sap_sync_jobs` para los jobs inbound? | GA_DECISION | No: tabla propia `sap_inbound_sync_jobs`. Los campos de auditoría de §42 no caben en la tabla de export y su actor es obligatorio; el scheduler no tiene actor. |
| Q3 | ¿Se amplía `SapReferenceType`? | GA_DECISION | No. `company`, `movement_type`, `production_order`, `outbound_order`, `material_movement` y el historial quedan en staging (`STAGED_ONLY`): no tienen consumidor de dominio hoy y se evita una migración de enum PostgreSQL. |
| Q4 | ¿Cómo se agregan cantidades de una OC? | GA_DECISION | Σ `MENGE` de ítems no borrados si comparten unidad. Unidades mixtas ⇒ promoción `BLOCKED` con `SAP_VALIDATION_ERROR` (fail-closed: una OC sin cantidad dejaría BR-18 inaplicable). |
| Q5 | ¿Quién define el mapping `BUKRS → empresa`? | GA_DECISION | Solo la autoridad global situada en la empresa (enlaza un inquilino con una sociedad SAP). `WERKS`/`LGORT` los mapea quien tenga `sap:send_sap`, dentro de su empresa. |
| Q6 | ¿Cuál es el alcance de una sincronización? | GA_DECISION | La empresa efectiva: una consulta por cada `BUKRS` mapeado a ella (bind), nunca listas dinámicas. Una fila cuyo `BUKRS` pertenece a otra empresa GA no se persiste. |
| Q7 | ¿Delta por objeto? | SAP_PROBE_CLARIFICATION | Maestros: `SNAPSHOT`. Documentos: `BOUNDED_RECONCILIATION_WINDOW` sobre el campo fecha de la definición, con solape `SAP_HANA_DEFAULT_LOOKBACK_DAYS`. Ningún watermark universal; los campos candidatos se confirman en P5. |
| Q8 | ¿De dónde salen las órdenes de salida? | SAP_PROBE_CLARIFICATION | Fuente candidata `LIKP/LIPS` (documento de entrega), separada de `MATDOC` (evidencia de movimiento). Se valida en P5; no se afirma como contrato final. |
| Q9 | ¿Cómo se distingue STO de OC? | SAP_PROBE_CLARIFICATION | Estructuralmente: `EKKO.RESWK` informado ⇒ traslado. Sin listas de `BSART`/`BWART`. |
| Q10 | ¿Fake HANA en el paquete de producción? | GA_DECISION | Sí, como `SAP_HANA_DRIVER=fake`, aceptado solo con `ENVIRONMENT` ∈ {development, test}; readiness lo declara `simulated=true` y nunca como conexión real (precedente: `MockSapAdapter`). |
| Q11 | ¿Vendors de mandante completo? | GA_DECISION | Acotados a la sociedad (`LFB1`) para no cruzar inquilinos que compartan mandante; BP/CVI se valida en el probe. |
| Q12 | ¿`SAP_OUTBOUND_ENABLED=true` habilita entrega real? | GA_DECISION | No: solo reabre la ruta de artefacto manual/mock existente. `SAP_ADAPTER=real` sigue en 501. |

## ANALYZE

Resultado en `audit/sap-hana-cloud/13_TRACEABILITY.md §3`: 20 categorías del mandato §59 = 0 defectos · `OPEN_TECHNICAL_CONTRADICTIONS = 0`.

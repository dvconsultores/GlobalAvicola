# Research — SPEC 005 SAP HANA Cloud READ ONLY Inbound

**Fecha**: 2026-10-06 · Discovery sobre `cf991b4` · sin conexiones a SAP

---

## 1 · Cambio de contexto

| Fecha | Decisión inbound | Estado |
|---|---|---|
| 2026-06-23 | OData recomendado (`docs/10 §8`) | superseded |
| 2026-09-22 | SOAP pull, proveedor = server (`specs/003`) | `CLOSED_HISTORICAL_CONTRACT_NOT_IMPLEMENTED` |
| 2026-10-06 | **SAP HANA Cloud READ ONLY** (Owner/Sponsor) | vigente |

## 2 · Hechos del producto relevantes

| Hecho | Fuente |
|---|---|
| Las rutas SAP solo se montan con `FEATURE_SAP_ENABLED` | `backend/app/main.py:173` |
| El arranque exige permiso, frontera transaccional y alcance de unidad por ruta | `authorization_coverage.py`, `transaction.py`, `business_units/route_scope.py` |
| Las rutas SAP `CONTRATO` deben coincidir con `SUPERFICIES_TRANSVERSALES` | `tests/test_sap_transversal.py:379` |
| `validate_oc_limit` usa `scalar_one_or_none()` sobre `(company, PURCHASE_ORDER, sap_code)`: exige una única referencia por OC | `operations/validators.py:859` |
| `retry_failed` marca `CONFIRMED` sin mirar `delivers_to_sap` | `sap/service.py` — queda cerrado por el 409 de outbound |
| `run_tests.sh` exige exactamente 60 tablas | `backend/scripts/run_tests.sh` — pasa a 64 |
| Toda tabla debe estar clasificada | `backend/scripts/data_classification.py` |
| El scheduler existente vive en `lifespan` y se apaga con `GA_TEST_ENV=1` | `main.py` (`vigilar_revisiones_pendientes`) |
| El frontend consume `/sap/references` con `sap_code`, `description`, `quantity`, `extra_data.vendor_name` | `frontend/src/pages/operations/OperationFormPage.tsx` |
| No hay usuario sembrado con rol SAP en la pila de pruebas | `backend/seeds/test_seeds.py` — el E2E lo crea por API |

## 3 · Driver `hdbcli` (verificado sobre el wheel 2.30.27, sin ejecutarlo contra SAP)

| Aspecto | Hallazgo | Consecuencia |
|---|---|---|
| `paramstyle` | `qmark` y `named` | binds `:nombre` |
| `threadsafety` | 1 | una conexión por llamada, nunca compartida |
| Opciones | `encrypt`, `sslValidateCertificate`, `sslTrustStore`, `connectTimeout`, `communicationTimeout` (ms) | TLS y timeouts por opciones de conexión |
| Cursor | `setquerytimeout(segundos)` | timeout por sentencia |
| Naturaleza | síncrono | `asyncio.to_thread` |

## 4 · Evidencia legacy relevante

`audit/sap-soap/11_…` y `audit/sap0/SAP_LEGACY_REPOSITORY_AUDIT.md`. Tablas confirmadas por uso histórico: `T001W, T001L, LFA1, EKKO, EKPO, EKBE, MATDOC, MAKT, T156HT`. El SQL legacy no está en este repositorio y no se copia. Matriz completa en `audit/sap-hana-cloud/02_LEGACY_QUERY_AUDIT.md`.

## 5 · Decisiones de diseño tomadas

| Decisión | Alternativa descartada | Razón |
|---|---|---|
| Interfaz inbound separada (`SapInboundAdapter`) | añadir `fetch_*` al ABC de export | no diluir `delivers_to_sap` (`12_SAP_SOAP_GA_ADAPTER_CHANGE_SPEC §2`) |
| SQL estático con un `BUKRS` por consulta | listas `IN` dinámicas | ningún fragmento SQL depende de datos |
| `LIMIT :page_limit OFFSET :page_offset` con orden estable y ventana | keyset multicolumna | simple; el hash absorbe relecturas |
| Una conexión por página | sesión larga compartida entre hilos | `threadsafety = 1`; coste acotado por el tope de filas |
| Estados como `String` en tablas nuevas | enums PostgreSQL | migración y `downgrade` sin tipos huérfanos |
| Savepoint por objeto | transacción única | un objeto que falla no arrastra a los demás ni mueve su watermark |
| `pg_try_advisory_xact_lock` por empresa+objeto | tabla de bloqueos | evita solape entre scheduler y sync manual sin infraestructura |

## 6 · Riesgos y mitigaciones

Ver `spec.md §RISKS`. El principal es externo: ninguna tabla está verificada contra el landscape real (SAP-0P = 0/12); cada definición declara `LEGACY_CONFIRMED` o `CANDIDATE` y el runbook las valida en P5.

## 7 · Referencias

`docs/10-sap-integration-strategy.md` · `audit/sap0/**` · `audit/sap0p/**` · `audit/sap-soap/**` · `specs/001…004` · `specs/remediation/OD-12…`, `OD-14…`, `OD-24…`, `GA-REM-010…`, `GA-REM-017…` · `audit/ga-pre-sap-program/GA_OWNER_DECISION_AOD29_*` · `audit/remediation/MUTATION_CHECKPOINT_GOVERNANCE.md`

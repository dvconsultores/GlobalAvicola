# SAP-HANA-CLOUD · 04_READONLY_SECURITY

Fecha: 2026-10-06 · SPEC 005 · Seguridad del conector inbound de solo lectura

---

## 1 · Principio

```text
SAP_WRITES_PHASE_1 = FORBIDDEN
INSERT · UPDATE · DELETE · MERGE · UPSERT · CALL · DDL · BAPI/RFC write · OData write · SOAP write = 0 rutas
```

El control primario es de SAP Basis: el usuario técnico debe ser READ ONLY. Global Avícola añade defensa en profundidad para que, **si SAP entregara por error un usuario con privilegios de más, el producto no pueda aprovecharlos**.

## 2 · Capas

| # | Capa | Implementación | Prueba |
|---|---|---|---|
| 1 | Usuario SAP READ ONLY | responsabilidad de SAP Basis; se verifica en el probe (P4) leyendo privilegios, nunca intentando escribir | runbook |
| 2 | Origen del SQL | `inbound/registry.py`: 14 definiciones estáticas en un `MappingProxyType`; no hay registro en caliente | `test_hana_registry_is_closed` |
| 3 | Guard | `inbound/sql_guard.py`: una sola sentencia, inicia en `SELECT`/`WITH`, sin tokens mutantes; decide sobre el SQL sin comentarios ni literales | `test_hana_guard_*` |
| 4 | Binds | todo valor viaja como parámetro; el cliente rechaza parámetros no declarados | `test_hana_query_uses_bound_parameters`, `test_hana_client_executes_registry_sql_with_bind_parameters` |
| 5 | Identificadores | el único interpolado es el schema: viene de `Settings` y pasa por `validate_identifier` (`^[A-Z_][A-Z0-9_]{0,126}$`) | `test_hana_schema_is_a_validated_identifier_never_request_input` |
| 6 | Cliente | `SapHanaReadOnlyClient` solo expone `ping` y `fetch_page(definición)`; no existe método para SQL libre | `test_hana_client_only_runs_registry_definitions` |
| 7 | API | peticiones con `extra="forbid"`; `object_type` es un enum; ninguna ruta acepta SQL, schema ni tabla | `test_hana_no_raw_sql_endpoint` |
| 8 | Outbound | `SAP_OUTBOUND_ENABLED=false` ⇒ `/sap/export` y `/sap/retry` = `409 SAP_OUTBOUND_DISABLED_READ_ONLY_PHASE`, antes de leer nada | `test_outbound_disabled` |

Tokens que el guard rechaza: `INSERT, UPDATE, DELETE, MERGE, UPSERT, REPLACE, CREATE, ALTER, DROP, TRUNCATE, RENAME, GRANT, REVOKE, CALL, DO, EXEC, EXECUTE, INTO, SET, COMMIT, ROLLBACK, LOCK, UNLOAD, IMPORT, EXPORT, LOAD`.

El guard no es la seguridad: es la tercera línea. Un regex solo sería falsa seguridad; por eso van antes el usuario READ ONLY y el registry cerrado.

## 3 · TLS

| Regla | Implementación |
|---|---|
| Cifrado obligatorio | `connect_options()` fija `encrypt=True` siempre |
| Validación de certificado obligatoria | `sslValidateCertificate=True` siempre |
| Configuración que lo niega | `SAP_HANA_ENCRYPT=false` o `SAP_HANA_SSL_VALIDATE_CERTIFICATE=false` ⇒ `SAP_TLS_ERROR` **antes de conectar**; readiness informa `TLS_POLICY_VIOLATION` |
| CA propia | `SAP_HANA_SSL_TRUST_STORE` (ruta): añade confianza, no quita validación |

Prohibido en cualquier entorno: `encrypt=false`, `sslValidateCertificate=false`, `verify=False`.

## 4 · Secretos

| Riesgo | Control |
|---|---|
| Secreto en el repositorio | las variables no tienen valor por defecto; `.env.example` y `docker-compose.yml` solo llevan nombres y marcadores |
| Secreto en un error o log | `errors.sanitize`: redacta la contraseña, el usuario y el host conocidos, cualquier `password=…`/`pwd=…`/`token=…` y las credenciales embebidas en una URL |
| Secreto en `repr` | `HanaSettings.password` es `repr=False` |
| Secreto en la API | readiness devuelve los **nombres** de las variables que faltan; nunca host, usuario ni contraseña |
| Secreto en el navegador | el frontend solo recibe estado, contadores y mensajes saneados |
| Stack trace al cliente | un fallo de SAP es un job `failed` con código cerrado, no un 500 |

Pruebas: `test_hana_secret_never_leaks`, `test_job_error_message_is_sanitized`, `test_readiness_never_returns_secret_values`, `test_failed_sync_is_reported_not_raised`.

## 5 · Errores (lista cerrada)

`SAP_CONFIG_MISSING · SAP_DRIVER_UNAVAILABLE · SAP_DNS_ERROR · SAP_TLS_ERROR · SAP_AUTH_ERROR · SAP_AUTHORIZATION_ERROR · SAP_QUERY_TIMEOUT · SAP_QUERY_CONTRACT_ERROR · SAP_SCHEMA_MISMATCH · SAP_OBJECT_NOT_FOUND · SAP_MAPPING_PENDING · SAP_VALIDATION_ERROR · SAP_TEMPORARY_UNAVAILABLE · SAP_INTERNAL_ERROR`

| Código del driver | Clasificación |
|---|---|
| 10 | `SAP_AUTH_ERROR` |
| 258 | `SAP_AUTHORIZATION_ERROR` |
| 259 | `SAP_OBJECT_NOT_FOUND` |
| 257, 260 | `SAP_QUERY_CONTRACT_ERROR` |
| 613 o texto «timeout» | `SAP_QUERY_TIMEOUT` |
| texto de resolución de nombres | `SAP_DNS_ERROR` |
| texto SSL/TLS/certificado | `SAP_TLS_ERROR` |
| -10709, -10806, -10807, -10808, errores de socket | `SAP_TEMPORARY_UNAVAILABLE` |
| cualquier otro | `SAP_INTERNAL_ERROR` |

Los códigos numéricos se confirman contra el sistema real en el probe; uno no previsto cae en `SAP_INTERNAL_ERROR`, nunca en éxito.

## 6 · Ejecución

- `hdbcli` es síncrono y `threadsafety = 1`: cada llamada abre su conexión y su cursor dentro de `asyncio.to_thread` y los cierra en `finally`, también al fallar.
- Concurrencia acotada por un semáforo de hilo (`SAP_HANA_MAX_CONCURRENCY`, por defecto 2).
- Timeouts: `connectTimeout` y `communicationTimeout` en la conexión; `setquerytimeout` por sentencia.
- El driver se importa de forma lazy: el backend arranca sin `hdbcli` y sin credenciales.

## 7 · Doble local (`SAP_HANA_DRIVER=fake`)

Aceptado solo con `ENVIRONMENT` ∈ {`development`, `test`}; en cualquier otro entorno `build_adapter` falla con `SAP_CONFIG_MISSING`. Readiness lo declara `simulated: true` y `connection-check` no lo cuenta como conexión real (`connected: false` en la clave heredada).

## 8 · Resultado del escaneo

Se registra en `11_LOCAL_CERTIFICATION.md` (`SECRETS_FOUND`).

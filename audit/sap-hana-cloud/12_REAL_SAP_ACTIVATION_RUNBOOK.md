# SAP-HANA-CLOUD · 12_REAL_SAP_ACTIVATION_RUNBOOK

Fecha: 2026-10-06 · SPEC 005 · `SAP-HANA-PROBE` — activación con la credencial técnica READ ONLY

> Este runbook **no se ha ejecutado**. Hasta completarlo el estado es `SAP_HANA_REAL = PENDING_CREDENTIALS`. Ningún paso prueba el carácter READ ONLY intentando escribir.

---

## 0 · Qué debe entregar SAP / Basis

| Dato | Variable | Canal |
|---|---|---|
| Endpoint SQL de HANA Cloud | `SAP_HANA_HOST`, `SAP_HANA_PORT` | canal seguro; nunca el repositorio |
| Usuario técnico **READ ONLY** | `SAP_HANA_USER`, `SAP_HANA_PASSWORD` | canal seguro (custodia AOD-12) |
| Schema de las tablas SAP | `SAP_HANA_SCHEMA` | canal seguro |
| Mandante | `SAP_HANA_CLIENT` | canal seguro |
| CA del endpoint, solo si no es pública | `SAP_HANA_SSL_TRUST_STORE` (ruta en el contenedor) | canal seguro |
| Allowlist de red para la IP de salida del backend | — | Basis |
| Ventana autorizada para el probe | — | Basis |

## 1 · Cargar la configuración

1. En el `.env` del servidor (no versionado) definir las variables de §0. Dejar `SAP_HANA_ENCRYPT=true`, `SAP_HANA_SSL_VALIDATE_CERTIFICATE=true`, `SAP_HANA_SYNC_ENABLED=false`, `SAP_OUTBOUND_ENABLED=false`.
2. El `docker-compose.yml` del servidor debe ser el de este repositorio (pasa las `SAP_HANA_*` al contenedor). Watchtower actualiza la imagen pero **no** las variables: hay que recrear el contenedor con `docker compose up -d backend`.
3. Opcional: `SAP_HANA_COMPANY_CODES` / `SAP_HANA_PLANTS` como listas de admisión mientras dure el probe.

## 2 · Secuencia del probe

Cada paso se detiene ante el primer fallo y se registra con el formato de `audit/sap0p/SAP0P_QUERY_REGISTER.md` (`QUERY_ID · PURPOSE · TARGET · START · END · ROW_LIMIT · RESULT · SANITIZATION · EVIDENCE_FILE`).

| Paso | Qué | Cómo | Éxito |
|---|---|---|---|
| P0 | Configuración | `GET /api/v1/sap/inbound/readiness` | `configured: true`, `missing: []`, `simulated: false`, `status: CONFIGURED_NOT_TESTED` |
| P1 | TCP / TLS | `GET /api/v1/sap/connection-check` | sin `SAP_DNS_ERROR`, `SAP_TLS_ERROR` ni `SAP_TEMPORARY_UNAVAILABLE` |
| P2 | Autenticación | misma llamada | sin `SAP_AUTH_ERROR` |
| P3 | `SELECT 1 FROM DUMMY` | misma llamada | `inbound_hana.connected: true`, `status: CONNECTED` |
| P4 | Identidad y privilegios | consultas de metadatos de solo lectura, ejecutadas por Basis o con su supervisión: usuario actual, privilegios efectivos, versión | el usuario **no** tiene privilegios de escritura sobre el schema SAP |
| P5 | Disponibilidad de objetos | mapear una sociedad de prueba y lanzar `POST /sap/inbound/sync/{objeto}` uno a uno, en el orden del catálogo | cada job `completed`; `SAP_OBJECT_NOT_FOUND` / `SAP_QUERY_CONTRACT_ERROR` / `SAP_AUTHORIZATION_ERROR` identifican la tabla o columna a ajustar |
| P6 | Muestra | con `SAP_HANA_MAX_ROWS_PER_SYNC=10` y una ventana de pocos días, revisar `GET /sap/inbound/records` | 1–10 filas por objeto, coherentes; evidencia saneada |
| P7 | Reconciliación funcional | comparar con el negocio: OC (cantidad ordenada vs. `quantity`), recibido (`received_quantity`), centros, almacenes, STO | sin discrepancias sin explicar |
| P8 | Sync inicial acotado | restaurar `SAP_HANA_MAX_ROWS_PER_SYNC`; sync por objeto y por tramos de ≤ 366 días | jobs `completed`, sin `partial` inesperados |
| P9 | Evidencia | registro de queries, jobs, conteos, discrepancias; todo saneado | commit de evidencia |

Solo tras P3: `SAP_HANA_REAL_CONNECTION = PASS`. Solo tras P7–P9: `SAP_HANA_READONLY_CONNECTED_AND_RECONCILED`.

## 3 · P5 — qué valida cada objeto

| Objeto | Tablas | Fuente | Punto a confirmar |
|---|---|---|---|
| `company` | T001 | candidata | disponibilidad |
| `plant` | T001W, T001K | T001W legacy; T001K candidata | relación centro→sociedad por `BWKEY` |
| `storage_location` | T001L, T001W, T001K | T001L legacy | ídem |
| `vendor` | LFA1, LFB1 | LFA1 legacy; LFB1 candidata | si el landscape usa BP/CVI y la relación `LIFNR ↔ BP` |
| `material` | MARA, MAKT, MARC, T001K | MAKT legacy; resto candidatas | idioma (`SAP_HANA_LANGUAGE`), `LAEDA` como candidato de delta |
| `batch` | MCHA, T001K | candidata | MCHA frente a MCH1 según el nivel de lote |
| `movement_type` | T156HT | legacy | idioma |
| `purchase_order` (+ item, history) | EKKO, EKPO, EKET, EKBE | legacy (EKET candidata) | `BSTYP='F'`; `AEDAT` como campo de ventana; `VGABE='1'` = entrada de mercancías |
| `production_order` | AUFK, AFKO, AFPO | candidatas | que las órdenes avícolas sean PP/PI; `PHAS1..3` como estado |
| `transfer_order` | EKKO, EKPO | tablas legacy; semántica candidata | que el traslado se identifique por `RESWK` informado |
| `outbound_order` | LIKP, LIPS, T001K | candidata | **de dónde salen realmente** las órdenes de salida (Q8); si no son entregas, se sustituye la definición |
| `material_movement` | MATDOC | legacy | columnas de reverso `SMBLN/SJAHR/SMBLP`; si hace falta filtrar por tipo de registro |

Si una tabla o columna candidata no existe, el fallo queda acotado a ese objeto (`failed` con código cerrado) y se corrige su definición del registry con un cambio versionado (`<objeto>.v2`) y su prueba. No se «arregla» relajando el guard ni concatenando SQL.

## 4 · Mapping

1. Con los `BUKRS` reales (P5, objeto `company`), la **autoridad global situada en cada empresa** declara su sociedad: `PUT /api/v1/sap/inbound/mappings` con `{"entity_type":"COMPANY_CODE","sap_key":"<BUKRS>"}`.
2. Quien tenga `sap:send_sap` declara los centros: `{"entity_type":"PLANT","sap_key":"<WERKS>","parent_sap_key":"<BUKRS>"}` y, si el negocio lo decide, su granja (`farm_id`).
3. Los almacenes solo se mapean a un galpón por decisión expresa (`LGORT ≠ galpón`).
4. Todo lo no mapeado permanece en `PENDING_MAPPING` y es visible en `/sap/inbound/errors`.

## 5 · Encender el scheduler

Solo después de P8: `SAP_HANA_SYNC_ENABLED=true`, `SAP_HANA_SYNC_INTERVAL_SECONDS` según el volumen observado, y recrear el contenedor.

## 6 · Condiciones de parada

- Cualquier indicio de que el usuario puede escribir ⇒ detener y devolver la credencial a Basis.
- `SAP_TLS_ERROR` ⇒ no desactivar la validación; pedir la CA correcta.
- Un job que alcanza el tope de filas con ventana corta ⇒ revisar el volumen con Basis antes de ampliar.
- Datos de una sociedad no esperada ⇒ detener; revisar mapping y allowlist.

## 7 · Vuelta atrás

Vaciar las `SAP_HANA_*` y recrear el contenedor devuelve la integración a `PENDING_CREDENTIALS`. Las referencias promovidas se identifican por `extra_data.source = "SAP_HANA_CLOUD"`. `alembic downgrade -1` elimina las cuatro tablas inbound sin tocar las demás.

## 8 · Lo que este runbook no cubre

Escritura a SAP, outbound real, go-live productivo, convergencia de maestros (OD-24), centros de coste e inventario (`DEFERRED_PHASE_1`).

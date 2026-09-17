# SAP-0 · SAP_LEGACY_REPOSITORY_AUDIT

Fecha: 2026-09-17 · Fase: **SAP-0 — Landscape Discovery + Inbound Data Contract** (SPEC ONLY — sin implementación)
Fuente auditada: **`https://github.com/dvconsultores/SapHanaLP`** · Clasificación: **`LEGACY_SAP_DISCOVERY_EVIDENCE`**
Método: lectura remota del repositorio (tool de comprensión de repo + fetch de archivos crudos). **NO** se recuperaron secretos, **NO** se ejecutaron endpoints SAP, **NO** se levantó VPN, **NO** se descargó el repositorio al workspace.

> Regla absoluta (mandato §3): **nada de lo aquí documentado se reutiliza como arquitectura del producto nuevo.** Este documento estudia el legacy para extraer conocimiento y separar hechos de suposiciones.

---

## 1 · Inventario de archivos del repositorio legacy

| Archivo | Contenido verificado | Evidencia |
|---|---|---|
| `README.md` | Una línea: «Integration SAP 4Hana and App Lider Pollo» | ✔ |
| `Dockerfile` | `python:3.11-slim` + strongswan, xl2tpd, ppp, iproute2, network-manager, supervisor; `CMD supervisord` | ✔ |
| `docker-compose.yml` | **`network_mode: host`**, `cap_add: [NET_ADMIN]`, `devices: [/dev/ppp, /dev/net/tun]`, monta `vpn/ipsec.conf`, `vpn/ipsec.secrets`, `vpn/xl2tpd.conf`, `vpn/options.l2tpd.client`; `env_file: .env`; Watchtower (poll 300 s) | ✔ |
| `entrypoint.sh` | Levanta IPsec (`L2TP-PSK`), xl2tpd, dispara túnel `LP`, espera `ppp0`, añade ruta `192.168.14.0/24`, ping a `192.168.14.24` | ✔ |
| `app.py` | Orquestador principal: VPN → `hdbcli` a HANA → consultas → pandas → PostgreSQL → scheduling 06/10/14/18 h | ✔ |
| `main.py` | FastAPI mínima: `POST /sap/call` que proxya el SOAP | ✔ |
| `operations.py` | UPSERTs a PostgreSQL por dominio (granjas, galpones, proveedores, órdenes, alimento, incubadora, producción) | ✔ |
| `inserts_thread.py` | Patrón **temp table**: `df.to_sql(..., if_exists='replace')` + `sleep(3)` + query de unión + store | ✔ |
| `querysHana.py` | Todas las consultas SQL a HANA (farms, warehouse, OC, MATDOC por BWART, inventarios, transferencias…) | ✔ |
| `sap_integration.py` | Cliente SOAP (envelope f-string, BasicAuth, `verify=False`) para `ZwsTasaMortalidad` | ✔ |
| `schemas.py` | Conexión HANA directa (`hdbcli.dbapi`) para inventariar `SYS.TABLES` | ✔ |
| `requirements.txt` | **`hdbcli==2.21.31`**, `psycopg2-binary`, `SQLAlchemy`, `pandas`, `schedule==1.2.2`, `zeep`, `requests`, `fastapi`, `uvicorn` | ✔ |
| `supervisord.conf` | 3 programas: `vpn_setup` (entrypoint), `main` (uvicorn FastAPI :8000), `app` (python app.py) | ✔ |
| XML / samples | No hay ficheros XML estáticos: el envelope SOAP se genera en código; params de ejemplo en `sap_integration.py` | ✔ |
| Workflows | No se observaron workflows CI en el material auditado | — (no concluyente) |

## 2 · Arquitectura legacy reconstruida (CONFIRMED_LEGACY_FACT)

```
[HANA saphana S/4]  (SAPHANADB, mandante 120)
        ▲ SQL directo (hdbcli 2.21.31, puerto 30241)
        │
[VPN L2TP/IPsec] ← strongswan+xl2tpd dentro del contenedor (host network, NET_ADMIN, /dev/ppp, /dev/tun)
        │
[app.py]  consultas (querysHana.py) → pandas
        │
[PostgreSQL app]  TEMP TABLES (to_sql if_exists='replace')  →  joins id_sap→id interno  →  UPSERT a tablas de dominio
        │
[FastAPI main.py] POST /sap/call  →  SOAP ZwsTasaMortalidad (vhemsds4ws1wd01, BasicAuth, verify=False)
```

## 3 · Inventario técnico (§5 del mandato)

Cada hallazgo: `SOURCE_FILE · SOURCE_LOCATION · VALUE/PATTERN · USE · PROCESS · CLASSIFICATION · CURRENT_VALIDITY`.

| # | Hallazgo | Fuente · Ubicación | Valor/Patrón | Uso | Clasificación | Validez actual |
|---|---|---|---|---|---|---|
| T-01 | Conexión HANA directa vía `hdbcli` | `app.py:L0-38,170-195` · `schemas.py:L0-42` | `dbapi.connect(address=HANA_HOST, port=30241, user, password)` | Leer datos operativos | `CONFIRMED_LEGACY_FACT` · `DO_NOT_REUSE` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-02 | Puerto HANA | `app.py:L17` · `schemas.py:L11` | **`30241`** (hardcode; el comentario sugiere `HANA_PORT`) | Conexión | `CONFIRMED_LEGACY_FACT` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-03 | Red: VPN embebida en el contenedor | `entrypoint.sh` · `app.py:99-135` · `docker-compose.yml` | IPsec L2TP (`L2TP-PSK`, túnel `LP`), `ppp0`, `network_mode: host`, `NET_ADMIN`, `/dev/ppp`, `/dev/net/tun` | Alcanzar la red SAP | `CONFIRMED_LEGACY_FACT` · `DO_NOT_REUSE` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-04 | Subred/host de prueba VPN | `entrypoint.sh:L58-72` | ruta `192.168.14.0/24`, ping `192.168.14.24` | Test de conectividad | `CONFIRMED_LEGACY_FACT` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-05 | Autenticación HANA | `app.py` (env) | usuario/clave por variables de entorno (`HANA_USER`/`HANA_PASSWORD`) | Login HANA | `CONFIRMED_LEGACY_FACT` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-06 | Base/schema | `querysHana.py` (todas) | **`SAPHANADB`** (schema); `SYS.TABLES` para catálogo | Consultas | `CONFIRMED_LEGACY_FACT` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-07 | Mandante | `querysHana.py:L0-28` | **`MANDT = '120'`** | Filtro fijo | `HARDCODED_LEGACY_RULE` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-08 | Sociedad/isla BUKRS | `querysHana.py:L322-341` | `MATDOC.BUKRS` etiquetado «Centro de Entrega» | Reporte | `LEGACY_ASSUMPTION` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-09 | Centros (WERKS) usados | `querysHana.py` (varias) | `3000` = incubadora; `2000/2002` centros producción; `2500` excluido; `1000` = «ABA» origen alimento; `4089` (comentado) despacho; `5000` (ejemplo SOAP) | Filtros y orígenes | `CONFIRMED_LEGACY_FACT` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-10 | Filtro semántico de granjas | `querysHana.py:L0-28` | `NAME1/NAME2 NOT LIKE '%NO USAR%'`, `WERKS NOT IN ('3000')` | Selección de granjas | `HARDCODED_LEGACY_RULE` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-11 | Almacenes (LGORT) = galpones | `querysHana.py:L28-49` y `operations.py` (`galpones`) | `T001L.LGORT/LGOBE` → tabla destino **`galpones`** | Mapeo almacén→galpón | `CONFIRMED_LEGACY_FACT` · `BUSINESS_RULE_NEEDS_VALIDATION` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-12 | Proveedores/transportes | `querysHana.py:L60-94`; `inserts_thread.py` | `LFA1.LIFNR/NAME1` → `proveedores` **y** `transportes` (mismo origen) | Maestros | `CONFIRMED_LEGACY_FACT` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-13 | Materiales (MATNR) | `querysHana.py` (listas IN) | Alimento `105001-105028`; aves `110000-110003`; huevo `115000`; pollito `120000/120005`; ejemplo SOAP `125001` | Filtros por proceso | `HARDCODED_LEGACY_RULE` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-14 | Tipos de movimiento (BWART) | `querysHana.py` (comentarios+WHERE) | **`641`** (transferencias alimento/aves/huevos), **`303`** (aves a reproductoras desde incubadora) | Clasificación de movimientos | `CONFIRMED_LEGACY_FACT` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-15 | Fechas de corte | `querysHana.py` | `>= '20230301'`, `>= '20240301'`, `>= '20250312'`, `MJAHR='2024'` | Ventanas de carga | `HARDCODED_LEGACY_RULE` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-16 | Destinos fijos | `querysHana.py:L227-296` | transporte `'3730'`, granja destino `'1'`, galpón `'1001'`, `transporteIdId '000000000000'` | Rellenar FKs locales | `HARDCODED_LEGACY_RULE` · `DO_NOT_REUSE` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-17 | Prefijo de orden de producción | `querysHana.py:L248-273` | `SUBSTRING(AUFNR,1,1)='7'`; ejemplo `121000000016`, `700300000256` | Filtrar órdenes | `HARDCODED_LEGACY_RULE` | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-18 | SOAP endpoint+auth | `sap_integration.py:L0-51` | `https://vhemsds4ci.sap.liderpollo.com:44300/vhemsws1wd01`; HTTPBasicAuth (`SAP_USER/SAP_PASSWORD`); **`session.verify=False`** | Mortalidad vía servicio Z | `CONFIRMED_LEGACY_FACT` · `DO_NOT_REUSE` (verify=False) | `NEEDS_CURRENT_SAP_VALIDATION` |
| T-19 | Patrón integración PostgreSQL | `inserts_thread.py` (`to_sql if_exists='replace'`) | HANA→pandas→**temp table**→join→UPSERT dominio | ETL | `CONFIRMED_LEGACY_FACT` · `DO_NOT_REUSE` | Aplica al legacy |
| T-20 | Periodicidad | `app.py:L281-301` | Job diario 06/10/14/18 h + al arrancar | Sincronización | `CONFIRMED_LEGACY_FACT` | — |
| T-21 | Mecanismo de updates | `operations.py` (funciones `store_*`) | UPSERT manual `SELECT id_sap IN (...)` + update/insert por lotes con ThreadPool | Persistencia | `CONFIRMED_LEGACY_FACT` · (patrón sin idempotencia nativa) | — |
| T-22 | Identificador local de OC | `querysHana.py:L28-60` | `EKPO.UNIQUEID` como `id_sap` de la orden de compra | Clave hacia PostgreSQL | `LEGACY_ASSUMPTION` | `NEEDS_CURRENT_SAP_VALIDATION` |

## 4 · Matriz de tablas SAP legacy (§7)

`CURRENT_VALIDITY = UNKNOWN` en todas salvo indicación (no hay evidencia ACTUAL verificable; sólo del legacy).

| TABLA | BUSINESS_PURPOSE | KEY_FIELDS | JOIN_FIELDS | FILTERS | LEGACY_PROCESS | LEGACY_GA_TARGET | CURRENT_GA_CONSUMER | VALIDEZ |
|---|---|---|---|---|---|---|---|---|
| `T001W` | Centros/granjas | `WERKS`,`NAME1`,`NAME2`,`MANDT` | `WERKS` | `MANDT='120'`, sin '%NO USAR%', `WERKS≠3000` | Granjas | `granjas` | `masters/farms` (sin clave SAP hoy) | UNKNOWN |
| `T001L` | Almacenes/galpones | `LGORT`,`LGOBE`,`WERKS` | `WERKS`+`LGORT` | ídem | Galpones | `galpones` | `masters/houses` (sin clave SAP) | UNKNOWN |
| `EKKO` | Cabecera OC | `EBELN`,`LIFNR` | `EBELN`→`EKPO` | — | OC progenitoras | `crias_ordenes_recepcion` | `sap_references PURCHASE_ORDER` (espejo parcial) | UNKNOWN |
| `EKPO` | Posiciones OC | `EBELN`,`UNIQUEID`,`MATNR`,`WERKS`,`MENGE`,`AEDAT` | autorrelación por `EBELN/AEDAT/MATNR` (machos/hembras) | `MATNR='...110001'` machos / `'...110000'` hembras; `AEDAT>=…` | OC aves por sexo | ídem | ídem | UNKNOWN |
| `EKBE` | Historial OC | `EBELN` | — | `EBELN='4500011936' LIMIT 100` (prueba) | OC (histórico) | — | — | UNKNOWN |
| `LFA1` | Proveedores | `LIFNR`,`NAME1` | — | — | Proveedores/transportes | `proveedores`+`transportes` | `masters/suppliers`(+`transports`) | UNKNOWN |
| `MATDOC` | **Documentos de material** (corazón) | `MBLNR`,`MJAHR`,`ZEILE`,`MATNR`,`WERKS`,`LGORT`,`BWART`,`BUDAT`,`ERFMG`,`SHKZG`,`CHARG`,`AUFNR`,`UMWRK`,`EBELN`,`MANDT`,`USNAM`,`SOBKZ`,`TCODE2` | `MAKT`(MATNR), `T001W`(WERKS), `T001L`(WERKS+LGORT), `T156HT`(BWART) | `BWART IN ('641','303')`; `MATNR IN (…listas duras…)`; `BUDAT>=…`; `MJAHR='2024'` | Alimento, aves, huevos, inventarios | `alimento_ordenes`, `crias_ordenes_*`, `produccion_ordenes_*`, `incubadora_ordenes_*` | **nada equivalente hoy** (eventos operativos capturados, no documentos SAP) | UNKNOWN |
| `MAKT` | Textos de material | `MATNR`,`SPRAS`,`MAKTX` | `MATNR` | `SPRAS='S'` | Descripciones | material desc | — | UNKNOWN |
| `T156HT` | Texto tipo movimiento | `BWART`,`SPRAS`,`BTEXT` | `BWART` | `SPRAS='S'` | Descripción BWART | — | — | UNKNOWN |
| `AFPO` | Órdenes producción (comentadas en legacy) | `AUFNR`,`MATNR`,`PSMNG`,`CHARG`,`PWERK`,`DWERK`,`LGORT`,`DGLTP` | — | (comentado) | Salida huevos/producción | — | — | UNKNOWN |
| `SYS.TABLES` | Catálogo | `SCHEMA_NAME`,`TABLE_NAME` | — | — | Exploración | — | — | UNKNOWN |

## 5 · Procesos legacy (§8)

| LEGACY_PROCESS | SAP_TABLES | SAP_DOCUMENT | MOVEMENT_TYPE | MATERIAL | ORIGEN | DESTINO | TARGET LEGACY | DOMINIO GA ACTUAL | VALIDACIÓN REQUERIDA |
|---|---|---|---|---|---|---|---|---|---|
| Empresas/centros | `T001W` | — | — | — | — | — | `granjas` | `companies`/`farms` | Origen de verdad (OD-24), BUKRS↔company |
| Granjas | `T001W` | — | — | — | — | — | `granjas` | `masters/farms` | Clave `WERKS`↔farm_code |
| Almacenes/galpones | `T001L` | — | — | — | — | — | `galpones` | `masters/houses` | **LGORT↔galpón** (clarificación SAP-STO-01) |
| Proveedores | `LFA1` | — | — | — | — | — | `proveedores` | `masters/suppliers` | BP real↔LIFNR |
| OC (aves) | `EKKO`,`EKPO` | OC | — | machos/hembras | Proveedor | Centro (granja) | `crias_ordenes_recepcion` | `sap_references PURCHASE_ORDER` + import GP | UNIQUEID, cantidades por sexo |
| Recepción de aves | `MATDOC` | doc material | 641/303 | 110000-110003 | Centro SAP / incubadora | Granja (`UMWRK`) | `crias_ordenes_*` | eventos `grandparent_import`/`bird_reception` | Lote SAP (`CHARG`), cuadre |
| Alimento (consumo/entrega) | `MATDOC` | doc material | **641** | 105001-105028 | «ABA» (1000) | Granja | `alimento_ordenes` | `feed_registration` | «ABA»↔almacén origen, tipo alimento |
| Transferencia alimento (OT) | `MATDOC`+`EBELN` | OT | 641 | 105000-105999 | ABA | Granja | `alimento_ordenes` (num_orden) | idem | OT provee identidad real |
| Incubadora→engorde (pollitos) | `MATDOC` | doc material | 641 | 120000/120005 | 3000 | Granja engorde | `incubadora_ordenes_salida_pollitos` | eventos `bird_reception` (broiler) | equivalencia doc↔recepción |
| Cría→producción | `MATDOC` | orden salida (AUFNR 7x) | (no fijado en SQL) | 1100xx | Centro cría | Centro producción | `crias_ordenes_salida` | `bird_distribution`/transferencias | prefijo AUFNR vs orden real |
| Gallinas→reproductoras | `MATDOC` | doc material | **303** | 110002 | 3000 | Granja | `crias_ordenes_salida` | idem | idem |
| Machos→reproductoras | `MATDOC` | doc material | **303** | 110003 | 3000 | Granja | idem | idem | idem |
| Producción→beneficio | `MATDOC` | orden salida | (post 641/303) | 110002 | Granja producción | Beneficio (`UMWRK`) | `produccion_ordenes_salida` | `bird_exit` | planta beneficio (¿centro SAP?) |
| Inventarios | `MATDOC`(+`T001W/T001L/T156HT/MAKT`) | docs del año | varios | — | — | — | reporte | reportes/KPIs | semántica de stock vs eventos GA |
| Batches/lotes SAP | `CHARG` en MATDOC / `SAP_BATCH` espejo | — | — | — | — | — | `lote`/`CHARG` | `sap_references SAP_BATCH`, `lots.lot_code` | lote productivo SAP (AOD-03) |
| Mortalidad (SOAP) | — | servicio Z | — | 125001 (ej.) | — | — | (no usado en SQL) | `mortality_recording` | `ZwsTasaMortalidad` (SAP-STO-02) |

## 6 · Hardcode inventory (§9) — TARGET_TREATMENT obligatorio, ninguno es regla del producto

| VALUE | TYPE | SOURCE | WHERE_USED | LEGACY_MEANING | RISK | TARGET_TREATMENT |
|---|---|---|---|---|---|---|
| `MANDT='120'` | Mandante | `querysHana.py` | todas las consultas | Mandante Lider Pollo en el CI | ALTO | `CURRENT_SAP_VALIDATION` (+`SAP_MASTER_DATA`) |
| `30241` (port) | Conexión | `app.py`,`schemas.py` | hdbcli | Puerto HANA del landscape | ALTO | `CURRENT_SAP_VALIDATION` |
| `'3000'` incubadora | Centro | `querysHana.py` | filtros/exclusiones | Planta incubadora | ALTO | `SAP_MASTER_DATA` (+validación) |
| `'2500'` excluido | Centro | `querysHana.py:L248` | `UMWRK NOT IN` | Centro no operativo | MEDIO | `CURRENT_SAP_VALIDATION` |
| `'1000'`/«ABA» | Centro origen alimento | comentario `querysHana.py:L341-362` | proceso alimento | Almacén administrativo ABA | MEDIO | `SAP_MASTER_DATA` |
| `'4089'` | Centro despacho | comentario `L322-341` | proceso beneficio | Centro desde el que se despacha | MEDIO | `CURRENT_SAP_VALIDATION` |
| `'3730'` transporte | FK fija | `querysHana.py:L227,248` | temp queries | Transporte fijo local | ALTO | `REMOVE` / `REFERENCE_MAPPING` con validación |
| `'1'` granja destino | FK fija | `L248-273` | temp queries | Granja planta fija | ALTO | `REMOVE` |
| `'1001'` galpón | FK fija | `L248-273` | temp queries | Galpón fijo | ALTO | `REMOVE` |
| `SUBSTRING(AUFNR,1,1)='7'` | Prefijo órdenes | `L248-273` | filtrado órdenes | Rango de órdenes producción | MEDIO | `CURRENT_SAP_VALIDATION` |
| Listas `MATNR` (105xxx/110xxx/115000/120xxx) | Materiales | `querysHana.py` | filtros | Catálogo de materiales avícolas | ALTO | `SAP_MASTER_DATA` + `REFERENCE_MAPPING` |
| `BWART '641','303'` | Tipos de movimiento | `querysHana.py` | filtros | Semántica operativa heredada | ALTO | `CURRENT_SAP_VALIDATION` (+`REFERENCE_MAPPING`) |
| Fechas `20230301/20240301/20250312`, `MJAHR='2024'` | Cortes | `querysHana.py` | ventanas | Inicio de cargas | MEDIO | `REMOVE` (fechas reales de go-live/watermark) |
| `'%NO USAR%'` | Filtro de nombres | `querysHana.py:L0-28` | granjas/almacenes | Marca manual de exclusión | MEDIO | `CURRENT_SAP_VALIDATION` (criterio de baja real) |
| `'125001'` (ejemplo SOAP), `ILgort '1006'`, `IWerks '5000'` | Parámetros de ejemplo | `sap_integration.py:L69` | doc de uso | Ejemplos de llamada | BAJO | `CURRENT_SAP_VALIDATION` |
| `L2TP-PSK` / túnel `LP` / `192.168.14.0/24` | Red | `entrypoint.sh`, `app.py` | VPN | Config VPN legacy | ALTO | `REMOVE` (nueva red a definir con Basis) |
| `verify=False` | TLS | `sap_integration.py` | sesión SOAP | TLS sin verificar | CRÍTICO | `REMOVE` (prohibido como target) |
| Credenciales por env | Secretos | `app.py`,`sap_integration.py` | login | Usuario/clave en `.env` | ALTO | `OWNER_DECISION` (modelo de custodia, `AOD-12`) |

## 7 · SOAP / Z services (§10)

| SERVICE_NAME | PURPOSE | ENDPOINT_PATTERN | AUTH_METHOD | REQUEST_FIELDS | RESPONSE_FIELDS | TLS_BEHAVIOUR | CURRENT_VALIDITY |
|---|---|---|---|---|---|---|---|
| `ZwsTasaMortalidad` | Registro/consulta de tasa de mortalidad | `https://vhemsds4ci.sap.liderpollo.com:44300/vhemsws1wd01` (SOAP WS, `urn:sap-com:document:sap:soap:functions:mc-style`) | HTTP Basic (`SAP_USER/SAP_PASSWORD`) | `IBudat, ICharg, IErfmg, ILgort, IMatnr, IMblnr, IProceso, IWerks` | Respuesta XML genérica parseada por tags | `verify=False` (⚠ prohibido como target) | UNKNOWN |

- **NO ejecutado** (mandato §10): ni disponibilidad ni contrato se validan por red en SAP-0.
- Solo se encontró **un** servicio Z en el material auditado (`ZwsTasaMortalidad`); el gateway `vhemsds4ci` (S/4HANA CI de Lider Pollo) es el único host observado.

## 8 · Elementos prohibidos observados → DO_NOT_REUSE (§3 del mandato)

| Prohibición | Evidencia legacy observada | Clasificación |
|---|---|---|
| VPN embebida en backend | entrypoint + strongswan + xl2tpd + configs montadas | `DO_NOT_REUSE` |
| `network_mode=host`, `NET_ADMIN`, `/dev/ppp`, `/dev/net/tun` | `docker-compose.yml` | `DO_NOT_REUSE` |
| SQL HANA en dominio / hdbcli acoplado | `querysHana.py` + `app.py` + `schemas.py` | `DO_NOT_REUSE` |
| Tablas SAP conocidas por módulos operacionales | consultas directas a `SAPHANADB.*` | `DO_NOT_REUSE` |
| Temp tables + `if_exists=replace` como puente de integración | `inserts_thread.py` | `DO_NOT_REUSE` |
| MATNR/WERKS/LGORT/MANDT/BWART/fechas/destinos hardcodeados | ver §6 | `DO_NOT_REUSE` (→ validación/master data) |
| `session.verify=False` | `sap_integration.py` | `DO_NOT_REUSE` |
| Credenciales/secretos/endpoints con password | env + ejemplos | `DO_NOT_REUSE` (custodia según `AOD-12`) |
| Direct HANA writes | no observados (solo lecturas), pero la capacidad existe por el driver | `DO_NOT_REUSE` (prohibición canónica) |

## 9 · Limitaciones de esta auditoría

- No se descargó el repo al workspace; el análisis proviene del contenido remoto leído por herramientas (no se listó exhaustivamente cada archivo del árbol).
- No se recuperaron secretos ni valores de `.env`; los nombres de variables se citan como **patrón**, jamás valores.
- Todo elemento sin evidencia actual queda `UNKNOWN`/`NEEDS_CURRENT_SAP_VALIDATION` — **nada se asume vigente**.
- No se ejecutó ningún servicio Z, ni conexión, ni VPN (condición del mandato).

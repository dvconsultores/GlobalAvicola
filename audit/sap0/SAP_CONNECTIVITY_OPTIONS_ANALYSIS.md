# SAP-0 · SAP_CONNECTIVITY_OPTIONS_ANALYSIS

Fecha: 2026-09-17 · Fase SAP-0 (SPEC ONLY) · **Ninguna opción se implementa aquí**; este documento fija el marco de comparación y la recomendación condicionada a discovery.

---

## 1 · Opciones evaluadas

| Código | Opción | Descripción |
|---|---|---|
| O1 | **Direct HANA (SQL read-only)** | Cuenta técnica read-only contra el schema SAP de HANA; lecturas masivas. Es lo que usaba el legacy. |
| O2 | **OData V2/V4 (Gateway)** | Servicios estándar/custom (incl. CDS expuestas) sobre SAP Gateway. |
| O3 | **CDS Views** | Vistas analíticas creadas en SAP y expuestas por OData. |
| O4 | **SOAP (Enterprise Services / Z-servicios)** | Legacy usó `ZwsTasaMortalidad` por SOAP + BasicAuth. |
| O5 | **IDoc** | Mensajería asíncrona por ALE; requiere middleware/equipo EDI/Basis. |
| O6 | **RFC/BAPI** | Llamadas de función (pyRFC/JCo); requiere autorización + librería nativa. |
| O7 | **SAP Cloud Connector** | Túnel inverso administrado desde SAP BTP; evita VPN en el contenedor. |
| O8 | **SFTP/intercambio de archivos** | Export/import por ficheros programados; sin llamada directa entre sistemas. |

## 2 · Matriz comparativa (13 dimensiones · §19 del mandato)

| Dimensión | O1 HANA RO | O2 OData | O3 CDS | O4 SOAP | O5 IDoc | O6 RFC/BAPI | O7 Cloud Connector | O8 SFTP |
|---|---|---|---|---|---|---|---|---|
| AUTHENTICATION | usuario/clave HANA (DB) o cert | OAuth2/Basic + certificados (Gateway) | igual que O2 | Basic/OAuth (según WS) | sistema ALE + partner profiles | sistema RFC + perfil | OAuth2 + subaccount | llaves SSH |
| NETWORK_REQUIREMENT | ruta directa a HANA (VPN histórica) | HTTPS expuesto/Gateway | HTTPS | HTTPS | conectividad ALE (NetWeaver) | puerto 33xx (sapgw) | túnel outbound (sin VPN) | salida internet/MPLS |
| READ_ONLY | posible (SOLO con cuenta dedicada) | sí (GET) | sí | sí (según servicio) | sí (inbound a GA) | depende del BAPI | sí | sí |
| INFRASTRUCTURE | baja (driver) pero **acopla al DB** | media (Gateway debe expuesto) | media (desarrollo ABAP para vistas) | media (desarrollo Z) | alta (Basis/EDI) | alta (librería nativa + red SAP) | media-alta (BTP) | baja |
| SECURITY | **alta exposición** (credencial DB con lectura total de tablas SAP) | buena (scopes, roles HTTP) | buena | buena si TLS/secretos OK (legacy usaba verify=False ✗) | buena (idocs firmados por canal) | **alta** (puerto gw expuesto) | **muy buena** (outbound, sin exponer SMTP) | buena |
| MONITORING | herramientas HANA | Gateway logs + BTP | Gateway logs | WS logs | ALE monitoring | SM59/RFC trace | Cloud Connector dashboard | logs SFTP |
| RATE_LIMITS | no nativos (queries pesadas afectan DB) | SICF/limits configurables | idem O2 | según WS | colas ALE | SAP workprocess limits | BTP quotas | ninguno |
| BULK_EXTRACTION | **excelente** | media (paginación) | media-buena | pobre-media | buena (por lotes) | media | media | **excelente** |
| EVENTUAL_LATENCY | baja (consulta directa) | baja-media | media | baja | media-alta | baja | media | **alta** (batch) |
| OPERATIONAL_COST | medio (control DBA) | medio | medio | medio | alto | medio-alto | medio-alto (lic., BTP) | bajo |
| IMPACT_ON_SAP | **alto si queries largas** (bloqueos/HANA load) | controlado | controlado (vistas precalculadas) | bajo | bajo | bajo | bajo | bajo |
| GA_COMPATIBILITY | ❌ contra arquitectura (prohibido acoplar DB SAP) | ✔ (adaptador HTTP) | ✔ (OData-like) | ✔ (adaptador HTTP) | △ (requiere nuevo servicio Bridge) | △ (binarios) | ✔ (transparente para GA) | ✔ (adaptador archivo, ya existe modo manual) |
| LEGACY_EVIDENCE | ✔ usado (hdbcli 2.21.31, puerto 30241) | ✗ no observado | ✗ | ✔ (1 Z-service) | ✗ | ✗ | ✗ | ✗ |

## 3 · Línea base de descubrimiento

- El **legacy demuestra que existe** conectividad de red con el landscape SAP (vía VPN L2TP) y que al menos un servicio Z (SOAP) existe y una cuenta HANA con lectura se usó — **todo eso es evidencia histórica, no current** (`NEEDS_CURRENT_SAP_VALIDATION`).
- `docs/10-sap-integration-strategy.md` (v1.1) menciona los cuatro mecanismos (manual/SFTP/OData/SOAP-IDoc) sin decisión: el descubrimiento actual debe **confirmar disponibilidad real** antes de elegir.

## 4 · Recomendación condicionada (sin implementar)

1. **Preferencia primaria**: `O2/O3` (OData sobre servicios estándar + CDS read-only custom mínimas) — menor impacto en SAP, HTTPS estándar, encaja con adaptador HTTP y con la regla «control directo por SAP» de `GA-REM-010/017`.
2. **Alternativa si OData no existe**: `O1` **solo** como origen de extracción **a través de** la capa SAP Bridge aislada (ver `SAP_BRIDGE_ARCHITECTURE_PROPOSAL.md`), jamás desde el backend del producto.
3. **O4** solo si SAP expone servicios Z administrados (caso legacy conocido `ZwsTasaMortalidad`) — deprecable si O2/O3 disponibles.
4. **O5/O6**: descartados para este programa salvo requisito de SAP (no son accesibles al stack actual sin remediación significativa).
5. **O7**: opción preferida de **red** cuando SAP no quiera exponer endpoints (elimina VPN embebida del lado GA).
6. **O8**: válido como **fallback operacional** (ya existe `manual`/archivo) y para volúmenes masivos iniciales (carga inicial por archivos certificados).

## 5 · Criterios de decisión (GATE SAP-CONN-01)

La elección final requiere: (a) respuesta de SAP Basis al request de información (`SAP_DISCOVERY_EXECUTION_PLAN.md §36`), (b) resultado del probe autorizado (P0–P4), (c) decisión Owner sobre custodia de secretos (`AOD-12`) y entorno de conexión. **Sin esos tres, la decisión queda `PENDING`.**

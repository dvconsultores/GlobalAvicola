# Research — SAP-0 (consolidado de discovery)

**Feature**: `specs/001-sap0-landscape-discovery` · Fecha: 2026-09-17 · Fuentes: repo legacy `dvconsultores/SapHanaLP` (lectura remota), código/specs del producto (lectura local), mandato SAP-0.

---

## 1 · Hallazgos legacy (resumen — detalle en `audit/sap0/SAP_LEGACY_REPOSITORY_AUDIT.md`)

| Tema | Hallazgo |
|---|---|
| Propósito | «Integration SAP 4Hana and App Lider Pollo» (README) |
| Conectividad | VPN L2TP/IPsec embebida en contenedor (strongswan + xl2tpd; `network_mode: host`, `NET_ADMIN`, `/dev/ppp`, `/dev/net/tun`; túnel `LP`/`L2TP-PSK`; `ppp0`; ruta `192.168.14.0/24`) |
| Driver | `hdbcli==2.21.31` — `dbapi.connect` directo a HANA (puerto **30241** hardcodeado; env `HANA_HOST/USER/PASSWORD`) |
| Datos | schema `SAPHANADB`; `MANDT '120'`; tablas `T001W,T001L,EKKO,EKPO,EKBE,LFA1,MATDOC,MAKT,T156HT` (+`AFPO` comentado) |
| Procesos | granjas; galpones; proveedores/transportes; OC aves (machos/hembras); alimento (BWART 641, 105xxx, origen 1000 «ABA»); transferencias; pollitos 120000/120005 (641, desde 3000); gallinas/machos a reproductoras (303, 110002/110003); cría→producción (AUFNR prefijo 7); producción→beneficio; inventarios anuales |
| SOAP | `ZwsTasaMortalidad` en `https://vhemsds4ci.sap.liderpollo.com:44300/vhemsws1wd01`, BasicAuth, `verify=False`; params `IBudat,ICharg,IErfmg,ILgort,IMatnr,IMblnr,IProceso,IWerks` |
| Scheduling | 06/10/14/18 h + arranque; temp-tables `to_sql(if_exists='replace')` + `sleep(3)`; UPSERTs manuales |
| Hardcodes | MANDT, puerto, centros (3000/2500/1000/4089), materiales, BWART, fechas de corte, destinos fijos (`3730`,`1`,`1001`), prefijo AUFNR, `%NO USAR%`, `verify=False` |

## 2 · Estado actual del producto (hechos GA)

- Adaptador: `SapIntegrationAdapter` (ABC) + `ManualSapAdapter` + `MockSapAdapter`; `delivers_to_sap=False` en ambos (GA-REM-010); **no existe `RealSapAdapter`**; `SAP_ADAPTER=real` → NO IMPLEMENTADO (GA-REM-017, `BLOCKED_EXTERNAL`).
- Espejo `sap_references`: 8 tipos; solo `PURCHASE_ORDER` consumido (BR-18).
- Outbox `sap_payloads` pasivo; sin worker; sin confirmación entrante SAP (H360-S09).
- Decisiones abiertas: `AOD-01…05` (export), `AOD-06`/OD-24, `AOD-12` (custodia secretos).
- Auditoría readiness: `SAP_INTEGRATION_READINESS = NOT READY` (2026-09-09).

## 3 · Implicaciones para el contrato inbound

1. El legacy demuestra **qué datos existen** en el SAP de Lider Pollo (pista de discovery), pero **nada** de su técnica es reutilizable.
2. Los 12 objetos inbound cubren el legacy + lo que el producto ya espeja + lo que `docs/10` planifica.
3. `CURRENT_SAP_VALIDATION=PENDING` en todo: el contrato es una **propuesta formal** a validar contra el SAP actual.
4. `GL-OD-06` no puede declararse resuelto: falta evidencia current → `BLOCKED_EXTERNAL_SAP_INFORMATION`.

## 4 · Referencias

- Mandato SAP-0 (Owner, 2026-09-17) · `audit/go-live/*` (baseline G0) · `audit/remediation/SAP_INTEGRATION_READINESS_AUDIT.md` · `audit/remediation/SAP_DEFERRED_LOCAL_PLACEHOLDERS.md` · `specs/remediation/GA-REM-017-SAP-REAL-INTEGRATION.md` · `specs/remediation/OD-12-SAP-TRANSVERSAL-CONTRACT.md` · `specs/remediation/OD-24-COMPANIES-FARMS-FROM-SAP.md` · `docs/10-sap-integration-strategy.md` · `backend/app/integrations/sap/adapter.py`.

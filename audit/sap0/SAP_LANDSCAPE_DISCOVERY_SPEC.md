# SAP-0 · SAP_LANDSCAPE_DISCOVERY_SPEC

Fecha: 2026-09-17 · Fase SAP-0 (SPEC ONLY) · Fuente legacy: `SapHanaLP` (`LEGACY_SAP_DISCOVERY_EVIDENCE`)
Regla: **todo campo del landscape está `UNKNOWN` salvo evidencia CURRENT verificable.** Hoy no existe evidencia current: todo es legado o suposición.

---

## 1 · Catálogo de datos a descubrir (§34 del mandato)

| # | Campo | Estado inicial | Nota |
|---|---|---|---|
| L01 | `SAP_PRODUCT` | **UNKNOWN** | Legacy habla de «SAP 4Hana» (README) y host `vhemsds4ci` (S/4 CI) — no verificado |
| L02 | `SAP_VERSION` | **UNKNOWN** | — |
| L03 | `SAP_SYSTEM_ID` | **UNKNOWN** | Patrón observado: `vhemsds4ci`/`vhemsws1wd01` (¿SID `hem`?) |
| L04 | `SAP_DEPLOYMENT_TYPE` | **UNKNOWN** | ¿on-premise / RISE / cloud? |
| L05 | `SAP_S4HANA_VERSION` | **UNKNOWN** | — |
| L06 | `SAP_DATABASE` | **UNKNOWN** | Legacy usaba HANA (`SAPHANADB`) |
| L07 | `SAP_HANA_VERSION` | **UNKNOWN** | — |
| L08 | `MANDANTS` | **UNKNOWN** | único valor legacy: `120` (hardcode) — ¿sigue activo? |
| L09 | `COMPANY_CODES` | **UNKNOWN** | legacy: `BUKRS` leído pero mal etiquetado; ver `AOD-06`/OD-24 |
| L10 | `PLANTS` | **UNKNOWN** | legacy: 1000/2000/2002/2500/3000/4089/5000 (patrones) |
| L11 | `HANA_SQL_AVAILABLE` | **UNKNOWN** | legacy: sí vía red dedicada; ¿sigue permitido? |
| L12 | `READ_ONLY_ACCOUNT_AVAILABLE` | **UNKNOWN** | requisito de este programa |
| L13 | `ODATA_AVAILABLE` | **UNKNOWN** | recomendado en `docs/10` (sin confirmación) |
| L14 | `CDS_AVAILABLE` | **UNKNOWN** | — |
| L15 | `SOAP_AVAILABLE` | **UNKNOWN** | legacy: 1 servicio Z; ¿vigente? |
| L16 | `IDOC_AVAILABLE` | **UNKNOWN** | — |
| L17 | `RFC_AVAILABLE` | **UNKNOWN** | — |
| L18 | `SAP_CLOUD_CONNECTOR_AVAILABLE` | **UNKNOWN** | — |
| L19 | `NETWORK_PATH` | **UNKNOWN** | legacy: VPN L2TP hacia `192.168.14.0/24` |
| L20 | `VPN_REQUIRED` | **UNKNOWN** | legacy: sí; hoy desconocido |
| L21 | `TLS` | **UNKNOWN** | legacy: TLS sin verificar (`verify=False`) |
| L22 | `AUTH_METHODS` | **UNKNOWN** | legacy: user/pass (HANA), Basic (SOAP) |
| L23 | `CUSTOM_Z_SERVICES` | **UNKNOWN** | legacy: `ZwsTasaMortalidad` |
| L24 | `SAP_API_GATEWAY` | **UNKNOWN** | legacy: `vhemsws1wd01` (WS), puerto 44300 |

## 2 · Probe plan (diseñado, **NO ejecutado**) → detalle en `SAP_DISCOVERY_EXECUTION_PLAN.md` y `SAP_DISCOVERY_EXECUTION_PLAN §Probe`

```
P0 NETWORK → P1 SYSTEM IDENTITY/VERSION → P2 PERMISSIONS → P3 METADATA/CATALOG
→ P4 TINY READ-ONLY SAMPLES → P5 RECONCILIATION → P6 DISCONNECT
```

Cada fase define: `allowed_actions`, `forbidden_actions`, `evidence_required`, `stop_conditions`, `security_controls` (ver plan). Sin credenciales reales en documentación.

## 3 · Requisitos de prueba (qué debe existir ANTES de un probe real)

1. Cuenta técnica **READ-ONLY** mínima (o perfil de autorización equivalente) — `SAP_BASIS_INPUT`.
2. Ruta de red documentada (VPN propia del lado SAP o endpoint expuesto) — decisión de Basis.
3. Autorización explícita del Owner para el probe (GATE: SAP0_PROBE_AUTHORIZATION) — **no antes de completar SPEC/PLAN/TASKS**.
4. Entorno no productivo por defecto; si el único disponible es productivo, probe P4 limitado a catálogo (P3) — decisión Owner.
5. Registro de evidencia por fase (comandos, salidas saneadas, timestamps) y **desconexión P6**.

## 4 · Veredicto de esta spec

`SAP0_LANDSCAPE = UNKNOWN` (todos los campos) ⇒ **`GL-OD-06 = BLOCKED_EXTERNAL_SAP_INFORMATION`** mientras no exista evidencia current (§38 del mandato: sin tercera vía).

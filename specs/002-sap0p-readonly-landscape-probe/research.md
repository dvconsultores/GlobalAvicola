# Research — SAP-0P (pre-probe)

**Feature**: `specs/002-sap0p-readonly-landscape-probe` · Fecha: 2026-09-17
Insumos: SAP-0 (`audit/sap0/**`), mandato SAP-0P, verificación local P0/P1, repo legacy `SapHanaLP` (evidencia histórica).

---

## 1 · Qué se conoce (y con qué estado)

| Elemento | Valor conocido | Estado |
|---|---|---|
| Conexión histórica legacy | VPN L2TP/IPsec embebida; `hdbcli` directo; puerto `30241` | `LEGACY_CONFIRMED` |
| Schema legacy | `SAPHANADB` | `LEGACY_CONFIRMED` |
| Mandante legacy | `120` | `LEGACY_CONFIRMED` |
| Tablas legacy | T001W, T001L, EKKO, EKPO, EKBE, LFA1, MATDOC, MAKT, T156HT (+AFPO comentado) | `LEGACY_CONFIRMED` |
| BWART legacy | 641 (transferencias), 303 (a reproductoras) | `LEGACY_CONFIRMED` |
| SOAP legacy | `ZwsTasaMortalidad` (BasicAuth; `verify=False` prohibido como target) | `LEGACY_CONFIRMED` |
| Landscape «sin cambios» | OC-01…OC-11 | `OWNER_CONFIRMED_CURRENT_UNCHANGED` |
| Todo lo técnico current | — | `NOT_VERIFIED` |

## 2 · Qué exige el probe (P2–P7) y no pudo ejecutarse

Identidad/versiones (HANA/SAP/SID/mandante), permisos efectivos, metadata de 9 tablas + objetos inbound, muestras mínimas, reconciliación multicompañía, servicios (OData/CDS/SOAP), condiciones GL-OD-06. Todos requieren el canal autorizado + cuenta RO.

## 3 · Resultado del preflight local (evidencia real)

| Chequeo | Resultado | Interpretación |
|---|---|---|
| Repo limpio en `0904330` | ✔ | P0 PASS |
| Diff de producto (`backend/frontend/e2e/.github`) | vacío | PRODUCT_FILES_CHANGED=0 |
| Env vars `HANA_*`/`SAP_*` presentes | **0** | sin configuración en entorno |
| `.env` presente / claves HANA/SAP dentro | 1 archivo / **0 claves** | sin credenciales SAP |
| `ipsec` / `xl2tpd` instalados | **AUSENTES** | canal legacy no replicado aquí |
| Interfaces `ppp*`/`tun*` | **0** | sin túnel activo |
| DNS host legacy (`vhemsds4ci…`) | **0 resoluciones** | host no alcanzable/no resoluble desde aquí |
| `hdbcli` | ausente | sin driver (y no debe añadirse en esta fase) |
| `requests` | presente | irrelevante sin canal |

Conclusión: **falta el canal autorizado completo** (VPN + ruta + cuenta + host/port vigentes + permiso). Conforme a §9 del mandato: `SAP0P_STATUS = BLOCKED_EXTERNAL`, una única acción «SAP ADMIN / BASIS ACTION REQUIRED», STOP del probe (sin inventar resultados).

## 4 · Riesgos de seguridad considerados

1. **No** se intentó conexión TCP al SAP desde red no autorizada (ruta no autorizada ⇒ prohibido; el probe debe correr desde el canal acordado).
2. **No** se imprimieron valores de configuración: solo presencia/conteos (`0/1`), jamás secretos.
3. **No** se instaló/alteró VPN, rutas ni firewall.

## 5 · Referencias
Mandato SAP-0P §3–§9, §17–§18, §36–§38, §43, §46, §49 · `audit/sap0/SAP_DISCOVERY_EXECUTION_PLAN.md` · `audit/sap0/SAP_CONNECTIVITY_OPTIONS_ANALYSIS.md` · `SapHanaLP` (legacy).

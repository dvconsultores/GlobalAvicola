# SAP-0P · SAP0P_READONLY_PROBE_CERTIFICATION

Fecha: 2026-09-17 · **Certificación honesta**: se certifica **solo lo demostrado**. El probe técnico contra SAP **no se ejecutó** (acceso no provisionado); por regla «NO EVIDENCE = NO CERTIFICATION», nada más recibe estado verificado.

---

## 1 · Certificación por dominio

| Dominio | Estado certificado | Base de la certificación |
|---|---|---|
| OWNER CONFIRMATION | **FORMALIZED** | `SAP0P_OWNER_CONFIRMATION.md` (OC-01…OC-11 como `OWNER_CONFIRMED_CURRENT_UNCHANGED`) |
| SPEC DEVELOPMENT | **PASS** | `specs/002-…` (spec/plan/tasks/analyze/converge) |
| READ_ONLY SAFETY | **PASS** | `SAP0P_SECURITY_REVIEW.md` |
| P0 PREFLIGHT | **PASS** | repo limpio en `0904330`; producto intacto; límites y stop conditions definidos |
| NETWORK | **BLOCKED** | canal autorizado ausente (0 IPsec/xl2tpd, 0 ppp/tun, DNS sin resolver) |
| VPN | **BLOCKED (no provisionada)** | idem (la VPN legacy `L2TP-PSK/LP` es `LEGACY_CONFIRMED`) |
| HANA | **NOT_VERIFIED** | sin conexión (no intentada: red no autorizada) |
| SAP_IDENTITY | **NOT_VERIFIED** | — |
| MANDANT | **NOT_VERIFIED** (legacy `120` = `LEGACY_CONFIRMED`) | — |
| PERMISSIONS / LEAST PRIVILEGE | **NOT_VERIFIED** (cuenta no provisionada) | `SAP0P_PERMISSION_ASSESSMENT.md` |
| SCHEMA | **NOT_VERIFIED** (legacy `SAPHANADB` = `LEGACY_CONFIRMED`) | — |
| TABLES (9 legacy) | **NOT_VERIFIED (0/9)** | `SAP0P_LANDSCAPE_VERIFICATION.md` |
| INBOUND OBJECTS (12) | **NOT_VERIFIED (0/12)** | `SAP0P_INBOUND_OBJECT_VERIFICATION.md` |
| COMPANY/PLANT (OD-24) | **NOT_VERIFIED · PENDING_MAPPING** | `SAP0P_OD24_COMPANY_PLANT_EVIDENCE.md` |
| LGORT ↔ galpón | **SIN EVIDENCIA NUEVA · OWNER_DECISION_REQUIRED** | `SAP0P_STORAGE_LOCATION_FINDINGS.md` |
| ODATA | **OWNER_CONFIRMED_CURRENT_UNCHANGED · TECHNICALLY_NOT_VERIFIED** | §30 del mandato (probe no ejecutado) |
| CDS | **OWNER_CONFIRMED_CURRENT_UNCHANGED · TECHNICALLY_NOT_VERIFIED** | idem |
| SOAP | **NOT_VERIFIED** (no en la confirmación; sin discovery) | §31 |
| ZwsTasaMortalidad | **NOT_VERIFIED** (no invocado ni descubierto; correcto: sin POST SOAP) | §31 |
| DIRECT_HANA_TECHNICAL_FEASIBILITY | **NOT_VERIFIED** | sin conexión |
| DIRECT_HANA_PRODUCTION_DECISION | **PENDING** (sin cambio — SAP-0P no decide arquitectura, §32) | — |
| SAP BRIDGE | **RECOMMENDED (sin cambios; observación: canal aún no verificado)** | §33; separación estricta si VPN persiste |
| GL-OD-06 | **BLOCKED_EXTERNAL_SAP_INFORMATION** | `SAP0P_GL_OD_06_READINESS.md` |
| GA-REM-017 | **STILL_BLOCKED_EXTERNAL** · `NOT IMPLEMENTED` preservado | `SAP0P_GA_REM_017_RECONCILIATION.md` |
| DEPLOY | **NO EJECUTADO** (0 workflows disparados) | §47 |

## 2 · Salvaguardas certificadas (lado ejecución)

```
SAP_WRITES_EXECUTED = 0
DOMAIN_WRITES_EXECUTED = 0
SAP_CONNECTION_ATTEMPTS = 0
REAL_SAP_READS = 0
QUERIES_UNBOUNDED = 0
SECRETS_IN_EVIDENCE = 0
PRODUCT_FILES_CHANGED = 0
UNAUTHORIZED_NETWORK_ATTEMPTS = 0
```

## 3 · Qué NO certifica este documento

- No certifica conectividad, versiones, identidades, permisos, tablas, objetos, servicios ni condiciones GL-OD-06.
- No certifica la equivalencia LGORT↔galpón ni ningún mapeo multicompañía.
- No certifica el mecanismo de integración ni la viabilidad de Direct HANA.

## 4 · Condición de re-certificación

Cumplida `SAP_ADMIN_BASIS_ACTION_REQUIRED.md` → re-ejecutar SAP-0P desde P0 en el entorno autorizado → nueva certificación con evidencia real (P1–P10). Solo entonces podrán existir estados `TECHNICALLY_VERIFIED_CURRENT`.

```
CERTIFICATION SAP-0P = EMITIDA (alcance: P0/P1 + spec-development; resto BLOCKED_EXTERNAL)
```

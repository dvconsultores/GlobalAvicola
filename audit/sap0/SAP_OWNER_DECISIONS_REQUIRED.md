# SAP-0 · SAP_OWNER_DECISIONS_REQUIRED

Fecha: 2026-09-17 · Fase SAP-0 (SPEC ONLY) · Solo **gates reales** (una decisión que el Owner/Basis debe tomar) — no se elevan como decisión preguntas que el discovery técnico o la norma SAP pueden resolver.

Leyenda de clasificación: `SAP_BASIS_INPUT` (respuesta técnica de SAP) · `BUSINESS_OWNER_DECISION` (decisión funcional del cliente) · `TECHNICAL_DISCOVERY` (se resuelve en probe/analítica de metadata, no requiere Owner).

---

## 1 · Gates del programa SAP-0

| # | Gate | Clasificación | Pregunta | Fuente | Estado |
|---|---|---|---|---|---|
| SAP-BASIS-01 | Respuesta al request de información (20 puntos) | `SAP_BASIS_INPUT` | Landscape, red, cuentas RO, servicios disponibles | `SAP_DISCOVERY_EXECUTION_PLAN.md §4` | **PENDING** |
| SAP0_PROBE_AUTHORIZATION | Autorización formal para ejecutar P0–P6 (o P0–P3) | `SAP_BASIS_INPUT` + Owner | ¿Cuándo y en qué entorno se autoriza el probe? | Plan §2–3 | **PENDING** |
| SAP-CONN-01 | Elección de mecanismo/red (OData/CDS/SOAP/HANA-RO/SFTP + VPN o Cloud Connector) | `SAP_BASIS_INPUT` + `BUSINESS_OWNER_DECISION` | Depende de SAP-BASIS-01 + probe | `SAP_CONNECTIVITY_OPTIONS_ANALYSIS.md` | **PENDING** |
| SAP-STO-01 | ¿`LGORT` (almacén) equivale a **galpón** en el modelo GA? | `BUSINESS_OWNER_DECISION` (AOD-02) | Evidencia legacy la mapeaba sin validar | `SAP_INBOUND_DATA_CATALOG.md` ob.3 | **PENDING** |
| SAP-CLASS-01 | Clasificación funcional de plantas (granja/incubadora/planta/administrativa) | `TECHNICAL_DISCOVERY` + validación negocio | Legacy mezclaba `3000`, `1000`, `2500`, `4089` | Convergencia §4 | **PENDING** |
| SAP-LOT-01 | ¿Lote productivo GA = batch SAP (`CHARG`), orden interna, orden de producción o custom? | `BUSINESS_OWNER_DECISION` (AOD-03) | `H360-S05`; `lots.lot_code` sin clave SAP | `SAP_INBOUND_DATA_CATALOG.md` ob.11 | **PENDING** |
| SAP-CUSTODY-01 | Dónde viven los secretos SAP (por empresa vs entorno) y quién opera la rotación | `BUSINESS_OWNER_DECISION` (AOD-12) | No hay variables SAP en `config.py` hoy | Auditoría readiness §7 | **PENDING** |
| SAP-SCOPE-01 | Alcance de la **primera** ola de inbound: ¿los 12 objetos o subconjunto prioritario? | `BUSINESS_OWNER_DECISION` | Inbound catalog cubre 12; priorizar evita sobrealcance | `SAP_INBOUND_DATA_CATALOG.md` | **PENDING** |
| SAP-ENV-01 | ¿Probe contra no-productivo o productivo (limitado)? | `BUSINESS_OWNER_DECISION` + Basis | Plan §1.6 | Plan §2 | **PENDING** |
| SAP-SEC-01 | Aprobación de protección de datos para almacenar RAW de SAP en Postgres GA (retención, acceso) | `BUSINESS_OWNER_DECISION` + Seguridad | `SAP_RAW_STAGING_SPEC.md` §2 | RAW spec | **PENDING** |
| SAP-FALLBACK-01 | ¿Se acepta SFTP/archivos como fallback operativo mientras se define el mecanismo? | `BUSINESS_OWNER_DECISION` | Modo `manual` ya existe (GA-REM-010) | Connectivity §4.6 | **PENDING** |
| SAP-PROD-01 | ¿La integración incluirá **escritura** SAP (envíos) en una fase posterior o solo lectura inbound? | `BUSINESS_OWNER_DECISION` | SAP-0 solo especifica inbound; export depende de `AOD-01…05` | `docs/10` + readiness | **PENDING** |

## 2 · Gates heredados (no se duplican aquí)

| Gate | Dónde | Relación |
|---|---|---|
| `AOD-01…AOD-05` (5 decisiones WAVE D) | `SAP_INTEGRATION_READINESS_AUDIT.md §4` | Necesarias para **export**; no bloquean el inbound SAP-0 |
| `AOD-06` / `OD-24` (empresa/granja espejo SAP) | OD-24 + convergencia spec | SAP-0 aporta la spec de convergencia; el timing de implementación es del Owner |
| `GL-OD-06` | `audit/go-live/GO_LIVE_OWNER_DECISIONS_REQUIRED.md` | SAP-0 lo reevalúa (§38): `BLOCKED_EXTERNAL_SAP_INFORMATION` |

## 3 · Regla de gobierno

- Ninguna decisión de este documento se toma en SAP-0. Se **registran** con su clasificación para que el Owner/Basis las resuelva en la fase de discovery real.
- Las decisiones `TECHNICAL_DISCOVERY` se convertirán en hallazgos verificables durante el probe autorizado (no requieren al Owner salvo confirmación funcional).
- Este registro es la entrada del futuro **GATE de continuidad** hacia SAP-1 (bridge/extracción) — que no se inicia sin `SAP-BASIS-01` + `SAP0_PROBE_AUTHORIZATION` resueltos.

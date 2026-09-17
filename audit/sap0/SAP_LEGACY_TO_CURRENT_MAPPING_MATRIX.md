# SAP-0 · SAP_LEGACY_TO_CURRENT_MAPPING_MATRIX

Fecha: 2026-09-17 · Fase SAP-0 (SPEC ONLY)
Propósito: separar **HECHOS LEGACY** de **HECHOS SAP ACTUAL** (§13 del mandato) y mapear el legacy contra la arquitectura y el dominio del producto actual (`GlobalAvicola`).

Regla de separación (§13):
- `LEGACY_FACT` = observado en `dvconsultores/SapHanaLP` (ver `SAP_LEGACY_REPOSITORY_AUDIT.md`).
- `CURRENT_SAP_FACT` = solo verificable con evidencia current → **hoy: no existe ninguna** (todo `UNKNOWN`).
- `GA_CURRENT_FACT` = estado del producto GA hoy (código en `backend/`, `frontend/`, specs).

---

## 1 · Matriz por objeto de negocio

| OBJETO LEGACY (SapHanaLP) | LEGACY_TARGET (PostgreSQL del legacy) | GA_CURRENT_EQUIVALENT | GA_CURRENT_KEY | ESTADO GA HOY | FUENTE DE SEPARACIÓN |
|---|---|---|---|---|---|
| `T001W` granjas (WERKS,NAME1) | `granjas.id_sap`+`name` | `masters/farms` (`farms.code`, name) | `code` (String, sin clave SAP) | Maestro local (PL-06, `NO_DECLARADO`) | `LEGACY_FACT` vs `GA_CURRENT_FACT` |
| `T001W` centros no-granja (3000,1000,2500,4089) | excluidos / usados en querys | `companies`/planta incubación | — | sin equivalente (PL-05, PL-08) | idem |
| `T001L` almacenes (LGORT,LGOBE) | `galpones.id_sap`+`granjaIdId` | `masters/houses` (`houses.code`) | por granja | Maestro local (PL-07) | idem |
| `LFA1` (LIFNR,NAME1) | `proveedores` **y** `transportes` | `masters/suppliers` (+catálogo transportes) | `sap_code` opcional / `code` | PL-04 `NO_DECLARADO` (doble vía) | idem |
| `EKKO`+`EKPO` (EBELN,UNIQUEID,MATNR,MENGE,AEDAT) | `crias_ordenes_recepcion` | `sap_references PURCHASE_ORDER` + eventos `grandparent_import`/`bird_reception` | `sap_code` espejo | Espejo SAP parcial (PL-11 `DECLARADO`) | idem |
| `EKBE` historial OC | — (solo prueba) | — | — | No consumido | idem |
| `MATDOC` BWART 641 alimento | `alimento_ordenes` | `feed_registration` / `feed_movements` | — | eventos operativos locales | idem |
| `MATDOC` BWART 641 huevo 115000 | (comentado `produccion_ordenes_salida_huevos`) | `egg_production`/`egg_dispatch` | — | eventos locales | idem |
| `MATDOC` BWART 641 pollitos 120000/120005 | `incubadora_ordenes_salida_pollitos` | eventos `bird_reception` (broiler) + `sap_references` | — | local | idem |
| `MATDOC` BWART 303 gallinas/machos 110002/110003 | `crias_ordenes_salida` | `bird_distribution`/transferencias internas | — | local | idem |
| `MATDOC` orden salida cría→producción (AUFNR 7x) | `crias_ordenes_salida` | idem | — | local | idem |
| `MATDOC` salida producción→beneficio | `produccion_ordenes_salida` | `bird_exit` | — | local | idem |
| `MATDOC` inventarios anuales | reporte plano | reportes/KPIs GA | — | **no consumido** | idem |
| `MAKT` (MAKTX) | descripciones material | nombres locales de alimento/vacunas/medicinas | `code` | PL-01/02/03 `NO_DECLARADO` | idem |
| `T156HT` textos BWART | — | — | — | — | idem |
| `CHARG`/batches | `lote` en temp/salidas | `sap_references SAP_BATCH`; `lots.lot_code` (sin clave SAP) | `lot_code` String(100) | PL-09 `NO_DECLARADO`, `H360-S05` | idem |
| `ZwsTasaMortalidad` (SOAP) | (no persistido en SQL legacy) | `mortality_recording` (evento local) | — | local; envío SAP no implementado | idem |

## 2 · Clasificación de transferencia de conocimiento

| Elemento legacy | ¿Se transfiere como conocimiento? | Tratamiento |
|---|---|---|
| Tablas y campos usados (`MATDOC` como corazón de documentos) | **SÍ como pista de discovery** | `CANDIDATE_FOR_DISCOVERY` (validación current obligatoria) |
| Semántica BWART 641/303 y flujos alimento/aves/huevos | **SÍ como hipótesis de negocio** | `BUSINESS_RULE_NEEDS_VALIDATION` |
| Estructura `T001W/T001L` como maestros | **SÍ** | `CANDIDATE_FOR_DISCOVERY` |
| Hardcodes (MANDT, materiales, fechas, destinos) | **NO** | `DO_NOT_REUSE` |
| VPN embebida, host network, NET_ADMIN | **NO** | `DO_NOT_REUSE` |
| hdbcli directo + SQL en dominio | **NO** | `DO_NOT_REUSE` |
| Temp tables + `if_exists=replace` | **NO** | `DO_NOT_REUSE` |
| `verify=False` y auth Basic sin custodia | **NO** | `DO_NOT_REUSE` |
| Puertos/hosts (`30241`, `vhemsds4ci…`) | **NO como valor**; **SÍ como pista** | `NEEDS_CURRENT_SAP_VALIDATION` |
| Endpoint WS `vhemsws1wd01`, `ZwsTasaMortalidad` | **SÍ como pista** | `NEEDS_CURRENT_SAP_VALIDATION` |

## 3 · Gaps explícitos entre legacy y producto actual

| # | Gap | Implicación |
|---|---|---|
| G-01 | El legacy importa ~10 objetos; GA hoy importa **solo por archivo manual** (modo `manual`) y refleja 8 tipos en `sap_references` (1 consumido) | SAP-0 debe especificar el contrato de los 12 inbound objects (§14) — hecho en `SAP_INBOUND_DATA_CATALOG.md` |
| G-02 | El legacy no tiene idempotencia ni RAW/STAGING | El producto introduce RAW/STAGING + idempotencia (`SAP_RAW_STAGING_SPEC.md`) |
| G-03 | El legacy escribe directo a tablas operativas | Prohibido: promoción por job controlado (§22) |
| G-04 | Convergencia empresas/granjas no existe en legacy ni en GA | `SAP_COMPANY_FARM_CONVERGENCE_SPEC.md` (OD-24) |
| G-05 | Decisiones de negocio `AOD-01…05` y `AOD-06` (OD-24) abiertas | `SAP_OWNER_DECISIONS_REQUIRED.md` |

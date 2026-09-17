# SAP-0 · SAP_COMPANY_FARM_CONVERGENCE_SPEC

Fecha: 2026-09-17 · Fase SAP-0 (SPEC ONLY) · Satisface la parte conceptual de `OD-24` y el ítem `GL-OD-06` §15 del mandato.
Estado del código: **nada implementado** (post-P-08: `Company`=espejo SAP, `Farm`=espejo Plant, lectura local — sin fuente SAP real).

---

## 1 · Objetivo

Definir **cómo convergen** las entidades Empresa (`companies`) y Granja (`farms`) del producto con sus orígenes SAP cuando exista la integración (inbound §14): sin duplicar, sin huérfanos, sin mezcla multi-compañía y con decisión humana donde no haya equivalencia automática.

## 2 · Entidades y claves propuestas

| GA | Clave canónica | Clave SAP origen | Objeto inbound |
|---|---|---|---|
| `companies` | `id` interno + `sap_company_code` (nueva, nullable) | BUKRS | SAP_COMPANY |
| `farms` | `id` interno + `sap_plant_code` (nueva, nullable) | WERKS | SAP_PLANT |
| `houses` (contexto, fuera de OD-24 pero dependiente) | `id` + `sap_storage_location` (propuesta) | LGORT | SAP_STORAGE_LOCATION |

`TENANT_MAPPING`: `company_code → companies` (1:1 estricto, fail-closed). `BU_MAPPING`: sin automatismos; una compañía puede contener N BU (OD-09) y la asignación es decisión de negocio.

## 3 · Estados de convergencia (§15 del mandato)

| Estado | Condición | Acción por defecto |
|---|---|---|
| `MATCH` | registro SAP y GA con misma clave y atributos equivalentes | mantener |
| `CONFLICT` | misma clave, atributos divergentes | cuarentena + reporte; resolución manual (no sobrescritura ciega) |
| `MISSING_IN_SAP` | entidad GA con clave propuesta que no existe en SAP | **NO borrar**; marcado `PENDING_OWNER` (posible alta pendiente) |
| `MISSING_IN_GA` | entidad SAP sin representación GA | candidata a alta (promoción), sujeta a reglas de negocio |
| `DUPLICATE` | ambas lados con múltiples registros equivalentes | bloqueo + revisión manual |
| `MANUAL_REVIEW_REQUIRED` | cualquier duda (clasificación de centro, `NO USAR`, tipo de planta) | cola de revisión |

Ningún estado provoca escritura destructiva automática. La convergencia se **reporta** (informe por lote) antes de cualquier promoción.

## 4 · Hallazgos legacy que fuerzan decisiones (no reglas)

Evidencia legacy (ver `SAP_LEGACY_REPOSITORY_AUDIT.md`):
- `T001W` incluía centros que **no eran granjas**: `3000` (incubadora), `1000` («ABA»), `2500` (excluido), `4089` (despacho); el legacy además ocultaba registros con `'%NO USAR%'`.
- `T001L` (almacén) se mapeaba a **galpón** sin validación de negocio.

⇒ La convergencia **no puede** asumir «todo WERKS es granja» ni «todo LGORT es galpón». Se requieren:
- `SAP-CLASS-01` (TECHNICAL_DISCOVERY): clasificación real de plantas (granja vs incubadora vs planta de proceso vs administrativa).
- `SAP-STO-01` (BUSINESS_OWNER_DECISION): equivalencia LGORT↔galpón (AOD-02).
- `SAP-BP-01` (definición de «baja lógica» SAP para reemplazar `NO USAR`).

## 5 · Multi-compañía (requisito duro)

1. Toda entidad converge **dentro** de su compañía; jamás un `MISSING_IN_GA` de la compañía A se satisface con un registro de la compañía B.
2. Si `company_code` no resuelve a `companies` existente → `QUARANTINE_COMPANY` (fail-closed).
3. Las promociones se ejecutan en lotes con resumen por compañía (`promotion_job_id`, contadores, conflictos).

## 6 · Flujo de convergencia (diseño)

```
SAP (inbound) → RAW → validación → STAGING (claves propuestas)
   → CLASIFICADOR de convergencia (MATCH/CONFLICT/MISSING_*/DUPLICATE/MANUAL)
   → INFORME de convergencia por compañía (obligatorio)
   → RESOLUCIÓN (manual/Owner para excepciones)
   → PROMOCIÓN de altas/actualizaciones aprobadas
```

## 7 · Criterios de aceptación de la futura implementación (no de SAP-0)

- AC-CONV-01: 100 % de registros de ambos maestros en un estado explícito (§3).
- AC-CONV-02: cero cruces de compañía en reportes y promociones.
- AC-CONV-03: `MISSING_IN_SAP` no borra nada; `CONFLICT` no sobrescribe sin resolución.
- AC-CONV-04: informe reproducible por lote con conteos y muestras.
- AC-CONV-05: LGORT↔galpón y clasificación de plantas resueltas por decisión registrada, no por heurística.

## 8 · Relación con OD-24

Este documento **no cambia** el estado de OD-24 en producto (código sin tocar). Aporta el diseño de convergencia exigido por SAP-0 y deja nombradas las decisiones externas necesarias. `OD-24` permanece `ACCEPTED (spec)` / implementación pendiente de fuente real.

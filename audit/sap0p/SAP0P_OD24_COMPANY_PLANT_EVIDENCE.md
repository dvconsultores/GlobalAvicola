# SAP-0P · SAP0P_OD24_COMPANY_PLANT_EVIDENCE

Fecha: 2026-09-17 · Evidencia técnica OD-24: **ninguna disponible** (probe bloqueado). Sin escrituras a Company/Farm (§24 del mandato); sin convergencia.

---

## 1 · Qué debía verificarse (§24)

Identificar técnicamente, para la futura convergencia OD-24: `MANDT`, `BUKRS` (cuando corresponda), `WERKS`, `NAME`, y relaciones disponibles — necesarios para la cadena multicompañía:

```
SAP SYSTEM → MANDT → BUKRS → WERKS → GA COMPANY → BU
```

## 2 · Estado por elemento

| Elemento | Legacy | Técnico actual | Estado SAP-0P |
|---|---|---|---|
| MANDT | `120` (hardcode) | no leído | `LEGACY_CONFIRMED` + `OWNER_CONFIRMED_CURRENT_UNCHANGED`; técnico `NOT_VERIFIED` |
| BUKRS ↔ company | `MATDOC.BUKRS` leído y mal etiquetado | no leído | `NOT_VERIFIED` |
| WERKS ↔ plant/farm | `T001W` con filtros y exclusiones | no leído | `NOT_VERIFIED` |
| NAME relaciones | `T001W.NAME1/NAME2` | no leído | `NOT_VERIFIED` |
| Clasificación de plantas (granja/incubadora/planta/admin) | mezcladas (`3000/1000/2500/4089`) | no verificada | `PENDING` (`SAP-CLASS-01`) |
| Relaciones disponibles | joins legacy por código | no verificadas | `NOT_VERIFIED` |

## 3 · Comparación conceptual contra GA (permitida, sin ejecutar convergencia)

| Clase | Resultado |
|---|---|
| MATCH_CANDIDATE | **no computable** sin datos técnicos (no inventar) |
| CONFLICT_CANDIDATE | **no computable** |
| MISSING_IN_GA | **no computable** |
| MISSING_IN_SAP | **no computable** |

Estados a usar cuando exista evidencia: los de `SAP_COMPANY_FARM_CONVERGENCE_SPEC.md` (SAP-0); cualquier inconsistencia de alcance → `PENDING_MAPPING`; **fail-closed**.

## 4 · Reglas respetadas

- **No** se creó/modificó ninguna Company/Farm/`sap_references` (DOMAIN_WRITES_EXECUTED=0).
- **No** se ejecutó convergencia.
- **No** se asumió equivalencia alguna (LGORT↔galpón permanece abierto; ver `SAP0P_STORAGE_LOCATION_FINDINGS.md`).

## 5 · Consecuencia para GL-OD-06

Sin ningún elemento verificable (MANDT/BUKRS/WERKS), OD-24 no puede avanzar técnicamente → aporta directamente al resultado `GL_OD_06 = BLOCKED_EXTERNAL_SAP_INFORMATION` (ver `SAP0P_GL_OD_06_READINESS.md`).

# SAP-0P · SAP0P_STORAGE_LOCATION_FINDINGS

Fecha: 2026-09-17 · Tema: `T001L` (WERKS, LGORT, LGOBE) y la cuestión `LGORT ↔ galpón` · **Sin evidencia técnica nueva** (probe bloqueado). No se decide automáticamente.

---

## 1 · Qué debía verificarse (§25)

- Existencia/estructura de `T001L` (WERKS, LGORT, LGOBE) con muestra mínima.
- **NO** decidir automáticamente `LGORT = GALPÓN`.
- Actualizar el clarification item `SAP_STORAGE_LOCATION_MAPPING` con evidencia real (si existe).

## 2 · Estado actual del item `SAP_STORAGE_LOCATION_MAPPING`

| Aspecto | Estado |
|---|---|
| Evidencia técnica | **NINGUNA** (P4/P5 no ejecutados) |
| Legacy | `T001L.LGORT/LGOBE` → tabla `galpones` (mapeo sin validación de negocio) — `LEGACY_CONFIRMED` |
| Owner confirmation | landscape sin cambios (OC-01…11) — no ilumina la semántica LGORT |
| Decisión funcional | `OWNER_DECISION_REQUIRED` (SAP-STO-01 / AOD-02) — **sin cambios** |

## 3 · Clasificación de la cuestión (sin cambios respecto de SAP-0)

- La equivalencia funcional final **puede seguir siendo** `OWNER_DECISION_REQUIRED` aunque el probe verifique estructura (el probe puede aportar semántica técnica —granularidad, unicidad WERKS+LGORT, descripciones— pero no decide negocio).
- Si el probe futuro muestra que la estructura SAP permite resolver técnicamente parte del problema (p. ej. correspondencia 1:1 estable por centro), se documentará — **sin convertirla** en equivalencia automática.

## 4 · Qué se probará cuando exista acceso (P4/P5 acotados)

| Check | Límite |
|---|---|
| `T001L` EXISTS / SELECT_ALLOWED / KEY_COLUMNS / REQUIRED_FIELDS | metadata |
| Muestra LGORT/LGOBE/WERKS | ≤10 filas filtradas por un WERKS autorizado |
| Cardinalidad WERKS→LGORT (solo si acotada) | conteo pequeño justificado |

## 5 · Reglas respetadas

- Cero decisiones automáticas; cero escrituras; cero muestras (bloqueo).
- El item permanece en `SAP_OWNER_DECISIONS_REQUIRED.md` (SAP-0) sin modificar; aquí solo se actualiza su estado de evidencia: **pendiente técnica + pendiente decisión**.

# GA-GOV-02 · RECONSTRUCCIÓN DE FUENTE — R-186 (candidato)

Objetivo: recuperar la **redacción exacta y el contexto** del candidato R-186 desde la evidencia de R-184. Nada se normaliza ni reinterpreta aquí.

## 1 · Primera mención y fuente exacta

| Elemento | Valor |
|---|---|
| Primera mención | Tranche R-184 · `audit/ga-r184/GA_R184_CANONICAL_RECONCILIATION.md` §7 «Hallazgos hermanos registrados (NO implementados en esta tranche)» — commit de gobernanza **`304174d`** (2026-09-11) |
| Redacción exacta | «**R-186 (propuesto)** \| `GET /reports/kpis/production-index` (G-05) tiene la **expresión idéntica** (`service.py:601`, `date.today() - lot.start_date`) ⇒ 500 con lote con `start_date`. Misma clase que R-184. API-only (sin consumidor frontend hoy) \| `runtime-red.json` caso `prodindex35` = 500 \| **REGISTRADO — SEPARATE_OPEN** (por regla de alcance §4: «si aparece otro defecto KPI, registrar por separado; no ampliar R-184 automáticamente»)» |
| Otras fuentes (mismo commit o posteriores) | `GA_R184_CERTIFICATION.md` §Registros derivados (1) · `GA_R184_RED_EVIDENCE.md` §1 fila «Hermano registrado» · `GA_R184_IPE_DATE_SEMANTICS_SPEC.md` §4 · `GA_R184_TASKS.md` T11 · `GA_R184_BACKEND_EVIDENCE.md` §1 · `REMEDIATION_BACKLOG.md` bloque R-184 («REGISTROS») · `audit/ga-uat-06/GA_OWNER_UAT_R184_OBSERVATIONS.md` nota 1 (redacción «R-186 — candidato existente, fuera del alcance de esta UAT») |

## 2 · Comportamiento observado (captura original)

- Evidencia cruda: `audit/ga-r184/evidence/red/runtime-red.json`, caso exacto:
  `{"case": "prodindex35", "path": "/reports/kpis/production-index?lot_id=35", "status": 500, "body": "Internal Server Error"}`
- Contexto de captura: actor autoridad global con empresa 1 efectiva, ventana BU `broiler` ON, lote 35 (`GA6A-GREEN-NOBU-…`, `start_date` no nulo — todo alta fija `start_date`). Misma sesión en que se capturó el 500 de IPE (defecto R-184).
- Superficie afectada: `GET /api/v1/reports/kpis/production-index` (G-05 «Broiler Production Index»), permiso `reports:read`, `lot_id` por query.
- Causa de código (idéntica a R-184, línea hermana): `app/reports/service.py::get_kpi_production_index` — `age_days = (date.today() - lot.start_date).days if lot and lot.start_date else 30`. La columna `Lot.start_date` es `DateTime(timezone=True)` ⇒ `date − datetime` ⇒ `TypeError` ⇒ 500. **No fue tocada por el fix de R-184** (verificado en el diff de C2 `3f88f94`: 1 expresión + 1 import, solo IPE).

## 3 · Por qué se consideró separado de R-184

1. **Regla de alcance del encargo R-184 §4**: «*If another KPI defect is discovered: record separately. Do not broaden R-184 automatically.*» — instrucción explícita del propietario.
2. Endpoint distinto (G-05 vs G-06), expresión distinta (línea propia), aunque misma clase técnica.
3. El fix de R-184 se limitó a `get_kpi_ipe`; la línea de G-05 permaneció intacta por diseño.

## 4 · Por qué no fue implementado

Por la regla de alcance anterior + §5 del encargo GA-GOV-02 (frontera R-186: no corregir, no fusionar, no iniciar tranche).

## 5 · ¿R-186 fue asignado en el catálogo canónico?

- **NO como finding formal.** La etiqueta «(propuesto)/(candidato)» fue usada consistentemente; el backlog lo registró como «R-186 (candidato)» dentro del bloque R-184, sin entrada propia OPEN.
- **Comprobación de numeración** (2026-09-11): máximo ID canónico usado = **R-185**; **R-183 fue ABSORBIDO en R-182 sin entrada propia** (`GA_FE_06_A_R183_DEDUP.md`: «no hay entrada R-183 independiente en el backlog»). Ninguna otra mención de R-186 existe fuera de los artefactos R-184/GA-UAT-06. ⇒ **El número R-186 está libre y es el siguiente canónico**.

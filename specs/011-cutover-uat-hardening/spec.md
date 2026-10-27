# SPEC 011 — Cutover UAT Hardening (GA-CUTOVER-UAT-HARDENING-2026-10-27)

**Estado:** DRAFT→IMPL · **Fecha:** 2026-10-27 · **Baseline HEAD:** `1436c27` · **Rama:** `main`. Remediación sobre el UAT de Yolinel (Cargas Iniciales). Amendment de **SPEC 006** (cutover v2), **SPEC 009** (KeyUser) y **SPEC 010** (UX descarga). No reabre decisiones ratificadas; preserva R-184/R-186/R-187/OD-22. SAP READ-ONLY, 0 escrituras.

Entrada: `FUNCTIONAL_HAPPY_PATH_PASS / UAT_INCOMPLETE` — Yolinel recorrió el ciclo completo (plantilla→aplicar) en las 4 BU con `qa.admin`/`qa.approver`. El módulo NO está roto.

## 1. Hallazgos (reproducidos en HEAD, con causa raíz)

### CUTOVER-UX-01 — botones sin etiqueta · **P3 / NO_DEFECT_ON_HEAD**
Reproducción: en HEAD todos los botones (`downloadTemplate`, `uploadTemplate`, `submit`, `approve`, `reject`, `apply`) usan `t('cutover.*')` con claves existentes (es/en), y los tests `getByRole({name})` pasan ⇒ etiquetas presentes. El reporte de blanco corresponde a un bundle/caché previo a SPEC 010. **Sin fix de código**; se añade test de render de etiquetas (regresión) y verificación visual en UAT.

### CUTOVER-UX-02 — filename sin versión · **P2 · REAL**
`frontend/src/pages/cutover/CargasInicialesPage.tsx:263` hardcodea `_v2` en el nombre del archivo (hatchery v3 se descarga mal nombrado). El backend YA devuelve el nombre correcto en `Content-Disposition` (`templates.py` → `filename="cutover_template_<bu>_<version>.<ext>"`, de `TemplateContract.filename_stem`). **Fix:** el frontend usa el filename del header `Content-Disposition` (versión real del template); se elimina el `_v2` duplicado y el nombre sin versión de la descarga temprana. No se duplica la versión en el cliente (§6).

### CUTOVER-DATA-01 — `Meta.cutover_datetime` vacío · **P2 (presentación, NO integridad)**
Reproducción: con `batch_id`, Meta trae el corte (`'2026-10-01T08:00:00+00:00'`); en la descarga temprana (sin batch, feature SPEC 010) queda vacío porque el endpoint solo rellena desde el batch. **La autoridad del corte es el batch**: `apply` y `reconciliación` leen `batch.cutover_datetime` (service.py:212/236/506/510/706), NUNCA Meta. No hay pérdida de semántica. **Fix:** param opcional `cutover_datetime` en `GET /cutover-templates/{bu}` que **solo** rellena Meta (display); el frontend envía el corte elegido en la descarga temprana. Meta nunca es autoridad; subir una plantilla con Meta editada no cambia el corte del batch (el upload no toma el corte de Meta).

### CUTOVER-DOC-01 — `source_lot_code` poco claro · **P2**
`contracts.py:233` `meaning` no explica la relación con `egg_origin`. **Fix:** ampliar el `meaning` (internal ⇒ lote interno compatible de la misma empresa/generación; purchased ⇒ no exige lote interno, procedencia externa) y regenerar `audit/cutover-initial-balances/03..10`. `generation` (grandparent/breeder) y `egg_origin` (internal/purchased) se mantienen distintos (SPEC 009).

## 2. Scope / Out of scope
Dentro: `backend/app/cutover/{contracts,templates}.py`, `frontend/src/pages/cutover/CargasInicialesPage.tsx`, `frontend/src/services/cutover.service.ts`, i18n `cutover.*`, tests backend/frontend/E2E, docs regenerados. Fuera (§25): SAP real, R-187/OD-22, waves cerradas, rediseño de maestros, lógica RBAC/segregación (se REUTILIZA, no se reimplementa). Sin DB/migración.

## 3. UAT disposition (reutilización §16 + gaps)
- **UAT-02 (negativas):** cubierto por `test_cutover_v2_validation.py`, `test_cutover_v2_contracts.py`, `test_cutover_v2_keyuser_s01_red_{parse,db}.py` (obligatorios, N/A, tipos, referencias, duplicados, mortalidad breeder, egg_origin/generation, eggs_set>received, hatchery v2 rechazada, cabecera/Meta/archivo). Gap: matriz consolidada + confirmar casos de mensajes accionables.
- **UAT-03 (RBAC/segregación/tenant/BU):** `security/test_multitenant_isolation.py`, `test_segregation_r143`, `_exigir_segregacion` (service), aislamiento por empresa en `validation.py`, gate `require_permission` en routers. Gap: matriz positiva/negativa + confirmación 403 en API para cada capacidad y anti-IDOR por batch.
- **UAT-04 (apply+verify E2E 4 BU):** `e2e/proceso-p16-cutover-{grandparent,breeder,hatchery,broiler}.spec.ts` via `flujoPorBu` (crear→plantilla→subir→validar→enviar→aprobar→aplicar→reconciliación→primer evento post-corte→verificación; CUT-GL-02 rechazo mismo-día). Ejecutar las 4 BU (`--workers=1`).
- **UAT-05 (auditoría):** `audit_accion` en el servicio (create/apply/FAILED_APPLY), `test_audit_coverage.py`. Gap: mapear las acciones del ciclo.

## 4. Acceptance Criteria
- UX-01: botones con etiqueta visible (test de render). UX-02: filename refleja versión real (Excel+CSV) vía Content-Disposition. DATA-01: Meta refleja el corte cuando se indica; backend conserva autoridad; apply/reconciliación usan el corte del batch; manipular Meta no altera el corte. DOC-01: instrucciones de `source_lot_code` claras y consistentes con egg_origin/generation. UAT-02/03/04/05 según §23 del mandato.

## 5. Test strategy
Backend: targeted de los campos tocados + regresión completa `run_tests.sh` (pre/post, cabeza Alembic sin cambio). Frontend: `vitest` + `tsc -b` + `vite build`; tests de filename (Content-Disposition) y descarga temprana con corte. E2E: 4 BU `p16-cutover` `--workers=1` + negativas/RBAC donde haya gap. Mutación/sensibilidad tras commit de implementación. Evidencia en `audit/cutover-uat-hardening-2026-10-27/`.

## 6. Constitution Gate
SPEC suficiente PASS · alcance PASS · reglas de negocio (sin cambio; autoridad del corte=batch) PASS · API impact (param display-only) PASS · DB impact (ninguno) PASS · seguridad (reusa RBAC/tenant) PASS · multiempresa PASS · regresión identificada PASS · AC verificables PASS · plan de pruebas PASS. **AUTHORIZATION GATE: PASS.**

## 7. Brief DeepSeek (rutas autorizadas)
- `backend/app/cutover/contracts.py` (meaning source_lot_code), `backend/app/cutover/templates.py` (param `cutover_datetime` display-only), `backend/scripts/cutover_v2_docs.py` si aplica.
- `frontend/src/services/cutover.service.ts` (param cutover_datetime; exponer headers), `frontend/src/pages/cutover/CargasInicialesPage.tsx` (filename desde Content-Disposition; early download envía corte).
- tests: `backend/tests/test_cutover_v2_*.py` (ampliar), `frontend/src/__tests__/cutoverV2.test.tsx` (filename + early cutoff), `test-support/cutover.ts`/E2E si aplica.
Prohibido: lógica RBAC/segregación, DB/migraciones, contratos de otras BU, SAP.

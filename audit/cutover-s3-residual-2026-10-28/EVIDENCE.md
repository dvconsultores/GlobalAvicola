# GA-CUTOVER-S3-RESIDUAL-01 — Evidencia

**Fecha:** 2026-10-28 · **Rama:** `main` · **Baseline HEAD:** `d55e682` · **Spec:** `specs/012-cutover-s3-residual/spec.md` (amendment de SPEC 006/010/011). Entrada: `SESION 3 - REVISION PLANTILLAS - CICLO DE CARGA - 28-10-2026.pdf` (Yolinel, `QA Avícola Integral, C.A.`, `qa.admin`/`qa.approver`, 4 BU). SAP READ-ONLY, 0 escrituras; sin DB/migración; persistencia UTC intacta.

## 1. Hallazgos — reproducción y causa raíz (§14)

| ID | Reproducido | Causa raíz | Capa | Sev | Fix |
|---|---|---|---|---|---|
| **S3-01** botones `primary` en blanco | Sí (4 BU; `Descargar Plantilla Excel`, `Cargar Plantilla`, `Enviar a Aprobación`, `Aprobar`, `Aplicar`) | **Tailwind v4** (`@import 'tailwindcss';` sin `@config`/`@theme`) no carga la paleta `brand` de `tailwind.config.ts` ⇒ utilidades `bg-brand-500/600/700`, `ring-brand-400` **no se generan** (verificado: 0 en `dist/*.css`). La variante `primary` de `Button.tsx` es `bg-brand-500 text-white` ⇒ **texto blanco sobre fondo transparente = invisible**. Las variantes `outline`/`ghost`/`danger` sí se ven (por eso `Descargar CSV`/`Rechazar` muestran etiqueta). **Causa única compartida**, no 5 etiquetas faltantes (las claves i18n existen). | Frontend / design system (CSS) | **P1** | `@theme { --color-brand-50..950 }` en `index.css` (wiring v4). Un cambio corrige los 5 botones. |
| **S3-02** `Meta.cutover_datetime` +4h | Sí (4 BU) | Usuario elige 18:00 local (UTC−4); `templates.py:154` escribía `isoformat()` del **instante UTC** persistido (22:00Z) ⇒ Meta mostraba `...22:00:00+00:00`. **Instante correcto**; solo la **representación** estaba en UTC. | Backend / generador Excel (Meta) | **P1** (representación, NO integridad) | `corte.astimezone(America/Caracas).isoformat()` ⇒ `...18:00:00-04:00`. Persistencia UTC y autoridad del batch intactas. |

Traza temporal S3-02 (§4.3): `datetime-local` 18:00 (civil local) → `new Date().toISOString()` 22:00Z → API/Pydantic 22:00+00:00 → persistencia `DateTime(timezone=True)` 22:00+00:00 → **Meta ANTES** `2026-10-28T22:00:00+00:00` / **Meta AHORA** `2026-10-28T18:00:00-04:00` (mismo instante) → apply/reconciliación usan el instante del batch (sin cambio). Clasificación (§4.4): INSTANT absoluto en UTC (canónico) + representación en hora de negocio (opción C). Zona de negocio: **`America/Caracas` (UTC−4 fijo)**, reúso del marco UTC−4 vigente (R-75/R-80); no material.

## 2. Fix y archivos
- **S3-01:** `frontend/src/index.css` (+bloque `@theme` brand). `Button.tsx` NO se tocó (su variante ya era correcta).
- **S3-02:** `backend/app/cutover/templates.py` (import `ZoneInfo`, const `ZONA_NEGOCIO = ZoneInfo("America/Caracas")`, conversión de Meta con guarda naive→UTC; texto de hoja Instrucciones actualizado a `-04:00` por consistencia).
- **Tests:** `backend/tests/test_cutover_s3_timezone.py` (nuevo: 6 vectores horarios + estabilidad ante TZ del proceso), `test_cutover_uat_hardening_s011.py` (aserción Meta → hora de negocio), `test_cutover_v2_red.py` red_06 (compara instantes), `frontend/src/__tests__/cutoverV2.test.tsx` (+2: className primary `bg-brand-500`/`text-white`; `index.css` tiene `@theme`/`--color-brand-500`), `test-support/cutover-flow.ts` (E2E: `verificarFondoPrimary` — estilo computado no transparente/blanco, teal dominante).

## 3. Resultados de verificación
- **S3-01 build:** `dist/assets/*.css` ahora contiene `.bg-brand-500{background-color:var(--color-brand-500)}` + `bg-brand-600/700`, `ring-brand-400`, `border-brand-500`, `text-brand-700` (ANTES: 0). — `evidence/01_frontend_build_brand.log`.
- **Frontend:** `vitest` **580/580** (incl. guards S3-01), `tsc -b` PASS, `vite build` PASS — `evidence/02_frontend_*.log`.
- **Backend cutover targeted (18 archivos):** **150 passed · 0 failed** (incl. `test_cutover_s3_timezone` 7 + s011 + red_06) — `evidence/03_backend_cutover_suite.log`.
- **S3-02 vectores horarios:** mañana/tarde/≈medianoche/23:30 local(día UTC+1)/00:30/fin de mes/fin de año + estabilidad TZ proceso → todos PASS (instante preservado, offset `-04:00`).
- **E2E 4 BU** (`p16-cutover-*`, `--workers=1`, con verificación de fondo `primary` computado en navegador real): **4 passed (56.7s)** — grandparent/breeder/hatchery/broiler, ciclo completo + `verificarFondoPrimary` (no transparente/blanco, teal) en descarga temprana y aplicar — `evidence/05_e2e_cutover_4bu.log`.
- **Regresión backend completa (pre-mutación):** **1774 passed · 0 failed · 49 skipped** (head `f1a2b3c4d5e6`) — `evidence/06_backend_full_pre_mutation.log`.
- **Mutación/sensibilidad S3-02** (`templates.py`, tras IMPL SHA `fc949f1`): **2/2 DETECTADAS** — S1 (revertir a UTC) → 8 failed; S2 (zona `America/New_York`) → 1 failed (vector fin de año −05:00); restaurado 0 diff; suite 9/9 — `evidence/08_sensibilidad_s3-02.md`.
- **Regresión backend completa (post-mutación, árbol = IMPL SHA, 0 diff):** **1774 passed · 0 failed · 49 skipped** (head `f1a2b3c4d5e6`) — `evidence/07_backend_full_post_mutation.log`.

## 4. Seguridad / integridad (§9)
La autoridad del corte sigue en el batch; el parser **ignora** `Meta.cutover_datetime` (SPEC 011, `test_data01_parser_ignora_cutover_de_meta` verde). Editar Meta (empresa/BU/corte) no altera el corte autorizado ni el batch efectivo. Persistencia UTC sin cambio.

## 5. Fuera de alcance / deuda observada (§20)
- `Button.tsx` variante `secondary`: clase malformada `hover:bg-slate-200:bg-slate-700` (hover cosmético) — no tocado.
- `CargasInicialesPage.tsx:330,445`: `new Date(...).toLocaleString()` del navegador (listado) — fuera de los 2 residuales.
- Tailwind v4 ignora el resto de `tailwind.config.ts` (borderRadius/fontFamily legacy); el fix solo cablea `brand` (mínimo necesario). Documentado; no se amplía para no alterar el layout vigente.

## 6. Estado
```
REAL_SAP_WRITES=0 · DB_CHANGES=0 · MIGRATION=none · PERSISTENCIA=UTC(intacta)
S3-01 FIXED (P1) PASS · S3-02 FIXED (P1, representación) PASS
GATES: frontend 580/580 · cutover 150/150 · pre-mut 1774/0/49 · E2E 4 BU 4/4 (visual) ·
       sensibilidad S3-02 2/2 DETECTADAS · post-mut 1774/0/49 · P0/P1 abiertos=0 · árbol limpio
OBSERVACIONES NO BLOQUEANTES (P3, preexistentes, ajenas): Button.secondary clase malformada ·
       toLocaleString del navegador en listado cutover · tailwind.config.ts legacy ignorado por v4
FINAL_STATUS=CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS
```

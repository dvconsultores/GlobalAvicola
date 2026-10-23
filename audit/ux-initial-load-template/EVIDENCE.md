# GA-UX-INITIAL-LOAD-TEMPLATE — Evidencia (SPEC 010)

**Fecha:** 2026-10-24 · **Rama:** `main` · **Spec:** `specs/010-ux-initial-load-template/spec.md` · **IMPL base HEAD:** `d7718ec`.

Mejora UX de «Cargas Iniciales»: hacer descubrible la descarga de plantilla. **Solo frontend** (sin backend/API/DB/migración). DeepSeek escribió el código/tests; Claude diseñó, autorizó, auditó y verificó.

## 1. Cambio

- **Descarga temprana de plantilla** como acción visible tras elegir unidad + corte, **sin crear la carga** (reutiliza `GET /cutover-templates/{bu}` con `batch_id` opcional). Deshabilitada sin corte, con hint del porqué. Etiquetas nuevas (`downloadTemplatePrimary`/`downloadTemplatePrimaryCsv`), distintas de las post-carga para no colisionar con test/E2E.
- Ayuda **1-2-3** + «¿No sabes cómo empezar?», panel **«Ver instrucciones»** (expandible, `aria-expanded`, `data-testid=cutover-instructions`), toast de éxito/error, **empty state** accionable.
- Se conserva íntegro el flujo existente (crear carga → descarga post-carga → subir → validar → preview → aprobar → aplicar → reconciliar) y todos los `data-testid`/labels previos.

## 2. Archivos (en alcance, §27)

`frontend/src/pages/cutover/CargasInicialesPage.tsx`, `frontend/public/locales/es/translation.json`, `.../en/translation.json`, `frontend/src/__tests__/cutoverV2.test.tsx`, `test-support/cutover-flow.ts`. **Backend tocado: 0.**

## 3. Auditoría §28

`backend_py=0`; sin cambios fuera de alcance; reutiliza endpoint y aislamiento (`cutover:create`, `effective_company_id`, BU limitada a las del usuario); a11y (aria-hidden/aria-expanded, textos descriptivos, disabled explicado); i18n es+en completas (113 claves `cutover` c/u). **Verdict: PASS.**

## 4. Verificación

- **Frontend:** `vitest` **577/577** (incluye nuevo `RC-010` de descarga temprana) — `evidence/01_frontend_vitest.log`. `tsc -b` rc=0 — `02_frontend_tsc.log`. `vite build` rc=0 — `03_frontend_build.log`.
- **E2E (Playwright, `--workers=1`):** breeder + hatchery, con paso de descarga **temprana** antes de crear la carga + flujo completo — `evidence/04_e2e_cutover.log`. Resultado: **2 passed** (descarga temprana + crear→subir→validar→preview→aprobar→aplicar→reconciliar).
- **QA en runtime UAT (`https://avicola.globaldv.net`, Playwright, usuario `qa.admin`):** `/cutover` **PASS** — «Descargar plantilla» visible y **deshabilitado sin corte**, **habilitado con corte**; intro y ayuda «¿No sabes cómo empezar?» visibles; «Ver instrucciones» despliega el panel (`cutover-instructions`). Bundle desplegado `index-hd1Y5Bm5.js` con los marcadores SPEC 010; `/locales/*/translation.json` sirve las claves nuevas. Capturas: `evidence/uat_cutover_inicial.png`, `evidence/uat_cutover_corte_instrucciones.png`.

## 5. Acceptance Criteria

AC-01..AC-17: cubiertos (CTA temprano visible/habilitado/deshabilitado con hint; descarga de la unidad/empresa activa; instrucciones accesibles; stepper con `aria-current`; responsive; histórico intacto; validación/preview/aprobación/aplicar/reconciliación sin cambios; permisos/multiempresa intactos; errores entendibles). Cobertura: `RC-010` (componente) + E2E (flujo) + auditoría (seguridad/alcance).

```
REAL_SAP_CALLS=0 · REAL_SAP_WRITES=0 · BACKEND_CHANGES=0 · DB_CHANGES=0
FRONTEND_VITEST=577/577 · TSC=PASS · BUILD=PASS
E2E=breeder+hatchery 2/2 (incl. descarga temprana)
UAT_RUNTIME=PASS (qa.admin, smoke /cutover)
FINAL_STATUS=CERTIFIED_GA_UX_INITIAL_LOAD_TEMPLATE
```

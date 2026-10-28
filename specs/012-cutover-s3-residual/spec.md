# SPEC 012 — Cutover S3 Residual (GA-CUTOVER-S3-RESIDUAL-01)

**Estado:** DRAFT→IMPL · **Fecha:** 2026-10-28 · **Baseline HEAD:** `d55e682` · **Rama:** `main`. Delta/amendment residual sobre **SPEC 006** (cutover v2), **SPEC 010** (UX descarga) y **SPEC 011** (UAT hardening). No reabre decisiones ratificadas; preserva autoridad del corte=batch, persistencia UTC (`R-80`, `docs/01-legacy-audit.md`, `docs/05-migration-plan.md`), semántica UNKNOWN/0/N/A, versiones de plantilla, `source_lot_code`, filename/versionado y RBAC/segregación.

Entrada: `SESION 3 - REVISION PLANTILLAS - CICLO DE CARGA - 28-10-2026.pdf` (Yolinel, empresa `QA Avícola Integral, C.A.`, usuarios `qa.admin`/`qa.approver`, 4 BU). Dos residuales demostrados tras los cambios de SESIÓN 2.

## 1. Hallazgos (reproducidos en HEAD, con causa raíz)

### GA-CUTOVER-S3-01 — botones `primary` sin etiqueta visible · **P1 · REAL**
Controles en blanco (4 BU): `Descargar Plantilla Excel` (CTA temprano), `Cargar Plantilla`, `Enviar a Aprobación`, `Aprobar Plantilla`, `Aplicar Plantilla`. **Causa raíz única y compartida** (NO son 5 etiquetas faltantes — las claves i18n existen y renderizan como children):
- El proyecto usa **Tailwind v4** (`tailwindcss@^4.3.1`, `@tailwindcss/vite`); `frontend/src/index.css` solo tiene `@import 'tailwindcss';` **sin `@config` ni `@theme`**. En v4 la paleta `brand` definida en `tailwind.config.ts` (legacy `theme.extend.colors.brand`) **no se carga**, por lo que las utilidades `bg-brand-500/600/700` y `ring-brand-400` **no se generan** (verificado: 0 ocurrencias en `dist/assets/*.css`).
- La variante `primary` de `components/ui/Button.tsx` es `bg-brand-500 text-white …`. Sin `bg-brand-*`, el botón queda **texto blanco sobre fondo transparente** = etiqueta invisible. Las variantes `outline`/`ghost`/`secondary` (texto `slate`) y `danger` (`bg-red-600`, color estándar) sí se ven → por eso `Descargar CSV` y `Rechazar` muestran etiqueta y los `primary` no. El resto de la UI se ve con marca porque usa clases `.gradient-brand-*` (hex literal en `index.css`), no utilidades.
- **Fix:** cablear la paleta `brand` en Tailwind v4 (preferente: bloque `@theme { --color-brand-50..950 }` en `index.css`; alternativa: `@config "../tailwind.config.ts";`) para que `bg-brand-*`/`ring-brand-*` se generen. Un solo cambio en el design system corrige los cinco botones y cualquier `primary` del producto. No se parchean botones individuales.

### GA-CUTOVER-S3-02 — `Meta.cutover_datetime` +4h · **P1 · REAL (representación, NO integridad)**
Usuario elige `2026-10-28 18:00` (06:00 p.m., hora local Venezuela UTC−4); Meta muestra `2026-10-28T22:00:00+00:00` (+4h). Traza extremo a extremo:

| Etapa | Valor | Zona/offset | Transformación |
|---|---|---|---|
| input `datetime-local` | `2026-10-28T18:00` | civil local (sin tz) | wall-clock del operador |
| frontend serialización | `2026-10-28T22:00:00.000Z` | UTC | `new Date(local).toISOString()` |
| API / Pydantic | `2026-10-28T22:00:00+00:00` | UTC | parse aware |
| persistencia (`CutoverBatch.cutover_datetime`) | `2026-10-28T22:00:00+00:00` | UTC | `DateTime(timezone=True)` |
| Meta Excel (`templates.py:154`) | `2026-10-28T22:00:00+00:00` | UTC | `isoformat()` del instante UTC |
| apply / reconciliation | `2026-10-28T22:00:00+00:00` → `.date()` | UTC | autoridad batch |

**El instante es correcto** (22:00Z == 18:00 UTC−4). El defecto es solo la **representación** de Meta. Clasificación (§4.4): `cutover_datetime` es un **INSTANT absoluto** persistido en UTC (canónico) **+ representación en hora de negocio** para el usuario (opción C). **Fix:** en `templates.py` representar `Meta.cutover_datetime` en la **zona de negocio** con offset explícito (`corte.astimezone(ZONA_NEGOCIO).isoformat()` ⇒ `2026-10-28T18:00:00-04:00`). Persistencia UTC **intacta**; apply/reconciliación siguen leyendo el instante del batch. Prohibido `hora-4` o cualquier offset fijo manual: la conversión es por zona horaria. Alcance de Meta: **solo** `cutover_datetime` (no se tocan `generated_at` ni otros).

## 2. Zona de negocio (§4.6)
Zona autorizada: **`America/Caracas` (UTC−04:00, Venezuela, offset fijo sin DST desde 2016)**. No se inventa una política nueva: el producto ya razona universalmente en UTC−4 (hallazgos `R-75`/`R-80`, auditorías `ga-claude-final-audit`), y la persistencia canónica es UTC (`R-80`, `docs/01-legacy-audit.md`, `docs/05-migration-plan.md`). Se materializa como **una** constante central en backend (p. ej. `ZONA_NEGOCIO = ZoneInfo("America/Caracas")`), reutilizable; no se crea una segunda política. Si el Owner exigiera otra zona, es un cambio de configuración trivial. **No se emite `MATERIAL_DECISION_REQUIRED`**: la zona es inequívoca para Global Avícola y el mandato la enmarca como «hora local Venezuela».

## 3. Scope / Out of scope
Dentro: `frontend/src/index.css` (wiring `brand` v4), opcional `tailwind.config.ts`; `backend/app/cutover/templates.py` (representación Meta `cutover_datetime`) + constante de zona; tests frontend (botones visibles + CSS con utilidades `brand`), backend (Meta en hora de negocio + round-trip + vectores horarios), E2E 4 BU; evidencia. Fuera (§20): persistencia/UTC, autoridad del corte, apply/reconciliación, RBAC, versiones/`source_lot_code`/filename, CSV Meta (no existe), SAP, rediseño. Deuda no relacionada observada (documentar, no tocar): `Button.tsx` variante `secondary` tiene clase malformada `hover:bg-slate-200:bg-slate-700` (hover cosmético); `CargasInicialesPage.tsx:330,445` usa `new Date(...).toLocaleString()` del navegador (fuera de alcance de estos residuales).

## 4. Acceptance Criteria
- **S3-01:** los 5 botones muestran etiqueta visible con contraste (fondo `brand` presente), accessible name correcto, visibles en enabled/disabled/loading; `dist` contiene utilidades `bg-brand-500` (y las que usa `primary`); acciones siguen funcionando; 4 BU.
- **S3-02:** Meta refleja la hora de corte seleccionada por el usuario en zona de negocio con offset explícito (`-04:00`); mismo instante que el batch; round-trip estable (`selected == meta == applied` a nivel de instante); apply/reconciliación usan el mismo corte; sin `-4h` hardcodeado; estable ante cambio de TZ de host/navegador; 4 BU; regresión verde.

## 5. Test strategy
Frontend: `vitest` (los 5 botones por rol+nombre; aserción de que `Button` `primary` usa `bg-brand-500` y no queda invisible) + test de que el CSS construido/configuración genera utilidades `brand` + `tsc -b` + `vite build`. Backend: test de Meta en hora de negocio (18:00-04:00), round-trip (parse de Meta == instante batch), **vectores horarios** (mañana, tarde, ~medianoche local, 23:30 local=día UTC siguiente, 00:30, fin de mes, fin de año) y estabilidad ante `TZ` del proceso distinto; integridad (editar Meta no cambia el corte autorizado — reusa SPEC 011). E2E 4 BU: ciclo completo con verificación de etiquetas visibles + Meta correcta. Mutación/sensibilidad del fix backend tras commit de implementación. Evidencia en `audit/cutover-s3-residual-2026-10-28/`.

## 6. Constitution Gate
SPEC suficiente PASS · alcance acotado a 2 residuales PASS · reglas de negocio (persistencia UTC intacta, autoridad=batch) PASS · API impact (ninguno nuevo; Meta display) PASS · DB impact (ninguno) PASS · seguridad (reusa RBAC/integridad SPEC 011) PASS · multiempresa/4 BU PASS · regresión identificada (cutover/template/meta/upload/validation/submit/approve/reject/apply/reconciliation/RBAC/tenant) PASS · AC verificables PASS · plan de pruebas (incl. vectores horarios) PASS. **AUTHORIZATION GATE: PASS** (ambos son bugs/regresiones de semántica ya definida; §15).

## 7. Brief DeepSeek (rutas autorizadas)
- `frontend/src/index.css`: cablear paleta `brand` en Tailwind v4 (`@theme` con `--color-brand-50..950` = valores de `tailwind.config.ts`, o `@config "../tailwind.config.ts";`). Objetivo: `bg-brand-500/600/700` y `ring-brand-400` presentes en el build; botones `primary` con fondo visible.
- `backend/app/cutover/templates.py`: representar `Meta.cutover_datetime` con `.astimezone(ZONA_NEGOCIO)` (constante central `ZoneInfo("America/Caracas")`), offset explícito; persistencia y autoridad intactas.
- tests: `frontend/src/__tests__/cutoverV2.test.tsx` (+ test de design system `brand`), `backend/tests/test_cutover_*` (Meta hora de negocio + round-trip + vectores horarios), E2E `e2e/proceso-p16-cutover-*.spec.ts` (etiquetas visibles + Meta).
Prohibido: cambiar persistencia/UTC, autoridad del corte, offset fijo `-4h`, RBAC, versiones/filename/`source_lot_code`, SAP, rediseño.

# SPEC 010 — UX Cargas Iniciales: descubribilidad de la descarga de plantilla

**Task ID:** GA-UX-INITIAL-LOAD-TEMPLATE · **Estado:** DRAFT (fase de gobierno §31; sin implementación) · **Fecha:** 2026-10-23 · **Rama:** `main` (HEAD `9bdef93`).

> Mejora **UX/UI** independiente. No cambia reglas de negocio, contratos, API, DB, SAP, RLS ni el flujo funcional del cutover. Baseline a preservar: `R-184`, `R-186`, `R-187`, `OD-22`, Owner UAT 6/6, SPEC 006/009.

---

## 1. Problem Statement

En **Cargas Iniciales** (`/cutover`) el usuario selecciona unidad de negocio y fecha/hora de corte, pero **no descubre cómo obtener la plantilla Excel**. Causa raíz (reproducida en el código): la acción **«Descargar plantilla» solo se renderiza DESPUÉS de pulsar «Crear carga»** — está dentro del bloque `{batch && …}` y además gateada por `canValidate && status∈{draft,validating,validated}` (`CargasInicialesPage.tsx:388-401`). Al entrar, la única acción visible tras elegir unidad/corte es **«Crear carga»**, no «Descargar plantilla». El usuario no sabe que debe crear la carga primero, ni cuál es el siguiente paso.

## 2. Hallazgo de implementación (§6: A/B/C/D/E)

- **A (generación dinámica): SÍ.** La plantilla se genera al vuelo (`backend/app/cutover/templates.py::construir_plantilla_xlsx` / `catalogos`).
- **B (endpoint existente): SÍ.** `GET /api/v1/cutover-templates/{business_unit}?format=xlsx|csv&batch_id=` (gate `require_permission("cutover","create")`). **`batch_id` es OPCIONAL**: sin él, genera la plantilla de la **empresa efectiva + BU** (la empresa la fija `effective_company_id`, la BU el path). El cliente `cutoverService.template(bu, {format, batchId?})` ya soporta omitir `batchId`.
- **D (la lógica del paso «2 Plantilla» existe pero NO está expuesta correctamente): SÍ — esta es la causa.**
- **C/E:** no aplica (no es estática ni está incompleta).

**Conclusión:** la funcionalidad existe; es un problema de **exposición/descubribilidad en el frontend**. **No se requiere cambio de backend, API, DB ni migración.** No duplicar funcionalidad.

## 3. User Story (§21)

> Como usuario autorizado de Global Avícola, quiero seleccionar mi unidad de negocio y fecha de corte y encontrar inmediatamente una acción visible para **descargar la plantilla correspondiente**, para completar la información y continuar al paso de carga sin conocimiento previo del sistema.

## 4. Scope

- **Dentro:** `frontend/src/pages/cutover/CargasInicialesPage.tsx` (presentación, estados, CTAs, stepper, empty state, ayuda, microcopy); textos en `frontend/public/locales/es/translation.json` y `.../en/translation.json` (claves `cutover.*`); pruebas de frontend (`frontend/src/__tests__/cutoverV2.test.tsx`) y, si procede, el soporte/spec E2E (`test-support/cutover-flow.ts`, `e2e/proceso-p16-cutover-*.spec.ts`).
- **Fuera (§18):** backend, endpoints, contratos, parser/validación/apply, DB/migraciones, SAP, autenticación, roles/RLS, multiempresa (lógica), reconciliación/aprobación/aplicación, reglas de negocio. `genetic_line_code`/`breed_name` siguen siendo **maestros internos de Global Avícola** (SPEC 009), no SAP — no se tocan.

## 5. Diseño propuesto (decisiones de arquitectura)

Cambios **aditivos**, sin alterar el flujo existente:

1. **Descarga de plantilla como acción primaria temprana.** En la tarjeta «Nueva carga», tras elegir unidad+corte, exponer **«Descargar plantilla»** (primaria) + «Descargar CSV» (secundaria), habilitadas cuando **unidad y corte son válidos**, llamando a `cutoverService.template(businessUnit, { format })` **sin `batchId`** (no requiere crear la carga). Si falta unidad o corte, deshabilitadas con ayuda del porqué.
2. **Mantener** la descarga existente dentro de la carga (post-`Crear carga`) para no romper el flujo ni el E2E. La nueva descarga temprana es adicional.
3. **Creación de la carga explícita.** «Crear carga» sigue siendo el puente hacia «Subir archivo» (no se auto-crea el batch al descargar: evita cargas huérfanas). El microcopy y el stepper hacen evidente la secuencia.
4. **Ayuda 1-2-3** visible bajo los campos: (1) elegir unidad y corte · (2) Descargar plantilla · (3) completar y subir en «Subir archivo».
5. **«Ver instrucciones»** (panel expandible/drawer, no modal bloqueante): ayuda operativa breve (7-8 pasos), sin duplicar el manual completo.
6. **Confirmación de descarga** no intrusiva (toast) + hint del siguiente paso.
7. **Empty state** más accionable: «Aún no has iniciado una carga. Comienza descargando la plantilla.» (solo cuando no hay carga en curso).
8. **Stepper**: estado actual/completado/pendiente/bloqueado con icono+label+estilo (no solo color), `aria-current` (ya presente), navegable por teclado.
9. **Histórico «Cargas de la empresa»**: solo mejoras menores de legibilidad/accesibilidad; sin quitar funcionalidad.

## 6. UI States y transiciones

| Estado | Condición | «Descargar plantilla» |
|---|---|---|
| Inicial | sin unidad o sin corte | **deshabilitado** + ayuda «Selecciona unidad y corte para generar la plantilla» |
| Listo | unidad y corte válidos | **habilitado** (primaria) |
| Descargando | petición en curso | spinner/disabled transitorio |
| Éxito | 200 + blob | toast «Plantilla descargada correctamente» + hint «Completa el archivo y súbelo en Subir archivo» |
| Error | fallo de red/permiso | toast accionable «No fue posible generar la plantilla. Intenta nuevamente» (o causa funcional del backend) |

El stepper refleja el paso según `pasoActual(batch)` (sin cambios de lógica de estado).

## 7. Error handling

Sin mensajes técnicos crudos. Reusar `getErrorMessage`/toast. Mapear a textos i18n accionables. Si el backend devuelve causa funcional conocida (403 permiso, 404 batch), mostrar texto apropiado.

## 8. Permisos, multiempresa y seguridad

- La descarga exige `cutover:create` (gate del endpoint, sin cambios). El `<select>` de unidad ya se limita a `effective_business_units` del usuario (`unidadesDelUsuario`).
- Aislamiento multiempresa: el endpoint usa `effective_company_id`; la plantilla es de la empresa activa. **No** se añade selección de empresa ni se expone ruta interna. Sin path traversal / filename injection (el nombre lo fija el cliente con `${bu}_v2|v3`; la BU es un enum validado). Pruebas negativas: usuario sin permiso, unidad no autorizada, otra empresa.

## 9. Impacto API / Data / Regresión

- **API:** ninguno (se reutiliza `GET /cutover-templates/{bu}`). **DB:** ninguno. **Migración:** ninguna.
- **Superficie de regresión:** el componente `CargasInicialesPage.tsx`, i18n `cutover.*`, pruebas de frontend (`cutoverV2.test.tsx`, `r061.cutoverFlow.test.tsx`) y el E2E `p16-cutover-*` (que descarga tras «Crear carga» vía `flujoPorBu`). **Compatibilidad obligatoria:** conservar los textos/`data-testid` de la descarga post-carga y el label «Descargar plantilla Excel/CSV» que el E2E matchea, o actualizar el E2E de forma aditiva.

## 10. Accesibilidad y responsive

- `label` real en inputs (ya existe), focus visible, navegación por teclado, contraste, estados `disabled` explicados, `aria-current` en stepper, botones con texto descriptivo, iconos con texto, feedback accesible de descarga/error.
- Responsive 360/390/desktop: campos apilados, CTA primaria visible, stepper sin romper layout (wrap/scroll controlado), sin overflow horizontal.

## 11. Acceptance Criteria (§22)

AC-01 sin unidad/corte, el primer paso (seleccionarlos) es visualmente comprensible. · AC-02 con unidad+corte válidos, «Descargar plantilla» aparece/habilita claramente. · AC-03 al pulsarla, se recibe la plantilla de la unidad seleccionada. · AC-04 la plantilla corresponde a la empresa activa y unidad. · AC-05 no se puede descargar plantilla de otra empresa. · AC-06 tras descargar, se indica completar y continuar en «Subir archivo». · AC-07 instrucciones breves accesibles sin salir del flujo. · AC-08 stepper muestra actual/completado/pendiente. · AC-09 desktop OK. · AC-10 mobile OK. · AC-11 no se rompen cargas históricas. · AC-12 no cambia validación/preview/aprobación/aplicar/reconciliación. · AC-13 permisos y aislamiento multiempresa intactos. · AC-14 errores de descarga con mensaje entendible. · AC-15 sin HTTP 500 del nuevo flujo. · AC-16 sin errores de consola relevantes. · AC-17 sin regresión en las 4 unidades.

## 12. Test Strategy (§23/§24)

- **Unit/componente (vitest+jsdom):** estados del CTA (deshabilitado sin unidad/corte; habilitado con ambos), llamada a `template` sin `batchId`, toast de éxito/error, empty state, panel de instrucciones, stepper (`aria-current`), por las 4 unidades. Pruebas negativas de permiso (sin `cutover:create` → sin CTA de descarga).
- **E2E (Playwright):** flujo `unidad+corte → Descargar plantilla (temprana) → crear carga → subir → validación → preview`; conservar verde `flujoPorBu` (descarga post-carga). Responsive 360/390/1280.
- **Regresión:** `npx vitest run`, `npx tsc -b`, `npx vite build`; E2E `p16-cutover-{grandparent,breeder,hatchery,broiler}` con `--workers=1` (carrera de siembra de fases conocida del soporte E2E).
- `NO E2E = NO PROCESS CERTIFIED`.

## 13. Traceability (§26)

| Requirement | AC | Componente/API | Test | Status |
|---|---|---|---|---|
| Descarga temprana visible | AC-02, AC-03 | `CargasInicialesPage.tsx` + `cutoverService.template` | vitest CTA + E2E | DRAFT |
| Empresa/unidad correcta y aislada | AC-04, AC-05, AC-13 | endpoint `cutover-templates` (sin cambio) | vitest negativo + E2E seguridad | DRAFT |
| Siguiente paso evidente | AC-01, AC-06 | microcopy + stepper + empty state | vitest | DRAFT |
| Instrucciones accesibles | AC-07 | panel «Ver instrucciones» | vitest a11y | DRAFT |
| Stepper de estado | AC-08 | `Stepper` | vitest `aria-current` | DRAFT |
| Responsive/desktop/mobile | AC-09, AC-10 | layout | E2E responsive | DRAFT |
| No regresión flujo/histórico | AC-11, AC-12, AC-17 | página + servicio | regresión + E2E | DRAFT |
| Errores entendibles | AC-14, AC-15, AC-16 | toast/i18n | vitest error | DRAFT |

## 14. Rollback

Cambio aislado en un componente + i18n. Rollback = revertir el commit del frontend; sin migraciones ni estado persistente que deshacer.

## 15. Constitution Gate (§25)

| Ítem | Veredicto |
|---|---|
| SPEC suficiente | **PASS** |
| Alcance definido (frontend-only) | **PASS** |
| Reglas de negocio identificadas (sin cambio) | **PASS** |
| Impacto API identificado (ninguno) | **PASS** |
| Impacto DB identificado (ninguno) | **PASS** |
| Seguridad evaluada (reusa aislamiento/gate) | **PASS** |
| Multiempresa evaluada | **PASS** |
| Riesgo de regresión identificado (página/i18n/tests/E2E) | **PASS** |
| Criterios de aceptación verificables | **PASS** |
| Plan de pruebas definido | **PASS** |

**Resultado: READY_FOR_IMPLEMENTATION** (sin FAIL crítico).

## 16. Brief para DeepSeek (§27) — PROPUESTA (no ejecutar hasta autorización)

- **Objetivo:** mejorar descubribilidad de la descarga de plantilla en Cargas Iniciales, aditivo, sin cambiar flujo/reglas.
- **Archivos AUTORIZADOS:** `frontend/src/pages/cutover/CargasInicialesPage.tsx`; `frontend/public/locales/es/translation.json` y `frontend/public/locales/en/translation.json` (solo rama `cutover.*`, añadir claves nuevas); `frontend/src/__tests__/cutoverV2.test.tsx` (ampliar). Si se toca E2E: `test-support/cutover-flow.ts` (aditivo, conservar el paso actual).
- **Archivos PROHIBIDOS:** todo `backend/**`, `*.py`, migraciones, contratos, `cutover.service.ts` (salvo que la auditoría lo exija; el cliente ya soporta `batchId` opcional), otros componentes.
- **Contratos que NO cambian:** firma de `cutoverService.template`; `data-testid` existentes; labels que el E2E matchea («Descargar plantilla Excel/CSV»); flujo crear→subir→validar→preview→aprobar→aplicar→reconciliar.
- **Cambios exactos:** (1) CTA primaria «Descargar plantilla» + CSV en la tarjeta «Nueva carga», habilitadas con unidad+corte válidos, llamando a `template(bu,{format})` sin `batchId`; (2) ayuda 1-2-3 + texto introductorio; (3) «Ver instrucciones» (panel expandible); (4) toast de éxito + hint siguiente paso; (5) empty state accionable; (6) stepper con estado/`aria-current`/teclado; (7) claves i18n nuevas (es/en). Conservar la descarga post-carga.
- **Pruebas obligatorias:** vitest de los estados del CTA y permisos; `tsc -b` y `vite build` verdes; E2E `p16-cutover-*` verde con `--workers=1`.
- **Definición de done:** AC-01..AC-17 verificables; sin regresión; i18n es/en completas; sin overflow horizontal; worktree limpio.

## 17. Estado final de la fase

**READY_FOR_IMPLEMENTATION** — pendiente de autorización del Owner para pasar a la fase de implementación (brief a DeepSeek → tests → auditoría → convergencia → certificación).

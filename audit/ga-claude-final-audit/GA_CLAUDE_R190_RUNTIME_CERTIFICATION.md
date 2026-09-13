# GA-CLAUDE · R-190 — CERTIFICACIÓN (ubicación del evento en `location_events`)

Fecha: 2026-09-14 · Hallazgo **R-190** (P1 · bloquea P-01/P-03 · BR-08) · Paquete `specs/R-190/` · Clarificaciones C-01…C-12 (sólo C-03 opcional del propietario; alternativas A por defecto) · Commits: C1 `a79fe0c` · C2 `d1c16a7` · C2s `801d18c`.

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | `evidence/red/vitest-r190.log` — **26F/2P**: helper inexistente (17 unit) + 9 jsdom (payload sin `house_id` en distribución/traslado/salida/recolección/despacho/inspecciones; sin bloqueo cliente; i18n ausente); controles verdes (lote con galpón; inspección con granja). **Control BE** `evidence/red/backend-r190-control.log` — BR-08 **4/4** verde (400×3 sin ubicación; 201 con ubicación) |
| **C2 · Implementación** | ✅ | `evidence/green/r190-green-final.log` — **32/32** (R-190 17+11 + F-01e 4); `tsc` 0; FE completa **360/360**; `npm run build` OK · commit `d1c16a7` |
| **C2s · Sensibilidad** | ✅ S1·S2·S3·S4 | **S1** (sin fallback a fila en distribución): 2F · **S2** (selector sin escritura): 9F · **S3** (sin guarda cliente): 2F · **S4** (sin derivación de granja por catálogo): 2F — `evidence/sensibilidad/`; mutaciones revertidas |
| **C3 · Runtime** | ⏸ **pendiente** | E2E-R190-01…08 (nube) + retry R-189 7/7: requieren ventana de deploy + credenciales runtime (misma clase que **G-06**); runner listo (`scripts_e2e_f01_retry.mjs` extendido) |

## 2 · Implementación

- `operationPayload.ts::resolverUbicacionDelEvento` — fuente única de verdad (pura, con tabla de test propio): galpón del lote manda; si no, fila destino (recepción/distribución), origen→destino (traslado), selector «Galpón del evento» (salida/recolección/despacho/inspección de transporte), fila inspeccionada (inspección de granja); granja: lote → granja elegida → catálogo del galpón (C-08). Sin fuente ⇒ ausencia (no se inventa). Frontera incubadora intacta (`R-194`).
- `OperationFormPage.tsx` — `onSubmit` unificado; selector «Galpón del evento» ×4 (preseleccionado/bloqueado si el lote ya declara galpón, C-05); guardas cliente con mensajes `operations.eventHouseRequired`/`operations.farmRequired` (C-03/C-07) — **sin petición** cuando faltan.
- i18n ES/EN (`eventHouse`, `eventHouseRequired`, `farmRequired`).
- Backend **sin cambio**: BR-08 intacta (control 4/4).

## 3 · AC

| AC | Estado |
|---|---|
| AC-R190-01 (distribución sin galpón de lote ⇒ `house_id` de fila) | ✅ jsdom AC-01 · S1 |
| AC-R190-02 (salida ⇒ selector) | ✅ jsdom AC-02 · S2 |
| AC-R190-03 (recolección ⇒ selector) | ✅ jsdom AC-03 · S2 |
| AC-R190-04a/b (inspección de granja: bloqueo sin fuente; con granja ⇒ completo) | ✅ jsdom 04a · S3 / 04b |
| AC-R190-05 (lote con galpón manda — control) | ✅ jsdom 05 + F-01e 4/4 |
| AC-R190-07 (traslado ⇒ origen) | ✅ jsdom 07 · S1 |
| AC-R190-08a/b (despacho/inspección transporte ⇒ selector) | ✅ jsdom 08a/08b · S2 |
| AC-R190-09 (sin galpón elegido ⇒ sin POST + mensaje) | ✅ jsdom 09 · S3 |
| AC-R190-10 (granja derivada del catálogo) | ✅ unit tabla · S4 |
| AC-R190-11 (i18n ES/EN) | ✅ unit i18n |
| AC-R190-06 (BR-08 por API — control) | ✅ backend 4/4 |
| AC-R190-08 (sin migración/endpoint/permiso) | ✅ diff FE-only (helper+página+i18n+tests) |

## 4 · Veredicto

**R-190 = `CLOSED_TECHNICALLY`** — C1/C2/C2s completos con paridad FE (F-01e intacto) y frontera BE demostrada; **C3 runtime pendiente** (ventana de deploy + credenciales). `P-01`/`P-02`/`P-03`/`P-04` recuperan el eslabón de ubicación en cuanto se ejecute la pasada E2E.

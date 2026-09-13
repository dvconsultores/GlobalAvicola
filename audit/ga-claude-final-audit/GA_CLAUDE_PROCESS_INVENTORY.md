# GA-CLAUDE · INVENTARIO DE PROCESOS DE NEGOCIO (§26 · §53)

Auditoría independiente Claude · 2026-09-13 · repo `dvconsultores/GlobalAvicola` · rama `main` · HEAD `c0b4afc` · runtime `https://avicola.globaldv.net` (bundle `index-DDCcWL76.js` == build local de HEAD) · producto intocado (diff 0).

Documentos hermanos: `GA_CLAUDE_FINAL_E2E_PROCESS_MATRIX.md` (paso a paso) · `GA_CLAUDE_SAP_EVENT_READINESS_MATRIX.md` (eventos fuente para SAP) · `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md` (R-190…R-220, P1-12 reapertura, GA-GOV-03).

Evidencia de este audit (carpeta `audit/ga-claude-final-audit/evidence/`): `runtime-gp-e2e.json` + `runtime-gp-e2e.run2-partial.json` + `R01…R09-*.png` (runtime real, empresa 1, actores UAT-09); `ui-e2e-local-pass1.json`, `ui-e2e-local-pass2.json` + PNG (pila local aislada, semillas `seeds.test_seeds`, aprobación de un nivel); `playwright_e2e.log` (`bash scripts_e2e.sh`, 17 suites de `e2e/`); `backend_full_suite.log` (`backend/scripts/run_tests.sh`). *Nota de integridad:* los ficheros se consolidan en `evidence/` al cierre del audit desde el área de trabajo de la sesión; los nombres citados son los definitivos.

---

## 0 · Método y leyenda

**Unidad de certificación**: el proceso de negocio completo, no la pantalla ni el endpoint (`GA-REM-016 AC05`, `audit/remediation/E2E_EVIDENCE_MODALITY_MATRIX.md:83-87`). Aquí, además, se exige lo que el encargo §27 y §62 piden: que un usuario normal y autorizado recorra la cadena **por la interfaz**, en el **runtime actual**, sin Swagger/curl/SQL ni conocimiento de rutas ocultas.

**Estados admitidos en este inventario** (uno solo por proceso): `FUNCTIONALLY_CERTIFIED_E2E` · `PARTIAL` · `BROKEN` · `BACKEND_ONLY` · `UAT_PENDING` · `OUT_OF_SCOPE` · `UNKNOWN`.

| Estado | Criterio aplicado |
|---|---|
| `FUNCTIONALLY_CERTIFIED_E2E` | cadena completa por UI con evidencia reproducible en HEAD y comprobación en el runtime actual; reglas, aprobación, estado final, auditoría y reporte verificados |
| `PARTIAL` | la cadena principal es recorrible pero uno o más pasos exigidos no quedaron probados por UI o presentan defecto no bloqueante del camino principal |
| `BROKEN` | al menos un paso exigido del proceso **no puede completarse por la interfaz** en el flujo normal (400/422/envío silencioso) |
| `BACKEND_ONLY` | el proceso existe y funciona por API pero carece de superficie de usuario |
| `UAT_PENDING` | probado técnicamente en runtime por UI; falta la aceptación del propietario declarada como condición |
| `OUT_OF_SCOPE` | legítimamente fuera del alcance pre-SAP (§53: P-08) |
| `UNKNOWN` | no ejercitado en este audit y sin evidencia histórica reproducible en HEAD; se indica el motivo |

**Certificación histórica**: se transcribe tal como la declara cada `PROCESS-xx-CERTIFICATION.md` (estado, modalidad, fecha). Ninguno de los 14 informes cita un artefacto de ejecución (log/trace/informe Playwright) ni el commit certificado; `PROCESS-14-CERTIFICATION.md:170,332` cita tres commits de **implementación** (`07e7410`, `846b1bf`, `a2e21da`), no de ejecución. La reproducibilidad en HEAD se mide con `evidence/playwright_e2e.log` (117 passed · 12 failed).

**Commits de producto desde la certificación**: `git rev-list --count HEAD --since='<fecha> 00:00' -- backend/app frontend/src` sobre HEAD `c0b4afc` (entre paréntesis, total de commits del repositorio): 2026-09-04 → **91** (295) · 2026-09-05 → **85** (275) · 2026-09-06 → **81** (251) · 2026-09-07 → **72** (231).

**Modalidades** (`E2E_EVIDENCE_MODALITY_MATRIX.md:14-23`): `API_E2E` (HTTP directo a `:8099`), `UI_E2E` (navegador → SPA), `RUNTIME_UI_E2E` (esta auditoría, navegador contra `avicola.globaldv.net`), `LOCAL_UI_E2E` (esta auditoría, navegador contra pila local `:5199`).

---

## 1 · Tabla resumen

| ID | Proceso | BU | Alcance pre-SAP | Cert. histórica (estado · modalidad · fecha) | Reproducible en HEAD (`playwright_e2e.log`) | Commits producto desde | **Estado de este audit** | Motivo (resumen) |
|---|---|---|---|---|---|---:|---|---|
| P-01 | Progenitoras — cría | grandparent | sí | `CERTIFIED` · `API_E2E` 3/3 · 2026-09-06 | sí (3/3) | 81 | **BROKEN** | por UI en el lote autocreado (OD-25, sin galpón) `bird_distribution`/`bird_exit` ⇒ 400 BR-08; `farm_inspection` ⇒ 400 sin granja (R-190) |
| P-02 | Progenitoras — producción de huevo | grandparent | sí | `CERTIFIED` · `API_E2E` 9/9 · 2026-09-05 | sí (9/9) | 85 | **BROKEN** | transición cría→producción por UI ⇒ 422 silencioso (R-191); `egg_collection` por UI ⇒ 400 BR-08 (R-190) |
| P-03 | Reproductoras — cría | breeder | sí | `CERTIFIED` (addendum B) · `API_E2E` 5/5 + `UI_E2E` 13/13 · 2026-09-06 | **no** (cadena 400 BR-20; curvas 12/13 locator) | 81 | **BROKEN** | recepción por el hub (`?type=`) no muestra el cuadre BR-20 ⇒ 400 (R-205); resto de la cadena por UI 201 sobre lote con galpón |
| P-04 | Reproductoras — huevo fértil | breeder | sí | `CERTIFIED` · `API_E2E` 9/9 · 2026-09-05 | **no** (BR-20) | 85 | **BROKEN** | transición de fase por UI ⇒ 422 (R-191); recolección/despacho por UI 201 sobre lote con galpón |
| P-05 | Incubación | hatchery | sí | `CERTIFIED` · `API_E2E` 8/8 · 2026-09-05 | **no** (BR-21 + BR-04) | 85 | **BROKEN** | recepción de huevos 422 `arrival_date` / 400 BR-08; carga bloqueada (saldo 0); nacimiento envío silencioso; despacho de pollitos 400 BR-08 (R-194) |
| P-06 | Pollo de engorde | broiler | sí | `CERTIFIED` · `API_E2E` 6/6 · 2026-09-06 | sí (6/6) | 81 | **PARTIAL** | cadena operativa y cierre por UI PASS en local; aprobación por UI no ejercitable con el rol sembrado (botón ausente); cierre imposible tras reverso efectivo (R-192); runtime no ejercitado |
| P-07 | Revisión → corrección → aprobación | transversal | sí | `CERTIFIED` · `API_E2E` 7/7 · 2026-09-04 | sí (7/7) | 91 | **PARTIAL** | enviar/tomar/devolver/reenviar/completar/aprobar/rechazar por UI PASS en runtime; pestañas y filtros del centro inertes, `in_review` huérfano (R-197); lote/`review:review` en aprobación por lote (R-208) |
| P-08 | Consolidación y envío a SAP | transversal | **no** (fase siguiente) | `PARTIAL` · `BLOCKED_EXTERNAL` (`GA-REM-017`) | — | — | **OUT_OF_SCOPE** | tratado aparte (§53/§56) en `GA_CLAUDE_SAP_EVENT_READINESS_MATRIX.md`; frontera interna funcional por API, UI con estados inexistentes (R-217), fail-open sin contexto (R-201) |
| P-09 | Auditoría interna | transversal | sí | `CERTIFIED` · `API_E2E` 6/6 · 2026-09-06 | sí (6/6) | 81 | **PARTIAL** | consulta y filtros operativos; traza duplicada ×2/×3 por acción (P1-12 reapertura), evidencias desaparecen al recargar (R-198), columnas inexistentes en `AuditPage` (R-219) |
| P-10 | Trazabilidad generacional | transversal (4 cadenas) | sí | `CERTIFIED` · `API_E2E` 5/5 · 2026-09-05 | **no** (BR-21 ×5) | 85 | **UNKNOWN** | no ejercitado de extremo a extremo en este audit; suite histórica no reproducible; los eventos que producen los vínculos en la Incubadora fallan por UI (ver traspaso) |
| P-11 | Activación manual de lotes | transversal | sí | `CERTIFIED` · `API_E2E` 6/6 · 2026-09-05 | **no** (BR-20; fixture de empresa) | 85 | **BACKEND_ONLY** | sin superficie de usuario (P1-15; `lots.service.ts:54` sin consumidor); solo `POST /lots/activate-manual` |
| P-12 | Gestión de datos maestros | transversal | sí | `CERTIFIED` · `API_E2E` 3 + `UI_E2E` 1 · 2026-09-06 | sí (4/4) | 81 | **BROKEN** | alta de maestros estructurales por UI envía `{}` ⇒ 422 + React #31 (R-196); 20/21 maestros solo por URL directa |
| P-13 | Autenticación y gestión de usuarios | transversal | sí | `CERTIFIED` · `UI_E2E` 2 + `API_E2E` 1 · 2026-09-06 | sí (3/3) | 81 | **BROKEN** | edición de usuarios imposible (`PUT /users` 422 `extra=forbid`, `alert('[object Object]')`, R-195); autoridad global fabricable desde rol de inquilino (R-199) |
| P-14 | Notificaciones y alertas | transversal | sí | `CERTIFIED` · `UI_E2E` 5/5 · 2026-09-07 | sí (5/5) | 72 | **PARTIAL** | bandeja interna operativa (suite local 5/5; runtime: contador sube tras devolución); los seis tipos normativos no se re-ejercitaron en runtime; sin corrida verde de referencia (GA-GOV-03) |
| P-15 | Reportes e indicadores | transversal | sí | `CERTIFIED` · `API_E2E` 4/4 · 2026-09-06 | **no** (BR-03 fixture) | 81 | **PARTIAL** | reporte de lote e IPE 200 en local; agregados sin predicado de unidad (R-204), doble conteo de huevos (R-214), sin filtro de estado (E-24); operador 403 en KPI del detalle (R-212) |
| OD-19 | Reverso interno de aprobados | transversal | sí | `GA-REM-041` (backend) · sin frontend | — | — | **BACKEND_ONLY** | flujo API probado (solicitud → contrapartida `pending_review` → aprobación → ambos `reversed`; cancelación prohibida); sin UI (R-207); efectos colaterales R-192/R-193 |
| OD-25 | Lote de abuelas al aprobar la importación | grandparent | sí | `GA-R153` certificación técnica; **UAT del propietario pendiente** | — | — | **UAT_PENDING** | probado por UI en runtime (importación → aprobación → `L-GP-2026-12` sin poblar → recepción puebla 50 exactos); 7 casos de `GA_R153_OWNER_UAT.md` sin sesión del propietario |
| X-BU | Traspaso entre unidades (OD-10) | breeder/grandparent → hatchery → breeder/broiler | sí | contrato `IMPLEMENTADO` 4/7 (`BUSINESS_UNIT_HANDOFF_CONTRACT_MATRIX.md:30-34`) · tests backend | tests backend en verde (13 + 4) | — | **BROKEN** | el traspaso no puede producirse por UI: `egg_reception_hatchery` 422/400 y `chick_dispatch` 400 (R-194); `TraceabilityTree` existe; runtime no re-ejercitado |

```
Entradas ............................. 18   (P-01…P-15 + OD-19 + OD-25 + X-BU)
FUNCTIONALLY_CERTIFIED_E2E ...........  0
PARTIAL ..............................  5   (P-06 · P-07 · P-09 · P-14 · P-15)
BROKEN ...............................  8   (P-01 · P-02 · P-03 · P-04 · P-05 · P-12 · P-13 · X-BU)
BACKEND_ONLY .........................  2   (P-11 · OD-19)
UAT_PENDING ..........................  1   (OD-25)
UNKNOWN ..............................  1   (P-10)
OUT_OF_SCOPE .........................  1   (P-08)
```

---

## 2 · Fichas por proceso

Convenciones de las fichas: **Fuente** = documento normativo (`path:línea`); **Pasos** = tipos de evento en el orden del catálogo del producto (`frontend/src/data/processCatalog.ts:354-432`, `STAGE_FLOWS`) contrastados con `docs/02`; **Superficies de entrada** = `App.tsx` (`frontend/src/App.tsx:253-282`); **Endpoints** = routers de backend con el permiso exigido; **Actores** = `docs/02-functional-spec.md:562-583` y `docs/12-approval-workflow.md:44-54`.

### P-01 · Progenitoras — cría
- **Fuente**: `docs/02-functional-spec.md:157-190` (§3.4 plan de importación y creación de lote de abuelas) + `:192-245` (§3.5 cría, común a reproductoras); `specs/global-avicola/spec.md §4.4`. **BU**: `grandparent`.
- **Pasos** (`processCatalog.ts:355-367`): `grandparent_import` → `farm_inspection` → `bird_reception` → `bird_distribution` → `feed_registration` → `weight_recording` → `vaccination` → `medication` → `mortality_recording` → `cull_recording` → `bird_exit`; más `transport_inspection`, `bird_transfer` admitidos en la etapa (`:206-210`). Aprobación P-07 de cada registro; con OD-25, la aprobación de la importación **crea el lote** sin poblarlo (`backend/app/review/service.py:351,515`; `backend/app/lots/service.py` `crear_lote_de_importacion_si_procede`).
- **Actores**: Operador de Granja (registra, `operations:create`), Supervisor (`review:review`), Aprobador (`approvals:approve/reject`); segregación BR-14.
- **Superficies de entrada**: hub `/poultry/grandparent/rearing` (`processCatalog.ts:115-122`) → asistente `/operations/new?type=<evento>` (`App.tsx:260`); detalle de lote `/lots/:id` (acciones rápidas, `App.tsx:265`); centro de revisión `/review`, `/review/:id` (`App.tsx:271-272`).
- **Endpoints**: `POST /operations` (`operations:create`, `operations/router.py:70-74`), `POST /operations/{id}/submit` (`:310-314`), `POST /review/start/{id}`, `/review/return`, `/review/complete` (`review:review`, `review/router.py:73-97`), `POST /approvals/approve|reject` (`approvals:approve|reject`, `:114-137`), `GET /lots/{id}` (`lots/router.py:49-53`).
- **Alcance pre-SAP**: sí (OC SAP como referencia manual, `docs/10:158-164`).
- **Certificación histórica**: `PROCESS-01-CERTIFICATION.md:1-70` — `CERTIFIED`, 12/12 pasos, `API_E2E` 3 casos («no se fabricaron pruebas de interfaz», `:60-63`), 2026-09-06; sin artefacto ni commit. Suite `e2e/proceso-p01-progenitoras-cria.spec.ts` (3 `{ request }`, 0 `{ page }`) pasa hoy 3/3 (`evidence/playwright_e2e.log:92-95`). Commits de producto desde: 81.
- **Estado de este audit: BROKEN.** Runtime por UI (`evidence/runtime-gp-e2e.json`): importación por el hub 201 (`run2-partial` `R-01-import-ui`), envío y revisión por UI, aprobación 200 y lote `L-GP-2026-12` autocreado con `house: null` (`lote-auto`), recepción por el detalle de lote 201 (F-01e, `R-04-reception-ui`), devolución/reenvío/aprobación 200, población exacta 50 (`R-07-poblacion-50`: mortalidad 51 rechazada), mortalidad/alimento/pesaje/vacunación 201 (`R-08-*`). **Rotos por UI**: `farm_inspection` 400 «requiere una granja asignada», `bird_distribution` 400 y `bird_exit` 400 «requiere un galpón asignado» (`R-08-farm_inspection|bird_distribution|bird_exit`). Causa: `OperationFormPage.tsx:386-394,438-439` deriva `house_id` solo para `bird_reception`/`farm_inspection`; `validators.py:828-838` (BR-08) exige granja y galpón en 10 tipos. Brecha **R-190** (P1). No ejercitados en runtime: `transport_inspection`, `cull_recording`, `medication` (en local pasa 2 el lote no llegó a crearse: `GP2-03-review-approve-ui NO_BUTTON`, limitación del rol sembrado).
- **Bloqueantes**: R-190 · R-206 (fecha opcional `''` ⇒ 400 BR-22, `GP2-01a`) · R-197 (centro de revisión) · GA-GOV-03.

### P-02 · Progenitoras — producción de huevo
- **Fuente**: `docs/02-functional-spec.md:247-275` (§3.6 transición, postura, clasificación, despacho, KPI); `spec.md §4.4`. **BU**: `grandparent`.
- **Pasos** (`processCatalog.ts:368-379`): transición de fase (`POST /lots/{id}/phases`, `lots/router.py:136-141`) → `farm_inspection` → `feed_registration` → `weight_recording` → `vaccination` → `medication` → `mortality_recording` → `cull_recording` → `egg_collection` → `egg_dispatch` → `bird_exit`. Aprobación P-07.
- **Actores**: Operador de Granja, Supervisor, Aprobador. **Superficies**: hub `/poultry/grandparent/production`; detalle de lote (botón de transición, `LotDetailPage.tsx:125-131`); asistente `?type=`.
- **Endpoints**: `POST /lots/{id}/phases` (`lots:create`), `POST /operations`, revisión/aprobación como P-01. **Alcance pre-SAP**: sí.
- **Certificación histórica**: `PROCESS-02-CERTIFICATION.md:1-75` — `CERTIFIED`, 10 pasos, `API_E2E` 9/9, 2026-09-05; sin artefacto ni commit. Suite pasa hoy 9/9 (`playwright_e2e.log:93-104`). Commits desde: 85.
- **Estado de este audit: BROKEN.** Runtime: transición por UI ⇒ `POST /lots/66/phases {phase_code:'production', …}` 422 `lot_id`/`phase_id` Field required, sin toast (`runtime-gp-e2e.json` `R-09-transicion-ui`; `R03-transition.png`); `egg_collection` por UI ⇒ 400 BR-08 sobre lote sin galpón (`R-10-egg_collection`); `egg_dispatch` inalcanzable. Local pasa 2: `GP2-16-boton-transicion no visible` (lote no creado). Brechas **R-191** (P1), **R-190** (P1).
- **Bloqueantes**: R-191 · R-190 · AOD-24 (tipo de huevo/ovoscopía sin decidir, `AUDIT_OWNER_DECISIONS_REQUIRED.md:86`) · R-214 (KPI huevo).

### P-03 · Reproductoras — cría
- **Fuente**: `docs/02-functional-spec.md:192-245` (§3.5.1–3.5.10, incluye alertas de cría); `spec.md §4.5`. **BU**: `breeder`.
- **Pasos** (`processCatalog.ts:380-392`): alta de lote (`POST /lots`, `lots/router.py:39-43`, UI `/lots/new`) → `farm_inspection` → `bird_reception` (BR-20 cuadre: `received_total`, `dead_on_arrival`, `rejected_on_arrival`, `validators.py:536-556`) → `bird_distribution` → `feed_registration` → `water_consumption` → `weight_recording` (curva OD-06) → `vaccination` → `medication` → `mortality_recording` → `cull_recording` → `bird_exit`. Aprobación P-07.
- **Actores**: Operador de Granja, Veterinario (vacunas/medicamentos), Supervisor, Aprobador; Administrador (curvas, `masters:*`).
- **Superficies**: hub `/poultry/breeder/rearing`; `/lots/new` (solo web); asistente `?type=`; curvas `/masters/genetic-lines/:id/weight-curves` (`App.tsx:227`).
- **Endpoints**: los de P-01 + `POST /masters/weight-curves`, `PUT /masters/weight-curves/{id}/activate`, `GET /operations/{id}/weight-evaluation` (`operations/router.py:247-252`). **Alcance pre-SAP**: sí.
- **Certificación histórica**: `PROCESS-03-CERTIFICATION.md:1-276` — `CERTIFIED` tras addendum B, 16 pasos, `API_E2E` 5/5 + `UI_E2E` 13/13 (curvas), 2026-09-06; sin artefacto ni commit. Hoy: `proceso-p03-reproductoras-cria.spec.ts` cadena completa **falla** (400 BR-20, `playwright_e2e.log:105,242`); `proceso-p03-curvas-ui.spec.ts` 12/13 (locator ambiguo `getByText(/135/)`, `:166,202-229`). Commits desde: 81.
- **Estado de este audit: BROKEN.** Local pasa 2 (`evidence/ui-e2e-local-pass2.json`): alta de lote por UI 201 con galpón (`BR2-00-lote-ui`, aviso de curva visible); `farm_inspection` 201; **`bird_reception` por el hub ⇒ 400 BR-20** «falta: received_total, dead_on_arrival, rejected_on_arrival» (`BR2-01-bird_reception-por-hub`, `BR2-hub-campo-cuadre-visible: 0`; `P2-B01-br-reception-por-hub.png`); el mismo formulario por URL directa sin `?type=` sí muestra el cuadre y responde 201 (`BR2-02-…-asistente`, `BR2-asistente-campo-cuadre-visible: 1`) — ruta a la que ningún enlace del producto lleva (`OperationFormPage.tsx:316-319,1901-1915`; `BR2-entrada-asistente-sin-type: 0 enlaces`). Con la recepción hecha por esa vía, el resto de la cadena por UI responde 201: distribución, alimento, agua, pesaje, mortalidad, descarte, vacunación, medicación, salida (`BR-*-201`). Brecha **R-205** (P1).
- **Bloqueantes**: R-205 · R-210 (peso capturado en kg, curva en g) · R-211 (BR-17 por galpón) · R-191 (transición a producción, `BR2-transicion-ui: 422`).

### P-04 · Reproductoras — producción de huevo fértil
- **Fuente**: `docs/02-functional-spec.md:247-275` (§3.6); `spec.md §4.6`. **BU**: `breeder`.
- **Pasos** (`processCatalog.ts:393-405`): transición cría→producción → `farm_inspection` → `feed_registration` → `water_consumption` → `weight_recording` → `vaccination` → `medication` → `mortality_recording` → `cull_recording` → `egg_collection` (BR-02 saldo) → `egg_dispatch` (STO SAP; crea `EggBatch`, `operations/service.py:462`) → `bird_exit`.
- **Actores/Superficies/Endpoints**: como P-02 (hub `/poultry/breeder/production`). **Alcance pre-SAP**: sí.
- **Certificación histórica**: `PROCESS-04-CERTIFICATION.md:1-75` — `CERTIFIED`, 10 pasos, `API_E2E` 9/9, 2026-09-05; sin artefacto ni commit. Hoy la cadena completa **falla** (BR-20 en la recepción del fixture, `playwright_e2e.log:112,270`). Commits desde: 85.
- **Estado de este audit: BROKEN.** Local pasa 2: **transición por UI 422** (`BR2-transicion-ui`, misma causa que R-191); sobre el lote de cría con galpón, `egg_collection` 201 y `egg_dispatch` 201 con `sap_order_ref` `AUD-STO-EGG`, transporte y `hatchery_params[{incubator_id}]` (`BR2-egg_collection`, `BR2-egg_dispatch`, `BR2-egg_dispatch-payload`); BR-02 4xx seguro (`BR2-egg_dispatch-exceso: 400`, `BR2-BR02-4xx-seguro PASS`). Runtime no ejercitado para esta BU.
- **Bloqueantes**: R-191 (P1) · R-190 (lotes sin galpón) · AOD-24 · R-214.

### P-05 · Incubación
- **Fuente**: `docs/02-functional-spec.md:278-309` (§3.7.1–3.7.6); `spec.md §4.7`. **BU**: `hatchery`.
- **Pasos** (`processCatalog.ts:406-417`): alta de lote de incubadora → `hatchery_inspection` → `egg_reception_hatchery` (completa `EggBatch`; BR-03 lee `egg_movements[fertile]`) → `egg_reception_classification` → `incubation_load` (BR-03 ≤ recibido) → `ovoscopy` → `transfer_to_hatcher` → `birth_registration` (BR-21 sanos/débiles, `validators.py:577-596`) → `mortality_recording`/`cull_recording` (post-nacimiento) → `chick_dispatch` (crea `ChickBatch`, `operations/service.py:507`).
- **Actores**: Operador de Incubadora, Supervisor, Aprobador. **Superficies**: hub `/poultry/hatchery`; asistente `?type=`; detalle de lote. **Endpoints**: `POST /operations`, revisión/aprobación; `POST /lots/egg-batches` / `chick-batches` (enlace manual, `lots/router.py:239-275`). **Alcance pre-SAP**: sí.
- **Certificación histórica**: `PROCESS-05-CERTIFICATION.md:1-75` — `CERTIFIED`, 8 pasos, `API_E2E` 8/8, 2026-09-05; sin artefacto ni commit. Hoy la cadena completa **falla** (BR-21 `chicks_healthy/weak` obligatorios y BR-04 en cascada, `playwright_e2e.log:122,298`). Commits desde: 85.
- **Estado de este audit: BROKEN.** Local pasa 2 (`ui-e2e-local-pass2.json`, `P2-C01-hat-egg-reception-form.png`): lote 201 (`HAT2-00`), `hatchery_inspection` 201 (`HAT2-01`); **`egg_reception_hatchery` 422** `egg_storage_records.0.arrival_date Field required` (`HAT2-02`) y, sin almacenamiento, **400 BR-08** «requiere una granja asignada» (`HAT2-02b`, `farm_id` forzado a `undefined` en etapa incubadora, `OperationFormPage.tsx:274-278,438`); la sonda por API sin `storage` responde 201 pero el saldo de incubadora queda en 0 porque la UI no escribe `egg_movements[fertile]` (`HAT2-02-saldo-tras-recepcion-ui: 400 … disponibles (0)`); `egg_reception_classification` 201 (`HAT2-03`); **`incubation_load` sin petición** (`HAT2-04 NO_REQUEST`); `ovoscopy` 201 y `transfer_to_hatcher` 201 (`HAT2-05/06`); **`birth_registration` envío silencioso** con y sin dosis (`HAT2-07`, `dosage_per_bird` sin `valueAsNumber`, `OperationFormPage.tsx:1651`) — la sonda API 201 prueba que el backend acepta; **`chick_dispatch` 400 BR-08** (`HAT2-08`). Brecha **R-194** (P1).
- **Bloqueantes**: R-194 · R-190 · AOD-23/AOD-24 (decisiones abiertas sobre nacimiento y tipos de huevo) · R-204 (`/reports/kpis/hatchery` sin unidad).

### P-06 · Pollo de engorde
- **Fuente**: `docs/02-functional-spec.md:312-339` (§3.8.1–3.8.4); `spec.md §4.8`; OD-21/OD-22 y R-184…R-187 (`audit/final-frontend-audit/GA_FINAL_FRONTEND_TEST_DATA_LEDGER.md:86,151-153`; `audit/ga-r186/GA_R186_CERTIFICATION.md`). **BU**: `broiler`.
- **Pasos** (`processCatalog.ts:418-431`): alta/recepción → `farm_inspection` → `bird_reception` (OC, BR-18 acumulado GA-TD-014) → `bird_distribution` → `feed_registration` → `water_consumption` → `weight_recording` → `vaccination` → `medication` → `mortality_recording` → `cull_recording` → `bird_exit` → `lot_closure`/`POST /lots/{id}/close` (BR-05 + R7 + resumen, `validators.py:409-`; `lots/router.py:80-84`, permiso `lots:create`) → reporte de lote e IPE (`reports/router.py:116-120,139-143`).
- **Actores**: Operador de Engorde, Supervisor, Aprobador; cierre con `lots:create`. **Superficies**: hub `/poultry/broiler`; detalle de lote (cierre `LotDetailPage.tsx:111`); `/reports/lot/:id`. **Alcance pre-SAP**: sí.
- **Certificación histórica**: `PROCESS-06-CERTIFICATION.md:1-113` — `CERTIFIED`, 11/11 pasos, `API_E2E` 6 casos, 2026-09-06; sin artefacto ni commit. Suite pasa hoy 6/6 (`playwright_e2e.log:130-137`). Commits desde: 81.
- **Estado de este audit: PARTIAL.** Local pasa 1 y 2 (`ui-e2e-local-pass1.json`, `ui-e2e-local-pass2.json`, `D01-bo-close-unapproved.png`, `D02-bo-closed.png`): sobre `TEST-LOTE-BROILER-01`, por UI 201: `farm_inspection`, `bird_reception` (con galpón), `bird_distribution`, `feed_registration`, `water_consumption`, `weight_recording`, `mortality_recording`, `cull_recording`, `vaccination`, `medication`, `bird_exit` (`BO-*`, `BO2-*`); cierre por UI con registros sin aprobar ⇒ 400 con mensaje claro R7 (`BO2-close-sin-aprobar`); **aprobación por UI**: el aprobador sembrado no ve el botón «Aprobar» en `/review/21` (`BO2-review-page-approver`, `BO2-aprobaciones-detalle: approve NO_BUTTON`; el rol «TEST Aprobador» carece de `review:read`, `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md:89`), aprobados 10/10 por API (`apiFallback`); tras ello **cierre por UI 200** (`BO2-close-aprobado {mort:40, feed:850.5}`, `BO2-lote-cerrado closed`), reporte de lote 200 e IPE 200 (`BO2-ipe {ipe:59.3, fcr:0.85, viab:100}`; R-184 no reproducido: IPE 200 también con lote recién creado, `BO-ipe`). **Defecto de cierre**: lote con reverso efectivo no cierra nunca — 400 «2 registro(s) sin aprobar (2 en «reversed»)» frente al lote de control que cierra 200 (`H8b-control-cierra-200`, `H8b-E02-cierre-bloqueado-por-reversed`), brecha **R-192** (P1). No probado: la cadena por UI en el runtime compartido (sin lote de engorde ejercitado) y la aprobación por UI dentro de la misma cadena.
- **Bloqueantes**: R-192 · R-209 (`sap_document_ref = String(id)` en el bloque de salida, `OperationFormPage.tsx:917-927`) · R-210 · R-211 · R-191 · R-212 (KPI 403 al operador).

### P-07 · Revisión → corrección → aprobación
- **Fuente**: `docs/02-functional-spec.md:375-430` (§3.10); `docs/12-approval-workflow.md:17-147` (flujo, actores, estados, niveles, reglas R1–R9); `docs/03-domain-model.md:622-647` (máquina de estados). **BU**: transversal.
- **Pasos**: `registered` → `submit` (`pending_review`) → `review/start` (`in_review`) → `review/return` (`returned`) / corrección (`POST /corrections`, `corrections:correct`, `corrections/router.py:16-20`) / `review/complete` (`approved` si nivel 1, `corrected` si multinivel, `review/service.py:333-355`) → `approvals/approve|reject` → consolidación (P-08). Aprobación por lote: `POST /approvals/batch-approve|reject` (`review:review`, `review/router.py:147-157`).
- **Actores**: Operador, Supervisor (`review:review`), Aprobador (`approvals:approve/reject`), Coordinador (correcciones); BR-14 segregación (`review/service.py` `SegregacionMixin`).
- **Superficies**: `/review` (`ReviewCenter`), `/review/:id` (`ReviewDetail`), `/review/:id/correct`, `/approvals` (`ApprovalPanel`) — todas solo web (`App.tsx:271-274`); detalle de operación `/operations/:id` (envío). **Alcance pre-SAP**: sí.
- **Certificación histórica**: `audit/remediation/processes/PROCESS-07-REVISION-CORRECCION-APROBACION.md:1-120` — `CERTIFIED`, `API_E2E` 7/7 (`e2e/proceso-03-revision-correccion-aprobacion.spec.ts`; «el ciclo se ejerce después por API», sección Frontend), 2026-09-04; sin artefacto ni commit (`BUSINESS_PROCESS_CERTIFICATION_MATRIX_360.md:30` lo data 2026-09-05 con cambios directos en `review/service.py` sin E2E posterior). Suite pasa hoy 7/7 (`playwright_e2e.log:79-91`). Commits desde: 91.
- **Estado de este audit: PARTIAL.** Runtime por UI con tres identidades UAT-09 (`runtime-gp-e2e.json`): envío 200, tomar+devolver 200 (`R-05-return-ui`, `R-05-devuelto returned`), reenvío 200 (`R-06-reenviado pending_review`), tomar+completar+aprobar 200 (`R-06-aprobado approved`), rechazo 200 (`R-11-rechazado rejected`), reenvío tras rechazo 200, aprobación directa desde `in_review` 200 (`R-12-approve-in_review`); tras `complete` (⇒ `corrected`) el mismo actor recibe 403 al aprobar (`R-11-aprobado approve: 403`) — segregación `docs/12 §6 R2` aplicada en servidor pero **el botón sigue ofreciéndose** (R-212). Notificación al operador tras devolución: `unread 1` (`R-05-notificacion-operador`). **Defectos**: el evento en `in_review` no aparece en las pestañas «Pendientes» ni «En revisión» (`R-12-review-tabs-in_review {pending_review:false,in_review:false}`, `R04-review-tabs.png`; local `H2-*`), filtros `status/operator_id` no declarados por `review/router.py:23-33`, historial vacío para acciones individuales, respuesta de aprobación descartada (sin enlace al lote creado) — **R-197** (P2); permiso más débil en aprobación por lote — **R-208** (P2); reverso sin superficie — **R-207**.
- **Bloqueantes**: R-197 · R-208 · R-207 · R-212 · P1-12 (auditoría duplicada de cada transición).

### P-08 · Consolidación y envío a SAP — *tratado aparte*
- **Fuente**: `docs/02-functional-spec.md:126-155` (§3.3), `:421-430` (§3.10.5); `docs/10-sap-integration-strategy.md:85-118,122-132,135-155,158-177`; `docs/03-domain-model.md:481-560`. **BU**: transversal (`OD-12`, contrato SAP transversal, `specs/remediation/OD-12-SAP-TRANSVERSAL-CONTRACT.md:57-80`).
- **Pasos**: `POST /sap/consolidate` (aprobados → `CONSOLIDATED`, `sap/service.py:151-227`) → `POST /sap/export` (adaptador `manual`/`mock`, `config.py:131`; payload `PREPARED`, eventos siguen `CONSOLIDATED`: `sap/service.py:344-364`; `adapter.py:88-133`) → `POST /sap/retry` (`:402-462`). Permisos `sap:read` / `sap:send_sap` (`sap/router.py:20-184`). UI `/sap` (`SapManagerPage`, `App.tsx:276`) y `/reports/sap`.
- **Actores**: Analista SAP. **Alcance pre-SAP**: **no** — es la fase siguiente (§53/§56). Real: `GA-REM-017` `BLOCKED_EXTERNAL` (`REMEDIATION_BACKLOG.md:32,59`); `SAP_ADAPTER=real` ⇒ 501 (`sap/service.py:49-56`).
- **Certificación histórica**: `PARTIAL · BLOCKED_EXTERNAL` (`PROCESS_CERTIFICATION_MATRIX.md:46`; `BUSINESS_PROCESS_CERTIFICATION_MATRIX_360.md:31`). Tests backend `test_sap.py` (9) y `test_sap_transversal.py` (15) dentro de los 1201 passed (`evidence/backend_full_suite.log:624`).
- **Estado de este audit: OUT_OF_SCOPE** para la puerta §53. Estado real de la frontera interna: por API funcional (consolidar/exportar/reintentar); **sin UI operativa** (`SapManagerPage.tsx:70-72` filtra `pending/draft/sent/error`, estados que el backend no produce — `prepared/sending/confirmed/failed/retrying`, `sap/models.py:47-52`; sin refetch ni reintento, **R-217**); lectura/reintento sin contexto de empresa fail-open (`sap/service.py:76-81`, **R-201**); `SAP_ERROR` sin productor y `retry_failed` salta a `SAP_CONFIRMED` sin auditoría (E-25). Detalle en `GA_CLAUDE_SAP_EVENT_READINESS_MATRIX.md`.

### P-09 · Auditoría interna
- **Fuente**: `docs/02-functional-spec.md:432-461` (§3.11); `docs/12-approval-workflow.md:248-266`; `docs/03-domain-model.md:450-479`. **BU**: transversal.
- **Pasos**: producción de `AuditLog` en cada acción (`audit/listeners.py`, `audit/helpers.py`) → consulta `GET /audit` con 7 filtros normativos, `GET /audit/{id}`, `GET /audit/timeline/{entity_type}/{entity_id}` (`audit:read`, `audit/router.py:16-59`) → evidencias de evento (`operations/router.py:334-417`).
- **Actores**: Auditor, Administrador, Supervisor autorizado. **Superficies**: `/audit` (`AuditPage`, solo web, `App.tsx:275`); `/operations/:id` (evidencias). **Alcance pre-SAP**: sí.
- **Certificación histórica**: `PROCESS-09-CERTIFICATION.md:1-163` — `CERTIFIED`, 19/19 acciones, `API_E2E` 6/6 (`:153-158`), 2026-09-06; sin artefacto ni commit. Suite pasa hoy 6/6 (`playwright_e2e.log:138-143`). Commits desde: 81.
- **Estado de este audit: PARTIAL.** `/audit` carga y lista (`ui-e2e-local-pass2.json` `PAGE2-audit`, `E02-audit.png`); `GET /audit` 200 (`H6-audit-api`). **Defectos de integridad**: la línea de tiempo devuelve cada acción por duplicado o triplicado — `created:registered ×2`, `review_started ×3`, `approved ×2` (`H8b-timeline-original`, `H8b-timeline-contraparte`; pasa 1 `H6-audit-timeline`) por doble productor `audit/listeners.py:71-113` + `audit/helpers.py` (**P1-12 reapertura**); las evidencias adjuntas desaparecen del detalle al recargar y se adjuntan en cualquier estado sin auditoría (**R-198**); `AuditPage.tsx:90-95` pinta campos inexistentes `user_name/old_value/new_value` (**R-219**); sin auditoría de cierre/activación/fases de lote, usuarios, evidencias ni exportaciones (P1-12). Runtime: sin fila de auditoría verificada de extremo a extremo por este audit (no ejercitado).
- **Bloqueantes**: P1-12 · R-198 · R-219.

### P-10 · Trazabilidad generacional
- **Fuente**: `docs/03-domain-model.md:300-380` (§4.4 `EggBatch`/`ChickBatch`, reglas, `GET /lots/{id}/traceability`); `spec.md §4.9`. **BU**: las cuatro cadenas.
- **Pasos** (`PROCESS-10-CERTIFICATION.md:34-47`, 12 pasos): `egg_dispatch` → `egg_reception_hatchery` → `EggBatch` automático → recepción lo completa → `chick_dispatch` → `bird_reception` → `ChickBatch` con `egg_batch_id` → navegación bidireccional → sin autorreferencia → sin destino no se inventa → enlace manual (`POST /lots/egg-batches|chick-batches`) → aislamiento por empresa.
- **Actores**: cualquier rol con `lots:read`; enlace manual `lots:create`. **Superficies**: `frontend/src/components/TraceabilityTree.tsx` dentro de `/lots/:id` (`LotDetailPage.tsx`). **Endpoints**: `GET /lots/{id}/traceability` (`lots/router.py:154-158`). **Alcance pre-SAP**: sí.
- **Certificación histórica**: `PROCESS-10-CERTIFICATION.md:1-161` — `CERTIFIED` tras `GA-REM-031`, `API_E2E` 5/5 (`:145-150`), 2026-09-05; sin artefacto ni commit. Hoy los 5 casos **fallan** (BR-21 en el fixture, `playwright_e2e.log:144-149,332-476`). Commits desde: 85.
- **Estado de este audit: UNKNOWN.** No se ejercitó el árbol ni los vínculos de extremo a extremo (ni en runtime ni en local); la evidencia histórica no es reproducible en HEAD; el contrato de traspaso está cubierto por `backend/tests/test_handoff_contract.py` (13 casos) y `test_traceability.py` (4) dentro de los 1201 passed (`backend_full_suite.log:624`). Motivo del UNKNOWN: no puede afirmarse PASS ni FAIL del **proceso** de lectura; lo que sí está probado es que los eventos que **producen** los vínculos en la Incubadora no se pueden registrar por UI (ver X-BU).
- **Bloqueantes**: R-194 (aguas arriba) · R-215 (`TraceabilityTree.tsx:95,114,347,389` renderiza `detail` crudo) · GA-GOV-03.

### P-11 · Activación manual de lotes existentes
- **Fuente**: `docs/02-functional-spec.md:342-371` (§3.9, «Prioridad: Crítica (para implantación)»; seis reglas §3.9.2). **BU**: transversal.
- **Pasos**: `POST /lots/activate-manual` (`lots:create`, `lots/router.py:99-103`) con saldos, acumulados, fecha real, motivo y soporte → `OpeningBalance` (`GET /lots/{id}/opening-balance`, `:109-113`) → operación desde el saldo inicial.
- **Actores**: Administrador («Activar lotes manualmente — Solo administradores», `docs/02:583`). **Superficies**: **ninguna** — `frontend/src/services/lots.service.ts:54-55` define `activateManual` sin ningún consumidor en `frontend/src/pages` (grep). **Alcance pre-SAP**: sí (crítico para implantación).
- **Certificación histórica**: `PROCESS-11-CERTIFICATION.md:1-114` — `CERTIFIED`, 6 reglas, `API_E2E` 6/6, 2026-09-05; sin artefacto ni commit. Hoy 4/6: fallan «un lote que ya opera no puede activarse» (BR-20 en el fixture) y «no se activa el lote de otra empresa» (fixture de empresa, R-118) (`playwright_e2e.log:152-156,477-532`). Commits desde: 85.
- **Estado de este audit: BACKEND_ONLY.** Sin superficie de usuario (P1-15, `REMEDIATION_BACKLOG.md:101`); no ejercitado por API en este audit (queda como capacidad no alcanzable por un usuario normal, §62).
- **Bloqueantes**: P1-15 (UI) · R-203 (`house_id`/`genetic_line_id`/`weight_curve_id` sin verificar pertenencia, `lots/service.py:362-392`) · GA-GOV-03.

### P-12 · Gestión de datos maestros
- **Fuente**: `docs/02-functional-spec.md:94-124` (§3.2, 17 catálogos base + maestros de flujo); `docs/03-domain-model.md:564-598`. **BU**: transversal (control-plane, OD-09).
- **Pasos** (`PROCESS-12-CERTIFICATION.md:64-77`): consultar con total → alta → edición → baja lógica → uso en la operación → aislamiento → pertenencia del padre → permiso. **Endpoints**: `GET/POST/PUT/DELETE /masters/<entidad>` ×21 (`masters:*`), `GET /masters/farms/{id}/houses`, `/hatcheries/{id}/incubators`.
- **Actores**: Administrador de Empresa. **Superficies**: `/masters/<entidad>` (`MasterListPage`, solo web, `App.tsx:220-233`); 20/21 maestros sin enlace de navegación (`GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md:86`). **Alcance pre-SAP**: sí (régimen provisional OD-24 para empresas/granjas).
- **Certificación histórica**: `PROCESS-12-CERTIFICATION.md:1-128` — `CERTIFIED`, 8 pasos, 19 maestros, `API_E2E` 3 + `UI_E2E` 1 (contador), 2026-09-06; sin artefacto ni commit. Suite pasa hoy 4/4 (`playwright_e2e.log:160-164`). Commits desde: 81.
- **Estado de este audit: BROKEN.** Local pasas 1 y 2 (`MAS-hatchery-create-ui`, `MAS2-hatchery-create-ui`, `H4-masters-house-create-ui`; `E01-masters-hatcheries.png`, `H04-masters-house-create.png`): el formulario genérico envía `POST /masters/hatcheries {}` ⇒ 422 (`company_id`, `name`) y `POST /masters/houses {}` ⇒ 422 (`farm_id`, `name`), con `pageerror` React #31 al pintar el `detail` estructurado (`fatal_react: 2` en pasa 1; `MasterListPage.tsx:80,92-99,193-203`). Brecha **R-196** (P1); errores crudos y sin `ErrorBoundary` **R-215**.
- **Bloqueantes**: R-196 · R-215 · OD-24 (empresas/granjas de SAP: sin código hoy) · OD-18 (`sap_config` fuera del catálogo).

### P-13 · Autenticación y gestión de usuarios
- **Fuente**: `docs/02-functional-spec.md:47-91` (§3.1 login, usuarios, roles, aislamiento multi-compañía, perfil). **BU**: transversal (control-plane).
- **Pasos** (`PROCESS-13-CERTIFICATION.md`, 14 pasos): login (`POST /login`, `/refresh`, `/me`) → alta/edición/baja de usuarios (`GET/POST/PUT/DELETE /users`, `POST /users/{id}/password`) → roles y permisos (`GET /roles/permissions-catalog`, `POST/PUT /roles`) → concesión de unidades (`POST/DELETE /users/{id}/business-units`) → perfil.
- **Actores**: Administrador de Empresa, Administrador de Accesos (OD-15), Super Administrador. **Superficies**: `/login`, `/users`, `/roles`, `/admin/unit-access`, `/profile` (`App.tsx:207,266,277-281`). **Alcance pre-SAP**: sí.
- **Certificación histórica**: `PROCESS-13-CERTIFICATION.md:1-143` — `CERTIFIED`, `UI_E2E` (superficie) + `API_E2E` (efecto) (`:121-126`), 2026-09-06; sin artefacto ni commit; `BUSINESS_PROCESS_CERTIFICATION_MATRIX_360.md:36`: «reescritura de su servicio; cubierta por 80+ tests de integración nuevos, no por E2E». Suite pasa hoy 3/3 (`playwright_e2e.log:165-168`). Commits desde: 81.
- **Estado de este audit: BROKEN.** Login por UI PASS en runtime y local (`login-ui`, `login-ui-admin`, `login-ui-approver`); `/users` y `/roles` cargan (`PAGE2-users`, `PAGE2-roles`); habilitar/deshabilitar unidad y reconceder por UI 200/201 (`OD23b-*`, `OD16b-hub-sin-incubadora-tras-OFF PASS`). **Edición de usuarios imposible**: `UsersPage.tsx:76-79,85` envía `username`/`company_id` a `PUT /users/{id}` cuyo `UserUpdate` es `extra="forbid"` ⇒ 422 y `alert('[object Object]')` (**R-195**, P1; local `H3-users-edit-boton: no visible`). **Seguridad**: un rol de inquilino con `("*", all)` fabrica `is_super_admin` y `switch-company` (`auth/service.py:585-658`, `security.py:119-120,507-540`, **R-199**, P1); refresh token aceptado como access (**R-200**); `/me` 500 con correos que `EmailStr` rechaza (**R-213**).
- **Bloqueantes**: R-195 · R-199 · R-200 · R-202 · R-213 · R-212.

### P-14 · Notificaciones y alertas
- **Fuente**: `docs/02-functional-spec.md:510-520` (§3.14, seis tipos); `docs/10-sap-integration-strategy.md:148-154` (aviso al Analista SAP); OD-07/OD-08. **BU**: transversal.
- **Pasos**: productor (rechazo/devolución, umbral de mortalidad, peso fuera de curva, pendiente > 24 h, lote próximo a cierre, error SAP `sap/service.py:464-525`) → `GET /notifications`, `/unread-count`, `PATCH /notifications/{id}/read` (`notifications/router.py:26-69`) → campana y bandeja.
- **Actores**: destinatarios OD-08 (originador, administradores, contraloría, supervisor; Analista SAP). **Superficies**: campana en la cabecera; `/my-pending` (huérfana, R-220). **Alcance pre-SAP**: sí (el tipo «error SAP» solo se produce en P-08).
- **Certificación histórica**: `PROCESS-14-CERTIFICATION.md` (addendum B) — `CERTIFIED` 6/6 tipos, `UI_E2E` 5/5, 2026-09-07 (`PROCESS_CERTIFICATION_MATRIX.md:582-613`); cita commits de implementación (`:170,332`), no de ejecución. Suite pasa hoy 5/5 (`playwright_e2e.log:173-182`). Commits desde: 72.
- **Estado de este audit: PARTIAL.** Runtime: tras la devolución por UI el contador del operador sube a 1 (`runtime-gp-e2e.json` `R-05-notificacion-operador {unread:1}`); local: `test_lot_planned_close.py` 14/14 dentro de la suite backend. No re-ejercitados en runtime: apertura y lectura del aviso, umbral de mortalidad, peso fuera de curva, > 24 h, próximo a cierre, error SAP (sin productor pre-SAP). Sin corrida verde completa que ampare la certificación (GA-GOV-03).
- **Bloqueantes**: GA-GOV-03 · dependencia de P-08 para el sexto tipo.

### P-15 · Reportes e indicadores
- **Fuente**: `docs/02-functional-spec.md:464-490` (§3.12, 13 KPI + 6 reportes); `spec.md §4.12`; `audit/remediation/KPI_FORMULA_AND_DATA_SOURCE_MATRIX.md`. **BU**: transversal (agregados D del contrato OD-10).
- **Pasos**: `GET /reports/kpis*` (11 rutas), `GET /reports/kpi/ipe/{lot}`, `/kpi/weight-uniformity/{lot}`, `/reports/lot/{lot}`, `/reports/sap-comparison` (`reports:read`, `reports/router.py:15-153`); `GET /dashboard/mobile|admin`.
- **Actores**: Consulta/Reportes, Supervisor, Administrador. **Superficies**: `/reports`, `/reports/lot/:id`, `/reports/sap`, `/kpi` (`App.tsx:216,267-269`); KPI en `/lots/:id`. **Alcance pre-SAP**: sí (excepto «Reporte de diferencias SAP»).
- **Certificación histórica**: `PROCESS-15-CERTIFICATION.md:1-157` — `CERTIFIED`, 15/15 indicadores y 6/6 reportes, `API_E2E` 4/4 (`:147-152`), 2026-09-06; sin artefacto ni commit; `BUSINESS_PROCESS_CERTIFICATION_MATRIX_360.md:38`: «certificó la cadena, no las fórmulas». Hoy 3/4: falla «los indicadores de incubadora son números…» (fixture BR-03, `playwright_e2e.log:169,533`). Commits desde: 81.
- **Estado de este audit: PARTIAL.** Local: `/reports` carga (`PAGE2-reports`), reporte de lote 200 con `lot/opening_balance/phases/event_summary` (`BO2-reporte-lote`), IPE 200 (`BO2-ipe`). **Defectos**: `/reports/kpis/hatchery`, `/reports/kpis` y `dashboard.active_alerts` agregan sin predicado de unidad (`reports/service.py:64-70,191-207,262-308`; `dashboard/service.py:206-242`, **R-204**); doble conteo `EGG_COLLECTION + EGG_CLASSIFICATION` (`reports/service.py:108-122`, **R-214**); IPE/uniformidad/AFCR sin filtro de estado (E-24); `lots_by_type` con claves `BirdTypeEnum.*` ⇒ tarjetas en 0 (**R-216**, `H5-dashboard-admin`); operador con 403 ×12 en KPI del detalle de lote (**R-212**, `runtime-gp-e2e.json httpErrores`).
- **Bloqueantes**: R-204 · R-214 · R-216 · R-218 · R-212.

### OD-19 · Reverso interno de registros aprobados (flujo)
- **Fuente**: `specs/remediation/OD-19-INTERNAL-REVERSAL-OF-APPROVED-RECORDS.md:22-43` (reglas 1–22); `docs/02-functional-spec.md:556` (R16); `GA-REM-041`. **BU**: transversal (regla 13: unidad habilitada).
- **Pasos**: `POST /reversals` (`reversals:create`, `reversals/router.py:16-20`; original `APPROVED`, `reversals/service.py:88-131`) → contrapartida generada por el servidor en `pending_review` (`:131`) → revisión/aprobación por el motor P-07 → `efectuar_reverso_si_procede` marca original y contrapartida `REVERSED` (`:181-216`; `review/service.py:341-345`) → consulta `GET /reversals`, `/reversals/event/{id}`.
- **Actores**: quien posea `reversals:create` (≠ aprobador, regla 70) + aprobador. **Superficies**: **ninguna** (`grep reversals frontend/src` ⇒ 0; badge `reversed` ausente en `statusColors.ts`). **Alcance pre-SAP**: sí (elegibilidad solo pre-SAP, regla 10).
- **Certificación histórica**: `GA-REM-041` «sin frontend» (`GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md:37`); `test_internal_reversal.py` 22 casos (1 fallo TEST_DEFECT `test_s03_s04`, `backend_full_suite.log:600`).
- **Estado de este audit: BACKEND_ONLY.** Local por API (`ui-e2e-local-pass1.json` `H8-*`; `ui-e2e-local-pass2.json` `H8b-*`): solicitud 201 con contrapartida (`H8b-reverso-solicitado counterpart: 38`), contrapartida nace `pending_review`, tras `start/complete` ambos `reversed` (`H8b-reverso-efectuado`), cancelación del reversado prohibida 400 (`H8b-reversed-no-cancelable`). **Efectos colaterales**: el lote con reverso efectivo no cierra (`H8b-cierre-con-reverso: 400 … (2 en «reversed»)`, **R-192**); BR-18 cuenta original y contrapartida (`validators.py:769-783`, **R-193**); auditoría de la contrapartida duplicada (`H8b-timeline-contraparte`).
- **Bloqueantes**: R-207 (UI) · R-192 · R-193 · P1-12.

### OD-25 · Lote de abuelas al aprobar la importación (flujo)
- **Fuente**: `audit/ga-r153/GA_OD_25_GRANDPARENT_LOT_ON_APPROVAL_DECISION.md:3-5` (opción B, `RATIFIED` 2026-09-12); `docs/02-functional-spec.md:185-188` (§3.4.2); `AUDIT_OWNER_DECISIONS_REQUIRED.md:99-101`. **BU**: `grandparent`.
- **Pasos**: `grandparent_import` sin lote (aviso en el selector) → P-07 → al aprobar (`review/service.py:351` nivel único; `:515` aprobación) `crear_lote_de_importacion_si_procede` crea `L-GP-{año}-{nn}` sin poblar y **sin galpón** → `bird_reception` sobre el lote puebla (F-01e deriva `house_id` de la primera fila, `OperationFormPage.tsx:387-394`) → BR-01 sobre el saldo.
- **Actores**: Operador de progenitoras + aprobador. **Superficies**: hub → `?type=grandparent_import`; `/review/:id`; `/lots/:id`. **Alcance pre-SAP**: sí.
- **Certificación histórica**: `GA-R153` C1 `9651550` · C2 `47ea484` · C2b `db8ae21` (E2E runtime 0 fallos) y `GA-F01` C2f/C3 (`c0b4afc`: «retry UAT-01..07 7/7 … pendiente: sesion del propietario»); **aceptación del propietario PENDIENTE** (`GA_R153_OWNER_UAT.md`, 7 casos).
- **Estado de este audit: UAT_PENDING.** Reproducido por UI en runtime (`runtime-gp-e2e.json`): importación 124 por el hub 201 (`run2-partial R-01-import-ui`), aprobación 200 ⇒ lote 66 `L-GP-2026-12` (`lote-auto {house:null, farm:1}`), un solo lote nuevo (`AC06-un-solo-lote-nuevo PASS`), recepción por el detalle de lote 201 (`R-04`), población exacta 50 (`R-07-poblacion-50`). Consecuencia abierta: el lote nace sin galpón y los eventos de ubicación posteriores fallan por UI (R-190; alternativa B de la clarificación: fijar `house_id` al aprobar la primera recepción — decisión del propietario).
- **Bloqueantes**: sesión UAT del propietario (GA-UAT-09) · R-190 · R-206.

### X-BU · Traspaso entre unidades de negocio (OD-10)
- **Fuente**: `specs/remediation/OD-10-HANDOFF-CONTRACT-AND-PENDING-CLASSIFICATION.md:57-99,150-165` (contrato limitado, destino declarado); `audit/remediation/BUSINESS_UNIT_HANDOFF_CONTRACT_MATRIX.md:18-34,47-78` (campos B/C por flujo); `audit/remediation/CROSS_MODULE_FLOW_MATRIX.md:20-29` (siete flujos); `docs/03-domain-model.md:300-380`. **BU**: origen `grandparent|breeder` → destino `hatchery`; origen `hatchery` → destino `breeder|broiler` (`backend/app/business_units/handoff.py:34-38`).
- **Pasos**: `egg_dispatch` con destino declarado → `EggBatch` (`operations/service.py:462`) → `egg_reception_hatchery` completa cantidades/fechas → `chick_dispatch` con destino → `ChickBatch` con `egg_batch_id` (`:507`) → `bird_reception` en destino → lectura por `LotRef` mínimo (`ConsolidatedMovementRead`/proyecciones) → árbol `GET /lots/{id}/traceability`; enlace manual `POST /lots/egg-batches|chick-batches` (`lots/router.py:239-275`); `validar_flujo` rechaza cadenas fuera de tabla (`handoff.py:50-67`).
- **Actores**: operadores de origen (despacho) y destino (recepción); aprobadores. **Superficies**: asistente `?type=egg_dispatch|egg_reception_hatchery|chick_dispatch|bird_reception`; `TraceabilityTree` en `/lots/:id`. **Alcance pre-SAP**: sí (flujos 1, 2, 3 y 7 `IMPLEMENTADO`; 4 y 6 aplazados a fase 6; 5 = excepción SAP OD-12).
- **Certificación histórica**: contrato `GA-REM-040` fase 5 (`BUSINESS_UNIT_HANDOFF_CONTRACT_MATRIX.md:30-34`); `test_handoff_contract.py` 13 casos en verde; P-10 `API_E2E` (no reproducible hoy).
- **Estado de este audit: BROKEN.** Por UI: el lado de despacho desde Reproductoras responde 201 (`BR2-egg_dispatch`, con `hatchery_params[{incubator_id:1}]`), pero la **recepción en la incubadora** responde 422/400 (`HAT2-02`, `HAT2-02b`) y el **despacho de pollitos** 400 BR-08 (`HAT2-08`): ninguno de los dos traspasos puede confirmarse por la interfaz. Requisitos §32 no verificables por UI en este audit: linaje, cantidades recibidas, estado del traspaso, auditoría del traspaso, entrada del frontend. Runtime no re-ejercitado. El contrato backend (campos B/C, destino declarado, aislamiento) queda cubierto por tests, no por E2E.
- **Bloqueantes**: R-194 · R-190 · R-215 (`TraceabilityTree` errores crudos) · GA-GOV-03 (P-10 no reproducible).

---

## 3 · Puerta de certificación §53

Regla: todo proceso de alcance pre-SAP debe terminar en `FUNCTIONALLY_CERTIFIED_E2E` o, legítimamente, `OUT_OF_SCOPE`; P-08 se trata aparte.

| Proceso | Estado | ¿Supera la puerta? |
|---|---|:--:|
| P-01 Progenitoras — cría | BROKEN | **NO** |
| P-02 Progenitoras — producción | BROKEN | **NO** |
| P-03 Reproductoras — cría | BROKEN | **NO** |
| P-04 Reproductoras — huevo fértil | BROKEN | **NO** |
| P-05 Incubación | BROKEN | **NO** |
| P-06 Pollo de engorde | PARTIAL | **NO** |
| P-07 Revisión → corrección → aprobación | PARTIAL | **NO** |
| P-08 Consolidación y envío a SAP | OUT_OF_SCOPE (fase siguiente; `BLOCKED_EXTERNAL`) | sí (legítimo, §53/§56) |
| P-09 Auditoría interna | PARTIAL | **NO** |
| P-10 Trazabilidad generacional | UNKNOWN | **NO** |
| P-11 Activación manual | BACKEND_ONLY | **NO** |
| P-12 Datos maestros | BROKEN | **NO** |
| P-13 Autenticación y usuarios | BROKEN | **NO** |
| P-14 Notificaciones | PARTIAL | **NO** |
| P-15 Reportes e indicadores | PARTIAL | **NO** |
| OD-19 Reverso interno | BACKEND_ONLY | **NO** |
| OD-25 Lote de abuelas al aprobar | UAT_PENDING | **NO** |
| X-BU Traspaso entre unidades | BROKEN | **NO** |

```
Procesos de alcance pre-SAP ........ 17
Superan la puerta §53 ..............  0
No superan la puerta ............... 17   (BROKEN 8 · PARTIAL 5 · BACKEND_ONLY 2 · UAT_PENDING 1 · UNKNOWN 1)
OUT_OF_SCOPE legítimo ..............  1   (P-08)
```

**Lectura**: ningún proceso del alcance pre-SAP alcanza `FUNCTIONALLY_CERTIFIED_E2E` con la evidencia exigida por §27 (cadena completa por UI, runtime actual, artefacto reproducible). Las 14 certificaciones históricas `CERTIFIED` se apoyan en 9 suites `API_E2E`, no citan artefacto de ejecución ni commit, tienen entre 72 y 91 commits de producto posteriores y seis de ellas (P-03, P-04, P-05, P-10, P-11, P-15) **no son reproducibles en HEAD** (`evidence/playwright_e2e.log`: 12 fallos). Además, la suite backend completa presenta 25 fallos (`backend_full_suite.log:624`) y la CI solo se ejecuta en `pull_request` (GA-GOV-03).

---

## 4 · Respuesta a §62 por unidad de negocio y a §63

¿Puede un usuario normal y autorizado iniciar el proceso por la interfaz, completar cada paso, disparar cada aprobación, ver el resultado, continuar y alcanzar el estado final sin Swagger, curl, SQL, cambios manuales ni rutas ocultas?

| BU | Respuesta | Ruptura exacta | Spec |
|---|---|---|---|
| **Progenitoras** | **NO** | lote autocreado sin galpón: `bird_distribution`, `bird_exit`, `egg_collection` ⇒ 400 BR-08 por UI; `farm_inspection` ⇒ 400 sin granja; transición cría→producción ⇒ 422 silencioso | R-190 · R-191 · (R-206) |
| **Reproductoras** | **NO** | recepción por el hub sin bloque de cuadre ⇒ 400 BR-20 (la ruta que lo muestra no está enlazada); transición de fase ⇒ 422 | R-205 · R-191 · (R-190, R-210, R-211) |
| **Incubadora** | **NO** | recepción de huevos 422 `arrival_date` / 400 BR-08; saldo de incubadora 0 (la UI no escribe `egg_movements[fertile]`); nacimiento con envío silencioso; despacho de pollitos 400 BR-08 | R-194 |
| **Engorde** | **NO DEMOSTRADO** (PARTIAL) | camino principal por UI PASS en local (eventos, cierre con R7, reporte, IPE); aprobación por UI no ejercitable con el rol sembrado; cierre imposible tras un reverso efectivo; runtime no ejercitado | R-192 · R-209 · R-210 · R-211 |
| **Cadena completa (§63)** | **NO** | el objeto de negocio no puede cruzar Reproductoras → Incubadora → Engorde por UI: la recepción en incubadora y el despacho de pollitos no se registran; los vínculos `EggBatch`/`ChickBatch` no llegan a completarse | R-194 · R-190 |

Conclusión del inventario para la decisión pre-SAP: **NO-GO** hasta cerrar, como mínimo, GA-GOV-03 (suite verde reproducible), R-190, R-191, R-194, R-205 (cadenas por UI), R-192/R-193 (cierre y ledger tras reverso), R-195/R-196 (usuarios y maestros) y R-199 (seguridad), y recertificar P-01…P-15 con artefactos de ejecución y la sesión UAT del propietario (OD-25). SAP no debe usarse como remedio de ninguno de estos huecos (§64).

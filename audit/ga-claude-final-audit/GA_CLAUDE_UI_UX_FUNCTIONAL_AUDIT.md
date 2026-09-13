# GA-CLAUDE · AUDITORÍA FUNCIONAL UI/UX (§8, §9, §10, §11, §39–§42)

**Fecha** 2026-09-13 · **Repositorio** `/home/maria/Proyectos/GlobalAvicola` · **HEAD** `c0b4afc` (`main`) · **Runtime** `https://avicola.globaldv.net` (bundle servido `index-DDCcWL76.js` = build local de HEAD) · **Modo** solo lectura: producto, tests y documentación existente intactos.

## 0 · Alcance, fuentes y leyenda

Esta auditoría **no** es una revisión estética: es la verificación funcional de §8 (¿puede el usuario previsto encontrar, entrar, rellenar, guardar, ver el resultado, recuperarse del error y continuar?) sobre los recorridos críticos del producto, en escritorio y móvil (390×844), en ES y EN, y aplicando §10 (ningún flujo requerido puede depender de curl/Swagger/SQL) y §11 (ningún «éxito» se certifica por toast/cierre de modal sin estado persistido).

| Fuente | Uso |
|---|---|
| Informes de código de esta auditoría (scratchpad de sesión): `A_fe_be_trace.md` (**A §n**), `B_form_contracts.md` (**B-nn**), `C_response_error_state.md` (**C#n**), `F_i18n_nav_responsive.md` (**G-nn**, **Rn**) | Citas `archivo:línea`; las de carga se verificaron sobre HEAD antes de usarlas aquí |
| Registro canónico de brechas: `audit/ga-claude-final-audit/GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md` (R-190…R-220, GA-GOV-03, P1-12-REOPEN) | Único origen de identificadores; **no se inventan ids**. Capacidades ausentes sin R-id se citan por su fila `CF-nn` de `GA_CLAUDE_FRONTEND_CAPABILITY_MATRIX.md` |
| Evidencia runtime (rutas relativas a `audit/ga-claude-final-audit/evidence/`): `runtime-gp-e2e.json` + `R01…R09.png` (**[RT]** — runtime real, empresa 1, actores UAT-09 `uat09-op-*`/`uat09-ap-*`); `ui-e2e-local-pass1.json` + PNG `A00…H05` (**[L1]** — pila local aislada, semillas `seeds.test_seeds`, aprobación de un nivel); `ui-e2e-local-pass2.json` + PNG `P2-*` (**[L2]**) | Al cerrar este documento el recorrido L2 seguía ejecutándose (PID 321449) y su JSON se escribe al final del script (`ui_e2e_local_pass2.mjs:566`); los pasos citados constan en `ui_e2e_local_pass2.log`. Los artefactos se generaron en el scratchpad (`evidence-runtime/`, `evidence-local/`) y estaban pendientes de consolidación en `evidence/` (carpeta vacía al redactar) |

**Veredictos por dimensión**: `PASS` (funciona y se verificó) · `PARTIAL` (funciona con brecha material) · `FAIL` (impide completar el proceso o desinforma) · `N/A` (no aplica) · `UNKNOWN` (no verificable; motivo indicado).

**Clases §9**: `FUNCTIONAL_UI_GAP`, `FRONTEND_BACKEND_INTEGRATION_GAP`, `DISCOVERABILITY_GAP`, `STATE_FEEDBACK_GAP`, `ERROR_HANDLING_GAP`, `RESPONSIVE_GAP`, `I18N_GAP`, `ACCESSIBILITY_GAP`, `UX_ENHANCEMENT`, `UX_PREFERENCE`.

Notas de lectura de las capturas: `R02-lot-detail.png` quedó capturada en estado «Cargando…» (captura prematura); la evidencia visual del detalle del lote autocreado es `R03-transition.png` (misma pantalla, cargada). `D01-bo-close-unapproved.png` muestra el detalle tras un cierre rechazado (400) **sin ningún mensaje visible**; el `bannerError:true` del arnés no corresponde a un banner de cierre (el único elemento rojo en pantalla es la tarjeta KPI de mortalidad) — se trata como fallo silencioso, coherente con `LotDetailPage.tsx:114-116` (`console.error`).

---

## 1 · Matriz de recorridos críticos

Columnas: Descubribilidad (§8 DISCOVERABILITY/ENTRY/CONTEXT) · Formulario (FORM/DEFAULTS/VALIDATION) · Éxito (ACTION/FEEDBACK/STATE/NEXT STEP, §39) · Fallo (ERROR, §40) · F5/relogin (REFRESH, §11) · Escritorio · Móvil (§41) · ES · EN (§42).

| # | Recorrido | Descubr. | Formulario | Éxito | Fallo | F5/relogin | Escritorio | Móvil | ES | EN | Brechas |
|---|---|---|---|---|---|---|---|---|---|---|---|
| J-01 | Login → primera pantalla | PASS | PASS | PASS | PARTIAL | PARTIAL | PASS | PASS | PASS | PASS | R-212 (C#21), R-220 (C#37, G-26) |
| J-02 | Home (`/`) según rol | FAIL (roles sin `dashboard:read`) | N/A | PARTIAL | PARTIAL | PASS | PARTIAL | PASS | PASS | PARTIAL | R-212 (G-02/N-1), R-216, R-220 (G-10) |
| J-03 | Hub → etapa → tile → asistente → guardar → lista | PARTIAL | PASS | PARTIAL | PASS | PASS | PASS | PARTIAL | PARTIAL | PARTIAL | R-212 (G-20), R-220 (C#14, G-07, G-15, G-19) |
| J-04 | Importación de abuelas (P-01) por hub → aprobación → lote automático | PASS | PARTIAL | PARTIAL | PASS | PASS | PASS | UNKNOWN | PASS | PASS | R-206, R-197 (C#13), C#16 (sin R-id) |
| J-05 | Enviar / reenviar a revisión (detalle de operación) | PARTIAL | N/A | PASS | PASS | PASS | PASS | PARTIAL | PARTIAL | PARTIAL | CF-23 (sin R-id), R-198, R-220 (G-07, G-15) |
| J-06 | Centro de revisión: iniciar / devolver / completar | FAIL | PARTIAL | PARTIAL | PASS | PASS | PARTIAL | N/A (web-only) | PARTIAL | PARTIAL | R-197, R-212, R-220 (C#31, B-29) |
| J-07 | Aprobación individual / por lote | PARTIAL | PASS | PARTIAL | PASS | PASS | PASS | N/A (web-only) | PASS | PASS | R-197 (C#13), R-208, R-220 (C#25, C#35) |
| J-08 | Detalle de lote (información, KPIs, fases, alertas, atajos) | PASS | N/A | FAIL | PARTIAL | PASS | PARTIAL | PASS | PARTIAL | PARTIAL | C#16 (sin R-id), R-191, R-218, R-212, R-220 (C#17, C#23, G-18) |
| J-09 | Recepción de aves en lote autocreado (F-01e) | PASS | PASS | PARTIAL | PASS | PASS | PASS | UNKNOWN | PASS | PASS | C#16, R-211 (latente) |
| J-10 | Registros diarios (mortalidad, alimento, pesaje, vacunación, agua, descarte, medicación) | PASS | PARTIAL | PARTIAL | PASS | PASS | PASS | PASS | PASS | PASS | R-209, R-210 (reevaluar), R-220 (C#29) |
| J-11 | Eventos de ubicación en lote sin galpón (distribución, salida, recolección, inspección de granja) | PASS | FAIL | FAIL | PASS | N/A | FAIL | FAIL | PASS | PARTIAL | **R-190** |
| J-12 | Recepción de reproductoras por navegación (cuadre BR-20) | FAIL | FAIL | FAIL | PASS | N/A | FAIL | FAIL | PASS | PASS | **R-205** |
| J-13 | Transición cría → producción | PASS | PARTIAL | FAIL | FAIL | N/A | FAIL | FAIL | PASS | PASS | **R-191** |
| J-14 | Cierre de lote | PASS | PASS | PARTIAL | FAIL | PASS | PARTIAL | PARTIAL | PASS | PASS | R-192 (C#8), R-220 (C#23) |
| J-15 | Cadena incubadora (P-05) | PASS | FAIL | FAIL | PARTIAL | N/A | FAIL | FAIL | PASS | PASS | **R-194** |
| J-16 | Alta y listado de lotes | PASS | PARTIAL | PARTIAL | PARTIAL | PASS | PASS | PARTIAL (alta web-only) | PARTIAL | FAIL (validación en ES) | R-215 (B-15), R-220 (B-18, B-19, C#17, C#19, C#33, G-09) |
| J-17 | Maestros (20 entidades) | FAIL (19/20 solo por URL) | FAIL (6 estructurales) | PARTIAL | FAIL (pantalla en blanco) | PASS | FAIL | N/A (web-only) | FAIL (etiquetas «Editar/Guardar») | FAIL | **R-196**, **R-215**, G-06 |
| J-18 | Usuarios y roles | PASS | FAIL (edición de usuario) | PARTIAL | PARTIAL | PASS | PARTIAL | N/A | PARTIAL | PARTIAL | **R-195**, R-220 (C#31, G-08, B-28), R-199 (seguridad) |
| J-19 | Acceso por unidad de negocio | PASS | PASS | PASS | PARTIAL | PASS | PASS | N/A | PASS | PASS | R-220 (C#30) |
| J-20 | Reportes (KPI, informe de lote, comparativo SAP) | PARTIAL | N/A | PARTIAL | PARTIAL | PASS | PARTIAL | PARTIAL | PARTIAL | PARTIAL | R-218, R-212 (C#20), R-220 (C#18, G-10, G-14) |
| J-21 | Auditoría | PASS | N/A | FAIL (campos inexistentes) | PARTIAL | PASS | PARTIAL | N/A | FAIL (enums crudos) | FAIL | R-219, R-212 (C#19), R-220 (G-08), P1-12-REOPEN |
| J-22 | Notificaciones (campana) | PASS | N/A | PASS | PASS | PASS | PASS | PARTIAL (panel recortado) | PASS | PASS | R-220 (C#32, R5) |
| J-23 | Perfil / cambio de contraseña | PASS (web) / FAIL (móvil) | PASS | PASS | PARTIAL | PASS | PASS | FAIL (sin enlace) | PASS | PASS | R-215 (B-15), R-220 (G-04) |
| J-24 | SAP (consolidar / exportar / referencias) | PASS | PASS | FAIL (sin refetch; estados inexistentes) | PARTIAL | PASS | PARTIAL | N/A | PARTIAL | PARTIAL | R-217, R-201 (seguridad) |
| J-25 | Evidencias (subir / ver / borrar) | PASS | PASS | FAIL (desaparecen al refrescar) | PASS | FAIL | PASS | PARTIAL (acciones ocultas en táctil) | PASS | PASS | **R-198** |
| J-26 | Trazabilidad generacional (vincular huevos / pollitos) | PARTIAL (botones ocultos sin vínculos) | PARTIAL | PASS | FAIL (React #31) | PASS | PARTIAL | PARTIAL | PASS | PASS | R-215 (B-15), R-220 (B-17, C#17) |
| J-27 | Mis pendientes (`/my-pending`) | FAIL (huérfana) | N/A | PARTIAL | PARTIAL | PASS | FAIL | FAIL | PASS | PASS | R-220 (huérfana, C#26) |

---

## 2 · Evidencia por recorrido

### J-01 · Login → primera pantalla
- Descubribilidad/Formulario/Éxito: `LoginPage.tsx:33-47` (submit → `login()` → `navigate('/')`); [RT] `login-ui: 200`; [L1] `login-ui-admin/approver: 200`, `MOB-login: 200 → /menu/poultry`. Errores con `getErrorMessage` + banner + toast (`LoginPage.tsx:40-44`) — PASS.
- Fallo PARTIAL: `fetchMe` traga el fallo de `/me` (`auth.store.ts:160-163`): toast «Bienvenido» y luego «No tiene permiso» en toda sección (C#37, C#21); R-213 documenta un `/me` 500 real por `EmailStr`.
- F5/relogin PARTIAL: tokens en `sessionStorage` (`auth.store.ts:60-69`) → F5 conserva la sesión en la pestaña; pestaña nueva pide login (diseño). Sin `returnTo` tras login (G-26). Refresh vencido → `forceLogout` silencioso y formulario perdido (`api.ts:64-78`, C#21).
- Móvil: `LoginPage.tsx:53` `max-w-[380px]` (R19 OK). ES/EN: claves `auth.*` existen (F §1.d).

### J-02 · Home según rol
- Admin: `DashboardPage.tsx:93-106` → `/dashboard/admin`; [L1] `PAGE-dashboard` sin claves crudas; **pero** `lots_by_type` llega como `BirdTypeEnum.BREEDER/BROILER/HATCHERY` ([L1] `H5-dashboard-admin`) y la página busca `'broiler'` (`DashboardPage.tsx:255,513`) → tarjetas por etapa en 0 (**R-216**).
- Operador/aprobador (sin `dashboard:read`): `HomeRoute` (`App.tsx:110-114`) renderiza `DashboardPage` sin guarda → `GET /dashboard/admin` 403 ([RT] `httpErrores` op ×1, ap ×1; [L1] approver ×2) → pantalla de error «Permiso requerido: dashboard:read» con «Reintentar» = `window.location.reload()` (`DashboardPage.tsx:130-143`). Es el destino de `LoginPage.tsx:39`, del «Atrás» de raíz del hub (`MenuHubPage.tsx:100`), del icono casa (`Breadcrumbs.tsx:42`) y de `*` → **DISCOVERABILITY FAIL** (G-02 / N-1 → **R-212**).
- Móvil PASS: `HomeRoute` → `/menu/poultry` ([L1] `MOB-login`; `F01-mobile-home.png`: hub con Lotes/Progenitoras/Reproductoras/Incubadora/Engorde y barra inferior).
- EN PARTIAL: `process.grandparent.title` etc. no existen → cabeceras del home móvil en español para EN (`DashboardPage.tsx:155-170`, G-10 → R-220).

### J-03 · Hub → etapa → tile → asistente → guardar → lista
- Navegación: `MenuHubPage.tsx:88-94` → `ProcessStagePage` → `OperationTile.tsx:60-73` (`/operations/new?type=…`) → `OperationFormPage` paso 3 (`OFP:317`). [RT] pasos `R-08-*` 201 ×4 con banner «Registro guardado exitosamente», `formVisible:true`, `pageerrorDelta:0`; [L1] `BO-*` 201 ×10; [L2] `BR-*` 201 ×9.
- Descubribilidad PARTIAL: tiles y línea de tiempo no aplican `operations:create` (`OperationTile.tsx`, `StageTimeline.tsx` sin `useCan`; `LotDetailPage.tsx:228` sí) → un aprobador llega al tile y recibe «No tiene permiso para ver esta sección» ([L1] `GUARD-approver-operations-new`) (G-20 → **R-212**).
- Éxito PARTIAL (§39): tras guardar la respuesta se descarta y se navega a `/operations` a 1,5 s (`OFP:452-455`): sin id, sin enlace al registro ni CTA «enviar a revisión» (C#14); la lista pinta `ev.status` crudo (`OperationListPage.tsx:85`) y el enlace al detalle dice «Editar» (`:89`, `common.edit` = «Editar»/«Edit») (G-07, G-15 → R-220).
- Fallo PASS (§40): `R05-error-ux.png` — 400 BR-01 con banner y toast «Mortalidad (99999) excede el saldo de aves disponibles (49)», formulario intacto, [RT] `pageerror: 0`, `http5xx: []`, `fatal_react: 0` (asistente con `getErrorMessage`, `OFP:456-461`).
- Móvil PARTIAL: flujo completable ([L1] `MOB-*`, `F02-mobile-stage.png`, `F03-mobile-form-saved.png`; [RT] `R-15-movil-overflow-form: 0`, `R09-mobile-form.png`); selects nativos (`MOB-selects: 3`); pero `/operations` (destino tras guardar) no tiene entrada en `MobileNav` y el «Ver historial» es solo web (`ProcessStagePage.tsx:118-123`) (G-19); back nativo de Telegram vuelve al formulario ya enviado (`navigate` sin `replace`, `OFP:455`).
- ES/EN PARTIAL: `R06-en-form.png`/`R07-en-hub.png` y [RT] `R-14-EN {spanish:0, rawKeys:[]}`, [L1] `EN-form {spanishLeft:0}` — sin claves crudas ni restos en el formulario/hub; el estado crudo de la lista y el `detail` del backend en español (G-11) afectan a ambos idiomas.

### J-04 · Importación de abuelas (P-01) por hub
- `R01-import-form.png`; [RT] `R-01-import-ui` (evento 124 creado por UI en la corrida 2, 201; reutilizado) → `R-03-review-ui approve 200` → lote automático **`L-GP-2026-12`** (id 66, `house:null`, `farm:1`) → PASS del camino OD-25 (B) por UI.
- Formulario PARTIAL: `quarantine_end_date` opcional en blanco viaja como `''` (`OFP:1782`; sin limpieza de cadenas en `extra_data`, `OFP:189-207`) → 400 BR-22 «Input should be a valid date or datetime, input is too short» ([L1] `GP-01-grandparent_import: 400`; [L2] `GP2-01a-contrato-fecha-vacia {quarantine_end_date_enviado:""}`; con fecha rellena [L2] `GP2-01: 201`) (**R-206**, B-11).
- Éxito PARTIAL: la respuesta de `approve` se descarta (`ApprovalPanel.tsx:54-58`, `ReviewDetail.tsx:72,77`) → ningún enlace al lote creado (C#13 → R-197); el detalle del lote no muestra población ni saldo tras la recepción ([RT] `lotdetail-poblacion-visible: false`; `R03-transition.png`: «Información: Inicio · Fecha prevista · Tipo · Granja 1 · Galpón —», sin población; `LotDetailPage` ignora `opening_balance` de `LotDetailRead`, `lots/schemas.py:89-91`) (C#16 — **sin R-id en el registro**; se eleva).
- F5 PASS: `AC06-un-solo-lote-nuevo` y `lotes-gp-antes` (7) → +1 en GET fresco.
- Móvil UNKNOWN: la importación no se ejercitó con `view_type=mobile` (el arnés móvil usó `mortality_recording`); la etapa Progenitoras es visible en el hub móvil (`F01-mobile-home.png`).

### J-05 · Enviar / reenviar a revisión
- `OperationDetailPage.tsx:127-145` (`operationsService.submit` → toast → `loadEvent()` en `finally`): [RT] `R-05-submit 200`, `R-06-resubmit-ui 200` (tras devolución), `R-11-resubmit 200` (tras rechazo); [L2] `GP2-02-submit-ui 200`; `BR2-P07-submit 200`. Fallo PASS (toast `getErrorMessage` + relectura).
- Descubribilidad PARTIAL: al detalle se llega por el enlace «Editar» de la lista (etiqueta engañosa), por la campana o por `/my-pending` (huérfana).
- Un registro **devuelto** solo puede reenviarse **sin corregir**: no existe «Editar» ni «Anular» (`OperationDetailPage.tsx:121-145`; `PUT /operations/{id}` y `POST …/cancel` sin consumidor, `operations/router.py:295-327`; [L1] `H7-cancel-ui-control {cancelar:0, editar:0}`) → **CF-23 / CF-24 (MISSING_UI, sin R-id en el registro)**; `CorrectionForm.tsx:72-74` solo corrige `observations` (B-30).
- ES/EN PARTIAL: `event.event_type` y `bm.sex` crudos en el detalle (`OperationDetailPage.tsx:196,221`, G-07).
- Móvil PARTIAL: acciones de evidencia `opacity-0 group-hover:opacity-100` invisibles en táctil (`OperationDetailPage.tsx:287`, R3).

### J-06 · Centro de revisión
- `R04-review-tabs.png`: pestaña «En revisión» seleccionada muestra 11 resultados en estado «Registrado»/«Enviado a Revisión» (la misma cola de pendientes). Causa: `ReviewCenter.tsx:85-96` envía `status`/`operator_id`; `review/router.py:22-33` no los declara; `review/service.py:165-169` fija `REGISTERED|PENDING_REVIEW`. [RT] `R-12-review-tabs-in_review {pending_review:false, in_review:false}`; [L1] `H2-in_review-visible-en-su-pestana: FAIL` — el evento en `in_review` **no aparece en ninguna pestaña** y «Completar/Devolver» (`ReviewCenter.tsx:323-334`, condición `status==='in_review'`) nunca se renderizan → **R-197** (DISCOVERABILITY FAIL: estado huérfano).
- Las acciones sí funcionan desde `ReviewDetail` (`/review/{id}` por URL o icono lupa): [RT] `R-05-return-ui {start:200, return:200}`, `R-06-aprobado {start,complete,approve:200}`. Observación por `prompt()` (`ReviewCenter.tsx:123`) sin validar los 10 caracteres mínimos (`review/schemas.py:101`) → 422 mostrado vía `getErrorMessage` (B-29, C#31 → R-220).
- Rol aprobador: `GET /users?limit=100` 403 ×7 ([RT]) para poblar un filtro que el backend no atiende (**R-212**). Historial de acciones vacío (`ReviewDetail.tsx:44-53` espera `batches[].actions`, C#15 → R-197).
- Móvil N/A: `WebOnlyRoute` redirige a `/` → `/menu/poultry` sin mensaje ([L1] `MOB-review-webonly-redirect`).

### J-07 · Aprobación
- `ApprovalPanel.tsx:52-79` (confirmación, motivo ≥10 validado en cliente); [RT] `R-03-review-ui approve:200`, `R-06-aprobado approve:200`; `R-11-aprobado approve:403` tras `complete` sobre un evento rechazado y reenviado (`POST /approvals/approve` 403, actor `ap`) — **UNKNOWN**: causa no aislada por esta auditoría (posible segregación por actor o estado; requiere sonda dedicada).
- [L1] `BO-aprobaciones-ui {aprobados:0, total:10}` seguido de `BO-close-aprobado: 400 «10 en pending_review»`: con aprobación de un nivel, `/approvals` solo lista `corrected` (`review/service.py:463`) y «Completar» no es alcanzable desde la lista → la aprobación por UI depende de abrir cada `/review/{id}` — coherente con **R-197**.
- Éxito PARTIAL: respuesta descartada (sin enlace al lote creado, C#13); KPIs «Aprobados/Rechazados» siempre 0 (`ApprovalPanel.tsx:146,168`, C#25); sin guarda de doble clic (C#35). Batch exige `review:review` en UI y backend (`ApprovalPanel.tsx:173`; `review/router.py:143-160`) → **R-208**.

### J-08 · Detalle de lote
- `R03-transition.png` / `D01-bo-close-unapproved.png`: tarjeta «Información» con Inicio en ISO completo (`2026-09-13T00:00:00Z`, C#17), Granja/Galpón como ids (`LotDetailPage.tsx:346-347`), sin población ni saldo (C#16); «Últimos Registros» con `event_type`/`status` crudos (`:319,326`, G-07); atajos «Registrar operación» visibles también en lotes cerrados (`:229-243`, C#23); «Vista semanal» nunca aparece (lista sin sublistas, `operations/schemas.py:256-266` → **R-218**); `activePhase?.phase?.name` siempre `undefined` (`:91`; `LotPhaseRead` sin `phase` anidado) → `stageKey` siempre cría para reproductoras/abuelas (C#3 → **R-191**).
- Fallo PARTIAL: operador sin `reports:read` → `/reports/kpis`, `/reports/kpi/ipe/66`, `/reports/kpi/weight-uniformity/66` 403 ×12 cada uno ([RT]) silenciados por `allSettled` (`:44-73`); 403/404/500 del lote ⇒ «Lote no encontrado» (`:66-67,86`, C#19 → **R-212**).
- Móvil PASS: `R08-mobile-lot.png`, [RT] `R-15-movil-overflow-lote: 0`; cabecera sin `wrap` (R11, cosmético). Sin enlace al informe del lote (G-18 → R-220).

### J-09 · Recepción de aves en lote autocreado (F-01e)
- [RT] `R-04-reception-ui: 201` (evento 125; payload con `sap_document_ref: PO-C001-GPR-0001`, `house_id: 1` derivado de la primera fila, `farm_id: 1`, listas hijas `[]`); población exacta: `R-07-poblacion-50` (51 rechazado por BR-01). Contrato canónico verificado (§4 del entregable de formularios).
- Éxito PARTIAL: la población no se refleja en el detalle del lote (C#16). R-211 (BR-17 Σ contra un solo galpón) no se ejercitó (recepción a un único galpón) — latente.
- [L2] `GP2-05…GP2-18: NO_REQUEST` con `zod:["Seleccionar lote..."]`: cascada del arnés (en L2 el botón de aprobación no se localizó, `GP2-03-review-approve-ui: NO_BUTTON`, y no se creó el lote); **no** es evidencia del formulario.

### J-10 · Registros diarios
- [RT] mortalidad/alimento/pesaje/vacunación 201 con `farm_id` derivado del lote; [L1] `BO-*` 201 (agua, descarte, medicación incluidos); [L2] `BR-*` 201. Fallo PASS: `R-13-4xx-seguro` y [L1] `MOB-mortality: 400 «Mortalidad (1) excede el saldo de aves disponibles (0)»` con mensaje claro en móvil.
- Formulario PARTIAL: la etiqueta mostrada es «Peso prom. (g)» (`operations.avgWeight` ES/EN, verificado en `translation.json`; el fallback «(kg)» de `OFP:470,1703` no se renderiza) pero `step="0.001"` y los restos «kg» mantienen la ambigüedad de unidad; [L1] el arnés capturó gramos (`avg_weight: 2400/2200`) — **R-210 se mantiene como riesgo, su severidad debe reevaluarse** (no se confirma captura en kg por UI). `feed_movements.0.sap_order_id` viaja como **id** (`OFP:1033-1040`, B-10 → **R-209**, no ejercitado en runtime).
- Éxito PARTIAL: el detalle no muestra `water_liters`, `chicks_*`, `hatchery_params`… (C#29 → R-220).

### J-11 · Eventos de ubicación en lote sin galpón
- [RT] sobre `L-GP-2026-12` (`house_id=null`): `bird_distribution` → 400 «requiere un galpón asignado» (payload con `farm_id:1`, sin `house_id`); `bird_exit` → 400 ídem; `egg_collection` → 400 ídem; `farm_inspection` → 400 «requiere una granja asignada» (payload con `house_id:1`, sin `farm_id`: el selector de granja quedó vacío y la UI no lo exige antes de enviar — `R05-error-ux.png` muestra «Granjas: Seleccionar granja…» vacío incluso con lote elegido). [L2] `GP2-12-farm_inspection: 400` ídem. Control: lotes con galpón → 201 ([L1] `BO-bird_distribution`, `BO-bird_exit`; [L2] `BR2-egg_collection`).
- Causa: `OFP:387-394` deriva `house_id` de la primera fila solo en `bird_reception` (F-01e) y del lote en el resto; `validators.py:822-839` exige granja **y** galpón en 10 tipos. Sin selector «Galpón del evento» (B-04) → **R-190 (P1)**. Fallo PASS (render seguro); Éxito FAIL (proceso no completable en lotes OD-25 por UI, §10).

### J-12 · Recepción de reproductoras por navegación (BR-20)
- [L2] `BR2-hub-campo-cuadre-visible: 0` → `BR2-01-bird_reception-por-hub: 400` BR-20 «falta: received_total, dead_on_arrival, rejected_on_arrival» (`P2-B01-br-reception-por-hub.png`) frente a `BR2-asistente-campo-cuadre-visible: 1` → `BR2-02: 201` por URL directa `/operations/new` (`P2-B02-br-reception-asistente.png`); [L1] `BR-EXCEPCION` (`[name="received_total"]` inexistente vía hub). `BR2-entrada-asistente-sin-type {enlaces_operations_new:0}`: ningún enlace del producto abre el asistente sin `?type=`.
- Causa: el bloque de cuadre depende de `stage === 'breeder_rearing'` (`OFP:666-682`) y `stage` solo lo fija el paso 1 (`OFP:316-319`); con `prefillType` el asistente arranca en paso 3 con `stage=null` (`OFP:317`). Recurrencia de «funciona solo por URL directa» (§19) → **R-205 (P1)**.

### J-13 · Transición cría → producción
- [RT] `R-09-transicion-ui`: `POST /lots/66/phases {phase_code:'production', start_date, start_population_male:0, start_population_female:0}` → 422 `lot_id`/`phase_id` Field required; `toasts: []`; `R03-transition.png`: botón «Iniciar Producción» sigue visible, sin mensaje. [L2] `BR2-transicion-ui: 422`. Código: `LotDetailPage.tsx:121-138` (`phase_code`, sin `lot_id`; `catch → console.error`); `lots/schemas.py:98-109`. **R-191 (P1)**: acción muerta y fallo silencioso (viola §40).

### J-14 · Cierre de lote
- [L1] `BO-close-sin-aprobar {status:400, toasts:[]}` y `consoleError` «No se puede cerrar el lote: 10 registro(s) sin aprobar…»; `D01-bo-close-unapproved.png`: sin banner, sin toast, botón «Cerrar Lote» activo, estado «Activo». Código: `LotDetailPage.tsx:107-119` (modal cerrado antes del POST; `console.error`). Es el AC04 de **R-192** (C#8). Con registros aprobados el cierre funciona (histórico R-153/GA-REM-029; [L1] `H8-cierre-lote-con-reverso` devuelve el motivo BR «sin pesaje» por API).
- Éxito PARTIAL: `closeResult` + estado optimista; tiles siguen visibles (C#23).

### J-15 · Cadena incubadora (P-05)
- [L2] `HAT2-01-hatchery_inspection: 201`; `HAT2-02-egg_reception_hatchery: 422 egg_storage_records.0.arrival_date Field required` (B-03); `HAT2-02b` (sin almacenamiento) → 400 «requiere una granja asignada» (B-01: `farm_id` forzado a `undefined` en etapa incubadora, `OFP:274-278,438`); `HAT2-02-sonda-sin-storage` (API con granja) → 201 pero `HAT2-02-saldo-tras-recepcion-ui` → BR-03 «disponibles en incubadora (0)» (B-02: la UI escribe la cantidad en `egg_storage_records` y el saldo lee `egg_movements[fertile]`); `HAT2-07-birth_registration` → `NO_REQUEST` con y sin dosis (B-05 parcialmente confirmado: sin petición; la causa exacta del bloqueo con dosis no se aisló — UNKNOWN); `HAT2-08-chick_dispatch: 400 «requiere una granja asignada»` (B-01). PNG `P2-C01-hat-egg-reception-form.png`, `P2-C02-hat-birth-form.png`. → **R-194 (P1)**: la cadena P-05 no es completable por UI (§10).

### J-16 · Alta y listado de lotes
- [L1] `BR-00-lote-ui: 201` (`curvaAviso:1`), `HAT-00-lote-ui: 201`; `LotFormPage.tsx:116-139` navega al detalle (GET fresco) — PASS.
- Formulario PARTIAL: `sap_reference` viaja y se descarta en silencio (B-18); `farm_id` obligatorio en UI aunque opcional en backend (B-19). Fallo PARTIAL: `toast.error(detail)` crudo (`LotFormPage.tsx:137`) → React #31 en cualquier 422 (B-15 → **R-215**). Lista: `console.error` (`LotListPage.tsx:32-33`, C#19), filtro en cliente sobre 100 (C#33), `start_date` ISO (C#17).
- EN FAIL: mensajes zod «Mínimo 2 caracteres»/«Requerido» fijos en español (`LotFormPage.tsx:21-23`, G-09 → R-220).

### J-17 · Maestros
- Descubribilidad FAIL: el único ítem «Maestros» redirige a `/masters/farms` (`App.tsx:220`) y `MasterListPage` no ofrece cambio de entidad; 19 de las 20 entidades de `App.tsx:135-165` solo por URL escrita (G-01; alcance de **R-196**). (`/masters/genetic-lines/:id/weight-curves` cuelga de una de ellas, `App.tsx:242-245`.)
- Formulario FAIL: alta de `hatcheries`/`houses` envía `{}` ([L1] `MAS-hatchery-create-ui: 422 company_id/name`, `H4-masters-house-create-ui: 422 farm_id/name`; `MAS-form-fields [null,null]`) porque el formulario genérico solo renderiza las columnas de listado (`MasterListPage.tsx:193-200`) sin selector de padre; `capacity:''` → 422 (B-14) → **R-196 (P1)**.
- Fallo FAIL: `setFormError(detail)` crudo (`MasterListPage.tsx:99,201-205`) → `pageerror` «Objects are not valid as a React child» ×2 ([L1]), `H04-masters-house-create.png` = **pantalla en blanco** sin recuperación (sin `ErrorBoundary`, grep vacío) → **R-215**. Borrado fallido: `console.error` con el modal abierto (`:114`).
- ES/EN FAIL: 21 columnas/labels con `labelKey: 'common.edit'`/`'common.save'` (`App.tsx:136-165` → `MasterListPage.tsx:122,196`) muestran «Editar»/«Guardar» («Edit»/«Save») como nombre de atributo (G-06).

### J-18 · Usuarios y roles
- Carga ejemplar: `UsersPage.tsx:37-63` distingue prohibido/error/ok. [L1] `PAGE-users`, `PAGE-roles` sin claves crudas.
- Formulario FAIL: edición envía `username` y `company_id` a `PUT /users/{id}` (`UsersPage.tsx:68-79`) con `UserUpdate extra="forbid"` (`auth/schemas.py:65-85`) → 422 en toda edición; `alert(detail)` → «[object Object]» (`:85`) → **R-195 (P1)**. [L1] `H3-users-edit-boton: no visible` (control no localizado por el arnés; UNKNOWN si es de visibilidad o de selector).
- Roles: matriz con `roles.actions/modules` sin claves (`RolesPage.tsx:205,213`, G-08); `alert/confirm` nativos (C#31). Seguridad: R-199 (comodín en rol de inquilino) documentado en `GA_CLAUDE_SECURITY_FINAL_AUDIT.md`.

### J-19 · Acceso por unidad
- `UnitAccessPage.tsx:50-79,115-159` carga con banner+reintento, confirmaciones, refetch tras éxito y fallo; contrato GA-FE-02 exacto (B §7). [L1] `OD23-grants-antes` (concesiones efectivas), `E03-unit-access.png`; `ADM-EXCEPCION` = selector del arnés (`li … Deshabilitar|Apagar`) no encontrado — UNKNOWN (no se pudo ejercitar apagar/encender por UI). Fallo PARTIAL: `detail` del 403/409 (segregación, unidad apagada) sustituido por mensaje genérico (`:124,138,153`, C#30).

### J-20 · Reportes
- `ReportsPage.tsx:13` `lotId=2` codificado y enlace `/reports/lot/2` (`:193`); `.catch(() => {})` (`:17,33`) → empresa sin lote 2 = tarjetas vacías sin mensaje (C#18); gráficos planos porque la lista no trae sublistas (C#4 → **R-218**); `LotReportPage` con 403 → toast y «Cargando…» eterno (`:64`, C#20 → R-212); `LotDetailPage` no enlaza su informe (G-18). [L1] `PAGE-reports`, `PAGE-sap-comparison` sin claves crudas; `BO-reporte-lote`/`BO-ipe` 200 por API. EN: 9 claves `kpi.*`/`reports.onlyApproved*` ausentes → español fijo (G-10); cabeceras de exportación en español (G-14).

### J-21 · Auditoría
- `AuditPage.tsx:90,94-95` usa `user_name/old_value/new_value` inexistentes en `AuditLogRead` (`audit/schemas.py:8-30`) → usuario como id y pestaña «Correcciones» sin diff (C#11 → **R-219**); `.catch(() => {})` (`:74`, C#19); acciones/módulos crudos (`:150,162,216`, G-08). [L1] `E02-audit.png`, `H6-audit-timeline` (duplicidad `created ×2` → **P1-12-REOPEN**, backend).

### J-22 · Notificaciones
- `NotificationBell.tsx:43-104`: contador, bandeja con error explícito ≠ vacía, marcar leída y navegar (`notifications.ts:56-61` solo `operational_event`). [RT] `R-05-notificacion-operador {unread:1}` tras la devolución. Móvil PARTIAL: panel `w-[min(22rem,calc(100vw-2rem))]` anclado a la campana → recortado ~44 px a 390 px (R5); avisos de mortalidad/peso/lote sin detalle ni destino (C#32 → R-220).

### J-23 · Perfil / contraseña
- `ProfilePage.tsx:18-40` → `POST /users/{id}/password`; mensaje de éxito/error. [L1] `PAGE-profile`. Fallo PARTIAL: `setMessage(detail)` crudo (`:38,70`) → React #31 ante 422 estructurado (B-15 → R-215). Móvil FAIL: ruta permitida sin ningún enlace (`Header.tsx:158-200` móvil: marca, empresa, campana, idioma; sin perfil ni logout) (G-04 → R-220).

### J-24 · SAP
- `SapManagerPage.tsx:37-67`: filtra por `pending/draft/sent/error` mientras el backend usa `prepared/sending/confirmed/failed/retrying` (`sap/models.py:40-52`) → «Pendientes»/«Errores» siempre 0; sin refetch tras consolidar/exportar; sin UI para `/sap/retry` ni `/sap/references/import` (C#10, C#22, C#24 → **R-217**); `delivers_to_sap` ignorado (adaptador simulado mostrado como conectado). [L1] `PAGE-sap` sin claves crudas. Móvil N/A.

### J-25 · Evidencias
- Subida/borrado con toast y estado local (`OperationDetailPage.tsx:76-114`); **tras F5 la lista vuelve vacía** porque el router descarta `evidences` (`operations/router.py:282-292` `pop("evidences")`) y la página lee `data.evidences || []` (`:66`) → viola §11 (estado persistido ≠ UI) → **R-198**. Adjuntar permitido en cualquier estado (`:297,327`). Móvil PARTIAL: acciones ocultas en táctil (`:287`).

### J-26 · Trazabilidad
- `TraceabilityTree.tsx:82-118` vincula y relee (`load()`); botones «Vincular…» solo si `hasData` (`:160-166`) → un lote sin vínculos no puede crear el primero desde UI; `hatchery_lot_id` tecleado como id y `|| null` → 422 (B-17); `setLinkError(detail)` crudo (`:95,114,347,389`) → React #31 (B-15 → R-215); fechas con locale del navegador (C#17).

### J-27 · Mis pendientes
- `App.tsx:262` es la única referencia a `/my-pending` (grep en `src`: sin `Link`/`navigate`); `F04-mobile-my-pending.png` (por URL) muestra «No tienes registros pendientes» con barra inferior sin la entrada; filtra `draft,registered` (devueltos/rechazados excluidos, `MyPendingPage.tsx:34`); `op.lot?.name` inexistente (`:101`, C#26) → huérfana (R-220).

---

## 3 · Resumen por dimensión (§8)

| Dimensión | Veredicto | Justificación (evidencia) |
|---|---|---|
| Discoverability | **FAIL** | R-205 (el formulario correcto de recepción de reproductoras solo por URL directa, [L2] `BR2-*`); R-196/G-01 (19/20 maestros solo por URL); R-212/G-02 (home = pantalla de error para roles sin `dashboard:read`, [RT] 403 `/dashboard/admin`); R-197 (estado `in_review` sin pestaña, `R04-review-tabs.png`); R-220 (`/my-pending` huérfana; `/reports/lot/:id` casi huérfana; móvil sin perfil/logout) |
| Forms | **FAIL** | R-190 ([RT] 400 BR-08 ×4), R-194 ([L2] `HAT2-*`), R-195 (`UsersPage.tsx:76-79` vs `UserUpdate`), R-196 ([L1] `{}` → 422), R-205 ([L2] 400 BR-20), R-191 ([RT] 422); no bloqueantes R-206 ([L1]/[L2] fecha `''`), R-209, R-210 (reevaluar), R-211 |
| Success states (§39) | **FAIL** | Población no reflejada tras recepción (C#16, `R03-transition.png`, `lotdetail-poblacion-visible:false`); lote creado sin enlace tras aprobar (C#13); guardado sin id/CTA (C#14); evidencias desaparecen al refrescar (R-198); SAP sin refetch (R-217); tarjetas del panel en 0 (R-216) |
| Failure states (§40) | **FAIL** | Asistente PASS (`R05-error-ux.png`, 0 pageerror, 0×5xx); pero 422 silencioso en transición (R-191, `toasts:[]`), 400 silencioso en cierre (R-192 C#8, `D01-bo-close-unapproved.png`), pantalla en blanco en maestros (R-215, `H04-masters-house-create.png`) |
| Error handling (§14) | **FAIL** | React #31 ×2 y sin `ErrorBoundary` (R-215); denegación mostrada como vacío/«no encontrado» en 9 pantallas y carga eterna en 2 (C#19/C#20 → R-212); logout silencioso con pérdida de formulario (C#21); `[object Object]` en `alert` (R-195) |
| Desktop | **PARTIAL** | Recorridos P-01/P-02 por UI en verde para lotes con galpón ([RT] 12 PASS, 0 fatales); bloqueados J-11/J-12/J-13/J-15/J-17/J-18; usuario web `<1024px` sin navegación ni logout (F R1 → R-220) |
| Mobile (§41) | **PARTIAL** | Flujo crítico completable y sin desbordamiento ([RT] `R-15-*: 0`, [L1] `MOB-overflow-*: 0`, selects nativos, mensaje 400 claro); sin logout ni perfil (`Header.tsx:158-200`), `/my-pending` inalcanzable, evidencias ocultas en táctil, `WebOnlyRoute` redirige sin mensaje; mismos bloqueos funcionales que escritorio |
| ES | **PARTIAL** | Sin claves crudas ([L1] `PAGE-*` `rawKeys:[]`); enumerados crudos en lista/detalle/revisión/detalle de lote (G-07), «Editar/Guardar» como nombre de atributo en 20 maestros (G-06), `EQUIPMENT_TYPES` y cabeceras de exportación fijas (G-14), namespaces `audit.*`/`roles.*` vacíos (G-08) |
| EN | **PARTIAL** | 0 restos en español y 0 claves crudas en hub/formulario ([RT] `R-14-EN`, `R06/R07.png`; [L1] `EN-hub`/`EN-form`, `G01/G02.png`); `detail` del backend siempre en español + 422 Pydantic en inglés (G-11); 15 claves ausentes con fallback español (G-10); validación de alta de lote en español (G-09); mismos enumerados crudos |

**Veredicto global UI/UX funcional: FAIL** — cinco recorridos requeridos no son completables por la interfaz normal (§10) y tres fallos críticos son silenciosos o dejan la aplicación en blanco (§40).

---

## 4 · Brechas UI/UX

### 4.1 Bloqueantes (según el registro canónico)
| Id | Clase §9 | Recorridos | Estado en runtime |
|---|---|---|---|
| **R-190** | FRONTEND_BACKEND_INTEGRATION_GAP | J-11 | Confirmado [RT] (4 × 400 BR-08) |
| **R-191** | FUNCTIONAL_UI_GAP + ERROR_HANDLING_GAP | J-08, J-13 | Confirmado [RT] (422 silencioso) y [L2] |
| **R-192** | ERROR_HANDLING_GAP (AC04: motivo del 400 visible) | J-14 | Confirmado [L1] (400 sin feedback, `D01`) |
| **R-194** | FRONTEND_BACKEND_INTEGRATION_GAP | J-15 | Confirmado [L2] (`HAT2-02/02b/08`, saldo BR-03) |
| **R-195** | FRONTEND_BACKEND_INTEGRATION_GAP + ERROR_HANDLING_GAP | J-18 | Por código; [L1] control no localizado (UNKNOWN) |
| **R-196** | FUNCTIONAL_UI_GAP + DISCOVERABILITY_GAP + I18N_GAP (G-06) | J-17 | Confirmado [L1] (`{}` → 422 ×2) |
| **R-205** | DISCOVERABILITY_GAP + FUNCTIONAL_UI_GAP | J-12 | Confirmado [L2] (hub 400 / URL directa 201) |
| **R-197** | STATE_FEEDBACK_GAP + DISCOVERABILITY_GAP | J-06, J-07 | Confirmado [RT] `R-12`, [L1] `H2-*`, `R04.png` |
| **R-198** | STATE_FEEDBACK_GAP (§11) | J-25 | Por código (`router.py:282-292`); no ejercitado F5 (UNKNOWN runtime) |
| **R-208** | acción/autoridad (ver entregable de navegación) | J-07 | Por código |
| **R-209** | FRONTEND_BACKEND_INTEGRATION_GAP | J-10 (salida de aves, alimento) | Por código; no ejercitado |
| **R-210** | FRONTEND_BACKEND_INTEGRATION_GAP (**severidad a reevaluar**: la etiqueta renderizada es «(g)») | J-10 | Por código; [L1] captura en gramos |
| **R-211** | regla BE vs estructura UI | J-09 | Latente; no ejercitado |
| **R-215** | ERROR_HANDLING_GAP | J-16, J-17, J-23, J-26 | Confirmado [L1] (`pageerror ×2`, `H04.png` en blanco) |

### 4.2 No bloqueantes (materiales; con paquete compacto)
R-206 (J-04, fecha opcional `''`), R-212 (J-02, J-03, J-06, J-08, J-20, J-21: UI no consciente del permiso; home sin `dashboard:read`), R-216 (J-02), R-217 (J-24), R-218 (J-08, J-20), R-219 (J-21), R-220 (residuales: `/my-pending`, móvil sin logout/perfil, web `<1024px`, evidencias ocultas en táctil, enumerados crudos, fechas ISO/locale, «Editar» en lista, C#14/C#23/C#25/C#26/C#29/C#31/C#32/C#35, G-09/G-10/G-14).

### 4.3 Hallazgos sin identificador en el registro (se elevan al coordinador; no se asigna id aquí)
| Hallazgo | Clase §9 | Evidencia |
|---|---|---|
| C#16 · el detalle de lote no muestra población/saldo (`opening_balance` ignorado) tras la recepción — §39 «balance updates» | STATE_FEEDBACK_GAP | `LotDetailPage.tsx:340-347`; `lots/schemas.py:89-91`; [RT] `lotdetail-poblacion-visible:false`; `R03-transition.png` |
| CF-23 / CF-24 · editar / anular una operación devuelta o registrada sin superficie (C#5) | FUNCTIONAL_UI_GAP (§10) | `operations/router.py:295-327`; [L1] `H7 {cancelar:0, editar:0}` |
| CF-32 · activación manual con saldo de apertura (P-11) sin superficie | FUNCTIONAL_UI_GAP (§10) | `lots/router.py:99-119`; `lots.service.ts:54-55` sin llamadores |
| CF-33 · edición de lote (`PUT /lots/{id}`) sin superficie | FUNCTIONAL_UI_GAP | `lots/router.py:69-77` |
| CF-63 · reactivar maestro (`is_active`) sin superficie (B-36) | FUNCTIONAL_UI_GAP | `MasterListPage.tsx:193-200` |

### 4.4 Clasificación §9 de los hallazgos menores (backlog, P3)
UX_PREFERENCE/UX_ENHANCEMENT: diálogos nativos (`alert/confirm/prompt` ×13, C#31), `window.location.reload()` como reintento (`DashboardPage.tsx:136`), objetivos táctiles <44 px (R13), `select` sin chevron en móvil (R15), `inputMode` ausente (R14). ACCESSIBILITY_GAP: observaciones truncadas sin `title` (`ReviewDetail.tsx:112`, R6), `alt="preview"` (`OperationDetailPage.tsx:367`), checkboxes nativos en matriz de permisos (`RolesPage.tsx:217`). RESPONSIVE_GAP cosméticos: R7–R12.

---

## 5 · UNKNOWN (no verificable en esta auditoría)
- Importación y cadena incubadora con `view_type=mobile` (no ejercitadas; el arnés móvil cubrió home, hub, lotes, mortalidad y redirección web-only).
- Causa del `POST /approvals/approve` 403 en `R-11-aprobado` (actor `ap`, evento rechazado→reenviado→completado).
- Visibilidad real del control «Editar» de usuarios ([L1] `H3-users-edit-boton: no visible`: selector del arnés vs. gate de UI).
- Apagar/encender unidad por UI ([L1] `ADM-EXCEPCION`: selector no encontrado).
- `birth_registration` con dosis rellena ([L2] `HAT2-07b: NO_REQUEST`): el bloqueo sin dosis coincide con B-05, el bloqueo con dosis no se aisló.
- Relogin explícito (cerrar sesión → volver a entrar → mismo estado) no se ejercitó; el análisis de F5 se apoya en `auth.store.ts:60-69,100` y `App.tsx:177-181` (C §3.1) y en las relecturas por GET fresco de los recorridos [RT].

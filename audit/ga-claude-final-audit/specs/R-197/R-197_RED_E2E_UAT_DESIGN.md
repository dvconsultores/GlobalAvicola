# R-197 · DISEÑO RED · E2E RUNTIME · UAT

Fecha: 2026-09-13 · Regla: una prueba RED debe fallar **por la causa exacta** (estado no filtrado, ruta inexistente, petición indebida), nunca por autenticación, fixture o permiso (GA-REM-032 §9). Sensibilidad (GA-REM-016 AC13) tras el commit de implementación, desde la raíz del repo.

## 1 · RED backend — `backend/tests/test_r197_review_queue_contract.py`

Fixture `esc` (patrón `test_review_decision_concurrency.py` / `test_internal_reversal.py`): empresa A (unidad `broiler` ON) y B; usuarios A: `operador` (`operations:create/read`), `supervisor` (`review:read`, `review:review`), `aprobador` (`review:read`, `approvals:approve/reject`), `lector` (`operations:read` sin `review:read`); B: `supervisor_b`. Eventos en A (lote con saldo): `e_reg` (`REGISTERED`), `e_pend` (`PENDING_REVIEW`, registrado por `operador`), `e_rev` (`IN_REVIEW`), `e_ret` (`RETURNED`), `e_cor` (`CORRECTED`), `e_apr` (`APPROVED`), `e_rej` (`REJECTED`), `e_con` (`CONSOLIDATED`); `e_pend2` registrado por `operador2`. Cliente `http_client` (`raise_app_exceptions=False`).

| Test | Pasos | Aserción que **falla hoy** |
|---|---|---|
| `test_r197_01_status_in_review_devuelve_solo_in_review` | supervisor `GET /review/pending?status=in_review` | `{e['id'] for e in events} == {e_rev}` — hoy `{e_reg, e_pend, e_pend2}` |
| `test_r197_02_sin_status_conserva_el_defecto` (CTRL) | `GET /review/pending` | `== {e_reg, e_pend, e_pend2}` y `total == 3` |
| `test_r197_03_status_invalido_es_422` | `?status=foo` | `status_code == 422` — hoy 200 |
| `test_r197_04_registered_by_id_filtra` | `?registered_by_id=<operador2>` | `== {e_pend2}` — hoy 3 filas |
| `test_r197_04b_status_multiple` | `?status=returned,rejected` | `== {e_ret, e_rej}` |
| `test_r197_05_acciones_por_evento_incluyen_las_individuales` | supervisor: `start` sobre `e_pend`, `return` con observación; luego `GET /review/events/{e_pend}/actions` | `status_code == 200` y `[a['action_type'] for a in body] == ['started_review','returned']` — hoy 404 (ruta inexistente) |
| `test_r197_06_acciones_de_evento_ajeno_404` | `supervisor_b` `GET /review/events/{e_pend}/actions` | `404` **y** control: supervisor A ⇒ 200 (mismo sujeto/misma consulta; sin Super Admin como negativo) |
| `test_r197_07_acciones_sin_review_read_403` | `lector` | `403` con `detail` «Permiso requerido: review:read» |
| `test_r197_08_approve_devuelve_lot_id_del_lote_creado` (CTRL) | aprobador aprueba `grandparent_import` sin lote (fixture R-153) | `body['lot_id'] is not None` (verde hoy; protege AC14) |

Sensibilidad (post-C2): S1 retirar el filtro `status` en el servicio ⇒ `01`, `04b` rojas; S2 retirar la validación ⇒ `03` roja; S3 quitar el predicado de empresa en `listar_acciones` ⇒ `06` roja con escritura observada; S4 cambiar el permiso de la ruta a `operations:read` ⇒ `07` roja.

## 2 · RED frontend (vitest/jsdom)

Convenciones de `gaFe04.reviewGates.test.tsx` y `f01.errorRendering.test.tsx`: mock de `services/api`, `react-i18next` (`t(k,f) => f ?? k`), `useAuthStore.setState`, `ToastProvider` real cuando se afirma sobre toasts.

### 2.1 `frontend/src/pages/review/__tests__/r197.reviewQueue.test.tsx`

| Caso | Sesión | Mock | Aserción que **falla hoy** |
|---|---|---|---|
| cada pestaña consulta su estado | `review:read`, `review:review` | `get` captura URL | al pulsar «Corregidos» la URL contiene `status=corrected`; «Rechazados» ⇒ `status=rejected` — hoy no existen esas pestañas |
| `in_review` muestra Completar/Devolver | ídem | `/review/pending` con `status=in_review` ⇒ `[{id:31,status:'in_review',…}]` | botones «Completar» y «Devolver» presentes (verde hoy si el mock respeta `status`: se mantiene como **control de contrato**; la RED real es backend `01`) |
| devolver corto no envía | ídem | — | escribir 5 caracteres en el modal ⇒ `post` **no** llamado; escribir 12 ⇒ `post('/review/return', {event_id:31, observations})` — hoy usa `prompt` (no existe modal) |
| sin `users:read` | `review:read` sólo | `get` espía | `get` **nunca** llamado con `/users` y el selector «Operador» ausente — hoy `ReviewCenter.tsx:109` |
| con `users:read` | + `users:read` | `/users` ⇒ `[{id:5,username:'op'}]` | selector presente; al elegir ⇒ URL contiene `registered_by_id=5` — hoy `operator_id` |
| 403 en carga | `review:read` | `get('/review/pending')` rechaza `{response:{status:403,data:{detail:'Permiso requerido: review:read'}}}` | texto `review.noPermissionQueue` visible y «Sin resultados» ausente |
| lote creado tras Completar | `review:review` | `post('/review/complete')` ⇒ `{id:31, status:'approved', lot_id:66, event_type:'grandparent_import'}` sobre fila con `lot_id:null` | `Link` con `href="/lots/66"` visible |
| guard: sin diálogos nativos | — | lectura de fuente (`fs.readFileSync`) de `ReviewCenter.tsx`, `ReviewDetail.tsx`, `CorrectionForm.tsx` | `/\b(prompt|alert|confirm)\(/` ⇒ 0 coincidencias — hoy 5 |

### 2.2 `frontend/src/pages/review/__tests__/r197.reviewDetailHistory.test.tsx`

| Caso | Aserción que **falla hoy** |
|---|---|
| historial por evento | `get` llamado con `/review/events/31/actions`; renderiza `started_review`, `returned`, `approved` — hoy llama `/review/batches?limit=50` |
| tras completar recarga | `post('/review/complete')` ⇒ evento `approved`; `get('/operations/31')` llamado 2 veces y **no** hay navegación a `/review` (MemoryRouter con `location` observada) |
| enlace al lote | respuesta con `lot_id:66` ⇒ `href="/lots/66"` |
| badge i18n | con `status:'in_review'` el texto es `status.in_review` (mock `t`), no `in_review` crudo |
| validación inline | pulsar «Devolver» sin observación ⇒ mensaje `review.obsMinLength` visible y `post` no llamado; `window.alert` no invocado (spy) |

### 2.3 `frontend/src/pages/approvals/__tests__/r197.approvalResult.test.tsx`

| Caso | Aserción que **falla hoy** |
|---|---|
| enlace al lote tras aprobar | `post('/approvals/approve')` ⇒ `{…, lot_id: 66}` sobre fila `lot_id:null` ⇒ `href="/lots/66"` |
| kpis | no se renderiza `review.approvedToday` ni `review.rejectedToday`; «Pendientes» = `total` del mock |
| doble clic | dos clics en Confirmar ⇒ `post` llamado **1** vez |

## 3 · E2E runtime — `scripts_e2e_r197.mjs`

Patrón `scripts_e2e_f01_retry.mjs`: modos `calibrate` (aborta POST) / `live`; journal `{pasos, posts, pageerror, consoleError, httpErrores, asserts, ids, fatal_react, http5xx}`; PNG por paso. Entorno: pila local (`local_stack.sh`, semillas `seeds.test_seeds` + usuarios para roles canónicos `Supervisor Avícola` y `Aprobador`, C-12), empresa 1 con `approval_levels` = 1 y = 2 (dos corridas).

| Paso | Actor | Acción UI | Aserción |
|---|---|---|---|
| E2E-01 | operador | registra `feed_registration` en lote con saldo y «Enviar a revisión» | `pending_review`; `pageerror 0` |
| E2E-02 | supervisor | `/review` «Pendientes» contiene el id; sin `GET /users` 403 en `httpErrores` (rol sin `users:read`) | `H2-pendientes: true`; `users403: 0` |
| E2E-03 | supervisor | «Iniciar» → pestaña «En revisión» contiene el id con «Completar»/«Devolver» | `in_review-visible: true` (hoy `false`, `R-12`) |
| E2E-04 | supervisor | «Devolver» (modal; 5 caracteres rechazados, 12 aceptados) → «Devueltos» contiene el id | POST 200; pestaña |
| E2E-05 | operador | detalle → «Reenviar a revisión» → supervisor «Pendientes» lo muestra | — |
| E2E-06 | supervisor | Iniciar → Completar (nivel 1) → «Aprobados» contiene el id; (nivel 2) → «Corregidos» lo contiene | — |
| E2E-07 | supervisor | `/review/{id}` historial ≥ 4 acciones (`started_review, returned, started_review, corrected/approved`) | conteo exacto |
| E2E-08 | aprobador | (nivel 2) `/approvals` aprueba; para `grandparent_import` sin lote (fixture UAT-09 local) el toast enlaza a `/lots/{id}` y el lote existe (`GET /lots/{id}` 200) | `lot_link: true` |
| E2E-09 | aprobador | `/review` pestaña «Aprobados» y «Consolidados» (tras `POST /sap/consolidate` por API) muestran los estados | — |
| E2E-10 | todos | `fatal_react == 0`, `http5xx == []`, capturas 1280×800 y 390×844 | cierre |

Sonda de contrato en nube (post-despliegue, sin UI): `GET /review/pending?status=in_review` con actor UAT-09 aprobador ⇒ sólo `in_review`; `GET /review/events/{id}/actions` ⇒ 200.

## 4 · UAT del propietario (runtime nube, tras C3)

| UAT | Guion | Resultado esperado |
|---|---|---|
| UAT-R197-01 | Como supervisor: abrir Revisión, cambiar de pestaña | cada pestaña cambia la lista y el contador |
| UAT-R197-02 | Iniciar un pendiente | aparece en «En revisión» con Completar/Devolver |
| UAT-R197-03 | Devolver con observación | modal exige ≥ 10; el registro pasa a «Devueltos»; el operador lo ve devuelto con la observación |
| UAT-R197-04 | Completar la revisión | pasa a «Corregidos» (2 niveles) o «Aprobados» (1 nivel) |
| UAT-R197-05 | Aprobar una importación de abuelas | toast «Lote creado» con enlace; el enlace abre el lote |
| UAT-R197-06 | Abrir el detalle de un registro decidido | historial completo de acciones con fecha y observaciones |

Criterio de repetición: 6/6 en verde, 0 errores fatales en consola, ninguna petición 403 a `/users` en la sesión del aprobador.

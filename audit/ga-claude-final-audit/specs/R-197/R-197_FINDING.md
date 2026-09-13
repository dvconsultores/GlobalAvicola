# R-197 · HALLAZGO — CENTRO DE REVISIÓN: PESTAÑAS/FILTROS MUERTOS, `in_review` HUÉRFANO, HISTORIAL VACÍO, RESPUESTA DE APROBACIÓN DESCARTADA

| Campo | Valor |
|---|---|
| **ID canónico** | **R-197** (nuevo; asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`, brecha G-08) |
| **Fecha / HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) · runtime `https://avicola.globaldv.net` (bundle `index-DDCcWL76.js`) |
| **Clase (§9)** | `RESPONSE_CONTRACT` · `BROKEN_FLOW` · `STATE_REFRESH` |
| **Prioridad** | **P2** · **Bloquea SAP: SÍ** (P-07 no es operable por interfaz más allá de «Iniciar») |
| **Proceso** | P-07 Revisión → Corrección → Aprobación (`docs/12-approval-workflow.md §4, §7`) |
| **Superficies** | `frontend/src/pages/review/ReviewCenter.tsx` · `ReviewDetail.tsx` · `frontend/src/pages/approvals/ApprovalPanel.tsx` · `frontend/src/services/review.service.ts` · `frontend/src/data/navigationConfig.ts:176-178` · `backend/app/review/router.py` · `backend/app/review/service.py` · `backend/app/review/schemas.py` |
| **Estado** | `SPEC_READY` · sin implementación (producto intocado) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-197/` (6 ficheros) |
| **Vecinos** | R-212 (UI no consciente del permiso; `/users` 403) · R-208 (permisos de lote) · R-207 (contrapartidas en la bandeja) · R-220 C-26/C-27/C-31 (residuales) · R-153/OD-25 (lote creado al aprobar) · R-166 (concurrencia de decisiones) · OD-17 (rechazo no terminal) |

## 1 · Qué se observó

1. **Pestañas y filtros muertos.** `ReviewCenter.tsx:33-39` declara cinco pestañas (`pending_review`, `in_review`, `returned`, `approved`, `consolidated`) y `:85-96` envía `status` (`:88`) y `operator_id` (`:95`) a `GET /review/pending`. El router `review/router.py:22-33` **no declara** ninguno de los dos (FastAPI los descarta en silencio) y el servicio `review/service.py:165-174` fija `status IN (registered, pending_review)` (`:168`, `:173`). Las cinco pestañas —y las entradas de menú `/review?status=approved|returned` (`navigationConfig.ts:177-178`)— devuelven la misma lista.
2. **`in_review` huérfano.** Tras «Iniciar» (`POST /review/start/{id}` → `IN_REVIEW`) el evento **desaparece** de todas las pestañas; los botones «Completar» / «Devolver» (`ReviewCenter.tsx:323-334`, `:421-432`) exigen `event.status === 'in_review'` y **nunca se renderizan**. La única vía es la URL directa `/review/{id}` (`ReviewDetail`). `GET /approvals/pending` tampoco lo lista (`review/service.py:463`, sólo `CORRECTED`), aunque `_get_event_for_approval` (`:629`) acepta `IN_REVIEW`.
3. **Historial vacío.** `ReviewDetail.tsx:44-54` deriva el «Historial de acciones» de `GET /review/batches?limit=50` filtrando `actions` por `event_id`; las acciones individuales (`start`/`return`/`complete`/`approve`/`reject`) se crean con `batch_id = NULL` (`review/service.py:276-280`, `:304-309`, `:360-365`, `:517-522`, `:541-546`) y no existe lectura por evento ⇒ el historial de un evento decidido individualmente queda vacío.
4. **Respuesta de aprobación descartada.** `ApprovalPanel.tsx:52-58` y `ReviewDetail.tsx:72,77` descartan el evento devuelto por `POST /approvals/approve` y navegan/refrescan. Para `grandparent_import` sin lote, `review/service.py:509-515` (`crear_lote_de_importacion_si_procede`, R-153/OD-25) crea el lote en la misma transacción y la respuesta trae `lot_id`; la interfaz no ofrece el enlace: el usuario debe buscar el lote «a mano».
5. **Petición sin permiso en la bandeja.** `ReviewCenter.tsx:109` pide `GET /users?limit=100` para un filtro (`:245-256`) cuyo parámetro el backend no atiende; el rol aprobador no tiene `users:read` ⇒ 403 silencioso (`.catch(() => {})`).
6. Secundarios en el mismo flujo: `prompt()`/`alert()` nativos (`ReviewCenter.tsx:123,143`; `ReviewDetail.tsx:69,74`) para una observación que el backend exige ≥ 10 caracteres (`review/schemas.py:98-101`); estado crudo sin i18n en `ReviewDetail.tsx:95`; KPIs «Aprobados/Rechazados» de `ApprovalPanel.tsx:146,168` contados sobre una lista que sólo contiene `corrected` ⇒ siempre 0; `review.service.ts:35` tipa `events` como `ApprovalAction[]`.

## 2 · Evidencia

| Fuente | Dato |
|---|---|
| `evidence/runtime-gp-e2e.json` (runtime real, 2026-09-13, actores UAT-09, empresa 1) | `R-12-review-tabs-in_review` ⇒ `{pending_review: false, in_review: false}` (evento iniciado no aparece en ninguna pestaña); `R-12-approve-in_review` ⇒ 200 (la aprobación desde `in_review` sí funciona por API/`ReviewDetail`) |
| ídem, `httpErrores` | actor aprobador (`ap`): `GET /api/v1/users?limit=100` ⇒ **403 ×7** (una por cada carga del centro de revisión) |
| `evidence/ui-e2e-local-pass1.json` (pila local, semillas `seeds.test_seeds`) | `H2-review-tabs` ⇒ las cuatro pestañas sin el evento; `H2-in_review-visible-en-su-pestana` ⇒ **false**; `H2-api-review-pending-status-in_review` ⇒ `estados: []`; `H2-api-approvals-pending` ⇒ `total 0, contieneInReview false` |
| Código | referencias del §1 (verificadas sobre HEAD `c0b4afc`) |
| Inventarios | `C_response_error_state.md` GAP #2, #13, #15, #25, #26, #31, #35 · `A_fe_be_trace.md` Parte 5 («STATE ORPHAN in_review») · `E_domain_ledger.md` §2.1 T5 |

## 3 · Causa raíz

- **Deriva de contrato** entre capas: la interfaz inventó `status`/`operator_id`; el backend nunca los implementó (patrón idéntico a R-82 en `AuditPage`, GA-REM-032 §3).
- **Cola de revisión modelada como «pendientes» y no como bandeja por estado**: `get_pending_review_events` es la única lectura y fija dos estados; no existe lectura de acciones por evento (`ApprovalActionRead` existe en `review/schemas.py:76-86` sin ruta que la use).
- **Respuestas ricas ignoradas**: `approve` devuelve el ORM completo con `lot_id` (R-153) y ningún consumidor lo lee.

## 4 · Impacto

- P-07 sólo es operable por interfaz hasta «Iniciar»; completar/devolver exige conocer la URL del evento. Con dos niveles de aprobación, el aprobador ve sólo `corrected`; con un nivel, el supervisor pierde de vista lo que ha tomado.
- La creación de lotes por aprobación (OD-25 B, R-153) es invisible para quien aprueba.
- Trazabilidad de decisión individual ausente en la UI (`docs/12 §11`, `docs/13 §6.3`).
- Ruido de seguridad: 403 recurrentes por un recurso que la bandeja no necesita (R-212).

## 5 · Dedup (§48)

Buscado en `REMEDIATION_BACKLOG.md` (R-001…R-189, P1-*, GA-REM-001…042, OD/AOD, GA-FE, OBS), `specs/remediation/*`, `audit/ga-*/`. Vecinos parciales: GA-REM-006/007 (motor de revisión, certificadas por API), GA-FE-04 (`gaFe04.reviewGates` sólo gates por permiso), R-82/GA-REM-032 (misma clase de deriva, otra pantalla), R-212 (N-3 `/users` 403 se documenta allí como síntoma transversal; **aquí** se corrige la petición innecesaria de la bandeja). Ningún hallazgo existente cubre la bandeja por estado ni el historial por evento ⇒ **nuevo**, R-197. No se asigna GA-REM (siguiente libre: GA-REM-043).

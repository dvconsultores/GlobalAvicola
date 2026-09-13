# R-197 · SPEC — BANDEJA DE REVISIÓN POR ESTADO, HISTORIAL POR EVENTO Y RESULTADO DE LA APROBACIÓN

Fecha: 2026-09-13 · Hallazgo canónico: **R-197** (P2, bloquea P-07 operativo) · HEAD `c0b4afc` · Estado `SPEC_READY` · Paquete `specs/R-197/` · Commits previstos: C1 (gobernanza + RED) · C2 (implementación) · C3 (certificación runtime) · C4 (UAT).

## 1 · Contexto

P-07 es «el diferenciador declarado del producto» (`e2e/proceso-03-revision-correccion-aprobacion.spec.ts`, GA-REM-016). El motor backend está certificado por API (GA-REM-006/007, R-166, R-143) y la interfaz del centro de revisión fue auditada sólo en sus *gates* por permiso (GA-FE-04). Nadie certificó que la bandeja **muestre** los estados sobre los que el motor opera. El recorrido runtime GA-UAT-09 (2026-09-13) lo puso de manifiesto: tras «Iniciar», el evento se pierde de la vista.

## 2 · Evidencia

Ver `R-197_FINDING.md §2`. Resumen: runtime `R-12-review-tabs-in_review {pending_review:false, in_review:false}`; local `H2-*` (mismo resultado); `httpErrores` `/users?limit=100` 403 ×7 para el aprobador; código `ReviewCenter.tsx:85-96` vs `review/router.py:22-33` vs `review/service.py:165-174`; `ReviewDetail.tsx:44-54` (historial desde `/review/batches`); `ApprovalPanel.tsx:52-58` / `ReviewDetail.tsx:72,77` (respuesta descartada); `review/service.py:509-515` (lote creado al aprobar).

## 3 · Causa raíz

1. `GET /review/pending` no acepta `status` ni `registered_by_id`; fija `REGISTERED|PENDING_REVIEW` (`review/service.py:168,173`).
2. No existe lectura de `approval_actions` por evento; el detalle intenta reconstruirla desde los lotes de revisión, donde las acciones individuales no están (`batch_id = NULL`).
3. Los consumidores de `approve`/`complete` descartan la respuesta.
4. La bandeja pide `/users` para un filtro inexistente en el backend, sin comprobar `users:read`.

## 4 · Impacto de negocio

- Flujo P-07 no operable por UI más allá del primer paso; devolución con observaciones (OD-17.a, `docs/12 §4` fila 5) inalcanzable desde la lista.
- El aprobador no sabe que su aprobación creó un lote (OD-25 B / R-153) ni cómo llegar a él.
- Sin historial de decisión por registro en la UI (`docs/12 §11`, `docs/13 §6.3`).
- Certificación P-07 «por UI» imposible hasta corregir.

## 5 · Comportamiento actual

| Acción | Resultado |
|---|---|
| Pestaña «En revisión» / «Devueltos» / «Aprobados» / «Consolidados» | misma lista que «Pendientes» (`registered` + `pending_review`) |
| «Iniciar» sobre un pendiente | 200; el evento desaparece de todas las pestañas; «Completar»/«Devolver» jamás visibles en la lista |
| Detalle `/review/{id}` | funciona por URL; «Historial de acciones» vacío para decisiones individuales; estado crudo; `alert()` para validar observación |
| Aprobar `grandparent_import` sin lote | 201 + toast «Evento aprobado»; ningún enlace al lote `L-GP-…` creado |
| Carga del centro por un aprobador | `GET /users` 403 (silencioso) en cada visita |
| KPIs del panel de aprobación | «Aprobados»/«Rechazados» siempre 0 |

## 6 · Comportamiento esperado

1. `GET /review/pending` acepta `status` (lista separada por comas, validada contra el conjunto de estados de bandeja) y `registered_by_id`; **sin `status` conserva** `registered,pending_review` (compatibilidad). Estados inválidos ⇒ 422.
2. La bandeja tiene pestañas por estado real: **Pendientes** (`registered,pending_review`) · **En revisión** (`in_review`) · **Devueltos** (`returned`) · **Corregidos** (`corrected`) · **Aprobados** (`approved`) · **Rechazados** (`rejected`) · **Consolidados** (`consolidated`). Cada pestaña envía su `status`; el conteo `total` es el del estado consultado.
3. Acciones por estado en la lista y en el detalle, gobernadas por `review:review`: `pending_review` ⇒ Iniciar · `in_review` ⇒ Completar / Devolver (modal con observación ≥ 10 caracteres validada en cliente) · `corrected`/`in_review` ⇒ enlace al detalle donde aprobar/rechazar (`approvals:*`) como hoy.
4. Nueva lectura `GET /review/events/{event_id}/actions` (`review:read`) que devuelve `list[ApprovalActionRead]` —individuales y de lote— en orden cronológico; `ReviewDetail` la consume para el historial.
5. Tras `approve`/`complete` la interfaz **lee la respuesta**: si `lot_id` pasó de nulo a valor (importación de abuelas) muestra toast persistente «Lote creado» con enlace `/lots/{lot_id}`; `ReviewDetail` permanece en la página y recarga (no navega a ciegas).
6. La bandeja **no pide `/users`** si la sesión carece de `users:read`; el filtro «Operador» sólo se muestra cuando puede poblarse; el parámetro viaja como `registered_by_id`.
7. Sin `prompt()`/`alert()` en revisión: modal/inline con validación de longitud; estados con i18n (`status.*`) y `Badge`.
8. Panel de aprobación: KPIs veraces (Pendientes = `total`; se retiran los contadores que no pueden calcularse desde la lista) y guarda de doble clic en Aprobar/Rechazar.

## 7 · Alcance

- Backend: parámetros `status`/`registered_by_id` en `GET /review/pending` + validación; nueva ruta de acciones por evento; `response_model` declarado para `GET /review/pending`, `GET /approvals/pending` y la ruta nueva (contrato explícito, GA-REM-041 guard «rutas nuevas declaran su contrato»).
- Frontend: `ReviewCenter` (pestañas, acciones, filtro operador condicionado, modal de observación), `ReviewDetail` (historial, permanencia, enlace al lote, badge i18n, sin `alert`), `ApprovalPanel` (respuesta de aprobación, KPIs, doble clic), `review.service.ts` (tipos y `getActions`), i18n ES/EN.
- Pruebas RED→GREEN backend y frontend; E2E runtime; UAT.

## 8 · Fuera de alcance

- Permisos de `batch-approve`/`batch-reject` y gating de la barra de lote (**R-208**).
- Marcador de contrapartida de reverso y pestaña/bandeja de reversos (**R-207**); badges `sap_*` (**R-220** C-27).
- «Lote #» con `lot_id` nulo en listados (R-220 C-26) salvo en las pantallas tocadas aquí, donde se muestra «—»/«Se creará al aprobar» como `OperationDetailPage.tsx:201-207`.
- Corrección de más campos que `observations` (`CorrectionForm`, E-07/R-142); segunda corrección sobre `CORRECTED`.
- Página «sin permiso» transversal y home sin `dashboard:read` (**R-212**); aquí sólo se evita la petición innecesaria y se distingue 403 de vacío en la bandeja.
- `/my-pending` huérfana (R-220); renombrar `/review/pending` (compatibilidad).
- Motor de revisión, BR-14, R-166, OD-17, OD-19: **sin cambio**.

## 9 · Impacto frontend

| Fichero | Cambio |
|---|---|
| `pages/review/ReviewCenter.tsx` | pestañas por estado (7); `status` por pestaña; `registered_by_id`; filtro operador sólo con `users:read`; modal de observación (≥ 10) en Devolver; sin `prompt()` (nombre de lote de revisión también por modal); 403 de carga ⇒ panel «sin permiso» (no «Sin resultados»); toast de lote creado tras Completar |
| `pages/review/ReviewDetail.tsx` | historial desde `/review/events/{id}/actions`; permanece y recarga tras acción; toast con enlace al lote creado; `Badge` + `status.*`; validación inline (sin `alert`) |
| `pages/approvals/ApprovalPanel.tsx` | lee respuesta de `approve` (enlace al lote); KPIs veraces; botón deshabilitado mientras la petición está en vuelo |
| `services/review.service.ts` | tipos reales (`events: OperationalEventRead[]`), `status: string`, `registered_by_id`, `getActions(eventId)` |
| `data/navigationConfig.ts` | sin cambio de rutas; las entradas `?status=approved|returned` pasan a ser veraces |
| `public/locales/{es,en}/translation.json` | claves nuevas (§19) |

## 10 · Impacto backend

| Fichero | Cambio |
|---|---|
| `review/router.py` | `list_pending_review`: `status: Optional[str]`, `registered_by_id: Optional[int]`; `response_model`; nueva `GET /review/events/{event_id}/actions` (`review:read`) |
| `review/service.py` | `get_pending_review_events(status=…, registered_by_id=…)`: parseo/validación contra `ESTADOS_DE_BANDEJA`; nuevo `listar_acciones(event_id)` que resuelve el evento con empresa + `_ambito_de_unidad` **sin** `FOR UPDATE` ni habilitación de escritura (lectura) |
| `review/schemas.py` | `ReviewQueueResponse {events: list[OperationalEventRead], total}`; reutiliza `ApprovalActionRead` |
| Guardianes | `test_population_invariant::test_ac14_sin_migracion_ni_rutas_nuevas` **211 → 212** (exacto); `test_rbac` (permiso `review:read` ya concedido a Supervisor/Aprobador/Auditor en `l2m3n4o5p6q7`); `test_business_unit_admin::test_las_rutas_nuevas_declaran_todas_su_contrato_de_respuesta` |

## 11 · Contrato frontend↔backend

| Ruta | Petición | Respuesta |
|---|---|---|
| `GET /api/v1/review/pending` | `status?=a,b` ⊆ `{registered, pending_review, in_review, returned, corrected, approved, rejected, consolidated, reversed}` · `registered_by_id?` · filtros existentes · `limit ≤ 200` | `{events: OperationalEventRead[], total}` (ordenado por `event_date desc`); sin `status` ⇒ `registered,pending_review` |
| `GET /api/v1/review/events/{event_id}/actions` | — | `ApprovalActionRead[]` (`id, event_id, batch_id, step_id, user_id, action_type, observations, created_at`), `created_at asc` |
| `POST /review/start/{id}` · `/review/return` · `/review/complete` · `POST /approvals/approve` · `/reject` | como hoy | `OperationalEventRead` (con `lot_id` ya poblado si la aprobación creó lote) |
| `GET /approvals/pending` | como hoy (C-07 decide si incluye `in_review`) | `{events, total}` |

`reversed` se admite en `status` para que R-207 no reabra el contrato; sin pestaña aquí.

## 12 · Impacto en datos

Ninguno: sin migración, sin columnas, sin cambio de estados ni de `approval_actions`. Sólo lecturas nuevas.

## 13 · Seguridad

- La ruta nueva es de **lectura** con `review:read`; resuelve el evento con `company_id` efectivo + predicado de unidad (`_ambito_de_unidad`) ⇒ evento ajeno ⇒ 404 (mismo contrato que `_get_event`), sin revelar existencia.
- `status`/`registered_by_id` no amplían el alcance: se aplican **después** del predicado de empresa/unidad.
- La bandeja deja de solicitar `/users` sin permiso: menos 403 en logs (R-212 N-3).
- Sin autorización en frontend (`AC-FE16`): los *gates* sólo ocultan; el backend decide.

## 14 · Inquilino

`OperationalEvent.company_id == company_id efectivo` en todas las lecturas (`review/service.py:166`, `:391`). Autoridad global sin contexto ⇒ cero filas (comportamiento vigente OD-14). Sin cambio.

## 15 · Unidad de negocio

`_ambito_de_unidad()` (`review/service.py:128-147`, `predicado_de_evento`) se conserva en la lista y se aplica a la ruta nueva. Unidad apagada: lectura excluida por el predicado (OD-16); acciones de escritura siguen exigiendo `exigir_unidad_operativa` (R-165). Sin cambio de política.

## 16 · RBAC

| Acción | Permiso | Frontend gate |
|---|---|---|
| Ver bandeja / historial | `review:read` | `CapabilityRoute permission="review:read"` (App.tsx:271-272) |
| Iniciar / Completar / Devolver / crear lote de revisión | `review:review` | `can({permission:'review:review'})` (ya) |
| Aprobar / Rechazar | `approvals:approve` / `approvals:reject` | ya |
| Filtro operador | `users:read` | **nuevo**: sin él no se pide `/users` ni se muestra el selector |

Sin permiso nuevo. Matriz canónica (`l2m3n4o5p6q7`): Supervisor y Aprobador tienen `review:read`; el rol de semillas `TEST Aprobador` **no** lo tiene (`test_seeds.py:136-141`) ⇒ para el E2E local se usa `Supervisor Avícola` + `Aprobador` canónicos o se completa la semilla (C-12).

## 17 · Transacciones

Lecturas fuera de bloqueo: `listar_acciones` **no** usa `_bloquear_evento` (`FOR UPDATE` sólo en escritores de decisión, R-166). Escrituras sin cambio (`RutaTransaccional`).

## 18 · Auditoría

Sin nuevas emisiones (lecturas). El historial de la UI muestra `approval_actions`; la duplicidad de filas en `audit_logs` la trata **P1-12-REOPEN**. Se conserva `REVIEW_COMPLETED` (GA-REM-032 AC05).

## 19 · i18n

Claves nuevas ES/EN (sin texto fijo en componentes): `review.corrected` («Corregidos»/«Corrected»), `review.rejected`, `review.obsMinLength` («La observación debe tener al menos 10 caracteres»), `review.lotCreated` («Lote creado: {{code}}»), `review.viewLot` («Ver lote»), `review.noPermissionQueue` («No tiene permiso para ver la bandeja»), `review.actionsEmpty` («Sin acciones registradas»), `review.batchNameLabel`, `review.returnObservationLabel`, `review.approving`. Estados via `status.*` (existentes, 14 valores incl. `reversed`).

## 20 · Escritorio

Tabla ≥ 1024 px con 7 pestañas (scroll horizontal ya existente `:181`), columna Estado con `Badge`, acciones por estado; detalle en dos columnas con historial cronológico.

## 21 · Móvil

Tarjetas (`lg:hidden`) con las mismas acciones; modal de observación a pantalla completa en 390×844; verificación de overflow 0. `/review` es `WebOnlyRoute` (App.tsx:271): la vista móvil aplica a escritorio estrecho, no a `view_type=mobile`.

## 22 · Manejo de errores (400/401/403/404/409/422)

| Código | Origen | UI |
|---|---|---|
| 400 | transición inválida (`review/service.py:266-270`, `:294-298`, `:323-327`, `:629-633`), BR-16 | toast con `detail` (`getErrorMessage`) y refetch (el estado real gana) |
| 401 | sesión | interceptor existente |
| 403 | sin permiso, BR-14 (`:47`, `:64-67`), R-165 unidad apagada | toast con `detail`; en carga de lista ⇒ panel «sin permiso» distinto de vacío |
| 404 | evento fuera de alcance | toast; detalle ⇒ «Evento no encontrado» + volver |
| 409 | no aplica en revisión (R-166 devuelve 400 tras releer) | — |
| 422 | `status` inválido; observación < 10; cuerpo | `getErrorMessage` (lista FastAPI → texto); la validación cliente evita el caso común |

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

Ninguno: `consolidated` sólo se lista; nada cambia en `sap/*`.

## 25 · Compatibilidad hacia atrás

`GET /review/pending` sin `status` responde igual que hoy. Clientes antiguos que envíen `status`/`operator_id`: `operator_id` sigue ignorado (se documenta); `status` con valores válidos ahora filtra —que es lo que ya pretendían—. `response_model` puede recortar campos ORM no declarados (`bird_movements`, `evidences`…): ningún consumidor de la lista los usa (`ReviewCenter`, `ApprovalPanel` leen `id, status, event_type, lot_id, event_date`).

## 26 · Criterios de aceptación

Bandeja: **AC01** `status=in_review` devuelve sólo `in_review` · **AC02** sin `status` ⇒ `registered,pending_review` (igual que hoy) · **AC03** `status` inválido ⇒ 422 · **AC04** `registered_by_id` filtra · **AC05** cada pestaña muestra su estado y `total` coherente · **AC06** evento iniciado aparece en «En revisión» con Completar/Devolver · **AC07** Devolver exige observación ≥ 10 en cliente y servidor · **AC08** evento devuelto aparece en «Devueltos»; reenviado por el operador vuelve a «Pendientes» · **AC09** `approved`/`consolidated`/`rejected`/`corrected` visibles en su pestaña.
Historial: **AC10** `GET /review/events/{id}/actions` devuelve individuales y de lote en orden · **AC11** evento ajeno ⇒ 404 · **AC12** sin `review:read` ⇒ 403 · **AC13** `ReviewDetail` muestra el historial.
Resultado: **AC14** aprobar `grandparent_import` sin lote ⇒ toast con enlace a `/lots/{lot_id}` (panel y detalle) · **AC15** `ReviewDetail` permanece y recarga tras cada acción · **AC16** KPIs del panel veraces · **AC17** doble clic no envía segunda petición.
Permisos/UX: **AC18** sin `users:read` la bandeja no pide `/users` y oculta el filtro · **AC19** 403 en carga ⇒ mensaje «sin permiso» (no «Sin resultados») · **AC20** sin `prompt/alert` en revisión · **AC21** estados con i18n en detalle.
Seguridad/regresión: **AC22** tenant/BU sin cambio (`test_review_bu_enforcement`, R-165) · **AC23** guardianes exactos (rutas 212; `test_rbac`; contrato de respuesta) · **AC24** regresión GA-REM-006/007, R-166 (`test_review_decision_concurrency`), R-143 verdes · **AC25** ES/EN y móvil · **AC26** sin migración ni permiso nuevo · **AC27** E2E runtime P-07 por UI 100 % (§28) · **AC28** UAT propietario (§29).

## 27 · Pruebas RED→GREEN

Detalle en `R-197_RED_E2E_UAT_DESIGN.md`. Backend `tests/test_r197_review_queue_contract.py` (8 casos, RED por causa exacta: lista con estados no pedidos; 404 de ruta inexistente). Frontend `pages/review/__tests__/r197.reviewQueue.test.tsx`, `r197.reviewDetailHistory.test.tsx`, `pages/approvals/__tests__/r197.approvalResult.test.tsx`. Regresión: suite backend completa en PG de pruebas; vitest ≥ 314; `tsc`; `build`.

## 28 · E2E

Runner `scripts_e2e_r197.mjs` (patrón `scripts_e2e_f01_retry.mjs`, modos `calibrate|live`) sobre pila local con semillas; journal `evidence/r197/runtime-*.json` con `pageerror`, `httpErrores`, `asserts`. Recorrido E2E-01…E2E-10 (§ diseño).

## 29 · UAT

UAT-R197-01…06 (propietario, runtime nube tras despliegue): pestañas, devolver, completar, historial, lote creado, sin 403 de `/users`.

## 30 · Criterios de cierre

AC01…AC28 verdes con evidencia; RED válida documentada (falla por la causa, no por fixture); suite backend íntegra ejecutada localmente (no «declarada a CI», GA-GOV-03); vitest/tsc/build; E2E local 10/10 con `fatal_react 0`; UAT del propietario firmada; `REMEDIATION_BACKLOG.md` con R-197 y su GA-REM asignado al autorizar (siguiente libre GA-REM-043).

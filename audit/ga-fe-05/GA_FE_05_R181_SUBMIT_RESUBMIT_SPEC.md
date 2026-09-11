# GA-FE-05 · SPEC · ENVÍO/REENVÍO A REVISIÓN (R-181)

## 1 · Contexto
Fase 9 · R-181 (P2) · baseline `b448f3e` · producto `de40d36` · `index-B66tpdeW.js`. La vertical UI de envío/reenvío a revisión nunca se cableó (backend completo desde `R-135`/`OD-17.b`).

## 2 · Historia R-181
Ver `GA_FE_05_R181_CANONICAL_RECONCILIATION.md` §1–§6. Sin trabajo backend esperado.

## 3 · Problema
`operationsService.submit` existe con 0 llamadores; sin CTA, sin i18n, sin feedback; estado del detalle en crudo. El operador no puede completar guardar → enviar → devolver → reenviar sin API manual.

## 4 · Contrato backend (verificado en código, no inventado)
- `POST /operations/{id}/submit` · permiso `operations:create` · respuesta `OperationalEventRead` · `registered|returned|rejected → pending_review` · `400` en otro estado (mensaje canónico) · `403` por guarda operativa (`AC-W13`) · auditoría `state_transition` «Enviado a revisión» · sin idempotencia explícita (segunda llamada tras éxito ⇒ 400).

## 5 · Brecha frontend
Ver reconciliación §3–§4: acción inexistente; único trabajo es exponerla de forma state-aware y comprensible.

## 6 · Ciclo de vida
`GA_FE_05_OPERATION_STATE_MATRIX.md` (verdades del enum real, 14 estados). CTA exacto: `{registered, returned, rejected}`.

## 7 · OD-17
`GA_FE_05_OD17_TRACEABILITY.md` (a: REJECTED no terminal; b: reenvío de devuelto/rechazado y segregación backend; c: SAP diferido). Ninguna decisión UI introduce transiciones.

## 8 · Actores
`GA_FE_05_ACTOR_MATRIX.md` (C operador · P RBAC-negativo · Z cero-BU · D sin autoridad · E global · V revisor).

## 9 · Seguridad
- Acción productiva: permiso `operations:create` ∧ unidad (efectiva normal / habilitada+contexto global) ∧ estado reenviable.
- CBU OFF ⇒ sin unidades ⇒ CTA oculto y API 403 (también para global).
- Sin User BU ⇒ CTA oculto (0 unidades efectivas) y API 403.
- Sin RBAC ⇒ CTA oculto y API 403 (`require_permission`).
- La UI es descubribilidad; la autoridad final es el backend (verificado con API directa).

## 10 · BU / tenant
Igual que §9 + propiedad del recurso: el evento de otra empresa responde 404/403 por los guardas existentes; no se añade lógica nueva.

## 11 · Permisos
Reutilizar `operations:create` (contrato real). **0 permisos nuevos.**

## 12 · Reglas estado/acción
CTA visible ⇔ `operations:create` ∧ `requiresUnits` ∧ `status ∈ {registered, returned, rejected}`. Label según estado (Enviar/Reenviar). Chip de estado localizado (`status.<x>` fallback crudo).

## 13 · Submit
Un clic ⇒ `operationsService.submit(id)` ⇒ éxito: toast + `GET` fresco ⇒ chip `pending_review` + CTA desaparece.

## 14 · Resubmit
Mismo endpoint y misma lógica; solo cambia el label (estados `returned`/`rejected`). Sin endpoint inventado.

## 15 · Confirmación
Sin modal (patrón directo del flujo de revisión). Documentado en clarificaciones C12. La inclusión de motivo/observación no aplica al envío (el backend no la pide).

## 16 · Success UX
Toasts ES/EN + refetch obligatorio (no toast-only) + botón no obsoleto.

## 17 · Failure UX
`catch` ⇒ `toast.error(getErrorMessage(...))` + `GET` fresco (reconciliar verdad). Sin estado optimista. 400/403/404/409 se muestran normalizados por la capa existente.

## 18 · Concurrency
Sin dedupe backend adicional: doble transición ⇒ 400 en la segunda; la UI deshabilita durante el vuelo ⇒ una mutación lógica.

## 19 · Audit
Backend ya audita el éxito; denegaciones no generan fila (verificado: la guarda ocurre antes de `db.add`). No se implementa auditoría nueva.

## 20 · Desktop
1440×900: CTA en cabecera del detalle, sin solapamientos, label correcto.

## 21 · Mobile
390×844: mismo componente, CTA alcanzable, sin overflow ni CTA oculto/duplicado.

## 22 · i18n
Nuevas claves ES/EN: `operations.submitToReview`, `operations.resubmitToReview`, `operations.submittedToReview`, `operations.resubmittedToReview`, `operations.submitError` (fallback). `status.draft|sap_error|reversed` añadidas. Sin claves crudas.

## 23 · AC
Contract: `R181-AC01…07` · Submit: `AC08…15` · Resubmit: `AC16…21` · Negativos: `AC22…28` · Calidad: `AC29…40` (listados en `GA_FE_05_CHECKLIST.md`).

## 24 · Testing
RED vitest (9 casos) ⇒ GREEN; gates completos; E2E autenticados E2E-01…10; regresión GA-FE-02/03/04.

## 25 · Deployment
Push normal ⇒ pipeline existente ⇒ nueva generación estable para toda la certificación.

## 26 · Evidencia
RED + runtime + red + capturas + ledger + cierre R-181 + certificación + UAT.

## 27 · Criterios de cierre R-181
Reconciliación §5 (10 criterios). R-181 = CLOSED solo con submit + estado + resubmit + inmutabilidad + seguridad completos y evidenciados.

## 28 · Fuera de alcance
R-182 (incl. `planned_close_date`, `area_id`, SLA), BU-D10, fase 9, SAP/Olas B/C, nuevos permisos, nueva semántica de negocio, rediseño, auditoría nueva, idempotencia backend nueva.

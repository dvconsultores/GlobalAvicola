# GA-FE-05 · R-181 · RECONCILIACIÓN CANÓNICA

Fecha: 2026-09-11 · Baseline: `b448f3e` · Producto: `de40d36` · Bundle: `index-B66tpdeW.js`
Fuentes leídas: `REMEDIATION_BACKLOG.md` §R-181 · `WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX.md` · `R135_R143_STATE_CORRECTION_MATRIX.md` · `CERTIFICATION_SCOPE_RECONCILIATION.md` · `AUTHENTICATED_USER_JOURNEY_MATRIX.md` · `MASTER_FRONTEND_RUNTIME_AUDIT_EVIDENCE.md §34` · `docs/12-approval-workflow.md` · backend `app/operations/{router,service,models}.py` · frontend `services/operations.service.ts`, `pages/operations/OperationDetailPage.tsx`.

## 1 · Problema original (R-181, P2 — vigente)

> «`POST /operations/{id}/submit` (enviar a revisión / reenviar un devuelto o rechazado) no tiene ningún control en la interfaz: `operationsService.submit` no tiene llamadores en todo el historial del frontend; 0 refs `/submit` en el bundle desplegado; sin claves i18n; los E2E lo suplen por API.»

- **Raíz**: vertical de UI nunca cableada (clase distinta de R-98/R-119 — no es permisos — y de R-135, que cerró el backend con `OD-17.b`).
- **Requisito**: `docs/12 §2` («Devuelto → Operador reenvía»; «Rechazado → Operador reenvía (corregido)») · `OD-17.b` · `spec §4.10`.
- **Backend**: IMPLEMENTED y desplegado — sin trabajo esperado (§53: 0 cambios).

## 2 · Verdad actual del backend (código leído)

| Elemento | Valor real |
|---|---|
| Ruta | `POST /operations/{event_id}/submit` → `OperationalEventRead` |
| Permiso | `require_permission("operations", "create")` |
| Estados fuente válidos (`REENVIABLES`) | `registered` · `returned` · `rejected` |
| Estado resultante | `pending_review` |
| Conflicto de estado | `400` «Solo eventos registrados, devueltos o rechazados pueden enviarse a revisión» |
| Guarda operativa | `exigir_unidad_operativa(event)`: empresa ON (si no, 403 `AC-W13`); actor de empresa ⇒ unidad en alcance efectivo; global ⇒ situado + unidad habilitada, concesión no exigida; denegación antes de `db.add` (sin fila/movimiento/auditoría) |
| Auditoría | `audit_state_transition(..., comments="Enviado a revisión")` |
| Idempotencia | No hay dedupe explícito; doble transición ⇒ segunda recibe 400 (estado ya `pending_review`) |
| Creación | `POST /operations` nace en `registered` ⇒ ya reenviable |

Enum de estados (`EventStatus`): `draft, registered, pending_review, in_review, returned, corrected, approved, rejected, consolidated, sent_to_sap, sap_confirmed, sap_error, cancelled, reversed`.

## 3 · Verdad actual del frontend (código leído)

| Elemento | Valor real |
|---|---|
| `operationsService.submit(id)` | **EXISTE** (`api.post('/operations/${id}/submit')`) |
| Llamadores en `src/` | **0** (el gap R-181 persiste) |
| Botón/CTA de enviar/reenviar | **No existe** en ninguna pantalla |
| Claves i18n `submit/resubmit` | **No existen** |
| Chip de estado en detalle | Muestra `event.status` **crudo** (sin `t('status.…')`) |
| Guardas GA-FE-04 en la página | Evidencia evidencias crear/borrar (no lifecycle) |
| Ruta/pantalla canónica | `/operations/:id` — `OperationDetailPage` (responsive; sirve desktop y móvil) |

## 4 · Brecha restante exacta (una sola)

**El acto explícito de enviar a revisión / reenviar no es descubrible por UI**: ni botón, ni estado comprensible localizado, ni feedback. El usuario autorizado no puede completar el ciclo guardar → enviar → (devuelto/rechazado) → reenviar sin herramientas externas (API manual), lo que `docs/12 §2` y `OD-17.b` no permiten como estado final del producto.

## 5 · Criterios de cierre R-181 (completos)

1. CTA «Enviar a revisión» visible y funcional en `/operations/:id` para `operations:create` ∧ estado ∈ `REENVIABLES` ∧ unidad disponible (evaluador GA-FE-04), en desktop y móvil.
2. CTA «Reenviar a revisión» en `returned` y `rejected` (mismo endpoint, `OD-17.a/b`).
3. Estado visible comprensible y localizado (chip `t('status.…')` con fallback).
4. Tras éxito: `GET` fresco, chip y CTA recomputados, sin botón obsoleto; sobrevive refresh y re-login.
5. Fallo (403/404/400/409/422): sin éxito falso; estado real reconciliado por `GET` fresco.
6. Sin doble mutación (loading deshabilita; un clic lógico = una petición).
7. Estados finales (`approved`, `consolidated`, `sent_to_sap`, `sap_confirmed`, `cancelled`, `reversed`) y no reenviables (`draft`, `pending_review`, `in_review`, `corrected`) **sin** acción.
8. Seguridad de producto intacta: CBU OFF / sin unidad / sin RBAC / no autorizado ⇒ UI sin acción **y** API denegada (403/400), sin cambio de estado; autoridad final backend.
9. Sin cambios de backend, sin migraciones, sin permisos nuevos.
10. No regresión GA-FE-02/03/04; R-182 intacto.

## 6 · Dedup (sin duplicados de ID)

- `R-98/R-119`: cerrados; este trabajo reutiliza su evaluador (GA-FE-04 `useCan`/ActionGate) — no se duplica.
- `R-135`: backend cerrado (`OD-17.b`); este hallazgo es la vertical UI — ya registrado como R-181, no se crea ID nuevo.
- `R-142` (`AOD-17`) / `R-140` / `R-154`: fuera de alcance, sin tocar.
- `R-182`: intacto; se prohíbe su corrección colateral (§76).

## 7 · Decisión de alcance de la tranche

Frontend-only (§53 esperado 0 backend): CTA state-aware + export del servicio ya existente + refresh/estado + i18n + pruebas RED→GREEN + evidencia runtime autenticada + cierre R-181.

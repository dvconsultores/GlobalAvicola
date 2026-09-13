# R-207 · SPEC — SUPERFICIE DE REVERSO: SOLICITAR, SEGUIR Y MOSTRAR

Fecha: 2026-09-13 · Hallazgo canónico: **R-207** (P2 · bloquea §10) · HEAD `c0b4afc` · Origen GA-REM-041/RES-04/C-13/C-27 · Registro G-19. Secciones §47.

## 1 · Contexto

El motor de reverso está completo y probado por API (OD-19): solicitud con motivo, contrapartida automática, aprobación por el motor existente, ambos `REVERSED`, cancelación prohibida. Falta la superficie de usuario: solicitar desde un aprobado, ver la contrapartida en las bandejas y el estado `reversed` en todas las listas/detalles.

## 2 · Evidencia

`R-207_FINDING.md §1` (`reversals/router.py:16-37`; `reversals/service.py:88-131,181-216`; `statusColors.ts:122-138`; `H8*` locales).

## 3 · Causa raíz

Capacidad backend-first sin fase de UI (RES-04 diferido).

## 4 · Impacto de negocio

Sin remedio legítimo por UI para aprobados erróneos; estado `reversed` invisible; §10 incumplido.

## 5 · Comportamiento actual → esperado

| Aspecto | Hoy | Esperado |
|---|---|---|
| Solicitar | solo API | acción «Solicitar reverso» en el detalle del evento **aprobado** (gate `reversals:create`), con motivo ≥5 obligatorio y confirmación |
| Contrapartida | invisible | visible en centro de revisión/bandejas como `pending_review` (con enlace al original) |
| Estado | sin badge | `reversed` con color/badge en listas, detalle, review, approval, timeline |
| Enlace | no existe | original ↔ contrapartida (campo `reversal_event_id` ya en el modelo) |
| Cancelar | prohibido (backend) | UI no ofrece cancelar para `reversed`; mensaje si se intenta por API |

## 6 · Comportamiento esperado

1. **Detalle de operación** (`OperationDetailPage`): para eventos `approved` elegibles, botón «Solicitar reverso» (gate `reversals:create` ∧ elegibilidad mostrada); modal con motivo (≥5) y resumen de efectos; tras 201, navegación/estado con la contrapartida enlazada.
2. **Bandejas** (`ReviewCenter`/`ApprovalPanel`/`ReviewDetail`): la contrapartida aparece como un evento normal `pending_review` (el motor ya la genera); su detalle muestra referencia al original (y viceversa).
3. **Badges**: `reversed` añadido a `statusColors`, `domain.types` y mapas locales; i18n `status.reversed` ya existe (14 estados) — verificar.
4. **Listas**: filtros/estados existentes muestran `reversed` correctamente (sin badges grises).
5. **Errores**: 409 (contrapartida activa), 400 (no elegible/motivo corto), 403/404 según patrón — render seguro (getErrorMessage).
6. Sin cambio backend (el contrato existe). Sin migración.

## 7 · Alcance

- `frontend/src/pages/operations/OperationDetailPage.tsx` (acción+modal), `services/reversals.service.ts` (nuevo o método en operations), `components/ui/statusColors.ts`, `types/domain.types.ts`, mapas locales de estado (`OperationListPage`, `OperationDetailPage`, `ReviewCenter`, `ReviewDetail`, `ApprovalPanel`), i18n ES/EN (claves del modal; `status.reversed` verificado).
- `ReviewDetail`/`OperationDetailPage`: mostrar enlace original↔contrapartida (campo existente en la respuesta ORM/detalle).
- Tests: `frontend/.../__tests__/r207.reversalSurface.test.tsx` (jsdom: botón/gate/motivo/payload; badge), regresión vitest.
- Sin migración; sin endpoint nuevo; sin permiso nuevo.

## 8 · Fuera de alcance

- R-192/R-193 (integridad del ciclo): paquetes propios; **dependencia de orden**: la UI de reverso no se libera antes de que el cierre tras reverso (R-192) y BR-18 (R-193) estén corregidos (o se documenta la ventana).
- Reverso post-SAP (`SAP_DEFERRED`, R-136).
- Huevos/incubación (no elegibles; OD-19 §18).

## 9 · Impacto frontend

Detalle + badges + enlaces; sin rediseño.

## 10 · Impacto backend

Ninguno.

## 11 · Contrato frontend↔backend

`POST /reversals {event_id, reason}` (existente); `GET /reversals`, `/reversals/event/{id}` (existentes). La UI consume; sin cambios de esquema.

## 12 · Impacto en datos

Sin cambio; la UI hace alcanzable la capacidad existente.

## 13 · Seguridad

Gate `reversals:create` (servidor autoridad); UI espejo. La segregación/BR-14 del motor P-07 intacta.

## 14 · Inquilino · 15 · Unidad

Sin cambio (pertenencia/unidad verificadas por el servicio).

## 16 · RBAC

`reversals:create` para solicitar (ya existe); aprobación con `approvals:*` (R-208 coordina el lote).

## 17 · Transacciones

Sin cambio.

## 18 · Auditoría

La solicitud ya audita (`audit_accion CREATED entity=reversal`); la contrapartida entra en P1-12-REOPEN (transición). Sin cambio aquí.

## 19 · i18n

| Clave | ES | EN |
|---|---|---|
| `reversals.request` | Solicitar reverso | Request reversal |
| `reversals.reason` | Motivo (mín. 5 caracteres) | Reason (min 5 chars) |
| `reversals.confirm` | Se creará una contrapartida que deberá aprobarse para neutralizar el registro. | A counterpart will be created and must be approved to neutralize the record. |
| `reversals.counterpart` | Contrapartida | Counterpart |
| `status.reversed` | Revertido | Reversed |

## 20 · Escritorio · 21 · Móvil

Acción usable en ambos (si el detalle es accesible en móvil; verificar view_type); mensajes sin overflow.

## 22 · Manejo de errores

409/400/403/404 con `getErrorMessage`; sin crash; modal preservado.

## 23 · Impacto de migración · 24 · Impacto SAP

Ninguna / el reverso pre-SAP queda operable por UI; post-SAP diferido.

## 25 · Compatibilidad hacia atrás

- API: sin cambio.
- UI: gana superficie; `reversed` deja de ser gris.

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R207-01 | Evento aprobado + `reversals:create` ⇒ botón visible; sin permiso ⇒ no visible y API 403 (control) |
| AC-R207-02 | Solicitar con motivo ≥5 ⇒ 201; contrapartida creada y visible en revisión; enlace original↔contrapartida |
| AC-R207-03 | Aprobar la contrapartida ⇒ ambos `reversed`; badges con estado; en listas/detalle |
| AC-R207-04 | Motivo <5 ⇒ validación cliente + 422 legible si se fuerza |
| AC-R207-05 | 409 contrapartida activa ⇒ mensaje claro |
| AC-R207-06 | `reversed` no ofrece cancelar/editar (coherente con backend) |
| AC-R207-07 | ES/EN y móvil usables |
| AC-R207-08 | Sin migración/endpoint/permiso; diff FE (+tests) |
| AC-R207-09 | Regresión: `test_internal_reversal.py` (API), vitest, tsc, build; R-192/R-193 verificados antes o ventana documentada |

## 27 · Pruebas RED→GREEN

`§1`: `r207.reversalSurface` (rojo: botón inexistente; badge sin `reversed`; sin enlace).

## 28 · E2E

`§2`: `R207-RT-01…05` (solicitar→contrapartida→aprobar→badges/enlace; gate; 409). Artefacto `evidence/r207/`.

## 29 · UAT

`UAT-R207-01…04`: solicitar un reverso con motivo; ver contrapartida; aprobarla; comprobar el estado y el enlace. 4/4.

## 30 · Criterios de cierre

AC-01…09 verdes · RED en `c0b4afc` · GREEN local · runtime con artefactos · UAT 4/4 · R-192/R-193 cerrados o ventana documentada · sin migración/endpoint/permiso · R-207 → `CLOSED` con GA-REM asignado.

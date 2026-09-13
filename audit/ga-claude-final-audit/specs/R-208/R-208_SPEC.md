# R-208 · SPEC — PERMISO DE APROBACIÓN POR LOTE ALINEADO CON LA OPERACIÓN UNITARIA

Fecha: 2026-09-13 · Hallazgo canónico: **R-208** (P2 · bloquea control) · HEAD `c0b4afc` · Origen E-09 · Registro G-20. Secciones §47.

## 1 · Contexto

El motor de aprobación (`review/service.py`) ejecuta aprobar/rechazar por evento, con segregación BR-14 y permisos `approvals:approve`/`approvals:reject` en las rutas unitarias. Las rutas por lote (`/approvals/batch-approve|reject`, `review/router.py:143-160`) ejecutan la misma operación sobre N eventos con `review:review`.

## 2 · Evidencia

`R-208_FINDING.md §1`. Código: `review/router.py:123-160`; `ApprovalPanel.tsx:100,119,173`; `review/service.py:463,629` (validaciones por evento, BR-14/R-143 intactas).

## 3 · Causa raíz

Permiso reutilizado del centro de revisión para una operación de aprobación; sin test de autoridad por lote.

## 4 · Impacto de negocio

Aprobación (con efecto de estado y efectos colaterales tipo creación de lote OD-25) ejercida por un actor sin la capacidad designada; política de autoridad inconsistente entre puertas.

## 5 · Comportamiento actual

| Actor | Batch-approve | Unitario approve |
|---|---|---|
| `review:review` sin `approvals:approve` | **200 (aprueba)** | 403 |
| `approvals:approve` | 200 | 200 |

## 6 · Comportamiento esperado

1. `POST /approvals/batch-approve` ⇒ `require_permission("approvals","approve")`; `batch-reject` ⇒ `approvals:reject` (idéntico a las unitarias).
2. Validaciones por evento intactas: BR-14 (segregación), R-143, estado aprobable; si un evento del lote falla, se comporta como hoy (por evento, según servicio) **sin** debilitar la puerta global.
3. UI: `ApprovalPanel` gatea los botones de lote con `approvals:approve`/`approvals:reject` (alineado con backend; `useCan`).
4. Actor con solo `review:review` conserva el centro de revisión; pierde la capacidad de aprobar en lote.

## 7 · Alcance

- `backend/app/review/router.py:143-160` (decoradores de permiso).
- `frontend/src/pages/review/ApprovalPanel.tsx:100,119,173` (gate).
- Tests: `backend/tests/test_r208_batch_approval_authority.py` (nuevo) + extensión de `test_review.py`/`test_rbac`-familia; UI: test de gates existente de GA-FE-05 (si cubre panel) o unit dirigido.
- Sin migración, sin esquemas, sin nuevos permisos (se reutilizan los existentes).

## 8 · Fuera de alcance

- Reanudar el SLA/auditoría de transiciones (E-06; P1-12/tranche de auditoría).
- Cambios de BR-14/R-143 (intactas).
- Semántica de resultados parciales del lote (comportamiento actual del servicio; solo cambia la puerta).

## 9 · Impacto frontend

`ApprovalPanel` (gate de botones). Sin cambio de contrato. Regresión: actores con permiso correcto ven y usan los botones como hoy.

## 10 · Impacto backend

`review/router.py` (dos decoradores). Sin servicio.

## 11 · Contrato frontend↔backend

Mismas rutas y cuerpos. Cambia el 403 para actores sin `approvals:*` (antes 200). Consistente con las unitarias.

## 12 · Impacto en datos

Ninguno.

## 13 · Seguridad

Cierra el hueco de autoridad (E-09) sin tocar la segregación; la política queda uniforme entre unitario y lote.

## 14 · Inquilino

Sin cambio (la pertenencia del evento ya se valida por `_get_event`).

## 15 · Unidad de negocio

Sin cambio (R-165 sigue aplicando por evento).

## 16 · RBAC

Es el objeto del paquete: `approvals:approve`/`approvals:reject` en las rutas por lote.

## 17 · Transacciones

Sin cambio (por evento dentro de la petición, patrón del servicio).

## 18 · Auditoría

Sin cambio en esta spec (las acciones por lote auditan por evento como hoy). Nota E-06/P1-12: la auditoría de transiciones en lote sigue su tranche propia.

## 19 · i18n

N/A (mensaje de permiso existente).

## 20 · Escritorio · 21 · Móvil

`/approvals` es web-only por diseño; sin cambio móvil.

## 22 · Manejo de errores

403 con mensaje de permiso (patrón actual). Sin códigos nuevos.

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

Indirecto (trazabilidad de autoridad de aprobación hacia consolidación).

## 25 · Compatibilidad hacia atrás

- Actores con `approvals:*`: idéntico.
- Actores con solo `review:review`: pierden la aprobación en lote (corrección).
- Roles semilla: «TEST Aprobador»/roles de revisión se revisan en la certificación para asignar el permiso correcto donde corresponda (decisión de administración, no de código).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R208-01 | Actor con `review:review` sin `approvals:approve`: `batch-approve` ⇒ **403**; cero cambios de estado |
| AC-R208-02 | Actor con `approvals:approve`: `batch-approve` ⇒ 200/según servicio; eventos aprobables transicionan |
| AC-R208-03 | `batch-reject` simétrico para `approvals:reject` |
| AC-R208-04 | BR-14 por evento intacta: revisor que rechazó no aprueba (403 por evento, no por lote completo) — control |
| AC-R208-05 | UI: botones de lote visibles solo con `approvals:*` (unit de gate) |
| AC-R208-06 | Unitarias sin cambio (control) |
| AC-R208-07 | Sin migración/endpoint/permiso nuevo; diff limitado a router + panel + tests |
| AC-R208-08 | Regresión: `test_review.py`, `test_review_bu_enforcement.py`, `test_review_decision_concurrency.py`, `test_r166*`, tests de GA-FE-05 (si tocan el panel) verdes |

## 27 · Pruebas RED→GREEN

`R-208_RED_E2E_UAT_DESIGN.md §1`: `test_r208_01_revisor_sin_permiso_no_aprueba_en_lote` (rojo: 200), `test_r208_02_aprobador_aprueba_en_lote` (control), `test_r208_03_reject_simetrico`, `test_r208_04_br14_por_evento` (control), `test_r208_05_gate_ui` (unit frontend, rojo si gatea por `review:review`).

## 28 · E2E

API sobre pila local (`§2`): `R208-RT-01…04` (revisor denegado; aprobador OK; reject; BR-14). UI regresión: panel con ambos actores. Artefacto `evidence/r208/runtime-{red,c3}.json`.

## 29 · UAT

**No requiere UAT del propietario** (control interno). Nota para administración de roles: al cambiar la puerta, los roles de aprobación deben portar `approvals:approve/reject` (ya es el patrón canónico en las unitarias).

## 30 · Criterios de cierre

RED válida · GREEN local · sensibilidad (S1: revertir permiso del batch ⇒ AC-01 roja) · sin migración/endpoint/permiso nuevo · R-208 → `CLOSED` con GA-REM asignado.

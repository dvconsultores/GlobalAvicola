# GA-FE-05 · MATRIZ PANTALLA/ACCIÓN (submit / resubmit)

Página canónica: `/operations/:id` — `frontend/src/pages/operations/OperationDetailPage.tsx` (responsive: desktop y móvil comparten componente). Ruta protegida por GA-FE-03 (`operations:read`).

| Estado | Actor | Permiso requerido | CBU | User BU | CTA visible | Label ES | Label EN | Resultado backend esperado | Estado post-acción |
|---|---|---|---|---|---|---|---|---|---|
| `registered` | Operador productivo | `operations:create` | ON | concedida | **SÍ** | Enviar a revisión | Submit for review | `200` | `pending_review` |
| `returned` | Operador productivo | `operations:create` | ON | concedida | **SÍ** | Reenviar a revisión | Resubmit for review | `200` | `pending_review` |
| `rejected` | Operador productivo | `operations:create` | ON | concedida | **SÍ** | Reenviar a revisión | Resubmit for review | `200` | `pending_review` |
| cualquiera de los 3 | Sin RBAC (`operations:create` ausente) | — | ON | — | **NO** | — | — | `403` (require_permission) | sin cambio |
| cualquiera de los 3 | Cero unidades efectivas (Z) | `operations:create` | ON | sin concesión | **NO** | — | — | `403` (guarda operativa) | sin cambio |
| cualquiera de los 3 | CBU OFF (empresa apagada) | `operations:create` | OFF | (lo que sea) | **NO** (sin unidades) | — | — | `403 AC-W13` | sin cambio |
| cualquiera de los 3 | Global (E) | comodín | ON | no exigida | **SÍ** si CBU ON + contexto | Enviar/Reenviar | — | `200` / `403` si CBU OFF | `pending_review` / sin cambio |
| `pending_review`, `in_review`, `corrected`, `approved`, `consolidated`, `sent_to_sap`, `sap_confirmed`, `sap_error`, `cancelled`, `reversed`, `draft` | cualquiera | — | — | — | **NO** | — | — | `400` si se fuerza | sin cambio |
| estado no reenviable | cualquiera | `operations:create` | ON | concedida | **NO** | — | — | `400` | sin cambio |

## Detalle de UI

- **Ubicación**: cabecera de la tarjeta «Evento» del detalle (acción primaria a la derecha del título/estado), mismo lugar en 390×844 (sin menús de desborde).
- **Loading**: botón `disabled` + estado de carga mientras la mutación está en vuelo (protección de doble clic).
- **Confirmación**: sin modal (patrón de la casa para transiciones directas del flujo de revisión: `start` en `ReviewCenter` es directo); el resultado se confirma con toast + estado fresco (§23 y C12).
- **Refresh**: tras éxito y tras fallo ⇒ `GET /operations/:id` fresco; el chip y el CTA se recomputan desde verdad del backend.
- **Chip de estado**: `t('status.<estado>')` con fallback al valor crudo (claves ya existentes; se añaden `draft`, `sap_error`, `reversed`).
- **Sin CTA duplicado** en la misma pantalla/estado.

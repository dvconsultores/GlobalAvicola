# GA-FE-04 · RECONCILIACIÓN DE CIERRE R-98

Fecha: 2026-09-11 · Generación: `index-B66tpdeW.js` (C2 `de40d36`) · Programa: P-13 «Gestión de usuarios, roles y permisos» — residuo intra-pantalla.

## 1 · Texto canónico y su cobertura

**`GA-REM-037` · `AC-FE16`** (fuente autoritativa):
> «La interfaz respeta RBAC: quien solo lee no ve acciones de escritura, y el backend sigue siendo la autoridad —ocultar un botón no es autorizar—.»

**`R-96` certificación §5** (origen del residuo):
> «Lo que no se verificó, porque no existe: ocultar botones según el permiso del usuario… es trabajo de P-13… Queda registrado como R-98.»

**Backlog R-98**:
> «Ninguna pantalla oculta acciones de escritura por permiso: no hay modelo de permisos en el frontend | P2 — OPEN · transversal, pertenece a P-13.»

| Condición | Estado GA-FE-03 | Cobertura GA-FE-04 | Evidencia | Estado final |
|---|---|---|---|---|
| Ocultar acciones de escritura cuando solo hay lectura | PARCIAL (solo navegación/rutas) | 12 superficies con gates por **permiso de acción** (31 acciones mapeadas) | Vitest 22/22 (10 objetivos RED→GREEN) · runtime R: masters 0/0/0 (pre 1/7/7) · users Crear=0 (pre 1); móvil 0/0/0 | **CUBIERTA** |
| El backend sigue siendo la autoridad | CUBIERTO (authz backend intacta) | Re-verificado en la generación congelada | 403 en PUT/POST/DELETE masters y POST users con token de R; lecturas 200 | **CUBIERTA** |
| Modelo único (sin segundo sistema) | Evaluador único `auth/navigation.ts` | `auth/actionAuthority.tsx` reexpone `canAccessCapability` (alias `canPerformAction`) + `useCan` + `ActionGate` | spec §18 · tests de equivalencia de vocabulario | **CUBIERTA** |
| Sin gating por rol/username | — | grep en archivos modificados: 0 coincidencias de comparación por nombre/rol; todo es permiso canónico | revisión C2 | **CUBIERTA** |
| Paridad ruta↔acción (deep links de alta) | PARCIAL (rutas de lectura con guarda) | `/lots/new`=lots:create · `/operations/new`=operations:create · `/review/:id/correct`=corrections:correct | test paridad 4/4 · runtime R: 3/3 negadas | **CUBIERTA** |
| Aprobación ≠ rechazo | — | Gates separados `approvals:approve` / `approvals:reject`; lote=`review:review` | tests ApprovalPanel 3/3 (incl. approve-sin-reject) | **CUBIERTA** |

## 2 · Condiciones de cierre (C1–C5 del doc canónico)

| # | Condición | Verificación | Estado |
|---|---|---|---|
| C1 | Actor con SOLO lectura no ve/acciona controles de escritura | R: 0 controles en masters/users (desktop+móvil); D/Z: negativa visual; P: negativa pese a concesión | ✅ |
| C2 | Backend permanece autoridad | 403 directos con la generación congelada (§3) | ✅ |
| C3 | Modelo compartido, sin segundo sistema | `actionAuthority` ≡ `canAccessCapability`; mismo vocabulario `modulo:accion` | ✅ |
| C4 | Sin gating por nombre de rol ni username | revisión de diff + grep: 0 | ✅ |
| C5 | Evidencia runtime autenticada por actor + no-regresión GA-FE-02/03 | runtime por actor (E/A/B/C/D/P/R) + suite completa 263/263 + superficies GA-FE-02 (UnitAccess/UBU) sin regresión | ✅ |

## 3 · No-regresión de tranches previas

- GA-FE-02 (pantallas de acceso por unidad): intactas; A/B operan `/admin/unit-access` con toggles visibles.
- GA-FE-03 (navegación dinámica): sin cambios en el evaluador; suite de navegación sigue verde (263/263 total).
- UAT aceptado (GA-UAT-01): las superficies aceptadas no cambiaron de comportamiento para actores con permiso (control positivo E/C verificado).

## 4 · Veredicto

**R-98 = CLOSED.**
Motivo: la conducta exigida por `AC-FE16` (ocultar por permiso, backend autoridad) y el residuo declarado por `R-96 §5`/backlog (ninguna pantalla ocultaba acciones) están implementados, probados (unidad + runtime), evidenciados y sin gating por rol/nombre. El cierre no invoca nuevas excepciones: R-181/R-182 permanecen UNCHANGED; BU-D10 PENDING_RATIFICATION.

> Matiz honesto registrado: la autoridad de acción visible es **descubribilidad**; la autorización efectiva continúa siendo del backend (verificado con 403). No se declaró ningún AC extra (p. ej., «todas las pantallas del producto») más allá del texto canónico.

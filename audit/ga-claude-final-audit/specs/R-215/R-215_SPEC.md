# R-215 · SPEC — RENDER SEGURO DE ERRORES ESTRUCTURADOS Y `ErrorBoundary` GLOBAL

Fecha: 2026-09-13 · Hallazgo canónico: **R-215** (P2 · bloquea) · HEAD `c0b4afc` · Origen B-15/C#6/#7 · Registro G-27. Secciones §47.

## 1 · Contexto

Los errores de FastAPI llegan con `detail` string o **lista** (422). Pintar la lista como hijo de React lanza React #31. El normalizador `getErrorMessage` existe desde R-189; falta propagarlo y añadir un límite de error.

## 2 · Evidencia

`R-215_FINDING.md §1`.

## 3 · Causa raíz

Helper no propagado + ausencia de `ErrorBoundary`.

## 4 · Impacto de negocio

Pantalla en blanco ante errores gobernados; pérdida de formulario/contexto; riesgo de que el usuario crea que la app «se rompió» con datos correctos.

## 5 · Comportamiento actual → esperado

| Superficie | Hoy | Esperado |
|---|---|---|
| MasterListPage | React #31 con 422 | texto (helper) |
| LotFormPage | `detail` crudo en toast | texto |
| TraceabilityTree | `detail` crudo | texto |
| ProfilePage | `detail` crudo | texto |
| UsersPage | `alert('[object Object]')` | texto (o mensaje normalizado; coordina R-195) |
| Cualquier excepción de render | app en blanco | `ErrorBoundary` con mensaje y acción «recargar/volver» |

## 6 · Comportamiento esperado

1. **Propagación**: los 5 consumidores usan `getErrorMessage` (o el helper de toast) para `detail`; sin objetos como hijos.
2. **`ErrorBoundary` global** (clase con `componentDidCatch`): envuelve `App` (o el `<Outlet/>` del layout); renderiza pantalla de recuperación (mensaje i18n, botón «Reintentar»/«Recargar», sin stack visible); registra `console.error` (sin datos sensibles).
3. **Boundary por sección** opcional (si se decide C-02): el fallo de una página no tumba la navegación — por defecto global + opcional en el layout principal si coste bajo.
4. Sin cambio de backend.

## 7 · Alcance

- `components/ErrorBoundary.tsx` (nuevo) + integración en `main.tsx`/`App.tsx`.
- 5 consumidores listados.
- Tests: `frontend/.../__tests__/r215.errorRendering.test.tsx` (render con `detail` lista ⇒ sin throw; boundary captura excepción simulada y muestra recuperación).
- i18n ES/EN: 2-3 claves del boundary.

## 8 · Fuera de alcance

- Normalización por código de regla (`rule` no mostrado: C#28 → R-220).
- `switch-company` sin catch y otros residuales de error (R-220).
- Telemetría/observabilidad (P1-5/GA-TD-039).

## 9 · Impacto frontend

5 consumidores + boundary global. Sin rediseño.

## 10 · Impacto backend

Ninguno.

## 11 · Contrato frontend↔backend

Sin cambio (solo render del error).

## 12 · Impacto en datos · 13 · Seguridad · 14 · Inquilino · 15 · Unidad · 16 · RBAC · 17 · Transacciones · 18 · Auditoría

Sin cambio.

## 19 · i18n

| Clave | ES | EN |
|---|---|---|
| `common.errorTitle` | Algo ha ido mal | Something went wrong |
| `common.errorReload` | Recargar la página | Reload page |
| `common.errorBack` | Volver al inicio | Go home |

## 20 · Escritorio · 21 · Móvil

Boundary usable en ambos; pantalla de recuperación responsive.

## 22 · Manejo de errores

Es el objeto: sin `detail` crudo, sin objeto como hijo, sin traza visible, con recuperación.

## 23 · Impacto de migración · 24 · Impacto SAP

Ninguna / indirecto.

## 25 · Compatibilidad hacia atrás

- Mensajes: pasan de «roto» a texto (mejora).
- Sin cambio de flujos.

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R215-01 | 422 lista en maestros ⇒ texto legible (sin React #31; sin pantalla en blanco) |
| AC-R215-02 | 422 en LotFormPage/TraceabilityTree/ProfilePage ⇒ texto legible |
| AC-R215-03 | UsersPage ⇒ sin `[object Object]` (coordinado R-195) |
| AC-R215-04 | Excepción simulada de render ⇒ `ErrorBoundary` muestra recuperación con botón funcional |
| AC-R215-05 | Sin stack traces visibles; sin datos sensibles en el mensaje |
| AC-R215-06 | ES/EN de las claves del boundary |
| AC-R215-07 | Sin migración/endpoint/permiso; diff FE (+tests) |
| AC-R215-08 | Regresión: `f01.errorRendering` (asistente) intacto; vitest completa; tsc; build |

## 27 · Pruebas RED→GREEN

`§1`: `r215.errorRendering` (rojo: throw con `detail` lista; boundary inexistente) + controles.

## 28 · E2E

`§2`: `R215-RT-01…04` (repro maestros 422 ⇒ texto; boundary; ES/EN; móvil). Artefacto `evidence/r215/`.

## 29 · UAT

`UAT-R215-01…02` (agrupable): provocar un error en maestros ⇒ mensaje claro, app usable; forzar error de render (si es posible de forma inocua) ⇒ página de recuperación. 2/2.

## 30 · Criterios de cierre

AC-01…08 verdes · RED en `c0b4afc` · GREEN local · runtime con artefactos · UAT 2/2 · sin migración/endpoint/permiso · R-215 → `CLOSED` con GA-REM asignado.

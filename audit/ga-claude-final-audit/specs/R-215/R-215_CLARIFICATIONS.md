# R-215 · CLARIFICACIONES

Fecha: 2026-09-13 · HEAD `c0b4afc` · Resolver antes de C2.

| # | Pregunta | Supuesto por defecto | Fuente | Decisión |
|---|---|---|---|---|
| C-01 | ¿Boundary global o por sección? | **Global** en `main.tsx`/`App.tsx` + opcional por sección en el layout si el coste es bajo (C-02). | `main.tsx`; `App.tsx` | técnica |
| C-02 | ¿Boundary por sección además del global? | Evaluar en C2 (si envuelve `<Outlet/>` sin efectos raros); por defecto solo global. | diseño | técnica |
| C-03 | ¿`getErrorMessage` o mover a toast con normalización interna? | Reutilizar `getErrorMessage` (helper único); mover la normalización al `ToastProvider` como red de seguridad adicional (si aplica). | `Toast.tsx:95-140` | técnica |
| C-04 | ¿Se muestran `rule`/código? | No en este paquete (C#28 → R-220). | informe C | técnica |
| C-05 | ¿Log del boundary? | `console.error` (sin PII); telemetría futura (P1-5) fuera. | diseño | técnica |
| C-06 | ¿Repro de `LotFormPage`/`TraceabilityTree`/`ProfilePage` en runtime? | Unit jsdom suficiente para el render; E2E cubre maestros (repro real) y boundary. | informes | técnica |

Sin decisiones abiertas que bloqueen.

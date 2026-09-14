# R-212 · CERTIFICACIÓN TÉCNICA LOCAL — UI consciente del permiso (403 ≠ «vacío»)

Fecha: 2026-09-14 · Programa: GA PRE-SAP (T11) · Política: **AOD-29 Clarification 01**.

## 1 · Paquetes y commits

| Fase | SHA | Contenido |
|---|---|---|
| C1 · RED | **`0583426`** | `r212.permissionAwareness` FE 13F por causa exacta (10× «alert» ausente = 403/500 como vacío; home sin landing; KPIs sin gate) |
| C2 · Implementación | **`abf1888`** | `ErrorState` reutilizable (prohibido/error + reintento); `LotDetailPage` no pide KPIs sin `reports:read`; `HomeRoute` cae a `/menu/poultry` sin `dashboard:read`; estados distinguidos en Operaciones, Lotes, Auditoría, Reportes, Maestros, Roles, SAP y Corrección; `LotReportPage`/`SapComparisonPage` fin del spinner eterno con reintento; SAP deja de silenciar 403 |

Sin migración/endpoint/permiso nuevos; diff FE + tests (AC-R212-07).

## 2 · Gates locales (PASS)

| Gate | Resultado | Evidencia |
|---|---|---|
| FE targeted R-212 | **15/15** | `green/fe-r212-green-targeted.log` |
| FE suite completa | **448/448** | `green/fe-r212-green-full.log` |
| `npm run build` | **EXIT 0** | `green/fe-r212-build.log` |
| BE | no requerida (`BACKEND_DIFF = 0` en este paquete) | — |

## 3 · Sensibilidad (restore `abf1888`)

M1 gate KPIs ⇒ AC-01a · M2 home ⇒ AC-02 · M3 403-como-vacío ⇒ operaciones {403,500}
· M4 spinner eterno ⇒ AC-05 LotReport · M5 sin distinción de textos ⇒ 9 superficies
(coherente: una sola fuente). Post-mutación **15/15**.

## 4 · Notas

- **AC-R212-03** (centro de revisión sin `/users`): cubierto y en verde por **R-197**
  (`r197.reviewQueue` AC18); aquí queda como contrato referido.
- El mock de `TraceabilityTree` en el harness es aislamiento de un colateral no
  relacionado (su contrato tiene pruebas propias).
- UAT: **no requerida** (calidad interna; SPEC §4).

## 5 · Estado

- **R-212 = `CLOSED_TECHNICALLY`** · T11 continúa con **R-218** y **R-220**.

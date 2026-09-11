# GA-FE-08 · OBS-UAT-01 — RECONSTRUCCIÓN DE LA FUENTE

Fecha: 2026-09-11 · Baseline: `30fe3dc` · Autorización: propietario (tranche GA-FE-08, «solo si la observación sigue presente»).

## 1 · Primera observación

- **Sesión:** GA-UAT-04 (UAT del propietario de GA-FE-06), fila **UAT-01**:
  > «El producto **no tiene entrada de menú «Lotes»** (solo URL directa). Pre-existente, no es regresión de GA-FE-06. Recorrido completado con enlace facilitado» — `audit/ga-uat-04/GA_OWNER_UAT_GA_FE_06_OBSERVATIONS.md:8`.
- Nota de ingeniería pre-sesión (mismo archivo, l.25):
  > «la configuración de navegación no contiene ningún ítem «Lotes» (`navigationConfig.ts`) y ningún enlace apunta a `/lots` desde otras pantallas. No es regresión de GA-FE-06; es un vacío de descubrimiento pre-existente.»

## 2 · Significado original exacto

El estado «`/lots*` sin fuente de menú» **precedía** a la observación y estaba inventariado y decidido en GA-FE-03:

- `audit/ga-fe-03/GA_FE_03_NAV_SOURCE_INVENTORY.md:34-36`: «Rutas sin fuente de menú (12): `/operations*`, `/my-pending`, **`/lots*`**, `/reports/lot/:id`, `/review/:id*`… Se rigen por guardas de ruta y backend; sin entradas nuevas salvo `Roles`.»
- `GA_FE_03_DYNAMIC_NAVIGATION_SPEC.md:59`: «No se crean entradas nuevas de producto más allá de `Roles`.»
- `GA_FE_03_ROUTE_CAPABILITY_MATRIX.md:25`: «`/lots` | LotListPage | (sin entrada; links) | … guarda `lots:read`».

## 3 · Clasificación formal (GA-GOV-01)

- **`UX_ENHANCEMENT_ONLY · P2 · sin R`** — `audit/ga-gov-01/GA_GOV_01_CLASSIFICATION_DECISIONS.md:7-19` («No defecto: falla §23.4/§23.5 — el estado está inventariado y decidido en GA-FE-03; es preferencia de mejora»). Tabla resumen l.86; veredicto final l.98.
- **No duplicado** (`GA_GOV_01_DEDUP_REPORT.md`): distinto de R-119 (autorización de entradas existentes), R-98, GA-FE-03 (registro canónico), R-181/R-135 (vertical inexistente); «sin expectativa canónica violada».
- **NO reabre** R-119, GA-FE-03, GA-FE-06. **NO** se creó finding R.

## 4 · Gap visible real

El usuario autorizado no podía alcanzar la superficie de Lotes por navegación normal; solo por URL directa (en GA-UAT-04/05/06 se «facilitaron accesos directos» en las guías — conveniencia operativa, sin cambio de producto). Reproducción propia de esta tranche (pre-fix, runtime `30fe3dc`): sidebar **sin** «Lotes», hub `/menu/poultry` **sin** tarjeta, móvil **sin** entrada; URL directa OK (`P01-P03`, `evidence/`).

## 5 · Dueño canónico

Backlog GA-GOV-01 **«Mejoras de navegación P2 (sin R)»** (`REMEDIATION_BACKLOG.md:1809-1813`; roadmap l.136 «candidato natural para la próxima iteración de navegación»). La tranche **GA-FE-08** la implementa por autorización explícita del propietario.

## 6 · Determinación §12 (DEDUP / REOPEN RULE)

| Opción | Resultado | Prueba |
|---|---|---|
| FRAMEWORK_DEFECT | **NO** | GA-FE-03 certificado y vigente: una sola política, evaluador funcionando para las entradas existentes; 0 contradicción de AC |
| ALREADY_RESOLVED | **NO** | Runtime pre-fix: sin entrada en sidebar/hub/móvil; `nav.lots` sin uso (grep 0) |
| **MISSING_NAV_CONFIGURATION** | **SÍ** | La ausencia es una entrada **no registrada** en `NAV_ITEMS`; la solución es configuración de navegación |
| OTHER | NO | — |

**No se reabre** GA-FE-03 · R-119 · GA-FE-04 · R-98. **No se crea R nuevo** (OBS-UAT-01 posee el trabajo; §13).

## 7 · Propagación (sin cambio hasta hoy)

Menciones «sin cambio» en GA-FE-07, GA-UAT-05/06/07/08, R-184/186/187/188, GA-GOV-02 (p. ej. `audit/ga-uat-08/GA_OWNER_UAT_R188_OBSERVATIONS.md:23` N-3). Ninguna tranche previa intentó la entrada.

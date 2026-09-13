# R-208 · FINDING — `batch-approve`/`batch-reject` EXIGEN `review:review` EN LUGAR DE `approvals:*`

| Campo | Valor |
|---|---|
| **ID canónico** | **R-208** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | Las rutas por lote de aprobación exigen `review:review` mientras las unitarias exigen `approvals:approve`/`approvals:reject`: un revisor **sin** capacidad de aprobar aprueba/rechaza en lote |
| **Severidad** | **P2** (§49: control interno/autoridad de acción; aprobación válida sin el permiso designado) |
| **Clase** | `SECURITY` (RBAC/authority) / `STATE_FEEDBACK` (gates UI alineados) |
| **Proceso** | P-07 (revisión → corrección → aprobación) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) |
| **Familia** | E-09 (informe E §2 T13); vecinos BR-14 (segregación), R-143 (permiso en approve unitario), OD-17 |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-208/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre **GA-REM-043** |
| **Bloquea SAP** | **SÍ** (integridad del proceso de aprobación; trazabilidad de autoridad) |
| **UAT del propietario** | no (control interno; verificación por API + regresión UI del panel) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `backend/app/review/router.py:123-160` — `POST /approvals/batch-approve` y `/batch-reject` con `require_permission("review","review")`; contrasta con `POST /approvals/approve|reject` (`:123-140`) que exigen `approvals:approve`/`approvals:reject`.
- `frontend/src/pages/review/ApprovalPanel.tsx:100,119,173` — los botones de lote se gatean por `review:review` (consistente con el backend actual, inconsistente con la autoridad deseada).
- BR-14 (segregación: quien revisó/decide no aprueba su propio evento) se aplica por evento dentro del lote (misma ruta de servicio), pero la **puerta** de autoridad del lote es más débil que la unitaria.

### 1.2 Cobertura de tests

Los tests existentes de aprobación (`test_review.py`, `test_review_bu_enforcement.py`) cubren rutas unitarias; los batch aparecen como `UNKNOWN` en la matriz de backend (sin test HTTP directo). Sin caso de «revisor sin `approvals:approve` aprueba en lote».

## 2 · Causa raíz

Al añadir la operación por lote se reutilizó el permiso del centro de revisión (`review:review`) en lugar del permiso de la operación que realmente ejecuta (aprobar/rechazar). Deriva de permisos entre tranches (OD-17/GA-REM-023) sin prueba de autoridad por lote.

## 3 · Impacto

- Autoridad de aprobación ejercida sin el permiso designado (`approvals:approve`), en lote (más alcance que la unitaria).
- Inconsistencia de política entre dos puertas de la misma acción; riesgo de que el permiso correcto se delegue mal (el revisor «solo revisa» podría aprobar en masa).
- La segregación por evento sigue protegida (BR-14), pero la puerta de permiso no.

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | `R-143` (permiso y segregación en approve unitario), `R-142` (estado CORRECTED), `OD-17` — ninguno cubre la puerta de los batch |
| GA-REM-001…042 | `GA-REM-023` (edición pre-revisión) no cubre batch |
| Informe E | E-09: «No (grep batch-approve → 0)» — sin registro previo |

Conclusión: **nuevo**; ID asignado **R-208**.

## 5 · Propietario sugerido

Equipo backend (`review`) + un ajuste menor de UI (`ApprovalPanel`). Sin migración.

## 6 · Bloquea SAP y por qué

**SÍ.** La autoridad de aprobación es el control que garantiza que los eventos consolidados hacia SAP fueron aprobados por quien debe; una puerta débil rompe esa garantía en la operación por lote.

## 7 · Interdependencias

- **R-197** (centro de revisión): misma superficie UI; no solapan (R-197 trata pestañas/filtros/historial).
- **R-207** (reverso sin UI): el motor de aprobación es compartido (contrapartidas); el cambio de permiso aplica también a la aprobación de contrapartidas por lote.
- **R-212** (UI consciente del permiso): el gate del panel queda alineado con el permiso correcto.

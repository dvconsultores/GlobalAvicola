# R-215 · FINDING — ERRORES ESTRUCTURADOS (422) RENDERIZADOS COMO HIJOS DE REACT FUERA DEL ASISTENTE; SIN `ErrorBoundary`

| Campo | Valor |
|---|---|
| **ID canónico** | **R-215** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | Cinco superficies ignoran el normalizador `getErrorMessage` y pintan `detail` crudo (React #31: «Objects are not valid as a React child»); no existe `ErrorBoundary` global: cualquier excepción de render deja la app en blanco sin recuperación |
| **Severidad** | **P2** (§49: pantalla en blanco; convierte cada 422 en app rota — es el multiplicador de los demás defectos) |
| **Clase** | `ERROR_HANDLING` / `ACCESSIBILITY`(recuperación) |
| **Proceso** | transversal (P-12, P-13, lotes, trazabilidad, perfil) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` |
| **Familia** | B-15 (informe B); C#6/#7 (informe C); extiende la corrección R-189 (limitada al asistente); I.10-error del encargo §14 |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-215/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Bloquea SAP** | **SÍ** (pantalla en blanco en superficies de proceso; §14/§40) |
| **UAT del propietario** | sí (visible: provocar un error y ver mensaje, no pantalla blanca) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- Consumidores con `detail` crudo:
  - `frontend/src/pages/masters/MasterListPage.tsx:99,201-205` — `setFormError(detail)` → `<p>{formError}</p>`.
  - `pages/lots/LotFormPage.tsx:137` — `toast.error(err?.response?.data?.detail ?? …)`.
  - `components/TraceabilityTree.tsx:95,114,347,389` — `setLinkError(detail)`.
  - `pages/profile/ProfilePage.tsx:38,70` — `setMessage(detail)`.
  - `pages/users/UsersPage.tsx:85` — `alert(detail)` ⇒ «[object Object]» (no crash, pero detalle perdido).
- Normalizador disponible y probado: `components/Toast.tsx:95-140` (`getErrorMessage`).
- Sin `ErrorBoundary`: `grep ErrorBoundary|componentDidCatch` en `frontend/src` = 0; `main.tsx`/`App.tsx` sin límite de error.
- Evidencia runtime local: `MAS-hatchery-create-ui` y `H4-masters-house-create-ui` ⇒ `pageerror` React #31 ×2 (`E99-adm-exception.png` en blanco); repro directo documentado en el informe C (#6).

### 1.2 Alcance

R-189 corrigió el asistente (y las superficies que ya usaban el helper); quedan 5 consumidores. El boundary global falta para cualquier excepción (no solo estas).

## 2 · Causa raíz

`getErrorMessage` se introdujo en R-189 y no se propagó a todas las superficies; nunca existió límite de error de React.

## 3 · Impacto

- Convierte errores de negocio gobernados (422) en pantalla en blanco (pérdida de contexto y de formulario).
- Sin boundary, cualquier excepción futura de render (no solo 422) deja la app sin recuperación ni aviso.

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | R-189 limitó su alcance (AC19-26 del asistente); `R-120`/`R-150` tratan estados de error de carga, no el render de `detail`. |
| Informes B/C | B-15 + C#6/#7: sin registro previo propio; P1-12 no aplica. |

Conclusión: **nuevo**; ID asignado **R-215**. Tranche contigua a R-196/R-195 (misma sesión UAT de errores).

## 5 · Propietario sugerido

Frontend (5 superficies + boundary). Sin backend.

## 6 · Bloquea SAP y por qué

**SÍ**: §14/§40 exigen que un 4xx no rompa la UI; es puerta funcional de calidad (y el multiplicador de otros defectos de contrato).

## 7 · Interdependencias

- **R-196** (maestros): su 422 es el caso demostrador; el fix de R-196 ya usa el helper — verificación conjunta.
- **R-195** (usuarios): `alert` → normalizado (decisión C-02 de R-195).
- **R-189**: helper canónico; sin cambios.
- **R-220** (residuales): otros puntos menores de error (p. ej. `switch-company` sin catch) quedan allí.

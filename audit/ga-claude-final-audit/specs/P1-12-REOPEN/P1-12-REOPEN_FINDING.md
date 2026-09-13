# P1-12 · REAPERTURA — AUDITORÍA DUPLICADA EN RUNTIME E INCOMPLETA POR PRODUCTOR

| Campo | Valor |
|---|---|
| **ID canónico** | **P1-12 (REAPERTURA)** — riesgo P1 original `P1-12` («auditoría duplicada e incompleta»); reabierto por esta auditoría con evidencia de runtime (el programa lo daba por cubierto por «GA-REM-003 AC06 + GA-REM-019», sin evidencia de cierre) |
| **Título** | En runtime real (uvicorn + `lifespan`) la auditoría escribe **2-3 filas por acción** (listener `after_flush` + helpers) y **omite** acciones clave (cierre/activación/fases de lote, usuarios, evidencias, curvas, exportaciones); además `complete_review` escribe una fila `corrected` espuria al aprobar |
| **Severidad** | **P2** (§49: integridad de la traza; P1-12 original era P1 — se mantiene P2 condicional como en el registro, con evidencia runtime) |
| **Clase** | `DATA_INTEGRITY` (auditoría) / `GOVERNANCE` |
| **Proceso** | P-09 (auditoría interna) transversal |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` |
| **Familia** | E-11/E-10/E-12/E-13/E-15/E-16 (informe E); D H.3 (`UNKNOWN` de duplicación), `R-148` (inmutabilidad), `R-83` (empresa), `GA-REM-032` (cobertura) |
| **Paquete** | `audit/ga-claude-final-audit/specs/P1-12-REOPEN/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Bloquea SAP** | **SÍ** (integridad de la traza; la auditoría es evidencia de aprobación/efectos hacia P-08) |
| **UAT del propietario** | no (superficie técnica; verificación por API/UI de auditoría) |

## 1 · Evidencia

### 1.1 Duplicación (runtime)

- `backend/app/main.py:41-42` — `register_audit_listeners()` dentro de `lifespan`; el listener `after_flush` (`audit/listeners.py:71-113`) escribe `CREATED`/transiciones (`:43-56,163-197,200-263`) y acciones de revisión/corrección/aprobación (`:270-325`).
- Helpers explícitos invocados en los mismos flujos: `operations/service.py:308` (`audit_event_created`), `:1172,1322,1350` (`audit_state_transition`); `review/service.py:285,314,370,377,527,551`.
- Evidencia local (uvicorn con `lifespan`): `ui-e2e-local-pass1.json H6-audit-timeline` y `ui-e2e-local-pass2.json H8b-timeline-*`: **13 filas para 6 acciones** en el original (`created ×2`, `review_started ×3`, `approved ×2`, más filas espurias); `created:registered ×2` en el evento 1.
- Fila espuria: `review/service.py:363` usa `ActionType.CORRECTED` en **ambas** ramas de `complete_review` (también al aprobar) ⇒ `corrected` escrito sin corrección.

### 1.2 Ceguera de los tests

`tests/conftest.py:117-140` usa `httpx.ASGITransport(app=app)` **sin `lifespan`** ⇒ el listener no se registra en tests; aserciones «exactamente 1» (`test_edit_cancel_balance.py:393`; `test_audit_coverage.py:171`) verdes en tests y falsas en runtime.

### 1.3 Acciones sin auditoría (incompletitud)

| Acción | Código | Evidencia |
|---|---|---|
| Cerrar lote | `lots/service.py:438-549` | E-10 |
| Activación manual (saldo de apertura) | `:555-659` | E-10 |
| Fases (cría→producción) | `:685-697` | E-10 |
| Usuarios (alta/edición/baja; cambio de rol) | `auth/service.py:337-421,491-506` | E-13 |
| Evidencias (subir/borrar) | `operations/service.py:1363-1414` | E-15/GAP-12 |
| Curvas (crear/activar) | `masters/curves.py:90,143` | E-12 |
| Exportaciones (Excel/PDF cliente; `REPORTS`) | `frontend/src/utils/export.ts` | E-16 |
| Batch de revisión / contrapartida de reverso (transición sin fila) | `review/service.py:206-243`; `reversals/service.py:131` | E-06 |

### 1.4 Norma

`docs/02 §3.11.1` («cada acción»); `GA-REM-032` (cobertura) — su AC01/AC04 no se cumplen para logout/exportaciones; el cierre técnico de `GA-REM-032` no incluyó estos productores (E).

## 2 · Causa raíz

Dos mecanismos de auditoría coexistiendo (listener + helpers) sin reconciliación ni prueba bajo `lifespan`; productores faltantes por estar fuera del listener (lotes/usuarios/evidencias/curvas) y por tranches no cerradas; rama de `complete_review` mal tipada.

## 3 · Impacto

- Traza inflada y confusa (recuentos dobles/triples; timeline no fiable para SLA de 24 h y para auditoría).
- Acciones críticas sin rastro: cierre de lote, apertura de saldo, cambio de rol de usuario, borrado de evidencia — precisamente las de mayor valor probatorio.
- Certificaciones de auditoría (P-09) no reproducibles con integridad.

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | `R-83` (empresa en audit), `R-148` (inmutabilidad BD), `GA-REM-003 AC06` (auth), `GA-REM-019` (deuda P2), `P1-12` original (abierto, «duplicada» sin cierre). |
| Informe E | E-11 lo reabre con evidencia runtime; E-10/12/13/15/16 completan los productores faltantes. |

Conclusión: **reaperura registrada**; paquete `P1-12-REOPEN` (sin nuevo ID R; se documenta como estado del riesgo existente).

## 5 · Propietario sugerido

Backend (audit + módulos listados). Sin UI nueva (la página de auditoría es R-219).

## 6 · Bloquea SAP y por qué

**SÍ (integridad)**: la aprobación y los efectos pre-SAP deben estar trazados de forma única y completa; la evidencia de auditoría sostiene la certificación.

## 7 · Interdependencias

- **R-219** (`AuditPage` lee campos inexistentes): superficie de lectura; paquete propio.
- **E-06** (batch/reverso sin fila `pending_review`): parte de esta reapertura (productor faltante).
- **GA-REM-032**: reconciliar AC01/AC04 tras el fix.
- **R-83/R-148**: sin cambio aquí (empresa nulable e inmutabilidad BD siguen su registro).

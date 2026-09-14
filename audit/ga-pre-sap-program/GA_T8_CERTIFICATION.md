# GA-CLAUDE · CERTIFICACIÓN T8 — AUDITORÍA Y EVIDENCIAS (P1-12-REOPEN · R-198 · R-219)

Fecha: 2026-09-14 · Tranche **T8** del programa Pre-SAP · Baseline de entrada: T7 CERRADA (`56d0fcb`) · Cierre: `d228eac`…`45acbf8` + este cierre.

## 1 · Alcance ejecutado

| Item | Espec | Estado | Certificación |
|---|---|---|---|
| **P1-12 (REAPERTURA)** · un productor por acción y cobertura completa | `specs/P1-12-REOPEN` | `CLOSED_TECHNICALLY` · C3 runtime en ventana · GA-REM-043 | `GA_CLAUDE_P112_RUNTIME_CERTIFICATION.md` |
| **R-198** · evidencias del detalle, gate por estado y borrado atómico | `specs/R-198` | `CLOSED_TECHNICALLY` · C3 runtime en ventana | `GA_CLAUDE_R198_RUNTIME_CERTIFICATION.md` |
| **R-219** · `AuditPage` contra el contrato real | `specs/R-219` | `CLOSED_TECHNICALLY` · C3 runtime en ventana | `GA_CLAUDE_R219_RUNTIME_CERTIFICATION.md` |

## 2 · Criterio de salida (ficha T8) — verificación

| Criterio | Estado |
|---|---|
| RED→GREEN→sensibilidad por spec | ✅ P1-12 (BE 6F/13P → 8F → 8/8; S1 2F/S2 1F) · R-198 (BE 5F/2P + FE 3F/1P → 7/7 + FE 4/4; S1 3F/S2 1F/S3 1F) · R-219 (FE 5F → 5/5; S1/S2/S3 1F) |
| «La trazabilidad única y fiable antes de certificar procesos» | ✅ Un productor por acción en runtime **y** sin listener (guarda compartida); decisiones por transición de estado; batch/contrapartida con transición explícita; cobertura de las siete acciones que no dejaban rastro |
| Suite completa BE con artefacto | ✅ **1364/0/49** (`evidence/t8/full_suite_t8.log`; 1 276.81 s — 1349 de T7 + 8 de P1-12 + 7 de R-198) |
| Suite FE + tipos + build | ✅ **399/399** (`specs/R-219/evidence/green/fe-suite-399.log`) · `tsc -b`/`npm run build` 0 (`evidence/t8/fe-build.log`) — un defecto de tipos de `AuditPage` (`t()` no-string) lo detectó **`tsc -b`** (no `tsc --noEmit`) y se corrigió antes del cierre (`String(...)`) |
| Regresión obligatoria del plan | ✅ P1-12: 207/207 (auditoría + superficies tocadas, con arnés runtime en `test_audit_coverage`/`test_edit_cancel_balance`) · R-198: 122/122 · R-219: FE 399/399 |
| Evidencia en el hogar del programa | ✅ certificaciones por spec + `specs/{P1-12-REOPEN,R-198,R-219}/evidence/` + esta certificación |
| Runtime (EX-01) | ⏸ ventana de deploy (familia G-06): recuento por acción en UI de auditoría (P1-12) · subir/F5/gate/borrado (R-198) · captura `/audit` (R-219) |
| UAT del propietario | ⏸ no requerida por los paquetes (superficie técnica; UAT mínima informativa de R-198 se recoge en la ventana) |
| GA-REM-032 reconciliado | ✅ C-03=A: logout (ya cerrado vía GA-REM-003 AC04); exportaciones cliente `NOT_APPLICABLE_CLIENT` |

## 3 · Riesgo residual y límites declarados

- **C3 runtime** pendiente de ventana en los tres paquetes; el comportamiento está demostrado con el **listener activo en tests** (fidelidad de runtime) y jsdom con la misma forma de contrato.
- Los **helpers** de auditoría se conservan (inertes en runtime por la guarda) para scripts/arnés sin listener — decisión C-01/C-02 registrada en `P1-12-REOPEN_CLARIFICATIONS.md`.
- Históricos con duplicados **no se limpian** (inmutabilidad, R-148).
- R-198: la UI conserva `GET /{id}/evidences` como ruta dedicada; el detalle es la fuente de pantalla.
- R-219: sin `users:read` el nombre degrada a `Usuario #id`; filtros adicionales del backend no expuestos (fuera de alcance).
- Los procesos **P-02 y P-09** quedan **reparados técnicamente**; su `FUNCTIONALLY_CERTIFIED_E2E` sigue dependiendo de la pasada runtime/UAT (KPI de procesos sin cambio: 0/17).
- Cierre **local** según AOD-29: `LOCAL_CERTIFIED_SHA` = commit de cierre de esta certificación; `REMOTE_SYNC_STATUS=NOT_REQUIRED_CURRENT_OWNER_POLICY`; `GITHUB_ACTIONS_STATUS=NOT_APPLICABLE_BY_OWNER_DECISION`.

## 4 · CI

- **`NOT_APPLICABLE_BY_OWNER_DECISION` (AOD-29, 2026-09-14)**: GitHub Actions salió del camino obligatorio de certificación PRE-SAP; la certificación de T8 se sostiene en los gates **locales** (RED/GREEN/regresión/sensibilidad/suites BE-FE/`tsc`). Registro: `GA_OWNER_DECISION_AOD29_GITHUB_ACTIONS_RETIRED.md`.

## 5 · Veredicto

**T8 = `CLOSED_TECHNICALLY`** — la traza es única (un productor por acción), completa (siete productores nuevos) y probada bajo listener; la evidencia del evento sobrevive a F5/relogin con gate en servidor y borrado atómico; y la vista de auditoría lee el contrato real con diff, motivo, usuario y paginación. **T9 (R-215 · R-196 · R-195 — maestros y usuarios) queda HABILITADA** según el DAG (T9 ← T2+T8, satisfechos).

# GA-CLAUDE · CERTIFICACIÓN T2 — FUNDACIÓN DE SEGURIDAD Y SESIÓN

Fecha: 2026-09-13 · Tranche **T2** del programa Pre-SAP (auth/roles/permisos) · Baseline de entrada: T1 CERRADA (AC-06 PASS, run #10) · Cierre: commits `52d0077` → `5044788`.

## 1 · Alcance ejecutado (5 items + CI)

| Item | Espec | Estado | Certificación |
|---|---|---|---|
| **R-199** · autoridad global fabricada desde rol de inquilino (P1) | `specs/R-199` | `CLOSED_TECHNICALLY` · **C3 runtime pendiente G-06** | `GA_CLAUDE_R199_RUNTIME_CERTIFICATION.md` (C1 `32c9906` · C2 `62cd0e1` · C2s 6/6) |
| **R-200** · refresh aceptado como access (P2) | `specs/R-200` | **`CLOSED_FUNCTIONALLY_CERTIFIED`** | `GA_CLAUDE_R200_RUNTIME_CERTIFICATION.md` (C1 `9406573` · C2 `bf1746c` · C3 runtime pre/post: 200 → 401) |
| **R-202** · reset de contraseña sin contexto (P2) | `specs/R-202` | `CLOSED_TECHNICALLY` · **C3 runtime pendiente G-06** | `GA_CLAUDE_R202_RUNTIME_CERTIFICATION.md` (C1 `58b374a` · C2 `fafd262`) |
| **R-208** · batch ≠ unitarias en permisos de aprobación (P2) | `specs/R-208` | **`CLOSED_FUNCTIONALLY_CERTIFIED`** | `GA_CLAUDE_R208_RUNTIME_CERTIFICATION.md` (C1 `11b8f89` · C2 `331ad83` · runtime no destructivo) |
| **GA-REM-003 AC04** · logout con revocación (P1-4) | `specs/remediation` | **`CLOSED_FUNCTIONALLY_CERTIFIED`** | `GA_CLAUDE_GA_REM_003_AC04_CERTIFICATION.md` (C1 `52d0077` · C2 `80ffd82` · runtime: 204 → 401 «Token revocado») |

## 2 · Criterio de salida (ficha T2) — verificación

| Criterio | Estado |
|---|---|
| Los 4 ataques bloqueados con test verde (RED→GREEN por spec) | ✅ R-199 12/12 · R-200 9/9 · R-202 5/5 · R-208 4/4 · AC04 7/7 (+controles) |
| Suites verdes con artefacto | ✅ **BE `1263 passed / 0 failed / 49 skipped`** (`evidence/ga-rem-003/full_suite_c2.log`; 23:43) · **FE 46/46 archivos, 318/318** · **CI**: ver §4 |
| `OD-13.c` registrada | ✅ ya resuelta en gobernanza vigente (`specs/remediation/OD-13-ROLE-AND-PERMISSION-TENANCY.md §3`, 2026-09-08); R-199 la ejecuta y su certificación la cita |
| Regresión OD-14/OD-16 obligatoria | ✅ suites `test_od14_productive_surfaces`, `test_r165*`/`rbu`, `rbac`, `r166` verdes en la suite completa |
| Evidencia en el hogar del programa | ✅ este documento + `evidence/t2-ci-run.json` + certificaciones por spec |
| Runtime (EX-01) | ✅ deploy verificado por commit (`Docker Push — Backend` #117… #124 + Watchtower); sondeos runtime R-200/R-208/AC04 observados post-deploy; R-199/R-202 bloqueados por **G-06** (credenciales privilegiadas, cola del propietario) |
| UAT del propietario | ⏸ lote U1 de T13 (no bloquea el cierre técnico de T2) |

## 3 · Riesgo residual y límites declarados

- **G-06** (cola del propietario): C3 runtime de R-199 y R-202 (probar «super sin contexto ⇒ 4xx» y «admin `users:update` ⇒ 204» exige actores privilegiados que no existen en las credenciales UAT-09). Sus certificaciones quedan `CLOSED_TECHNICALLY` con la ruta de sondeo lista.
- GA-REM-003: cerrado **AC04** (logout/revocación). AC01/AC02/AC03/AC05/AC06-resto/AC07 del spec siguen su recorrido propio (ya cubiertos en parte por tranches previos de FE/sesión).
- Ventana del access tras logout ≤ 30 min (documentada en la spec).

## 4 · CI (paridad con el rigor de T1)

- Run de referencia del cierre: **Quality Suite #26** (`34778950665`, `5044788`) = **Success**: backend ✅ 24m25s · frontend ✅ 1m1s. Artefactos descargados vía navegador autorizado y **sha256 recomputado == digest de GitHub**: backend `6f97466f…` (JUnit 1312/0/0/49; log `1263 passed, 49 skipped`) · frontend `b919ac69…` (JUnit 318/0). Detalle completo en `evidence/t2-ci-run.json`; XML en `evidence/backend-junit-post-t2.xml` y `evidence/vitest-junit-post-t2.xml`.
- Runs intermedios: #20/#22/#23 = Success; **#21/#24 = rojos por diseño** (commits RED con tests que deben fallar antes de C2); **#25 = rojo por pines del harness** que el commit de cierre `5044788` actualiza (cabezas Alembic, recuento de rutas, clasificador de datos) — clase ya remediada; #26 verde. Lección registrada en `/memories/repo/spec-dev-red-green-pitfalls.md`.

## 5 · Veredicto

**T2 = `CLOSED_FUNCTIONALLY_CERTIFIED`** — fundación de seguridad ejecutada y certificada por spec (RED→GREEN→sensibilidad→runtime), suites completas verdes, CI del cierre observado con artefactos verificados. KPI de procesos sin cambio (0/17): T2 es plataforma; los procesos se certifican en T4+. **T3 (alcance de datos) queda HABILITADA.**

# GA · PRE-SAP — ESTADO DEL PROGRAMA (TRANCHE 0 · cierre)

Fecha: 2026-09-13 · Baseline: `f270d0b` (+ commits de governance de T0) · Fase: **remediación no iniciada — programa listo para arrancar en T1**.

## 1 · KPI del programa

| KPI | Valor | Meta de cierre |
|---|---|---|
| Procesos certificados E2E | **0 / 17** | 17/17 |
| Brechas bloqueantes abiertas | **24** (9 P1 + 15 P2) + GA-GOV-03 | 0 |
| Otras brechas abiertas | 10 (7 P2 no bloqueantes + 3 P3, incl. R-214) | cerradas o aceptadas |
| Heredados que bloquean/condicionan | 36 filas (incl. 4 sin spec: Wave C P1 + condicionales por decisión) | resueltos por decisión/rider |
| Suites | **0 rojos** — backend 1226/0/0/49 (JUnit) · Playwright 129/0 · vitest 314/314 | mantenido en cada tranche |
| CI de tests | `Quality Suite (push)` publicado (PG efímero + vitest; artefactos JUnit/log). **AC-06 pendiente**: observación del run `66be1c1` externamente bloqueada en este entorno | verificación del propietario en GitHub (`GA_GOV_03_CI_EVIDENCE.md §4`) |
| Certificaciones con artefacto | informes históricos anotados `NOT_REPRODUCIBLE_EN_HEAD (pre-GA-GOV-03)`; plantilla de evidencia vigente | nuevas certificaciones con commit+artefacto (regla ya aplicada a T1) |
| UAT con evidencia primaria | 0 de 11 registros + 2 pendientes | 8 lotes finales completos |
| Decisiones del propietario pendientes (alcance actual) | 14 (+4 por tranche según roadmap) | registradas antes de su tranche |
| Tranches del programa | T0 **CERRADA** (`e828c3a`); **T1 = `PARTIAL / BLOCKED_EXTERNAL_CI_OBSERVATION`** (pendiente AC-06); T2-T13 + Pista OPS planificadas | todas cerradas |
| Veredicto pre-SAP | `NO_GO_SAP_FUNCTIONAL_GAPS` (sin cambios) | GO/NO-GO final en T13 |

## 2 · Estado por tranche

| Tranche | Estado | Nota |
|---|---|---|
| T0 · Cierre de auditoría + programa | **CERRADA** (`e828c3a`, 2026-09-13) | 15 documentos del programa + correcciones D-03 |
| T1 · GA-GOV-03 | **`PARTIAL / BLOCKED_EXTERNAL_CI_OBSERVATION`** (`66be1c1`/`e0458b7`, 2026-09-13) | 37/37; suites verdes; CI push publicado; **AC-06 pendiente de verificación del propietario** ⇒ `CERTIFICATION_PENDING_AC06` |
| T2-T13 + OPS | PLANIFICADAS | Orden y gates en el roadmap maestro |

## 3 · NEXT_IMPLEMENTATION_TRANCHE (§52) — siguiente tras T1

**GATE**: T2 solo es autorizable cuando **AC-06 = PASS** (observación del run de `66be1c1` en GitHub: enlace + jobs verdes + artefactos). La spec **no admite** cierre con `BLOCKED_EXTERNAL`. Verificación exacta para el propietario: `GA_GOV_03_CI_EVIDENCE.md §4`.

- **ID**: `T2` · **Nombre**: Fundación de seguridad y sesión (auth/roles/permisos).
- **Specs**: `R-199` · `R-200` · `R-202` · `R-208` (+ rider `GA-REM-003 AC04` — logout con revocación).
- **Findings**: R-199 (P1 — un rol de inquilino no puede fabricar autoridad global), R-200 (refresh aceptado como access), R-202 (reset de contraseña sin contexto), R-208 (permisos batch ≠ unitarios), P1-4/AC04 (no existe logout servidor; refresh robado vive 7 días).
- **Prioridad**: **P1 seguridad** — la fundación de seguridad se ejecuta primero (T2 del roadmap maestro).
- **Dependencias**: **T1 cerrada** ✔ (suites verdes). Decisión habilitante a registrar antes del merge de R-199: **`OD-13.c`** (¿puede existir `("*", all)` en roles de inquilino? propuesta del programa: NO).
- **Alcance**:
  1. R-199: validación de la forma de permisos en `create_role`/`update_role` (sin wildcard de inquilino).
  2. R-200: chequeo del `type` del token en la ruta de access (`decode_token`).
  3. GA-REM-003 AC04: `POST /logout` con denylist de `jti` + auditoría `LOGOUT` (mismo ciclo de tokens que R-200).
  4. R-202: reset de contraseña con contexto de empresa.
  5. R-208: dependencias de permiso de `batch-approve`/`batch-reject` alineadas con las rutas unitarias.
- **Fuera de alcance**: el resto de tranches (T3+); el fix de lectura de `/me` (R-213 → T11); decisiones de negocio.
- **Ficheros esperados**: `backend/app/auth/service.py`, `backend/app/auth/security.py`, `backend/app/auth/router.py`, `backend/app/review/router.py` (solo permisos), tests de seguridad nuevos por spec, evidencia en `audit/ga-pre-sap-program/evidence/`.
- **Tests**: ataques de cada spec bloqueados (RED→GREEN) + suites completas verdes con artefacto; regresión OD-14/OD-16 obligatoria.
- **Runtime**: deploy por el flujo vigente (EX-01); paridad bundle/marcadores al cierre de la tranche.
- **UAT del propietario**: lote **U1** de T13 (no bloquea el cierre técnico de T2).
- **Criterio de salida**: los 4 ataques bloqueados con test verde; suites verdes con artefacto; `OD-13.c` registrada; evidencia en el hogar del programa.

## 4 · Repositorio y siguiente paso

- Material del programa: `audit/ga-pre-sap-program/` (T0 + T1 + registros de ejecución autónoma) + correcciones D-03 en el paquete de auditoría; **producto diff acumulado = 0**.
- Tras el cierre de T1: **STOP** hasta `AC-06 = PASS`. Con la autorización autónoma vigente (prompt maestro del propietario, 2026-09-13), **T2 arranca automáticamente al cerrarse T1** (criterio de salida definido arriba).

## 5 · Ejecución autónoma (2026-09-13 06:08 +0200) — `PROGRAM_EXECUTION_BLOCKED_BY_OWNER_GATE`

- **Intento final de AC-06 por vías legítimas**: SIN VÍA — navegador integrado sin sesión de GitHub (404 + «Sign in»), `gh`/`glab` ausentes, sin tokens, API anónima 404; sin búsqueda de credenciales. AC-06 sigue `BLOCKED_EXTERNAL_CI_OBSERVATION`; T1 `PARTIAL`.
- **DAG consultado (9 documentos canónicos)**: T2-T13 dependen de T1 (o transitivamente; GA-GOV-03 es el gate de arranque) ⇒ **ninguna tranche independiente ejecutable**; T2 NO iniciada. **Pista OPS** (única línea independiente, «arrancable ya»): declarada **owner/ops** (acciones fuera del código) ⇒ encolada en `GA_OWNER_GATE_QUEUE.md` (bloquea solo T13).
- **OD-13.c verificada**: **ya resuelta** en la gobernanza vigente (`specs/remediation/OD-13-ROLE-AND-PERMISSION-TENANCY.md §3`, 2026-09-08) — sin decisión redundante del propietario.
- **Único gate inmediato**: `AC-06 (evidencia externa de CI)`.
- **Registros**: `GA_AUTONOMOUS_EXECUTION_LEDGER.md` (AE-01…AE-05; AE-05 = continuación 06:19-06:21 sin sesión disponible) · `GA_OWNER_GATE_QUEUE.md` (G-01…G-05 + programados §25). Commit docs-only sobre `a3b53a8`.
- Sin cambios de producto/tests/CI/migraciones; KPI `0/17` sin cambio; veredicto `NO_GO_SAP_FUNCTIONAL_GAPS` sin cambio.

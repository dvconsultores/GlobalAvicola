# GA-FE-01 · ATOMIC TASKS

Cada tarea: ID · finding · file · symbol · requirement · current failure · intended fix · test · expected result · dependency · status.

Estado de este documento: **plan pre-implementación** (COMMIT 1). El estado de ejecución se
actualiza con la evidencia del cierre (COMMIT 3). `⏳` pendiente.

| ID | Finding | File | Symbol | Requirement | Current failure | Intended fix | Test | Expected | Dep | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| **GA-FE-01-T01** | R-158 E1 | `frontend/src/pages/audit/AuditPage.tsx:3` | `User` (import) | `GA-REM-032 AC11` (retiro gobernado de pestañas) | TS6133 — declarado y no leído | eliminar `User` del import de `lucide-react` | `npx tsc -b --noEmit` + Vitest | tsc sigue avanzando (queda 1 error de AuditPage) | — | ⏳ |
| **GA-FE-01-T02** | R-158 E2 | `AuditPage.tsx:3` | `Database` (import) | ídem T01 | TS6133 | eliminar `Database` del import | ídem | AuditPage.tsx con **0 errores** | T01 | ⏳ |
| **GA-FE-01-T03** | R-158 E3–E4 | `frontend/src/pages/lots/LotFormPage.tsx:47` | `areas`, `setAreas` | sin AC para esta superficie (feature no gobernada; `R-182` registra el gap) | 2 × TS6133 — jamás leído / jamás llamado | eliminar la línea de estado muerta (no se añade petición ni control) | `npx tsc -b --noEmit` + Vitest | 2 errores menos; comportamiento idéntico | — | ⏳ |
| **GA-FE-01-T04** | R-158 E5–E6 | `LotFormPage.tsx:85` | `areaRes` (5.º de 4) | ídem T03 | TS2493 + TS6133 — el elemento no existe | destructuring a **4** elementos | ídem | **6 → 0 errores**; build desbloqueado | T03 | ⏳ |
| **GA-FE-01-T05** | R-158 | `frontend/` | — | AC-R158-01 | — | ejecutar `npx tsc -b --noEmit` sin caché | — | **exit 0 · 0 errores** | T01–T04 | ⏳ |
| **GA-FE-01-T06** | R-158 | `frontend/` | — | AC-R158-03 | — | `npx vite build` | — | exit 0 | T05 | ⏳ |
| **GA-FE-01-T07** | R-158 | `frontend/` | — | AC-R158-02 | — | `npm run build` (comando del Dockerfile) | — | exit 0 | T05 | ⏳ |
| **GA-FE-01-T08** | R-158 | `frontend/` | — | AC-R158-09/10 | — | Vitest completo + verificación de no relajaciones (diff tsconfig/package/Dockerfile vacío) | — | 0 failed · diff vacío | T07 | ⏳ |
| **GA-FE-01-T09** | R-158 | repo | — | §45 | — | COMMIT 2 (solo ediciones mínimas) tras todos los gates | — | worktree limpio; commit creado | T08 | ⏳ |
| **GA-FE-01-T10** | R-99 | repo→origin | — | AC-R99-02/03/04 | — | push normal a `main`; verificar `ls-remote` | — | remote == C2; origin intacto | T09 | ⏳ |
| **GA-FE-01-T11** | R-99 | runtime | — | AC-R99-05/06 | artefacto congelado 09-05 | observación acotada; fingerprint de egreso | sonda root+asset | asset ≠ `index-D5dwMXuP.js` · LM posterior | T10 | ⏳ |
| **GA-FE-01-T12** | R-99 | runtime | — | AC-R99-07 | marcadores M1–M7 = 0 | comprobar presencia en el bundle servido | grep marcadores | M1–M7 presentes | T11 | ⏳ |
| **GA-FE-01-T13** | R-99 | runtime | — | AC-R99-08/09 | — | smoke público (root/login/JS/CSS/API) + contexto fresco | navegador + curl | todo 200; sin error fatal | T11 | ⏳ |
| **GA-FE-01-T14** | R-99 | runtime | — | AC-R99-10 | — | buscar credenciales autorizadas; si no → `BLOCKED_AUTH` | — | `BLOCKED_AUTH` explícito | T13 | ⏳ |
| **GA-FE-01-T15** | cierre | `audit/` + backlog | — | §87–§90 | — | evidencia final + reconciliación + `R-182` + addenda R-99/R-158 | — | artefactos completos | T11–T14 | ⏳ |
| **GA-FE-01-T16** | cierre | repo | — | §96 | — | COMMIT 3 + push + verificación remota final | — | local == remoto; limpio | T15 | ⏳ |

## Notas

- **T03–T04** son la parte delicada: la resolución (retirar el scaffold muerto) está justificada en
  `GA_FE_01_CLARIFICATIONS.md C-02/C-03` — la feature de área-del-lote **no está gobernada para
  esta superficie** y completarla sería UX nueva; la intención se preserva vía el campo
  `area_id` del esquema + el finding `R-182` (que cubre además `planned_close_date`).
- **T08** incluye la comprobación explícita de no-relajación (`git diff 42108b0..HEAD -- frontend/tsconfig*.json frontend/package.json frontend/Dockerfile` → vacío).
- Ninguna tarea de R-98/R-119 · R-181 · fase 9 · Wave B/C · SAP · backend · migraciones.

# 21 — ÍNDICE DE EVIDENCIAS

Toda afirmación relevante de esta auditoría se apoya en una de las evidencias listadas aquí.
Estados: `STATIC_CONFIRMED` (confirmado leyendo el código) · `RUNTIME_CONFIRMED` (confirmado ejecutando) · `BLOCKED_EXTERNAL` · `NOT_VERIFIED`.

---

## 1. Comandos ejecutados durante la auditoría

Ninguno modificó el repositorio, el código ni la base de datos.

| # | Comando | Propósito | Resultado |
|---|---|---|---|
| 1 | `git log --reverse --format=... --date=...` | reconstrucción temporal | 171 commits, 2026-06-23 → 2026-07-08 |
| 2 | `git rev-list --count HEAD` | volumen | 171 |
| 3 | `git log --merges --oneline` | detectar PRs | **0 merges** |
| 4 | `git shortlog -sn --all` | autoría | Maria 157, dvconsultores 14 |
| 5 | `git branch -a` / `git tag` | ramas y versiones | 1 rama, **0 tags** |
| 6 | `git show --name-only 3c93440` | contenido del commit inicial | 227 archivos, 32 954 inserciones |
| 7 | `git show <commit>:specs/global-avicola/tasks.md \| grep -c "Phase 8"` | fechar la Fase 8 | aparece por primera vez en `37c8f0e` (2026-06-24 02:55) |
| 8 | `git show <commit>:specs/global-avicola/spec.md \| grep -c "Generational Traceability"` | fechar §4.9 | aparece en `ac125b2` (2026-06-24 18:38) |
| 9 | `git show <commit>:specs/global-avicola/spec.md \| grep -c "Feature Flags"` | fechar §14 | aparece en `b2c3f3c`, el mismo commit que la implementa |
| 10 | `git log --diff-filter=A -- <archivo>` | fecha de alta de artefactos | ver `18_GIT_FORENSICS.md §7` |
| 11 | `git log --all -- '*.env'` | fuga de secretos en el historial | **vacío** — sin fugas |
| 12 | `git log -i --grep="dark mode\|modo oscuro"` | campaña de modo oscuro | **24 commits** |
| 13 | `python -c "from app.main import app; app.openapi()"` | inventario de API | **168 operaciones** — `RUNTIME_CONFIRMED` |
| 14 | script AST sobre `alembic/versions/*.py` vs `Base.metadata` | deriva de esquema | **0 tablas, 0 columnas de deriva** — `RUNTIME_CONFIRMED` |
| 15 | `python -c "ScriptDirectory.get_heads()"` | integridad de migraciones | 1 head, 1 base, 21 revisiones — `RUNTIME_CONFIRMED` |
| 16 | script AST sobre `operations/service.py` | verificar el import ausente | `get_current_bird_balance` **no importado** — `RUNTIME_CONFIRMED` |
| 17 | `python -c "import app.integrations.sap.mock_adapter"` | verificar el módulo mock | `ModuleNotFoundError: app.integrations.sap.interface` — `RUNTIME_CONFIRMED` |
| 18 | `python -c "len(EventType)"` y `len(ALL_EVENT_TYPES)` | tipos de evento | **25** y **25** (el test espera 24) — `RUNTIME_CONFIRMED` |
| 19 | `python -m pytest --collect-only -q` | inventario de tests backend | **76 tests** — `RUNTIME_CONFIRMED` |
| 20 | `python -m compileall app seeds tests` | sintaxis del backend | exit 0 — `RUNTIME_CONFIRMED` |
| 21 | `tsc -b --noEmit` | typecheck del frontend | **exit 0** — `RUNTIME_CONFIRMED` |
| 22 | `eslint .` | lint del frontend | **5 errores, 431 avisos** — `RUNTIME_CONFIRMED` |
| 23 | `vitest run` | tests unitarios del frontend | **61/61 PASS**, 4 archivos — `RUNTIME_CONFIRMED` |
| 24 | script Node de comparación de `translation.json` | paridad i18n | **865 = 865 claves, 0 faltantes** — `RUNTIME_CONFIRMED` |
| 25 | `python -c "Base.metadata"` (índices, uniques, checks, FK) | integridad de BD | 47 tablas, 66 índices, 2 uniques, **0 checks**, 105 FK — `RUNTIME_CONFIRMED` |
| 26 | extracción y normalización de todas las llamadas `api.*` del frontend | matriz FE↔BE | 176 llamadas, 99 URLs distintas — `STATIC_CONFIRMED` |
| 27 | `grep -c '<SearchSelect'` y `grep -oE "case '…'"` en `OperationFormPage` | verificar la certificación | **34** y **25** — coincide con lo declarado |

### Comandos deliberadamente NO ejecutados

| Comando | Motivo |
|---|---|
| `pytest` (backend, 76 tests) | la única BD configurada es un PostgreSQL en la nube en IP pública que, por los indicios, sirve al entorno real; los tests **escriben** eventos, correcciones, aprobaciones y usuarios. Regla 2 del encargo: no alterar datos. Docker no está instalado, así que no fue posible levantar una BD desechable. → **BLOCKED_EXTERNAL** |
| `playwright test` | requiere el stack completo levantado y datos sembrados → **NOT_VERIFIED** |
| cualquier `git` de escritura, `docker`, `alembic upgrade`, `deploy` | prohibidos por el encargo |

---

## 2. Índice de evidencias por hallazgo

### Bloqueadores P0

| Hallazgo | Evidencia primaria | Corroboración |
|---|---|---|
| P0-1 mortalidad → 500 | `backend/app/operations/service.py:242` | `backend/app/operations/validators.py:21` (firma de 2 args); análisis AST: sin import |
| P0-2 corrección no aplicada | `backend/app/corrections/service.py:37-58` | ausencia de `setattr` sobre el evento |
| P0-3 sin RBAC | ausencia de `require_permission` en todo `backend/app/` | `backend/app/auth/security.py:107-118`; `backend/app/auth/models.py:46-69`; `seeds/dev_seeds.py:43-115` |
| P0-4 escalada por refresh | `backend/app/auth/service.py:72` | `frontend/src/stores/auth.store.ts:85-101`; `frontend/src/App.tsx:63-67,117-121` |
| P0-5 pantallas rotas (422) | `frontend/src/pages/lots/LotDetailPage.tsx:45` | `pages/review/ReviewDetail.tsx:32`; `pages/review/CorrectionForm.tsx:27`; `pages/users/UsersPage.tsx:21`; `pages/reports/ReportsPage.tsx:19`; `stores/company.store.ts:38`; `backend/app/*/router.py` (`le=100`) |
| P0-6 evidencias efímeras | `backend/app/operations/router.py:19,166` | `docker-compose.yml` (sin `volumes` en `backend`) |
| P0-7 SAP simulado en producción | `backend/app/integrations/sap/service.py:34-38` | `backend/app/integrations/sap/adapter.py:80-105`; `docker-compose.yml:28`; commit `bfccdfb`; `tasks.md` T-085 |
| P0-8 credenciales públicas | `GUIA_PRUEBAS_EN_VIVO.md:13-40` | `backend/seeds/dev_seeds.py:154`; `seeds/integration_seeds.py:174-203`; `backend/app/config.py:96`; `docker-compose.yml` |
| P0-9 contraseña no cambia | `backend/app/auth/schemas.py:42-49` | `backend/app/auth/service.py:130-142`; `frontend/src/pages/users/ProfilePage.tsx:24-26` |
| P0-10 BR-14 eludible | `backend/app/review/service.py:196-234` | `backend/app/review/service.py:301-309` (donde sí se valida) |
| P0-11 trazabilidad rota | `backend/app/operations/service.py:127-176` | `backend/app/operations/service.py:190-228` |
| P0-12 sin puerta de calidad | `.github/workflows/backend-ci.yml:8-12` | `.github/workflows/frontend-ci.yml:11-15`; `docker-push-*.yml:9-14`; `git log --merges` → 0; commit `9004f3a` |

### Spec Development

| Hallazgo | Evidencia |
|---|---|
| Constitución sin ratificar | `.specify/memory/constitution.md` (marcadores `[PRINCIPLE_1_NAME]`, `[GOVERNANCE_RULES]`) |
| Spec-first demostrado (Fase 8) | `37c8f0e` 02:55 → `d3f37f8` 03:25, `b3a0c56` 03:36, `2d06024` 03:51 |
| Code-before-spec (trazabilidad) | `2d06024` 03:51 → `ac125b2` 18:38 |
| Spec retro-documentada (flags) | `b2c3f3c` (código y spec en el mismo commit) |
| Dark mode contra la spec | `specs/global-avicola/spec.md:304`; 24 commits; `8940d9e` |
| Paleta sustituida | `frontend/tailwind.config.ts:12-24`; `frontend/src/index.css:1-3`; `specs/.../spec.md:299`; commit `a1d7843` |
| 12 features sin spec | búsqueda con 0 resultados en `spec.md` y `docs/` para `egg_reception_classification`, `hatchery_purpose`, `egg_storage`, alertas, evidencias, `SearchSelect`, Telegram, `Reversal` |
| Emojis prohibidos | `specs/.../spec.md:303`; `frontend/src/pages/operations/OperationFormPage.tsx:60-65`; `backend/app/dashboard/service.py:48-53` |
| Navegación divergente | `specs/.../spec.md` §6.1 (5 elementos) vs `frontend/src/components/layout/MobileNav.tsx:25-27` (3) |
| Referencias rotas | `specs/.../spec.md §14.5` y `tasks.md` Fase 9 → `docs/17-production-checklist.md` inexistente |

### Integración y contrato

| Hallazgo | Evidencia |
|---|---|
| `sap_document_ref` nunca enviado | búsqueda en `frontend/src`: 2 apariciones, ambas de lectura (`ReviewDetail.tsx:163`, `OperationDetailPage.tsx:145`) |
| `idempotency_key` nunca enviado | búsqueda en `frontend/src`: 0 apariciones fuera de un tipo de `sap.service.ts` |
| Comparativo SAP siempre vacío | `backend/app/reports/service.py:218-224` |
| Parámetros inexistentes | `MyPendingPage:33`; `ReviewCenter:86,91`; `AuditPage:44-48` vs `review/router.py:21-33` y `audit/router.py:15-30` |
| Maestros sin `PUT` | `backend/app/masters/router.py:88-107` vs `frontend/src/pages/masters/MasterListPage.tsx:79` |
| Capa de servicios/hooks muerta | búsqueda: ninguna página importa `*.service` ni `use*` (salvo `useTelegram`) |

### Base de datos

| Hallazgo | Evidencia |
|---|---|
| Sin deriva ORM↔migraciones | script AST comparando `Base.metadata` con `upgrade()` de las 21 migraciones |
| Cadena Alembic íntegra | `ScriptDirectory.get_heads()` → `['i9j0k1l2m3n4']`; `get_bases()` → `['0c661168cb12']` |
| `reversals` huérfana | `grep -rn "Reversal" backend/app --include=*.py` → solo su definición |
| `approval_steps` sin enforcement | `backend/app/review/service.py:412-470` (solo CRUD); `approve()` no la consulta |
| `egg_storage` solo escritura | 1 referencia, en `operations/service.py:94` |
| 9 migraciones sin spec | `12_DATABASE_MODEL.md §7` |

### Seguridad

| Hallazgo | Evidencia |
|---|---|
| Sin inyección SQL | 0 usos de `text(` o SQL concatenado en `backend/app/` |
| Sin XSS conocido | 0 usos de `dangerouslySetInnerHTML`, 0 `eval`/`new Function` en `frontend/src` |
| Sin secretos en Git | `git log --all -- '*.env'` vacío; `.gitignore:19,36`; `git ls-files \| grep .env` → solo `.env.example` |
| Validación de arranque | `backend/app/config.py:63-83` (aborta con `JWT_SECRET_KEY` vacío o `change_me`) |
| Cabeceras de seguridad | `backend/app/main.py:66-80` |
| Subidas seguras | `backend/app/operations/router.py:20-21,168-172` (lista blanca MIME, 10 MB, `uuid4` + `basename`) |

---

## 3. Documentos fuente consultados

**Specs (23):** `specs/global-avicola/{spec,plan,tasks,data-model,research,quickstart}.md`, `specs/global-avicola/contracts/api-contract.md`, `docs/00`…`docs/16` (falta `docs/14`).

**Gobierno:** `.specify/memory/constitution.md`, `.specify/init-options.json`, `.github/copilot-instructions.md`, `.github/prompts/speckit.*.md` (11), `.github/agents/speckit.*.md` (11).
**No existen `CLAUDE.md` ni `AGENTS.md`** en el repositorio.

**Informes de estado (nivel C, 20 archivos en la raíz):** `AUDITORIA_COMPLETA.md`, `AUDITORIA_FUNCIONAL_E2E.md`, `AUDITORIA_MULTICOMPANIA.md`, `AUDITORIA_MULTIDISCIPLINARIA_V2{,_RESULTADOS}.md`, `CERTIFICACION_FUNCIONAL.md`, `GLOBAL_AVICOLA_AUDIT_REPORT{,_v3}.md`, `GLOBAL_AVICOLA_UI_*.md`, `GUIA_PRUEBAS_EN_VIVO.md`, `IMPLEMENTATION_COMPLETE.md`, `INFORME_{PROGENITORAS,REPRODUCTORAS,INCUBADORA,BROILER}.md`, `NEXT_STEPS.md`, `REDESIGN_SUMMARY.md`, `SESSION_FINAL_REPORT.md`, `USER_GUIDE.md`, `VISUAL_GUIDE.md`, `WCAG_ACCESSIBILITY_REPORT.md`, `prompt-*.md` (4).

**Documentación de proceso de negocio no versionada como spec:** `Imagen de Procesos Documentado/` — 44 archivos (XLSX de formatos AVI-*, PDF de manuales Ross/Cobb, capturas del sistema legacy, `Sap y App Proceso Avícola Software primera version.pdf`). Es la **fuente funcional original del cliente** y no está trazada a ningún requerimiento del repositorio. Se registra como fuente disponible y no explotada formalmente.

**Configuración:** `docker-compose.yml`, `docker-compose.dev.yml`, `Makefile`, `.env.example`, `backend/{Dockerfile,pyproject.toml,alembic.ini,requirements.txt}`, `frontend/{Dockerfile,nginx.conf,package.json,vite.config.ts,vitest.config.ts,playwright.config.ts,tsconfig*.json,eslint.config.js,tailwind.config.ts}`, `.github/workflows/` (5).

---

## 4. Cobertura de la auditoría — control de calidad (§113)

| Control | Estado |
|---|---|
| ¿Revisados todos los `.md` relevantes? | ✔ 23 specs + 20 informes + 4 prompts + 2 README |
| ¿Reconstruidos los requerimientos? | ✔ 56 `GA-REQ-###` (no existían identificadores previos) |
| ¿Normalizados los duplicados? | ✔ ver `03_REQUIREMENTS_TRACEABILITY.md §4` |
| ¿Mapeado requirements → specs → código? | ✔ matriz maestra |
| ¿Mapeado código → spec (trazabilidad inversa)? | ✔ 30 features en la matriz forense |
| ¿Auditado el frontend? | ✔ 24 pantallas, 108 fuentes, 15 226 LOC |
| ¿Auditado el backend? | ✔ 11 módulos, 168 endpoints, 14 796 LOC |
| ¿Auditada la integración FE↔BE? | ✔ 176 llamadas verificadas una a una |
| ¿Auditada la base de datos? | ✔ 47 tablas, 21 migraciones, deriva verificada programáticamente |
| ¿Auditada la infraestructura y el deployment? | ✔ compose, Dockerfiles, Nginx, Watchtower, ambientes |
| ¿Auditado el CI/CD? | ✔ 5 workflows |
| ¿Auditada la seguridad y los permisos? | ✔ 22 hallazgos clasificados P0-P3 |
| ¿Auditado el testing? | ✔ 217 casos inventariados; 61 ejecutados |
| ¿Auditados mocks y hardcoding? | ✔ 0 mocks de datos; hardcoding localizado y listado |
| ¿Auditados TODO/FIXME? | ✔ **1 TODO** en todo el repositorio |
| ¿Auditado el código muerto? | ✔ ~1 800 LOC identificadas |
| ¿Auditados los procesos de negocio? | ✔ 15 procesos |
| ¿Identificados los procesos completos? | ✔ **0** — lista deliberadamente vacía |
| ¿Calculada la cobertura real? | ✔ 12/56 = 21,4 %, con numerador y denominador explícitos |
| ¿Auditado el cumplimiento de Spec Development? | ✔ 30 features, 5 tasas calculadas |
| ¿Revisados code-before-spec, out-of-spec y drift? | ✔ con marcas temporales de Git |
| ¿Revisadas las migraciones y refactores sin spec? | ✔ 9 y 5 respectivamente |
| ¿Revisado el cierre de specs? | ✔ `INFORMAL_CLOSE` |
| ¿Usado Git como evidencia forense? | ✔ sin ninguna operación de escritura |
| ¿Construido el baseline? | ✔ vigente + recomendación v1.1 |
| ¿Construido el roadmap? | ✔ 76 pasos en 9 fases |
| ¿Toda conclusión relevante tiene evidencia? | ✔ ruta y línea en cada hallazgo |

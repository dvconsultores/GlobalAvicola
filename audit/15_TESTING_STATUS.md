# 15 — ESTADO DEL TESTING

## 1. Inventario

| Suite | Ubicación | Archivos | Casos | Runner | ¿Configurada? | ¿En CI? |
|---|---|---|---|---|---|---|
| Backend integración/API | `backend/tests/` | 8 | **76** | pytest + pytest-asyncio + httpx ASGI | sí (`pyproject.toml`) | sí, pero **solo en `pull_request`** |
| Frontend unitarios | `frontend/src/**/__tests__/` | 4 | **61** | Vitest 4 + Testing Library + jsdom | sí (`vitest.config.ts`) | sí, solo en `pull_request` |
| Frontend E2E | `frontend/tests/` | 4 | ~50 | Playwright (6 proyectos de navegador) | sí (`frontend/playwright.config.ts`) | **NO** |
| E2E raíz | `tests/` | 4 (1 065 LOC) | ~30 | Playwright / script propio | **NO — sin `playwright.config` en la raíz** | **NO** |
| **Total** | | **20 archivos** | **~217 casos** | | | |

### Detalle backend

| Archivo | Casos | Qué prueba |
|---|---|---|
| `test_full_workflow_audit.py` | 23 | flujos F1–F10: creación de 6 tipos de evento, idempotencia, envío a revisión, corrección, aprobación, segregación BR-14, rechazo con motivo, timeline de auditoría, inmutabilidad, cancelación, duplicado de documento SAP, BR-01, dashboard, los 25 tipos de evento |
| `test_operations.py` | 12 | listado, tipos de evento, creación de eventos, reglas |
| `test_multi_company.py` | 5 | aislamiento por compañía |
| `test_auth.py` | 7 | login, refresh, /me |
| `test_masters.py` | 7 | CRUD de catálogos |
| `test_review.py` | 7 | flujo de revisión |
| `test_audit_reports.py` | 6 | auditoría y KPIs |
| `test_sap.py` | 9 | consolidación, exportación, jobs, payloads, errores |

### Detalle frontend

| Archivo | Casos | Qué prueba |
|---|---|---|
| `components/ui/__tests__/ui-components.test.tsx` | ~40 | Button, Input, Card, Badge, Modal, EmptyState |
| `components/ui/__tests__/signature-pad.test.tsx` | 8 | **componente que no se usa en ninguna pantalla** |
| `stores/__tests__/auth.store.test.ts` | ~9 | store de autenticación |
| `hooks/__tests__/useMediaQuery.test.ts` | 4 | **hook que no se usa en ninguna pantalla** |

## 2. Ejecución realizada en esta auditoría

### 2.1 Frontend — EJECUTADO

```
$ ./node_modules/.bin/vitest run
 Test Files  4 passed (4)
      Tests  61 passed (61)
   Duration  2,66 s
```
**RUNTIME_CONFIRMED: 61/61 PASS.**

```
$ ./node_modules/.bin/tsc -b --noEmit      → exit 0   (RUNTIME_CONFIRMED)
$ ./node_modules/.bin/eslint .             → exit 1
   ✖ 436 problemas (5 errores, 431 avisos)
```

### 2.2 Backend — NO EJECUTADO (decisión de auditoría)

```
$ python -m pytest --collect-only -q      →  76 tests collected
$ python -m compileall app seeds tests    →  exit 0
```

**Los 76 tests NO se ejecutaron.** Motivo: la única base de datos configurada (`backend/.env` → `DATABASE_URL`) es un **PostgreSQL en la nube en IP pública**, que por los indicios (mismo host que `avicola.globaldv.net`, seeds de "pruebas en vivo") sirve al entorno real. Los tests **escriben datos**: crean eventos operativos, correcciones, aprobaciones y usuarios. La regla 2 del encargo ("no alterar datos") lo prohíbe. Docker no está instalado en la máquina auditada, por lo que no fue posible levantar una base de datos desechable.

Estado: **`BLOCKED_EXTERNAL` — 76 casos.**

### 2.3 E2E — NO EJECUTADO

Requiere el stack completo levantado (`baseURL: http://localhost:5173` con `webServer: npm run dev` y un backend con datos sembrados). Estado: **NOT_VERIFIED — ~80 casos.**

## 3. Resultado consolidado

```
Tests encontrados ................ 217
Tests ejecutados ................. 61
PASS ............................. 61
FAIL ............................. 0   (de los ejecutados)
FAIL confirmado estáticamente .... 1   (ver §4)
SKIPPED .......................... 0
BLOCKED_EXTERNAL ................. 76  (backend: requiere BD desechable)
NO EJECUTADOS .................... 80  (E2E Playwright)
```

## 4. Defectos confirmados en las propias pruebas

**T-01 · Test que fallaría hoy.**
`backend/tests/test_operations.py:19`:
```python
assert len(data) == 24  # 24 event types documented
```
`GET /operations/event-types` devuelve `ALL_EVENT_TYPES`, que tiene **25 elementos** (verificado en runtime). El enum `EventType` también tiene 25. El test se escribió cuando había 24 y nunca se actualizó al añadir `egg_reception_classification` (`076ca5e`, 2026-06-29). **Nadie lo detectó porque el CI nunca se ejecuta.**

**T-02 · La suite de backend no puede pasar en CI tal como está.**
`backend-ci.yml` levanta un PostgreSQL 15 vacío y ejecuta `pytest` directamente. **No hay paso `alembic upgrade head` ni siembra de datos.** La fixture `auth_headers` hace `POST /login` con `admin/admin123` y `assert resp.status_code == 200`. Contra una base vacía: sin tablas → error; con tablas pero sin usuarios → 401. **Todos los tests que dependen de `auth_headers` (la práctica totalidad) fallarían.** Además, muchos tests dependen de datos preexistentes: `test_operations.py` usa `"lot_id": 2` codificado.

**T-03 · Los tests E2E de la raíz son código muerto.**
`tests/` contiene 1 065 LOC de specs de Playwright (`e2e.spec.ts`, `integration-full.spec.ts`, `operations.spec.ts`) y un script propio (`integration-test.ts`). **No existe `playwright.config.ts` en la raíz**; el único config está en `frontend/` y apunta a `./tests` **relativo a `frontend/`**. El `package.json` de la raíz no define scripts. Esas suites **nunca se han podido ejecutar** con la configuración del repositorio.

**T-04 · El job de lint del CI fallaría.**
`npm run lint` es `eslint .` sin `--max-warnings`; hoy devuelve 5 errores → exit 1.

**T-05 · Artefacto de resultados obsoleto.**
`frontend/test-results/.last-run.json` (`{"status":"passed","failedTests":[]}`) tiene fecha del **2026-06-25**, tres días antes del cambio completo de paleta y de la refactorización de navegación. No es evidencia del estado actual.

## 5. Cobertura

| Métrica | Objetivo (spec §7) | Real |
|---|---|---|
| Cobertura backend | > 80 % | **NO MEDIBLE** — `pytest-cov` está en las dependencias dev pero no se ejecuta; los tests no corren |
| Cobertura frontend | > 70 % | **~4 %** estimado: 4 archivos de test para 108 fuentes; ninguno cubre páginas, servicios, formularios ni lógica de negocio |
| Trazabilidad AC → test | 100 % | **6,7 %** (ver `05_SPEC_DEVELOPMENT_COMPLIANCE.md`) |

**Ninguno de los defectos P0 de esta auditoría está cubierto por un test:**
`mortality_recording` (BE-01), la no aplicación de correcciones (BE-02), la ausencia de RBAC (BE-03), la degradación del token en refresh (BE-04), los límites de paginación (FE-02), el cambio de contraseña inoperante (S-07) o la trazabilidad auto-referencial (BE-11l).

`test_full_workflow_audit.py::test_f8c_business_rule_mortality_exceeds_balance` **sí** cubre BR-01 y habría detectado BE-01 — si alguna vez se hubiera ejecutado.

## 6. Tipos de prueba: cobertura por categoría

| Tipo | Estado |
|---|---|
| Unit (backend) | **ausente** — todos los tests de `backend/tests/` son de integración vía HTTP |
| Unit (frontend) | presente, mínimo (4 archivos) |
| Integración / API | presente (76 casos) — **no ejecutable** |
| Componente | presente (UI primitives) |
| E2E | presente (~80 casos) — **no ejecutado nunca** |
| Contract testing | **ausente** — es exactamente lo que habría evitado los 13 desajustes FE↔BE |
| Smoke | `frontend/tests/smoke.spec.ts` — no ejecutado |
| Cross-browser | `frontend/tests/cross-browser.spec.ts` + 6 proyectos Playwright — no ejecutado |
| Seguridad | **ausente**; `pip-audit`/`npm audit` con `|| true` y solo en PR |
| Carga / rendimiento | **ausente** |
| Accesibilidad | **ausente** (`WCAG_ACCESSIBILITY_REPORT.md` es una revisión manual, sin herramienta ni CI) |

## 7. Conclusión

El proyecto **tiene** una cantidad razonable de pruebas escritas (217 casos, incluida una suite de flujo completo bien estructurada y nombrada por criterio de aceptación). El problema no es la ausencia de tests: es que **nunca se ejecutan**.

- CI configurado exclusivamente para `pull_request` + **0 pull requests en 171 commits** ⇒ ninguna prueba del repositorio se ha ejecutado nunca de forma automática.
- El pipeline de despliegue (`push` → imagen → Watchtower) **no depende del pipeline de pruebas**.
- Los tests que sí podrían ejecutarse localmente (los 61 de Vitest) pasan, pero cubren únicamente componentes de presentación, dos de ellos **muertos**.

Este es, junto con la ausencia de RBAC, el hallazgo estructural más importante de la auditoría: **no existe ninguna puerta de calidad entre un commit y la producción.**

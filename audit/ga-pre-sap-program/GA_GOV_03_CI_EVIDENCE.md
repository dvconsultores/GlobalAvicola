# GA-GOV-03 · EVIDENCIA DE CI (T1 · cierre)

## 1 · Workflow implementado

| Ítem | Valor |
|---|---|
| Fichero | `.github/workflows/quality-suite.yml` (nuevo) |
| Nombre | `Quality Suite (push)` |
| Triggers | `push` a `main` + `workflow_dispatch` |
| Job `backend-suite` | `pip install -e ".[dev]"` + `pip install pgserver` → `backend/scripts/run_tests.sh -q --junitxml=reports/backend-junit.xml` → artefacto `backend-suite-<sha>` (log + JUnit) |
| Job `frontend-suite` | `npm install --legacy-peer-deps` → `npx vitest run --reporter=default --reporter=junit --outputFile=vitest-junit.xml` → artefacto `frontend-suite-<sha>` (log + JUnit) |
| PostgreSQL | **efímero, de usuario, sin privilegios** (`pgserver` en el runner; sin credenciales compartidas ni BD de entorno) |
| Dependencia del deploy | **NINGUNA** — sin `needs:` desde/ hacia los `docker-push*`; workflow independiente (EX-01 intacto) |
| Secretos | Ninguno: JWT de test efímero generado por `run_tests.sh`; el artefacto no incluye credenciales |

## 2 · Equivalencia local (§37) — ejecutada antes del push

| Paso CI | Comando local equivalente | Resultado |
|---|---|---|
| backend `run_tests.sh` + JUnit | `bash backend/scripts/run_tests.sh -q --junitxml=reports/backend-junit.xml` | **1226 passed · 0 failed · 0 errors · 49 skipped** (20:18) — JUnit `tests=1275 failures=0 errors=0` |
| vitest + JUnit | `npx vitest run --reporter=junit --outputFile=vitest-junit.xml` | **314/314** (44 ficheros) |
| tsc / build / i18n | `tsc -b --noEmit` · `npm run build` · script de paridad | 0 · OK (`index-DDCcWL76.js`) · ES=1041/EN=1041 |

## 3 · Push ejecutado

| Ítem | Valor |
|---|---|
| Commit de implementación | `66be1c15d8c299e2746faf6b5f90fec77b9bc758` |
| Comando | `git push origin main` → `e828c3a..66be1c1 main -> main` |
| `git ls-remote origin main` | `66be1c1…` ✔ (local == remoto tras el push) |
| Consecuencia | El workflow `Quality Suite (push)` queda **disparado por construcción** (trigger `push` a `main`), junto con los workflows existentes de calidad y el docker-push de backend |

## 4 · Observación del run

- **Estado: `BLOCKED_EXTERNAL_CI_OBSERVATION`.**
- Motivo verificado en el entorno de ejecución: `gh` no está disponible; no hay `GITHUB_TOKEN` en el entorno; la API anónima responde **404** (repositorio privado) — `GET https://api.github.com/repos/dvconsultores/GlobalAvicola/actions/runs` = 404 (2026-09-13T05:40+02:00).
- **No se fabrica ningún resultado de GitHub.** Verificación para el propietario: pestaña Actions del repositorio → run «Quality Suite (push)» sobre `66be1c1` → jobs `backend-suite`/`frontend-suite` → artefactos `backend-suite-66be1c1…` / `frontend-suite-66be1c1…`.
- Mitigación de evidencia: la **misma lógica** de ambos jobs se ejecutó localmente con resultado verde y artefactos versionados (§2); el JUnit del backend y el de vitest quedan preservados en `evidence/`.

## 5 · Independencia del despliegue (prueba)

| Ítem | Resultado |
|---|---|
| `docker-push-backend.yml` / `docker-push-frontend.yml` / `docker-build-push.yml` | **sin cambios** (`git diff e828c3a..66be1c1 -- .github/workflows` muestra solo la creación de `quality-suite.yml`) |
| Watchtower / Nginx / `docker-compose*.yml` | **sin cambios** |
| `needs:` entre suite y deploy | **ninguno** (workflows independientes; EX-01 preservado) |
| scope-guard de `quality-gates.yml` | sigue verificando en cada push que EX-01 no se modifica |

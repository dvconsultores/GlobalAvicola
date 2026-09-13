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

- **Estado: `BLOCKED_EXTERNAL_CI_OBSERVATION`** (reconfirmado en la micro-tranche de cierre externo AC-06, 2026-09-13).
- Motivos verificados en el entorno de ejecución: `gh` no está disponible; sin `GITHUB_TOKEN`/`GH_TOKEN`; API anónima 404 (repo privado); **nuevo intento legítimo vía navegador** — `https://github.com/dvconsultores/GlobalAvicola/actions?query=branch%3Amain` → «Page not found» + enlace «Sign in» (sesión del navegador **no autenticada**). Sin acceso autorizado ⇒ sin observación; **no se fabrica resultado**.
- **Contrato AC-06 (spec, literal):** «run del workflow sobre el commit de cierre con ambas suites verdes (**enlace de run + artefacto**)»; la AC matrix exige «enlace al run + descarga de artefacto» y artefacto `evidence/ci-run.json`. **La spec NO contempla excepción** por bloqueo externo ⇒ mantener `CLOSED` era contradictorio: la certificación queda **`CERTIFICATION_PENDING_AC06`** hasta la observación real.
- **Verificación manual del propietario (exacta; sin re-ejecutar pruebas funcionales):**
  1. Abrir GitHub → pestaña **Actions** del repositorio `dvconsultores/GlobalAvicola`.
  2. Localizar «**Quality Suite (push)**» — run del push con SHA **`66be1c1`** (secundario: `e0458b7`).
  3. Confirmar conclusión **verde** y jobs `backend-suite` (pytest sobre PostgreSQL efímero vía pgserver) y `frontend-suite` (vitest).
  4. Confirmar artefactos `backend-suite-66be1c1…` y `frontend-suite-66be1c1…` (JUnit + log saneado).
  5. Registrar el enlace del run (evidencia `ci-run.json`): **con ello AC-06 = PASS y T1 cierra incondicionalmente**.
- Mitigación de evidencia mientras tanto: la **misma lógica** de ambos jobs se ejecutó localmente con resultado verde y artefactos versionados (§2); el JUnit del backend y el de vitest quedan preservados en `evidence/`.

## 5 · Independencia del despliegue (prueba)

| Ítem | Resultado |
|---|---|
| `docker-push-backend.yml` / `docker-push-frontend.yml` / `docker-build-push.yml` | **sin cambios** (`git diff e828c3a..66be1c1 -- .github/workflows` muestra solo la creación de `quality-suite.yml`) |
| Watchtower / Nginx / `docker-compose*.yml` | **sin cambios** |
| `needs:` entre suite y deploy | **ninguno** (workflows independientes; EX-01 preservado) |
| scope-guard de `quality-gates.yml` | sigue verificando en cada push que EX-01 no se modifica |

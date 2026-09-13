# PLANTILLA DE EVIDENCIA DE CERTIFICACIÓN — REGLA «NO GREEN POR DECLARACIÓN»

Publicada por `GA-GOV-03` (T1 · 2026-09-13). **Toda certificación (tranche, spec, proceso) debe citar los siguientes campos con valores reales; ningún campo PASS puede quedar vacío ni derivarse de una declaración sin artefacto.** Esta plantilla es un requisito del programa pre-SAP (`audit/ga-pre-sap-program/`).

## 1 · Campos obligatorios

| Campo | Contenido exigido |
|---|---|
| Commit | SHA exacto certificado (y rama) |
| Fecha/hora | Inicio y fin de la corrida (ISO-8601 con zona) |
| Entorno | SO, versiones (Python/Node/PG), método de PostgreSQL (efímero/aislado) |
| Alembic head | Cabeza única verificada (`ScriptDirectory.get_heads()`), sincronía código↔BD |
| Resultado de casos | Conteos: collected / passed / failed / errors / skipped (+ duración) |
| Suites | Comando canónico exacto por suite (backend, Playwright, vitest, tsc, build, i18n) |
| Logs | Rutas versionadas del log crudo por suite (sin secretos) |
| Artefactos | JUnit XML + logs del run de CI (nombre + run + SHA) |
| CI | Workflow, run ID/enlace, trigger, jobs, estado — o `BLOCKED_EXTERNAL` documentado |
| Diff de producto | `git diff` de `backend/app/**`, `frontend/src/**` (producto), `backend/alembic/versions/**` = 0 |
| Política de deploy | `docker-push*` / Watchtower / Nginx / compose sin cambios (EX-01) |
| Residuales | Fallos o desviaciones clasificados (TEST_DEFECT / APP_DEFECT / ENVIRONMENT / EXTERNAL) |
| Veredicto | Estado final con la terminología canónica del repositorio |

## 2 · Checklist de cierre

- [ ] 37/37 (o N/N) casos con disposición final individual (no agrupada).
- [ ] Cero redefiniciones ocultas: cada cambio de expectativa cita spec/decisión/migración vigente.
- [ ] Suite objetivo verde **reproducida** con el comando canónico (no un subconjunto «conocido verde»).
- [ ] Suite completa: 0 fallos inexplicados; los residuales están clasificados y con dueño.
- [ ] Guardas de diff: producto = 0, migraciones = 0, política de deploy = 0.
- [ ] Limpieza de secretos en logs/artefactos (sin `.env`, tokens, cookies, credenciales).
- [ ] La plantilla se aplica a sí misma: la certificación cita commit + comandos + logs + run.

## 3 · Ejemplo mínimo (referencia: GA-GOV-03)

```
SPEC/TRANCHE: GA-GOV-03 / T1
COMMIT: e828c3a (entrada) → <SHA de implementación> (cierre)
SUITES: backend/scripts/run_tests.sh → 0 failed (log evidence/…); Playwright → 0 failed;
        vitest → 0 failed; tsc/build → OK; alembic → 1 head canónica
CI: Quality Suite (push) · run <ID> · SHA <SHA> · artefactos backend-suite-<SHA> / frontend-suite-<SHA>
DIFF: producto 0 · migraciones 0 · deploy 0
VEREDICTO: CLOSED_FUNCTIONALLY_CERTIFIED
```

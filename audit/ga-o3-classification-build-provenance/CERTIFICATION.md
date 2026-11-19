# CERTIFICACIÓN LOCAL — GA-O3-INSPECTION-CLASSIFICATION-AND-BUILD-PROVENANCE

Spec: `specs/016-o3-classification-build-provenance/spec.md` · Baseline `main` = `7a9887b` · IMPL = `92d8db0`.
Sin migración (head `g2b3c4d5e6f7`). Rutas `/api/` 241 → 243 (+`classification-candidates`, +`version`).

## 1. Alcance y reparto de trabajo

- Claude: discovery, spec, diseño, auditoría de diffs, ejecución de suites y certificación. Además editó **a mano los 4
  workflows** `.github/workflows/docker-push-*.yml` (solo `build-args` + guardia + fecha): la guarda del ejecutor veda
  `.github/workflows` y el mandato pedía expresamente el cambio de CI (§19, §22, §25). Cambio mecánico, verificado con
  `yaml.safe_load` y con el test de contrato `spec016.buildProvenance.test.ts`.
- DeepSeek (`deepseek-executor`): todo el código de aplicación y todos los tests nuevos (ver §8).

## 2. Contrato O-3 (cerrado)

| Punto | Resultado |
|---|---|
| Derivación automática | Intacta (granja de una sola cadena ⇒ BU derivada, nunca pendiente). Cubierto por O3-E2E-01. |
| Pendiente | Sin lote y cadena no derivable ⇒ bandeja `GET /operations/pending-classification`. |
| Clasificación manual | `POST /operations/{id}/classify` con `business_unit_code` (o `company_business_unit_id`, exactamente uno) + `reason`. |
| Motivo | Obligatorio; `strip()`; 3..500 caracteres; `""`, `"  "`, `null`, `"ab"` ⇒ 422. Va a `change_reason` de P-09. |
| Candidatos | `GET /operations/{id}/classification-candidates` (`masters:update`): `{code,name_key}` de unidades habilitadas y activas **de la empresa del evento**; sin ids; 404 si el registro no es un pendiente visible. |
| Autoridad | Misma que `classify` (`masters:update`); el creador sin ese permiso recibe 403 en ambas. |
| Alcance del actor | Decisión D-A4: clasificar es configuración (plano `CONTROL`); candidato = toda unidad habilitada de la empresa, no solo las concedidas al actor (AC-F04). **No concede acceso a nadie** (probado: `/me` y unidades efectivas idénticas antes/después). |
| Doble clasificación | 404 determinista («Registro pendiente no encontrado»); la BU no cambia; exactamente una fila de auditoría. |
| Reclasificación | Fuera de alcance (existe `reclassify`, `corrections:correct`, sin tocar). |

Observabilidad: el detalle del evento **no expone** la cadena clasificada (contrato previo, no tocado). La clasificación se
demuestra por tres observables independientes: sale de la bandeja, entra en el Historial (API y UI) y la auditoría registra
`updated` con `previous_state='pending'`, `new_state=<código>`, `change_reason=<motivo>`, actor y empresa.

## 3. Procedencia del build (implementada)

| Pieza | Detalle |
|---|---|
| Backend | `GA_GIT_SHA`/`GA_BUILD_TIME` (settings, default `unknown`); `GET /api/v1/version` pública, solo `{git_sha,build_time,environment}`; sin `subprocess` ni `git`. |
| Frontend | `dist/version.json` + `__GA_BUILD_SHA__` + atributo `data-build-sha` no visible; nginx `location = /version.json` con `Cache-Control: no-store`. |
| Imágenes | `ARG GIT_SHA/BUILD_TIME` + `LABEL org.opencontainers.image.revision/created` en ambos Dockerfile (tras los `COPY`). |
| CI | Los 4 workflows pasan `build-args` (`GIT_SHA=${{ github.sha }}`, `BUILD_TIME` UTC) y una guardia que falla sin `github.sha`. |
| Guardia | `scripts/verify_runtime_sha.sh <url> <sha>`: PASS exacto / PASS tree-equal por carpeta / FAIL; `unknown` ⇒ exit 2. |

Pin consciente: el cupo de rutas anónimas en `tests/test_rbac.py::test_ac08b` pasa de ≤2 a ≤3 (la tercera es `/api/v1/version`,
metadata no sensible, coherente con `/health` público).

## 4. Regresión (HEAD = IMPL `92d8db0`, árbol idéntico)

| Gate | Resultado | Evidencia |
|---|---|---|
| Backend completo | **1906 passed, 0 failed, 52 skipped** (antes 1888) | `evidence/10_backend_full.log` |
| Frontend completo | **725 passed** (123 archivos) | `evidence/11_frontend_full.log` |
| TSC | PASS | `evidence/12_tsc.log` |
| Build | PASS; `version.json` con el SHA inyectado | `evidence/13_build.log` |
| E2E completa en serie (`--workers=1`) | **207 passed, 0 failed, 0 skipped** (P18A–D, P19A–C y 8 nuevas de O-3 incluidas) | `evidence/14_e2e_full.log` |
| O3-E2E-01..08 | 8/8 PASS (también en solitario) | `evidence/e2e_spec016/` |

Corridas E2E anteriores, conservadas por honestidad: `14a` (fallo de `spec008` por O-11), `14b` (fallo de mi spec en el
filtro de granja del Historial por O-11), `14c` (interrumpida al reiniciarse la sesión), `14d` (detenida por pausa).

## 5. Sensibilidad / mutación (tras el commit de implementación, restauración desde SHA explícito)

Cada mutante se aplicó de uno en uno, se restauró con `git restore --source=92d8db0 -- <archivo>` y se comprobó `git diff`
vacío. **19/19 detectados, 0 supervivientes.**

| # | Mutación | Detectada por |
|---|---|---|
| B1 | motivo sin longitud mínima | `test_ac_o3_02_el_motivo_es_obligatorio` |
| B2 | sin «exactamente una unidad» | `test_ac_o3_03_ni_dos_unidades_ni_ninguna` |
| B3 | resolver código sin filtro de empresa | `test_ac_o3_04/01/06/07/08/09_3` (500 `MultipleResultsFound`) |
| B4 | resolver código sin `is_enabled` | `test_ac_o3_04` |
| B5 | candidatos sin filtro de empresa | `test_ac_o3_09_1` |
| B6 | candidatos sin `is_enabled` | `test_ac_o3_09_1` |
| B7 | sin `change_reason` en auditoría | `test_ac_o3_07_el_rastro_lleva_el_motivo_y_el_actor` |
| B8 | candidatos con `operations:read` | `test_ac_o3_09_2_candidatos_permiso_y_tenencia` |
| B9 | `/version` con SHA fijo `unknown` | `test_vp_01_la_respuesta_es_lo_inyectado_en_el_build` |
| B10 | sin guarda de «código no resuelve» | `test_ac_o3_04` (mensaje único anti-oráculo) |
| F1 | motivo sin mínimo en la UI | `o3.classifyDialog` «Clasificar» deshabilitado… |
| F2 | botón sin permiso | `o3.classifyDialog` «sin masters:update no hay acción» |
| F3 | opción sin código | `o3.classifyDialog` «código — descripción» |
| F4 | clave del POST distinta | `o3.classifyDialog` «cuerpo EXACTO» |
| F5 | sin recarga tras éxito | `o3.classifyDialog` «recarga la lista» |
| S1 | `unknown` no falla (exit 0) | `spec016.buildProvenance` AC-VP-07 |
| S2 | `tree_equal` siempre cierto | `spec016.buildProvenance` AC-VP-07 |
| V1 | `version.json` con `unknown` | `spec016.buildProvenance` AC-VP-03 |
| V2 | nginx sin `no-store` | `spec016.buildProvenance` AC-VP-05 |
| V3 | workflow sin `GIT_SHA` (ejecutado por Claude) | `spec016.buildProvenance` AC-VP-05 |

Regresión posterior a la mutación (árbol == `92d8db0`): backend dirigido **125 passed** (`evidence/20_backend_postmutation.log`),
frontend **724 passed + 1 skipped** (`evidence/21_frontend_postmutation.log`; el caso `tree-equal` del script se omite porque
HEAD toca `frontend/`, es lo previsto).

## 6. Observaciones

- **O-10 (ajena, preexistente, SIN TOCAR):** owner Andres, commit `7610ece`, rama `develop`; `test_first_superuser_bootstrap::test_t_043_02` falla en `develop`.
- **O-11 (nueva, P3, preexistente):** los filtros de granja de `/lots` y `/operations` cargan `GET /masters/farms?limit=100`
  (tope del backend). Con más de 100 granjas las posteriores no son seleccionables desde la UI. La BD de E2E se reinicia por
  corrida pero acumula granjas dentro de ella; por eso `spec008` falló al añadirse mis pruebas. Mitigación solo de pruebas:
  spec renombrado `proceso-spec016-…` (corre después de `spec008`) y el Historial se abre con el filtro persistido en
  `sessionStorage`. Fuera de alcance corregir el producto (selector buscable): requiere decisión de UX.
- **Desajuste de tags (a verificar en el despliegue):** los workflows `-dev` publican el tag `dev` mientras
  `docker-compose.develop.yml` consume `:develop`; además las imágenes solo se reconstruyen si el push toca `backend/**` o `frontend/**`.

## 7. Despliegue y paridad

Se completa en `POSTDEPLOY.md` tras el push y la verificación del runtime con `scripts/verify_runtime_sha.sh`.

## 8. Delegación a DeepSeek (qué escribió)

Backend: `classification.py` (`habilitacion_por_codigo`, `candidatos_de_clasificacion`, `motivo`), `operations/{schemas,router}.py`,
`route_scope.py`, `version.py`, `config.py`, `main.py`, `authorization_coverage.py`, `Dockerfile`; tests `test_o3_classification.py`,
`test_build_provenance.py` y ajustes en `test_pending_classification.py`, `test_population_invariant.py`, `test_rbac.py`.
Frontend: `PendingClassificationPage.tsx`, `operations.service.ts`, locales es/en, `vite.config.ts`, `vitest.config.ts`,
`vite-env.d.ts`, `main.tsx`, `Dockerfile`, `nginx.conf`; tests `o3.classifyDialog.test.tsx`, `spec016.buildProvenance.test.ts`.
Otros: `scripts/verify_runtime_sha.sh`, `e2e/proceso-spec016-o3-clasificacion-de-pendientes.spec.ts`, campañas de mutación.

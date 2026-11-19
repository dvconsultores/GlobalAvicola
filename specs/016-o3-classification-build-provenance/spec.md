# SPEC 016 — O-3 clasificación de inspecciones pendientes + procedencia exacta del build

Mandato: `GA-O3-INSPECTION-CLASSIFICATION-AND-BUILD-PROVENANCE` (2026-11-18). Continúa SPEC 015
(`O-3`, `Deployment Parity = PARTIAL`). Baseline `main` = `7a9887b`. Sin migración (head
`g2b3c4d5e6f7`). Fuera de alcance: O-1, O-2, O-4, O-5, O-6, O-9, O-10 (Andres, `7610ece`, `develop`).

## A. O-3 — Clasificar desde la UI

### Contrato existente (discovery)

- `GET /operations/pending-classification` — bandeja (`predicado_de_pendientes`): el autor ve las suyas,
  quien tiene `masters:update` ve las de su empresa. Alcance `CONTROL`.
- `POST /operations/{id}/classify` — `masters:update`; hoy recibe `company_business_unit_id` (id de fila de
  `CompanyBusinessUnit`), **sin motivo**. Ninguna API expone ese id (`HabilitacionRead` no lo publica a
  propósito) → el flujo es inalcanzable desde un cliente = `FUNCTIONAL GAP`.
- `clasificar()` (`business_units/classification.py`): valida misma empresa, habilitación activa, que no sea
  derivable; fija `business_unit_id`, `classified_at`, `classified_by_id`; audita `UPDATED` con
  `previous_state='pending'`, `new_state=<código>`; **no concede acceso a nadie** (AC-F04).
- Re-clasificar un registro ya clasificado: `POST /operations/{id}/reclassify` (`corrections:correct`,
  ya existente, fuera de este ciclo).

### Decisiones de diseño

- **D-A1 Direccionamiento por código.** `classify` acepta `business_unit_code` (código del catálogo,
  p. ej. `breeder`) y lo resuelve **dentro de la empresa del registro** (misma doctrina de
  `business_units/router.py`: «la unidad se direcciona por código»). `company_business_unit_id` se
  conserva como alternativa compatible; se exige **exactamente uno** de los dos.
- **D-A2 Motivo obligatorio.** `reason: str` requerido, `strip()`, no vacío ni solo espacios, longitud
  mínima 3 y máxima 500 (≈ convención de `ReclassificationRequest` + límite del campo de auditoría).
  Se registra en la auditoría como `change_reason`.
- **D-A3 Candidatos.** Nueva lectura mínima `GET /operations/{event_id}/classification-candidates`
  (ninguna API existente sirve: `GET /business-units` exige `business_units:read`, que el clasificador
  `masters:update` no tiene por contrato, y no está acotada al registro). Misma autoridad que `classify`
  (`masters:update`) y mismo filtro de pendientes (`predicado_de_pendientes`) → registro inexistente,
  ajeno de empresa o ya clasificado = `404`. Devuelve `[{code, name_key}]` de las unidades **habilitadas
  y activas de la empresa del registro**. Nunca ids internos.
- **D-A4 Alcance del actor.** Clasificar es acto de **configuración** (plano `CONTROL`): el candidato es
  toda unidad habilitada de la empresa, no solo las concedidas al actor (AC-F04: administrar no es acceder).
  La clasificación **no modifica** concesiones del actor ni de nadie (ya probado; se re-prueba).
- **D-A5 Estado tras clasificar.** `pending → manual` (estado derivado, sin columna nueva). Sale de la
  bandeja; entra al historial de la cadena asignada; conserva granja y galpón.
- **D-A6 Doble clasificación.** Segunda llamada = `404` determinista («Registro pendiente no encontrado»),
  la BU no cambia, no hay auditoría adicional.
- **D-A7 Derivación automática intacta.** Granja de una sola cadena ⇒ BU derivada, nunca pendiente.

### ACs

| AC | Enunciado |
|---|---|
| AC-O3-01 | `POST classify` con `business_unit_code` válido + motivo válido ⇒ 200, evento clasificado. |
| AC-O3-02 | `reason` ausente / `""` / `"   "` / `null` / <3 caracteres ⇒ 422; sin cambios. |
| AC-O3-03 | Exactamente uno de `business_unit_code` / `company_business_unit_id`; ambos o ninguno ⇒ 422. |
| AC-O3-04 | Código inexistente, unidad deshabilitada o de otra empresa ⇒ 400/404 fail-closed; sin cambios. |
| AC-O3-05 | Sin `masters:update` ⇒ 403 (también el autor del registro). |
| AC-O3-06 | Empresa ajena / evento inexistente / ya clasificado ⇒ 404. |
| AC-O3-07 | Auditoría P-09: actor, `entity_id`, `previous_state='pending'`, `new_state=<código>`, `change_reason`, timestamp. |
| AC-O3-08 | Clasificar no cambia las concesiones/unidades efectivas de nadie ni habilita unidades. |
| AC-O3-09 | `GET classification-candidates`: `masters:update`; solo unidades habilitadas+activas de la empresa del registro; sin ids; 404 si no pendiente o ajeno; 403 sin permiso. |
| AC-O3-10 | UI: cada fila de la bandeja muestra «Clasificar» **solo** si el usuario tiene `masters:update`; el diálogo muestra inspección, fecha, granja, galpón, registrado por, estado; selector «Código — Descripción» con los candidatos; motivo obligatorio; Cancelar / Clasificar; errores sin 422 crudo. |
| AC-O3-11 | Tras clasificar: la fila sale de la bandeja, el evento aparece en Historial de la cadena, persiste tras recargar. |
| AC-O3-12 | E2E O3-E2E-01..08 (mandato §16). |

## B. Procedencia exacta del build

### Discovery

- Dockerfiles (`backend/`, `frontend/`) no reciben SHA; los workflows `docker-push-{backend,frontend}[-dev].yml`
  no pasan `build-args`. `docker/metadata-action` ya añade `org.opencontainers.image.revision` (= SHA del
  push) vía `labels:`; se conserva y se complementa con `ARG`/`LABEL` explícitos.
- UAT consume la imagen `develop` (`docker-compose.develop.yml`, Watchtower). Las imágenes se reconstruyen
  **solo** si el push toca `backend/**` o `frontend/**` (filtros `paths`).
- `GET /health` es público y ya expone `environment` y `version` ⇒ metadata de build no sensible es
  consistente con la política vigente. nginx solo proxea `/api/`.

### Decisiones

- **D-B1 Backend.** `Dockerfile`: `ARG GIT_SHA=unknown`, `ARG BUILD_TIME=unknown`; `ENV GA_GIT_SHA`/`GA_BUILD_TIME`;
  `LABEL org.opencontainers.image.revision=$GIT_SHA` y `...created=$BUILD_TIME` (al final de la etapa de
  runtime, para no invalidar la caché de dependencias). `settings` lee `GA_GIT_SHA`, `GA_BUILD_TIME` (default
  `unknown`).
- **D-B2 Endpoint.** `GET /api/v1/version` **público** (`Alcance.PUBLICA`), solo lectura, sin efectos:
  `{"git_sha","build_time","environment"}`. Nada más (ni hostname, ni rutas, ni DSN, ni configuración).
  `GET /health` no cambia. Respuesta con `Cache-Control: no-store` (ya la pone el middleware).
- **D-B3 Frontend.** El build emite `dist/version.json` = `{"git_sha","build_time"}` (plugin mínimo en
  `vite.config.ts` con `process.env.GIT_SHA`/`BUILD_TIME`, `unknown` si faltan) y el bundle incorpora
  `__GA_BUILD_SHA__` (`define`) sin mostrarlo en pantalla. `Dockerfile` frontend: `ARG`/`ENV` antes de
  `npm run build` + `LABEL` OCI. nginx: `location = /version.json` con `Cache-Control: no-store`.
- **D-B4 CI.** Los cuatro workflows pasan `build-args: GIT_SHA=${{ github.sha }}`, `BUILD_TIME=<UTC ISO>`
  y un paso de guardia que falla si `github.sha` está vacío. Autorizado expresamente por el mandato §19/§22/§25.
- **D-B5 Guardia `unknown`.** `scripts/verify_runtime_sha.sh <base_url> <sha_esperado>`: consulta
  `/api/v1/version` y `/version.json`; falla con `unknown`, vacío o SHA distinto. Si el SHA del runtime ≠
  HEAD pero **los árboles `backend/` y `frontend/` coinciden** entre ambos commits (commit solo de
  docs/tests, que no reconstruye la imagen), imprime `PARITY=PASS (tree-equal)` y los dos SHA; si no, `FAIL`.
  No se declara paridad por nombre de bundle.
- **D-B6 Sin `.git` en runtime.** El SHA viene de la variable inyectada en build; ningún `git` en runtime.

### ACs

| AC | Enunciado |
|---|---|
| AC-VP-01 | `GA_GIT_SHA=<x>` ⇒ `/api/v1/version` devuelve exactamente `<x>`. |
| AC-VP-02 | La respuesta contiene únicamente `git_sha`, `build_time`, `environment`; sin secretos ni rutas. |
| AC-VP-03 | `vite build` con `GIT_SHA=<x>` ⇒ `dist/version.json` y bundle contienen `<x>`. |
| AC-VP-04 | Sin `GA_GIT_SHA` ⇒ `unknown` y no hay llamada a `git` (el código no importa `subprocess`). |
| AC-VP-05 | Dockerfiles declaran `ARG GIT_SHA` + `LABEL org.opencontainers.image.revision`; los 4 workflows pasan `build-args` (test de contrato sobre los archivos). |
| AC-VP-06 | `/api/v1/version` es `PUBLICA` en `route_scope` y no exige token. |
| AC-VP-07 | `verify_runtime_sha.sh`: PASS con SHA igual; FAIL con `unknown`; PASS tree-equal; FAIL si difieren los árboles (probado con servidor simulado). |
| AC-VP-08 | Runtime real: `BACKEND_RUNTIME_SHA`, `FRONTEND_RUNTIME_SHA` == SHA fuente (o árboles iguales). |

### Pins a avanzar de forma consciente

Recuento de rutas `/api/` 241 → 243 (+`classification-candidates`, +`version`).

## C. Estado de certificación

Ver `audit/ga-o3-classification-build-provenance/CERTIFICATION.md` (local) y `POSTDEPLOY.md` (runtime).

- IMPL `92d8db0`. Backend 1906/0/52 · frontend 725 · tsc/build PASS · E2E serie 207/0/0 (8 nuevas O3-E2E) · mutación 19/19.
- O-3: cerrada en local. Procedencia: CERRADA (UAT declara SHA exacto `424dda0`). Paridad contra `main` certificado: FAIL estricto por 1 archivo ajeno (ver POSTDEPLOY).
- Observaciones nuevas: O-11 (filtros de granja capados a 100, P3 preexistente). O-10 intacta.

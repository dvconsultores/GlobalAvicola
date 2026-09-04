# 02 — ARQUITECTURA E INFRAESTRUCTURA

Estados de evidencia: `CONFIRMADO` (verificado en código/runtime local) · `INFERIDO` (deducido de configuración) · `NO ENCONTRADO` · `NO VERIFICABLE` (requiere acceso al entorno productivo).

---

## 1. Inventario tecnológico

| Capa | Tecnología | Versión declarada | Evidencia |
|---|---|---|---|
| Frontend | React | ^19.2.6 | `frontend/package.json:20` |
| | Vite | ^8.0.12 | `frontend/package.json:53` |
| | TypeScript | ~6.0.2 | `frontend/package.json:51` |
| | TailwindCSS | ^4.3.1 | `frontend/package.json:29` |
| | Router | react-router-dom ^7.18.0 | `frontend/package.json:25` |
| | Estado | Zustand ^5.0.14 | `frontend/src/stores/` (5 stores) |
| | Formularios | react-hook-form ^7.80 + zod ^4.4.3 + @hookform/resolvers | `frontend/src/pages/operations/OperationFormPage.tsx:2-4` |
| | HTTP | axios ^1.18.1 con interceptores | `frontend/src/services/api.ts` |
| | i18n | react-i18next ^17 + i18next-http-backend | `frontend/src/i18n/index.ts` |
| | Gráficas | recharts ^3.9.0 | `frontend/src/pages/reports/ReportsPage.tsx:4` |
| | Export | xlsx ^0.18.5, jspdf ^4.2.1, jspdf-autotable ^5.0.8 | `frontend/src/utils/export.ts` |
| | Iconos | lucide-react ^1.21.0 | `frontend/src/data/processCatalog.ts:1-7` |
| | Telegram | @telegram-apps/sdk ^3.11.8 | `frontend/src/hooks/useTelegram.ts` |
| Backend | FastAPI | >=0.110 | `backend/pyproject.toml:7` |
| | Python | >=3.11 | `backend/pyproject.toml:5` |
| | SQLAlchemy | >=2.0 (async) | `backend/app/database.py` |
| | Pydantic | v2 + pydantic-settings | `backend/app/config.py` |
| | Driver | asyncpg >=0.29 | `backend/pyproject.toml:10` |
| | Migraciones | Alembic >=1.13 | `backend/alembic/` |
| | Auth | PyJWT + passlib[bcrypt] | `backend/app/auth/security.py` |
| | Rate limit | slowapi >=0.1.9 | `backend/app/main.py:5,14` |
| | Uploads | python-multipart, aiofiles | `backend/app/operations/router.py` |
| | Telegram bot | pyTelegramBotAPI >=4.29 | `backend/app/integrations/telegram/bot.py` |
| Base de datos | PostgreSQL | 15 (imagen usada en CI) | `.github/workflows/backend-ci.yml:19` |
| Contenedores | Docker + Compose | — | `docker-compose.yml`, `docker-compose.dev.yml` |
| Servidor web | Nginx 1.27-alpine | — | `frontend/Dockerfile:22` |
| CI/CD | GitHub Actions | 5 workflows | `.github/workflows/` |
| Auto-deploy | Watchtower (poll 60 s) | — | `docker-compose.yml:87-99` |
| QA | Pytest, Vitest 4, Playwright 1.61 | — | `backend/pyproject.toml`, `frontend/package.json` |

**Estado: CONFIRMADO.**

---

## 2. Arquitectura de aplicación

### 2.1 Backend — modular monolito por dominio

```
backend/app/
├── main.py            FastAPI app, CORS, security headers, rate limit condicional, registro de routers
├── config.py          Settings (pydantic-settings) + feature flags
├── database.py        async engine, sessionmaker, get_db (commit/rollback por request)
├── dependencies.py    re-export de get_current_user / get_company_filter / require_company
├── auth/              models · schemas · security(JWT) · service · router
├── masters/           19 catálogos con CRUD genérico (register_crud) + MasterService genérico
├── lots/              lotes, fases, saldos iniciales, egg_batches, chick_batches, trazabilidad
├── operations/        modelo unificado OperationalEvent + 6 submodelos + validators (BR) + evidencias + alertas
├── review/            ReviewService, ApprovalService, ApprovalStepService
├── corrections/       CorrectionLog
├── audit/             AuditLog + listeners(SQLAlchemy) + helpers(servicio) + context(ContextVar)
├── reports/           14 endpoints de KPI + reporte de lote + comparativo SAP
├── dashboard/         KPIs móvil y admin
└── integrations/
    ├── sap/           adapter(ABC) · ManualSapAdapter · MockSapAdapter · service · models · router
    └── telegram/      bot.py (lanzador Mini App)
```

Patrón: **router → service → SQLAlchemy models**. No hay capa repositorio (el README la anuncia; no existe). Los servicios reciben `db` + `current_user` y aplican aislamiento por `company_id`.

**Desviación respecto al README:** `README.md:60-75` describe `backend/app/routers/`, `schemas/`, `services/`, `repositories/`, `models/`, `domain/`, `workflows/` y `migrations/`. Ninguna de esas carpetas existe. Estado: `IMPLEMENTADO_NO_DOCUMENTADO` / documentación obsoleta.

### 2.2 Frontend — páginas con acceso directo a axios

```
frontend/src/
├── main.tsx           bootstrap, registro de accesores de token, init Telegram, restos de dark mode
├── App.tsx            40 entradas de ruta, ProtectedRoute, WebOnlyRoute
├── pages/             24 componentes de página
├── components/        ui/ (16), layout/ (9), operations/ (6), data-table/, TraceabilityTree, Toast, Icon
├── services/          12 módulos (api.ts + 11 servicios de dominio)  ← 11 de 12 SIN USO REAL
├── hooks/             10 hooks                                        ← 9 de 10 SIN USO REAL
├── stores/            auth, ui, company, theme, i18n (Zustand)
├── data/              processCatalog (catálogo de etapas/eventos), navigationConfig, statusColors, thermalCurves
├── i18n/              init de i18next (traducciones en public/locales/{es,en}/translation.json)
└── utils/export.ts    Excel/PDF cliente
```

**Hallazgo arquitectónico mayor:** la capa `services/` + `hooks/` está **completamente desconectada**. Ninguna página importa un servicio de dominio ni un hook de datos; todas las páginas invocan `api.get/post/put/delete` con URLs literales. Los 11 servicios solo son importados por los 9 hooks, y los hooks no son importados por nadie.

Evidencia: `frontend/src/pages/**` no contiene ninguna importación de `../../services/*.service` ni de `../../hooks/use*`; `useTelegram` es el único hook consumido (`App.tsx:4`, `main.tsx:7`).
Consecuencia directa: los desajustes de contrato (límites de paginación, filtros inexistentes) no tienen un punto único donde corregirse.

---

## 3. Infraestructura

### 3.1 Dónde y cómo corre

```
                 Usuario / Telegram Mini App
                            │
                            ▼
                 avicola.globaldv.net        (DNS + TLS: NO ENCONTRADO en el repo — INFERIDO externo)
                            │
                            ▼
        ┌───────────────────────────────────────────┐
        │ Host Docker (proveedor: INFERIDO Digital  │
        │ Ocean, por la IP 64.225.104.69 del .env)  │
        │                                           │
        │  globalavicola-frontend  :3005→80         │
        │    Nginx 1.27  ·  SPA  ·  /api/ → backend │
        │                                           │
        │  globalavicola-backend   :8002→8000       │
        │    Uvicorn · FastAPI                      │
        │    /app/media  (SIN VOLUMEN)              │
        │    /tmp/sap_exports (SIN VOLUMEN)         │
        │                                           │
        │  globalavicola-telegram-bot               │
        │    misma imagen, comando bot.py           │
        │                                           │
        │  watchtower  (docker.sock, poll 60 s)     │
        └───────────────────────────────────────────┘
                            │
                            ▼
              PostgreSQL EXTERNO en IP pública
              (no forma parte del compose)
```

| Elemento | Estado | Evidencia |
|---|---|---|
| Cloud / on-prem | INFERIDO cloud | IP pública en `backend/.env`; imágenes en Docker Hub |
| Proveedor | INFERIDO (rango DigitalOcean) | `backend/.env` `POSTGRES_HOST` |
| Hosting frontend | CONFIRMADO — Nginx en contenedor | `frontend/Dockerfile`, `frontend/nginx.conf` |
| Hosting backend | CONFIRMADO — Uvicorn en contenedor | `backend/Dockerfile:52` |
| Base de datos | CONFIRMADO externa, **no gestionada por el compose** | `docker-compose.yml` no define servicio `db` |
| Storage de archivos | CONFIRMADO — filesystem del contenedor, **sin volumen** | `backend/app/operations/router.py:19`; `docker-compose.yml` sin `volumes` |
| CDN | NO ENCONTRADO | — |
| DNS / SSL | NO ENCONTRADO en el repo | `TELEGRAM_MINI_APP_URL=https://avicola.globaldv.net` en `.env.example` |
| Reverse proxy | CONFIRMADO — Nginx `location /api/ → http://backend:8000` | `frontend/nginx.conf:41` |
| Workers / colas | NO ENCONTRADO | ninguna dependencia de Celery/RQ/arq |
| Cron / schedulers | NO ENCONTRADO | los reintentos SAP requieren invocación manual de `POST /sap/retry` |
| Secretos | CONFIRMADO — variables de entorno; sin gestor de secretos | `docker-compose.yml`, `.env` (no versionado) |
| Ambientes | CONFIRMADO: `development` / `production` por variable `ENVIRONMENT`; **no existe staging** | `backend/app/config.py:11` |
| CI/CD | CONFIRMADO — GitHub Actions | `.github/workflows/` |
| Backups | NO ENCONTRADO | ningún script, ningún job, ninguna documentación |
| Monitoring / alertas | NO ENCONTRADO | sin Sentry, sin Prometheus, sin logging estructurado |
| Health checks | CONFIRMADO | `GET /health`; healthcheck en ambos Dockerfile y en compose |

### 3.2 Hallazgos de infraestructura

**INF-01 — Despliegue continuo sin puerta de calidad (P0).**
`docker-push-backend.yml` y `docker-push-frontend.yml` se disparan en `push` a `main`, publican `:latest`, y Watchtower (`WATCHTOWER_POLL_INTERVAL=60`) actualiza los contenedores. Los workflows de test (`backend-ci.yml`, `frontend-ci.yml`) solo se disparan en `pull_request`, y el repositorio tiene **0 merges y 0 pull requests** en 171 commits. Resultado: **ningún commit del proyecto ha pasado nunca por CI**, y todos llegaron a producción automáticamente.
Evidencia: `.github/workflows/docker-push-backend.yml:9-14`; `.github/workflows/backend-ci.yml:8-12`; `git log --merges` → 0; commit `9004f3a` ("ci: tests solo en pull_request, no en push a main").

**INF-02 — Migraciones no automatizadas (P0).**
No existe `alembic upgrade head` en `backend/Dockerfile` (CMD es solo uvicorn), ni en `docker-compose.yml`, ni en ningún workflow. Con despliegue automático, cualquier release con cambio de esquema rompe producción hasta que alguien ejecute la migración a mano. Precedente documentado: `AUDITORIA_FUNCIONAL_E2E.md` H1 describe 4 migraciones sin aplicar que causaban `UndefinedColumnError` en producción.

**INF-03 — Pérdida de datos en cada despliegue (P0).**
Evidencias operativas (`/app/media/evidences/...`) y exportaciones SAP (`/tmp/sap_exports/...`) se escriben en el sistema de archivos del contenedor sin volumen. Watchtower recrea el contenedor en cada publicación de imagen.

**INF-04 — Rate limiting desactivado en producción (P1).**
`docker-compose.yml` pasa `FEATURE_SAP_ENABLED` pero **no** `FEATURE_RATE_LIMIT_ENABLED`; el valor por defecto en `backend/app/config.py:96` es `False`. La tarea T-086 y `spec.md §14.3` exigen activarlo. El endpoint de login queda sin protección anti-fuerza bruta, con credenciales conocidas publicadas.

**INF-05 — `FEATURE_TELEGRAM_ENABLED` es una variable inexistente (P3).**
Se inyecta en `docker-compose.yml:29` pero `Settings` no la declara y `extra="ignore"` la descarta. El servicio `telegram-bot` arranca siempre.

**INF-06 — Base de datos en IP pública con superusuario (P1).**
`backend/.env` apunta el entorno de desarrollo directamente a un PostgreSQL en IP pública usando el rol `postgres` y sin `?ssl=require` (la línea SSL está comentada en `.env.example`). Los mismos datos aparecen en el `.env` de la raíz junto a credenciales SMTP de AWS SES. Los ficheros `.env` **no** están versionados (verificado: `git log --all -- '*.env'` vacío, `.gitignore:19,36`), por lo que no hay fuga en el historial, pero sí en las estaciones de trabajo.

**INF-07 — Límite de subida incompatible entre Nginx y el backend (P2).**
El backend acepta evidencias de hasta 10 MB (`operations/router.py:21`), pero `frontend/nginx.conf` no define `client_max_body_size`, quedando en el valor por defecto de Nginx (1 MB). Cualquier evidencia entre 1 MB y 10 MB fallará con 413 en producción.

**INF-08 — Watchtower monta el socket de Docker (P2).**
`/var/run/docker.sock` montado en un contenedor con acceso a red. Superficie de escalada a root en el host.

**INF-09 — Divergencia de configuración entre `.env` raíz y `backend/.env` (P3).**
Raíz: `BACKEND_PORT=8002`, `SAP_ENABLED=false`. Backend: `BACKEND_PORT=8000`, `FEATURE_SAP_ENABLED=true`. Dos fuentes de verdad para el mismo entorno.

**INF-10 — Objetivos del Makefile rotos (P3).**
`make db-seed` ejecuta `python -m app.seeds`, pero los seeds están en `backend/seeds/`, no en `backend/app/seeds/`. `make backend-lint` (ruff) y `make backend-typecheck` (mypy) fallan: ninguna de las dos herramientas está instalada en `backend/.venv`.

---

## 4. Ambientes

| Ambiente | Definido | Diferencias | Estado |
|---|---|---|---|
| development | Sí | `docker-compose.dev.yml`: build local, `--reload`, Vite HMR, watchtower desactivado | CONFIRMADO |
| test | Parcial | solo dentro de `backend-ci.yml` (servicio Postgres efímero) | CONFIRMADO |
| **staging** | **No existe** | T-084 lo exige antes de producción | **NO ENCONTRADO** |
| production | Sí | `docker-compose.yml`, imágenes `:latest`, `ENVIRONMENT=production`, `DEBUG=false`, HSTS activo | CONFIRMADO |

---

## 5. Observabilidad

| Capacidad | Estado | Evidencia |
|---|---|---|
| Logging estructurado | NO IMPLEMENTADO | solo `logging.basicConfig` en el bot de Telegram; el backend no configura logging |
| Correlation IDs | NO IMPLEMENTADO | — |
| Audit trail | PARCIAL (duplicado) | ver `13_ROLES_AND_SECURITY.md` |
| Error tracking (Sentry…) | NO ENCONTRADO | sin dependencia |
| Métricas / dashboards | NO ENCONTRADO | — |
| Alertas de infraestructura | NO ENCONTRADO | T-089 lo deja como pendiente |
| Tracing | NO ENCONTRADO | — |
| Health checks | IMPLEMENTADO | `GET /health` + healthcheck Docker |
| Backup / restore | NO ENCONTRADO | ningún procedimiento |

**Respuesta a la pregunta obligatoria — ¿se puede diagnosticar una falla productiva con la observabilidad actual?**
**No.** No hay logs estructurados, ni identificador de correlación, ni captura de errores, ni métricas. El único recurso es `docker logs` con el formato por defecto de Uvicorn y el `AuditLog` de negocio, que no registra errores técnicos. Un fallo como el `NameError` de mortalidad (P0-1) solo sería visible como un 500 genérico en el navegador del operador.

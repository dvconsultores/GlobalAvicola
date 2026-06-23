# Plan Técnico — Global Avícola

> **Documento:** 04-technical-plan.md
> **Versión:** 1.0.0
> **Fecha:** 2026-06-22

---

## 1. INTRODUCCIÓN

Este documento define la arquitectura técnica, stack tecnológico, estructura del proyecto, decisiones de diseño y plan de implementación para Global Avícola.

---

## 2. ARQUITECTURA GENERAL

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENTES                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐      │
│  │  Móvil   │  │  Tablet  │  │  Desktop Admin   │      │
│  │ (campo)  │  │ (mixto)  │  │  (oficina)       │      │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘      │
│       │             │                 │                 │
│       └─────────────┼─────────────────┘                 │
│                     │ HTTPS                             │
└─────────────────────┼───────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────┐
│              CONTENEDORES DOCKER                         │
│  ┌──────────────────┴──────────────────┐                │
│  │        NGINX (Reverse Proxy)        │ :80/:443       │
│  └────────┬─────────────────┬──────────┘                │
│           │                 │                            │
│  ┌────────┴────────┐ ┌──────┴──────────┐               │
│  │   FRONTEND       │ │   BACKEND       │               │
│  │   React + Vite   │ │   FastAPI       │               │
│  │   :5173 (dev)    │ │   :8000         │               │
│  │   :80 (prod)     │ │                 │               │
│  └─────────────────┘ └──────┬──────────┘               │
│                             │                            │
│                    ┌────────┴──────────┐                │
│                    │   POSTGRESQL 15   │ :5432           │
│                    └───────────────────┘                │
│                                                         │
│  ┌────────────────────────────────────┐                 │
│  │   SAP INTEGRATION LAYER (future)   │                 │
│  │   (API/OData/File/BAPI/RFC)        │                 │
│  └────────────────────────────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

---

## 3. STACK TECNOLÓGICO

### 3.1 Backend

| Componente | Tecnología | Versión | Justificación |
|---|---|---|---|
| **Lenguaje** | Python | 3.11+ | Maduro, gran ecosistema, tipado fuerte |
| **Framework API** | FastAPI | 0.110+ | Alto rendimiento, OpenAPI automático, async nativo |
| **ORM** | SQLAlchemy | 2.0+ | ORM moderno con async support, migraciones |
| **Migraciones** | Alembic | 1.13+ | Integración nativa con SQLAlchemy |
| **Validación** | Pydantic | 2.0+ | Validación de esquemas, serialización |
| **Autenticación** | PyJWT | 2.8+ | JWT estándar, RBAC |
| **Servidor** | Uvicorn | 0.27+ | ASGI server de alto rendimiento |
| **Testing** | Pytest + HTTPX | latest | Tests unitarios, integración y async |
| **Linting** | Ruff | latest | Linter rápido, reemplaza flake8/isort |
| **Type checking** | Mypy | latest | Verificación de tipos estática |

### 3.2 Frontend

| Componente | Tecnología | Versión | Justificación |
|---|---|---|---|
| **Framework** | React | 18.3+ | Ecosistema maduro, componentes, hooks |
| **Build tool** | Vite | 5.4+ | Rápido, HMR, TypeScript nativo |
| **Lenguaje** | TypeScript | 5.5+ | Tipado fuerte, mejor DX |
| **Estilos** | TailwindCSS | 3.4+ | Utility-first, rápido, sin CDN |
| **Router** | React Router | 6.26+ | Navegación SPA estándar |
| **Estado** | Zustand | 4.5+ | Ligero, simple, TypeScript-friendly |
| **HTTP Client** | Axios | 1.7+ | Interceptors, cancelación |
| **i18n** | react-i18next | 14+ | Internacionalización completa |
| **Formularios** | React Hook Form | 7.52+ | Rendimiento, validación |
| **Validación** | Zod | 3.23+ | Validación de esquemas |
| **Tablas** | TanStack Table | 8.20+ | Headless, flexible |
| **Gráficos** | Recharts | 2.12+ | React nativo, ligero |
| **Testing** | Vitest + Playwright | latest | Unit + E2E |
| **Iconos** | Lucide React | latest | SVG limpios, tree-shakeable |

### 3.3 Infraestructura

| Componente | Tecnología | Versión |
|---|---|---|
| **Base de datos** | PostgreSQL | 15+ |
| **Contenedores** | Docker + Docker Compose | latest |
| **Reverse Proxy** | Nginx | 1.25+ |
| **CI/CD** | GitHub Actions | latest |
| **E2E Testing** | Playwright | latest |

---

## 4. ESTRUCTURA DEL PROYECTO (DETALLADA)

```
global-avicola/
│
├── README.md
├── Makefile
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── .github/
│   └── workflows/
│       ├── backend-ci.yml       # Lint, test, typecheck backend
│       ├── frontend-ci.yml      # Lint, test, typecheck, build frontend
│       └── e2e.yml              # Playwright E2E tests
│
├── docs/                        # Documentación
│   ├── 00-product-vision.md
│   ├── 01-legacy-audit.md
│   ├── 02-functional-spec.md
│   ├── 03-domain-model.md
│   ├── 04-technical-plan.md
│   ├── 05-migration-plan.md
│   ├── 06-api-contract.md
│   ├── 07-qa-plan.md
│   ├── 08-browser-compatibility-plan.md
│   ├── 09-i18n-plan.md
│   ├── 10-sap-integration-strategy.md
│   ├── 11-ui-ux-design-system.md
│   ├── 12-approval-workflow.md
│   └── 13-audit-strategy.md
│
├── specs/                       # Spec-Driven Development
│   └── global-avicola/
│       └── spec.md
│
├── backend/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── requirements.txt         # O usar solo pyproject.toml
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app factory
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── dependencies.py      # FastAPI dependencies (auth, db, etc.)
│   │   │
│   │   ├── auth/                # Autenticación y autorización
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # User, Role, Permission (SQLAlchemy)
│   │   │   ├── schemas.py       # Pydantic schemas
│   │   │   ├── service.py       # Lógica de auth
│   │   │   ├── router.py        # Endpoints /auth/*
│   │   │   └── security.py      # JWT, hashing, RBAC
│   │   │
│   │   ├── masters/             # Maestros / Catálogos
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # Company, Farm, House, Hatchery, etc.
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py        # Endpoints /masters/*
│   │   │
│   │   ├── lots/                # Gestión de Lotes
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # Lot, LotPhase, OpeningBalance
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py        # Endpoints /lots/*
│   │   │
│   │   ├── operations/          # Eventos Operativos
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # OperationalEvent, BirdMovement, EggMovement, etc.
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py        # Endpoints /operations/*
│   │   │
│   │   ├── review/              # Centro de Revisión Operativa
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # ReviewBatch, ApprovalStep, ApprovalAction
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py        # Endpoints /review/*
│   │   │
│   │   ├── corrections/         # Correcciones
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # CorrectionLog
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   │
│   │   ├── approvals/           # Aprobaciones
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py        # Endpoints /approvals/*
│   │   │
│   │   ├── consolidation/       # Consolidación para SAP
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # ConsolidatedMovement
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   │
│   │   ├── audit/               # Auditoría
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # AuditLog
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── router.py        # Endpoints /audit/*
│   │   │
│   │   ├── reports/             # Reportes e Indicadores
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   └── router.py        # Endpoints /reports/*
│   │   │
│   │   ├── dashboard/           # Dashboard / KPIs
│   │   │   ├── __init__.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   │
│   │   └── integrations/        # Integraciones externas
│   │       └── sap/
│   │           ├── __init__.py
│   │           ├── models.py    # SapReference, SapSyncJob, SapPayload, SapResponse
│   │           ├── schemas.py
│   │           ├── service.py   # Lógica de integración SAP
│   │           ├── router.py    # Endpoints /integrations/sap/*
│   │           ├── adapter.py   # Capa de abstracción (API, File, OData, etc.)
│   │           └── mock.py      # Mock para desarrollo sin SAP
│   │
│   ├── seeds/                   # Datos semilla para desarrollo
│   │   ├── __init__.py
│   │   ├── dev_seeds.py
│   │   └── demo_data.py
│   │
│   └── tests/
│       ├── conftest.py          # Fixtures: test DB, test client, auth
│       ├── test_auth/
│       ├── test_masters/
│       ├── test_lots/
│       ├── test_operations/
│       ├── test_review/
│       ├── test_approvals/
│       ├── test_audit/
│       ├── test_sap_integration/
│       └── test_reports/
│
└── frontend/
    ├── Dockerfile
    ├── .dockerignore
    ├── nginx.conf
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.ts
    ├── postcss.config.js
    ├── index.html
    │
    ├── public/
    │   ├── favicon.ico
    │   ├── logo.svg
    │   └── locales/             # i18n translation files
    │       ├── es/
    │       │   └── translation.json
    │       └── en/
    │           └── translation.json
    │
    ├── src/
    │   ├── main.tsx             # Entry point
    │   ├── App.tsx              # Root component with router
    │   ├── vite-env.d.ts
    │   │
    │   ├── i18n/                # i18n config
    │   │   ├── index.ts         # i18next setup
    │   │   └── resources.ts     # Dynamic import of translation files
    │   │
    │   ├── components/          # Componentes compartidos
    │   │   ├── ui/              # UI primitives (Button, Input, Card, Table, Modal, Badge, etc.)
    │   │   ├── layout/          # Layout components (Sidebar, Header, MobileNav)
    │   │   ├── forms/           # Form components (FormField, Select, DatePicker, etc.)
    │   │   ├── data-table/      # Data table with filters, pagination, sorting
    │   │   ├── status-badge/    # Status indicator badges
    │   │   ├── approval/        # Approval workflow components
    │   │   └── audit/           # Audit log viewer components
    │   │
    │   ├── pages/               # Páginas por módulo
    │   │   ├── auth/
    │   │   │   ├── LoginPage.tsx
    │   │   │   └── ForgotPasswordPage.tsx
    │   │   ├── dashboard/
    │   │   │   ├── MobileDashboard.tsx
    │   │   │   └── AdminDashboard.tsx
    │   │   ├── masters/
    │   │   │   ├── FarmsPage.tsx
    │   │   │   ├── HousesPage.tsx
    │   │   │   ├── HatcheriesPage.tsx
    │   │   │   └── ...
    │   │   ├── lots/
    │   │   │   ├── LotListPage.tsx
    │   │   │   ├── LotDetailPage.tsx
    │   │   │   ├── LotActivationPage.tsx
    │   │   │   └── OpeningBalancePage.tsx
    │   │   ├── operations/
    │   │   │   ├── FeedRegistration.tsx
    │   │   │   ├── WeightRecording.tsx
    │   │   │   ├── MortalityRecording.tsx
    │   │   │   ├── VaccinationRecording.tsx
    │   │   │   ├── EggCollection.tsx
    │   │   │   ├── EggDispatch.tsx
    │   │   │   ├── IncubationLoad.tsx
    │   │   │   ├── BirthRegistration.tsx
    │   │   │   ├── ChickDispatch.tsx
    │   │   │   ├── BirdReception.tsx
    │   │   │   ├── BirdExit.tsx
    │   │   │   └── FarmInspection.tsx
    │   │   ├── review/
    │   │   │   ├── ReviewCenter.tsx
    │   │   │   ├── ReviewDetail.tsx
    │   │   │   └── CorrectionForm.tsx
    │   │   ├── approvals/
    │   │   │   ├── ApprovalPanel.tsx
    │   │   │   └── BatchApproval.tsx
    │   │   ├── sap/
    │   │   │   ├── SapSyncPanel.tsx
    │   │   │   ├── SapErrorsPage.tsx
    │   │   │   └── SapReferencesPage.tsx
    │   │   ├── audit/
    │   │   │   └── AuditLogViewer.tsx
    │   │   ├── reports/
    │   │   │   ├── LotReport.tsx
    │   │   │   ├── KpiDashboard.tsx
    │   │   │   └── SapComparisonReport.tsx
    │   │   ├── users/
    │   │   │   ├── UserManagement.tsx
    │   │   │   └── RoleManagement.tsx
    │   │   └── settings/
    │   │       ├── ProfilePage.tsx
    │   │       └── CompanySettings.tsx
    │   │
    │   ├── hooks/               # Custom hooks
    │   │   ├── useAuth.ts
    │   │   ├── useLot.ts
    │   │   ├── useOperations.ts
    │   │   ├── useReview.ts
    │   │   ├── useApprovals.ts
    │   │   ├── useAudit.ts
    │   │   ├── useSap.ts
    │   │   ├── useMediaQuery.ts
    │   │   └── useI18n.ts
    │   │
    │   ├── services/            # API clients
    │   │   ├── api.ts           # Axios instance with interceptors
    │   │   ├── auth.service.ts
    │   │   ├── masters.service.ts
    │   │   ├── lots.service.ts
    │   │   ├── operations.service.ts
    │   │   ├── review.service.ts
    │   │   ├── approvals.service.ts
    │   │   ├── audit.service.ts
    │   │   ├── reports.service.ts
    │   │   └── sap.service.ts
    │   │
    │   ├── stores/              # Zustand stores
    │   │   ├── auth.store.ts
    │   │   ├── ui.store.ts
    │   │   └── i18n.store.ts
    │   │
    │   ├── types/               # TypeScript types
    │   │   ├── api.types.ts
    │   │   ├── domain.types.ts
    │   │   └── enums.ts
    │   │
    │   └── styles/              # Estilos globales
    │       ├── globals.css      # Tailwind directives + custom
    │       └── theme.ts         # Tailwind theme extension (colors, fonts)
    │
    ├── tests/
    │   ├── unit/
    │   └── e2e/
    │       ├── auth.spec.ts
    │       ├── operations.spec.ts
    │       ├── review.spec.ts
    │       ├── approvals.spec.ts
    │       └── sap.spec.ts
    │
    └── playwright.config.ts
```

---

## 5. DECISIONES DE ARQUITECTURA

### 5.1 Backend

| Decisión | Elección | Justificación |
|---|---|---|
| **Async vs Sync** | Async (asyncpg) | Mayor rendimiento para I/O intensivo (DB, SAP) |
| **ORM** | SQLAlchemy 2.x async | ORM más maduro de Python, async nativo en 2.x |
| **Estructura** | Modular por dominio | Cada módulo independiente con models/schemas/service/router |
| **Validación** | Pydantic v2 en capa API | Validación en entrada/salida, no en capa de negocio |
| **Autenticación** | JWT access + refresh tokens | Estándar, stateless, compatible con móvil y web |
| **Autorización** | RBAC con dependencias FastAPI | Permisos granulares por módulo, acción y alcance |
| **Migraciones** | Alembic autogenerate | Control de versiones de esquema, reproducible |
| **Manejo de errores** | Excepciones HTTP estandarizadas | Códigos de error consistentes en toda la API |
| **Logging** | Structlog / Python logging | JSON estructurado para observabilidad |
| **Paginación** | Cursor-based para listados grandes | Mejor rendimiento que offset en tablas grandes |

### 5.2 Frontend

| Decisión | Elección | Justificación |
|---|---|---|
| **State management** | Zustand | Más simple que Redux, mejor TS que Context |
| **Estilos** | TailwindCSS | Rápido desarrollo, consistente, sin CDN |
| **Formularios** | React Hook Form + Zod | Rendimiento (uncontrolled) + validación tipada |
| **Tablas** | TanStack Table | Headless, flexible, compatible con Tailwind |
| **i18n** | react-i18next | Estándar, lazy loading de traducciones |
| **Rutas** | React Router v6 con lazy loading | Code splitting automático por ruta |
| **Mobile-first** | Tailwind breakpoints + useMediaQuery | Adaptación real a viewport |
| **Bundle size** | Vite code splitting | Carga rápida en móvil con 4G |
| **PWA** | vite-plugin-pwa (opcional futuro) | Instalable en dispositivo móvil |

### 5.3 SAP S/4HANA Integration

| Decisión | Elección | Justificación |
|---|---|---|
| **Target SAP** | SAP S/4HANA | Plataforma SAP actual, OData nativo |
| **Acoplamiento** | Capa de abstracción (Adapter pattern) | Cambiar mecanismo SAP sin tocar dominio |
| **Mecanismo recomendado** | OData REST Services + SAP API Business Hub | Nativo S/4HANA, estándar REST |
| **Mecanismos alternativos** | SOAP Web Services, IDoc, SFTP | Soportados si OData no está disponible |
| **Idempotencia** | Hash SHA-256 del payload + ref SAP | Evitar envíos duplicados |
| **Reintentos** | Exponential backoff (3 intentos) | Tolerancia a fallos temporales |
| **Modo inicial** | Manual (archivos CSV/JSON) | No asumir conectividad S/4HANA disponible |
| **Mock** | Mock OData adapter para desarrollo | Desarrollo sin SAP físico |

---

## 6. DOCKER COMPOSE

```yaml
version: '3.8'
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-global_avicola}
      POSTGRES_USER: ${POSTGRES_USER:-global_avicola_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change_me}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-global_avicola_user}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      ENVIRONMENT: ${ENVIRONMENT:-development}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      target: development
    command: npm run dev
    environment:
      VITE_API_URL: http://localhost:8000/api/v1
    ports:
      - "5173:5173"
    volumes:
      - ./frontend/src:/app/src
    depends_on:
      - backend

volumes:
  pgdata:
```

---

## 7. PLAN DE IMPLEMENTACIÓN (FASES)

### Fase 0: Setup y Especificación (ACTUAL)
- ✅ Auditoría de repositorios legacy
- ✅ Visión del producto
- ✅ Especificación funcional
- ✅ Modelo de dominio
- 🔄 Plan técnico (este documento)
- ⬜ Configuración del proyecto (Docker, DB, CI/CD)
- ⬜ Especificación Spec Kit

### Fase 1: Fundación (Core)
1. Setup del proyecto backend (FastAPI + SQLAlchemy + Alembic)
2. Setup del proyecto frontend (React + Vite + TailwindCSS)
3. Docker Compose funcional
4. Autenticación JWT + RBAC básico
5. Migración inicial de base de datos
6. Seeds de desarrollo
7. CI/CD pipeline básico

### Fase 2: Maestros y Lotes
1. CRUD de maestros (empresas, granjas, galpones, etc.)
2. Gestión de lotes (creación, fases, activación manual)
3. Opening Balance / Saldos iniciales
4. Referencias SAP (importación manual)
5. i18n setup completo (ES/EN)

### Fase 3: Registro Operativo (Móvil)
1. Formularios de registro operativo mobile-first
2. Recepción de aves, distribución
3. Alimento, pesaje, mortalidad, vacunación
4. Producción de huevos, despacho
5. Incubación, nacimiento
6. Engorde
7. Validaciones de reglas de negocio

### Fase 4: Revisión y Aprobación
1. Centro de Revisión Operativa (bandeja)
2. Corrección auditada
3. Flujo de aprobación multinivel
4. Rechazo con motivo
5. Dashboard de revisión

### Fase 5: Consolidación y SAP
1. Consolidación de movimientos aprobados
2. Capa de abstracción SAP
3. Preparación de payloads
4. Envío a SAP (mock + real)
5. Bitácora de envíos
6. Gestión de errores SAP

### Fase 6: Auditoría y Reportes
1. Sistema completo de auditoría
2. Vista de auditoría
3. Reportes (lote, diferencias SAP, KPIs)
4. Exportaciones

### Fase 7: Pulido y QA
1. Testing completo (unit, integration, E2E)
2. Pruebas cross-browser
3. Pruebas mobile viewport
4. Pruebas de i18n
5. Pruebas de permisos
6. Pruebas de carga inicial
7. Documentación final

---

## 8. ESTÁNDARES DE CÓDIGO

### 8.1 Backend (Python)
- **Formateo:** Ruff (reemplaza Black + isort)
- **Linting:** Ruff
- **Type checking:** Mypy (strict mode)
- **Docstrings:** Google style
- **Nombres:** snake_case para variables/funciones, PascalCase para clases
- **Imports:** Ordenados con Ruff (stdlib → third-party → local)
- **Tests:** pytest con fixtures, AAA pattern (Arrange-Act-Assert)

### 8.2 Frontend (TypeScript/React)
- **Formateo:** Prettier
- **Linting:** ESLint con reglas estrictas
- **Type checking:** TypeScript strict mode
- **Nombres:** PascalCase para componentes, camelCase para funciones/variables
- **Imports:** Ordenados con @/ alias para src/
- **Componentes:** Functional components con hooks, nunca class components
- **Tests:** Vitest + React Testing Library

---

## 9. SEGURIDAD

1. **Autenticación:** JWT con refresh tokens, expiración configurable
2. **Autorización:** RBAC con verificación en cada endpoint (FastAPI dependencies)
3. **CORS:** Restringido a orígenes configurados en .env
4. **Validación:** Pydantic v2 en todas las entradas de API
5. **Sanitización:** SQLAlchemy parametrized queries (anti-SQL injection)
6. **Rate limiting:** slowapi o similar para endpoints de auth
7. **HTTPS:** Forzado en producción vía Nginx
8. **Secretos:** Variables de entorno, nunca en código
9. **Auditoría:** Inmutable, sin posibilidad de borrado
10. **Contraseñas:** Hash bcrypt/argon2, nunca en texto plano
11. **Archivos:** Validación de tipo, tamaño máximo, escaneo (futuro)

---

## 10. OBSERVABILIDAD

1. **Logging:** Structlog con salida JSON, niveles configurados
2. **Health checks:** Endpoint /health para DB y servicios
3. **Métricas:** (futuro) Prometheus + Grafana
4. **Alertas:** (futuro) Basadas en logs de error y latencia
5. **Trazabilidad:** Correlation ID en cada request

---

## 11. RENDIMIENTO

1. **Backend async:** Todas las operaciones I/O son async (DB, HTTP, archivos)
2. **Conexiones DB:** Pool de conexiones configurable
3. **Frontend:** Code splitting por ruta, lazy loading de componentes
4. **Assets:** Compresión, cache busting con hash en filename
5. **Imágenes:** Carga lazy, formatos modernos (WebP)
6. **Bundle size:** Budget < 500KB inicial (gzipped) para mobile

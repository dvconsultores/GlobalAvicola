# Global Avícola 🐔

**Plataforma empresarial de gestión operativa avícola integrada con SAP**

[![License](https://img.shields.io/badge/license-Proprietary-red)](./LICENSE)
[![Status](https://img.shields.io/badge/status-Spec--Driven%20Development-blue)](./docs/00-product-vision.md)

---

## 🎯 Visión

Global Avícola es la capa operativa inteligente que conecta el campo avícola con **SAP S/4HANA**. Gestión completa del ciclo productivo — desde abuelas hasta engorde — con trazabilidad total, flujo de aprobación multinivel, auditoría interna e integración SAP S/4HANA desacoplada vía OData/SOAP/IDoc.

**SAP S/4HANA sigue siendo el sistema principal administrativo (MM, FI, CO). Global Avícola es el auxiliar operativo que garantiza calidad, trazabilidad y control antes de que los datos lleguen a SAP.**

---

## 🏗️ Arquitectura

| Capa | Tecnología |
|---|---|
| **Frontend** | React 18 · Vite · TypeScript · TailwindCSS |
| **Backend** | FastAPI · Python 3.11+ · SQLAlchemy 2.x · Pydantic v2 |
| **Base de datos** | PostgreSQL 15+ |
| **Migraciones** | Alembic |
| **Autenticación** | JWT + RBAC |
| **Documentación API** | OpenAPI (automático con FastAPI) |
| **Contenedores** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |
| **QA** | Pytest · Playwright |
| **i18n** | react-i18next (ES/EN) |

---

## 📁 Estructura del Proyecto

```
global-avicola/
├── README.md
├── Makefile
├── docker-compose.yml
├── .env.example
├── .github/workflows/
├── docs/                         # Documentación del proyecto
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
├── specs/                        # Especificaciones Spec-Driven
│   └── global-avicola/
│       └── spec.md
├── backend/                      # API FastAPI
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── auth/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── models/
│   │   ├── integrations/sap/
│   │   ├── domain/
│   │   ├── audit/
│   │   ├── workflows/
│   │   └── reports/
│   ├── migrations/
│   └── tests/
└── frontend/                     # Aplicación React
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── i18n/
        ├── components/
        ├── pages/
        ├── hooks/
        ├── services/
        ├── stores/
        ├── types/
        └── styles/
```

---

## 🚀 Inicio Rápido

> ⚠️ **El proyecto está en fase de especificación.** No se ha iniciado codificación funcional.

### Fase actual: Spec-Driven Development

1. ✅ Auditoría de repositorios legacy
2. ✅ Visión del producto
3. 🔄 Especificación funcional (en progreso)
4. ⬜ Plan técnico
5. ⬜ Tareas
6. ⬜ Implementación

### Requisitos del entorno

- Git 2.39+
- Python 3.11+
- Node.js 20+
- uv / uvx
- npm
- Docker + Docker Compose
- PostgreSQL 15+

---

## 📋 Documentación

| Documento | Descripción | Estado |
|---|---|---|
| [00-product-vision.md](./docs/00-product-vision.md) | Visión y propuesta de valor | ✅ |
| [01-legacy-audit.md](./docs/01-legacy-audit.md) | Auditoría de repositorios legacy | ✅ |
| [02-functional-spec.md](./docs/02-functional-spec.md) | Especificación funcional | 🔄 |
| [03-domain-model.md](./docs/03-domain-model.md) | Modelo de dominio | ⬜ |
| [04-technical-plan.md](./docs/04-technical-plan.md) | Plan técnico | ⬜ |
| [05-migration-plan.md](./docs/05-migration-plan.md) | Plan de migración funcional | ⬜ |
| [06-api-contract.md](./docs/06-api-contract.md) | Contrato de API | ⬜ |
| [07-qa-plan.md](./docs/07-qa-plan.md) | Plan de pruebas | ⬜ |
| [10-sap-integration-strategy.md](./docs/10-sap-integration-strategy.md) | Estrategia de integración SAP | ⬜ |
| [11-ui-ux-design-system.md](./docs/11-ui-ux-design-system.md) | Sistema de diseño UI/UX | ⬜ |
| [12-approval-workflow.md](./docs/12-approval-workflow.md) | Flujo de aprobación | ⬜ |
| [13-audit-strategy.md](./docs/13-audit-strategy.md) | Estrategia de auditoría | ⬜ |

---

## 🔗 SAP S/4HANA — Estrategia de Integración

| Dirección | Mecanismo |
|---|---|
| **SAP → Global Avícola** | Importación de maestros y documentos vía OData / SFTP |
| **Global Avícola → SAP** | Envío de movimientos consolidados y aprobados vía OData / IDoc |
| **Modo inicial** | Manual (archivos CSV/JSON) |
| **Modo objetivo** | OData REST Services + SAP API Business Hub |

> **Ver estrategia completa:** [docs/10-sap-integration-strategy.md](./docs/10-sap-integration-strategy.md)

---

## 🔗 Repositorios Legacy Auditados

| Repositorio | Tecnología | Rol |
|---|---|---|
| [app_liderpollo](https://github.com/dvconsultores/app_liderpollo) | Flutter 3.16 / Dart 3.2 | App móvil multiplataforma |
| [app_liderpollo_fronend](https://github.com/dvconsultores/app_liderpollo_fronend) | Vue 3 / Vite / Vuetify 3 | Frontend web administrativo |
| [app_liderpollo_backend](https://github.com/dvconsultores/app_liderpollo_backend) | Node.js / Express / TypeORM | Backend API REST |

> **Ver auditoría completa:** [docs/01-legacy-audit.md](./docs/01-legacy-audit.md)

---

## 🎨 Diseño

- **Paleta:** Blanco (base) + Azules corporativos (primario)
- **Estados:** Verde (aprobado) · Amarillo (pendiente) · Rojo (rechazado) · Azul (en proceso)
- **Mobile-first:** Diseñado para operadores de campo en teléfono
- **Web ejecutiva:** Vista profesional para supervisores y administradores
- **Bilingüe:** Español (default) + Inglés

---

## 🔒 Seguridad

- JWT + RBAC con permisos granulares
- CORS controlado
- Validación fuerte (Pydantic v2)
- Auditoría completa de acciones
- Sanitización de entrada
- Separación multi-empresa
- Control de permisos por módulo, estado y acción

---

## 📄 Licencia

Propietaria. Todos los derechos reservados.

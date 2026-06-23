# Phase 0 Research — Global Avícola

> **Spec Kit:** `/speckit.plan` Phase 0 output
> **Date:** 2026-06-22

---

## 1. Technology Research

### 1.1 Backend Framework Selection

| Option | Pros | Cons | Decision |
|---|---|---|---|
| **FastAPI** | Async native, OpenAPI auto, Pydantic integration, high performance | Python GIL limits CPU-bound | ✅ **SELECTED** |
| Django Ninja | Django ecosystem, ORM included | Heavier, less async-native | ❌ |
| Flask + extensions | Simple, flexible | Too manual, no OpenAPI auto | ❌ |
| Node.js/Express | Same as legacy | We're moving away from it | ❌ |

### 1.2 ORM Selection

| Option | Pros | Cons | Decision |
|---|---|---|---|
| **SQLAlchemy 2.x** | Mature, async support, Alembic migrations | Learning curve | ✅ **SELECTED** |
| Tortoise ORM | Async native, Django-like | Less mature, smaller community | ❌ |
| Prisma (Python) | Type-safe | Not Python-native, limited | ❌ |
| Raw SQL (asyncpg) | Maximum control | Too much boilerplate | ❌ |

### 1.3 Frontend State Management

| Option | Pros | Cons | Decision |
|---|---|---|---|
| **Zustand** | Lightweight, TS-native, simple API | Less ecosystem than Redux | ✅ **SELECTED** |
| Redux Toolkit | Large ecosystem, devtools | Boilerplate heavy | ❌ |
| Jotai | Atomic, React-like | Less known | ❌ |
| React Context | Built-in | Re-render issues at scale | ❌ |

### 1.4 SAP Integration Approach

| Option | Pros | Cons | Decision |
|---|---|---|---|
| **Adapter Pattern** | Decoupled, swappable, testable | More initial design work | ✅ **SELECTED** |
| Direct API calls | Simple | Tight coupling, hard to test | ❌ |
| ESB/Middleware | Enterprise-grade | Overkill for v1 | ❌ |

### 1.5 Database Model Strategy

| Option | Pros | Cons | Decision |
|---|---|---|---|
| **Unified model with `phase` field** | DRY, maintainable, consistent | Migration from legacy requires mapping | ✅ **SELECTED** |
| Separate tables per phase (legacy) | Matches legacy | DRY violation, maintenance nightmare | ❌ |

---

## 2. Legacy System Analysis

Full audit in [docs/01-legacy-audit.md](../../docs/01-legacy-audit.md).

### Key Findings:
- **Flutter app** (`app_liderpollo`): Mobile UI reference only. Not migrated.
- **Vue.js frontend** (`app_liderpollo_fronend`): Web admin reference only. Replaced by React.
- **Node.js backend** (`app_liderpollo_backend`): API reference only. Replaced by FastAPI.
- **SAP integration**: `id_sap` fields exist in DB but **no integration logic implemented**.
- **Approval flow**: **Does not exist** in legacy.
- **Audit trail**: **Does not exist** in legacy.
- **Correction tracking**: **Does not exist** in legacy.
- **Entity duplication**: Tables duplicated by phase (`crias_*`, `produccion_*`, `engorde_*`).

### What to extract (conceptual only):
- Form field definitions
- Operational flows (cría → producción → incubación → engorde)
- Business rules implicit in code
- Master data catalogs
- KPI calculation formulas

### What to NOT migrate:
- Flutter widgets
- Vue components
- Express controllers
- TypeORM entities
- jQuery CDN dependency
- Dark theme design
- Duplicated table structure

---

## 3. Domain Research

### 3.1 Poultry Industry Domains

| Domain | Key Concepts | Complexity |
|---|---|---|
| Grandparent importation | International logistics, sanitary docs, quarantine | High |
| Breeder rearing | Weight curves, feed conversion, mortality thresholds | Medium |
| Breeder production | Egg classification, fertility, hatchability | Medium |
| Hatchery | Incubation parameters, ovoscopy, birth rates | High |
| Broiler | Feed conversion, daily gain, uniformity | Medium |

### 3.2 SAP Integration Research

- SAP ECC uses BAPI/RFC for integration
- SAP S/4HANA offers OData REST APIs
- Common integration patterns: IDoc, BAPI, RFC, OData, flat files
- **Decision:** Start with manual file-based import/export. Design adapter for future API/OData.

### 3.3 Approval Workflow Research

- Configurable 1/2/3 level approval is common in enterprise
- Segregation of duties: operator ≠ reviewer ≠ approver
- Correction must preserve original value (regulatory requirement)
- Batch approval for efficiency (by lot, by period)

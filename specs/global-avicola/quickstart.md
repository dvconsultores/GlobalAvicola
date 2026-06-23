# Quickstart — Global Avícola

> **Spec Kit:** `/speckit.plan` Phase 1 output
> **Date:** 2026-06-22

---

## Prerequisites

- Git 2.39+
- Python 3.11+ with `uv`
- Node.js 20+ with `npm`
- Docker + Docker Compose (optional, for containerized dev)
- PostgreSQL 15+ (or use Docker service)

## Quick Start (Docker)

```bash
# 1. Clone and enter
git clone <repo-url> global-avicola
cd global-avicola

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings (especially JWT_SECRET_KEY, DB passwords)

# 3. Start all services
docker compose up -d

# 4. Run migrations
docker compose exec backend alembic upgrade head

# 5. Seed development data
docker compose exec backend python -m app.seeds

# 6. Open the app
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Development (Without Docker)

```bash
# Backend
cd backend
uv sync                    # Install dependencies
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd frontend
npm install                # Install dependencies
npm run dev                # Start Vite dev server on :5173
```

## Database Setup

```bash
# Create database
createdb global_avicola

# Run migrations
cd backend
uv run alembic upgrade head

# Seed data
uv run python -m app.seeds
```

## Available Commands

```bash
make help              # Show all available commands
make install           # Install all dependencies
make dev               # Run full stack in development
make test              # Run all tests
make lint              # Lint all code
make typecheck         # Type check all code
make docker-up         # Start Docker services
make docker-down       # Stop Docker services
```

## Default Login (Development)

| Role | Username | Password |
|---|---|---|
| Super Admin | `admin` | `admin123` |
| Supervisor | `supervisor` | `super123` |
| Operador | `operador` | `oper123` |
| Aprobador | `aprobador` | `aprob123` |
| Analista SAP | `sap_analyst` | `sap123` |
| Auditor | `auditor` | `audit123` |

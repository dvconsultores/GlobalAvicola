.PHONY: help install dev build test lint typecheck clean docker-up docker-down docker-dev docker-dev-down docker-dev-logs docker-dev-rebuild db-migrate db-seed

# ============================================================
# Global Avícola - Makefile
# ============================================================

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ----- Backend -----
backend-install: ## Install backend dependencies
	cd backend && uv sync

backend-dev: ## Run backend in development mode
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

backend-test: ## Run backend tests
	cd backend && uv run pytest -v

backend-lint: ## Lint backend code
	cd backend && uv run ruff check .

backend-typecheck: ## Type check backend
	cd backend && uv run mypy app/

backend-migrate: ## Run database migrations
	cd backend && uv run alembic upgrade head

backend-migrate-new: ## Create new migration (usage: make backend-migrate-new MSG="description")
	cd backend && uv run alembic revision --autogenerate -m "$(MSG)"

backend-telegram-bot: ## Run Telegram bot (requires TELEGRAM_API_KEY and TELEGRAM_MINI_APP_URL)
	cd backend && uv run python -m app.integrations.telegram.bot

# ----- Frontend -----
frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-dev: ## Run frontend in development mode
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

frontend-test: ## Run frontend tests
	cd frontend && npm run test

frontend-lint: ## Lint frontend code
	cd frontend && npm run lint

frontend-typecheck: ## Type check frontend
	cd frontend && npx tsc --noEmit

# ----- Docker -----
docker-up: ## Start all services with Docker Compose
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

docker-build: ## Build Docker images
	docker compose build

# ----- Docker (DESARROLLO local con autoreload de UI) -----
DEV_COMPOSE = docker compose -f docker-compose.yml -f docker-compose.dev.yml

docker-dev: ## Levanta el stack en modo desarrollo (UI con HMR + backend autoreload)
	$(DEV_COMPOSE) up -d --build
	@echo "Frontend dev: http://localhost:5173"

docker-dev-down: ## Detiene el stack de desarrollo
	$(DEV_COMPOSE) down

docker-dev-logs: ## Muestra los logs del stack de desarrollo
	$(DEV_COMPOSE) logs -f

docker-dev-rebuild: ## Reconstruye y reinicia el stack de desarrollo
	$(DEV_COMPOSE) up -d --build --force-recreate

# ----- Full Stack -----
install: backend-install frontend-install ## Install all dependencies

dev: ## Run full stack in development mode
	@echo "Starting backend and frontend..."
	@(make backend-dev & make frontend-dev & wait)

test: backend-test frontend-test ## Run all tests

lint: backend-lint frontend-lint ## Lint all code

typecheck: backend-typecheck frontend-typecheck ## Type check all code

# ----- Database -----
db-seed: ## Seed database with development data
	cd backend && uv run python -m app.seeds

# ----- E2E -----
e2e: ## Run end-to-end tests with Playwright
	cd frontend && npx playwright test

e2e-ui: ## Run Playwright tests with UI
	cd frontend && npx playwright test --ui

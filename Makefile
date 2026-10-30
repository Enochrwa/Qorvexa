.PHONY: help install up down backend-dev frontend-dev worker-dev migrate seed serve gen-api test lint fmt

help:
	@echo "Targets: install up down backend-dev frontend-dev worker-dev migrate seed serve gen-api test lint fmt"

install:
	cd backend && uv sync
	cd frontend && npm ci

up:
	docker compose up -d

down:
	docker compose down

backend-dev:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

worker-dev:
	cd backend && uv run arq app.workers.settings.WorkerSettings

frontend-dev:
	cd frontend && npm run dev

migrate:
	cd backend && uv run alembic upgrade head

seed:  ## genres, admin from SEED_ADMIN_EMAIL/SEED_ADMIN_PASSWORD, sample titles (dev only)
	cd backend && uv run python -m app.cli.seed --sample

serve:  ## production-like: build the web app and serve it from the API on http://localhost:8000
	cd frontend && VITE_API_URL= npm run build
	cd backend && FRONTEND_DIST_DIR=../frontend/dist FRONTEND_URL=http://localhost:8000 uv run uvicorn app.main:app --port 8000

gen-api:  ## regenerate frontend API types from the backend OpenAPI schema
	./scripts/gen-api.sh

test:
	cd backend && uv run pytest
	cd frontend && npm test -- --run

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app
	cd frontend && npm run lint && npm run typecheck && npm run format:check

fmt:
	cd backend && uv run ruff format .
	cd frontend && npm run format

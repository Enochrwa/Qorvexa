.PHONY: help up down backend-dev frontend-dev worker-dev migrate test lint fmt

help:
	@echo "Targets: up down backend-dev frontend-dev worker-dev migrate test lint fmt"

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

test:
	cd backend && uv run pytest
	cd frontend && npm test -- --run

lint:
	cd backend && uv run ruff check . && uv run mypy app
	cd frontend && npm run lint && npm run typecheck

fmt:
	cd backend && uv run ruff format .
	cd frontend && npm run format

.PHONY: help up down logs build test lint migrate revision backend-shell fmt

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n",$$1,$$2}'

up: ## Start the full dev stack
	docker compose up --build

down: ## Stop the stack and remove containers
	docker compose down

logs: ## Tail backend logs
	docker compose logs -f backend

build: ## Build all images
	docker compose build

test: ## Run backend tests
	cd backend && python -m pytest -q

lint: ## Lint backend (ruff) and frontend (next lint)
	cd backend && ruff check app tests
	cd frontend && npm run lint

fmt: ## Auto-fix backend lint
	cd backend && ruff check --fix app tests

migrate: ## Apply DB migrations
	cd backend && alembic upgrade head

revision: ## Autogenerate a migration (use: make revision m="message")
	cd backend && alembic revision --autogenerate -m "$(m)"

backend-shell: ## Open a shell in the backend container
	docker compose exec backend bash

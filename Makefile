.PHONY: help build up down restart logs shell-back shell-db migrate seed test lint format clean reset-dev backup

help:
	@echo ""
	@echo "Personal AI Job Agent — Developer Commands"
	@echo "==========================================="
	@echo "make build        Build all Docker images"
	@echo "make up           Start all services (detached)"
	@echo "make down         Stop all services"
	@echo "make restart      Restart all services"
	@echo "make logs         Tail all service logs"
	@echo "make logs-back    Tail backend logs only"
	@echo "make logs-worker  Tail worker logs only"
	@echo "make shell-back   Open shell in backend container"
	@echo "make shell-db     Open psql shell"
	@echo "make migrate      Run Alembic migrations"
	@echo "make seed         Seed initial data"
	@echo "make test         Run all backend tests"
	@echo "make lint         Run linters"
	@echo "make format       Auto-format code"
	@echo "make reset-dev    Wipe volumes and reinitialize"
	@echo "make backup       Backup database and storage"
	@echo ""

build:
	docker-compose build

up:
	docker-compose up -d
	@echo ""
	@echo "========================================="
	@echo "  Personal AI Job Agent is running!"
	@echo "========================================="
	@echo "  Dashboard:   http://localhost:5173"
	@echo "  API Docs:    http://localhost:8000/docs"
	@echo "  Flower:      http://localhost:5555"
	@echo "  MinIO:       http://localhost:9001"
	@echo "========================================="

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-back:
	docker-compose logs -f backend

logs-worker:
	docker-compose logs -f worker celery-beat

shell-back:
	docker-compose exec backend bash

shell-db:
	docker-compose exec postgres psql -U postgres job_agent

migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	@read -p "Migration name: " name; \
	docker-compose exec backend alembic revision --autogenerate -m "$$name"

seed:
	docker-compose exec backend python -m db.init_db

test:
	docker-compose exec backend pytest tests/ -v --asyncio-mode=auto

test-cov:
	docker-compose exec backend pytest tests/ --cov=. --cov-report=html

lint:
	docker-compose exec backend ruff check .
	docker-compose exec backend mypy . --ignore-missing-imports

format:
	docker-compose exec backend ruff format .

reset-dev:
	@echo "WARNING: This will destroy all data. Press Ctrl+C to cancel."
	@sleep 3
	docker-compose down -v --remove-orphans
	docker-compose up -d postgres redis qdrant minio
	@sleep 8
	docker-compose run --rm backend alembic upgrade head
	docker-compose run --rm backend python -m db.init_db
	docker-compose up -d
	@echo "Dev environment reset complete."

backup:
	./infrastructure/scripts/backup.sh

crawl-test:
	docker-compose exec -T crawler scrapy crawl remoteok_api -L INFO

worker-inspect:
	docker-compose exec worker celery -A celery_app inspect active

trigger-discovery:
	docker-compose exec backend python -c "from workers.celery_app import celery_app; celery_app.send_task('tasks.discovery_tasks.run_discovery')"

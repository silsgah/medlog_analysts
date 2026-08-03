.PHONY: dev test build discover docker-up docker-down help

help:
	@echo "AI Freight Operations & Financial Intelligence Copilot"
	@echo "Commands:"
	@echo "  make dev         - Start local backend and frontend"
	@echo "  make docker-up   - Start all services with Docker Compose"
	@echo "  make docker-down - Stop Docker Compose services"
	@echo "  make test        - Run backend test suite"
	@echo "  make discover    - Run database schema discovery"

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

test:
	cd backend && python -m pytest tests/ -v

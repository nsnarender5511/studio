# Makefile for Git Documentation Project

.PHONY: help install install-backend install-frontend run-backend run-celery run-frontend run-all stop-all

# Default target
default: help

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  help           Display this help message."
	@echo "  install        Install frontend and backend dependencies."
	@echo "  run-backend    Run the backend Flask server (localhost:5001)."
	@echo "  run-celery     Run the Celery worker."
	@echo "  run-frontend   Run the frontend Next.js server (localhost:9002)."
	@echo "  run-all        Run backend, celery, and frontend concurrently (in background)."
	@echo "  stop-all       Attempt to stop background processes (use with caution)."

# Installation
install: install-backend install-frontend

install-backend:
	@echo ">>> Installing backend dependencies..."
	cd backend && poetry install

install-frontend:
	@echo ">>> Installing frontend dependencies using yarn..."
	cd frontend && yarn install

# Running Services
run-backend:
	@echo ">>> Starting backend Flask server on http://localhost:5001 ..."
	cd backend && export FLASK_APP=src.app:create_app && poetry run flask run --debug --host=0.0.0.0 --port=5001

run-celery:
	@echo ">>> Starting Celery worker..."
	cd backend && poetry run celery -A src.app.celery_app worker --loglevel=info

run-frontend:
	@echo ">>> Starting frontend Next.js server on http://localhost:9002 ..."
	cd frontend && yarn dev

# Running All (in background)
# Note: Stopping requires manual process management or more sophisticated tooling
run-all:
	@echo ">>> Starting all services in background..."
	$(MAKE) run-backend & \
	$(MAKE) run-celery & \
	$(MAKE) run-frontend &
	@echo ">>> All services started. Use 'make stop-all' or manual termination (Ctrl+C in respective terminals if run separately, or pkill/kill)."
	@echo "Backend: http://localhost:5001 | Frontend: http://localhost:9002"

# Stopping (Basic Attempt)
# WARNING: This is a basic pkill attempt and might kill unintended processes. Use carefully.
# A more robust solution involves process group IDs or specific PID files.
stop-all:
	@echo ">>> Attempting to stop services (Flask, Celery, Next.js)..."
	-pkill -f "flask run --debug --host=0.0.0.0 --port=5001"
	-pkill -f "celery -A src.app.celery_app worker"
	-pkill -f "next dev --turbopack -p 9002" # Match the actual frontend command
	@echo ">>> Stop commands sent. Verify processes manually."
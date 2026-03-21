# MedNews — Developer Commands
# Requires: Python 3.11+ in venv, Node 20+

VENV = .venv
PYTHON = $(VENV)/Scripts/python
PIP = $(VENV)/Scripts/pip

# ── Setup ──────────────────────────────────────────────────────────────────────

install: install-backend install-frontend

install-backend:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PYTHON) -m playwright install chromium

install-frontend:
	cd frontend && npm install

# ── Development ────────────────────────────────────────────────────────────────

dev-backend:
	$(PYTHON) -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# ── Testing ────────────────────────────────────────────────────────────────────

test:
	$(PYTHON) -m pytest tests/ -v

test-smoke:
	$(PYTHON) -m pytest tests/test_smoke.py -v

test-api:
	$(PYTHON) -m pytest tests/test_api/ -v

test-frontend:
	cd frontend && npm test

# ── Build ──────────────────────────────────────────────────────────────────────

build-frontend:
	cd frontend && npm run build

# ── Database ───────────────────────────────────────────────────────────────────

migrate:
	$(PYTHON) -m alembic upgrade head

migrate-new:
	$(PYTHON) -m alembic revision --autogenerate -m "$(msg)"

# ── Seed ───────────────────────────────────────────────────────────────────────

seed:
	$(PYTHON) -m backend.seeds.sources

# ── Lint ───────────────────────────────────────────────────────────────────────

lint:
	$(PYTHON) -m ruff check backend/

# ── Frontend test (non-interactive, CI-friendly) ────────────────────────────────

frontend-test:
	cd frontend && npm test -- --run

# ── Deploy (Linux only) ────────────────────────────────────────────────────────

deploy:
	@echo "Copying project to /opt/mednews (requires sudo)..."
	sudo rsync -av --exclude='.venv' --exclude='node_modules' --exclude='*.db' \
		./ /opt/mednews/
	sudo bash /opt/mednews/deploy/setup.sh

# ── Utilities ──────────────────────────────────────────────────────────────────

.PHONY: install install-backend install-frontend dev-backend dev-frontend \
        test test-smoke test-api test-frontend frontend-test build-frontend \
        migrate migrate-new seed lint deploy

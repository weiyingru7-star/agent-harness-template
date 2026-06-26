PYTHON ?= python3
API_VENV := apps/api/.venv
API_PYTHON := $(API_VENV)/bin/python
NPM_CACHE := ../../.npm-cache
DOCKER_CONFIG_DIR := .docker

.PHONY: install-api install-web install dev-api dev-web test-api prepare-docker-config prepare-env up down

prepare-env:
	if [ -f ".env" ] && [ ! -f "apps/api/.env" ]; then cp ".env" "apps/api/.env"; fi

install-api:
	$(PYTHON) -m venv --clear $(API_VENV)
	$(API_PYTHON) -m pip install --upgrade pip
	cd apps/api && ../../$(API_PYTHON) -m pip install -e ".[dev]"

install-web:
	cd apps/web && npm install --cache $(NPM_CACHE)

install: install-api install-web

dev-api: prepare-env
	cd apps/api && PYTHONPATH=../..:. ../../$(API_PYTHON) -m uvicorn app.main:app --host $${API_HOST:-127.0.0.1} --port $${API_PORT:-8005}

dev-web:
	cd apps/web && npm run dev -- --port $${WEB_PORT:-3005}

test-api:
	cd apps/api && PYTHONPATH=../..:. ../../$(API_PYTHON) -m pytest

prepare-docker-config:
	mkdir -p $(DOCKER_CONFIG_DIR)
	if [ ! -f "$(DOCKER_CONFIG_DIR)/config.json" ]; then printf '{}\n' > "$(DOCKER_CONFIG_DIR)/config.json"; fi
	if [ ! -e "$(DOCKER_CONFIG_DIR)/cli-plugins" ] && [ -d "$$HOME/.docker/cli-plugins" ]; then ln -s "$$HOME/.docker/cli-plugins" "$(DOCKER_CONFIG_DIR)/cli-plugins"; fi

up: prepare-docker-config
	DOCKER_CONFIG=$(CURDIR)/$(DOCKER_CONFIG_DIR) docker compose up -d postgres redis

down:
	DOCKER_CONFIG=$(CURDIR)/$(DOCKER_CONFIG_DIR) docker compose down

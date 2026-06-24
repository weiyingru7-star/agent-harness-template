PYTHON ?= python3
API_VENV := apps/api/.venv
API_PYTHON := $(API_VENV)/bin/python
API_UVICORN := $(API_VENV)/bin/uvicorn
API_PYTEST := $(API_VENV)/bin/pytest
NPM_CACHE := ../../.npm-cache
DOCKER_CONFIG_DIR := .docker

.PHONY: install-api install-web install dev-api dev-web test-api prepare-docker-config up down

install-api:
	$(PYTHON) -m venv $(API_VENV)
	$(API_PYTHON) -m pip install --upgrade pip
	cd apps/api && ../../$(API_PYTHON) -m pip install -e ".[dev]"

install-web:
	cd apps/web && npm install --cache $(NPM_CACHE)

install: install-api install-web

dev-api:
	cd apps/api && ../../$(API_UVICORN) app.main:app --reload --host $${API_HOST:-0.0.0.0} --port $${API_PORT:-8000}

dev-web:
	cd apps/web && npm run dev -- --port $${WEB_PORT:-3000}

test-api:
	cd apps/api && ../../$(API_PYTEST)

prepare-docker-config:
	mkdir -p $(DOCKER_CONFIG_DIR)
	if [ ! -f "$(DOCKER_CONFIG_DIR)/config.json" ]; then printf '{}\n' > "$(DOCKER_CONFIG_DIR)/config.json"; fi
	if [ ! -e "$(DOCKER_CONFIG_DIR)/cli-plugins" ] && [ -d "$$HOME/.docker/cli-plugins" ]; then ln -s "$$HOME/.docker/cli-plugins" "$(DOCKER_CONFIG_DIR)/cli-plugins"; fi

up: prepare-docker-config
	DOCKER_CONFIG=$(CURDIR)/$(DOCKER_CONFIG_DIR) docker compose up -d postgres redis

down:
	DOCKER_CONFIG=$(CURDIR)/$(DOCKER_CONFIG_DIR) docker compose down

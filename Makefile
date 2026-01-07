.PHONY: help install build test lint format clean package docker all

# Variables
VERSION := $(shell cat VERSION)
PYTHON := python3
NPM := npm
CARGO := cargo

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies
	@echo "Installing dependencies..."
	$(PYTHON) -m pip install -e ".[dev]"
	$(NPM) install
	@echo "✓ Dependencies installed"

build: ## Build all projects
	@./scripts/build.sh release all

build-debug: ## Build all projects in debug mode
	@./scripts/build.sh debug all

build-python: ## Build Python package only
	@./scripts/build.sh release python

build-rust: ## Build Rust package only
	@./scripts/build.sh release rust

build-ts: ## Build TypeScript package only
	@./scripts/build.sh release typescript

test: ## Run all tests
	@./scripts/test.sh all

test-python: ## Run Python tests only
	@./scripts/test.sh python

test-rust: ## Run Rust tests only
	@./scripts/test.sh rust

test-ts: ## Run TypeScript tests only
	@./scripts/test.sh typescript

test-coverage: ## Run tests with coverage
	@./scripts/test.sh all true

lint: ## Lint all code
	@echo "Linting Python..."
	@$(PYTHON) -m black --check src/aicodex tests || true
	@$(PYTHON) -m flake8 src/aicodex tests --max-line-length=100 || true
	@echo "Linting Rust..."
	@$(CARGO) clippy -- -D warnings || true
	@echo "Linting TypeScript..."
	@$(NPM) run lint || true

format: ## Format all code
	@echo "Formatting Python..."
	@$(PYTHON) -m black src/aicodex tests
	@$(PYTHON) -m isort src/aicodex tests
	@echo "Formatting Rust..."
	@$(CARGO) fmt
	@echo "Formatting TypeScript..."
	@$(NPM) run format

clean: ## Clean build artifacts
	@./scripts/clean.sh

package: ## Package all artifacts
	@./scripts/package.sh

docker: ## Build Docker image
	@docker build -t aicodex:$(VERSION) -t aicodex:latest .

docker-run: ## Run Docker container
	@docker run --rm -it aicodex:latest

all: clean install lint test build package ## Run complete build pipeline

.DEFAULT_GOAL := help

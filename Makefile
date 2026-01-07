.PHONY: all clean install lint format test build package verify help

# Variables
PYTHON := python3
PIP := $(PYTHON) -m pip
NPM := npm
CARGO := cargo
VERSION := 0.1.0
DIST_DIR := dist
BUILD_DIR := build

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)AicodeX Build System$(NC)"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

all: clean install lint test build ## Run complete build pipeline

clean: ## Clean build artifacts and caches
	@echo "$(GREEN)Cleaning build artifacts...$(NC)"
	rm -rf $(DIST_DIR) $(BUILD_DIR)
	rm -rf src/aicodex/__pycache__ tests/__pycache__
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf node_modules dist coverage
	rm -rf target
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

install: ## Install all dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@echo "$(YELLOW)Installing Python dependencies...$(NC)"
	$(PIP) install -e .[dev]
	@echo "$(YELLOW)Installing Node.js dependencies...$(NC)"
	$(NPM) install
	@echo "$(GREEN)Dependencies installed!$(NC)"

lint: ## Run linters
	@echo "$(GREEN)Running linters...$(NC)"
	@echo "$(YELLOW)Python linting...$(NC)"
	$(PYTHON) -m flake8 src/aicodex tests
	$(PYTHON) -m mypy src/aicodex
	@echo "$(YELLOW)TypeScript linting...$(NC)"
	$(NPM) run lint
	@echo "$(YELLOW)Rust linting...$(NC)"
	$(CARGO) clippy -- -D warnings
	@echo "$(GREEN)Linting complete!$(NC)"

format: ## Format code
	@echo "$(GREEN)Formatting code...$(NC)"
	@echo "$(YELLOW)Python formatting...$(NC)"
	$(PYTHON) -m black src/aicodex tests
	$(PYTHON) -m isort src/aicodex tests
	@echo "$(YELLOW)TypeScript formatting...$(NC)"
	$(NPM) run format
	@echo "$(YELLOW)Rust formatting...$(NC)"
	$(CARGO) fmt
	@echo "$(GREEN)Formatting complete!$(NC)"

test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	@echo "$(YELLOW)Python tests...$(NC)"
	$(PYTHON) -m pytest
	@echo "$(YELLOW)TypeScript tests...$(NC)"
	$(NPM) test
	@echo "$(YELLOW)Rust tests...$(NC)"
	$(CARGO) test
	@echo "$(GREEN)All tests passed!$(NC)"

build: ## Build all components
	@echo "$(GREEN)Building project...$(NC)"
	@echo "$(YELLOW)Building Python package...$(NC)"
	$(PYTHON) -m build
	@echo "$(YELLOW)Building TypeScript...$(NC)"
	$(NPM) run build
	@echo "$(YELLOW)Building Rust (debug)...$(NC)"
	$(CARGO) build
	@echo "$(GREEN)Build complete!$(NC)"

build-release: ## Build release version
	@echo "$(GREEN)Building release version...$(NC)"
	@echo "$(YELLOW)Building Python package...$(NC)"
	$(PYTHON) -m build
	@echo "$(YELLOW)Building TypeScript...$(NC)"
	$(NPM) run build
	@echo "$(YELLOW)Building Rust (release)...$(NC)"
	$(CARGO) build --release
	@echo "$(GREEN)Release build complete!$(NC)"

package: build-release ## Create distribution packages
	@echo "$(GREEN)Creating distribution packages...$(NC)"
	mkdir -p $(DIST_DIR)
	./scripts/package.sh
	@echo "$(GREEN)Packaging complete!$(NC)"

verify: ## Verify build artifacts
	@echo "$(GREEN)Verifying build artifacts...$(NC)"
	./scripts/verify.sh
	@echo "$(GREEN)Verification complete!$(NC)"

docker-build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t aicodex:$(VERSION) -t aicodex:latest .
	@echo "$(GREEN)Docker image built!$(NC)"

docker-run: ## Run Docker container
	@echo "$(GREEN)Running Docker container...$(NC)"
	docker run -it --rm aicodex:latest

ci: clean install lint test build verify ## Run CI pipeline
	@echo "$(GREEN)CI pipeline complete!$(NC)"

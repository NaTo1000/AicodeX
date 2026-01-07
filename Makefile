# ===========================
# AicodeX Build System
# ===========================
# Multi-language build orchestration for Python, Rust, TypeScript, and Go

.PHONY: all bootstrap clean test build package lint format help
.PHONY: python-test python-build python-lint python-format
.PHONY: rust-test rust-build rust-lint rust-format
.PHONY: ts-test ts-build ts-lint ts-format
.PHONY: go-test go-build go-lint go-format

# Default target
all: lint test build

# ===========================
# Bootstrap
# ===========================

bootstrap: ## Install all dependencies
	@echo "=== Bootstrapping Python ==="
	cd src/python && pip install -e ".[dev]"
	@echo "=== Bootstrapping Rust ==="
	cd src/rust && cargo fetch
	@echo "=== Bootstrapping TypeScript ==="
	cd src/typescript && npm install
	@echo "=== Bootstrapping Go ==="
	cd src/go && go mod download
	@echo "=== Bootstrap complete ==="

# ===========================
# Clean
# ===========================

clean: ## Clean all build artifacts
	@echo "=== Cleaning Python ==="
	cd src/python && rm -rf dist build *.egg-info .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache
	find src/python -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "=== Cleaning Rust ==="
	cd src/rust && cargo clean
	@echo "=== Cleaning TypeScript ==="
	cd src/typescript && rm -rf dist node_modules coverage
	@echo "=== Cleaning Go ==="
	cd src/go && go clean -cache -testcache
	rm -rf src/go/bin
	@echo "=== Clean complete ==="

# ===========================
# Test
# ===========================

test: python-test rust-test ts-test go-test ## Run all tests

python-test: ## Run Python tests
	@echo "=== Running Python tests ==="
	cd src/python && python -m pytest --cov=aicodex --cov-report=term-missing

rust-test: ## Run Rust tests
	@echo "=== Running Rust tests ==="
	cd src/rust && cargo test

ts-test: ## Run TypeScript tests
	@echo "=== Running TypeScript tests ==="
	cd src/typescript && npm test

go-test: ## Run Go tests
	@echo "=== Running Go tests ==="
	cd src/go && go test ./...

# ===========================
# Build
# ===========================

build: python-build rust-build ts-build go-build ## Build all targets

python-build: ## Build Python package
	@echo "=== Building Python ==="
	cd src/python && pip install build && python -m build

rust-build: ## Build Rust binary
	@echo "=== Building Rust ==="
	cd src/rust && cargo build --release

ts-build: ## Build TypeScript
	@echo "=== Building TypeScript ==="
	cd src/typescript && npm run build

go-build: ## Build Go binary
	@echo "=== Building Go ==="
	cd src/go && go build -o bin/aicodex ./cmd/aicodex

# ===========================
# Lint
# ===========================

lint: python-lint rust-lint ts-lint go-lint ## Run all linters

python-lint: ## Run Python linter
	@echo "=== Linting Python ==="
	cd src/python && ruff check aicodex tests && mypy aicodex

rust-lint: ## Run Rust linter
	@echo "=== Linting Rust ==="
	cd src/rust && cargo clippy -- -D warnings

ts-lint: ## Run TypeScript linter
	@echo "=== Linting TypeScript ==="
	cd src/typescript && npm run lint

go-lint: ## Run Go linter
	@echo "=== Linting Go ==="
	cd src/go && go vet ./...

# ===========================
# Format
# ===========================

format: python-format rust-format ts-format go-format ## Format all code

python-format: ## Format Python code
	@echo "=== Formatting Python ==="
	cd src/python && ruff format aicodex tests && ruff check --fix aicodex tests

rust-format: ## Format Rust code
	@echo "=== Formatting Rust ==="
	cd src/rust && cargo fmt

ts-format: ## Format TypeScript code
	@echo "=== Formatting TypeScript ==="
	cd src/typescript && npm run format

go-format: ## Format Go code
	@echo "=== Formatting Go ==="
	cd src/go && gofmt -w .

# ===========================
# Package
# ===========================

package: build ## Create distribution packages
	@echo "=== Creating packages ==="
	mkdir -p artifacts
	@echo "=== Python package ==="
	cp -r src/python/dist/* artifacts/ 2>/dev/null || true
	@echo "=== Rust binary ==="
	cp src/rust/target/release/aicodex artifacts/aicodex-rust 2>/dev/null || true
	@echo "=== TypeScript package ==="
	cd src/typescript && npm pack && mv *.tgz ../../artifacts/
	@echo "=== Go binary ==="
	cp src/go/bin/aicodex artifacts/aicodex-go 2>/dev/null || true
	@echo "=== Packaging complete ==="

# ===========================
# Help
# ===========================

help: ## Show this help message
	@echo "AicodeX Build System"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

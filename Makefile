# AicodeX Makefile
# Unified build commands for Python, Rust, and TypeScript

.PHONY: all clean install lint lint-fix test build package verify help
.PHONY: python-install python-lint python-lint-fix python-test python-build
.PHONY: rust-lint rust-lint-fix rust-test rust-build rust-build-release
.PHONY: ts-install ts-lint ts-lint-fix ts-test ts-build

# Default target
all: install lint test build

#------------------------------------------------------------------------------
# General targets
#------------------------------------------------------------------------------

help:
	@echo "AicodeX Build System"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "General targets:"
	@echo "  all            - Install deps, lint, test, and build all"
	@echo "  clean          - Clean all build artifacts"
	@echo "  install        - Install all dependencies"
	@echo "  lint           - Lint all code"
	@echo "  lint-fix       - Fix linting issues in all code"
	@echo "  test           - Run all tests"
	@echo "  build          - Build all targets (debug)"
	@echo "  build-release  - Build all targets (release)"
	@echo "  package        - Package all artifacts"
	@echo "  verify         - Verify all builds"
	@echo ""
	@echo "Python targets:"
	@echo "  python-install   - Install Python dependencies"
	@echo "  python-lint      - Lint Python code"
	@echo "  python-lint-fix  - Fix Python linting issues"
	@echo "  python-test      - Run Python tests"
	@echo "  python-build     - Build Python package"
	@echo ""
	@echo "Rust targets:"
	@echo "  rust-lint        - Lint Rust code (clippy)"
	@echo "  rust-lint-fix    - Fix Rust linting issues"
	@echo "  rust-test        - Run Rust tests"
	@echo "  rust-build       - Build Rust (debug)"
	@echo "  rust-build-release - Build Rust (release)"
	@echo ""
	@echo "TypeScript targets:"
	@echo "  ts-install       - Install TypeScript dependencies"
	@echo "  ts-lint          - Lint TypeScript code"
	@echo "  ts-lint-fix      - Fix TypeScript linting issues"
	@echo "  ts-test          - Run TypeScript tests"
	@echo "  ts-build         - Build TypeScript"

clean:
	@echo "Cleaning all build artifacts..."
	rm -rf dist/ build/ target/ coverage/ .pytest_cache/ __pycache__/
	rm -rf node_modules/ .venv/ *.egg-info/
	rm -rf htmlcov/ .coverage .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete."

install: python-install ts-install
	@echo "All dependencies installed."

lint: python-lint rust-lint ts-lint
	@echo "All linting complete."

lint-fix: python-lint-fix rust-lint-fix ts-lint-fix
	@echo "All linting fixes applied."

test: python-test rust-test ts-test
	@echo "All tests complete."

build: python-build rust-build ts-build
	@echo "All builds complete (debug)."

build-release: python-build rust-build-release ts-build
	@echo "All builds complete (release)."

package: build-release
	@echo "Packaging artifacts..."
	mkdir -p dist/packages
	@echo "Packaging complete."

verify:
	@echo "Verifying builds..."
	@[ -f target/release/aicodex ] && echo "✓ Rust binary exists" || echo "✗ Rust binary missing"
	@[ -d dist ] && echo "✓ TypeScript dist exists" || echo "✗ TypeScript dist missing"
	@echo "Verification complete."

#------------------------------------------------------------------------------
# Python targets
#------------------------------------------------------------------------------

python-install:
	@echo "Installing Python dependencies..."
	pip install -q -r requirements.txt -r requirements-dev.txt
	pip install -q -e .

python-lint:
	@echo "Linting Python code..."
	ruff check src/python tests/python

python-lint-fix:
	@echo "Fixing Python linting issues..."
	ruff check --fix src/python tests/python
	ruff format src/python tests/python

python-test:
	@echo "Running Python tests..."
	pytest tests/python -v --tb=short

python-test-coverage:
	@echo "Running Python tests with coverage..."
	pytest tests/python -v --cov=src/python --cov-report=html --cov-report=term

python-build:
	@echo "Building Python package..."
	python -m build

#------------------------------------------------------------------------------
# Rust targets
#------------------------------------------------------------------------------

rust-lint:
	@echo "Linting Rust code..."
	cargo clippy --all-targets --all-features -- -D warnings

rust-lint-fix:
	@echo "Fixing Rust linting issues..."
	cargo clippy --fix --allow-dirty --allow-staged

rust-test:
	@echo "Running Rust tests..."
	cargo test --all-features

rust-build:
	@echo "Building Rust (debug)..."
	cargo build

rust-build-release:
	@echo "Building Rust (release)..."
	cargo build --release

rust-check:
	@echo "Checking Rust code..."
	cargo check --all-targets

rust-fmt:
	@echo "Formatting Rust code..."
	cargo fmt

rust-fmt-check:
	@echo "Checking Rust formatting..."
	cargo fmt -- --check

#------------------------------------------------------------------------------
# TypeScript targets
#------------------------------------------------------------------------------

ts-install:
	@echo "Installing TypeScript dependencies..."
	npm ci || npm install

ts-lint:
	@echo "Linting TypeScript code..."
	npm run lint

ts-lint-fix:
	@echo "Fixing TypeScript linting issues..."
	npm run lint:fix

ts-test:
	@echo "Running TypeScript tests..."
	npm run test

ts-test-coverage:
	@echo "Running TypeScript tests with coverage..."
	npm run test:coverage

ts-build:
	@echo "Building TypeScript..."
	npm run build

ts-format:
	@echo "Formatting TypeScript code..."
	npm run format

ts-format-check:
	@echo "Checking TypeScript formatting..."
	npm run format:check

#!/usr/bin/env bash
# Test script for AicodeX multi-language project
set -e

echo "=== Testing AicodeX ==="

# Parse arguments
TARGETS="${1:-all}"
COVERAGE="${2:-false}"

test_python() {
    echo "=== Running Python Tests ==="
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 not found, skipping Python tests"
        return
    fi
    
    python3 -m pip install -e ".[dev]" --quiet
    
    if [ "$COVERAGE" = "true" ]; then
        python3 -m pytest -v --cov=aicodex --cov-report=term --cov-report=html
    else
        python3 -m pytest -v
    fi
    
    echo "✓ Python tests passed"
}

test_rust() {
    echo "=== Running Rust Tests ==="
    if ! command -v cargo &> /dev/null; then
        echo "Cargo not found, skipping Rust tests"
        return
    fi
    
    cargo test --all-features
    echo "✓ Rust tests passed"
}

test_typescript() {
    echo "=== Running TypeScript Tests ==="
    if ! command -v npm &> /dev/null; then
        echo "npm not found, skipping TypeScript tests"
        return
    fi
    
    if [ ! -d "node_modules" ]; then
        npm ci --prefer-offline
    fi
    
    if [ "$COVERAGE" = "true" ]; then
        npm run test:coverage
    else
        npm test
    fi
    
    echo "✓ TypeScript tests passed"
}

# Run tests based on targets
case "$TARGETS" in
    python)
        test_python
        ;;
    rust)
        test_rust
        ;;
    typescript|ts)
        test_typescript
        ;;
    all)
        test_python
        test_rust
        test_typescript
        ;;
    *)
        echo "Unknown target: $TARGETS"
        echo "Usage: $0 [python|rust|typescript|all] [true|false (coverage)]"
        exit 1
        ;;
esac

echo ""
echo "✓ All tests passed!"

#!/usr/bin/env bash
# Clean build artifacts and dependencies
set -e

echo "=== Cleaning AicodeX Build Artifacts ==="

# Clean Python
echo "Cleaning Python artifacts..."
rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ .tox/ .venv/ venv/
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Clean Rust
echo "Cleaning Rust artifacts..."
if [ -f "Cargo.toml" ]; then
    cargo clean 2>/dev/null || true
fi
rm -rf target/

# Clean TypeScript/Node
echo "Cleaning TypeScript/Node artifacts..."
rm -rf node_modules/ dist/ coverage/ *.tsbuildinfo

# Clean misc
echo "Cleaning temporary files..."
rm -rf tmp/ *.log *.tmp

echo "✓ Clean complete!"

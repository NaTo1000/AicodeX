#!/bin/bash
# Verification script for AicodeX build artifacts

set -e

echo "Verifying build artifacts..."

ERRORS=0

# Check Python wheel
if ls dist/*.whl 1> /dev/null 2>&1; then
    echo "✓ Python wheel found"
else
    echo "✗ Python wheel not found"
    ERRORS=$((ERRORS + 1))
fi

# Check TypeScript output
if [ -f "dist/index.js" ]; then
    echo "✓ TypeScript build found"
else
    echo "✗ TypeScript build not found"
    ERRORS=$((ERRORS + 1))
fi

# Check Rust binary
if [ -f "target/release/aicodex" ] || [ -f "target/release/aicodex.exe" ]; then
    echo "✓ Rust binary found"
else
    echo "✗ Rust binary not found"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -eq 0 ]; then
    echo ""
    echo "✓ All verifications passed!"
    exit 0
else
    echo ""
    echo "✗ Verification failed with $ERRORS error(s)"
    exit 1
fi

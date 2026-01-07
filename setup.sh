#!/bin/bash
# Setup script for AicodeX development environment

set -e

echo "========================================"
echo "AicodeX Development Environment Setup"
echo "========================================"
echo ""

# Check if required tools are installed
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ $1 is not installed"
        return 1
    else
        echo "✓ $1 is installed"
        return 0
    fi
}

echo "Checking required tools..."
MISSING_TOOLS=0

check_tool python3 || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_tool node || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_tool npm || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_tool cargo || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_tool make || MISSING_TOOLS=$((MISSING_TOOLS + 1))

echo ""

if [ $MISSING_TOOLS -gt 0 ]; then
    echo "❌ $MISSING_TOOLS required tool(s) missing"
    echo ""
    echo "Please install the missing tools:"
    echo "  - Python 3.8+: https://www.python.org/downloads/"
    echo "  - Node.js 20+: https://nodejs.org/"
    echo "  - Rust: https://rustup.rs/"
    echo "  - Make: Usually pre-installed or available via package manager"
    exit 1
fi

echo "✓ All required tools are installed"
echo ""

# Install dependencies
echo "Installing dependencies..."
make install

echo ""
echo "========================================"
echo "Setup complete! 🎉"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Review the README.md for usage instructions"
echo "  2. Run 'make test' to verify your setup"
echo "  3. Run 'make build' to build the project"
echo "  4. Run 'aicodex' to start the application"
echo ""

#!/usr/bin/env bash
# Build script for AicodeX multi-language project
set -e

VERSION=$(cat VERSION)
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_NUMBER=${BUILD_NUMBER:-"local"}

echo "=== Building AicodeX v${VERSION} ==="
echo "Build Date: ${BUILD_DATE}"
echo "Git Commit: ${GIT_COMMIT}"
echo "Build Number: ${BUILD_NUMBER}"
echo ""

# Parse arguments
BUILD_MODE="${1:-release}"
TARGETS="${2:-all}"

build_python() {
    echo "=== Building Python Package ==="
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 not found, skipping Python build"
        return
    fi
    
    python3 -m pip install --upgrade pip setuptools wheel build
    python3 -m build
    echo "✓ Python build complete"
}

build_rust() {
    echo "=== Building Rust Package ==="
    if ! command -v cargo &> /dev/null; then
        echo "Cargo not found, skipping Rust build"
        return
    fi
    
    if [ "$BUILD_MODE" = "release" ]; then
        cargo build --release
        echo "✓ Rust release build complete"
        echo "Binary: target/release/aicodex"
    else
        cargo build
        echo "✓ Rust debug build complete"
        echo "Binary: target/debug/aicodex"
    fi
}

build_typescript() {
    echo "=== Building TypeScript Package ==="
    if ! command -v npm &> /dev/null; then
        echo "npm not found, skipping TypeScript build"
        return
    fi
    
    npm ci --prefer-offline
    npm run build
    echo "✓ TypeScript build complete"
}

# Build based on targets
case "$TARGETS" in
    python)
        build_python
        ;;
    rust)
        build_rust
        ;;
    typescript|ts)
        build_typescript
        ;;
    all)
        build_python
        build_rust
        build_typescript
        ;;
    *)
        echo "Unknown target: $TARGETS"
        echo "Usage: $0 [debug|release] [python|rust|typescript|all]"
        exit 1
        ;;
esac

echo ""
echo "=== Build Summary ==="
echo "Version: ${VERSION}"
echo "Mode: ${BUILD_MODE}"
echo "Targets: ${TARGETS}"
echo "✓ All builds complete!"

#!/usr/bin/env bash
# Package script for AicodeX multi-language project
set -e

VERSION=$(cat VERSION)
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "=== Packaging AicodeX v${VERSION} ==="

# Create artifacts directory
ARTIFACTS_DIR="artifacts"
mkdir -p "$ARTIFACTS_DIR"

package_python() {
    echo "=== Packaging Python Distribution ==="
    if ! command -v python3 &> /dev/null; then
        echo "Python 3 not found, skipping Python packaging"
        return
    fi
    
    # Ensure wheel is built
    python3 -m build
    
    # Copy to artifacts
    cp dist/*.whl "$ARTIFACTS_DIR/" 2>/dev/null || true
    cp dist/*.tar.gz "$ARTIFACTS_DIR/" 2>/dev/null || true
    
    echo "✓ Python packages created"
}

package_rust() {
    echo "=== Packaging Rust Binary ==="
    if ! command -v cargo &> /dev/null; then
        echo "Cargo not found, skipping Rust packaging"
        return
    fi
    
    # Ensure release build exists
    if [ ! -f "target/release/aicodex" ]; then
        cargo build --release
    fi
    
    # Determine platform
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    # Create archive
    BINARY_NAME="aicodex-${VERSION}-${OS}-${ARCH}"
    mkdir -p "$ARTIFACTS_DIR/$BINARY_NAME"
    cp target/release/aicodex "$ARTIFACTS_DIR/$BINARY_NAME/"
    cp README.md LICENSE "$ARTIFACTS_DIR/$BINARY_NAME/" 2>/dev/null || true
    
    cd "$ARTIFACTS_DIR"
    tar -czf "${BINARY_NAME}.tar.gz" "$BINARY_NAME"
    rm -rf "$BINARY_NAME"
    cd ..
    
    echo "✓ Rust binary packaged: ${BINARY_NAME}.tar.gz"
}

package_typescript() {
    echo "=== Packaging TypeScript Package ==="
    if ! command -v npm &> /dev/null; then
        echo "npm not found, skipping TypeScript packaging"
        return
    fi
    
    # Ensure build exists
    if [ ! -d "dist" ]; then
        npm run build
    fi
    
    # Create tarball
    npm pack
    mv *.tgz "$ARTIFACTS_DIR/" 2>/dev/null || true
    
    echo "✓ TypeScript package created"
}

# Create metadata file
create_metadata() {
    echo "=== Creating Build Metadata ==="
    
    cat > "$ARTIFACTS_DIR/metadata.json" <<EOF
{
  "version": "${VERSION}",
  "build_date": "${BUILD_DATE}",
  "git_commit": "${GIT_COMMIT}",
  "build_number": "${BUILD_NUMBER:-local}",
  "artifacts": []
}
EOF

    # List all artifacts
    echo "Artifacts created:"
    ls -lh "$ARTIFACTS_DIR"
    
    echo "✓ Metadata created"
}

# Package all
package_python
package_rust
package_typescript
create_metadata

echo ""
echo "=== Packaging Complete ==="
echo "Artifacts directory: $ARTIFACTS_DIR"
echo "✓ All packages created!"

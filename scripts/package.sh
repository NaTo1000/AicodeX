#!/bin/bash
# Package script for AicodeX

set -e

echo "Creating distribution packages..."

VERSION="0.1.0"
DIST_DIR="dist"
BUILD_DIR="build"

# Create dist directory if it doesn't exist
mkdir -p "$DIST_DIR"

# Package Python wheel (already built)
echo "Python wheel created in dist/"

# Package TypeScript build
echo "Packaging TypeScript build..."
cd dist
if [ -f index.js ]; then
    tar -czf "../$DIST_DIR/aicodex-typescript-${VERSION}.tar.gz" *.js *.d.ts *.map 2>/dev/null || true
fi
cd ..

# Package Rust binary
echo "Packaging Rust binary..."
if [ -f "target/release/aicodex" ]; then
    tar -czf "$DIST_DIR/aicodex-rust-${VERSION}-$(uname -s)-$(uname -m).tar.gz" -C target/release aicodex
elif [ -f "target/release/aicodex.exe" ]; then
    cd target/release
    zip "../../$DIST_DIR/aicodex-rust-${VERSION}-windows-$(uname -m).zip" aicodex.exe
    cd ../..
fi

echo "Packaging complete! Artifacts in $DIST_DIR/"
ls -lh "$DIST_DIR/"

# Build Documentation

This document provides detailed information about building, testing, and packaging AicodeX across all supported platforms and languages.

## Table of Contents

- [Overview](#overview)
- [Build System](#build-system)
- [Prerequisites](#prerequisites)
- [Building](#building)
- [Testing](#testing)
- [Packaging](#packaging)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [CI/CD](#cicd)
- [Troubleshooting](#troubleshooting)

## Overview

AicodeX is a multi-language project consisting of:

- **Python Package**: Core engine library
- **Rust Binary/Library**: High-performance native components
- **TypeScript Package**: Web and Node.js support

### Supported Platforms

- **Linux**: x86_64, ARM64
- **macOS**: x86_64, ARM64 (Apple Silicon)
- **Windows**: x86_64
- **Web**: WebAssembly (via TypeScript)

### Build Modes

- **Debug** (`O0`): Full debug symbols, no optimizations
- **Release** (`O2/O3`): Optimized, stripped symbols

## Build System

The project uses:

- **Make**: Top-level build orchestration
- **Scripts**: Bash scripts in `scripts/` directory
- **Language Tools**:
  - Python: pip, setuptools, build
  - Rust: Cargo
  - TypeScript: npm, tsc

### Build Pipeline Stages

1. **Clean**: Remove build artifacts
2. **Install**: Install dependencies
3. **Lint/Format**: Code quality checks
4. **Test**: Run test suites
5. **Build**: Compile source code
6. **Package**: Create distributable artifacts
7. **Verify**: Hash/signature verification
8. **Publish**: Upload to registries (CI only)

## Prerequisites

### All Platforms

```bash
# Git
git --version  # 2.0+

# Python
python3 --version  # 3.8+
pip3 --version

# Rust
rustc --version  # 1.75+
cargo --version

# Node.js
node --version  # 18.0+
npm --version   # 9.0+
```

### Platform-Specific

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    curl \
    pkg-config \
    libssl-dev

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### macOS

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 rust node

# Update tools
brew upgrade python rust node
```

#### Windows

```powershell
# Install via Chocolatey
choco install python rust nodejs-lts git

# Or download installers:
# Python: https://www.python.org/downloads/
# Rust: https://rustup.rs/
# Node.js: https://nodejs.org/
```

## Building

### Quick Build

```bash
# Build everything in release mode
make build

# Or using script
./scripts/build.sh release all
```

### Language-Specific Builds

#### Python

```bash
# Using Make
make build-python

# Using script
./scripts/build.sh release python

# Manual build
python3 -m pip install --upgrade build
python3 -m build
```

Output: `dist/aicodex-0.1.0-py3-none-any.whl`, `dist/aicodex-0.1.0.tar.gz`

#### Rust

```bash
# Using Make
make build-rust

# Using script
./scripts/build.sh release rust

# Manual build (release)
cargo build --release

# Manual build (debug)
cargo build
```

Output:
- Release: `target/release/aicodex` (or `.exe` on Windows)
- Debug: `target/debug/aicodex`

#### TypeScript

```bash
# Using Make
make build-ts

# Using script
./scripts/build.sh release typescript

# Manual build
npm ci
npm run build
```

Output: `dist/` directory with compiled JavaScript and type definitions

### Build Options

#### Debug Build

```bash
./scripts/build.sh debug all
```

Features:
- Full debug symbols
- No optimizations
- Faster compilation
- Larger binaries

#### Release Build

```bash
./scripts/build.sh release all
```

Features:
- Optimized code (O2/O3)
- Stripped symbols
- Link-time optimization (Rust)
- Smaller binaries

## Testing

### Running Tests

```bash
# All tests
make test

# With coverage
make test-coverage

# Language-specific
make test-python
make test-rust
make test-ts
```

### Test Scripts

```bash
# All tests
./scripts/test.sh all

# With coverage
./scripts/test.sh all true

# Language-specific
./scripts/test.sh python
./scripts/test.sh rust
./scripts/test.sh typescript
```

### Manual Testing

#### Python

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest -v

# With coverage
pytest -v --cov=aicodex --cov-report=html
```

#### Rust

```bash
# Run all tests
cargo test

# Run specific test
cargo test test_engine_new

# With output
cargo test -- --nocapture
```

#### TypeScript

```bash
# Run tests
npm test

# With coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

### Test Coverage

Coverage reports are generated in:
- Python: `htmlcov/index.html`
- Rust: Terminal output
- TypeScript: `coverage/lcov-report/index.html`

## Packaging

### Create All Packages

```bash
# Using Make
make package

# Using script
./scripts/package.sh
```

Output: `artifacts/` directory containing all packages

### Package Contents

```
artifacts/
├── aicodex-0.1.0-py3-none-any.whl      # Python wheel
├── aicodex-0.1.0.tar.gz                # Python source
├── aicodex-0.1.0-linux-x86_64.tar.gz   # Rust binary (Linux)
├── aicodex-0.1.0.tgz                   # TypeScript package
└── metadata.json                        # Build metadata
```

### Metadata

The `metadata.json` file contains:

```json
{
  "version": "0.1.0",
  "build_date": "2026-01-07T15:10:00Z",
  "git_commit": "abc1234",
  "build_number": "123",
  "artifacts": []
}
```

## Platform-Specific Instructions

### Linux

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y build-essential pkg-config libssl-dev

# Build
make build

# Test
make test

# Package
make package
```

### macOS

```bash
# For Apple Silicon (M1/M2)
# Ensure Rosetta is installed for x86_64 compatibility
softwareupdate --install-rosetta

# Build universal binary (both architectures)
# This is automatic in recent Rust/Cargo versions

# Build
make build

# Test
make test

# Package
make package
```

### Windows

```powershell
# Use Git Bash or WSL for scripts
# Or use Make if available (via Cygwin/MSYS2)

# Build Python
python -m build

# Build Rust
cargo build --release

# Build TypeScript
npm ci
npm run build

# Package (manual)
# Create archives of build artifacts
```

## CI/CD

### GitHub Actions Workflow

The CI/CD pipeline (`.github/workflows/ci.yml`) runs:

1. **Lint**: Code quality checks
   - Python: black, flake8, isort, mypy
   - Rust: rustfmt, clippy
   - TypeScript: eslint, prettier

2. **Test**: Multi-platform testing
   - Matrix: Ubuntu, Windows, macOS
   - Coverage reporting

3. **Build**: Release builds
   - All platforms
   - Artifacts uploaded

4. **Docker**: Container image
   - Multi-stage build
   - Published to GHCR

5. **Release**: Automated releases
   - Triggered on release tags
   - Artifacts attached

### CI Environment Variables

- `BUILD_NUMBER`: Build number from CI
- `GITHUB_TOKEN`: For package publication
- `CARGO_TERM_COLOR`: Colored output
- `RUST_BACKTRACE`: Debug information

## Docker

### Building Docker Image

```bash
# Using Make
make docker

# Using Docker directly
docker build -t aicodex:latest .
```

### Running Docker Container

```bash
# Using Make
make docker-run

# Using Docker directly
docker run --rm -it aicodex:latest
```

### Multi-stage Build

The Dockerfile uses multi-stage builds:

1. **rust-builder**: Compile Rust binary
2. **python-builder**: Build Python wheel
3. **ts-builder**: Compile TypeScript
4. **Final**: Minimal runtime image

### Image Size

Optimizations for smaller images:
- Multi-stage build
- Alpine/slim base images where possible
- Stripped binaries
- No development dependencies

## Troubleshooting

### Build Failures

#### Python Build Issues

```bash
# Update pip and build tools
python3 -m pip install --upgrade pip setuptools wheel build

# Clear cache
pip cache purge

# Reinstall
pip install -e ".[dev]" --force-reinstall --no-cache-dir
```

#### Rust Build Issues

```bash
# Update Rust
rustup update

# Clean build
cargo clean
cargo build --release

# Check for missing dependencies
cargo check
```

#### TypeScript Build Issues

```bash
# Clear node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Clear npm cache
npm cache clean --force
```

### Test Failures

```bash
# Run verbose tests
pytest -vv           # Python
cargo test -- --nocapture  # Rust
npm test -- --verbose      # TypeScript

# Run single test
pytest tests/test_core.py::test_engine_init
cargo test test_engine_new
npm test -- --testNamePattern="Engine"
```

### Permission Issues

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Fix ownership (Linux/macOS)
sudo chown -R $USER:$USER .
```

### Dependency Issues

```bash
# Update all dependencies
pip install --upgrade -e ".[dev]"  # Python
cargo update                        # Rust
npm update                          # TypeScript
```

### Platform-Specific Issues

#### macOS: Command Line Tools

```bash
xcode-select --install
sudo xcode-select --switch /Library/Developer/CommandLineTools
```

#### Windows: Long Path Support

```powershell
# Enable long paths in Git
git config --system core.longpaths true

# Enable in Windows (requires admin)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

#### Linux: Missing Libraries

```bash
# Install common development libraries
sudo apt-get install -y build-essential pkg-config libssl-dev libffi-dev
```

## Performance Optimization

### Build Speed

```bash
# Parallel builds
cargo build --release -j $(nproc)  # Use all CPU cores

# Incremental builds (Rust)
export CARGO_INCREMENTAL=1

# Faster linker (Linux)
sudo apt-get install mold
export RUSTFLAGS="-C link-arg=-fuse-ld=mold"
```

### Binary Size

```bash
# Rust: Strip and optimize
cargo build --release
strip target/release/aicodex

# Or configure in Cargo.toml (already done)
# [profile.release]
# strip = true
# lto = true
```

## Additional Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [Cargo Book](https://doc.rust-lang.org/cargo/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Docker Documentation](https://docs.docker.com/)

## Support

For build issues or questions:
1. Check this documentation
2. Review [CONTRIBUTING.md](CONTRIBUTING.md)
3. Search existing issues
4. Create a new issue with build logs

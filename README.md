# AicodeX

A companion overlay code engine with hotkey enabled and highly customizable features.

[![CI/CD Pipeline](https://github.com/NaTo1000/AicodeX/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/NaTo1000/AicodeX/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

AicodeX is a multi-language project supporting Python, Rust, and TypeScript with the following capabilities:

- **Languages**: Python 3.8+, Rust 1.75+, TypeScript 5.0+
- **Platforms**: Windows, macOS, Linux, Web
- **Build Modes**: Debug, Release, CI
- **Deliverables**: Binaries, installers, Docker images, libraries

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Rust 1.75 or higher
- Node.js 18.0 or higher
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/NaTo1000/AicodeX.git
cd AicodeX

# Install dependencies
make install
```

### Build

```bash
# Build all components (Python, Rust, TypeScript)
make build

# Or use the build script directly
./scripts/build.sh release all

# Build specific components
./scripts/build.sh release python
./scripts/build.sh release rust
./scripts/build.sh release typescript
```

### Test

```bash
# Run all tests
make test

# Run tests with coverage
make test-coverage

# Or use the test script
./scripts/test.sh all
./scripts/test.sh python
./scripts/test.sh rust
./scripts/test.sh typescript
```

### Package

```bash
# Create distribution packages
make package

# Or use the package script
./scripts/package.sh
```

## Project Structure

```
AicodeX/
├── src/
│   ├── aicodex/          # Python package
│   │   ├── __init__.py
│   │   └── core.py
│   ├── lib.rs            # Rust library
│   ├── main.rs           # Rust binary
│   ├── engine.rs         # Rust engine module
│   └── index.ts          # TypeScript entry point
├── tests/                # Test files
│   └── test_core.py      # Python tests
├── scripts/              # Build and utility scripts
│   ├── build.sh
│   ├── test.sh
│   ├── package.sh
│   └── clean.sh
├── .github/
│   └── workflows/
│       └── ci.yml        # CI/CD pipeline
├── Dockerfile            # Docker image definition
├── Makefile              # Build automation
├── pyproject.toml        # Python configuration
├── Cargo.toml            # Rust configuration
├── package.json          # TypeScript/Node.js configuration
├── tsconfig.json         # TypeScript compiler options
├── VERSION               # Version file
└── README.md             # This file
```

## Development

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"
npm install

# Set up pre-commit hooks (optional)
# pip install pre-commit
# pre-commit install
```

### Code Style

- **Python**: Follow PEP 8, use Black for formatting
- **Rust**: Follow Rust style guide, use rustfmt
- **TypeScript**: Use ESLint and Prettier

```bash
# Format code
make format

# Lint code
make lint
```

### Running in Development Mode

```bash
# Python
python -m aicodex

# Rust
cargo run

# TypeScript
npm run build:watch
```

## Docker

Build and run the Docker container:

```bash
# Build Docker image
make docker

# Run container
make docker-run

# Or manually
docker build -t aicodex:latest .
docker run --rm -it aicodex:latest
```

## CI/CD Pipeline

The project includes a comprehensive GitHub Actions CI/CD pipeline that:

1. **Lints** code across all languages
2. **Tests** on multiple platforms (Ubuntu, Windows, macOS)
3. **Builds** release artifacts
4. **Packages** distributable artifacts
5. **Creates** Docker images
6. **Publishes** releases automatically

## Build Targets

### Python Package
- Wheel (`.whl`) and source distribution (`.tar.gz`)
- Available via pip after installation

### Rust Binary
- Native executables for each platform
- Optimized release builds with LTO

### TypeScript Package
- Compiled JavaScript with type definitions
- NPM package tarball

## Configuration

### Build Options
- **Optimization**: O0 (debug), O2, O3 (release)
- **Debug Info**: Full or none
- **Architecture**: x86_64, arm64 (platform dependent)

### Environment Variables
- `BUILD_NUMBER`: Build number for CI (default: "local")
- `CARGO_TERM_COLOR`: Enable colored output for Cargo
- `RUST_BACKTRACE`: Enable Rust backtraces (1 or full)

## Artifacts

Build artifacts are stored in the `artifacts/` directory with the following naming convention:

```
aicodex-<version>-<platform>-<arch>.tar.gz
aicodex-<version>-py3-none-any.whl
aicodex-<version>.tgz
```

Metadata is included in `artifacts/metadata.json`.

## Scripts

### `./scripts/build.sh [mode] [target]`
Build the project.
- Mode: `debug` or `release` (default: `release`)
- Target: `python`, `rust`, `typescript`, or `all` (default: `all`)

### `./scripts/test.sh [target] [coverage]`
Run tests.
- Target: `python`, `rust`, `typescript`, or `all` (default: `all`)
- Coverage: `true` or `false` (default: `false`)

### `./scripts/package.sh`
Create distribution packages for all components.

### `./scripts/clean.sh`
Remove all build artifacts and dependencies.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/NaTo1000/AicodeX).

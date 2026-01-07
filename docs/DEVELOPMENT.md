# AicodeX Development Guide

## Overview

AicodeX is a companion overlay code engine with hotkey-enabled features. This document provides instructions for developers working on the project.

## Project Structure

```
AicodeX/
├── .devcontainer/       # VS Code devcontainer configuration
├── .github/workflows/   # CI/CD workflows
├── docs/                # Documentation
├── scripts/             # Build and utility scripts
├── src/
│   ├── python/          # Python implementation
│   ├── rust/            # Rust implementation
│   ├── typescript/      # TypeScript implementation
│   └── go/              # Go implementation
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules
├── LICENSE              # MIT License
├── Makefile             # Build automation
└── README.md            # Project overview
```

## Prerequisites

- Python ≥ 3.10
- Rust ≥ 1.75
- Node.js ≥ 18
- Go ≥ 1.21
- Make

## Quick Start

### Using Devcontainer (Recommended)

1. Open the project in VS Code
2. Install the "Remote - Containers" extension
3. Click "Reopen in Container" when prompted
4. The container will automatically install all dependencies

### Manual Setup

1. Clone the repository
2. Copy `.env.example` to `.env`
3. Run `make bootstrap` to install all dependencies

## Build Commands

```bash
# Install all dependencies
make bootstrap

# Run all linters
make lint

# Run all tests
make test

# Build all targets
make build

# Create distribution packages
make package

# Clean all build artifacts
make clean

# Show all available commands
make help
```

## Language-Specific Commands

### Python

```bash
make python-test    # Run Python tests
make python-build   # Build Python package
make python-lint    # Lint Python code
make python-format  # Format Python code
```

### Rust

```bash
make rust-test      # Run Rust tests
make rust-build     # Build Rust binary
make rust-lint      # Lint Rust code
make rust-format    # Format Rust code
```

### TypeScript

```bash
make ts-test        # Run TypeScript tests
make ts-build       # Build TypeScript
make ts-lint        # Lint TypeScript code
make ts-format      # Format TypeScript code
```

### Go

```bash
make go-test        # Run Go tests
make go-build       # Build Go binary
make go-lint        # Lint Go code
make go-format      # Format Go code
```

## Testing

All implementations include comprehensive test suites:

- **Python**: pytest with coverage reporting
- **Rust**: cargo test
- **TypeScript**: Jest with coverage
- **Go**: go test with race detection

Run `make test` to execute all test suites.

## CI/CD

The project uses GitHub Actions for continuous integration:

1. **Build & Test**: Runs on every push and pull request
2. **Multi-platform**: Tests on Windows, macOS, and Linux
3. **Security Scan**: CodeQL analysis for security vulnerabilities
4. **Artifact Packaging**: Creates distribution packages on main branch

## Code Style

### Python
- Formatter: `ruff format`
- Linter: `ruff`, `mypy`
- Style guide: PEP 8

### Rust
- Formatter: `rustfmt`
- Linter: `clippy`
- Style guide: Rust official style

### TypeScript
- Formatter: `prettier`
- Linter: `eslint`
- Style guide: TypeScript ESLint recommended

### Go
- Formatter: `gofmt`
- Linter: `go vet`
- Style guide: Effective Go

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run `make lint test` to ensure code quality
5. Commit your changes
6. Push to your fork
7. Open a Pull Request

## License

MIT License - see [LICENSE](../LICENSE) for details.

# AicodeX

A companion overlay code engine with hotkey support and high customizability.

[![CI Pipeline](https://github.com/NaTo1000/AicodeX/actions/workflows/ci.yml/badge.svg)](https://github.com/NaTo1000/AicodeX/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

AicodeX is a multi-language project built with Python, Rust, and TypeScript. It provides a powerful overlay code engine with the following features:

- 🔥 Hotkey support
- ⚙️ Highly customizable
- 🖥️ Cross-platform (Windows, macOS, Linux)
- 🌐 Web support

## Prerequisites

### Required Tools

- **Python**: 3.9 or higher
- **Rust**: Latest stable (via [rustup](https://rustup.rs/))
- **Node.js**: 18.0.0 or higher
- **npm**: 8.0.0 or higher

### Optional Tools

- **Make**: For unified build commands
- **Docker**: For containerized builds

## Quick Start

```bash
# Clone the repository
git clone https://github.com/NaTo1000/AicodeX.git
cd AicodeX

# Install all dependencies
make install

# Run all linters
make lint

# Run all tests
make test

# Build all targets (debug)
make build

# Build all targets (release)
make build-release
```

## Project Structure

```
AicodeX/
├── .github/
│   └── workflows/
│       └── ci.yml          # CI/CD pipeline
├── src/
│   ├── python/             # Python source code
│   ├── rust/               # Rust source code
│   └── typescript/         # TypeScript source code
├── tests/
│   ├── python/             # Python tests
│   ├── rust/               # Rust tests
│   └── typescript/         # TypeScript tests
├── Cargo.toml              # Rust configuration
├── package.json            # Node.js/TypeScript configuration
├── pyproject.toml          # Python configuration
├── Makefile                # Unified build commands
└── README.md               # This file
```

## Build Commands

### Unified Commands (via Make)

| Command | Description |
|---------|-------------|
| `make all` | Install, lint, test, and build |
| `make clean` | Clean all build artifacts |
| `make install` | Install all dependencies |
| `make lint` | Run all linters |
| `make lint-fix` | Fix all linting issues |
| `make test` | Run all tests |
| `make build` | Build all targets (debug) |
| `make build-release` | Build all targets (release) |
| `make package` | Package all artifacts |
| `make verify` | Verify all builds |
| `make help` | Show all available commands |

### Language-Specific Commands

#### Python

```bash
make python-install    # Install Python dependencies
make python-lint       # Lint Python code
make python-test       # Run Python tests
make python-build      # Build Python package
```

#### Rust

```bash
make rust-lint         # Lint Rust code (clippy)
make rust-test         # Run Rust tests
make rust-build        # Build Rust (debug)
make rust-build-release # Build Rust (release)
```

#### TypeScript

```bash
make ts-install        # Install TypeScript dependencies
make ts-lint           # Lint TypeScript code
make ts-test           # Run TypeScript tests
make ts-build          # Build TypeScript
```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration. The pipeline includes:

1. **Setup**: Environment preparation and build type detection
2. **Lint**: Code linting for all languages
3. **Test**: Unit and integration tests with coverage
4. **Build**: Multi-platform builds (Windows, macOS, Linux)
5. **Package**: Artifact packaging with checksums
6. **Security**: Dependency review and security scanning

### Build Types

- **Debug**: Development builds with debugging symbols
- **Release**: Optimized production builds

### Artifacts

The CI pipeline produces the following artifacts:

- Python wheel and source distribution
- Rust binaries for all platforms
- TypeScript compiled JavaScript
- Checksums (SHA256) for all artifacts
- Build metadata

## Development

### Setting Up Development Environment

```bash
# Python
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .

# Rust
cargo build

# TypeScript
npm install
```

### Running Tests

```bash
# All tests
make test

# Python tests with coverage
pytest tests/python -v --cov=src/python

# Rust tests
cargo test --all-features

# TypeScript tests with coverage
npm run test:coverage
```

### Code Style

- **Python**: [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- **Rust**: [Clippy](https://github.com/rust-lang/rust-clippy) for linting, `rustfmt` for formatting
- **TypeScript**: [ESLint](https://eslint.org/) for linting, [Prettier](https://prettier.io/) for formatting

## Configuration

### Build Options

| Option | Debug | Release |
|--------|-------|---------|
| Optimization | O0 | O3 |
| Debug Symbols | Full | None |
| LTO | No | Yes |

### Target Architectures

- x86_64 (AMD64)
- ARM64 (planned)

### Target Platforms

- Linux (x86_64-unknown-linux-gnu)
- Windows (x86_64-pc-windows-msvc)
- macOS (x86_64-apple-darwin)
- Web (wasm32-unknown-unknown) (planned)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For questions and support, please open an issue on GitHub.

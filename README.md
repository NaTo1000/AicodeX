# AicodeX

[![CI/CD Pipeline](https://github.com/NaTo1000/AicodeX/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/NaTo1000/AicodeX/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A companion overlay code engine with hotkey-enabled features and highly customizable interface.

## Overview

**Project Name:** AicodeX  
**Description:** Multi-language code companion with overlay capabilities  
**Languages:** Python, TypeScript, Rust  
**Target Platforms:** Windows, macOS, Linux, Web  
**Build Types:** Debug, Release, CI  
**Deliverables:** Binaries, installers, Docker images

## Features

- 🎯 Hotkey-enabled interface for quick actions
- 🎨 Highly customizable overlay system
- 🚀 Multi-language implementation (Python, TypeScript, Rust)
- 🐳 Docker support for easy deployment
- 🔧 Cross-platform compatibility
- ⚡ High-performance Rust core engine

## Project Structure

```
AicodeX/
├── src/
│   ├── aicodex/          # Python source code
│   ├── typescript/       # TypeScript source code
│   ├── lib.rs            # Rust library
│   └── main.rs           # Rust binary
├── tests/
│   ├── python/           # Python tests
│   └── typescript/       # TypeScript tests
├── scripts/              # Build and packaging scripts
├── .github/workflows/    # CI/CD configuration
├── Makefile              # Build automation
├── Dockerfile            # Docker configuration
├── pyproject.toml        # Python configuration
├── package.json          # Node.js configuration
└── Cargo.toml            # Rust configuration
```

## Setup

### Prerequisites

- Python 3.8+
- Node.js 20+
- Rust (stable)
- Make
- Docker (optional)

### Repository Setup

```bash
# Clone the repository
git clone https://github.com/NaTo1000/AicodeX.git
cd AicodeX

# Install all dependencies
make install
```

### Branches

- `main` - Production-ready code
- `develop` - Development branch
- Feature branches: `feature/*`
- Release branches: `release/*`

## Build Instructions

### Complete Build Pipeline

```bash
# Run the complete pipeline
make all
```

This executes:
1. Clean - Remove build artifacts
2. Install - Install dependencies
3. Lint - Run code linters
4. Test - Run all tests
5. Build - Build all components

### Individual Build Steps

```bash
# Clean build artifacts
make clean

# Install dependencies
make install

# Lint code
make lint

# Format code
make format

# Run tests
make test

# Build debug version
make build

# Build release version
make build-release

# Package for distribution
make package

# Verify build artifacts
make verify

# Run CI pipeline
make ci
```

### Language-Specific Builds

**Python:**
```bash
python3 -m pip install -e .[dev]
python3 -m pytest
python3 -m build
```

**TypeScript:**
```bash
npm install
npm run build
npm test
npm run lint
```

**Rust:**
```bash
cargo build --release
cargo test
cargo clippy
```

## Docker

### Build Docker Image

```bash
# Using Makefile
make docker-build

# Using docker directly
docker build -t aicodex:latest .
```

### Run Docker Container

```bash
# Using Makefile
make docker-run

# Using docker directly
docker run -it --rm aicodex:latest
```

## Development

### Linting and Formatting

The project uses multiple linters and formatters:

- **Python:** Black, isort, flake8, mypy
- **TypeScript:** ESLint, Prettier
- **Rust:** rustfmt, clippy

```bash
# Format all code
make format

# Lint all code
make lint
```

### Testing

```bash
# Run all tests
make test

# Python tests only
python3 -m pytest

# TypeScript tests only
npm test

# Rust tests only
cargo test
```

### Environment Variables

CI/CD secrets required:
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password
- `GITHUB_TOKEN` - GitHub token (auto-provided)

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

1. **Lint** - Code quality checks
2. **Test** - Run tests on multiple platforms and Python versions
3. **Build** - Create platform-specific artifacts
4. **Docker** - Build and push Docker images
5. **Release** - Create releases with artifacts

### Supported Platforms

- Ubuntu (Linux)
- Windows
- macOS

### Artifacts

Build artifacts follow the naming convention:
- `aicodex-{version}-{platform}-{architecture}.tar.gz`
- `aicodex-{version}-windows-{architecture}.zip`

## Usage

### Running the Application

```bash
# From source (Python)
aicodex

# From Docker
docker run -it aicodex:latest

# From compiled binary (Rust)
./target/release/aicodex
```

### Configuration

Create a configuration file at `~/.aicodex/config.json`:

```json
{
  "hotkeys": {
    "ctrl+shift+a": "action1",
    "ctrl+shift+b": "action2"
  },
  "theme": "dark",
  "opacity": 0.9
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**NaTo1000**

## Acknowledgments

- Built with modern development practices
- Comprehensive CI/CD pipeline
- Multi-language support for flexibility
- Docker support for easy deployment

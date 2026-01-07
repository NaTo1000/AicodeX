# Build System Documentation

## Overview

AicodeX uses a comprehensive build system that supports multiple programming languages and build targets. This document describes the build architecture and how to use it.

## Build Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Build Pipeline                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Clean         → Remove build artifacts                   │
│  2. Install       → Install dependencies                     │
│  3. Lint/Format   → Code quality checks                      │
│  4. Test          → Run unit tests                          │
│  5. Build         → Compile all components                   │
│  6. Package       → Create distribution packages             │
│  7. Verify        → Verify build artifacts                   │
│  8. Publish       → Deploy (CI/CD only)                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Language-Specific Build Details

### Python
- **Package Manager**: pip
- **Build Tool**: setuptools, build
- **Test Framework**: pytest
- **Linters**: flake8, mypy, black, isort
- **Output**: Wheel file in `dist/`

### TypeScript
- **Package Manager**: npm
- **Build Tool**: tsc
- **Test Framework**: jest
- **Linters**: ESLint, Prettier
- **Output**: JavaScript files in `dist/`

### Rust
- **Package Manager**: cargo
- **Build Tool**: cargo
- **Test Framework**: cargo test
- **Linters**: clippy, rustfmt
- **Output**: Binary in `target/release/`

## Build Targets

### Development Build
```bash
make build
```
- Debug symbols included
- No optimizations
- Fast compilation

### Release Build
```bash
make build-release
```
- Optimized
- Stripped binaries
- Production-ready

### CI Build
```bash
make ci
```
- Full pipeline with verification

## Verification

### Automated Verification
```bash
make verify
```

Checks:
- ✓ Python wheel exists
- ✓ TypeScript build exists
- ✓ Rust binary exists

## Troubleshooting

### Common Issues

**1. Dependency Installation Fails**
```bash
make clean
make install
```

**2. Tests Fail**
```bash
python3 -m pytest -v
npm test
cargo test
```

## Best Practices

1. Always run tests before committing: `make test`
2. Format code before committing: `make format`
3. Verify builds before pushing: `make ci`

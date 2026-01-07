# Contributing to AicodeX

Thank you for your interest in contributing to AicodeX! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Commit Messages](#commit-messages)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please be respectful and considerate in all interactions.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/AicodeX.git`
3. Create a feature branch: `git checkout -b feature/my-feature`
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8+
- Rust 1.75+
- Node.js 18+
- Git

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/NaTo1000/AicodeX.git
cd AicodeX

# Install dependencies
make install

# Verify installation
make test
```

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Urgent fixes for production

## Coding Standards

### Python

- Follow PEP 8 style guide
- Use type hints where applicable
- Maximum line length: 100 characters
- Use Black for code formatting
- Use isort for import sorting

```bash
# Format Python code
black src/aicodex tests
isort src/aicodex tests

# Lint Python code
flake8 src/aicodex tests --max-line-length=100
mypy src/aicodex
```

### Rust

- Follow the Rust style guide
- Use rustfmt for formatting
- Use clippy for linting
- Write documentation for public APIs

```bash
# Format Rust code
cargo fmt

# Lint Rust code
cargo clippy -- -D warnings
```

### TypeScript

- Follow the TypeScript style guide
- Use ESLint for linting
- Use Prettier for formatting
- Maximum line length: 100 characters

```bash
# Format TypeScript code
npm run format

# Lint TypeScript code
npm run lint
```

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-coverage

# Run language-specific tests
make test-python
make test-rust
make test-ts
```

### Writing Tests

#### Python Tests

```python
# tests/test_example.py
import pytest
from aicodex import Engine

def test_example():
    """Test description."""
    engine = Engine()
    assert engine is not None
```

#### Rust Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_example() {
        let engine = Engine::new();
        assert!(engine.is_ready());
    }
}
```

#### TypeScript Tests

```typescript
// src/example.test.ts
import { Engine } from './index';

describe('Engine', () => {
  it('should create instance', () => {
    const engine = new Engine();
    expect(engine).toBeDefined();
  });
});
```

## Pull Request Process

1. **Update your branch**: Ensure your branch is up-to-date with `develop`
   ```bash
   git checkout develop
   git pull origin develop
   git checkout feature/my-feature
   git rebase develop
   ```

2. **Run tests**: Ensure all tests pass
   ```bash
   make test
   ```

3. **Lint your code**: Fix any linting issues
   ```bash
   make lint
   ```

4. **Update documentation**: Update relevant documentation

5. **Create pull request**:
   - Use a clear, descriptive title
   - Reference related issues
   - Describe your changes in detail
   - Include screenshots for UI changes

6. **Code review**: Address reviewer feedback

7. **Merge**: Once approved, your PR will be merged

## Commit Messages

Use conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

### Examples

```
feat(python): add hotkey configuration support

Implement hotkey configuration in the Python engine to allow
users to customize keyboard shortcuts.

Closes #123
```

```
fix(rust): resolve memory leak in engine

Fixed a memory leak that occurred when repeatedly starting
and stopping the engine.

Fixes #456
```

## Development Workflow

### Daily Development

```bash
# Start development
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# Make changes and test frequently
make test

# Format and lint
make format
make lint

# Commit changes
git add .
git commit -m "feat: implement new feature"

# Push changes
git push origin feature/my-feature
```

### Before Submitting PR

```bash
# Ensure everything is up-to-date
git checkout develop
git pull origin develop
git checkout feature/my-feature
git rebase develop

# Run full test suite
make clean
make install
make test
make build

# Fix any issues
make lint
make format
```

## Project-Specific Guidelines

### Adding Dependencies

- **Python**: Add to `pyproject.toml` dependencies
- **Rust**: Add to `Cargo.toml` dependencies
- **TypeScript**: Add to `package.json` dependencies

Always specify version ranges appropriately.

### Adding New Features

1. Create tests first (TDD approach)
2. Implement the feature
3. Update documentation
4. Add examples if applicable
5. Update CHANGELOG.md

### Reporting Bugs

Create an issue with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, versions)
- Logs or error messages

## Questions?

If you have questions, please:
1. Check existing documentation
2. Search existing issues
3. Create a new issue with the "question" label

Thank you for contributing to AicodeX!

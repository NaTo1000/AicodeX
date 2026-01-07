# Contributing to AicodeX

Thank you for your interest in contributing to AicodeX! This document provides guidelines for contributing to the project.

## Code of Conduct

Please be respectful and constructive in all interactions with the project and community.

## How to Contribute

### Reporting Bugs

- Check if the bug has already been reported in Issues
- Use the bug report template
- Include detailed steps to reproduce
- Include system information and versions

### Suggesting Features

- Check if the feature has already been suggested
- Use the feature request template
- Explain the use case and benefits
- Be open to discussion and alternatives

### Pull Requests

1. Fork the repository
2. Create a feature branch from `develop`
3. Make your changes following our coding standards
4. Write or update tests as needed
5. Run the full test suite: `make test`
6. Run linters: `make lint`
7. Update documentation if needed
8. Submit a pull request to `develop`

## Development Setup

```bash
git clone https://github.com/NaTo1000/AicodeX.git
cd AicodeX
make install
```

## Coding Standards

### Python
- Follow PEP 8 style guide
- Use type hints
- Maximum line length: 100 characters
- Use Black for formatting
- Use isort for import sorting

### TypeScript
- Follow the project's ESLint configuration
- Use TypeScript strict mode
- Document public APIs with JSDoc
- Use Prettier for formatting

### Rust
- Follow Rust standard style
- Use rustfmt for formatting
- Run clippy before submitting
- Add tests for new functionality

## Testing

All code changes should include appropriate tests:

```bash
# Run all tests
make test

# Run specific language tests
python3 -m pytest
npm test
cargo test
```

## Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense
- Keep the first line under 50 characters
- Add detailed description if needed

Example:
```
Add hotkey configuration support

- Implement configuration file parsing
- Add validation for hotkey combinations
- Update documentation with examples
```

## Review Process

1. All PRs require at least one review
2. CI checks must pass
3. Code coverage should not decrease
4. Documentation must be updated

## Questions?

Feel free to open an issue for questions or join our discussions.

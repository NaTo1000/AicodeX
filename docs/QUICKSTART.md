# Quick Start Guide

## Installation

### Prerequisites

Ensure you have the following installed:
- Python 3.8 or higher
- Node.js 20 or higher
- Rust (stable)
- Make
- Git

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/NaTo1000/AicodeX.git
cd AicodeX

# Run automated setup
./setup.sh
```

The setup script will:
- Check for required tools
- Install all dependencies (Python, Node.js, Rust)
- Verify the installation

## Basic Usage

### Running AicodeX

**From Python:**
```bash
aicodex
```

**From Rust:**
```bash
cargo run
```

**From Docker:**
```bash
docker build -t aicodex .
docker run -it aicodex
```

### Configuration

1. Copy the example configuration:
```bash
cp config.example.json ~/.aicodex/config.json
```

2. Edit the configuration:
```bash
nano ~/.aicodex/config.json
```

3. Configure hotkeys, theme, and other settings as needed.

## Development

### Building the Project

```bash
# Build everything (debug mode)
make build

# Build for release
make build-release
```

### Running Tests

```bash
# Run all tests
make test

# Run specific language tests
python3 -m pytest          # Python only
npm test                   # TypeScript only
cargo test                 # Rust only
```

### Code Formatting

```bash
# Format all code
make format

# Lint all code
make lint
```

## Common Tasks

### Clean Build Artifacts

```bash
make clean
```

### Install Dependencies

```bash
make install
```

### Run CI Pipeline Locally

```bash
make ci
```

### Create Distribution Packages

```bash
make package
```

### Build Docker Image

```bash
make docker-build
```

## Next Steps

- Read the [full documentation](README.md)
- Check the [build documentation](docs/BUILD.md)
- Review [contributing guidelines](CONTRIBUTING.md)
- Explore the [example configuration](config.example.json)

## Troubleshooting

**Build fails?**
```bash
make clean
./setup.sh
```

**Tests fail?**
```bash
make test
# Check individual test suites for specific failures
```

**Need help?**
- Open an issue on GitHub
- Check the documentation in the `docs/` directory
- Review the SECURITY.md file for security concerns

## Example Workflow

```bash
# 1. Clone and setup
git clone https://github.com/NaTo1000/AicodeX.git
cd AicodeX
./setup.sh

# 2. Make changes
# ... edit files ...

# 3. Test changes
make test

# 4. Format code
make format

# 5. Build
make build

# 6. Run
aicodex
```

## Platform-Specific Notes

### Linux
- All features supported
- Use package manager for system dependencies

### macOS
- All features supported
- May need to grant permissions for hotkeys

### Windows
- Use WSL2 or native Windows tools
- Some scripts may need adjustments

## Docker

### Quick Docker Setup

```bash
# Build
docker build -t aicodex:latest .

# Run
docker run -it --rm aicodex:latest

# Run with volume
docker run -it --rm -v $(pwd):/app aicodex:latest
```

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/NaTo1000/AicodeX/issues
- GitHub Discussions: https://github.com/NaTo1000/AicodeX/discussions

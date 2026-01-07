# AicodeX

its a companion overlay code engine with a fair few really awesome features its hot key enabled and highly customisable

## Overview
- **Name:** AicodeX  
- **Description:** Companion overlay code engine with hotkeys and deep customization.  
- **Languages:** Python, Rust, TypeScript  
- **Targets:** Windows, macOS, Linux, Web  
- **Build profiles:** Debug, Release, CI  
- **Deliverables:** CLI binaries, installers, Docker images

## Repository and setup
- Branches: `main` (stable) and `develop` (integration).
- Dependencies managed with language-native tools and lockfiles:
  - Python: `python -m venv .venv && pip install -r requirements.txt` (track with `requirements.txt`/`poetry.lock`).
  - Rust: `cargo fetch` / `cargo build` (track with `Cargo.lock`).
  - TypeScript: `npm ci` (track with `package-lock.json`).
- Configure CI secrets for signing, registry tokens, and release publishing.

## Build and release plan
1. **Clean:** remove build artifacts (`build/`, `dist/`, `target/`, `node_modules/.cache`).
2. **Install:** restore Python, Rust, and TypeScript dependencies using their lockfiles.
3. **Lint/Format:** `ruff`/`black` for Python, `cargo fmt`/`cargo clippy` for Rust, `eslint`/`prettier` for TypeScript.
4. **Tests:** `pytest`, `cargo test`, and `npm test` (or framework-specific test runner).
5. **Build:** create Debug/Release/CI outputs (`cargo build`, `npm run build`, Python packaging if applicable).
6. **Package:** produce binaries/installers and Docker images.
7. **Verify:** smoke test packaged artifacts on all targets.
8. **Publish:** upload artifacts following the naming scheme `aicodex-<version>-<arch>`.

## Artifacts
- `aicodex-<version>-<arch>.tar.gz` / `.zip` for binaries
- Platform installers (Windows/MSI, macOS/DMG, Linux packages)
- `aicodex-<version>-<arch>.docker` (Docker image tag)

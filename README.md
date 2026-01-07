# AicodeX
AicodeX is a companion overlay code engine with hotkey-driven, highly customizable workflows.

## Project Overview
- **Name:** AicodeX
- **Purpose:** Provide a cross-platform, hotkey-enabled overlay for rapid coding assistance.
- **Languages:** Python (automation/integration), Rust (performance-critical components), TypeScript (UI/overlay).
- **Targets:** Windows, macOS, Linux, Web.
- **Build Variants:** Debug, Release, CI.
- **Deliverables:** CLI binaries, shared libraries, installer bundles, Docker images.

## Setup
- **Repository:** Git (`main` stable, `develop` integration).
- **Toolchains:** Python ≥ 3.11 with `pip`, Rust stable with `cargo`/`rustup`, Node.js ≥ 18 with `npm`. Lockfiles (`requirements.txt` or `poetry.lock`, `Cargo.lock`, `package-lock.json`) ensure reproducibility.
- **Environment:** Configure CI secrets for publishing/signing; use a local `.env` (never committed) for development secrets.
- **Commands:**
  - Python: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
  - Rust targets (add as needed): `rustup target add x86_64-unknown-linux-gnu`, `rustup target add x86_64-pc-windows-gnu`, `rustup target add x86_64-apple-darwin`, `rustup target add wasm32-unknown-unknown`; then `cargo fetch`
  - TypeScript: `npm ci`
  - Optional: `make` targets may wrap the steps below when present.

## Configuration
- **Targets:** `BUILD_TARGET=app|lib|cli` (overlay app, reusable library, or CLI).
- **Optimization:** `PROFILE=debug|release|ci` mapping to O0/O2/O3 and deterministic CI flags.
- **Debug Info:** `DEBUG_SYMBOLS=full|none`.
- **Architecture:** `ARCH=x86_64|arm64`.
- **Features:** `FEATURES="telemetry,wasm"` etc. (Rust `--features`, TS feature flags, Python env toggles).
- **Environment Flags:** `RUSTFLAGS`, `NODE_ENV=production`, `PYTHONWARNINGS`, `AICODEX_CONFIG` path.

## Pipeline
1. **Clean:** `make clean` or:
   - Unix: `cargo clean && npm run clean --if-present && if [ -f .venv/pyvenv.cfg ] && [ -d .venv/bin ]; then rm -rf .venv; fi`
   - Windows: `cargo clean && npm run clean --if-present && if exist .venv\\pyvenv.cfg ( if exist .venv\\Scripts ( rmdir /s /q .venv ) )`
   (only remove a project-local virtualenv; detection uses the activation script folder and `pyvenv.cfg`; optionally wrap per-OS commands in dedicated cleanup scripts)
2. **Install:** Python (`pip install -r requirements.txt`), Rust (`cargo fetch`), TypeScript (`npm ci`)
3. **Lint/Format:** `ruff check .`, `cargo fmt --check && cargo clippy -- -D warnings`, `npm run lint && npm run format:check`
4. **Tests:** `pytest`, `cargo test --all-targets`, `npm test` (local default parallel); `npm test -- --runInBand` only in CI when memory constrained
5. **Build:** `cargo build --profile $PROFILE`, `npm run build`, optional `cargo build --target wasm32-unknown-unknown` for Web
6. **Package:** `cargo build --release --target <triple>`, archive installers per OS, `npm run bundle`, `docker build -t org/aicodex:$TAG .`; generate `sha256sum` for all artifacts
7. **Verify:** smoke tests on built artifacts, `pytest -m integration`, `npm run test:e2e` (headless) when available
8. **Publish:** sign artifacts (GPG/cosign) using CI secrets, push Docker images, upload release binaries/installers, publish libraries to registries as applicable
9. **Cleanup:** remove `dist/`, `build/`, `target/`, and temporary caches to keep CI lean

## Security & Compliance
- Enforce dependency scanning (`pip-audit`, `cargo audit`, `npm audit`) in CI.
- Produce SBOMs when packaging (`syft` or ecosystem equivalents).
- Keep secrets in CI-managed stores; never commit them. Validate licenses of third-party dependencies.

## Testing
- **Types:** Unit, integration, and UI/overlay checks (headless where possible).
- **Environments:** Local dev parity with CI; optional staging with feature flags.
- **Criteria:** All required suites green; maintain agreed coverage thresholds for Python, Rust, and TS components.

## Delivery
- **Artifacts:** CLI binaries and shared libraries (`target/<triple>/release`), installer bundles per OS (`dist/`), web bundles (`build/`), Docker images.
- **Metadata:** Include version, commit, build date, and checksums with every artifact.
- **Distribution:** Upload release assets, publish containers to registries, and keep rollback-ready previous versions. Sign all distributed artifacts.

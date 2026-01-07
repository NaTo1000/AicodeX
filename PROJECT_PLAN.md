# AicodeX Delivery Blueprint

This document instantiates the provided problem statement for the AicodeX project to guide build, test, security, and release activities.

## 1) Project, Scope & Constraints
- **Project**: AicodeX – companion overlay code engine (hotkey-enabled, highly customizable).
- **Purpose / Success criteria**: Deliver a cross-platform, low-latency overlay that can be triggered by hotkeys, render assistive code panels, and remain secure by default. Success is measured by (a) reproducible builds, (b) green CI across all stacks, (c) packaged artifacts for each target platform, and (d) documented rollback and support playbooks.
- **Assumptions & constraints**: Open-source dependencies must comply with MIT-compatible licenses; SBOM required for every release; no secrets in CI; rely on pinned toolchains via lockfiles.
- **Non-functional requirements**: Security first (least-privilege CI, dependency scanning), predictable performance (overlay render under 50ms on supported hardware), accessibility (keyboard navigation + screen reader labels), localization-ready strings, reproducible builds.

## 2) Repository, Environment & Tooling
- **VCS & branches**: Git; main/develop/feature/*; protected main.
- **Stacks (per component)**: Python (automation/services), Rust (performance-critical overlay pieces), TypeScript (UI & tooling), Go (CLI/aux services).
- **Target platforms**: Windows, macOS, Linux (desktop); Web bundle for embedded panels.
- **Build types**: Debug (dev), Release (prod), CI (pull_request), Nightly (schedule).
- **Deliverables**: Binaries/CLIs (Rust/Go), npm FE bundle, Python wheel, Docker images, docs.
- **Environments**: Local dev, CI (GitHub Actions), staging; sanitized env vars only.
- **Tooling**: Build: make/scripts; Python: uv/pip + pyproject; Rust: cargo; TS: npm/yarn + tsconfig; Go: go modules; Docker multi-stage for release images.
- **Reproducibility**: Pin via lockfiles (Cargo.lock, package-lock.json, uv.lock/requirements.txt, go.sum); record tool versions; prefer containerized runners.

## 3) Architecture & Build Configuration
- **Modules**: UI overlay (TS), core engine (Rust), automation/SDK (Python), utilities/CLI (Go).
- **Artifacts**: Primary – overlay bundle, core binary; Optional – docs, samples, benchmarks.
- **Build params**: Optimize Release with debug info: minimal on prod, full on Debug; targets x86_64/arm64.
- **Feature flags**: Enable performance tracing & telemetry guardrails; disable experimental features by default.
- **Resource constraints**: CI time-box per job; keep memory within default GitHub runners.
- **Versioning & signing**: Semver from git tags; sign release artifacts (GPG) when available; embed commit hash + timestamp in binaries.

## 4) Comprehensive Pipeline (CI/CD Steps)
0. **Preflight**: Verify toolchains and caches; lint workflow files for pinned actions.
1. **Clean**: Remove build artifacts and caches per language.
2. **Restore/Install**: Install deps using lockfiles; validate checksums.
3. **Static quality**: Run eslint/prettier, black/ruff, cargo fmt/clippy, gofmt/golangci-lint.
4. **Security**: Dependency scan (GH advisories), secret scanning, license/SBOM generation (CycloneDX/SPDX).
5. **Tests**: Unit + integration; E2E where applicable; collect coverage (lcov/coverage.xml); enforce thresholds.
6. **Build**: Compile per language; parallelize by module; hash artifacts for integrity.
7. **Packaging**: Produce installers/archives, Docker images, FE bundles; include LICENSE/README/CHANGELOG.
8. **Verification**: Sanity checks, permission checks, size thresholds, signature verification.
9. **Publish/Deploy**: Push to registry/artifact store; tag release; update notes/changelog.
10. **Post-process**: Cleanup caches; finalize SBOM and provenance metadata.

## 5) Security, Compliance & Governance
- Least-privilege workflow permissions; short-lived tokens; no plaintext secrets.
- SBOM required per build; allow-list licenses; audit trail via workflow logs and attestation.
- Code signing policy for release artifacts; verify signatures before publish.

## 6) Testing Strategy & Validation
- **Matrix**: Unit/integration/E2E; cross-OS (win/mac/linux); hardware limits noted.
- **Quality gates**: Coverage thresholds; defect density tracked; flaky-test budget documented.
- **Determinism**: Reproducible builds with pinned deps; artifact hashing.

## 7) Artifacts, Distribution & Rollback
- **Catalog**: Rust/Go binaries, Python wheel, npm bundle, Docker images, docs.
- **Metadata**: Version, commit, build number, date, platform.
- **Distribution**: Internal registry/CDN; GitHub Releases; file server as fallback.
- **Rollback**: Revert to last known-good tag; retain artifacts; hotfix branch policy.

## 8) Observability & Metrics
- Track build duration, cache hits, success rate; failure taxonomy for CI.
- Telemetry for overlay performance; quality signals (lint/test pass rates, coverage trends, SBOM completeness).

## 9) Troubleshooting Guide
- Common failures: dependency resolution, cache corruption, flaky UI tests, Docker pull limits.
- Logs to capture: workflow artifacts, test outputs, build logs, SBOM/scan reports.
- Quick fixes: clear caches, rerun with --locked/--frozen, re-pin tool versions.

## 10) Customization, Extensibility & Onboarding
- Adding languages/targets: extend make/scripts and workflows; add lint/test/build blocks + lockfiles.
- Onboarding: documented CI commands, lint rules, env setup; ensure hotkeys/localization guidelines.

## 11) Quick Start Template
- **Project**: AicodeX  
- **Stack**: Python, Rust, TypeScript, Go  
- **CI**: GitHub Actions (ci.yml/ci.yaml)  
- **Planned commands** (to be added in future iterations): `./scripts/prep.sh`, `./scripts/build.sh`, `./scripts/test.sh`, `./scripts/package.sh`  
- **Signing**: GPG/signing pipeline when keys available  
- **SBOM**: CycloneDX/SPDX generation in CI

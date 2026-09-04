# AicodeX

**AicodeX** is a companion overlay code engine with a fair few really awesome features. It's hotkey-enabled and highly customizable, designed to enhance your coding experience with quick access to code snippets, actions, and utilities.

## Features

- 🎯 **Overlay Interface** - Semi-transparent overlay window that stays on top of all applications
- ⌨️ **Global Hotkeys** - Quick access to features from anywhere on your system
- 📝 **Code Snippets** - Pre-defined code templates for faster development
- ⚡ **Quick Actions** - One-click access to common development tasks
- 🎨 **Highly Customizable** - Configure hotkeys, appearance, and behavior
- 🔧 **HandBrake Integration** - Check and download the latest HandBrake version
- 🖥️ **Windows Optimized** - Built specifically for Windows development workflows

## Edition 2 — Multi-Model Orchestration & Secrets Vault

Edition 2 layers an optional, config-driven multi-model orchestration system on top of the AicodeX core. A roster of specialized model roles is sequenced by the **CHAiMERA.ConductorX** orchestration system, which creates the *symphony of structure and code accuracy* for the user-desired output.

### Model Roles

Each role binds a model to a mission and can be toggled on or off independently via its `enabled` flag in `config/edition2_settings.json`:

| Role | Model | Mission |
|------|-------|---------|
| `skeleton_architect` | **Claude** | Skeleton structure & overall code-base architecture |
| `formation_planner` | **Gemini** | Formation system setup & TODO planning |
| `base_coder` | **Cursor** | Write the base code structure |
| `error_patcher` | **Kimi 3** | Code-base error checks & patching refinements |
| `research_dev` | **Mistral** | R&D of errors/queries from internal build metrics; supply data feeds & algorithms for requirement rectifications & enhanced performance |
| `security_netops` | **Grok** | Security system, network management & port-allocation structure |
| `spec_logger` | **ChatGPT** | Full-spec logging & advanced workflow mapping; job-building alignment, requirements/regulations & error prevention |

### Optional Secrets Vault

Edition 2 includes an **optional, local-only secrets vault** (`edition2/vault.py`) for the per-model job credentials. Config references secrets indirectly with `$VAULT:key` entries so no secret value ever lives in version-controlled configuration.

- Stored as a single JSON file with owner-only (`0600`) permissions, auto-repaired on write.
- **Local-only:** the vault warns if placed in a synced/shared location and must never be committed or uploaded. Use your CI secret manager for shared/production secrets.

```bash
# Store a credential locally (never in the repo)
python -c "from edition2.vault import SecretsVault; SecretsVault('~/.aicodex/edition2_vault.json').set('CLAUDE_API_KEY', '...')"
```

### CHAiMERA ConductorX Orchestration

`CHAiMERA.ConductorX` validates each role's declared inputs against the outputs of earlier roles (plus external `seeds` such as `requirements_spec` and `internal_build_metrics`), then sequences the enabled roles into a dependency-aware run and emits a plain-text **Symphony Report** of structure and code-accuracy status.

```bash
python -m edition2 --version                 # print the Edition 2 version
python -m edition2 --list-roles              # list configured roles & their state
python -m edition2                           # run the orchestration, print the report
python -m edition2 --include-disabled        # also show disabled roles as skipped
```

Disable any optional role by setting `"enabled": false` for it in `config/edition2_settings.json`; ConductorX then records it as skipped (or omits it) without touching the rest of the configuration.

### Hive — Model-Driven VMware Worker Bots

The **hive** (`edition2/hive/`) is a cluster of lightweight **VMware worker bots**, one spawned per enabled model role (per its declared needs). Working **in parallel**, the cluster:

1. **Finds bandwidth gaps & peaks/troughs** — every bot samples its bandwidth concurrently (`ThreadPoolExecutor`) and is classified `peak`, `trough`, or `idle`.
2. **Balances the load into the troughs** — load is shed from peak-saturated bots into trough-idle bots (total load is conserved and troughs are never overfilled).
3. **Patches missing data bits** — gaps detected during analysis are filled with updated **innovation-research results** supplied by the Mistral `research_dev` role.

Tune the cluster in the `hive` section of `config/edition2_settings.json` (`worker_capacity`, `peak_threshold`, `trough_threshold`, `max_workers`, `research_source_model`), then run it:

```bash
python -m edition2 --hive               # analyse → balance → patch, print Cluster Report
```

The implementation is standard-library only and deterministic when load/bandwidth samples are injected, so it is fully testable offline (see `tests/test_hive.py`).

### Compute Backends — Per-Model Links

Every model has its own **compute link** (`edition2/backends.py`) describing where its work runs. Each role's `compute` block in `config/edition2_settings.json` selects exactly one backend kind:

- **`standard`** — the provider's standard model output (no endpoint).
- **`vps`** — a user-supplied VPS.
- **`cloud`** — a user-supplied cloud instance.
- **`gpu`** — a user GPU, with `gpu_vendor` of **`Nvidia`** or **`Tesla`**.

Non-standard backends require an `endpoint`, stored as a `$VAULT:key` reference (resolved through the local secrets vault) so no host or credential is ever committed. The default assignment:

| Role | Model | Compute link |
|------|-------|--------------|
| `skeleton_architect` | Claude | standard |
| `formation_planner` | Gemini | cloud |
| `base_coder` | Cursor | VPS |
| `error_patcher` | Kimi 3 | standard |
| `research_dev` | Mistral | GPU (Nvidia) |
| `security_netops` | Grok | GPU (Tesla) |
| `spec_logger` | ChatGPT | standard |

```bash
python -m edition2 --backends           # list each model's compute link
```

### Metrics Control Deck & Model Catalog

Within the backend links is a **metrics panel** (`edition2/metrics.py`) the user can click into — a parameters/usage **control deck** that monitors:

- **Token usage per model output** (tokens and cost per output) and **cost per token** per model.
- **Better-model swap suggestions** — flags when a cheaper model delivers equal-or-more value (tokens/output) at a lower cost per token, so you can swap for better performance.
- **Platform-wide totals** — token performance and usage per output aggregated **across all users** on the platform.

`render_page()` renders a self-contained HTML **metrics web page** so other users can see the current value trend per model they picked, plus an overall report on the value each model provided from actual build-performance analysis and research results.

```bash
python -m edition2 --metrics                    # print the usage control-deck summary
python -m edition2 --metrics-html metrics.html  # write the metrics web page
```

The **Hugging Face model-selection catalog** (`edition2/hfcatalog.py`) offers full **click-and-install** model variety with user **API-key access activation**. The API key is supplied via a `$VAULT:key` reference (resolved through the local vault, never persisted); gated models require it.

```bash
python -m edition2 --hf-catalog                 # list the installable HF model variety
```

Cost-per-token per model lives in the `metrics` section, and the installable HF catalog in the `hf_models` section, of `config/edition2_settings.json`.

### Realtime Monitor, COB Reports & Community Forum

A **monitor system** (`edition2/monitor.py`) sits over everything. Each component feeds it through a per-component **valve** that batches realtime metrics and forwards them to the **conductor** for enhancement management and to the **database-analysis coordination** hooks — keeping innovation and future-development signals flowing. The display updates in realtime on a configurable interval (default **0.5 s**).

```bash
python -m edition2 --monitor                  # run the realtime monitor display
```

At **close of business**, `edition2/cob.py` builds a daily report on **who is the best at what job**, generates a **daily article**, and allocates **user-wanted improvements** to a discussion channel (forum, **voice message**, or **email**):

```bash
python -m edition2 --cob-report               # print the close-of-business daily report
```

The **community forum** (`edition2/forum.py`) is a link off the app but wholly connected to it — a **live web page that non-members can access and read** (read-only publicly; members post via the app). It hosts the daily COB articles, discussions, and allocated improvement requests, refreshing live every 0.5 s.

```bash
python -m edition2 --forum-html forum.html    # write the public community forum page
```

Tune the monitor, COB, and forum in the `monitor` section of `config/edition2_settings.json`.

## AI Writers Integration

AicodeX is integrated as the **internal overlayer for the AI writers** — it provides the shared overlay layer that AI writing tools use to surface hotkey-driven, in-context coding and writing assistance on top of any application.

### How the Integration Works

- **Overlay host:** AicodeX renders the always-on-top overlay window (see `src/overlay.py`) that AI writer features are injected into, so writers get assistance without leaving their editor.
- **Hotkey bridge:** Global hotkeys registered by AicodeX (see `src/hotkeys.py`) are forwarded to the active AI writer, keeping triggering consistent across tools.
- **Context & snippets:** AI writers consume AicodeX's snippet and quick-action pipeline (see `src/main.py`) to insert, format, and transform content at the cursor.
- **Shared configuration:** Writers inherit overlay, hotkey, and feature settings from `config/default_settings.json`, so behavior stays customizable in one place.

## Installation

### Prerequisites

- Python 3.11 or higher
- Windows 10/11 (recommended)
- Administrator privileges (for global hotkey registration)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NaTo1000/AicodeX.git
   cd AicodeX
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run AicodeX:**
   ```bash
   python src/main.py
   ```

### Building Executable

To create a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name AicodeX src/main.py
```

The executable will be created in the `dist/` directory.

## Usage

### Starting the Application

Run the application with default settings:
```bash
python src/main.py
```

With custom configuration:
```bash
python src/main.py --config path/to/config.json
```

With debug mode:
```bash
python src/main.py --debug
```

### Global Hotkeys

AicodeX supports the following global hotkeys (customizable in settings):

| Hotkey | Action | Description |
|--------|--------|-------------|
| `Ctrl+Shift+O` | Toggle Overlay | Show/hide the AicodeX overlay window |
| `Ctrl+Shift+S` | Insert Snippet | Insert a code snippet at cursor position |
| `Ctrl+Shift+F` | Format Code | Format selected code |

**Note:** Administrator privileges may be required for global hotkey functionality on Windows.

### Using the Overlay

The overlay window features three main tabs:

1. **Snippets** - Browse and copy code snippets
   - View pre-configured code templates
   - Quick copy-paste functionality
   - Support for multiple programming languages

2. **Actions** - Quick development actions
   - Check HandBrake version
   - Format code
   - Generate docstrings
   - Refactor selection

3. **Settings** - Configure the application
   - Adjust window opacity
   - View hotkey mappings
   - Customize appearance

## Configuration

### Configuration File

AicodeX uses a JSON configuration file located at `config/default_settings.json`. You can customize the following settings:

```json
{
  "window": {
    "width": 400,
    "height": 600,
    "x_position": 100,
    "y_position": 100,
    "opacity": 0.95
  },
  "hotkeys": {
    "toggle_overlay": "ctrl+shift+o",
    "insert_snippet": "ctrl+shift+s",
    "format_code": "ctrl+shift+f"
  },
  "snippets": [
    {
      "name": "Python Function",
      "code": "def function_name(param):\n    \"\"\"Docstring\"\"\"\n    pass"
    }
  ],
  "features": {
    "handbrake_integration": true,
    "auto_format": true,
    "snippet_suggestions": true
  }
}
```

### Window Settings

- `width` / `height` - Overlay window dimensions in pixels
- `x_position` / `y_position` - Window position on screen
- `opacity` - Window transparency (0.0 - 1.0)

### Hotkey Settings

Hotkeys use the format: `modifier+key`

Supported modifiers:
- `ctrl` - Control key
- `shift` - Shift key
- `alt` - Alt key
- `win` - Windows key

Examples:
- `ctrl+shift+o`
- `alt+f1`
- `ctrl+alt+s`

### Adding Custom Snippets

Add new snippets to the configuration file:

```json
{
  "snippets": [
    {
      "name": "Your Snippet Name",
      "code": "Your code here\nMultiple lines supported"
    }
  ]
}
```

## HandBrake Integration

AicodeX includes integration with HandBrake for video encoding tasks:

- **Latest Version:** 1.10.2
- **Download URL:** [HandBrake 1.10.2 for Windows x64](https://github.com/HandBrake/HandBrake/releases/download/1.10.2/HandBrake-1.10.2-x86_64-Win_GUI.exe)
- **SHA256 Checksum:** `ff868bb43c19a4fd8bec8f4b9d83a756f6818cf4b229012715f35eb2416673cd`

Use the "Check HandBrake Version" action in the Actions tab to check for the latest version.

## Development

### Project Structure

```
AicodeX/
├── .github/
│   ├── workflows/
│   │   └── build.yml              # CI/CD workflow
│   └── actions/
│       └── copilot/
│           └── setup-build-tools-enviroments/
│               └── action.yml     # Build tools setup action
├── src/
│   ├── main.py                    # Application entry point
│   ├── overlay.py                 # Overlay window implementation
│   ├── hotkeys.py                 # Hotkey management
│   ├── config.py                  # Configuration management
│   └── utils/
│       └── handbrake_checker.py   # HandBrake integration
├── edition2/                      # Edition 2 — multi-model orchestration
│   ├── __init__.py                # Package version & metadata
│   ├── __main__.py                # CLI entry point
│   ├── orchestrator.py            # Role registry & config validation
│   ├── vault.py                   # Optional local-only secrets vault
│   ├── backends.py                # Per-model compute-backend links
│   ├── metrics.py                 # Usage metrics control deck & HTML page
│   ├── hfcatalog.py               # Hugging Face model-selection catalog
│   ├── monitor.py                 # Realtime monitor system with valves
│   ├── cob.py                     # Close-of-business daily reports
│   ├── forum.py                   # Public community forum page
│   └── chaimera/
│       ├── __init__.py            # CHAiMERA subsystem exports
│       └── conductorx.py          # ConductorX orchestrator & report
│   └── hive/
│       ├── __init__.py            # Hive subsystem exports
│       └── cluster.py             # VMware worker-bot cluster & balancing
├── config/
│   ├── default_settings.json      # Default configuration
│   └── edition2_settings.json     # Edition 2 roles & orchestration
├── tests/                         # Test files
│   └── test_edition2.py           # Edition 2 test suite (stdlib unittest)
│   └── test_hive.py               # Hive cluster tests (stdlib unittest)
│   └── test_backends.py           # Compute-backend tests (stdlib unittest)
│   └── test_metrics.py            # Metrics control-deck tests (stdlib unittest)
│   └── test_hf.py                 # HF catalog tests (stdlib unittest)
│   └── test_monitor.py            # Monitor system tests (stdlib unittest)
│   └── test_cob.py                # COB report tests (stdlib unittest)
│   └── test_forum.py              # Forum page tests (stdlib unittest)
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore patterns
└── README.md                      # This file
```

### Running Tests

The Edition 2 suite uses only the standard library, so it runs anywhere:

```bash
python -m unittest discover -s tests -v
```

It is also pytest-compatible:

```bash
pytest tests/ -v
```

### Code Quality

Format code with Black:
```bash
black src/
```

Lint code with Pylint:
```bash
pylint src/
```

## Build & Delivery Pipeline

- **Languages:** Python (automation/integration), Rust (performance-critical components), TypeScript (UI/overlay).
- **Targets:** Windows, macOS, Linux, Web.
- **Build Variants:** Debug, Release, CI.
- **Deliverables:** CLI binaries, shared libraries, installer bundles, Docker images.

### Setup

- **Repository:** Git (`main` stable, `develop` integration).
- **Toolchains:** Python ≥ 3.11 with `pip`, Rust stable with `cargo`/`rustup`, Node.js ≥ 18 with `npm`. Lockfiles (`requirements.txt` or `poetry.lock`, `Cargo.lock`, `package-lock.json`) ensure reproducibility.
- **Environment:** Configure CI secrets for publishing/signing; use a local `.env` (never committed) for development secrets.
- **Commands:**
  - Python: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
  - Rust targets (add as needed): `rustup target add x86_64-unknown-linux-gnu`, `rustup target add x86_64-pc-windows-gnu`, `rustup target add x86_64-apple-darwin`, `rustup target add wasm32-unknown-unknown`; then `cargo fetch`
  - TypeScript: `npm ci`
  - Optional: `make` targets may wrap the steps below when present.

### Configuration

- **Targets:** `BUILD_TARGET=app|lib|cli` (overlay app, reusable library, or CLI).
- **Optimization:** `PROFILE=debug|release|ci` mapping to O0/O2/O3 and deterministic CI flags.
- **Debug Info:** `DEBUG_SYMBOLS=full|none`.
- **Architecture:** `ARCH=x86_64|arm64`.
- **Features:** `FEATURES="telemetry,wasm"` etc. (Rust `--features`, TS feature flags, Python env toggles).
- **Environment Flags:** `RUSTFLAGS`, `NODE_ENV=production`, `PYTHONWARNINGS`, `AICODEX_CONFIG` path.

### Pipeline Stages

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

### Security & Compliance

- Enforce dependency scanning (`pip-audit`, `cargo audit`, `npm audit`) in CI.
- Produce SBOMs when packaging (`syft` or ecosystem equivalents).
- Keep secrets in CI-managed stores; never commit them. Validate licenses of third-party dependencies.

### Testing Strategy

- **Types:** Unit, integration, and UI/overlay checks (headless where possible).
- **Environments:** Local dev parity with CI; optional staging with feature flags.
- **Criteria:** All required suites green; maintain agreed coverage thresholds for Python, Rust, and TS components.

### Delivery

- **Artifacts:** CLI binaries and shared libraries (`target/<triple>/release`), installer bundles per OS (`dist/`), web bundles (`build/`), Docker images.
- **Metadata:** Include version, commit, build date, and checksums with every artifact.
- **Distribution:** Upload release assets, publish containers to registries, and keep rollback-ready previous versions. Sign all distributed artifacts.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the terms included in the LICENSE file.

## Troubleshooting

### Hotkeys Not Working

- Ensure you're running the application with administrator privileges
- Check if other applications are using the same hotkey combinations
- Verify your hotkey configuration in the settings file

### Overlay Not Appearing

- Check if the overlay is hidden (try the toggle hotkey)
- Verify the window position is within your screen bounds
- Ensure Python and tkinter are properly installed

### Import Errors

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Verify you're using Python 3.11 or higher: `python --version`

## Support

For issues, questions, or suggestions, please open an issue on the [GitHub repository](https://github.com/NaTo1000/AicodeX/issues).

---

**AicodeX** - Enhance your coding workflow with hotkey-powered productivity!

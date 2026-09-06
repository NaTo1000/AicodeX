# AicodeX

**AicodeX** is a companion overlay code engine with a fair few really awesome features. It's hotkey-enabled and highly customizable, designed to enhance your coding experience with quick access to code snippets, actions, and utilities.

> ## 🍎 New: Full SwiftUI Overhaul
>
> AicodeX has been rebuilt as a **native SwiftUI app** for macOS & iOS, ready for App Store review and release.
> The Apple code lives in [`apple/`](apple/):
>
> - **`apple/Sources/AicodeXCore`** — pure-Foundation core (models, settings store, HandBrake checker, SHA-256). Compiles and tests on Linux: `cd apple && swift test`.
> - **`apple/App`** — the SwiftUI app (Snippets / Actions / Settings tabs, macOS overlay panel), built with Xcode.
>
> **Build & test the core (macOS or Linux):**
> ```bash
> cd apple
> swift build
> swift test
> ```
>
> **App Store release:** signing & upload are driven by CI secrets — see [`apple/APPLE_CREDENTIALS.md`](apple/APPLE_CREDENTIALS.md).
> The Python/tkinter Windows version below is retained for reference.

## Features

- 🎯 **Overlay Interface** - Semi-transparent overlay window that stays on top of all applications
- ⌨️ **Global Hotkeys** - Quick access to features from anywhere on your system
- 📝 **Code Snippets** - Pre-defined code templates for faster development
- ⚡ **Quick Actions** - One-click access to common development tasks
- 🎨 **Highly Customizable** - Configure hotkeys, appearance, and behavior
- 🔧 **HandBrake Integration** - Check and download the latest HandBrake version
- 🖥️ **Windows Optimized** - Built specifically for Windows development workflows

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
├── config/
│   └── default_settings.json      # Default configuration
├── tests/                         # Test files
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore patterns
└── README.md                      # This file
```

### Running Tests

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

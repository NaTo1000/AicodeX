#!/bin/bash
# Installation script for different platforms

set -e

INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="$HOME/.aicodex"

echo "Installing AicodeX..."

# Create config directory
mkdir -p "$CONFIG_DIR"

# Copy example config if not exists
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    cp config.example.json "$CONFIG_DIR/config.json"
    echo "Created default configuration at $CONFIG_DIR/config.json"
fi

# Install based on platform
case "$(uname -s)" in
    Linux*)
        echo "Installing on Linux..."
        # Install Python package
        pip3 install --user .
        ;;
    Darwin*)
        echo "Installing on macOS..."
        # Install Python package
        pip3 install --user .
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "Installing on Windows..."
        # Install Python package
        pip install --user .
        ;;
    *)
        echo "Unknown platform: $(uname -s)"
        exit 1
        ;;
esac

echo ""
echo "✓ Installation complete!"
echo ""
echo "Configuration: $CONFIG_DIR/config.json"
echo "Run 'aicodex' to start the application"

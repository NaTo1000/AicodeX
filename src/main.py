"""
AicodeX - Companion Overlay Code Engine
Main entry point for the application
"""

import sys
import argparse
from overlay import OverlayWindow
from config import Config
from hotkeys import HotkeyManager

__version__ = "1.0.0"


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description="AicodeX - Companion Overlay Code Engine"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"AicodeX {__version__}"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/default_settings.json",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config(args.config)
    
    # Initialize hotkey manager
    hotkey_manager = HotkeyManager(config)
    
    # Create and run overlay window
    overlay = OverlayWindow(config, hotkey_manager)
    
    print(f"AicodeX {__version__} starting...")
    print(f"Configuration loaded from: {args.config}")
    print(f"Debug mode: {args.debug}")
    
    # Register global hotkeys
    hotkey_manager.register_all()
    
    # Start the overlay application
    try:
        overlay.run()
    except KeyboardInterrupt:
        print("\nShutting down AicodeX...")
    finally:
        hotkey_manager.unregister_all()
        print("AicodeX stopped.")


if __name__ == "__main__":
    main()

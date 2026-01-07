"""
Main entry point for AicodeX application.
"""

import sys
from typing import List, Optional

from aicodex.engine import CodeEngine
from aicodex.hotkey import HotkeyManager


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the application.

    Args:
        args: Command line arguments

    Returns:
        Exit code
    """
    if args is None:
        args = sys.argv[1:]

    print("AicodeX v0.1.0")
    print("Companion overlay code engine starting...")

    try:
        engine = CodeEngine()
        hotkey_mgr = HotkeyManager()

        print("Engine initialized successfully")
        print("Press Ctrl+C to exit")

        # Keep the application running
        engine.run()

        return 0
    except KeyboardInterrupt:
        print("\nShutting down...")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

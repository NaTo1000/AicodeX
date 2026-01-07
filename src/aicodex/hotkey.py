"""
Hotkey management for AicodeX.
"""

from typing import Dict, Callable


class HotkeyManager:
    """Manage hotkeys for the application."""

    def __init__(self) -> None:
        """Initialize the hotkey manager."""
        self.hotkeys: Dict[str, Callable[[], None]] = {}

    def register(self, key_combo: str, callback: Callable[[], None]) -> None:
        """
        Register a hotkey.

        Args:
            key_combo: Key combination string (e.g., "ctrl+shift+a")
            callback: Function to call when hotkey is pressed
        """
        self.hotkeys[key_combo] = callback
        print(f"Registered hotkey: {key_combo}")

    def unregister(self, key_combo: str) -> None:
        """
        Unregister a hotkey.

        Args:
            key_combo: Key combination string
        """
        if key_combo in self.hotkeys:
            del self.hotkeys[key_combo]
            print(f"Unregistered hotkey: {key_combo}")

    def trigger(self, key_combo: str) -> bool:
        """
        Trigger a hotkey callback.

        Args:
            key_combo: Key combination string

        Returns:
            True if hotkey was found and triggered, False otherwise
        """
        if key_combo in self.hotkeys:
            self.hotkeys[key_combo]()
            return True
        return False

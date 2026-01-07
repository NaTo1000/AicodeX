"""Hotkey management module for AicodeX."""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Hotkey:
    """Represents a hotkey binding."""

    key: str
    modifiers: list[str] = field(default_factory=list)
    action: Callable[[], None] | None = None
    description: str = ""

    def matches(self, key: str, modifiers: list[str]) -> bool:
        """Check if the given key and modifiers match this hotkey."""
        return self.key == key and set(self.modifiers) == set(modifiers)

    def trigger(self) -> bool:
        """Trigger the hotkey action."""
        if self.action is not None:
            self.action()
            return True
        return False


class HotkeyManager:
    """Manager for hotkey bindings."""

    def __init__(self) -> None:
        """Initialize the hotkey manager."""
        self._hotkeys: list[Hotkey] = []
        self._enabled = True

    @property
    def is_enabled(self) -> bool:
        """Check if hotkey manager is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable hotkey processing."""
        self._enabled = True

    def disable(self) -> None:
        """Disable hotkey processing."""
        self._enabled = False

    def register(self, hotkey: Hotkey) -> bool:
        """Register a new hotkey."""
        for existing in self._hotkeys:
            if existing.matches(hotkey.key, hotkey.modifiers):
                return False
        self._hotkeys.append(hotkey)
        return True

    def unregister(self, key: str, modifiers: list[str] | None = None) -> bool:
        """Unregister a hotkey."""
        modifiers = modifiers or []
        for i, hotkey in enumerate(self._hotkeys):
            if hotkey.matches(key, modifiers):
                self._hotkeys.pop(i)
                return True
        return False

    def process(self, key: str, modifiers: list[str] | None = None) -> bool:
        """Process a key press and trigger matching hotkey."""
        if not self._enabled:
            return False
        modifiers = modifiers or []
        for hotkey in self._hotkeys:
            if hotkey.matches(key, modifiers):
                return hotkey.trigger()
        return False

    def list_hotkeys(self) -> list[Hotkey]:
        """Return list of registered hotkeys."""
        return self._hotkeys.copy()

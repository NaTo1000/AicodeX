"""
Tests for the hotkey manager.
"""

import pytest
from aicodex.hotkey import HotkeyManager


def test_hotkey_manager_initialization() -> None:
    """Test that hotkey manager initializes correctly."""
    manager = HotkeyManager()
    assert manager is not None
    assert len(manager.hotkeys) == 0


def test_hotkey_registration() -> None:
    """Test hotkey registration."""
    manager = HotkeyManager()
    called = []

    def callback() -> None:
        called.append(True)

    manager.register("ctrl+a", callback)
    assert "ctrl+a" in manager.hotkeys
    assert manager.trigger("ctrl+a")
    assert len(called) == 1


def test_hotkey_unregistration() -> None:
    """Test hotkey unregistration."""
    manager = HotkeyManager()

    def callback() -> None:
        pass

    manager.register("ctrl+a", callback)
    assert "ctrl+a" in manager.hotkeys
    manager.unregister("ctrl+a")
    assert "ctrl+a" not in manager.hotkeys


def test_trigger_nonexistent_hotkey() -> None:
    """Test triggering a non-existent hotkey."""
    manager = HotkeyManager()
    result = manager.trigger("ctrl+z")
    assert result is False

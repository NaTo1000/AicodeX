"""Tests for the hotkey module."""

import pytest

from aicodex.hotkey import Hotkey, HotkeyManager


class TestHotkey:
    """Tests for Hotkey."""

    def test_hotkey_matches(self) -> None:
        """Test hotkey matching."""
        hotkey = Hotkey(key="a", modifiers=["ctrl"])
        assert hotkey.matches("a", ["ctrl"]) is True
        assert hotkey.matches("b", ["ctrl"]) is False
        assert hotkey.matches("a", []) is False

    def test_hotkey_trigger_with_action(self) -> None:
        """Test triggering hotkey with action."""
        triggered = []
        hotkey = Hotkey(key="a", action=lambda: triggered.append(True))
        result = hotkey.trigger()
        assert result is True
        assert len(triggered) == 1

    def test_hotkey_trigger_without_action(self) -> None:
        """Test triggering hotkey without action."""
        hotkey = Hotkey(key="a")
        result = hotkey.trigger()
        assert result is False


class TestHotkeyManager:
    """Tests for HotkeyManager."""

    def test_register_hotkey(self) -> None:
        """Test registering a hotkey."""
        manager = HotkeyManager()
        hotkey = Hotkey(key="a", modifiers=["ctrl"])
        result = manager.register(hotkey)
        assert result is True
        assert len(manager.list_hotkeys()) == 1

    def test_register_duplicate_hotkey(self) -> None:
        """Test that duplicate hotkeys are rejected."""
        manager = HotkeyManager()
        hotkey1 = Hotkey(key="a", modifiers=["ctrl"])
        hotkey2 = Hotkey(key="a", modifiers=["ctrl"])
        manager.register(hotkey1)
        result = manager.register(hotkey2)
        assert result is False
        assert len(manager.list_hotkeys()) == 1

    def test_unregister_hotkey(self) -> None:
        """Test unregistering a hotkey."""
        manager = HotkeyManager()
        hotkey = Hotkey(key="a", modifiers=["ctrl"])
        manager.register(hotkey)
        result = manager.unregister("a", ["ctrl"])
        assert result is True
        assert len(manager.list_hotkeys()) == 0

    def test_process_hotkey(self) -> None:
        """Test processing a hotkey."""
        manager = HotkeyManager()
        triggered = []
        hotkey = Hotkey(key="a", modifiers=["ctrl"], action=lambda: triggered.append(True))
        manager.register(hotkey)
        result = manager.process("a", ["ctrl"])
        assert result is True
        assert len(triggered) == 1

    def test_process_when_disabled(self) -> None:
        """Test that processing is blocked when disabled."""
        manager = HotkeyManager()
        triggered = []
        hotkey = Hotkey(key="a", action=lambda: triggered.append(True))
        manager.register(hotkey)
        manager.disable()
        result = manager.process("a")
        assert result is False
        assert len(triggered) == 0

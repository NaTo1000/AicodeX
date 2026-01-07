"""Tests for the overlay module."""

import pytest

from aicodex.overlay import Overlay, OverlayConfig


class TestOverlayConfig:
    """Tests for OverlayConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = OverlayConfig()
        assert config.enabled is True
        assert config.opacity == 0.9
        assert config.width == 800
        assert config.height == 600


class TestOverlay:
    """Tests for Overlay."""

    def test_overlay_initially_hidden(self) -> None:
        """Test that overlay starts hidden."""
        overlay = Overlay()
        assert overlay.is_visible is False

    def test_show_overlay(self) -> None:
        """Test showing the overlay."""
        overlay = Overlay()
        result = overlay.show()
        assert result is True
        assert overlay.is_visible is True

    def test_hide_overlay(self) -> None:
        """Test hiding the overlay."""
        overlay = Overlay()
        overlay.show()
        result = overlay.hide()
        assert result is True
        assert overlay.is_visible is False

    def test_toggle_overlay(self) -> None:
        """Test toggling overlay visibility."""
        overlay = Overlay()
        # Toggle on
        overlay.toggle()
        assert overlay.is_visible is True
        # Toggle off
        overlay.toggle()
        assert overlay.is_visible is False

    def test_show_disabled_overlay(self) -> None:
        """Test that disabled overlay cannot be shown."""
        config = OverlayConfig(enabled=False)
        overlay = Overlay(config)
        result = overlay.show()
        assert result is False
        assert overlay.is_visible is False

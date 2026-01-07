"""Overlay module for AicodeX."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OverlayConfig:
    """Configuration for the overlay."""

    enabled: bool = True
    opacity: float = 0.9
    position_x: int = 0
    position_y: int = 0
    width: int = 800
    height: int = 600


class Overlay:
    """Overlay manager for AicodeX."""

    def __init__(self, config: Optional[OverlayConfig] = None) -> None:
        """Initialize the overlay with optional configuration."""
        self.config = config or OverlayConfig()
        self._visible = False

    @property
    def is_visible(self) -> bool:
        """Check if overlay is currently visible."""
        return self._visible

    def show(self) -> bool:
        """Show the overlay."""
        if not self.config.enabled:
            return False
        self._visible = True
        return True

    def hide(self) -> bool:
        """Hide the overlay."""
        self._visible = False
        return True

    def toggle(self) -> bool:
        """Toggle overlay visibility."""
        if self._visible:
            return self.hide()
        return self.show()

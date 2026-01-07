"""
Tests for the main module.
"""

import pytest
from aicodex.main import main


def test_main_with_keyboard_interrupt(monkeypatch) -> None:
    """Test main function handles keyboard interrupt."""
    def mock_run(self):
        raise KeyboardInterrupt()

    from aicodex import engine
    monkeypatch.setattr(engine.CodeEngine, "run", mock_run)

    result = main([])
    assert result == 0

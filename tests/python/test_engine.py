"""
Tests for the code engine.
"""

import pytest
from aicodex.engine import CodeEngine


def test_engine_initialization() -> None:
    """Test that engine initializes correctly."""
    engine = CodeEngine()
    assert engine is not None
    assert not engine.is_running


def test_engine_configuration() -> None:
    """Test engine configuration."""
    engine = CodeEngine()
    config = {"theme": "dark", "opacity": 0.9}
    engine.configure(config)
    assert engine.config["theme"] == "dark"
    assert engine.config["opacity"] == 0.9


def test_engine_stop() -> None:
    """Test engine can be stopped."""
    engine = CodeEngine()
    engine.stop()
    assert not engine.is_running

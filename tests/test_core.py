"""Tests for the core engine."""

import pytest
from aicodex import Engine


def test_engine_init():
    """Test engine initialization."""
    engine = Engine()
    assert engine is not None
    assert not engine.is_running()


def test_engine_start():
    """Test engine start."""
    engine = Engine()
    assert engine.start()
    assert engine.is_running()


def test_engine_stop():
    """Test engine stop."""
    engine = Engine()
    engine.start()
    assert engine.stop()
    assert not engine.is_running()


def test_engine_with_config():
    """Test engine with configuration."""
    config = {"debug": True}
    engine = Engine(config=config)
    assert engine.config == config

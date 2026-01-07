"""Tests for the AicodeX Python package."""

import sys
from pathlib import Path

# Add src/python to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "python"))

from __init__ import __version__, get_version, greet


class TestVersion:
    """Tests for version functionality."""

    def test_version_string(self):
        """Test that version is a valid string."""
        assert isinstance(__version__, str)
        assert __version__ == "0.1.0"

    def test_get_version(self):
        """Test get_version function."""
        assert get_version() == __version__


class TestGreet:
    """Tests for greet functionality."""

    def test_greet_default(self):
        """Test greet with default name."""
        assert greet() == "Hello, World from AicodeX!"

    def test_greet_custom_name(self):
        """Test greet with custom name."""
        assert greet("Python") == "Hello, Python from AicodeX!"

    def test_greet_empty_name(self):
        """Test greet with empty string."""
        assert greet("") == "Hello,  from AicodeX!"

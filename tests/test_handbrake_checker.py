"""
Tests for HandBrake checker utility
"""

import os
import sys
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.handbrake_checker import HandBrakeChecker


def test_handbrake_checker_initialization():
    """Test HandBrake checker initialization"""
    checker = HandBrakeChecker()
    assert checker.version == "1.10.2"


def test_handbrake_version_check():
    """Test version check returns expected format"""
    checker = HandBrakeChecker()
    result = checker.check_version()
    
    assert "1.10.2" in result
    assert "HandBrake" in result


def test_handbrake_get_info():
    """Test getting HandBrake information"""
    checker = HandBrakeChecker()
    info = checker.get_info()
    
    assert 'version' in info
    assert 'download_url' in info
    assert 'sha256' in info
    
    assert info['version'] == "1.10.2"
    assert "HandBrake" in info['download_url']
    assert len(info['sha256']) == 64  # SHA256 hash length


def test_handbrake_constants():
    """Test HandBrake constants are correctly defined"""
    assert HandBrakeChecker.LATEST_VERSION == "1.10.2"
    assert HandBrakeChecker.EXPECTED_SHA256 == "ff868bb43c19a4fd8bec8f4b9d83a756f6818cf4b229012715f35eb2416673cd"
    assert "github.com/HandBrake/HandBrake" in HandBrakeChecker.DOWNLOAD_URL

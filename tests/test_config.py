"""
Tests for AicodeX configuration module
"""

import os
import sys
import json
import tempfile
import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config


def test_config_initialization():
    """Test that Config initializes with default settings"""
    config = Config("non_existent_config.json")
    assert config.settings is not None
    assert 'window' in config.settings
    assert 'hotkeys' in config.settings


def test_config_get():
    """Test getting configuration values"""
    config = Config("non_existent_config.json")
    window_config = config.get('window')
    assert window_config is not None
    assert 'width' in window_config
    assert window_config['width'] == 400


def test_config_set():
    """Test setting configuration values"""
    config = Config("non_existent_config.json")
    config.set('test_key', 'test_value')
    assert config.get('test_key') == 'test_value'


def test_config_save_and_load():
    """Test saving and loading configuration"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_config_path = f.name
    
    try:
        # Create and save config
        config1 = Config("non_existent_config.json")
        config1.config_path = temp_config_path
        config1.set('custom_key', 'custom_value')
        config1.save()
        
        # Load config in new instance
        config2 = Config(temp_config_path)
        assert config2.get('custom_key') == 'custom_value'
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)


def test_default_hotkeys():
    """Test that default hotkeys are properly configured"""
    config = Config("non_existent_config.json")
    hotkeys = config.get('hotkeys')
    
    assert 'toggle_overlay' in hotkeys
    assert 'insert_snippet' in hotkeys
    assert 'format_code' in hotkeys
    
    assert hotkeys['toggle_overlay'] == 'ctrl+shift+o'
    assert hotkeys['insert_snippet'] == 'ctrl+shift+s'
    assert hotkeys['format_code'] == 'ctrl+shift+f'


def test_default_snippets():
    """Test that default snippets are configured"""
    config = Config("non_existent_config.json")
    snippets = config.get('snippets')
    
    assert isinstance(snippets, list)
    assert len(snippets) >= 2
    assert any(s['name'] == 'Python Function' for s in snippets)

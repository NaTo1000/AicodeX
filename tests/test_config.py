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


def _resilience_config(tmp_path):
    """Build a config file with resilience enabled and mirror cloud drives"""
    cloud1 = tmp_path / "cloud1"
    cloud2 = tmp_path / "cloud2"
    cloud1.mkdir()
    cloud2.mkdir()
    settings = {
        "window": {"width": 400, "height": 600},
        "theme": {"background": "#2b2b2b"},
        "resilience": {
            "enabled": True,
            "storage_dir": str(tmp_path / "local"),
            "backup_count": 3,
            "driver_registry": {
                "local": {"type": "local", "path": str(tmp_path / "local")},
                "cloud": {"type": "mirror-cloud",
                          "paths": [str(cloud1), str(cloud2)]},
            },
            "defaults": {"codecs": ["utf-8", "base64"],
                         "drivers": ["local", "cloud"]},
        },
    }
    config_file = tmp_path / "settings.json"
    config_file.write_text(json.dumps(settings))
    return str(config_file)


def test_resilience_disabled_by_default():
    """Resilience layer stays off unless enabled"""
    config = Config("non_existent_config.json")
    assert config._resilience is None
    assert config.list_section_backups("window") == []


def test_config_save_mirrors_sections(tmp_path):
    """Saving the config mirrors each section to local and cloud drives"""
    config = Config(_resilience_config(tmp_path))
    config.save()
    for drive in (tmp_path / "local", tmp_path / "cloud1", tmp_path / "cloud2"):
        assert (drive / "sections" / "window.dat").is_file()
        assert (drive / "sections" / "theme.dat").is_file()


def test_config_restore_section(tmp_path):
    """A user can restore a section to its previous mirrored value"""
    config = Config(_resilience_config(tmp_path))
    config.save()
    config.set('window', {"width": 999, "height": 999})
    config.save()
    assert config.restore_section('window')
    assert config.get('window') == {"width": 400, "height": 600}
    # Restore also persists back to the config file on disk
    with open(config.config_path, encoding='utf-8') as f:
        on_disk = json.load(f)
    assert on_disk['window'] == {"width": 400, "height": 600}


def test_config_clean_shutdown_marks_no_crash(tmp_path, capsys):
    """A clean shutdown means the next run reports no crash recovery"""
    config_path = _resilience_config(tmp_path)
    config = Config(config_path)
    config.save()
    config.shutdown()
    capsys.readouterr()  # drain prior output
    Config(config_path)
    assert "did not shut down cleanly" not in capsys.readouterr().out


def test_config_crash_recovery(tmp_path, capsys):
    """A run without clean shutdown triggers crash recovery output"""
    config_path = _resilience_config(tmp_path)
    config = Config(config_path)
    config.save()
    capsys.readouterr()  # drain prior output
    # Simulate a crash: no shutdown() call before the next run starts
    Config(config_path)
    assert "did not shut down cleanly" in capsys.readouterr().out

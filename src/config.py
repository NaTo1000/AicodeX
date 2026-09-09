"""
Configuration management for AicodeX
Loads and manages application settings
"""

import json
import os


class Config:
    """Configuration manager for AicodeX"""
    
    def __init__(self, config_path="config/default_settings.json"):
        """Initialize configuration"""
        self.config_path = config_path
        self.settings = {}
        self._resilience = None
        self.load()
        self._init_resilience()
        
    def load(self):
        """Load configuration from file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                print(f"Configuration loaded from {self.config_path}")
            except Exception as e:
                print(f"Error loading configuration: {e}")
                self.settings = self.get_default_settings()
        else:
            print(f"Configuration file not found: {self.config_path}")
            print("Using default settings")
            self.settings = self.get_default_settings()
            
    def save(self):
        """Save configuration to file (atomically, with mirror backup)"""
        try:
            dirname = os.path.dirname(self.config_path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            temp_path = self.config_path + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            os.replace(temp_path, self.config_path)
            print(f"Configuration saved to {self.config_path}")
            self._save_sections_to_resilience()
        except Exception as e:
            print(f"Error saving configuration: {e}")
            
    def _init_resilience(self):
        """Set up crash resilience if enabled in the configuration"""
        spec = self.settings.get('resilience', {})
        if not spec.get('enabled', False):
            return
        try:
            from resilience import ResilienceManager
            self._resilience = ResilienceManager(spec)
            crashed = self._resilience.crashed_last_run()
            self._resilience.mark_start()
            if crashed:
                print("Resilience: previous run did not shut down cleanly; "
                      "verifying sections via mirror cloud drives")
                report = self._resilience.recover_after_crash()
                for section, status in report.items():
                    print(f"Resilience: section '{section}': {status}")
        except Exception as e:
            print(f"Error initializing resilience: {e}")
            self._resilience = None
            
    def _save_sections_to_resilience(self):
        """Mirror each fine-tuned section through the resilience layer"""
        if self._resilience is None:
            return
        for section, value in self.settings.items():
            if section == 'resilience':
                continue
            self._resilience.save_section(section, value)
            
    def restore_section(self, section, backup_stamp=None):
        """Restore a section from its mirrored backups (user restore)

        Without backup_stamp, the most recent backup is used. Returns
        True if the section was restored into the live settings.
        """
        if self._resilience is None:
            print("Resilience is not enabled")
            return False
        stamp = backup_stamp
        if stamp is None:
            stamps = self._resilience.list_backups(section)
            if not stamps:
                print(f"No backups available for section '{section}'")
                return False
            stamp = stamps[-1]
        data = self._resilience.load_section(section, backup_stamp=stamp)
        if data is None:
            return False
        self.settings[section] = data
        self.save()
        return True
        
    def list_section_backups(self, section):
        """List available backup stamps for a section"""
        if self._resilience is None:
            return []
        return self._resilience.list_backups(section)
        
    def shutdown(self):
        """Record a clean shutdown so the next run knows no crash occurred"""
        if self._resilience is not None:
            self._resilience.mark_clean_shutdown()
            
    def get(self, key, default=None):
        """Get configuration value"""
        return self.settings.get(key, default)
        
    def set(self, key, value):
        """Set configuration value"""
        self.settings[key] = value
        
    def get_default_settings(self):
        """Get default configuration settings"""
        return {
            "window": {
                "width": 400,
                "height": 600,
                "x_position": 100,
                "y_position": 100,
                "opacity": 0.95
            },
            "hotkeys": {
                "toggle_overlay": "ctrl+shift+o",
                "insert_snippet": "ctrl+shift+s",
                "format_code": "ctrl+shift+f"
            },
            "snippets": [
                {
                    "name": "Python Function",
                    "code": "def function_name(param):\n    \"\"\"Docstring\"\"\"\n    pass"
                },
                {
                    "name": "JavaScript Function",
                    "code": "function functionName(param) {\n    // Comment\n    return value;\n}"
                }
            ],
            "theme": {
                "background": "#2b2b2b",
                "foreground": "#ffffff",
                "accent": "#007acc"
            },
            "features": {
                "handbrake_integration": True,
                "auto_format": True,
                "snippet_suggestions": True
            },
            "resilience": {
                "enabled": False,
                "storage_dir": ".aicodex",
                "backup_count": 5,
                "codecs": {},
                "drivers": {},
                "driver_registry": {},
                "defaults": {
                    "codecs": ["utf-8", "base64"],
                    "drivers": ["local"]
                }
            }
        }

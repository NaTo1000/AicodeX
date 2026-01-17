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
        self.load()
        
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
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            print(f"Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
            
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
            }
        }

"""
Configuration management for AicodeX
Loads and manages application settings
"""

import json
import os


def default_assistant_settings():
    """Default Assistant Persona & Analysis Engine configuration.

    Mirrors the ``assistant`` block in ``config/default_settings.json`` so the
    engine has sane defaults even when the config file omits the block.
    """
    return {
        "persona": {
            "name": "AicodeX Assistant",
            "tone": "analytical",
            "traits": {
                "analytical": 0.9,
                "creative": 0.4,
                "driver": 0.6,
                "amiable": 0.7,
            },
        },
        "trait_axes": ["analytical", "creative", "driver", "amiable"],
        "knowledge_base": [
            {
                "id": "perf-analytical",
                "solution": (
                    "Profile the hot path, add benchmark coverage, then optimize "
                    "the dominant cost centre with measurable before/after metrics."
                ),
                "traits": {"analytical": 0.7, "driver": 0.4},
                "min_confidence": 0.5,
            },
            {
                "id": "perf-creative",
                "solution": (
                    "Prototype two alternative designs, spike the riskiest "
                    "assumption, and pick the design that best satisfies the "
                    "constraints."
                ),
                "traits": {"creative": 0.7, "analytical": 0.3},
                "min_confidence": 0.5,
            },
            {
                "id": "perf-driver",
                "solution": (
                    "Cut scope to the critical path, time-box a decision, and ship "
                    "the smallest change that moves the key metric."
                ),
                "traits": {"driver": 0.7},
                "min_confidence": 0.45,
            },
            {
                "id": "perf-amiable",
                "solution": (
                    "Align stakeholders on the goal, gather requirements, and pair "
                    "on a solution that the team can maintain together."
                ),
                "traits": {"amiable": 0.7},
                "min_confidence": 0.45,
            },
        ],
        "retention": {"enabled": True, "max_records": 200},
        "council": {"min_confidence": 0.5, "min_justification": 0.4},
    }


def default_interaction_settings():
    """Default interaction (voice / chat / sandbox / providers) configuration.

    Mirrors the ``interaction`` block in ``config/default_settings.json``.
    Provider API keys are referenced by environment-variable *name* only —
    never literal secrets.
    """
    return {
        "voice": {"enabled": True, "wake_word": "aicodex", "command_prefix": ""},
        "chat": {"system_persona_tone": "analytical", "max_history": 100},
        "sandbox": {"enabled": True, "timeout_seconds": 5, "max_output_chars": 4000},
        "providers": [
            {"name": "huggingface", "kind": "huggingface", "endpoint": "https://api-inference.huggingface.co/models", "api_key_env": "HUGGINGFACE_API_KEY", "enabled": True},
            {"name": "northflank", "kind": "northflank", "endpoint": "https://api.northflank.com/v1", "api_key_env": "NORTHFLANK_API_KEY", "enabled": False},
            {"name": "bentoml", "kind": "bentoml", "endpoint": "http://localhost:3000", "api_key_env": "BENTOML_API_KEY", "enabled": False},
            {"name": "replicate", "kind": "replicate", "endpoint": "https://api.replicate.com/v1", "api_key_env": "REPLICATE_API_TOKEN", "enabled": False},
            {"name": "modal", "kind": "modal", "endpoint": "https://api.modal.com/v1", "api_key_env": "MODAL_TOKEN", "enabled": False},
            {"name": "lambdalabs", "kind": "lambdalabs", "endpoint": "https://api.lambdalabs.com/v1", "api_key_env": "LAMBDA_API_KEY", "enabled": False},
            {"name": "together", "kind": "together", "endpoint": "https://api.together.xyz/v1", "api_key_env": "TOGETHER_API_KEY", "enabled": True},
            {"name": "runpod", "kind": "runpod", "endpoint": "https://api.runpod.io/v2", "api_key_env": "RUNPOD_API_KEY", "enabled": False},
        ],
    }


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
            },
            "assistant": default_assistant_settings(),
            "interaction": default_interaction_settings()
        }

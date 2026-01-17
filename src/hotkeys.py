"""
Hotkey management for AicodeX
Handles global hotkey registration and callbacks
"""

import keyboard
import threading


class HotkeyManager:
    """Manages global hotkeys for the application"""
    
    def __init__(self, config):
        """Initialize hotkey manager"""
        self.config = config
        self.hotkeys = config.get('hotkeys', {})
        self.registered_hotkeys = []
        self.toggle_callback = None
        self.lock = threading.Lock()
        
    def set_toggle_callback(self, callback):
        """Set the callback for toggle hotkey"""
        self.toggle_callback = callback
        
    def register_all(self):
        """Register all hotkeys from configuration"""
        with self.lock:
            # Register toggle visibility hotkey
            toggle_key = self.hotkeys.get('toggle_overlay', 'ctrl+shift+o')
            try:
                keyboard.add_hotkey(toggle_key, self._on_toggle)
                self.registered_hotkeys.append(toggle_key)
                print(f"Registered hotkey: {toggle_key} (Toggle Overlay)")
            except Exception as e:
                print(f"Failed to register hotkey {toggle_key}: {e}")
            
            # Register snippet hotkey
            snippet_key = self.hotkeys.get('insert_snippet', 'ctrl+shift+s')
            try:
                keyboard.add_hotkey(snippet_key, self._on_snippet)
                self.registered_hotkeys.append(snippet_key)
                print(f"Registered hotkey: {snippet_key} (Insert Snippet)")
            except Exception as e:
                print(f"Failed to register hotkey {snippet_key}: {e}")
            
            # Register format hotkey
            format_key = self.hotkeys.get('format_code', 'ctrl+shift+f')
            try:
                keyboard.add_hotkey(format_key, self._on_format)
                self.registered_hotkeys.append(format_key)
                print(f"Registered hotkey: {format_key} (Format Code)")
            except Exception as e:
                print(f"Failed to register hotkey {format_key}: {e}")
                
    def unregister_all(self):
        """Unregister all hotkeys"""
        with self.lock:
            for hotkey in self.registered_hotkeys:
                try:
                    keyboard.remove_hotkey(hotkey)
                    print(f"Unregistered hotkey: {hotkey}")
                except Exception as e:
                    print(f"Failed to unregister hotkey {hotkey}: {e}")
            self.registered_hotkeys.clear()
            
    def _on_toggle(self):
        """Handle toggle overlay hotkey"""
        if self.toggle_callback:
            self.toggle_callback()
        else:
            print("Toggle overlay callback not set")
            
    def _on_snippet(self):
        """Handle insert snippet hotkey"""
        print("Snippet hotkey triggered")
        # Implement snippet insertion logic here
        
    def _on_format(self):
        """Handle format code hotkey"""
        print("Format code hotkey triggered")
        # Implement code formatting logic here

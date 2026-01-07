//! Hotkey management module for AicodeX

use std::collections::HashSet;

/// Represents a hotkey binding
#[derive(Debug, Clone)]
pub struct Hotkey {
    pub key: String,
    pub modifiers: HashSet<String>,
    pub description: String,
}

impl Hotkey {
    /// Create a new hotkey
    pub fn new(key: impl Into<String>) -> Self {
        Self {
            key: key.into(),
            modifiers: HashSet::new(),
            description: String::new(),
        }
    }

    /// Add a modifier to the hotkey
    pub fn with_modifier(mut self, modifier: impl Into<String>) -> Self {
        self.modifiers.insert(modifier.into());
        self
    }

    /// Add a description to the hotkey
    pub fn with_description(mut self, description: impl Into<String>) -> Self {
        self.description = description.into();
        self
    }

    /// Check if the given key and modifiers match this hotkey
    pub fn matches(&self, key: &str, modifiers: &HashSet<String>) -> bool {
        self.key == key && self.modifiers == *modifiers
    }
}

/// Manager for hotkey bindings
pub struct HotkeyManager {
    hotkeys: Vec<Hotkey>,
    enabled: bool,
}

impl HotkeyManager {
    /// Create a new hotkey manager
    pub fn new() -> Self {
        Self {
            hotkeys: Vec::new(),
            enabled: true,
        }
    }

    /// Check if hotkey manager is enabled
    pub fn is_enabled(&self) -> bool {
        self.enabled
    }

    /// Enable hotkey processing
    pub fn enable(&mut self) {
        self.enabled = true;
    }

    /// Disable hotkey processing
    pub fn disable(&mut self) {
        self.enabled = false;
    }

    /// Register a new hotkey
    pub fn register(&mut self, hotkey: Hotkey) -> bool {
        for existing in &self.hotkeys {
            if existing.matches(&hotkey.key, &hotkey.modifiers) {
                return false;
            }
        }
        self.hotkeys.push(hotkey);
        true
    }

    /// Unregister a hotkey
    pub fn unregister(&mut self, key: &str, modifiers: &HashSet<String>) -> bool {
        if let Some(pos) = self
            .hotkeys
            .iter()
            .position(|h| h.matches(key, modifiers))
        {
            self.hotkeys.remove(pos);
            true
        } else {
            false
        }
    }

    /// Check if a key combination matches any registered hotkey
    pub fn matches(&self, key: &str, modifiers: &HashSet<String>) -> bool {
        if !self.enabled {
            return false;
        }
        self.hotkeys.iter().any(|h| h.matches(key, modifiers))
    }

    /// List all registered hotkeys
    pub fn list_hotkeys(&self) -> &[Hotkey] {
        &self.hotkeys
    }
}

impl Default for HotkeyManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hotkey_matches() {
        let mut modifiers = HashSet::new();
        modifiers.insert("ctrl".to_string());
        
        let hotkey = Hotkey::new("a").with_modifier("ctrl");
        assert!(hotkey.matches("a", &modifiers));
        assert!(!hotkey.matches("b", &modifiers));
        assert!(!hotkey.matches("a", &HashSet::new()));
    }

    #[test]
    fn test_register_hotkey() {
        let mut manager = HotkeyManager::new();
        let hotkey = Hotkey::new("a").with_modifier("ctrl");
        assert!(manager.register(hotkey));
        assert_eq!(manager.list_hotkeys().len(), 1);
    }

    #[test]
    fn test_register_duplicate_hotkey() {
        let mut manager = HotkeyManager::new();
        let hotkey1 = Hotkey::new("a").with_modifier("ctrl");
        let hotkey2 = Hotkey::new("a").with_modifier("ctrl");
        manager.register(hotkey1);
        assert!(!manager.register(hotkey2));
        assert_eq!(manager.list_hotkeys().len(), 1);
    }

    #[test]
    fn test_unregister_hotkey() {
        let mut manager = HotkeyManager::new();
        let hotkey = Hotkey::new("a").with_modifier("ctrl");
        manager.register(hotkey);
        
        let mut modifiers = HashSet::new();
        modifiers.insert("ctrl".to_string());
        assert!(manager.unregister("a", &modifiers));
        assert_eq!(manager.list_hotkeys().len(), 0);
    }

    #[test]
    fn test_matches_when_disabled() {
        let mut manager = HotkeyManager::new();
        let hotkey = Hotkey::new("a");
        manager.register(hotkey);
        manager.disable();
        assert!(!manager.matches("a", &HashSet::new()));
    }
}

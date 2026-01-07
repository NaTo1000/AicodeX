//! Overlay module for AicodeX

/// Configuration for the overlay
#[derive(Debug, Clone)]
pub struct OverlayConfig {
    pub enabled: bool,
    pub opacity: f32,
    pub position_x: i32,
    pub position_y: i32,
    pub width: u32,
    pub height: u32,
}

impl Default for OverlayConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            opacity: 0.9,
            position_x: 0,
            position_y: 0,
            width: 800,
            height: 600,
        }
    }
}

/// Overlay manager for AicodeX
pub struct Overlay {
    config: OverlayConfig,
    visible: bool,
}

impl Overlay {
    /// Create a new overlay with default configuration
    pub fn new() -> Self {
        Self::with_config(OverlayConfig::default())
    }

    /// Create a new overlay with custom configuration
    pub fn with_config(config: OverlayConfig) -> Self {
        Self {
            config,
            visible: false,
        }
    }

    /// Check if overlay is currently visible
    pub fn is_visible(&self) -> bool {
        self.visible
    }

    /// Show the overlay
    pub fn show(&mut self) -> bool {
        if !self.config.enabled {
            return false;
        }
        self.visible = true;
        true
    }

    /// Hide the overlay
    pub fn hide(&mut self) -> bool {
        self.visible = false;
        true
    }

    /// Toggle overlay visibility
    pub fn toggle(&mut self) -> bool {
        if self.visible {
            self.hide()
        } else {
            self.show()
        }
    }

    /// Get the current configuration
    pub fn config(&self) -> &OverlayConfig {
        &self.config
    }
}

impl Default for Overlay {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = OverlayConfig::default();
        assert!(config.enabled);
        assert!((config.opacity - 0.9).abs() < f32::EPSILON);
        assert_eq!(config.width, 800);
        assert_eq!(config.height, 600);
    }

    #[test]
    fn test_overlay_initially_hidden() {
        let overlay = Overlay::new();
        assert!(!overlay.is_visible());
    }

    #[test]
    fn test_show_overlay() {
        let mut overlay = Overlay::new();
        assert!(overlay.show());
        assert!(overlay.is_visible());
    }

    #[test]
    fn test_hide_overlay() {
        let mut overlay = Overlay::new();
        overlay.show();
        assert!(overlay.hide());
        assert!(!overlay.is_visible());
    }

    #[test]
    fn test_toggle_overlay() {
        let mut overlay = Overlay::new();
        overlay.toggle();
        assert!(overlay.is_visible());
        overlay.toggle();
        assert!(!overlay.is_visible());
    }

    #[test]
    fn test_show_disabled_overlay() {
        let config = OverlayConfig {
            enabled: false,
            ..Default::default()
        };
        let mut overlay = Overlay::with_config(config);
        assert!(!overlay.show());
        assert!(!overlay.is_visible());
    }
}

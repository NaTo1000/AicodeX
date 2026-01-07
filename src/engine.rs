//! Core engine module

/// Main engine struct for AicodeX
pub struct Engine {
    running: bool,
}

impl Engine {
    /// Create a new engine instance
    pub fn new() -> Self {
        Self { running: false }
    }

    /// Start the engine
    pub fn start(&mut self) -> bool {
        self.running = true;
        true
    }

    /// Stop the engine
    pub fn stop(&mut self) -> bool {
        self.running = false;
        true
    }

    /// Check if engine is running
    pub fn is_running(&self) -> bool {
        self.running
    }

    /// Check if engine is ready
    pub fn is_ready(&self) -> bool {
        true
    }
}

impl Default for Engine {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_engine_new() {
        let engine = Engine::new();
        assert!(!engine.is_running());
        assert!(engine.is_ready());
    }

    #[test]
    fn test_engine_start_stop() {
        let mut engine = Engine::new();
        assert!(engine.start());
        assert!(engine.is_running());
        assert!(engine.stop());
        assert!(!engine.is_running());
    }
}

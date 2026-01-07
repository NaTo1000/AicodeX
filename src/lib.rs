use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct Config {
    pub hotkeys: std::collections::HashMap<String, String>,
    pub theme: String,
    pub opacity: f32,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            hotkeys: std::collections::HashMap::new(),
            theme: "dark".to_string(),
            opacity: 0.9,
        }
    }
}

pub struct Engine {
    config: Config,
    running: bool,
}

impl Engine {
    pub fn new(config: Config) -> Self {
        Self {
            config,
            running: false,
        }
    }

    pub fn start(&mut self) {
        self.running = true;
        println!("Engine started");
    }

    pub fn stop(&mut self) {
        self.running = false;
        println!("Engine stopped");
    }

    pub fn is_running(&self) -> bool {
        self.running
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_engine_creation() {
        let config = Config::default();
        let engine = Engine::new(config);
        assert!(!engine.is_running());
    }

    #[test]
    fn test_engine_start_stop() {
        let config = Config::default();
        let mut engine = Engine::new(config);
        engine.start();
        assert!(engine.is_running());
        engine.stop();
        assert!(!engine.is_running());
    }
}

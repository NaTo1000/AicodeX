//! AicodeX - A companion overlay code engine

pub mod engine;

pub use engine::Engine;

/// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

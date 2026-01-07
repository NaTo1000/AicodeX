//! AicodeX - A companion overlay code engine with hotkey-enabled features
//!
//! This library provides core functionality for the AicodeX application.

pub mod hotkey;
pub mod overlay;

/// Library version
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

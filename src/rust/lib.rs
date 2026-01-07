//! `AicodeX` - A companion overlay code engine
//!
//! This library provides core functionality for the `AicodeX` overlay code engine
//! with hotkey support and high customizability.

/// Returns the version of the `AicodeX` library
#[must_use]
pub fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

/// Greets a user with a message
///
/// # Arguments
///
/// * `name` - The name to greet
///
/// # Examples
///
/// ```
/// use aicodex::greet;
/// assert_eq!(greet("World"), "Hello, World from AicodeX!");
/// ```
#[must_use]
pub fn greet(name: &str) -> String {
    format!("Hello, {name} from AicodeX!")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version() {
        assert_eq!(version(), "0.1.0");
    }

    #[test]
    fn test_greet() {
        assert_eq!(greet("World"), "Hello, World from AicodeX!");
        assert_eq!(greet("Rust"), "Hello, Rust from AicodeX!");
    }
}

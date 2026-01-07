//! Integration tests for AicodeX Rust library

use aicodex::{greet, version};

#[test]
fn test_version_format() {
    let v = version();
    // Check that version follows semver format
    let parts: Vec<&str> = v.split('.').collect();
    assert_eq!(parts.len(), 3, "Version should have 3 parts");
}

#[test]
fn test_greet_integration() {
    let greeting = greet("Integration Test");
    assert!(greeting.contains("AicodeX"));
    assert!(greeting.contains("Integration Test"));
}

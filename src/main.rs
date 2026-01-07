//! Main binary for AicodeX

use aicodex::{Engine, VERSION};

fn main() {
    println!("AicodeX v{}", VERSION);
    let engine = Engine::new();
    println!("Engine initialized: {}", engine.is_ready());
}

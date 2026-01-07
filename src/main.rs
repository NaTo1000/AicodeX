use aicodex::{Config, Engine};

fn main() {
    println!("AicodeX v0.1.0");
    println!("Companion overlay code engine starting...");

    let config = Config::default();
    let mut engine = Engine::new(config);

    engine.start();
    println!("Engine running. Press Ctrl+C to exit.");

    // In a real application, we would have an event loop here
    // For now, just demonstrate the functionality
    std::thread::sleep(std::time::Duration::from_secs(1));

    engine.stop();
}

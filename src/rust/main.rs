//! `AicodeX` CLI - Main entry point

use aicodex::greet;

fn main() {
    println!("{}", greet("User"));
    println!("AicodeX v{}", aicodex::version());
}

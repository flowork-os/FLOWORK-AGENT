use std::net::TcpListener;
use std::sync::atomic::{AtomicU16, Ordering};

/// Dynamic port allocator for polyglot plugin engines
pub struct PortManager {
    last_port: AtomicU16,
}

impl PortManager {
    pub fn new() -> Self {
        Self {
            last_port: AtomicU16::new(18000),
        }
    }

    /// Allocate a guaranteed free ephemeral port from the OS
    pub fn allocate_free_port(&self) -> u16 {
        // Attempt OS ephemeral port binding (port 0 lets OS assign)
        if let Ok(listener) = TcpListener::bind("127.0.0.1:0") {
            if let Ok(addr) = listener.local_addr() {
                return addr.port();
            }
        }
        // Fallback to sequential increment
        self.last_port.fetch_add(1, Ordering::Relaxed)
    }
}

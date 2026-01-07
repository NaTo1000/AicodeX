"""Core engine module for AicodeX."""


class Engine:
    """Main engine class for AicodeX overlay code engine."""

    def __init__(self, config: dict = None):
        """Initialize the engine with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.running = False

    def start(self) -> bool:
        """Start the engine.
        
        Returns:
            True if started successfully
        """
        self.running = True
        return True

    def stop(self) -> bool:
        """Stop the engine.
        
        Returns:
            True if stopped successfully
        """
        self.running = False
        return True

    def is_running(self) -> bool:
        """Check if the engine is running.
        
        Returns:
            True if running
        """
        return self.running

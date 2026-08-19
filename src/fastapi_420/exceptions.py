"""Exceptions for fastapi-420."""

class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, limit: int, remaining: int, reset_time: float, retry_after: int = None):
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Limit: {limit}, Remaining: {remaining}")


class ConfigurationError(Exception):
    """Raised for configuration errors."""
    pass


class StorageError(Exception):
    """Raised for storage backend errors."""
    pass
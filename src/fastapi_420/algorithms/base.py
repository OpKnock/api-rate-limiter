"""Base rate limiting algorithm."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    limit: int
    remaining: int
    reset_time: float
    retry_after: Optional[int] = None


class BaseAlgorithm(ABC):
    """Base class for rate limiting algorithms."""
    
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
    
    @abstractmethod
    def check_limit(self, key: str, cost: int = 1) -> RateLimitResult:
        """Check if request is allowed and update counters."""
        pass
    
    @abstractmethod
    def reset(self, key: str) -> None:
        """Reset the rate limit for a key."""
        pass
    
    @abstractmethod
    def get_current_usage(self, key: str) -> int:
        """Get current usage for a key."""
        pass
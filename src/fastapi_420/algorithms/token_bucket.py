"""Token bucket rate limiting algorithm."""

import time
from threading import Lock
from typing import Dict

from fastapi_420.algorithms.base import BaseAlgorithm, RateLimitResult


class TokenBucketAlgorithm(BaseAlgorithm):
    """Token bucket rate limiting.
    
    Allows burst traffic up to bucket size, then enforces steady rate.
    Good for allowing occasional bursts while maintaining average rate.
    """
    
    def __init__(self, limit: int, window_seconds: int, burst: Optional[int] = None):
        super().__init__(limit, window_seconds)
        # Tokens per second
        self.rate = limit / window_seconds
        # Bucket size (allow bursts)
        self.capacity = burst or limit
        self._buckets: Dict[str, tuple[float, float]] = {}  # key -> (tokens, last_update)
        self._lock = Lock()
    
    def _get_bucket(self, key: str) -> tuple[float, float]:
        """Get or create bucket for key."""
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = (float(self.capacity), time.time())
            return self._buckets[key]
    
    def _refill(self, tokens: float, last_update: float) -> float:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - last_update
        new_tokens = tokens + elapsed * self.rate
        return min(new_tokens, self.capacity)
    
    def check_limit(self, key: str, cost: int = 1) -> RateLimitResult:
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = (float(self.capacity), time.time())
            
            tokens, last_update = self._buckets[key]
            tokens = self._refill(tokens, last_update)
            
            if tokens < cost:
                # Calculate retry time
                needed = cost - tokens
                retry_after = int(needed / self.rate) + 1
                reset_time = time.time() + retry_after
                return RateLimitResult(
                    allowed=False,
                    limit=self.limit,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after
                )
            
            tokens -= cost
            self._buckets[key] = (tokens, time.time())
            remaining = int(tokens)
            reset_time = time.time() + (self.capacity - tokens) / self.rate
            
            return RateLimitResult(
                allowed=True,
                limit=self.limit,
                remaining=remaining,
                reset_time=reset_time
            )
    
    def reset(self, key: str) -> None:
        with self._lock:
            if key in self._buckets:
                del self._buckets[key]
    
    def get_current_usage(self, key: str) -> int:
        with self._lock:
            if key not in self._buckets:
                return 0
            tokens, last_update = self._buckets[key]
            tokens = self._refill(tokens, last_update)
            return int(self.capacity - tokens)
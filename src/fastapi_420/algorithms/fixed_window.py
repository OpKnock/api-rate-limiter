"""Fixed window rate limiting algorithm."""

import time
from collections import defaultdict
from threading import Lock
from typing import Dict

from fastapi_420.algorithms.base import BaseAlgorithm, RateLimitResult


class FixedWindowAlgorithm(BaseAlgorithm):
    """Fixed window rate limiting.
    
    Divides time into fixed windows and counts requests per window.
    Simple but can allow bursts at window boundaries.
    """
    
    def __init__(self, limit: int, window_seconds: int):
        super().__init__(limit, window_seconds)
        self._counters: Dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))
        self._lock = Lock()
    
    def _get_window_start(self) -> float:
        """Get the start of the current window."""
        now = time.time()
        return now - (now % self.window_seconds)
    
    def check_limit(self, key: str, cost: int = 1) -> RateLimitResult:
        window_start = self._get_window_start()
        
        with self._lock:
            current_count, stored_window = self._counters[key]
            
            if stored_window != window_start:
                # New window, reset counter
                current_count = 0
                self._counters[key] = (0, window_start)
            
            if current_count + cost > self.limit:
                reset_time = window_start + self.window_seconds
                retry_after = int(reset_time - time.time()) + 1
                return RateLimitResult(
                    allowed=False,
                    limit=self.limit,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after
                )
            
            self._counters[key] = (current_count + cost, window_start)
            remaining = self.limit - current_count - cost
            reset_time = window_start + self.window_seconds
            
            return RateLimitResult(
                allowed=True,
                limit=self.limit,
                remaining=remaining,
                reset_time=reset_time
            )
    
    def reset(self, key: str) -> None:
        with self._lock:
            if key in self._counters:
                del self._counters[key]
    
    def get_current_usage(self, key: str) -> int:
        window_start = self._get_window_start()
        with self._lock:
            current_count, stored_window = self._counters.get(key, (0, 0.0))
            if stored_window != window_start:
                return 0
            return current_count
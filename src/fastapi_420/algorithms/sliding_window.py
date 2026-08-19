"""Sliding window rate limiting algorithm."""

import time
from collections import defaultdict
from threading import Lock
from typing import Deque, Dict
from collections import deque

from fastapi_420.algorithms.base import BaseAlgorithm, RateLimitResult


class SlidingWindowAlgorithm(BaseAlgorithm):
    """Sliding window rate limiting.
    
    Uses a sliding time window for more accurate rate limiting.
    Tracks individual request timestamps for precise limiting.
    """
    
    def __init__(self, limit: int, window_seconds: int):
        super().__init__(limit, window_seconds)
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = Lock()
    
    def _clean_old_requests(self, requests: Deque[float], now: float) -> None:
        """Remove requests older than the window."""
        cutoff = now - self.window_seconds
        while requests and requests[0] < cutoff:
            requests.popleft()
    
    def check_limit(self, key: str, cost: int = 1) -> RateLimitResult:
        now = time.time()
        
        with self._lock:
            requests = self._requests[key]
            self._clean_old_requests(requests, now)
            
            current_count = len(requests)
            
            if current_count + cost > self.limit:
                # Find when the oldest request will expire
                oldest = requests[0] if requests else now
                reset_time = oldest + self.window_seconds
                retry_after = int(reset_time - now) + 1
                return RateLimitResult(
                    allowed=False,
                    limit=self.limit,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after
                )
            
            # Add new request timestamps
            for _ in range(cost):
                requests.append(now)
            
            remaining = self.limit - current_count - cost
            # Reset time is when the oldest current request expires
            oldest = requests[0] if requests else now
            reset_time = oldest + self.window_seconds
            
            return RateLimitResult(
                allowed=True,
                limit=self.limit,
                remaining=remaining,
                reset_time=reset_time
            )
    
    def reset(self, key: str) -> None:
        with self._lock:
            if key in self._requests:
                del self._requests[key]
    
    def get_current_usage(self, key: str) -> int:
        now = time.time()
        with self._lock:
            requests = self._requests.get(key, deque())
            self._clean_old_requests(requests, now)
            return len(requests)
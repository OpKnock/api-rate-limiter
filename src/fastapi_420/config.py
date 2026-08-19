"""Configuration for the rate limiter."""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class RateLimiterSettings:
    """Settings for the rate limiter."""
    
    default_limit: str = "100/minute"
    redis_url: Optional[str] = None
    storage_backend: str = "memory"  # "memory" or "redis"
    default_fingerprint: str = "normal"  # "relaxed", "normal", "strict"
    enable_headers: bool = True
    header_prefix: str = "X-RateLimit"
    excluded_paths: list = field(default_factory=lambda: ["/health", "/metrics", "/docs", "/openapi.json"])
    scoped_limiters: Dict[str, str] = field(default_factory=dict)
    lua_scripts_path: Optional[str] = None
    
    def __post_init__(self):
        if self.storage_backend not in ("memory", "redis"):
            raise ValueError("storage_backend must be 'memory' or 'redis'")
        if self.default_fingerprint not in ("relaxed", "normal", "strict"):
            raise ValueError("default_fingerprint must be 'relaxed', 'normal', or 'strict'")
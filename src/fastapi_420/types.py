"""Type definitions for the rate limiter."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
import time


class FingerprintLevel(str, Enum):
    """Client fingerprint granularity levels."""
    RELAXED = "relaxed"   # IP only
    NORMAL = "normal"     # IP + User-Agent
    STRICT = "strict"     # IP + User-Agent + Auth headers


class AlgorithmType(str, Enum):
    """Rate limiting algorithm types."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitRule:
    """A single rate limit rule."""
    limit: str  # e.g., "100/minute", "1000/hour"
    algorithm: AlgorithmType = AlgorithmType.SLIDING_WINDOW
    scope: str = "default"
    fingerprint: FingerprintLevel = FingerprintLevel.NORMAL
    
    def parse_limit(self) -> tuple[int, int]:
        """Parse limit string into (requests, window_seconds)."""
        parts = self.limit.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid limit format: {self.limit}")
        requests = int(parts[0])
        window = parts[1].lower()
        if window.endswith("s") or window == "second":
            seconds = int(window.rstrip("s"))
        elif window.endswith("m") or window == "minute":
            seconds = int(window.rstrip("m")) * 60
        elif window.endswith("h") or window == "hour":
            seconds = int(window.rstrip("h")) * 3600
        elif window.endswith("d") or window == "day":
            seconds = int(window.rstrip("d")) * 86400
        else:
            raise ValueError(f"Invalid window: {window}")
        return requests, seconds


@dataclass
class RateLimitInfo:
    """Information about a rate limit check."""
    allowed: bool
    limit: int
    remaining: int
    reset_time: float
    retry_after: Optional[int] = None
    scope: str = "default"
    
    def to_headers(self, prefix: str = "X-RateLimit") -> Dict[str, str]:
        """Convert to rate limit headers."""
        return {
            f"{prefix}-Limit": str(self.limit),
            f"{prefix}-Remaining": str(max(0, self.remaining)),
            f"{prefix}-Reset": str(int(self.reset_time)),
        }


@dataclass
class ClientIdentity:
    """Client identity for fingerprinting."""
    ip: str
    user_agent: Optional[str] = None
    auth_header: Optional[str] = None
    custom: Dict[str, Any] = None
    
    def fingerprint(self, level: FingerprintLevel) -> str:
        """Generate fingerprint based on level."""
        parts = [self.ip]
        if level in (FingerprintLevel.NORMAL, FingerprintLevel.STRICT):
            if self.user_agent:
                parts.append(self.user_agent)
        if level == FingerprintLevel.STRICT:
            if self.auth_header:
                parts.append(self.auth_header)
            if self.custom:
                parts.append(str(sorted(self.custom.items())))
        return "|".join(parts)
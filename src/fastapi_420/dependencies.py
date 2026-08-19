"""FastAPI dependencies for rate limiting."""

from fastapi import Request, HTTPException, Depends
from typing import Callable, Optional

from fastapi_420.types import FingerprintLevel, RateLimitInfo
from fastapi_420.fingerprinting import CompositeFingerprinter, ClientIdentity
from fastapi_420.defense import DefenseLayer


class RateLimitDependency:
    """FastAPI dependency for rate limiting."""
    
    def __init__(
        self,
        limiter,
        fingerprint_level: FingerprintLevel = FingerprintLevel.NORMAL,
        scope: str = "default",
    ):
        self.limiter = limiter
        self.fingerprinter = CompositeFingerprinter(fingerprint_level)
        self.scope = scope
        self.defense = DefenseLayer()
    
    def extract_identity(self, request: Request) -> ClientIdentity:
        """Extract client identity from request."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            real_ip = request.headers.get("x-real-ip")
            ip = real_ip if real_ip else (request.client.host if request.client else "unknown")
        
        return ClientIdentity(
            ip=ip,
            user_agent=request.headers.get("user-agent"),
            auth_header=request.headers.get("authorization"),
        )
    
    async def __call__(self, request: Request) -> RateLimitInfo:
        identity = self.extract_identity(request)
        fingerprint = self.fingerprinter.fingerprint(identity)
        key = f"{self.scope}:{fingerprint}"
        
        # Check rate limit
        rule = self.limiter._get_rule(self.scope)
        rate_limit = self.limiter._check_limit(key, rule)
        
        # Run defense layers
        defense_result = self.defense.check(key, rate_limit)
        
        if not defense_result.allowed:
            if defense_result.circuit_breaker_open:
                raise HTTPException(
                    status_code=503,
                    detail="Service temporarily unavailable",
                    headers={"Retry-After": "30"}
                )
            else:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers=rate_limit.to_headers() if rate_limit else {}
                )
        
        return rate_limit


def create_rate_limit_dependency(
    limiter,
    fingerprint_level: FingerprintLevel = FingerprintLevel.NORMAL,
    scope: str = "default",
) -> Callable:
    """Create a rate limit dependency for FastAPI."""
    dep = RateLimitDependency(limiter, fingerprint_level, scope)
    return dep
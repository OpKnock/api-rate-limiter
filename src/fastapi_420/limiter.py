"""Main rate limiter for FastAPI."""

import time
import uuid
from typing import Dict, Optional, List, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi_420.config import RateLimiterSettings
from fastapi_420.types import (
    RateLimitRule,
    RateLimitInfo,
    FingerprintLevel,
    AlgorithmType,
    ClientIdentity,
)
from fastapi_420.algorithms import (
    FixedWindowAlgorithm,
    SlidingWindowAlgorithm,
    TokenBucketAlgorithm,
)
from fastapi_420.storage import MemoryStorage, RedisStorage
from fastapi_420.fingerprinting import CompositeFingerprinter, ClientIdentity as FPClientIdentity
from fastapi_420.defense import DefenseLayer


class RateLimiter:
    """Main rate limiter class for FastAPI."""
    
    def __init__(self, settings: RateLimiterSettings):
        self.settings = settings
        self._rules: Dict[str, RateLimitRule] = {}
        self._algorithms: Dict[str, object] = {}
        self._storage = self._create_storage()
        self._fingerprinter = CompositeFingerprinter(settings.default_fingerprint)
        self._defense = DefenseLayer()
        
        # Parse default limit
        default_rule = self._parse_limit(settings.default_limit)
        default_rule.scope = "default"
        self._rules["default"] = default_rule
        self._create_algorithm("default", default_rule)
    
    def _create_storage(self):
        if self.settings.storage_backend == "redis":
            if not self.settings.redis_url:
                raise ValueError("redis_url required for Redis storage")
            return RedisStorage(self.settings.redis_url)
        return MemoryStorage()
    
    def _parse_limit(self, limit_str: str) -> RateLimitRule:
        return RateLimitRule(limit=limit_str)
    
    def _create_algorithm(self, scope: str, rule: RateLimitRule):
        requests, window = rule.parse_limit()
        
        if rule.algorithm == AlgorithmType.FIXED_WINDOW:
            self._algorithms[scope] = FixedWindowAlgorithm(requests, window)
        elif rule.algorithm == AlgorithmType.SLIDING_WINDOW:
            self._algorithms[scope] = SlidingWindowAlgorithm(requests, window)
        elif rule.algorithm == AlgorithmType.TOKEN_BUCKET:
            self._algorithms[scope] = TokenBucketAlgorithm(requests, window)
        else:
            self._algorithms[scope] = SlidingWindowAlgorithm(requests, window)
    
    def add_rule(self, scope: str, limit: str, algorithm: AlgorithmType = AlgorithmType.SLIDING_WINDOW):
        """Add a scoped rate limit rule."""
        rule = RateLimitRule(limit=limit, algorithm=algorithm, scope=scope)
        self._rules[scope] = rule
        self._create_algorithm(scope, rule)
    
    def _get_rule(self, scope: str) -> RateLimitRule:
        return self._rules.get(scope, self._rules["default"])
    
    def _get_algorithm(self, scope: str):
        return self._algorithms.get(scope, self._algorithms["default"])
    
    def _check_limit(self, key: str, rule: RateLimitRule) -> RateLimitInfo:
        algorithm = self._algorithms.get(rule.scope, self._algorithms["default"])
        return algorithm.check_limit(key)
    
    def _extract_identity(self, request: Request) -> FPClientIdentity:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            real_ip = request.headers.get("x-real-ip")
            ip = real_ip if real_ip else (request.client.host if request.client else "unknown")
        
        return FPClientIdentity(
            ip=ip,
            user_agent=request.headers.get("user-agent"),
            auth_header=request.headers.get("authorization"),
        )
    
    def _get_fingerprint(self, request: Request) -> str:
        identity = self._extract_identity(request)
        return self._fingerprinter.fingerprint(identity)
    
    def check_limit(self, request: Request, scope: str = "default") -> RateLimitInfo:
        """Check rate limit for a request."""
        fingerprint = self._get_fingerprint(request)
        key = f"{scope}:{fingerprint}"
        rule = self._get_rule(scope)
        
        rate_limit = self._check_limit(key, rule)
        
        # Run defense layers
        defense_result = self._defense.check(key, rate_limit)
        
        if not defense_result.allowed:
            return defense_result.rate_limit
        
        return rate_limit
    
    def middleware(self):
        """Return ASGI middleware for automatic rate limiting."""
        return RateLimitMiddleware(self)
    
    def limit(self, scope: str = "default"):
        """Decorator for endpoint-specific rate limiting."""
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                request = kwargs.get("request")
                if not request:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                
                if request:
                    rate_limit = self.check_limit(request, scope)
                    if not rate_limit.allowed:
                        from fastapi import HTTPException
                        raise HTTPException(
                            status_code=429,
                            detail="Rate limit exceeded",
                            headers=rate_limit.to_headers()
                        )
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator


class RateLimitMiddleware(BaseHTTPMiddleware):
    """ASGI middleware for automatic rate limiting."""
    
    def __init__(self, app, limiter: RateLimiter):
        super().__init__(app)
        self.limiter = limiter
    
    async def dispatch(self, request: Request, call_next):
        # Skip excluded paths
        for path in self.limiter.settings.excluded_paths:
            if request.url.path.startswith(path):
                return await call_next(request)
        
        rate_limit = self.limiter.check_limit(request)
        
        # Add rate limit headers
        response = await call_next(request)
        
        if self.limiter.settings.enable_headers:
            headers = rate_limit.to_headers(self.limiter.settings.header_prefix)
            for k, v in headers.items():
                response.headers[k] = v
            
            if not rate_limit.allowed:
                response.headers["Retry-After"] = str(rate_limit.retry_after or 1)
        
        if not rate_limit.allowed:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers=rate_limit.to_headers(self.limiter.settings.header_prefix)
            )
        
        return response
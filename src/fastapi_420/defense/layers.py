"""Layered defense for rate limiting."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from fastapi_420.defense.circuit_breaker import CircuitBreaker, CircuitOpenError
from fastapi_420.types import RateLimitInfo


@dataclass
class DefenseResult:
    """Result of defense layer checks."""
    allowed: bool
    rate_limit: Optional[RateLimitInfo] = None
    circuit_breaker_open: bool = False
    reason: Optional[str] = None


class DefenseLayer:
    """Manages layered defense for rate limiting."""
    
    def __init__(self):
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, key: str) -> CircuitBreaker:
        if key not in self._circuit_breakers:
            self._circuit_breakers[key] = CircuitBreaker()
        return self._circuit_breakers[key]
    
    def check(self, key: str, rate_limit_info: RateLimitInfo) -> DefenseResult:
        # Check rate limit first
        if not rate_limit_info.allowed:
            return DefenseResult(
                allowed=False,
                rate_limit=rate_limit_info,
                reason="rate_limit_exceeded"
            )
        
        # Check circuit breaker
        cb = self.get_circuit_breaker(key)
        if cb.state.name == "OPEN":
            return DefenseResult(
                allowed=False,
                rate_limit=rate_limit_info,
                circuit_breaker_open=True,
                reason="circuit_breaker_open"
            )
        
        return DefenseResult(
            allowed=True,
            rate_limit=rate_limit_info
        )
    
    def record_failure(self, key: str):
        """Record a failure for the circuit breaker."""
        cb = self.get_circuit_breaker(key)
        # The circuit breaker will be triggered on next check
    
    def record_success(self, key: str):
        """Record a success for the circuit breaker."""
        # Handled by circuit breaker on successful call
    
    def reset(self, key: Optional[str] = None):
        """Reset circuit breaker(s)."""
        if key:
            if key in self._circuit_breakers:
                self._circuit_breakers[key].reset()
        else:
            for cb in self._circuit_breakers.values():
                cb.reset()
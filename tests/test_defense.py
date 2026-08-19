"""Tests for defense mechanisms."""

import pytest
import time

from fastapi_420.defense import CircuitBreaker, DefenseLayer, CircuitOpenError


class TestCircuitBreaker:
    def test_closed_by_default(self):
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state.name == "CLOSED"
    
    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        
        def fail():
            raise ValueError("fail")
        
        for i in range(3):
            with pytest.raises(ValueError):
                cb.call(fail)
        
        assert cb.state.name == "OPEN"
    
    def test_rejects_when_open(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60)
        
        def fail():
            raise ValueError("fail")
        
        with pytest.raises(ValueError):
            cb.call(fail)
        
        assert cb.state.name == "OPEN"
        
        with pytest.raises(CircuitOpenError):
            cb.call(lambda: "success")
    
    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        def fail():
            raise ValueError("fail")
        
        with pytest.raises(ValueError):
            cb.call(fail)
        
        assert cb.state.name == "OPEN"
        time.sleep(0.15)
        assert cb.state.name == "HALF_OPEN"
    
    def test_success_resets(self):
        cb = CircuitBreaker(failure_threshold=3)
        
        def fail():
            raise ValueError("fail")
        
        for i in range(2):
            with pytest.raises(ValueError):
                cb.call(fail)
        
        assert cb.state.name == "CLOSED"
        cb.call(lambda: "success")
        assert cb.state.name == "CLOSED"
        assert cb._failure_count == 0


class TestDefenseLayer:
    def test_allows_when_rate_limit_ok(self):
        layer = DefenseLayer()
        from fastapi_420.types import RateLimitInfo
        
        rate_limit = RateLimitInfo(allowed=True, limit=100, remaining=50, reset_time=time.time() + 60)
        result = layer.check("test", rate_limit)
        
        assert result.allowed is True
        assert result.rate_limit == rate_limit
    
    def test_blocks_when_rate_limit_exceeded(self):
        layer = DefenseLayer()
        from fastapi_420.types import RateLimitInfo
        
        rate_limit = RateLimitInfo(allowed=False, limit=100, remaining=0, reset_time=time.time() + 60)
        result = layer.check("test", rate_limit)
        
        assert result.allowed is False
        assert result.reason == "rate_limit_exceeded"
    
    def test_blocks_when_circuit_open(self):
        layer = DefenseLayer()
        from fastapi_420.types import RateLimitInfo
        
        cb = layer.get_circuit_breaker("test")
        cb._state = type('obj', (object,), {'name': 'OPEN'})()
        
        rate_limit = RateLimitInfo(allowed=True, limit=100, remaining=50, reset_time=time.time() + 60)
        result = layer.check("test", rate_limit)
        
        assert result.allowed is False
        assert result.circuit_breaker_open is True
        assert result.reason == "circuit_breaker_open"
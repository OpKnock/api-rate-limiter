"""Tests for rate limiting algorithms."""

import pytest
import time

from fastapi_420.algorithms import (
    FixedWindowAlgorithm,
    SlidingWindowAlgorithm,
    TokenBucketAlgorithm,
)
from fastapi_420.types import AlgorithmType


class TestFixedWindowAlgorithm:
    def test_allows_within_limit(self):
        algo = FixedWindowAlgorithm(limit=5, window_seconds=60)
        for i in range(5):
            result = algo.check_limit("test_key")
            assert result.allowed is True
            assert result.remaining == 4 - i
    
    def test_blocks_over_limit(self):
        algo = FixedWindowAlgorithm(limit=3, window_seconds=60)
        for i in range(3):
            result = algo.check_limit("test_key")
            assert result.allowed is True
        
        result = algo.check_limit("test_key")
        assert result.allowed is False
        assert result.remaining == 0
    
    def test_resets_after_window(self):
        algo = FixedWindowAlgorithm(limit=2, window_seconds=1)
        algo.check_limit("test_key")
        algo.check_limit("test_key")
        
        result = algo.check_limit("test_key")
        assert result.allowed is False
        
        time.sleep(1.1)
        result = algo.check_limit("test_key")
        assert result.allowed is True


class TestSlidingWindowAlgorithm:
    def test_allows_within_limit(self):
        algo = SlidingWindowAlgorithm(limit=5, window_seconds=60)
        for i in range(5):
            result = algo.check_limit("test_key")
            assert result.allowed is True
    
    def test_blocks_over_limit(self):
        algo = SlidingWindowAlgorithm(limit=3, window_seconds=60)
        for i in range(3):
            assert algo.check_limit("test_key").allowed is True
        
        assert algo.check_limit("test_key").allowed is False
    
    def test_sliding_behavior(self):
        algo = SlidingWindowAlgorithm(limit=2, window_seconds=1)
        assert algo.check_limit("test_key").allowed is True
        assert algo.check_limit("test_key").allowed is True
        assert algo.check_limit("test_key").allowed is False
        
        time.sleep(1.1)
        assert algo.check_limit("test_key").allowed is True


class TestTokenBucketAlgorithm:
    def test_allows_burst(self):
        algo = TokenBucketAlgorithm(limit=10, window_seconds=10, burst=5)
        # Should allow up to burst
        for i in range(5):
            assert algo.check_limit("test_key").allowed is True
        
        # Next should be blocked
        assert algo.check_limit("test_key").allowed is False
    
    def test_refills_over_time(self):
        algo = TokenBucketAlgorithm(limit=10, window_seconds=1, burst=2)
        assert algo.check_limit("test_key").allowed is True
        assert algo.check_limit("test_key").allowed is True
        assert algo.check_limit("test_key").allowed is False
        
        time.sleep(1.5)
        assert algo.check_limit("test_key").allowed is True
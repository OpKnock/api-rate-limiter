"""Redis storage backend for rate limiting."""

import json
from typing import Any, Dict, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class RedisStorage:
    """Redis-backed storage for distributed rate limiting."""
    
    def __init__(self, url: str = "redis://localhost:6379/0", **kwargs):
        if not REDIS_AVAILABLE:
            raise RuntimeError("redis-py not installed. Install with: pip install redis")
        
        self._client = redis.from_url(url, decode_responses=True, **kwargs)
        self._kwargs = kwargs
    
    def get(self, key: str) -> Any:
        data = self._client.get(key)
        if data is None:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        data = json.dumps(value) if not isinstance(value, str) else value
        if ttl:
            self._client.setex(key, ttl, data)
        else:
            self._client.set(key, data)
    
    def delete(self, key: str) -> None:
        self._client.delete(key)
    
    def exists(self, key: str) -> bool:
        return self._client.exists(key) > 0
    
    def increment(self, key: str, amount: int = 1) -> int:
        return self._client.incrby(key, amount)
    
    def get_all(self, prefix: str = "") -> Dict[str, Any]:
        pattern = f"{prefix}*" if prefix else "*"
        keys = self._client.keys(pattern)
        if not keys:
            return {}
        pipe = self._client.mget(keys)
        result = {}
        for k, v in zip(keys, pipe):
            if v is not None:
                try:
                    result[k] = json.loads(v)
                except json.JSONDecodeError:
                    result[k] = v
        return result
    
    def clear(self) -> None:
        self._client.flushdb()
    
    def ping(self) -> bool:
        try:
            return self._client.ping()
        except Exception:
            return False
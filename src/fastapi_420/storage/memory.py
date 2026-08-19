"""In-memory storage backend for rate limiting."""

from typing import Any, Dict, Optional
from threading import Lock


class MemoryStorage:
    """Thread-safe in-memory storage for rate limiting data."""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Any:
        with self._lock:
            return self._data.get(key)
    
    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
    
    def delete(self, key: str) -> None:
        with self._lock:
            if key in self._data:
                del self._data[key]
    
    def exists(self, key: str) -> bool:
        with self._lock:
            return key in self._data
    
    def increment(self, key: str, amount: int = 1) -> int:
        with self._lock:
            current = self._data.get(key, 0)
            new_value = current + amount
            self._data[key] = new_value
            return new_value
    
    def get_all(self, prefix: str = "") -> Dict[str, Any]:
        with self._lock:
            if prefix:
                return {k: v for k, v in self._data.items() if k.startswith(prefix)}
            return dict(self._data)
    
    def clear(self) -> None:
        with self._lock:
            self._data.clear()
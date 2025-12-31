import time
from typing import Any
import threading

class TTLCache:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self.store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.RLock()
        
    def get(self, key: str):
        with self._lock:
            data = self.store.get(key)
            if not data:
                return None

            timestamp, value = data
            if time.time() - timestamp > self.ttl:
                self.store.pop(key, None)
                return None

            return value
    
    def set(self, key: str, value: Any):
        with self._lock:
            self.store[key] = (time.time(), value)
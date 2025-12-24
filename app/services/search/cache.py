import time
from typing import Any

class TTLCache:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self.store: dict[str, tuple[float, Any]] = {}
        
    def get(self, key: str):
        data = self.store.get(key)
        if not data:
            return None
        
        timestamp, value = data
        if time.time() - timestamp > self.ttl:
            del self.store[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any):
        self.store[key] = (time.time(), value)
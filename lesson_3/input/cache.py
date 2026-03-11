import time
from dataclasses import dataclass, field


@dataclass
class Cache:
    ttl_seconds: int = 300
    _store: dict = field(default_factory=dict, init=False, repr=False)

    def get(self, key: str):
        if key in self._store:
            value, timestamp = self._store[key]
            if time.time() - timestamp < self.ttl_seconds:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value) -> None:
        self._store[key] = (value, time.time())

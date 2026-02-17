import time
from collections import defaultdict
from typing import Optional


class CircuitBreaker:
    STATE_CLOSED = "closed"
    STATE_OPEN = "open"
    STATE_HALF_OPEN = "half_open"

    def __init__(self, failure_threshold: int = 3, cooldown_s: float = 30.0):
        self.failure_threshold = failure_threshold
        self.cooldown_s = cooldown_s
        self._failures: dict[str, int] = defaultdict(int)
        self._state: dict[str, str] = {}
        self._opened_at: dict[str, float] = {}
        self.trips_total: int = 0

    def state(self, key: str) -> str:
        s = self._state.get(key, self.STATE_CLOSED)
        if s == self.STATE_OPEN:
            if time.perf_counter() - self._opened_at[key] > self.cooldown_s:
                self._state[key] = self.STATE_HALF_OPEN
                return self.STATE_HALF_OPEN
        return s

    def is_available(self, key: str) -> bool:
        return self.state(key) != self.STATE_OPEN

    def record_success(self, key: str):
        self._failures[key] = 0
        self._state[key] = self.STATE_CLOSED

    def record_failure(self, key: str):
        self._failures[key] += 1
        if self._failures[key] >= self.failure_threshold:
            self._state[key] = self.STATE_OPEN
            self._opened_at[key] = time.perf_counter()
            self.trips_total += 1

    def get_states(self) -> dict[str, dict]:
        all_keys = set(self._state.keys()) | set(self._failures.keys())
        result = {}
        for key in all_keys:
            result[key] = {
                'state': self.state(key),
                'consecutive_failures': self._failures.get(key, 0),
            }
        return result

    def reset(self):
        self._failures.clear()
        self._state.clear()
        self._opened_at.clear()
        self.trips_total = 0


class ResponseCache:
    def __init__(self, ttl_s: float = 60.0):
        self.ttl_s = ttl_s
        self._cache: dict[str, tuple[str, float]] = {}

    def get(self, key: str) -> Optional[str]:
        entry = self._cache.get(key)
        if entry is None:
            return None
        value, timestamp = entry
        if time.perf_counter() - timestamp > self.ttl_s:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: str):
        self._cache[key] = (value, time.perf_counter())

    def clear(self):
        self._cache.clear()

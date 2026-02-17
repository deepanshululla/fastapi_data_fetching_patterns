import asyncio
import math
import time
from collections import defaultdict
from typing import Callable, Optional
import httpx
from resilience import CircuitBreaker


def percentile(sorted_data: list[float], p: float) -> float:
    if not sorted_data:
        return 0
    k = (len(sorted_data) - 1) * (p / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


class RetryStats:
    def __init__(self):
        self.calls_total: int = 0
        self.retries_total: int = 0
        self.attempts: int = 0
        self.failures: int = 0
        self.successes: int = 0
        self.total_chars: int = 0
        self.char_distribution: dict[str, int] = defaultdict(int)
        self.longest_line: str = ""
        self.timeouts: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.circuit_breaker_skips: int = 0
        self.response_times_ms: list[float] = []

    def record_response(self, data: str):
        self.total_chars += len(data)
        for ch in data:
            self.char_distribution[ch] += 1
        for line in data.splitlines():
            if len(line) > len(self.longest_line):
                self.longest_line = line

    def to_dict(self, circuit_breaker: Optional['CircuitBreaker'] = None) -> dict:
        times = self.response_times_ms
        sorted_times = sorted(times)
        result = {
            'calls_total': self.calls_total,
            'successes': self.successes,
            'retries_total': self.retries_total,
            'attempts': self.attempts,
            'failures': self.failures,
            'timeouts': self.timeouts,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_ratio': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            'circuit_breaker_skips': self.circuit_breaker_skips,
            'total_chars': self.total_chars,
            'char_distribution': dict(self.char_distribution),
            'longest_line': self.longest_line,
            'response_times_ms': {
                'min': min(times) if times else 0,
                'avg': sum(times) / len(times) if times else 0,
                'max': max(times) if times else 0,
                'p50': percentile(sorted_times, 50),
                'p95': percentile(sorted_times, 95),
                'p99': percentile(sorted_times, 99),
            },
        }
        if circuit_breaker:
            result['circuit_breaker'] = {
                'trips_total': circuit_breaker.trips_total,
                'sources': circuit_breaker.get_states(),
            }
        return result


async def retry(
        fn: Callable[[], object],
        *args,
        max_attempts: int = 3,
        delay_s: int,
        retry_on,
        stats: RetryStats
):
    if stats:
        stats.calls_total += 1

    for attempt in range(1, max_attempts+1):
        try:
            stats.attempts += 1

            start = time.perf_counter()
            result = await fn(*args)
            elapsed_ms = (time.perf_counter() - start) * 1000
            stats.response_times_ms.append(elapsed_ms)
            stats.successes += 1
            if isinstance(result, str):
                stats.record_response(result)
            return result
        except retry_on as e:
            if isinstance(e, httpx.TimeoutException):
                print(f'timeout: {e}')
                stats.timeouts += 1
            else:
                print(f'exception: {e}')

            if attempt == max_attempts:
                stats.failures += 1
                raise Exception("Failed after too many retries")
            if stats:
                stats.retries_total += 1
                await asyncio.sleep(delay_s)

    raise Exception("Unreachable place")

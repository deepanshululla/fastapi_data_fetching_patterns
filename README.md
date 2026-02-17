# fastapi_data_fetching_patterns

A FastAPI web server that fetches data from distributed sources with retry logic, caching, circuit breaking, and detailed statistics tracking.

## Project Structure

```
main.py               - FastAPI app and endpoints
get_data.py           - Data fetching from random sources
statistics_helper.py  - RetryStats, retry logic, percentile calculations
resilience.py         - ResponseCache and CircuitBreaker
client_test.py        - Async test client (50 sequential requests with stats)
```

## Setup

```bash
uv sync
```

## Running

Start the server:

```bash
uv run uvicorn main:app --reload
```

Run the test client:

```bash
uv run client_test.py
```

## Endpoints

### `GET /fetch`

Fetches data from a randomly selected source with retry logic.

| Parameter    | Type   | Default | Description                                      |
|-------------|--------|---------|--------------------------------------------------|
| `timeout_ms` | int    | 5000    | Request timeout in milliseconds                  |
| `retry_on`   | string | "all"   | Exception filter: `all`, `timeout`, `connection`, `http_status` |

### `GET /stats`

Returns all tracked statistics:

- **Calls**: total, successes, failures, retries, attempts
- **Timeouts**: count of timed-out requests
- **Cache**: hits, misses, hit ratio
- **Circuit breaker**: skips, trips, per-source state
- **Content**: total characters, character distribution, longest line
- **Response times**: min, avg, max, p50, p95, p99

### `GET /reset`

Resets all statistics, cache, and circuit breaker state.

## Features

### Retry Logic

Configurable retry with async sleep between attempts. Max 3 attempts per request. The `retry_on` parameter controls which exception types trigger retries.

### Response Cache

TTL-based cache (60s) keyed by source URL. Caches raw responses before minute-based multiplication. Toggle with `CACHE_ENABLED` in `main.py`.

### Circuit Breaker

Per-source circuit breaker that stops requests to failing sources:

- **Closed** (healthy): requests flow normally
- **Open** (tripped): after 3 consecutive failures, source is skipped for 30s
- **Half-open** (probing): after cooldown, one request is allowed to test recovery

Toggle with `CIRCUIT_BREAKER_ENABLED` in `main.py`.

### Statistics

Tracks response times with percentile calculations (p50, p95, p99), character frequency distribution, cache hit ratios, and circuit breaker state per source.

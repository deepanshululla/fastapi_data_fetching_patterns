import httpx
from fastapi import FastAPI
from typing import Optional
from get_data import get_data
from resilience import ResponseCache, CircuitBreaker
from statistics_helper import retry, RetryStats

RETRY_ON_OPTIONS = {
    "all": Exception,
    "timeout": httpx.TimeoutException,
    "connection": httpx.ConnectError,
    "http_status": httpx.HTTPStatusError,
}


# Create an instance of the FastAPI app
app = FastAPI()
retry_stats = RetryStats()
response_cache = ResponseCache(ttl_s=60.0)
circuit_breaker = CircuitBreaker(failure_threshold=3, cooldown_s=30.0)

# Define a GET route for the root URL ("/")
@app.get("/")
async def read_root():
    return {"Hello": "World"}

# Define a GET route with a path parameter (item_id) 
# and an optional query parameter (q)
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}


CACHE_ENABLED = True
CIRCUIT_BREAKER_ENABLED = True

@app.get("/fetch")
async def fetch(timeout_ms: int = 5000, retry_on: str = "all"):
    timeout_s = timeout_ms / 1000.0
    retry_on_exc = RETRY_ON_OPTIONS.get(retry_on, Exception)
    def print_result(data: str) -> str:
       print(f"Received {len(data)} characters")
       print(f"First 100 chars: {data[:100]}")
       return data
    return await retry(
        get_data,
        print_result,
        timeout_s,
        response_cache if CACHE_ENABLED else None,
        retry_stats,
        circuit_breaker if CIRCUIT_BREAKER_ENABLED else None,
        delay_s=0,
        retry_on=retry_on_exc,
        stats=retry_stats
        )

@app.get("/stats")
async def stats():
    return retry_stats.to_dict(circuit_breaker=circuit_breaker)

@app.get("/reset")
async def reset():
    global retry_stats, response_cache, circuit_breaker
    retry_stats = RetryStats()
    response_cache = ResponseCache(ttl_s=60.0)
    circuit_breaker = CircuitBreaker(failure_threshold=3, cooldown_s=30.0)
    return True

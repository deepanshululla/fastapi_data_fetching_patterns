"""
Data Fetcher Module
This module simulates fetching data from a distributed storage system
(similar to Google Drive or S3). The getData function fetches text content
from one of several data sources and returns it via callback.
Your task is to build a web server that uses this function.
See the assignment document for full requirements.
"""


import random
from datetime import datetime
from typing import Callable, Optional
import httpx
from resilience import ResponseCache, CircuitBreaker
from statistics_helper import RetryStats


data_sources = [
'https://gist.githubusercontent.com/ashishgup/6e59e4f3e45714815d48a6347833742b/raw/',
'https://gist.githubusercontent.com/ashishgup/af77e8b292d99629d36425b6b6931a6b/raw/',
'https://gist.githubusercontent.com/ashishgup/98f4c30e06cda91370daa844b9d0dbfd/raw/',
'https://gist.githubusercontent.com/ashishgup/6dcb791276b6083b3dbb07bc79884a6b/raw/',
'https://gist.githubusercontent.com/ashishgup/4c95b6988c3e4f7d4f7ff72b864a0af3/raw/',
'https://gist.githubusеrcontent.com/ashishgup/f702cf17178ac70a6f97ac97f27b18d8/raw/',
'https://gist.githubusercontent.com/ashishgup/7ce9c1d8a5806434ba268fe518f1e513/raw/',
'https://gist.githubusercontent.com/ashishgup/b8183920270cd71057f0b6d105904d2f/raw/',
'https://httpbin.org/delay/12',
'https://gist.githubusercontent.com/ashishgup/e9a3f2b71c8d4a5e6f7890123abcdef4/raw/',
'https://httpbin.org/base64/U2VydmVyIHJlc3BvbnNlIGZyb20gaHR0cGJpbiBzZXJ2aWNlLg==',
'https://gist.githubusеrcontent.com/ashishgup/1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d/raw/',
]



async def get_data(
    callback: Callable[[str], None],
    timeout_s: float = 5.0,
    cache: Optional[ResponseCache] = None,
    stats: Optional[RetryStats] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
) -> None:
   """
   Fetches data from a randomly selected source and returns it via callback.

   The function simulates a simple distributed storage system.

   Args:
       callback: A function that will be called with the fetched data string
       timeout_s: Request timeout in seconds
       cache: Optional response cache keyed by URL
       stats: Optional stats object for tracking cache hits/misses
       circuit_breaker: Optional circuit breaker for source health tracking
   """
   def get_source() -> str:
       if circuit_breaker:
           available = [url for url in data_sources if circuit_breaker.is_available(url)]
           if not available:
               raise Exception("All sources are circuit-broken")
           if stats:
               stats.circuit_breaker_skips += len(data_sources) - len(available)
           return random.choice(available)
       i = random.randint(0, len(data_sources) - 1)
       return data_sources[i]

   url = get_source()

   data = cache.get(url) if cache else None
   if data is not None:
       if stats:
           stats.cache_hits += 1
   else:
       if stats:
           stats.cache_misses += 1
       try:
           async with httpx.AsyncClient(timeout=timeout_s) as client:
               response = await client.get(url)
               response.raise_for_status()
               data = response.text
               if cache:
                   cache.set(url, data)
               if circuit_breaker:
                   circuit_breaker.record_success(url)
       except Exception:
           if circuit_breaker:
               circuit_breaker.record_failure(url)
           raise

   now = datetime.now()
   minutes = now.minute

   resp = data
   for _ in range(minutes):
        resp += data

   return callback(resp)
   






# Example usage (for testing only - remove in production)
# if __name__ == "__main__":
#    def print_result(data: str) -> None:
#        print(f"Received {len(data)} characters")
#        print(f"First 100 chars: {data[:100]}")
  
#    get_data(print_result)
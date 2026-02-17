import asyncio
import time
import httpx

BASE_URL = "http://127.0.0.1:8000"
TOTAL_REQUESTS = 50


async def fetch_one(client: httpx.AsyncClient, i: int) -> bool:
    try:
        response = await client.get(f"{BASE_URL}/fetch")
        response.raise_for_status()
        print(f"[{i+1}] success ({response.status_code})")
        return True
    except Exception as e:
        print(f"[{i+1}] failure ({e})")
        return False


async def main():
    start = time.perf_counter()

    async with httpx.AsyncClient(timeout=30.0) as client:
        results = []
        for i in range(TOTAL_REQUESTS):
            result = await fetch_one(client, i)
            results.append(result)
            stats = await client.get(f"{BASE_URL}/stats")
            s = stats.json()
            rt = s['response_times_ms']
            cb = s.get('circuit_breaker', {})
            open_count = sum(1 for src in cb.get('sources', {}).values() if src['state'] == 'open')
            print(f"  stats: successes={s['successes']} failures={s['failures']} "
                  f"retries={s['retries_total']} timeouts={s['timeouts']} "
                  f"cache={s['cache_hits']}/{s['cache_hits']+s['cache_misses']} "
                  f"cb_skips={s['circuit_breaker_skips']} cb_open={open_count} "
                  f"avg={rt['avg']:.1f}ms p50={rt['p50']:.1f}ms p95={rt['p95']:.1f}ms")

    elapsed = time.perf_counter() - start
    successes = sum(results)
    failures = TOTAL_REQUESTS - successes

    print(f"\n--- Summary ---")
    print(f"Total requests: {TOTAL_REQUESTS}")
    print(f"Successes:      {successes}")
    print(f"Failures:       {failures}")
    print(f"Total time:     {elapsed:.2f}s")

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/stats")
        s = resp.json()
        rt = s['response_times_ms']
        cb = s.get('circuit_breaker', {})

        print(f"\n--- Server Stats ---")
        print(f"  Calls:      {s['calls_total']}")
        print(f"  Successes:  {s['successes']}")
        print(f"  Failures:   {s['failures']}")
        print(f"  Retries:    {s['retries_total']} (across {s['attempts']} attempts)")
        print(f"  Timeouts:   {s['timeouts']}")
        print(f"\n--- Cache ---")
        print(f"  Hits:       {s['cache_hits']}")
        print(f"  Misses:     {s['cache_misses']}")
        print(f"  Hit ratio:  {s['cache_hit_ratio']:.2%}")
        print(f"\n--- Circuit Breaker ---")
        print(f"  Trips:      {cb.get('trips_total', 0)}")
        print(f"  Skips:      {s['circuit_breaker_skips']}")
        for url, state in cb.get('sources', {}).items():
            print(f"  {url}: {state['state']} ({state['consecutive_failures']} failures)")
        print(f"\n--- Response Times ---")
        print(f"  Min:  {rt['min']:.1f}ms")
        print(f"  Avg:  {rt['avg']:.1f}ms")
        print(f"  P50:  {rt['p50']:.1f}ms")
        print(f"  P95:  {rt['p95']:.1f}ms")
        print(f"  P99:  {rt['p99']:.1f}ms")
        print(f"  Max:  {rt['max']:.1f}ms")
        print(f"\n--- Content ---")
        print(f"  Total chars:   {s['total_chars']}")
        print(f"  Longest line:  {len(s['longest_line'])} chars")


asyncio.run(main())

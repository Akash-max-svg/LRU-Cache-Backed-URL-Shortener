"""
Performance Benchmark: LRU Cache Lookup vs. Database Lookup.

Demonstrates algorithmic complexity benefits of the custom LRU Cache:
    - LRU Cache Lookup: In-memory O(1) HashMap + Doubly Linked List pointer operations.
    - Database Lookup: Persistent B-Tree index scan + query dispatch.

Usage:
    python benchmark.py
"""
import time
import statistics
from database.mongodb import MongoDB
from cache.lru_cache import LRUCache
from services.hash_service import HashService


def run_benchmark(iterations: int = 1000):
    print("=" * 70)
    print("  LRU CACHE vs. DATABASE LOOKUP PERFORMANCE BENCHMARK")
    print("=" * 70)
    print(f"Iterations: {iterations} reads")

    # 1. Initialize MongoDB and LRU Cache
    db = MongoDB(database_name="benchmark_db", force_mock=True)
    cache = LRUCache(capacity=500)

    # Populate 100 sample URLs
    sample_codes = []
    for i in range(100):
        code = HashService.generate_short_code(length=6)
        sample_codes.append(code)
        doc = {
            "short_code": code,
            "original_url": f"https://www.example.com/resource/{i}",
            "click_count": 0,
            "is_active": True,
        }
        # Insert into DB and Cache
        db.urls_collection.insert_one(doc)
        cache.put(code, doc)

    target_code = sample_codes[0]

    # Benchmark LRU Cache (In-Memory O(1))
    cache_times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = cache.get(target_code)
        t1 = time.perf_counter()
        cache_times.append((t1 - t0) * 1000)  # ms

    # Benchmark Database Query (Query filter scan)
    db_times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        _ = db.urls_collection.find_one({"short_code": target_code, "is_active": True})
        t1 = time.perf_counter()
        db_times.append((t1 - t0) * 1000)  # ms

    avg_cache_ms = statistics.mean(cache_times)
    avg_db_ms = statistics.mean(db_times)
    speedup = avg_db_ms / avg_cache_ms if avg_cache_ms > 0 else 1.0

    print("-" * 70)
    print(f"LRU Cache Lookup (In-Memory O(1)) : {avg_cache_ms * 1000:.3f} µs ({avg_cache_ms:.5f} ms)")
    print(f"Database Query Lookup             : {avg_db_ms * 1000:.3f} µs ({avg_db_ms:.5f} ms)")
    print(f"Observed Speedup Ratio            : {speedup:.2f}x faster with LRU Cache")
    print("-" * 70)
    print("Architectural Analysis:")
    print("• LRU Cache operates strictly in O(1) time complexity via pointer rewiring.")
    print("• Database lookups require index lookup, serialization, and round-trips.")
    print("• Actual end-to-end latency in production also depends on network transmission,")
    print("  connection pooling, and database disk I/O conditions.")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark(iterations=2000)

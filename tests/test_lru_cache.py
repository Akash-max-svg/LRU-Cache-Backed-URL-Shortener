"""
Unit tests for the custom LRU Cache.
"""
import pytest
from cache.lru_cache import LRUCache


def test_put_and_get():
    """Test 1: Basic put() and get() functionality."""
    cache = LRUCache(3)
    cache.put("a", "alpha")
    cache.put("b", "beta")

    assert cache.get("a") == "alpha"
    assert cache.get("b") == "beta"
    assert cache.size() == 2


def test_lru_eviction():
    """
    Test 2: LRU eviction with capacity=2.
    Scenario:
        put A
        put B
        get A  (A becomes MRU, B is LRU)
        put C  (B should be evicted)
    """
    cache = LRUCache(2)
    cache.put("A", "val_A")
    cache.put("B", "val_B")

    # Access A to make it most recently used
    assert cache.get("A") == "val_A"

    # Put C -> should evict B
    cache.put("C", "val_C")

    assert cache.get("B") is None  # B evicted
    assert cache.get("A") == "val_A"  # A remains
    assert cache.get("C") == "val_C"  # C remains
    assert cache.size() == 2


def test_cache_hit():
    """Test 3: Cache hit increments hit counter and returns correct value."""
    cache = LRUCache(5)
    cache.put("short1", "https://example.com")

    val = cache.get("short1")
    assert val == "https://example.com"

    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 0
    assert stats["hit_rate"] == 100.0


def test_cache_miss():
    """Test 4: Cache miss increments miss counter and returns None."""
    cache = LRUCache(5)
    val = cache.get("non_existent")

    assert val is None
    stats = cache.get_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 0.0


def test_cache_capacity_boundary():
    """Test 5: Cache respects configured capacity limit."""
    capacity = 4
    cache = LRUCache(capacity)

    for i in range(10):
        cache.put(f"key_{i}", f"val_{i}")

    assert cache.size() == capacity
    assert cache.is_full() is True

    # The most recent 4 should exist: key_6, key_7, key_8, key_9
    for i in range(6):
        assert cache.get(f"key_{i}") is None
    for i in range(6, 10):
        assert cache.get(f"key_{i}") == f"val_{i}"


def test_update_existing_key():
    """Updating an existing key updates its value and moves it to MRU."""
    cache = LRUCache(2)
    cache.put("k1", "v1")
    cache.put("k2", "v2")
    cache.put("k1", "v1_updated")  # Update k1

    cache.put("k3", "v3")  # Should evict k2, not k1

    assert cache.get("k1") == "v1_updated"
    assert cache.get("k2") is None
    assert cache.get("k3") == "v3"


def test_remove_key():
    """Removing key explicitly works and reduces cache size."""
    cache = LRUCache(3)
    cache.put("x", 100)
    cache.put("y", 200)

    val = cache.remove("x")
    assert val == 100
    assert cache.get("x") is None
    assert cache.size() == 1

    # Removing non-existent key returns None
    assert cache.remove("non_existent") is None


def test_clear_cache():
    """Clearing cache removes all items."""
    cache = LRUCache(3)
    cache.put("1", "one")
    cache.put("2", "two")
    cache.clear()

    assert cache.size() == 0
    assert cache.get("1") is None
    assert cache.display() == []


def test_display_order():
    """display() returns items from MRU to LRU."""
    cache = LRUCache(3)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.put("C", 3)
    # Order currently: C (MRU), B, A (LRU)
    cache.get("A")
    # Order after get("A"): A (MRU), C, B (LRU)

    items = cache.display()
    assert items == [("A", 1), ("C", 3), ("B", 2)]


def test_hit_rate_calculation():
    """Verify hit rate percentage calculation."""
    cache = LRUCache(5)
    cache.put("k1", "val1")

    # 3 hits, 1 miss -> 75.0%
    cache.get("k1")
    cache.get("k1")
    cache.get("k1")
    cache.get("unknown")

    stats = cache.get_stats()
    assert stats["total_requests"] == 4
    assert stats["hits"] == 3
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 75.0


def test_invalid_capacity():
    """Creating cache with 0 or negative capacity raises ValueError."""
    with pytest.raises(ValueError):
        LRUCache(0)
    with pytest.raises(ValueError):
        LRUCache(-5)

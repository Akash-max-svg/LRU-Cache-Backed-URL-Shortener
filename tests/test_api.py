"""
Integration tests for the Flask REST API and End-to-End Cache-Aside Redirection Flow.
"""
import time
import pytest
from app import create_app
from config import TestConfig


@pytest.fixture
def test_client():
    """Create a configured Flask test client using isolated in-memory DB and test cache."""
    flask_app = create_app(config_class=TestConfig, force_mock_db=True)
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client, flask_app


def test_api_health(test_client):
    """Test health check endpoint."""
    client, _ = test_client
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] in ("healthy", "degraded")
    assert data["cache"] == "operational"


def test_api_shorten_url_success(test_client):
    """Test 8: API endpoint POST /api/shorten successfully generates short code."""
    client, _ = test_client
    payload = {"url": "https://www.example.com/products/iphone-16"}
    res = client.post("/api/shorten", json=payload)

    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    assert "short_code" in data
    assert "short_url" in data
    assert data["original_url"] == "https://www.example.com/products/iphone-16"


def test_api_shorten_invalid_url(test_client):
    """Test 8: API endpoint rejects invalid URLs."""
    client, _ = test_client

    # Case 1: Missing scheme
    res = client.post("/api/shorten", json={"url": "google.com"})
    assert res.status_code == 400
    assert res.get_json()["success"] is False

    # Case 2: Dangerous scheme
    res = client.post("/api/shorten", json={"url": "javascript:alert(1)"})
    assert res.status_code == 400

    # Case 3: Empty body
    res = client.post("/api/shorten", json={})
    assert res.status_code == 400


def test_api_duplicate_url(test_client):
    """Test 9: Submitting the same active URL returns the existing short code."""
    client, _ = test_client
    target_url = "https://www.google.com/search?q=lru+cache"

    # First request
    res1 = client.post("/api/shorten", json={"url": target_url})
    assert res1.status_code == 201
    code1 = res1.get_json()["short_code"]

    # Second request with identical URL
    res2 = client.post("/api/shorten", json={"url": target_url})
    assert res2.status_code == 200
    code2 = res2.get_json()["short_code"]

    # Must return identical short code, no duplicate records
    assert code1 == code2
    assert res2.get_json().get("is_duplicate") is True


def test_end_to_end_cache_hit_and_miss_flow(test_client):
    """
    Test End-to-End cache flow:
    1. Shorten URL.
    2. Clear cache to simulate clean restart or cold cache.
    3. First access: Cache MISS -> Fetches from DB -> Populates Cache -> 302 Redirect.
    4. Second access: Cache HIT -> Immediate 302 Redirect.
    5. Cache Stats verify 1 Hit, 1 Miss, 50% hit rate.
    """
    client, app = test_client
    url = "https://developer.mozilla.org/en-US/docs/Web/HTTP"

    # Create short URL
    create_res = client.post("/api/shorten", json={"url": url})
    assert create_res.status_code == 201
    short_code = create_res.get_json()["short_code"]

    # Clear cache to guarantee first access is a cold Cache MISS
    app.lru_cache.clear()
    app.lru_cache.reset_stats()
    assert app.lru_cache.size() == 0

    # 1st Access: Should be Cache MISS
    res1 = client.get(f"/{short_code}", follow_redirects=False)
    assert res1.status_code == 302
    assert res1.headers["Location"] == url

    # Item should now be warmed into the cache
    assert app.lru_cache.size() == 1
    stats_after_miss = app.lru_cache.get_stats()
    assert stats_after_miss["hits"] == 0
    assert stats_after_miss["misses"] == 1

    # 2nd Access: Should be Cache HIT
    res2 = client.get(f"/{short_code}", follow_redirects=False)
    assert res2.status_code == 302
    assert res2.headers["Location"] == url

    stats_after_hit = app.lru_cache.get_stats()
    assert stats_after_hit["hits"] == 1
    assert stats_after_hit["misses"] == 1
    assert stats_after_hit["hit_rate"] == 50.0

    # Verify click count updated
    info_res = client.get(f"/api/url/{short_code}")
    assert info_res.status_code == 200
    assert info_res.get_json()["click_count"] == 2


def test_api_expired_url(test_client):
    """Test 10: URL expiration handling."""
    client, app = test_client
    url = "https://news.ycombinator.com"

    # Shorten with 1-second expiration
    create_res = client.post("/api/shorten", json={"url": url, "expires_in": 1})
    assert create_res.status_code == 201
    short_code = create_res.get_json()["short_code"]

    # Verify initially accessible
    res_before = client.get(f"/{short_code}", follow_redirects=False)
    assert res_before.status_code == 302

    # Wait for expiration
    time.sleep(1.2)

    # Access after expiration (request json header)
    res_after = client.get(
        f"/{short_code}",
        headers={"Accept": "application/json"},
        follow_redirects=False,
    )
    assert res_after.status_code == 410
    data = res_after.get_json()
    assert data["success"] is False
    assert "expired" in data["error"].lower()

    # Expired URL should be removed from cache
    assert short_code not in app.lru_cache


def test_api_delete_url(test_client):
    """Test deleting URL removes it from MongoDB and LRU Cache."""
    client, app = test_client
    url = "https://en.wikipedia.org/wiki/LRU_cache"

    create_res = client.post("/api/shorten", json={"url": url})
    short_code = create_res.get_json()["short_code"]

    # Verify in cache
    assert short_code in app.lru_cache

    # Delete
    del_res = client.delete(f"/api/url/{short_code}")
    assert del_res.status_code == 200
    assert del_res.get_json()["success"] is True

    # Cache should no longer have it
    assert short_code not in app.lru_cache

    # Subsequent access should be 404
    get_res = client.get(
        f"/{short_code}",
        headers={"Accept": "application/json"},
    )
    assert get_res.status_code == 404


def test_api_analytics(test_client):
    """Test GET /api/analytics returns proper metrics."""
    client, _ = test_client

    client.post("/api/shorten", json={"url": "https://site1.org"})
    client.post("/api/shorten", json={"url": "https://site2.org"})

    res = client.get("/api/analytics")
    assert res.status_code == 200
    data = res.get_json()
    assert "total_urls" in data
    assert "total_clicks" in data
    assert "cache_hits" in data
    assert "cache_misses" in data
    assert "cache_hit_rate" in data
    assert data["total_urls"] >= 2

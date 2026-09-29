"""
Analytics Service layer for URL Shortener.
Computes system-wide metrics, cache statistics, and URL usage.
"""
from typing import Dict, Any, List
from database.mongodb import MongoDB
from cache.lru_cache import LRUCache


class AnalyticsService:
    """Provides aggregation and analytics metrics for dashboard and APIs."""

    def __init__(self, db: MongoDB, cache: LRUCache, base_url: str = "http://localhost:5000"):
        self.db = db
        self.cache = cache
        self.base_url = base_url.rstrip("/")

    def get_system_analytics(self) -> Dict[str, Any]:
        """
        Aggregate total URLs, total clicks, and LRU cache metrics.

        Returns:
            Dictionary matching specifications:
            total_urls, total_clicks, cache_hits, cache_misses, cache_hit_rate,
            along with capacity and current_cache_size.
        """
        cache_stats = self.cache.get_stats()

        total_urls = 0
        total_clicks = 0

        try:
            col = self.db.urls_collection
            if col is not None:
                # Count total active URLs
                total_urls = col.count_documents({"is_active": True})

                # Aggregate total clicks
                pipeline = [
                    {"$match": {"is_active": True}},
                    {"$group": {"_id": None, "total": {"$sum": "$click_count"}}},
                ]
                res = list(col.aggregate(pipeline))
                if res and len(res) > 0:
                    total_clicks = res[0].get("total", 0)
        except Exception:
            # Fallback gracefully if aggregation fails
            pass

        return {
            "total_urls": total_urls,
            "total_clicks": total_clicks,
            "cache_hits": cache_stats["hits"],
            "cache_misses": cache_stats["misses"],
            "cache_hit_rate": cache_stats["hit_rate"],
            "cache_capacity": cache_stats["capacity"],
            "current_cache_size": cache_stats["current_size"],
            "database_type": "in-memory mock" if self.db.is_mock else "MongoDB Live",
        }

    def get_recent_urls(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Retrieve recent URLs for frontend display with formatted links and click counts.
        """
        urls = []
        try:
            col = self.db.urls_collection
            if col is not None:
                cursor = col.find({"is_active": True}).sort("created_at", -1).limit(limit)
                for doc in cursor:
                    short_code = doc.get("short_code", "")
                    urls.append({
                        "short_code": short_code,
                        "short_url": f"{self.base_url}/{short_code}",
                        "original_url": doc.get("original_url", ""),
                        "click_count": doc.get("click_count", 0),
                        "created_at": doc.get("created_at", ""),
                        "expires_at": doc.get("expires_at"),
                        "in_cache": short_code in self.cache,
                    })
        except Exception:
            pass
        return urls

    def get_cache_contents(self) -> List[Dict[str, Any]]:
        """
        Return the list of items currently resident in the LRU cache,
        ordered from Most Recently Used (MRU) to Least Recently Used (LRU).
        """
        raw_items = self.cache.display()
        result = []
        for key, value in raw_items:
            orig = value.get("original_url", "") if isinstance(value, dict) else str(value)
            clicks = value.get("click_count", 0) if isinstance(value, dict) else 0
            result.append({
                "short_code": key,
                "original_url": orig,
                "click_count": clicks,
            })
        return result

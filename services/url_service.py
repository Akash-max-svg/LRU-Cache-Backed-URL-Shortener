"""
URL Service layer coordinating business logic, LRU Cache, and MongoDB persistence.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple

from cache.lru_cache import LRUCache
from database.mongodb import MongoDB
from models.url_model import URLModel
from services.hash_service import HashService
from utils.validators import URLValidator

logger = logging.getLogger(__name__)


class URLService:
    """
    Manages URL shortening, caching, persistence, retrieval, deletion, and expiration.
    """

    def __init__(self, db: MongoDB, cache: LRUCache, base_url: str = "http://localhost:5000"):
        self.db = db
        self.cache = cache
        self.base_url = base_url.rstrip("/")

    @property
    def urls_collection(self):
        return self.db.urls_collection

    def shorten_url(
        self,
        original_url: str,
        expires_in: Optional[int] = None,
    ) -> Tuple[bool, Dict[str, Any], int]:
        """
        Validate, fingerprint, and shorten a long URL.

        Handles:
            - Validation (HTTP/HTTPS only, length, structure)
            - Duplicate URL detection using SHA-256 fingerprinting
            - Collision-resistant Base62 short-code generation
            - MongoDB persistent storage
            - Immediate insertion into the LRU Cache

        Args:
            original_url: The long URL to shorten.
            expires_in: Optional TTL in seconds.

        Returns:
            Tuple of (success_flag, response_dict, http_status_code).
        """
        # 1. Validate URL
        is_valid, error_msg = URLValidator.validate_url(original_url)
        if not is_valid:
            logger.warning("URL validation failed for input: %s - Error: %s", original_url, error_msg)
            return False, {"success": False, "error": error_msg or "Invalid URL"}, 400

        normalized_url = original_url.strip()

        # 2. Compute SHA-256 hash for fingerprinting and duplicate detection
        url_hash = HashService.sha256_hash(normalized_url)

        # 3. Check for existing active URL with the same hash (Duplicate Handling)
        try:
            existing = self.urls_collection.find_one({"url_hash": url_hash, "is_active": True})
            if existing:
                existing_model = URLModel.from_dict(existing)
                # Check if already expired
                if existing_model.is_expired():
                    self.urls_collection.update_one(
                        {"_id": existing["_id"]},
                        {"$set": {"is_active": False}},
                    )
                    self.cache.remove(existing_model.short_code)
                else:
                    # Return existing short URL without creating duplicate records
                    logger.info("Duplicate URL detected. Returning existing code: %s", existing_model.short_code)
                    # Warm LRU cache with existing record
                    self.cache.put(existing_model.short_code, existing_model.to_dict())
                    return True, {
                        "success": True,
                        "short_code": existing_model.short_code,
                        "short_url": f"{self.base_url}/{existing_model.short_code}",
                        "original_url": existing_model.original_url,
                        "is_duplicate": True,
                    }, 200
        except Exception as e:
            logger.error("Error querying duplicate URL from MongoDB: %s", e)
            return False, {"success": False, "error": "Database error while verifying URL"}, 500

        # 4. Calculate expiration timestamp if provided
        expires_at_iso = None
        if expires_in is not None and expires_in > 0:
            exp_dt = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            expires_at_iso = exp_dt.isoformat()

        # 5. Generate unique short code with collision handling
        short_code = None
        for attempt in range(10):
            candidate_code = HashService.generate_short_code(length=6)
            # Ensure not collision in MongoDB
            collision = self.urls_collection.find_one({"short_code": candidate_code})
            if not collision:
                short_code = candidate_code
                break

        if not short_code:
            logger.error("Failed to generate unique short code after 10 attempts.")
            return False, {"success": False, "error": "Unable to generate unique short code. Please try again."}, 500

        # 6. Construct document model
        url_model = URLModel(
            short_code=short_code,
            original_url=normalized_url,
            url_hash=url_hash,
            expires_at=expires_at_iso,
            click_count=0,
            is_active=True,
        )

        # 7. Persist to MongoDB
        try:
            doc = url_model.to_dict()
            self.urls_collection.insert_one(doc)
            logger.info("URL created: %s -> %s", short_code, normalized_url)
        except Exception as e:
            logger.error("Database error creating URL document: %s", e)
            return False, {"success": False, "error": "Database error while storing URL"}, 500

        # 8. Add to LRU Cache
        self.cache.put(short_code, url_model.to_dict())

        return True, {
            "success": True,
            "short_code": short_code,
            "short_url": f"{self.base_url}/{short_code}",
            "original_url": normalized_url,
            "expires_at": expires_at_iso,
        }, 201

    def resolve_url(self, short_code: str) -> Tuple[Optional[str], str, Optional[str], int]:
        """
        Resolve a short code to its original URL using the Cache-Aside pattern.

        Flow:
            1. Check LRU Cache:
               - If HIT: Check expiration -> redirect or reject.
            2. If MISS:
               - Lookup in MongoDB.
               - Check expiration.
               - If found & valid: populate LRU Cache, update click stats, return redirect.
               - If not found: return 404.

        Returns:
            Tuple of (original_url, cache_status ['HIT'|'MISS'], error_message, http_status_code).
        """
        # Validate short code structure
        is_valid, _ = URLValidator.validate_short_code(short_code)
        if not is_valid:
            logger.warning("Invalid short code format: %s", short_code)
            return None, "MISS", "Invalid short code format", 400

        now_utc = datetime.now(timezone.utc)
        now_iso = now_utc.isoformat()

        # Step 1: Check LRU Cache
        cached_data = self.cache.get(short_code)

        if cached_data is not None:
            logger.info("Cache HIT: %s", short_code)
            # Check expiration
            expires_at = cached_data.get("expires_at")
            if expires_at:
                try:
                    exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                    if now_utc > exp_dt:
                        logger.warning("Expired URL accessed: %s", short_code)
                        self.cache.remove(short_code)
                        self.urls_collection.update_one(
                            {"short_code": short_code},
                            {"$set": {"is_active": False}},
                        )
                        return None, "HIT", "URL has expired", 410
                except Exception as e:
                    logger.error("Error parsing expiration date for %s: %s", short_code, e)

            # Update click count and timestamp in cached object
            cached_data["click_count"] = cached_data.get("click_count", 0) + 1
            cached_data["last_accessed"] = now_iso

            # Update click statistics in MongoDB
            try:
                self.urls_collection.update_one(
                    {"short_code": short_code},
                    {"$inc": {"click_count": 1}, "$set": {"last_accessed": now_iso}},
                )
            except Exception as e:
                logger.error("Error updating click count in MongoDB: %s", e)

            return cached_data["original_url"], "HIT", None, 302

        # Step 2: Cache MISS -> Query MongoDB
        logger.info("Cache MISS: %s", short_code)
        try:
            doc = self.urls_collection.find_one({"short_code": short_code, "is_active": True})
        except Exception as e:
            logger.error("MongoDB query error for %s: %s", short_code, e)
            return None, "MISS", "Database error occurred", 500

        if not doc:
            logger.info("Short URL not found in database: %s", short_code)
            return None, "MISS", "Short URL not found", 404

        url_model = URLModel.from_dict(doc)

        # Step 3: Check expiration
        if url_model.is_expired():
            logger.warning("Expired URL accessed from database: %s", short_code)
            self.urls_collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"is_active": False}},
            )
            self.cache.remove(short_code)
            return None, "MISS", "URL has expired", 410

        # Step 4: Populate LRU Cache
        doc_dict = url_model.to_dict()
        doc_dict["click_count"] += 1
        doc_dict["last_accessed"] = now_iso
        self.cache.put(short_code, doc_dict)

        # Step 5: Update click count and last_accessed in MongoDB
        try:
            self.urls_collection.update_one(
                {"_id": doc["_id"]},
                {"$inc": {"click_count": 1}, "$set": {"last_accessed": now_iso}},
            )
        except Exception as e:
            logger.error("Error updating click stats in MongoDB: %s", e)

        return url_model.original_url, "MISS", None, 302

    def get_url_info(self, short_code: str) -> Tuple[bool, Dict[str, Any], int]:
        """
        Retrieve URL metadata by short code.
        """
        try:
            doc = self.urls_collection.find_one({"short_code": short_code})
        except Exception as e:
            logger.error("Error fetching URL metadata: %s", e)
            return False, {"success": False, "error": "Database error"}, 500

        if not doc or not doc.get("is_active", True):
            return False, {"success": False, "error": "Short URL not found"}, 404

        url_model = URLModel.from_dict(doc)
        if url_model.is_expired():
            self.cache.remove(short_code)
            self.urls_collection.update_one({"short_code": short_code}, {"$set": {"is_active": False}})
            return False, {"success": False, "error": "URL has expired"}, 410

        return True, {
            "success": True,
            "short_code": url_model.short_code,
            "short_url": f"{self.base_url}/{url_model.short_code}",
            "original_url": url_model.original_url,
            "click_count": doc.get("click_count", 0),
            "created_at": url_model.created_at,
            "expires_at": url_model.expires_at,
            "last_accessed": doc.get("last_accessed"),
            "is_active": url_model.is_active,
        }, 200

    def delete_url(self, short_code: str) -> Tuple[bool, Dict[str, Any], int]:
        """
        Delete a shortened URL:
            1. Delete / deactivate from MongoDB.
            2. Evict from LRU Cache.
        """
        is_valid, _ = URLValidator.validate_short_code(short_code)
        if not is_valid:
            return False, {"success": False, "error": "Invalid short code"}, 400

        try:
            result = self.urls_collection.delete_one({"short_code": short_code})
            # Evict from LRU cache
            self.cache.remove(short_code)
            logger.info("URL deleted: %s", short_code)

            if result.deleted_count == 0:
                return False, {"success": False, "error": "Short URL not found"}, 404

            return True, {"success": True, "message": "URL deleted successfully"}, 200
        except Exception as e:
            logger.error("Error deleting URL %s from MongoDB: %s", short_code, e)
            return False, {"success": False, "error": "Database error while deleting URL"}, 500

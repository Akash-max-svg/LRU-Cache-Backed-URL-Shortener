"""
Data Model for Shortened URLs.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class URLModel:
    """
    URL entity model representing a shortened URL document.

    Attributes:
        short_code: Unique alphanumeric short code (e.g. 'aB72xK').
        original_url: Target URL to redirect to.
        url_hash: SHA-256 fingerprint for duplicate detection.
        created_at: ISO 8601 creation timestamp string.
        expires_at: Optional ISO 8601 expiration timestamp string or None.
        click_count: Number of times this short URL has been visited.
        last_accessed: Optional ISO 8601 timestamp of most recent access.
        is_active: Boolean indicating whether the URL is active or deleted/expired.
    """

    def __init__(
        self,
        short_code: str,
        original_url: str,
        url_hash: str,
        created_at: Optional[str] = None,
        expires_at: Optional[str] = None,
        click_count: int = 0,
        last_accessed: Optional[str] = None,
        is_active: bool = True,
        _id: Optional[Any] = None,
    ):
        now_iso = datetime.now(timezone.utc).isoformat()
        self.short_code = short_code
        self.original_url = original_url
        self.url_hash = url_hash
        self.created_at = created_at or now_iso
        self.expires_at = expires_at
        self.click_count = click_count
        self.last_accessed = last_accessed
        self.is_active = is_active
        self._id = _id

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to MongoDB document dict."""
        doc = {
            "short_code": self.short_code,
            "original_url": self.original_url,
            "url_hash": self.url_hash,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "click_count": self.click_count,
            "last_accessed": self.last_accessed,
            "is_active": self.is_active,
        }
        if self._id is not None:
            doc["_id"] = self._id
        return doc

    def to_public_dict(self, base_url: str = "") -> Dict[str, Any]:
        """Convert model instance to public JSON response format."""
        short_url = f"{base_url.rstrip('/')}/{self.short_code}" if base_url else f"/{self.short_code}"
        return {
            "short_code": self.short_code,
            "short_url": short_url,
            "original_url": self.original_url,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "click_count": self.click_count,
            "last_accessed": self.last_accessed,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "URLModel":
        """Instantiate URLModel from a MongoDB document dict."""
        return cls(
            short_code=data.get("short_code", ""),
            original_url=data.get("original_url", ""),
            url_hash=data.get("url_hash", ""),
            created_at=data.get("created_at"),
            expires_at=data.get("expires_at"),
            click_count=data.get("click_count", 0),
            last_accessed=data.get("last_accessed"),
            is_active=data.get("is_active", True),
            _id=data.get("_id"),
        )

    def is_expired(self) -> bool:
        """Check if this URL has passed its expiration timestamp."""
        if not self.expires_at:
            return False
        try:
            exp_time = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            curr_time = datetime.now(timezone.utc)
            return curr_time > exp_time
        except Exception:
            return False

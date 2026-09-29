"""
MongoDB database connection and management layer.
Supports both native MongoDB via PyMongo and in-memory mongomock fallback.
"""
import logging
from typing import Optional
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class MongoDB:
    """Manages MongoDB connection, database collections, and index creation."""

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017",
        database_name: str = "url_shortener",
        connect_timeout_ms: int = 2500,
        force_mock: bool = False,
    ):
        self.mongo_uri = mongo_uri
        self.database_name = database_name
        self.connect_timeout_ms = connect_timeout_ms
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self.urls_collection: Optional[Collection] = None
        self.is_mock: bool = False

        if force_mock:
            self._connect_mock("Forced mock requested")
        else:
            self._connect()

    def _connect(self) -> None:
        """Attempt connection to real MongoDB; fallback to mongomock if unavailable."""
        try:
            logger.info("Attempting connection to MongoDB at %s...", self.mongo_uri)
            client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=self.connect_timeout_ms,
                connectTimeoutMS=self.connect_timeout_ms,
            )
            # Execute ping command to test connectivity
            client.admin.command("ping")
            self.client = client
            self.db = self.client[self.database_name]
            self.urls_collection = self.db["urls"]
            self.is_mock = False
            logger.info("Successfully connected to live MongoDB database '%s'.", self.database_name)
            self._init_indexes()
        except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as exc:
            logger.warning(
                "Could not connect to live MongoDB (%s). Falling back to in-memory mongomock database.",
                str(exc),
            )
            self._connect_mock(f"Connection failure: {exc}")

    def _connect_mock(self, reason: str = "") -> None:
        """Initialize in-memory mongomock database."""
        try:
            import mongomock

            self.client = mongomock.MongoClient()
            self.db = self.client[self.database_name]
            self.urls_collection = self.db["urls"]
            self.is_mock = True
            logger.info(
                "Initialized in-memory mongomock database '%s' (%s).",
                self.database_name,
                reason,
            )
            self._init_indexes()
        except ImportError as err:
            logger.error("mongomock package not installed: %s", err)
            raise

    def _init_indexes(self) -> None:
        """Create necessary database indexes for fast query performance and uniqueness."""
        if self.urls_collection is None:
            return
        try:
            # 1. Unique index on short_code
            self.urls_collection.create_index(
                [("short_code", ASCENDING)],
                unique=True,
                name="idx_unique_short_code",
            )
            # 2. Index on url_hash for fast duplicate detection
            self.urls_collection.create_index(
                [("url_hash", ASCENDING)],
                name="idx_url_hash",
            )
            # 3. Compound index on url_hash + is_active
            self.urls_collection.create_index(
                [("url_hash", ASCENDING), ("is_active", ASCENDING)],
                name="idx_url_hash_active",
            )
            logger.info("MongoDB indexes verified successfully.")
        except Exception as e:
            logger.warning("Error creating MongoDB indexes (may already exist): %s", e)

    def ping(self) -> bool:
        """Check database health status."""
        if self.is_mock:
            return True
        try:
            if self.client:
                self.client.admin.command("ping")
                return True
        except Exception:
            return False
        return False

    def close(self) -> None:
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

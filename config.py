"""
Configuration module for LRU Cache-Backed URL Shortener.
Loads configuration from environment variables and provides sensible defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Application configuration settings."""

    # Server Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "default-dev-secret-key")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = FLASK_ENV == "development"
    PORT = int(os.getenv("PORT", 5000))
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")

    # MongoDB Settings
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "url_shortener")
    COLLECTION_NAME = "urls"
    MONGO_CONNECT_TIMEOUT_MS = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", 3000))

    # LRU Cache Settings
    CACHE_CAPACITY = int(os.getenv("CACHE_CAPACITY", 100))

    # Short Code Settings
    SHORT_CODE_LENGTH = int(os.getenv("SHORT_CODE_LENGTH", 6))
    MAX_URL_LENGTH = int(os.getenv("MAX_URL_LENGTH", 2048))


class TestConfig(Config):
    """Testing configuration settings."""
    TESTING = True
    DATABASE_NAME = "url_shortener_test"
    CACHE_CAPACITY = 3  # Small capacity for easy testing of eviction
    BASE_URL = "http://localhost:5000"

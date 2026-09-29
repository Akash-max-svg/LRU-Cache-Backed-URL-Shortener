"""
Main Application Entrypoint for Simple LRU Cache-Backed URL Shortener.
"""
import logging
import sys
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from database.mongodb import MongoDB
from cache.lru_cache import LRUCache
from services.url_service import URLService
from services.analytics_service import AnalyticsService
from routes.url_routes import create_url_blueprint

# Configure centralized Python logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("url_shortener")


def create_app(config_class=Config, force_mock_db: bool = False) -> Flask:
    """
    Application factory pattern to configure and instantiate the Flask web app.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Enable CORS
    CORS(app)

    # 1. Initialize MongoDB Database
    logger.info("Initializing Database connection...")
    db = MongoDB(
        mongo_uri=app.config.get("MONGO_URI", "mongodb://localhost:27017"),
        database_name=app.config.get("DATABASE_NAME", "url_shortener"),
        connect_timeout_ms=app.config.get("MONGO_CONNECT_TIMEOUT_MS", 2000),
        force_mock=force_mock_db,
    )

    # 2. Initialize Custom LRU Cache
    capacity = app.config.get("CACHE_CAPACITY", 100)
    logger.info("Initializing custom LRU Cache with capacity=%d...", capacity)
    lru_cache = LRUCache(capacity=capacity)

    # 3. Initialize Business Services
    base_url = app.config.get("BASE_URL", "http://localhost:5000")
    url_service = URLService(db=db, cache=lru_cache, base_url=base_url)
    analytics_service = AnalyticsService(db=db, cache=lru_cache, base_url=base_url)

    # Attach instances to app for testing / debugging access
    app.db = db
    app.lru_cache = lru_cache
    app.url_service = url_service
    app.analytics_service = analytics_service

    # 4. Register Blueprint Routes
    blueprint = create_url_blueprint(
        url_service=url_service,
        analytics_service=analytics_service,
        lru_cache=lru_cache,
    )
    app.register_blueprint(blueprint)

    # 5. Global Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"success": False, "error": "Resource not found"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({"success": False, "error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def handle_server_error(e):
        logger.error("Unhandled internal server error: %s", e)
        return jsonify({"success": False, "error": "Internal server error"}), 500

    return app


# Default app instance
app = create_app()

if __name__ == "__main__":
    port = Config.PORT
    debug = Config.DEBUG
    logger.info("Starting LRU Cache URL Shortener on port %s (debug=%s)...", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)

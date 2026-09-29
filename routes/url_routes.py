"""
Flask Blueprint containing URL shortening, redirection, analytics, and cache routes.
"""
import logging
from flask import Blueprint, request, jsonify, redirect, render_template

from services.url_service import URLService
from services.analytics_service import AnalyticsService
from cache.lru_cache import LRUCache

logger = logging.getLogger(__name__)


def create_url_blueprint(
    url_service: URLService,
    analytics_service: AnalyticsService,
    lru_cache: LRUCache,
) -> Blueprint:
    """Factory function creating the URL Shortener blueprint with injected dependencies."""
    bp = Blueprint("urls", __name__)

    # --------------------------------------------------------------------------
    # Frontend Page Routes
    # --------------------------------------------------------------------------

    @bp.route("/", methods=["GET"])
    def index():
        """Render main shortening interface."""
        return render_template("index.html")

    @bp.route("/analytics", methods=["GET"])
    def analytics():
        """Render analytics dashboard page."""
        return render_template("analytics.html")

    # --------------------------------------------------------------------------
    # REST API Routes
    # --------------------------------------------------------------------------

    @bp.route("/api/shorten", methods=["POST"])
    def api_shorten():
        """
        Create a new shortened URL or return existing if duplicate.

        Request JSON:
            url (str): The original URL to shorten.
            expires_in (int, optional): Expiration time in seconds.

        Response JSON:
            success (bool): True/False
            short_code (str): Base62 short code
            short_url (str): Full short URL
        """
        if not request.is_json:
            return jsonify({"success": False, "error": "Request must be JSON"}), 400

        data = request.get_json(silent=True) or {}
        original_url = data.get("url")

        if not original_url:
            return jsonify({"success": False, "error": "URL is required"}), 400

        expires_in = data.get("expires_in")
        if expires_in is not None:
            try:
                expires_in = int(expires_in)
                if expires_in <= 0:
                    expires_in = None
            except (ValueError, TypeError):
                return jsonify({"success": False, "error": "expires_in must be a positive integer"}), 400

        success, response_data, status_code = url_service.shorten_url(original_url, expires_in)
        return jsonify(response_data), status_code

    @bp.route("/api/url/<short_code>", methods=["GET"])
    def api_get_url(short_code: str):
        """Retrieve URL metadata by short code."""
        success, response_data, status_code = url_service.get_url_info(short_code)
        return jsonify(response_data), status_code

    @bp.route("/api/url/<short_code>", methods=["DELETE"])
    def api_delete_url(short_code: str):
        """Delete URL from database and LRU cache."""
        success, response_data, status_code = url_service.delete_url(short_code)
        return jsonify(response_data), status_code

    @bp.route("/api/cache/stats", methods=["GET"])
    def api_cache_stats():
        """
        Return custom LRU Cache performance metrics.

        Response JSON:
            capacity, current_size, total_requests, hits, misses, hit_rate
        """
        stats = lru_cache.get_stats()
        return jsonify(stats), 200

    @bp.route("/api/analytics", methods=["GET"])
    def api_analytics():
        """
        Return comprehensive application analytics:
        total_urls, total_clicks, cache_hits, cache_misses, cache_hit_rate.
        """
        stats = analytics_service.get_system_analytics()
        return jsonify(stats), 200

    @bp.route("/api/analytics/details", methods=["GET"])
    def api_analytics_details():
        """Return analytics along with recent URLs and cached items for dashboard."""
        stats = analytics_service.get_system_analytics()
        recent = analytics_service.get_recent_urls(limit=20)
        cached_items = analytics_service.get_cache_contents()
        return jsonify({
            "metrics": stats,
            "recent_urls": recent,
            "cached_items": cached_items,
        }), 200

    @bp.route("/api/health", methods=["GET"])
    def api_health():
        """Health check endpoint."""
        db_healthy = url_service.db.ping()
        return jsonify({
            "status": "healthy" if db_healthy else "degraded",
            "database": "connected",
            "cache": "operational",
        }), 200

    # --------------------------------------------------------------------------
    # URL Redirection Route
    # --------------------------------------------------------------------------

    @bp.route("/<short_code>", methods=["GET"])
    def redirect_short_url(short_code: str):
        """
        Resolve short code to original URL via LRU Cache -> MongoDB fallback.
        Redirects on success (302).
        """
        # Skip static assets or favicon
        if short_code in ("favicon.ico", "robots.txt", "static", "analytics", "api"):
            return jsonify({"success": False, "error": "Not found"}), 404

        original_url, cache_status, error_msg, status_code = url_service.resolve_url(short_code)

        if original_url:
            return redirect(original_url, code=302)

        # Check if client expects JSON (e.g. API request / test suite)
        wants_json = request.accept_mimetypes.best_match(["application/json", "text/html"]) == "application/json"
        if wants_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": error_msg or "URL error"}), status_code

        # Render friendly HTML error page for browser users
        return render_template(
            "error.html",
            error_code=status_code,
            error_message=error_msg or "The requested URL could not be resolved.",
            short_code=short_code,
        ), status_code

    return bp

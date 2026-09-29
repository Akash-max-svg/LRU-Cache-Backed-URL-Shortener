"""
URL and Short Code validation utilities.
"""
import re
from urllib.parse import urlparse
from typing import Tuple, Optional

ALLOWED_SCHEMES = {"http", "https"}
MAX_URL_LENGTH = 2048
SHORT_CODE_REGEX = re.compile(r"^[0-9a-zA-Z]{4,16}$")


class URLValidator:
    """Validator for URLs and generated short codes."""

    @staticmethod
    def validate_url(url: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate URL format, scheme, and length.

        Rules:
            1. Cannot be empty or whitespace.
            2. Must not exceed MAX_URL_LENGTH (2048 characters).
            3. Must have a valid network scheme ('http' or 'https').
            4. Must have a valid network location (host/domain).
            5. Rejects 'javascript:', 'file:', 'ftp:', 'data:', etc.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not url or not isinstance(url, str) or not url.strip():
            return False, "URL cannot be empty"

        url = url.strip()

        if len(url) > MAX_URL_LENGTH:
            return False, f"URL exceeds maximum allowed length of {MAX_URL_LENGTH} characters"

        # Explicitly check for dangerous schemes upfront
        lower_url = url.lower()
        if lower_url.startswith("javascript:") or lower_url.startswith("data:") or lower_url.startswith("file:"):
            return False, "Dangerous or unsupported URL scheme"

        try:
            parsed = urlparse(url)
        except Exception:
            return False, "Malformed URL structure"

        if not parsed.scheme:
            return False, "URL missing scheme. Must start with http:// or https://"

        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            return False, f"Unsupported scheme '{parsed.scheme}'. Only http:// and https:// are allowed"

        if not parsed.netloc:
            return False, "Invalid URL: Missing domain or host"

        # Validate domain name has at least one dot or is localhost
        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid URL host"

        if hostname != "localhost" and "." not in hostname:
            return False, "Invalid URL host: Domain must contain a valid TLD (e.g. .com, .org)"

        return True, None

    @staticmethod
    def validate_short_code(code: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate that short code contains only allowed Base62 alphanumeric characters.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not code or not isinstance(code, str) or not code.strip():
            return False, "Short code cannot be empty"

        code = code.strip()

        if not SHORT_CODE_REGEX.match(code):
            return False, "Invalid short code. Must be 4-16 alphanumeric characters"

        return True, None

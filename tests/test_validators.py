"""
Unit tests for URL and short code validators.
"""
from utils.validators import URLValidator


def test_valid_urls():
    """Verify standard HTTP and HTTPS URLs are accepted."""
    valid_cases = [
        "https://google.com",
        "http://example.com",
        "https://www.example.com/products/category?id=123#ref",
        "http://localhost:5000/test",
        "https://sub.domain.co.uk/path/to/resource?query=1&b=2",
    ]
    for url in valid_cases:
        is_valid, err = URLValidator.validate_url(url)
        assert is_valid is True, f"Expected {url} to be valid, got error: {err}"
        assert err is None


def test_invalid_urls():
    """Verify invalid, malicious, or malformed URLs are rejected."""
    invalid_cases = [
        ("", "cannot be empty"),
        ("   ", "cannot be empty"),
        ("google.com", "missing scheme"),
        ("javascript:alert(1)", "scheme"),
        ("file:///C:/secret.txt", "scheme"),
        ("ftp://ftp.example.com", "scheme"),
        ("data:text/plain;base64,SGVsbG8=", "scheme"),
        ("http://", "Missing domain"),
    ]
    for url, expected_err_substring in invalid_cases:
        is_valid, err = URLValidator.validate_url(url)
        assert is_valid is False, f"Expected {url} to be invalid"
        assert expected_err_substring.lower() in (err or "").lower()


def test_excessively_long_url():
    """URLs exceeding 2048 characters are rejected."""
    long_url = "https://example.com/" + "a" * 2050
    is_valid, err = URLValidator.validate_url(long_url)
    assert is_valid is False
    assert "maximum" in err.lower()


def test_validate_short_code():
    """Verify Base62 short code validation."""
    assert URLValidator.validate_short_code("aB72xK")[0] is True
    assert URLValidator.validate_short_code("123456")[0] is True

    # Invalid cases
    assert URLValidator.validate_short_code("ab")[0] is False  # too short
    assert URLValidator.validate_short_code("aB72xK!#")[0] is False  # special chars
    assert URLValidator.validate_short_code("")[0] is False

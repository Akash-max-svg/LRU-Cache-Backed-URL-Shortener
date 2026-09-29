"""
Unit tests for HashService (Base62 and SHA-256).
"""
import pytest
from services.hash_service import HashService, BASE62_ALPHABET


def test_sha256_hash():
    """Verify SHA-256 returns consistent 64-char hex string."""
    url = "https://www.example.com"
    hash1 = HashService.sha256_hash(url)
    hash2 = HashService.sha256_hash(url)

    assert len(hash1) == 64
    assert hash1 == hash2  # Deterministic

    # Different URL gives different hash
    hash3 = HashService.sha256_hash("https://www.example.org")
    assert hash1 != hash3


def test_sha256_empty_raises_error():
    """Empty URL raises ValueError."""
    with pytest.raises(ValueError):
        HashService.sha256_hash("")


def test_base62_encode_and_decode():
    """Verify Base62 bidirectional encoding and decoding."""
    test_numbers = [0, 1, 61, 62, 125, 99999, 123456789, 9876543210]

    for num in test_numbers:
        encoded = HashService.encode_base62(num)
        # All chars must be in alphabet
        assert all(c in BASE62_ALPHABET for c in encoded)
        decoded = HashService.decode_base62(encoded)
        assert decoded == num


def test_base62_negative_raises():
    """Negative integer raises ValueError."""
    with pytest.raises(ValueError):
        HashService.encode_base62(-1)


def test_generate_short_code():
    """Verify short code generation produces expected length alphanumeric string."""
    code = HashService.generate_short_code(length=6)
    assert len(code) == 6
    assert all(c in BASE62_ALPHABET for c in code)

    # Generated codes should be distinct
    codes = {HashService.generate_short_code(length=6) for _ in range(50)}
    assert len(codes) == 50

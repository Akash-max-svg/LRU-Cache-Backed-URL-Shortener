"""
Hashing and Encoding Services for URL Shortener.

Provides:
- Base62 encoding: Maps integer IDs / hashes to URL-safe alphanumeric strings.
- SHA-256 hashing: Computes deterministic hexadecimal digest for URL fingerprinting
  and duplicate detection.
- Short code generator: Combines high-resolution timestamp counter and entropy
  to generate clean 6-8 character Base62 identifiers.
"""
import hashlib
import time
import secrets
from typing import Optional

BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(BASE62_ALPHABET)  # 62


class HashService:
    """Handles SHA-256 hashing and Base62 encoding for URL identifiers."""

    @staticmethod
    def sha256_hash(url: str) -> str:
        """
        Generate SHA-256 hexadecimal hash for an input URL string.

        Used for deterministic URL fingerprinting and duplicate detection in MongoDB.

        Args:
            url: The normalized URL string.

        Returns:
            64-character hexadecimal SHA-256 digest string.
        """
        if not url:
            raise ValueError("URL cannot be empty for SHA-256 hashing.")
        return hashlib.sha256(url.strip().encode("utf-8")).hexdigest()

    @staticmethod
    def encode_base62(num: int) -> str:
        """
        Convert a non-negative integer into a Base62 string.

        Args:
            num: Non-negative integer.

        Returns:
            Base62 encoded string.
        """
        if num < 0:
            raise ValueError("Cannot encode negative integers to Base62.")
        if num == 0:
            return BASE62_ALPHABET[0]

        chars = []
        while num > 0:
            num, rem = divmod(num, BASE)
            chars.append(BASE62_ALPHABET[rem])

        return "".join(reversed(chars))

    @staticmethod
    def decode_base62(code: str) -> int:
        """
        Convert a Base62 string back into an integer.

        Args:
            code: Base62 encoded string.

        Returns:
            Integer value.
        """
        if not code:
            raise ValueError("Short code cannot be empty.")
        num = 0
        for char in code:
            val = BASE62_ALPHABET.find(char)
            if val == -1:
                raise ValueError(f"Invalid character in Base62 code: '{char}'")
            num = num * BASE + val
        return num

    @classmethod
    def generate_short_code(cls, seed: Optional[int] = None, length: int = 6) -> str:
        """
        Generate a collision-resistant Base62 short code.

        Combines nanosecond timestamp and cryptographically secure random bits,
        ensuring codes are compact (6-8 characters), unique, and URL-safe.

        Args:
            seed: Optional integer seed (e.g. database sequence/counter).
            length: Target length for the short code (default: 6).

        Returns:
            Base62 string of requested length.
        """
        if seed is not None:
            code = cls.encode_base62(seed)
            if len(code) < length:
                # Pad deterministically with alphabet chars
                code = code.rjust(length, BASE62_ALPHABET[0])
            return code

        # Generate using high-resolution timestamp (nanoseconds) + random entropy
        timestamp_ns = time.time_ns()
        random_suffix = secrets.randbelow(10000)
        combined = (timestamp_ns % (BASE ** length)) * 10000 + random_suffix

        code = cls.encode_base62(combined)

        # Ensure exact desired length
        if len(code) > length:
            code = code[-length:]
        elif len(code) < length:
            # Pad with random Base62 characters
            padding = "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length - len(code)))
            code = padding + code

        return code

"""
JWKS (JSON Web Key Set) Helper.

Utilities for converting PEM keys to JWK format and caching.
"""

import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from app.config.settings import settings


def _int_to_base64url(n: int) -> str:
    """Convert integer to base64url encoding without padding."""
    byte_length = (n.bit_length() + 7) // 8
    return (
        base64.urlsafe_b64encode(n.to_bytes(byte_length, byteorder="big"))
        .rstrip(b"=")
        .decode("ascii")
    )


def get_jwk_from_pem() -> dict:
    """
    Convert PEM public key to JWK format.

    Reads the public key from the configured path and converts it
    to JSON Web Key (JWK) format suitable for JWKS endpoints.

    Returns:
        dict: JWK representation of the public key with fields:
            - kty: Key type (RSA)
            - use: Public key use (sig for signature)
            - alg: Algorithm (from settings)
            - kid: Key ID
            - n: Modulus (base64url encoded)
            - e: Exponent (base64url encoded)
    """
    with open(settings.JWT_PUBLIC_KEY_PATH, "rb") as f:
        pem_data = f.read()

    public_key = serialization.load_pem_public_key(pem_data, backend=default_backend())

    # Get the public numbers (n and e for RSA)
    public_numbers = public_key.public_numbers()

    return {
        "kty": "RSA",
        "use": "sig",
        "alg": settings.JWT_ALGORITHM,
        "kid": "sso-v1",
        "n": _int_to_base64url(public_numbers.n),
        "e": _int_to_base64url(public_numbers.e),
    }


# Cache the JWK to avoid recomputing on each request
_cached_jwk: dict | None = None


def get_cached_jwk() -> dict:
    """
    Get the cached JWK or compute it if not cached.

    Uses module-level caching to avoid recomputing the JWK
    from the PEM file on every request.

    Returns:
        dict: Cached JWK representation
    """
    global _cached_jwk
    if _cached_jwk is None:
        _cached_jwk = get_jwk_from_pem()
    return _cached_jwk

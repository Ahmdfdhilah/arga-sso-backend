"""
JWKS (JSON Web Key Set) Endpoint.

Exposes the public key in JWK format for token verification by other services.
Standard OAuth2/OIDC endpoint: /.well-known/jwks.json
"""

from fastapi import APIRouter

from app.modules.auth.utils.jwks_helper import get_cached_jwk

router = APIRouter()


@router.get("/.well-known/jwks.json", tags=["JWKS"])
async def get_jwks():
    """
    Get the JSON Web Key Set (JWKS).

    Returns the public key(s) used to sign JWT tokens.
    Other services can fetch this to verify tokens without
    needing a local copy of the public key file.

    No authentication required (public endpoint).
    """
    return {"keys": [get_cached_jwk()]}

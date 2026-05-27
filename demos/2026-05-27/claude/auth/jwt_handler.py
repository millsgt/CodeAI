"""JWT authentication and password hashing utilities."""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production-use-32-plus-bytes!")
TOKEN_EXPIRATION = int(os.environ.get("TOKEN_EXPIRATION", 86400))  # 24 hours
REFRESH_EXPIRATION = int(os.environ.get("REFRESH_EXPIRATION", 604800))  # 7 days


def generate_token(user_id: int) -> dict:
    """Generate an access token and refresh token pair for a user."""
    now = datetime.now(timezone.utc)

    access_payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(seconds=TOKEN_EXPIRATION),
    }

    refresh_payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(seconds=REFRESH_EXPIRATION),
    }

    return {
        "access_token": jwt.encode(access_payload, SECRET_KEY, algorithm="HS256"),
        "refresh_token": jwt.encode(refresh_payload, SECRET_KEY, algorithm="HS256"),
        "expires_in": TOKEN_EXPIRATION,
    }


def validate_token(token: str) -> dict:
    """Decode and validate a JWT token, returning its payload.

    Raises:
        jwt.ExpiredSignatureError: Token has expired.
        jwt.InvalidTokenError: Token is malformed or invalid.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])


def refresh_token(refresh_tok: str) -> dict:
    """Exchange a valid refresh token for a new access/refresh token pair.

    Raises:
        ValueError: Token is not a refresh token.
        jwt.ExpiredSignatureError: Refresh token has expired.
        jwt.InvalidTokenError: Token is malformed or invalid.
    """
    payload = validate_token(refresh_tok)

    if payload.get("type") != "refresh":
        raise ValueError("Token is not a refresh token")

    return generate_token(int(payload["sub"]))


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())

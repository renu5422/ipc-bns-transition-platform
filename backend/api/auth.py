"""Authentication — JWT login for analysts.

Demo deployment ships one analyst account, configurable via env:
  AUTH_USERNAME (default "analyst")
  AUTH_PASSWORD (default "nyayasetu2026")
  AUTH_SECRET_KEY (dev-only fallback; REQUIRED when APP_ENV=production)
  APP_ENV         ("development" by default; "production" enables the hard
                   secret check in resolve_secret)
"""

import logging
import os
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

router = APIRouter(tags=["auth"])
logger = logging.getLogger("ipc_bns.auth")

_ALGORITHM = "HS256"
DEV_SECRET = "dev-secret-change-in-production"
MIN_SECRET_LENGTH = 32
_GENERATE_HINT = (
    'generate one with: python -c "import secrets; '
    'print(secrets.token_urlsafe(48))"'
)


class InsecureSecretError(RuntimeError):
    """Raised at import time when production runs without a strong JWT secret."""


def resolve_secret(env: Mapping[str, str]) -> str:
    """Return the JWT signing secret for the given environment mapping.

    APP_ENV=production: AUTH_SECRET_KEY must be set, not a placeholder/dev value,
    and at least MIN_SECRET_LENGTH chars — otherwise InsecureSecretError.
    Any other APP_ENV: falls back to DEV_SECRET with a warning.
    """
    app_env = (env.get("APP_ENV") or "development").strip().lower()
    secret = (env.get("AUTH_SECRET_KEY") or "").strip()
    if app_env == "production":
        if not secret:
            problem = "is not set"
        elif secret == DEV_SECRET or "change-me" in secret.lower():
            problem = "is the dev default / a placeholder"
        elif len(secret) < MIN_SECRET_LENGTH:
            problem = f"is shorter than {MIN_SECRET_LENGTH} characters"
        else:
            return secret
        raise InsecureSecretError(
            f"APP_ENV=production but AUTH_SECRET_KEY {problem}. "
            f"Set a strong AUTH_SECRET_KEY ({_GENERATE_HINT})."
        )
    if not secret:
        logger.warning(
            "AUTH_SECRET_KEY not set — using the insecure dev secret (APP_ENV=%s). "
            "Never do this in production; %s",
            app_env, _GENERATE_HINT,
        )
        return DEV_SECRET
    return secret


_SECRET = resolve_secret(os.environ)
_TOKEN_TTL_MINUTES = int(os.getenv("AUTH_TOKEN_TTL_MINUTES", "60"))

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer(auto_error=False)

_DEMO_USER = os.getenv("AUTH_USERNAME", "analyst")
_DEMO_HASH = _pwd.hash(os.getenv("AUTH_PASSWORD", "nyayasetu2026"))


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int  # seconds


def create_access_token(username: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=_TOKEN_TTL_MINUTES)
    return jwt.encode({"sub": username, "exp": expires}, _SECRET, algorithm=_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Dependency: validates the Bearer token, returns the username."""
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(credentials.credentials, _SECRET, algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest) -> TokenResponse:
    if data.username != _DEMO_USER or not _pwd.verify(data.password, _DEMO_HASH):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return TokenResponse(
        access_token=create_access_token(data.username),
        token_type="bearer",
        expires_in=_TOKEN_TTL_MINUTES * 60,
    )


@router.get("/me")
def me(username: str = Depends(get_current_user)) -> dict:
    return {"username": username, "role": "analyst"}


@router.post("/logout")
def logout() -> dict:
    # Stateless JWT — client discards the token.
    return {"message": "Logged out"}

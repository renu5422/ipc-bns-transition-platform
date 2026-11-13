"""Authentication — JWT login for analysts.

Demo deployment ships one analyst account, configurable via env:
  AUTH_USERNAME (default "analyst")
  AUTH_PASSWORD (default "nyayasetu2026")
  AUTH_SECRET_KEY (default is dev-only; set a real secret in production)
"""

import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

router = APIRouter(tags=["auth"])

_ALGORITHM = "HS256"
_SECRET = os.getenv("AUTH_SECRET_KEY", "dev-secret-change-in-production")
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
        raise HTTPException(status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(credentials.credentials, _SECRET, algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"}) from exc
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload", headers={"WWW-Authenticate": "Bearer"})
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

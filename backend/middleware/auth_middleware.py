from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

PROTECTED_PREFIXES = ["/admin"]

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(p) for p in PROTECTED_PREFIXES):
            token = request.headers.get("Authorization")
            if not token or not token.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Unauthorized")
            # TODO: validate JWT token
        return await call_next(request)

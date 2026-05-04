from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(data: LoginRequest):
    # TODO: validate credentials and return token
    raise HTTPException(status_code=501, detail="Not implemented")

@router.post("/logout")
async def logout():
    # TODO: invalidate session/token
    return {"message": "Logged out"}

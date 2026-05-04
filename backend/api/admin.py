from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/admin/users")
async def list_users():
    # TODO: return list of users (admin only)
    return {"users": []}

@router.post("/admin/upload")
async def upload_data():
    # TODO: handle mapping data upload
    return {"message": "Not implemented"}

from fastapi import APIRouter
from backend.services.diagnostics_service import diagnostics_service

router = APIRouter(prefix="/admin")


@router.get("/diagnostics")
def get_diagnostics():
    return diagnostics_service.project_summary()


@router.get("/health")
def get_health():
    return diagnostics_service.service_health_checks()


@router.get("/config/verify")
def verify_config():
    return diagnostics_service.verify_configuration()


@router.get("/users")
async def list_users():
    return {"users": []}


@router.post("/upload")
async def upload_data():
    return {"message": "Not implemented"}

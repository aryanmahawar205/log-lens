from fastapi import APIRouter
from app.integration_manager import integration_manager

router = APIRouter()

@router.get("/integrations")
async def get_integrations():
    """
    Get the status and version of all registered system integrations.
    """
    return integration_manager.get_tool_status()

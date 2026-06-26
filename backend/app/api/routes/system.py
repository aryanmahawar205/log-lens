from fastapi import APIRouter
from typing import Optional
from app.integration_manager import integration_manager

router = APIRouter()

@router.get("/integrations")
async def get_integrations():
    """
    Get the status and version of all registered system integrations.
    """
    return integration_manager.get_tool_status()

@router.get("/provider")
async def get_active_provider():
    """
    Get information about the currently active analytics provider.
    """
    from app.config import config
    from app.integration_manager import integration_manager

    active = config.get("analytics.provider", "native")
    status = integration_manager.get_tool_status()

    goaccess_info = status.get("goaccess", {})
    execution = goaccess_info.get("execution", {})

    return {
        "active_provider": active,
        "fallback_provider": "native",
        "goaccess_available": goaccess_info.get("healthy", False),
        "last_execution": execution.get("last_execution"),
        "last_execution_status": execution.get("last_status"),
        "goaccess_version": goaccess_info.get("version"),
        "duration": execution.get("duration")
    }

@router.get("/integrations/goaccess")
async def get_goaccess_diagnostics(upload_id: Optional[int] = None):
    """
    Get detailed diagnostics for GoAccess integration.
    """
    from app.integration_manager import integration_manager
    from app.api.routes.analytics import storage

    status = integration_manager.get_tool_status().get("goaccess", {})

    query = "SELECT * FROM external_tool_executions WHERE tool_name = 'goaccess'"
    params = []
    if upload_id:
        query += " AND upload_id = ?"
        params.append(upload_id)
    query += " ORDER BY execution_timestamp DESC LIMIT 10"

    history = storage.execute_query(query, tuple(params))

    return {
        "installation_status": status.get("healthy", False),
        "version": status.get("version"),
        "last_execution": status.get("execution"),
        "execution_history": history
    }

from fastapi.responses import FileResponse
import os
from fastapi import HTTPException

@router.get("/integrations/goaccess/report")
async def get_goaccess_report(path: str):
    """Serve the generated GoAccess HTML report."""
    if not os.path.exists(path) or not path.endswith('.html'):
        raise HTTPException(status_code=404, detail="Report not found")
    # Basic path traversal protection
    if ".." in path or not path.startswith("data/artifacts/goaccess"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return FileResponse(path)

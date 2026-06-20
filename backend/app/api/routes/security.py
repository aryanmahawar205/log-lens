from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any, List

from app.security.analyzer import SecurityAnalyzer

router = APIRouter()

# Dependency hack to re-use from analytics route but normally this would be shared better
from app.api.routes.analytics import get_filters, storage

security_analyzer = SecurityAnalyzer(storage=storage)

@router.get("/overview")
async def get_security_overview(filters: dict = Depends(get_filters)):
    """
    Get high-level security overview.
    """
    return security_analyzer.get_overview(filters)

@router.get("/findings")
async def get_security_findings(filters: dict = Depends(get_filters)):
    """
    Get all structured security findings.
    """
    return security_analyzer.get_findings(filters)

@router.get("/attack-trends")
async def get_attack_trends(filters: dict = Depends(get_filters)):
    """
    Get timeline of attacks.
    """
    return security_analyzer.get_attack_trends(filters)

@router.get("/suspicious-ips")
async def get_suspicious_ips(filters: dict = Depends(get_filters)):
    """
    Get scored IPs with suspicious behaviors.
    """
    return security_analyzer.get_suspicious_ips(filters)

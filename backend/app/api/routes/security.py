from fastapi import APIRouter, Depends, Query, HTTPException
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
    # Ensure dataset_id/upload_id is respected
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

@router.get("/rules")
async def get_sigma_rules():
    """
    Get all loaded Sigma rules.
    """
    return security_analyzer.sigma_engine.get_rules()

@router.get("/rules/{rule_id}")
async def get_sigma_rule(rule_id: str):
    """
    Get a specific Sigma rule by ID.
    """
    rule = security_analyzer.sigma_engine.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule

@router.post("/rules/reload")
async def reload_sigma_rules():
    """
    Reload Sigma rules from disk.
    """
    security_analyzer.sigma_engine.load_rules()
    return {"message": f"Successfully reloaded {len(security_analyzer.sigma_engine.get_rules())} Sigma rules"}

"""
Power BI Integration API Endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_role
from app.models.user import User, UserRole
from app.services.powerbi_service import get_powerbi_service, PowerBIService

router = APIRouter()


@router.get("/datasets/sites")
async def get_sites_dataset(
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.EXECUTIVE)),
    db: Session = Depends(get_db),
    powerbi_service: PowerBIService = Depends(get_powerbi_service)
):
    """Get sites inventory dataset for Power BI"""
    dataset = await powerbi_service.get_sites_dataset()
    return {"dataset": "sites", "records": len(dataset), "data": dataset}


@router.get("/datasets/access-reviews")
async def get_access_reviews_dataset(
    days: int = Query(365, ge=30, le=730),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.EXECUTIVE)),
    db: Session = Depends(get_db),
    powerbi_service: PowerBIService = Depends(get_powerbi_service)
):
    """Get access reviews dataset for Power BI"""
    dataset = await powerbi_service.get_access_reviews_dataset(days=days)
    return {"dataset": "access_reviews", "records": len(dataset), "data": dataset}


@router.get("/datasets/audit-logs")
async def get_audit_logs_dataset(
    days: int = Query(90, ge=7, le=365),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR)),
    db: Session = Depends(get_db),
    powerbi_service: PowerBIService = Depends(get_powerbi_service)
):
    """Get audit logs dataset for Power BI"""
    dataset = await powerbi_service.get_audit_logs_dataset(days=days)
    return {"dataset": "audit_logs", "records": len(dataset), "data": dataset}


@router.get("/datasets/storage-analytics")
async def get_storage_analytics_dataset(
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.EXECUTIVE)),
    db: Session = Depends(get_db),
    powerbi_service: PowerBIService = Depends(get_powerbi_service)
):
    """Get storage analytics dataset for Power BI"""
    dataset = await powerbi_service.get_storage_analytics_dataset()
    return {"dataset": "storage_analytics", "records": len(dataset), "data": dataset}


@router.get("/datasets/compliance-metrics")
async def get_compliance_metrics_dataset(
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db),
    powerbi_service: PowerBIService = Depends(get_powerbi_service)
):
    """Get compliance metrics dataset for Power BI"""
    dataset = await powerbi_service.get_compliance_metrics_dataset()
    return {"dataset": "compliance_metrics", "records": len(dataset), "data": dataset}


@router.post("/refresh/{dataset_name}")
async def refresh_powerbi_dataset(
    dataset_name: str,
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
    powerbi_service: PowerBIService = Depends(get_powerbi_service)
):
    """Trigger Power BI dataset refresh"""
    result = await powerbi_service.refresh_powerbi_dataset(dataset_name)
    return result


@router.get("/connection-string")
async def get_powerbi_connection_string(
    user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
    powerbi_service: PowerBIService = Depends(get_powerbi_service)
):
    """Get database connection details for Power BI Direct Query"""
    connection_info = await powerbi_service.get_connection_string()
    return connection_info


import logging
logger = logging.getLogger(__name__)

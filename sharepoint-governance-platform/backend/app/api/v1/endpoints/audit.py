"""
Audit API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid
import csv
import io

from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User, UserRole
from app.models.audit import AuditLog

router = APIRouter()


class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    audit_id: str
    event_type: str
    operation: str
    event_datetime: datetime
    user_email: Optional[str] = None
    site_url: Optional[str] = None
    resource_name: Optional[str] = None
    result_status: str
    client_ip: Optional[str] = None
    
    class Config:
        from_attributes = True


@router.get("/logs", response_model=List[AuditLogResponse])
async def query_audit_logs(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_type: Optional[str] = None,
    operation: Optional[str] = None,
    user_email: Optional[str] = None,
    site_url: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR, UserRole.COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Query audit logs with filters
    
    Requires Admin, Auditor, or Compliance Officer role
    """
    query = db.query(AuditLog)
    
    # Apply filters
    if start_date:
        query = query.filter(AuditLog.event_datetime >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.event_datetime <= end_date)
    else:
        # Default to last 30 days if no end date
        if not start_date:
            query = query.filter(AuditLog.event_datetime >= datetime.utcnow() - timedelta(days=30))
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    
    if operation:
        query = query.filter(AuditLog.operation == operation)
    
    if user_email:
        query = query.filter(AuditLog.user_email.like(f"%{user_email}%"))
    
    if site_url:
        query = query.filter(AuditLog.site_url.like(f"%{site_url}%"))
    
    # Order by event datetime (newest first)
    query = query.order_by(AuditLog.event_datetime.desc())
    
    # Apply pagination
    logs = query.offset(skip).limit(limit).all()
    
    return [AuditLogResponse.from_orm(log) for log in logs]


@router.get("/logs/export")
async def export_audit_logs(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    format: str = Query("csv", regex="^(csv|json)$"),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.AUDITOR, UserRole.COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Export audit logs to CSV or JSON
    
    Requires Admin, Auditor, or Compliance Officer role
    """
    query = db.query(AuditLog)
    
    # Apply date filters
    if start_date:
        query = query.filter(AuditLog.event_datetime >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.event_datetime <= end_date)
    else:
        # Default to last 90 days for exports
        if not start_date:
            query = query.filter(AuditLog.event_datetime >= datetime.utcnow() - timedelta(days=90))
    
    logs = query.order_by(AuditLog.event_datetime.desc()).all()
    
    if format == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Event DateTime', 'Event Type', 'Operation', 'User Email',
            'Site URL', 'Resource Name', 'Result Status', 'Client IP'
        ])
        
        # Write data
        for log in logs:
            writer.writerow([
                log.event_datetime.isoformat(),
                log.event_type,
                log.operation,
                log.user_email or '',
                log.site_url or '',
                log.resource_name or '',
                log.result_status,
                log.client_ip or ''
            ])
        
        csv_data = output.getvalue()
        
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
        )
    
    else:  # JSON
        logs_data = [AuditLogResponse.from_orm(log).dict() for log in logs]
        
        import json
        json_data = json.dumps(logs_data, default=str, indent=2)
        
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=audit_logs_{datetime.utcnow().strftime('%Y%m%d')}.json"}
        )


@router.get("/compliance-report")
async def generate_compliance_report(
    report_type: str = Query(..., regex="^(gdpr|iso27001|sox)$"),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.COMPLIANCE_OFFICER)),
    db: Session = Depends(get_db)
):
    """
    Generate compliance report (GDPR, ISO 27001, SOX)
    
    Requires Admin or Compliance Officer role
    """
    # Query relevant audit events based on compliance type
    query = db.query(AuditLog).filter(
        AuditLog.event_datetime >= start_date,
        AuditLog.event_datetime <= end_date
    )
    
    if report_type == "gdpr":
        # GDPR-relevant operations: data access, export, deletion
        operations = ['FileAccessed', 'FileDownloaded', 'FileDeleted', 'UserDeleted', 'SiteDeleted']
        query = query.filter(AuditLog.operation.in_(operations))
    
    elif report_type == "iso27001":
        # ISO 27001-relevant: security events, permission changes
        operations = ['PermissionModified', 'SharingChanged', 'SecurityRoleChanged', 'SiteAccessChanged']
        query = query.filter(AuditLog.operation.in_(operations))
    
    elif report_type == "sox":
        # SOX-relevant: administrative actions, configuration changes
        operations = ['ConfigurationChanged', 'PolicyModified', 'AdminActionPerformed']
        query = query.filter(AuditLog.operation.in_(operations))
    
    logs = query.order_by(AuditLog.event_datetime.desc()).all()
    
    # Generate summary statistics
    total_events = len(logs)
    unique_users = len(set(log.user_email for log in logs if log.user_email))
    unique_sites = len(set(log.site_url for log in logs if log.site_url))
    
    return {
        "report_type": report_type.upper(),
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "summary": {
            "total_events": total_events,
            "unique_users": unique_users,
            "unique_sites": unique_sites
        },
        "events": [AuditLogResponse.from_orm(log) for log in logs[:100]]  # Limit to first 100
    }


import logging
logger = logging.getLogger(__name__)

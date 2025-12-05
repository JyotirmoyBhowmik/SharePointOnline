"""
Audit service for syncing and managing audit logs
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.audit import AuditLog
from app.models.user import User
from app.models.site import SharePointSite
from app.integrations.graph_client import graph_service

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit log management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def sync_audit_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        operations: Optional[List[str]] = None
    ) -> int:
        """
        Sync audit logs from Microsoft 365 to local database
        
        Args:
            start_date: Start date for audit log query
            end_date: End date for audit log query
            operations: Optional list of operations to filter
        
        Returns:
            Number of audit logs synced
        """
        logger.info(f"Syncing audit logs from {start_date} to {end_date}")
        
        try:
            # Fetch audit logs from Microsoft Graph
            audit_events = await graph_service.get_audit_logs(
                start_date,
                end_date,
                operations
            )
            
            synced_count = 0
            
            for event in audit_events:
                # Check if event already exists (deduplication)
                ms_audit_id = event.get('id')
                if ms_audit_id:
                    existing = self.db.query(AuditLog).filter(
                        AuditLog.ms_audit_id == ms_audit_id
                    ).first()
                    
                    if existing:
                        continue  # Skip if already synced
                
                # Extract event details
                event_type = event.get('category', 'Unknown')
                operation = event.get('operationType', 'Unknown')
                event_datetime = self._parse_datetime(event.get('activityDateTime'))
                
                # Extract user information
                user_email = event.get('initiatedBy', {}).get('user', {}).get('userPrincipalName')
                user = None
                if user_email:
                    user = self.db.query(User).filter(User.email == user_email).first()
                
                # Extract target resource (site)
                site_url = event.get('targetResources', [{}])[0].get('displayName')
                site = None
                if site_url:
                    site = self.db.query(SharePointSite).filter(
                        SharePointSite.site_url.like(f"%{site_url}%")
                    ).first()
                
                # Create audit log entry
                audit_log = AuditLog(
                    event_type=event_type,
                    operation=operation,
                    event_datetime=event_datetime or datetime.utcnow(),
                    user_id=user.user_id if user else None,
                    user_email=user_email,
                    site_id=site.site_id if site else None,
                    site_url=site_url,
                    resource_name=event.get('targetResources', [{}])[0].get('displayName'),
                    resource_type=event.get('targetResources', [{}])[0].get('type'),
                    client_ip=event.get('initiatedBy', {}).get('user', {}).get('ipAddress'),
                    result_status=event.get('result', 'Success'),
                    details=event,  # Store full event as JSON
                    ms_audit_id=ms_audit_id,
                )
                
                self.db.add(audit_log)
                synced_count += 1
            
            self.db.commit()
            logger.info(f"Successfully synced {synced_count} audit logs")
            return synced_count
        
        except Exception as e:
            logger.error(f"Error syncing audit logs: {str(e)}")
            self.db.rollback()
            raise
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except Exception:
            return None


def get_audit_service(db: Session) -> AuditService:
    """Dependency to get audit service"""
    return AuditService(db)

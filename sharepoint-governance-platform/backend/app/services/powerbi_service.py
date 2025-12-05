"""
Power BI Integration Service for executive dashboards
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import json

from app.models.site import SharePointSite, AccessMatrix
from app.models.audit import AuditLog
from app.models.access_review import AccessReviewCycle
from app.models.user import User

logger = logging.getLogger(__name__)


class PowerBIService:
    """Service for Power BI integration"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_sites_dataset(self) -> List[Dict]:
        """
        Get sites dataset for Power BI
        
        Returns complete site inventory with metrics
        """
        sites = self.db.query(SharePointSite).all()
        
        dataset = []
        for site in sites:
            dataset.append({
                'SiteID': str(site.site_id),
                'SiteName': site.name,
                'SiteURL': site.site_url,
                'Classification': site.classification.value if site.classification else 'Unknown',
                'CreatedDate': site.created_date.isoformat() if site.created_date else None,
                'LastActivity': site.last_activity.isoformat() if site.last_activity else None,
                'StorageUsedMB': site.storage_used_mb or 0,
                'StorageQuotaMB': site.storage_quota_mb or 0,
                'StorageUsagePercent': site.storage_usage_percent or 0,
                'IsArchived': site.is_archived,
                'RetentionExcluded': site.retention_excluded,
            })
        
        return dataset
    
    async def get_access_reviews_dataset(
        self,
        days: int = 365
    ) -> List[Dict]:
        """
        Get access reviews dataset for Power BI
        
        Includes historical review data
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        reviews = self.db.query(AccessReviewCycle).filter(
            AccessReviewCycle.start_date >= cutoff
        ).all()
        
        dataset = []
        for review in reviews:
            site = self.db.query(SharePointSite).filter(
                SharePointSite.site_id == review.site_id
            ).first()
            
            dataset.append({
                'ReviewCycleID': str(review.review_cycle_id),
                'SiteID': str(review.site_id),
                'SiteName': site.name if site else 'Unknown',
                'CycleNumber': review.cycle_number,
                'StartDate': review.start_date.isoformat(),
                'DueDate': review.due_date.isoformat(),
                'Status': review.status.value,
                'CertifiedDate': review.certified_date.isoformat() if review.certified_date else None,
                'DaysToComplete': (review.certified_date - review.start_date).days if review.certified_date else None,
                'IsOverdue': review.due_date < datetime.utcnow() if review.status in ['pending', 'in_progress'] else False,
            })
        
        return dataset
    
    async def get_audit_logs_dataset(
        self,
        days: int = 90
    ) -> List[Dict]:
        """
        Get audit logs dataset for Power BI
        
        Limited to recent data for performance
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        logs = self.db.query(AuditLog).filter(
            AuditLog.event_datetime >= cutoff
        ).all()
        
        dataset = []
        for log in logs:
            dataset.append({
                'AuditID': str(log.audit_id),
                'EventDateTime': log.event_datetime.isoformat(),
                'EventType': log.event_type,
                'Operation': log.operation,
                'UserEmail': log.user_email,
                'SiteURL': log.site_url,
                'ResourceName': log.resource_name,
                'ResultStatus': log.result_status,
                'Hour': log.event_datetime.hour,
                'DayOfWeek': log.event_datetime.strftime('%A'),
                'Date': log.event_datetime.date().isoformat(),
            })
        
        return dataset
    
    async def get_storage_analytics_dataset(self) -> List[Dict]:
        """
        Get storage analytics dataset for Power BI
        
        Aggregated storage metrics
        """
        from sqlalchemy import func
        
        # Get storage by classification
        storage_by_class = self.db.query(
            SharePointSite.classification,
            func.sum(SharePointSite.storage_used_mb).label('total_storage'),
            func.count(SharePointSite.site_id).label('site_count')
        ).filter(
            SharePointSite.is_archived == False
        ).group_by(SharePointSite.classification).all()
        
        dataset = []
        for row in storage_by_class:
            dataset.append({
                'Classification': row.classification.value if row.classification else 'Unknown',
                'TotalStorageGB': round(row.total_storage / 1024, 2) if row.total_storage else 0,
                'SiteCount': row.site_count,
                'AvgStoragePerSiteGB': round((row.total_storage / row.site_count) / 1024, 2) if row.total_storage and row.site_count else 0,
            })
        
        return dataset
    
    async def get_compliance_metrics_dataset(self) -> List[Dict]:
        """
        Get compliance metrics dataset for Power BI
        
        Compliance scores and status
        """
        sites = self.db.query(SharePointSite).filter(
            SharePointSite.is_archived == False
        ).all()
        
        dataset = []
        for site in sites:
            # Calculate compliance score
            score = 100
            factors = []
            
            # Check for overdue reviews
            overdue_reviews = self.db.query(AccessReviewCycle).filter(
                AccessReviewCycle.site_id == site.site_id,
                AccessReviewCycle.status.in_(['pending', 'in_progress']),
                AccessReviewCycle.due_date < datetime.utcnow()
            ).count()
            
            if overdue_reviews > 0:
                score -= 30
                factors.append('Overdue Reviews')
            
            # Check for external users
            external_users = self.db.query(AccessMatrix).filter(
                AccessMatrix.site_id == site.site_id,
                AccessMatrix.is_external_user == True
            ).count()
            
            if external_users > 10:
                score -= 20
                factors.append('High External User Count')
            elif external_users > 0:
                score -= 10
            
            # Check for inactivity
            if site.last_activity:
                days_inactive = (datetime.utcnow() - site.last_activity).days
                if days_inactive > 180:
                    score -= 20
                    factors.append('Inactive Site')
            
            dataset.append({
                'SiteID': str(site.site_id),
                'SiteName': site.name,
                'ComplianceScore': max(0, score),
                'ComplianceLevel': 'High' if score >= 80 else 'Medium' if score >= 60 else 'Low',
                'RiskFactors': '; '.join(factors) if factors else 'None',
                'ExternalUserCount': external_users,
                'OverdueReviewCount': overdue_reviews,
            })
        
        return dataset
    
    async def refresh_powerbi_dataset(self, dataset_name: str) -> Dict:
        """
        Trigger Power BI dataset refresh
        
        This would integrate with Power BI REST API
        """
        logger.info(f"Triggering Power BI refresh for dataset: {dataset_name}")
        
        # TODO: Implement actual Power BI API call
        # Would use Microsoft Power BI REST API with service principal
        
        return {
            'dataset': dataset_name,
            'status': 'refresh_triggered',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def get_connection_string(self) -> Dict:
        """
        Get connection details for Power BI direct query
        
        Returns database connection information
        """
        from app.core.config import settings
        
        # Return sanitized connection info
        # In production, this would use a dedicated read-only user
        return {
            'server': settings.POSTGRES_SERVER,
            'database': settings.POSTGRES_DB,
            'port': settings.POSTGRES_PORT,
            'authentication': 'service_principal',
            'note': 'Use service principal for Power BI connection'
        }


def get_powerbi_service(db: Session) -> PowerBIService:
    """Dependency to get Power BI service"""
    return PowerBIService(db)

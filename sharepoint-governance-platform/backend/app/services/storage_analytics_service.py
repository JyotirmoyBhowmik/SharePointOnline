"""
Storage Analytics Service for tracking and analyzing storage usage
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models.site import SharePointSite
from app.models.retention import DocumentLibrary

logger = logging.getLogger(__name__)


class StorageAnalyticsService:
    """Service for storage analytics and trend analysis"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_tenant_storage_summary(self) -> Dict:
        """
        Get tenant-wide storage summary
        
        Returns:
            Storage statistics dictionary
        """
        # Total storage across all sites
        total_storage = self.db.query(
            func.sum(SharePointSite.storage_used_mb)
        ).scalar() or 0
        
        # Total quota
        total_quota = self.db.query(
            func.sum(SharePointSite.storage_quota_mb)
        ).scalar() or 0
        
        # Count sites by usage percentage
        sites_over_90 = self.db.query(SharePointSite).filter(
            (SharePointSite.storage_used_mb / SharePointSite.storage_quota_mb) > 0.9,
            SharePointSite.is_archived == False
        ).count()
        
        sites_over_75 = self.db.query(SharePointSite).filter(
            (SharePointSite.storage_used_mb / SharePointSite.storage_quota_mb) > 0.75,
            SharePointSite.is_archived == False
        ).count()
        
        # Top storage consumers
        top_sites = self.db.query(SharePointSite).filter(
            SharePointSite.is_archived == False
        ).order_by(
            SharePointSite.storage_used_mb.desc()
        ).limit(10).all()
        
        return {
            'total_storage_gb': round(total_storage / 1024, 2),
            'total_quota_gb': round(total_quota / 1024, 2),
            'usage_percentage': round((total_storage / total_quota * 100) if total_quota > 0 else 0, 2),
            'sites_over_90_percent': sites_over_90,
            'sites_over_75_percent': sites_over_75,
            'top_consumers': [{
                'site_id': str(site.site_id),
                'name': site.name,
                'storage_used_gb': round(site.storage_used_mb / 1024, 2),
                'usage_percent': round(site.storage_usage_percent, 2),
            } for site in top_sites]
        }
    
    async def get_storage_trends(
        self,
        site_id: Optional[str] = None,
        days: int = 30
    ) -> List[Dict]:
        """
        Get storage trend data
        
        Args:
            site_id: Optional site ID to filter by
            days: Number of days of historical data
        
        Returns:
            List of daily storage snapshots
        """
        # TODO: This requires a storage_history table to track daily snapshots
        # For now, return current data as a single point
        
        if site_id:
            site = self.db.query(SharePointSite).filter(
                SharePointSite.site_id == site_id
            ).first()
            
            if not site:
                return []
            
            return [{
                'date': datetime.utcnow().isoformat(),
                'storage_used_mb': site.storage_used_mb,
                'storage_quota_mb': site.storage_quota_mb,
                'usage_percent': site.storage_usage_percent,
            }]
        
        else:
            # Tenant-wide trend
            total_storage = self.db.query(
                func.sum(SharePointSite.storage_used_mb)
            ).scalar() or 0
            
            total_quota = self.db.query(
                func.sum(SharePointSite.storage_quota_mb)
            ).scalar() or 0
            
            return [{
                'date': datetime.utcnow().isoformat(),
                'storage_used_mb': int(total_storage),
                'storage_quota_mb': int(total_quota),
                'usage_percent': round((total_storage / total_quota * 100) if total_quota > 0 else 0, 2),
            }]
    
    async def get_storage_recommendations(self) -> List[Dict]:
        """
        Get storage optimization recommendations
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Find sites over 90% capacity
        critical_sites = self.db.query(SharePointSite).filter(
            (SharePointSite.storage_used_mb / SharePointSite.storage_quota_mb) > 0.9,
            SharePointSite.is_archived == False
        ).all()
        
        for site in critical_sites:
            recommendations.append({
                'site_id': str(site.site_id),
                'site_name': site.name,
                'type': 'quota_increase',
                'priority': 'critical',
                'current_usage_gb': round(site.storage_used_mb / 1024, 2),
                'current_quota_gb': round(site.storage_quota_mb / 1024, 2) if site.storage_quota_mb else 0,
                'recommended_quota_gb': round(site.storage_used_mb / 1024 * 1.5, 2),
                'reason': f'Site is at {site.storage_usage_percent}% capacity',
            })
        
        # Find inactive sites with high storage
        inactive_date = datetime.utcnow() - timedelta(days=180)
        inactive_sites = self.db.query(SharePointSite).filter(
            SharePointSite.last_activity < inactive_date,
            SharePointSite.storage_used_mb > 10240,  # > 10 GB
            SharePointSite.is_archived == False
        ).all()
        
        for site in inactive_sites:
            recommendations.append({
                'site_id': str(site.site_id),
                'site_name': site.name,
                'type': 'archive_candidate',
                'priority': 'medium',
                'current_usage_gb': round(site.storage_used_mb / 1024, 2),
                'last_activity': site.last_activity.isoformat() if site.last_activity else None,
                'reason': f'Site inactive for {(datetime.utcnow() - site.last_activity).days} days with {round(site.storage_used_mb / 1024, 2)} GB storage',
            })
        
        return recommendations
    
    async def get_library_storage_breakdown(self, site_id: str) -> List[Dict]:
        """
        Get storage breakdown by library for a site
        
        Args:
            site_id: Site ID
        
        Returns:
            List of library storage data
        """
        libraries = self.db.query(DocumentLibrary).filter(
            DocumentLibrary.site_id == site_id
        ).order_by(DocumentLibrary.total_size_mb.desc()).all()
        
        return [{
            'library_id': str(lib.library_id),
            'name': lib.name,
            'item_count': lib.item_count,
            'size_mb': lib.total_size_mb,
            'size_gb': round(lib.total_size_mb / 1024, 2),
            'version_count': lib.version_count,
        } for lib in libraries]


def get_storage_analytics_service(db: Session) -> StorageAnalyticsService:
    """Dependency to get storage analytics service"""
    return StorageAnalyticsService(db)

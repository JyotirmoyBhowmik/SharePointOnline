"""
Version Management Service for tracking and cleaning up document versions
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.site import SharePointSite
from app.models.retention import DocumentLibrary
from app.integrations.sharepoint_client import sharepoint_service

logger = logging.getLogger(__name__)


class VersionManagementService:
    """Service for managing document versions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def scan_library_versions(self, library_id: str) -> Dict[str, int]:
        """
        Scan a document library for version statistics
        
        Returns:
            Statistics dictionary with version counts
        """
        logger.info(f"Scanning library {library_id} for versions")
        
        library = self.db.query(DocumentLibrary).filter(
            DocumentLibrary.library_id == library_id
        ).first()
        
        if not library:
            raise ValueError(f"Library {library_id} not found")
        
        site = self.db.query(SharePointSite).filter(
            SharePointSite.site_id == library.site_id
        ).first()
        
        # Get library details from SharePoint
        # Note: This is a simplified version; actual implementation would need
        # to enumerate all documents and check version counts
        
        stats = {
            'total_documents': library.item_count or 0,
            'total_versions': library.version_count or 0,
            'avg_versions_per_doc': 0,
            'docs_over_threshold': 0,
            'estimated_version_storage_mb': 0,
        }
        
        if stats['total_documents'] > 0:
            stats['avg_versions_per_doc'] = stats['total_versions'] / stats['total_documents']
        
        # Update library statistics
        library.version_count = stats['total_versions']
        library.last_scanned = datetime.utcnow()
        self.db.commit()
        
        return stats
    
    async def cleanup_old_versions(
        self,
        library_id: str,
        retention_days: int = 90,
        keep_minimum: int = 3
    ) -> Dict[str, int]:
        """
        Clean up old document versions
        
        Args:
            library_id: Library to clean
            retention_days: Keep versions newer than this
            keep_minimum: Minimum versions to keep regardless of age
        
        Returns:
            Statistics dictionary
        """
        logger.info(f"Cleaning versions in library {library_id} older than {retention_days} days")
        
        library = self.db.query(DocumentLibrary).filter(
            DocumentLibrary.library_id == library_id
        ).first()
        
        if not library:
            raise ValueError(f"Library {library_id} not found")
        
        site = self.db.query(SharePointSite).filter(
            SharePointSite.site_id == library.site_id
        ).first()
        
        # This would use SharePoint API to delete old versions
        # Placeholder implementation
        stats = {
            'versions_deleted': 0,
            'storage_freed_mb': 0,
            'documents_processed': 0,
        }
        
        # TODO: Implement actual version deletion via SharePoint API
        # Would require:
        # 1. Enumerate all documents in library
        # 2. For each document, get version history
        # 3. Delete versions older than retention_days, keeping keep_minimum
        # 4. Track deletion stats
        
        logger.info(f"Version cleanup completed for library {library_id}: {stats}")
        return stats
    
    async def get_version_recommendations(self, site_id: str) -> List[Dict]:
        """
        Get recommendations for version cleanup
        
        Returns:
            List of libraries needing attention
        """
        libraries = self.db.query(DocumentLibrary).filter(
            DocumentLibrary.site_id == site_id
        ).all()
        
        recommendations = []
        
        for library in libraries:
            if not library.version_count or not library.item_count:
                continue
            
            avg_versions = library.version_count / library.item_count
            
            # Recommend cleanup if average versions > 10
            if avg_versions > 10:
                estimated_savings = (avg_versions - 5) * library.item_count * 0.5  # Estimate: 0.5MB per version
                
                recommendations.append({
                    'library_id': str(library.library_id),
                    'library_name': library.name,
                    'avg_versions': round(avg_versions, 2),
                    'estimated_savings_mb': round(estimated_savings, 2),
                    'priority': 'high' if avg_versions > 20 else 'medium',
                })
        
        # Sort by estimated savings
        recommendations.sort(key=lambda x: x['estimated_savings_mb'], reverse=True)
        
        return recommendations


def get_version_management_service(db: Session) -> VersionManagementService:
    """Dependency to get version management service"""
    return VersionManagementService(db)

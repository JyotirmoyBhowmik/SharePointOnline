"""
Recycle Bin Service for managing SharePoint recycle bin
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.site import SharePointSite
from app.models.retention import RecycleBinItem
from app.integrations.sharepoint_client import sharepoint_service

logger = logging.getLogger(__name__)


class RecycleBinService:
    """Service for recycle bin management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def scan_recycle_bin(self, site_id: str, stage: str = 'first') -> Dict[str, int]:
        """
        Scan and update recycle bin inventory
        
        Args:
            site_id: Site ID to scan
            stage: 'first' or 'second' stage recycle bin
        
        Returns:
            Statistics dictionary
        """
        logger.info(f"Scanning {stage}-stage recycle bin for site {site_id}")
        
        site = self.db.query(SharePointSite).filter(
            SharePointSite.site_id == site_id
        ).first()
        
        if not site:
            raise ValueError(f"Site {site_id} not found")
        
        # Get recycle bin items from SharePoint
        bin_items = sharepoint_service.get_recycle_bin_items(
            site.site_url,
            stage=stage
        )
        
        # Clear existing records for this site/stage
        self.db.query(RecycleBinItem).filter(
            RecycleBinItem.site_id == site_id,
            RecycleBinItem.stage == stage
        ).delete()
        
        # Insert new records
        total_size = 0
        for item in bin_items:
            bin_item = RecycleBinItem(
                site_id=site.site_id,
                item_name=item.get('title', ''),
                item_path=item.get('dir_name', ''),
                item_type=item.get('item_type', 'unknown'),
                deleted_by_email=item.get('deleted_by_email'),
                deletion_date=self._parse_datetime(item.get('deleted_date')),
                size_mb=int(item.get('size', 0) / (1024 * 1024)),
                stage=stage,
                ms_item_id=item.get('id'),
            )
            self.db.add(bin_item)
            total_size += bin_item.size_mb
        
        self.db.commit()
        
        stats = {
            'items_found': len(bin_items),
            'total_size_mb': total_size,
            'total_size_gb': round(total_size / 1024, 2),
        }
        
        logger.info(f"Recycle bin scan completed: {stats}")
        return stats
    
    async def cleanup_second_stage(
        self,
        site_id: str,
        older_than_days: int = 90
    ) -> Dict[str, int]:
        """
        Clean up second-stage recycle bin items
        
        Args:
            site_id: Site ID
            older_than_days: Delete items older than this
        
        Returns:
            Statistics dictionary
        """
        logger.info(f"Cleaning second-stage bin for site {site_id}, items older than {older_than_days} days")
        
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
        
        # Get items to delete
        items_to_delete = self.db.query(RecycleBinItem).filter(
            RecycleBinItem.site_id == site_id,
            RecycleBinItem.stage == 'second',
            RecycleBinItem.deletion_date < cutoff_date,
            RecycleBinItem.restored == False
        ).all()
        
        stats = {
            'items_deleted': len(items_to_delete),
            'space_freed_mb': sum(item.size_mb for item in items_to_delete),
        }
        
        # TODO: Actually delete items from SharePoint
        # For now, just mark as deleted in database
        for item in items_to_delete:
            self.db.delete(item)
        
        self.db.commit()
        
        logger.info(f"Second-stage cleanup completed: {stats}")
        return stats
    
    async def get_bin_summary(self, site_id: Optional[str] = None) -> Dict:
        """
        Get recycle bin summary
        
        Args:
            site_id: Optional site ID (None for tenant-wide)
        
        Returns:
            Summary dictionary
        """
        query = self.db.query(RecycleBinItem)
        
        if site_id:
            query = query.filter(RecycleBinItem.site_id == site_id)
        
        first_stage = query.filter(RecycleBinItem.stage == 'first').all()
        second_stage = query.filter(RecycleBinItem.stage == 'second').all()
        
        return {
            'first_stage': {
                'item_count': len(first_stage),
                'total_size_mb': sum(item.size_mb for item in first_stage),
                'total_size_gb': round(sum(item.size_mb for item in first_stage) / 1024, 2),
            },
            'second_stage': {
                'item_count': len(second_stage),
                'total_size_mb': sum(item.size_mb for item in second_stage),
                'total_size_gb': round(sum(item.size_mb for item in second_stage) / 1024, 2),
            }
        }
    
    async def restore_item(self, item_id: str) -> bool:
        """
        Restore an item from recycle bin
        
        Args:
            item_id: Recycle bin item ID
        
        Returns:
            True if successful
        """
        item = self.db.query(RecycleBinItem).filter(
            RecycleBinItem.item_id == item_id
        ).first()
        
        if not item:
            raise ValueError(f"Item {item_id} not found")
        
        # TODO: Actually restore via SharePoint API
        
        item.restored = True
        item.restored_date = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Restored item {item_id} from recycle bin")
        return True
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string"""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except Exception:
            return None


def get_recycle_bin_service(db: Session) -> RecycleBinService:
    """Dependency to get recycle bin service"""
    return RecycleBinService(db)

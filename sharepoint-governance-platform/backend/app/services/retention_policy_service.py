"""
Retention Policy Service for managing retention policies and exclusions
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.models.site import SharePointSite
from app.models.retention import RetentionPolicy, RetentionExclusion
from app.models.user import User
from app.integrations.graph_client import graph_service

logger = logging.getLogger(__name__)


class RetentionPolicyService:
    """Service for retention policy management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def sync_policies_from_purview(self) -> Dict[str, int]:
        """
        Sync retention policies from Microsoft Purview
        
        Returns:
            Statistics dictionary
        """
        logger.info("Syncing retention policies from Microsoft Purview")
        
        # Get policies from Graph API
        purview_policies = await graph_service.get_retention_policies()
        
        stats = {
            'total_found': len(purview_policies),
            'new_policies': 0,
            'updated_policies': 0,
        }
        
        for policy_data in purview_policies:
            ms_policy_id = policy_data.get('id')
            
            # Check if policy exists
            policy = self.db.query(RetentionPolicy).filter(
                RetentionPolicy.ms_policy_id == ms_policy_id
            ).first()
            
            if policy:
                # Update existing
                policy.policy_name = policy_data.get('displayName', policy.policy_name)
                policy.description = policy_data.get('description')
                policy.last_synced = datetime.utcnow()
                stats['updated_policies'] += 1
            else:
                # Create new
                policy = RetentionPolicy(
                    policy_name=policy_data.get('displayName', 'Unknown Policy'),
                    description=policy_data.get('description'),
                    ms_policy_id=ms_policy_id,
                    retention_period_days=policy_data.get('retentionDuration', {}).get('days'),
                    scope=policy_data.get('scope'),
                    is_active=policy_data.get('isEnabled', True),
                )
                self.db.add(policy)
                stats['new_policies'] += 1
        
        self.db.commit()
        
        logger.info(f"Policy sync completed: {stats}")
        return stats
    
    async def request_exclusion(
        self,
        site_id: str,
        policy_id: str,
        user_id: str,
        reason: str
    ) -> RetentionExclusion:
        """
        Request a site to be excluded from a retention policy
        
        Args:
            site_id: Site ID
            policy_id: Policy ID
            user_id: Requesting user ID
            reason: Justification for exclusion
        
        Returns:
            Created exclusion record
        """
        logger.info(f"Creating exclusion request for site {site_id} from policy {policy_id}")
        
        # Check if exclusion already exists
        existing = self.db.query(RetentionExclusion).filter(
            RetentionExclusion.site_id == site_id,
            RetentionExclusion.policy_id == policy_id,
            RetentionExclusion.status == 'active'
        ).first()
        
        if existing:
            raise ValueError("Exclusion already exists for this site and policy")
        
        # Create exclusion request
        exclusion = RetentionExclusion(
            site_id=site_id,
            policy_id=policy_id,
            added_by_user_id=user_id,
            reason=reason,
            status='pending_approval',
        )
        
        self.db.add(exclusion)
        self.db.commit()
        
        # TODO: Send notification to compliance officers for approval
        
        logger.info(f"Exclusion request created: {exclusion.exclusion_id}")
        return exclusion
    
    async def approve_exclusion(
        self,
        exclusion_id: str,
        approver_user_id: str,
        comments: Optional[str] = None
    ) -> RetentionExclusion:
        """
        Approve an exclusion request
        
        Args:
            exclusion_id: Exclusion ID
            approver_user_id: Approving user ID
            comments: Optional approval comments
        
        Returns:
            Updated exclusion record
        """
        exclusion = self.db.query(RetentionExclusion).filter(
            RetentionExclusion.exclusion_id == exclusion_id
        ).first()
        
        if not exclusion:
            raise ValueError(f"Exclusion {exclusion_id} not found")
        
        exclusion.status = 'active'
        exclusion.added_date = datetime.utcnow()  # Record approval date as added date
        
        # TODO: Actually apply exclusion in Microsoft Purview/SharePoint
        
        self.db.commit()
        
        logger.info(f"Exclusion {exclusion_id} approved by user {approver_user_id}")
        return exclusion
    
    async def remove_exclusion(
        self,
        exclusion_id: str,
        remover_user_id: str
    ) -> RetentionExclusion:
        """
        Remove a site from exclusion list
        
        Args:
            exclusion_id: Exclusion ID
            remover_user_id: Removing user ID
        
        Returns:
            Updated exclusion record
        """
        exclusion = self.db.query(RetentionExclusion).filter(
            RetentionExclusion.exclusion_id == exclusion_id
        ).first()
        
        if not exclusion:
            raise ValueError(f"Exclusion {exclusion_id} not found")
        
        exclusion.status = 'removed'
        exclusion.removed_date = datetime.utcnow()
        exclusion.removed_by_user_id = remover_user_id
        
        # TODO: Actually remove exclusion in Microsoft Purview/SharePoint
        
        self.db.commit()
        
        logger.info(f"Exclusion {exclusion_id} removed by user {remover_user_id}")
        return exclusion
    
    async def get_compliance_status(self) -> List[Dict]:
        """
        Get compliance status for all sites
        
        Returns:
            List of site compliance statuses
        """
        sites = self.db.query(SharePointSite).filter(
            SharePointSite.is_archived == False
        ).all()
        
        statuses = []
        
        for site in sites:
            # Check if site has any active exclusions
            exclusions = self.db.query(RetentionExclusion).filter(
                RetentionExclusion.site_id == site.site_id,
                RetentionExclusion.status == 'active'
            ).all()
            
            statuses.append({
                'site_id': str(site.site_id),
                'site_name': site.name,
                'retention_excluded': site.retention_excluded,
                'exclusion_count': len(exclusions),
                'excluded_policies': [
                    {
                        'policy_id': str(exc.policy_id),
                        'reason': exc.reason,
                        'added_date': exc.added_date.isoformat() if exc.added_date else None,
                    }
                    for exc in exclusions
                ],
                'compliance_status': 'non_compliant' if exclusions else 'compliant',
            })
        
        return statuses


def get_retention_policy_service(db: Session) -> RetentionPolicyService:
    """Dependency to get retention policy service"""
    return RetentionPolicyService(db)

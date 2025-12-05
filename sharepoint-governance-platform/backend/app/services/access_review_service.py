"""
Access Review service for managing quarterly review cycles
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.access_review import AccessReviewCycle, AccessReviewItem, ReviewStatus, AccessDecision
from app.models.site import SharePointSite, SiteOwnership, AccessMatrix
from app.models.user import User
from app.integrations.graph_client import graph_service

logger = logging.getLogger(__name__)


class AccessReviewService:
    """Service for access review management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def initiate_quarterly_reviews(self) -> Dict[str, int]:
        """
        Initiate access reviews for all sites
        
        Returns:
            Statistics dictionary
        """
        logger.info("Initiating quarterly access reviews")
        
        stats = {
            'total_sites': 0,
            'reviews_created': 0,
            'reviews_skipped': 0,
        }
        
        try:
            # Calculate cycle number (YYYYQ format: 20251, 20252, etc.)
            now = datetime.utcnow()
            quarter = (now.month - 1) // 3 + 1
            cycle_number = int(f"{now.year}{quarter}")
            
            # Get all active sites
            sites = self.db.query(SharePointSite).filter(
                SharePointSite.is_archived == False
            ).all()
            
            stats['total_sites'] = len(sites)
            
            for site in sites:
                # Check if review already exists for this cycle
                existing_review = self.db.query(AccessReviewCycle).filter(
                    AccessReviewCycle.site_id == site.site_id,
                    AccessReviewCycle.cycle_number == cycle_number
                ).first()
                
                if existing_review:
                    stats['reviews_skipped'] += 1
                    continue
                
                # Get primary owner
                primary_owner = self.db.query(SiteOwnership).filter(
                    SiteOwnership.site_id == site.site_id,
                    SiteOwnership.is_primary_owner == True
                ).first()
                
                if not primary_owner:
                    # Skip if no primary owner
                    logger.warning(f"Site {site.name} has no primary owner, skipping review")
                    stats['reviews_skipped'] += 1
                    continue
                
                # Create review cycle
                review_cycle = AccessReviewCycle(
                    site_id=site.site_id,
                    cycle_number=cycle_number,
                    start_date=now,
                    due_date=now + timedelta(days=30),  # 30 days to complete
                    status=ReviewStatus.PENDING,
                    assigned_to_user_id=primary_owner.user_id,
                )
                
                self.db.add(review_cycle)
                self.db.flush()  # Get review_cycle_id
                
                # Create review items for all access permissions
                access_list = self.db.query(AccessMatrix).filter(
                    AccessMatrix.site_id == site.site_id
                ).all()
                
                for access in access_list:
                    review_item = AccessReviewItem(
                        review_cycle_id=review_cycle.review_cycle_id,
                        user_id=access.user_id,
                        user_email=access.external_user_email if access.is_external_user else (
                            self.db.query(User).filter(User.user_id == access.user_id).first().email if access.user_id else None
                        ),
                        permission_level=access.permission_level,
                        assignment_type=access.assignment_type,
                        last_access_date=access.last_access,
                        access_status=AccessDecision.PENDING,
                    )
                    self.db.add(review_item)
                
                stats['reviews_created'] += 1
                
                # Send notification email to assignee
                if primary_owner.user_id:
                    user = self.db.query(User).filter(User.user_id == primary_owner.user_id).first()
                    if user:
                        await self._send_review_notification(user, site, review_cycle)
            
            self.db.commit()
            logger.info(f"Access review initiation completed: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error initiating access reviews: {str(e)}")
            self.db.rollback()
            raise
    
    async def _send_review_notification(
        self,
        user: User,
        site: SharePointSite,
        review_cycle: AccessReviewCycle
    ):
        """Send email notification to site owner about pending review"""
        subject = f"Action Required: Access Review for {site.name}"
        
        body = f"""
        <html>
        <body>
            <h2>Quarterly Access Review</h2>
            <p>Dear {user.name},</p>
            <p>You have been assigned an access review for the following SharePoint site:</p>
            <ul>
                <li><strong>Site Name:</strong> {site.name}</li>
                <li><strong>Site URL:</strong> {site.site_url}</li>
                <li><strong>Review Due Date:</strong> {review_cycle.due_date.strftime('%Y-%m-%d')}</li>
            </ul>
            <p>Please review and certify the access permissions for this site within 30 days.</p>
            <p>Login to the SharePoint Governance Platform to complete your review.</p>
            <p>Thank you,<br>SharePoint Governance Team</p>
        </body>
        </html>
        """
        
        await graph_service.send_email(user.email, subject, body, is_html=True)


def get_access_review_service(db: Session) -> AccessReviewService:
    """Dependency to get access review service"""
    return AccessReviewService(db)

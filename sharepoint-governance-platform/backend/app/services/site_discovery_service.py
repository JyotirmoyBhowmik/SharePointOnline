"""
Site Discovery Service - Automated SharePoint site discovery and classification
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.models.site import SharePointSite, SiteClassification, SiteOwnership, AccessMatrix
from app.models.user import User
from app.integrations.graph_client import graph_service
from app.integrations.sharepoint_client import sharepoint_service

logger = logging.getLogger(__name__)


class SiteDiscoveryService:
    """Service for discovering and synchronizing SharePoint sites"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def discover_all_sites(self) -> Dict[str, int]:
        """
        Discover all SharePoint sites and update database
        
        Returns:
            Statistics dictionary with counts of new, updated, deleted sites
        """
        logger.info("Starting site discovery process")
        
        stats = {
            'total_discovered': 0,
            'new_sites': 0,
            'updated_sites': 0,
            'unchanged_sites': 0,
        }
        
        try:
            # Fetch all sites from Microsoft Graph
            graph_sites = await graph_service.get_all_sites()
            stats['total_discovered'] = len(graph_sites)
            
            # Get existing sites from database
            existing_sites = {site.site_url: site for site in self.db.query(SharePointSite).all()}
            
            for graph_site in graph_sites:
                site_url = graph_site.get('webUrl')
                
                if not site_url:
                    continue
                
                # Check if site exists in database
                if site_url in existing_sites:
                    # Update existing site
                    if await self._update_site(existing_sites[site_url], graph_site):
                        stats['updated_sites'] += 1
                    else:
                        stats['unchanged_sites'] += 1
                else:
                    # Create new site
                    await self._create_site(graph_site)
                    stats['new_sites'] += 1
            
            self.db.commit()
            logger.info(f"Site discovery completed: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error during site discovery: {str(e)}")
            self.db.rollback()
            raise
    
    async def _create_site(self, graph_site: Dict) -> SharePointSite:
        """Create a new site in the database"""
        site_url = graph_site.get('webUrl')
        
        # Get additional details from SharePoint API
        sp_details = sharepoint_service.get_site_details(site_url)
        
        # Classify site
        classification = self._classify_site(graph_site, sp_details)
        
        # Create site object
        site = SharePointSite(
            site_url=site_url,
            name=graph_site.get('displayName') or graph_site.get('name'),
            description=graph_site.get('description') or (sp_details.get('description') if sp_details else None),
            classification=classification,
            created_date=self._parse_datetime(graph_site.get('createdDateTime')),
            last_activity=self._parse_datetime(graph_site.get('lastModifiedDateTime')),
            ms_site_id=graph_site.get('id'),
            ms_group_id=graph_site.get('sharepointIds', {}).get('siteId') if 'sharepointIds' in graph_site else None,
        )
        
        # Get storage metrics if available
        if sp_details:
            storage = sharepoint_service.get_storage_metrics(site_url)
            if storage:
                site.storage_used_mb = int(storage.get('storage_used', 0) / (1024 * 1024))
        
        self.db.add(site)
        self.db.flush()  # Get site ID
        
        # Discover and create owners
        await self._discover_site_owners(site)
        
        # Discover and create access matrix
        await self._discover_site_access(site)
        
        logger.info(f"Created new site: {site.name} ({site.site_url})")
        return site
    
    async def _update_site(self, site: SharePointSite, graph_site: Dict) -> bool:
        """
        Update existing site with latest data
        
        Returns:
            True if site was updated, False if unchanged
        """
        updated = False
        
        # Update basic metadata
        new_name = graph_site.get('displayName') or graph_site.get('name')
        if site.name != new_name:
            site.name = new_name
            updated = True
        
        new_last_activity = self._parse_datetime(graph_site.get('lastModifiedDateTime'))
        if new_last_activity and site.last_activity != new_last_activity:
            site.last_activity = new_last_activity
            updated = True
        
        # Update last discovered timestamp
        site.last_discovered = datetime.utcnow()
        
        if updated:
            logger.info(f"Updated site: {site.name}")
        
        #  Refresh owners and access (can be done periodically, not every discovery)
        # Uncomment if you want full refresh every discovery
        # await self._discover_site_owners(site)
        # await self._discover_site_access(site)
        
        return updated
    
    def _classify_site(self, graph_site: Dict, sp_details: Optional[Dict]) -> SiteClassification:
        """
        Classify site based on metadata
        
        Args:
            graph_site: Graph API site object
            sp_details: SharePoint API site details
        
        Returns:
            SiteClassification enum value
        """
        # Check if site is connected to a Microsoft 365 Group (Team site)
        if graph_site.get('sharepointIds', {}).get('group'):
            return SiteClassification.TEAM_CONNECTED
        
        # Check web template from SharePoint API
        if sp_details:
            template = sp_details.get('web_template', '')
            if 'SITEPAGEPUBLISHING' in template:
                return SiteClassification.COMMUNICATION
            elif 'HUB' in template:
                return SiteClassification.HUB
        
        # Check site URL patterns
        site_url = graph_site.get('webUrl', '').lower()
        if '/sites/' in site_url:
            return SiteClassification.TEAM_CONNECTED
        elif '/teams/' in site_url:
            return SiteClassification.TEAM_CONNECTED
        
        # Default to legacy
        return SiteClassification.LEGACY
    
    async def _discover_site_owners(self, site: SharePointSite):
        """Discover and create site ownership records"""
        try:
            # Get owners from Graph API
            owners = await graph_service.get_site_owners(site.ms_site_id)
            
            # Clear existing ownership records
            self.db.query(SiteOwnership).filter(SiteOwnership.site_id == site.site_id).delete()
            
            for idx, owner in enumerate(owners):
                # Extract email from owner object
                email = owner.get('grantedToIdentities', [{}])[0].get('user', {}).get('email')
                if not email:
                    email = owner.get('grantedTo', {}).get('user', {}).get('email')
                
                if email:
                    # Check if user exists in database
                    user = self.db.query(User).filter(User.email == email).first()
                    
                    ownership = SiteOwnership(
                        site_id=site.site_id,
                        user_id=user.user_id if user else None,
                        user_email=email,
                        ownership_type='owner',
                        is_primary_owner=(idx == 0),  # First owner is primary
                    )
                    self.db.add(ownership)
            
            logger.info(f"Discovered {len(owners)} owners for site {site.name}")
        
        except Exception as e:
            logger.error(f"Error discovering owners for site {site.site_id}: {str(e)}")
    
    async def _discover_site_access(self, site: SharePointSite):
        """Discover and create access matrix records"""
        try:
            # Get permissions from Graph API
            permissions = await graph_service.get_site_permissions(site.ms_site_id)
            
            # Also get detailed role assignments from SharePoint API
            role_assignments = sharepoint_service.get_role_assignments(site.site_url)
            
            # Clear existing access records
            self.db.query(AccessMatrix).filter(AccessMatrix.site_id == site.site_id).delete()
            
            # Process permissions
            for perm in permissions:
                # Extract user/group information
                granted_to = perm.get('grantedTo', {}).get('user', {})
                email = granted_to.get('email')
                
                if email:
                    # Check if user exists
                    user = self.db.query(User).filter(User.email == email).first()
                    
                    # Determine permission level
                    roles = perm.get('roles', [])
                    permission_level = ', '.join(roles) if roles else 'Read'
                    
                    access = AccessMatrix(
                        site_id=site.site_id,
                        user_id=user.user_id if user else None,
                        permission_level=permission_level,
                        assignment_type='direct' if perm.get('link') else 'inherited',
                        is_external_user='@' not in email.split('@')[1] if '@' in email else False,
                    )
                    self.db.add(access)
            
            logger.info(f"Discovered {len(permissions)} access permissions for site {site.name}")
        
        except Exception as e:
            logger.error(f"Error discovering access for site {site.site_id}: {str(e)}")
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string"""
        if not dt_str:
            return None
        try:
            # Remove 'Z' and parse
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except Exception:
            return None


def get_discovery_service(db: Session) -> SiteDiscoveryService:
    """Dependency to get site discovery service"""
    return SiteDiscoveryService(db)

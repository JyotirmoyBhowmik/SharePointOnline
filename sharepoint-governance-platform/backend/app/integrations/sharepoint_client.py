"""
SharePoint client using Office365-REST-Python-Client
"""
from typing import List, Dict, Optional, Any
import logging

from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.client_credential import ClientCredential

from app.core.config import settings

logger = logging.getLogger(__name__)


class SharePointService:
    """SharePoint Online client wrapper"""
    
    def __init__(self, site_url: Optional[str] = None):
        """
        Initialize SharePoint client
        
        Args:
            site_url: SharePoint site URL (defaults to tenant root)
        """
        self.site_url = site_url or settings.SHAREPOINT_SITE_URL
        self.credentials = ClientCredential(
            settings.CLIENT_ID,
            settings.CLIENT_SECRET
        )
        self.ctx = None
    
    def _get_context(self, site_url: Optional[str] = None) -> ClientContext:
        """Get or create SharePoint context for a site"""
        url = site_url or self.site_url
        return ClientContext(url).with_credentials(self.credentials)
    
    def get_site_details(self, site_url: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed site information
        
        Args:
            site_url: SharePoint site URL
        
        Returns:
            Site details dictionary
        """
        try:
            ctx = self._get_context(site_url)
            web = ctx.web
            ctx.load(web)
            ctx.execute_query()
            
            return {
                'title': web.title,
                'description': web.description,
                'url': web.url,
                'created': web.created.isoformat() if web.created else None,
                'last_item_modified_date': web.last_item_modified_date.isoformat() if web.last_item_modified_date else None,
                'server_relative_url': web.server_relative_url,
                'web_template': web.web_template,
                'language': web.language,
            }
        
        except Exception as e:
            logger.error(f"Error getting site details for {site_url}: {str(e)}")
            return None
    
    def get_site_users(self, site_url: str) -> List[Dict[str, Any]]:
        """
        Get all users with access to a site
        
        Args:
            site_url: SharePoint site URL
        
        Returns:
            List of user dictionaries
        """
        try:
            ctx = self._get_context(site_url)
            users = ctx.web.site_users
            ctx.load(users)
            ctx.execute_query()
            
            user_list = []
            for user in users:
                user_list.append({
                    'id': user.id,
                    'login_name': user.login_name,
                    'title': user.title,
                    'email': user.email,
                    'is_site_admin': user.is_site_admin if hasattr(user, 'is_site_admin') else False,
                    'principal_type': str(user.principal_type) if hasattr(user, 'principal_type') else None,
                })
            
            logger.info(f"Retrieved {len(user_list)} users for site {site_url}")
            return user_list
        
        except Exception as e:
            logger.error(f"Error getting site users for {site_url}: {str(e)}")
            return []
    
    def get_site_groups(self, site_url: str) -> List[Dict[str, Any]]:
        """
        Get all groups with access to a site
        
        Args:
            site_url: SharePoint site URL
        
        Returns:
            List of group dictionaries
        """
        try:
            ctx = self._get_context(site_url)
            groups = ctx.web.site_groups
            ctx.load(groups)
            ctx.execute_query()
            
            group_list = []
            for group in groups:
                group_list.append({
                    'id': group.id,
                    'title': group.title,
                    'description': group.description if hasattr(group, 'description') else None,
                    'owner_title': group.owner_title if hasattr(group, 'owner_title') else None,
                    'login_name': group.login_name,
                })
            
            logger.info(f"Retrieved {len(group_list)} groups for site {site_url}")
            return group_list
        
        except Exception as e:
            logger.error(f"Error getting site groups for {site_url}: {str(e)}")
            return []
    
    def get_role_assignments(self, site_url: str) -> List[Dict[str, Any]]:
        """
        Get role assignments (permissions) for a site
        
        Args:
            site_url: SharePoint site URL
        
        Returns:
            List of role assignment dictionaries
        """
        try:
            ctx = self._get_context(site_url)
            role_assignments = ctx.web.role_assignments
            ctx.load(role_assignments)
            ctx.execute_query()
            
            assignment_list = []
            for assignment in role_assignments:
                ctx.load(assignment.member)
                ctx.load(assignment.role_definition_bindings)
                ctx.execute_query()
                
                roles = [role.name for role in assignment.role_definition_bindings]
                
                assignment_list.append({
                    'member_id': assignment.member.id,
                    'member_title': assignment.member.title,
                    'member_login_name': assignment.member.login_name if hasattr(assignment.member, 'login_name') else None,
                    'roles': roles,
                })
            
            logger.info(f"Retrieved {len(assignment_list)} role assignments for site {site_url}")
            return assignment_list
        
        except Exception as e:
            logger.error(f"Error getting role assignments for {site_url}: {str(e)}")
            return []
    
    def get_document_libraries(self, site_url: str) -> List[Dict[str, Any]]:
        """
        Get all document libraries in a site
        
        Args:
            site_url: SharePoint site URL
        
        Returns:
            List of library dictionaries
        """
        try:
            ctx = self._get_context(site_url)
            lists = ctx.web.lists
            ctx.load(lists)
            ctx.execute_query()
            
            library_list = []
            for lst in lists:
                # Filter for document libraries only
                if lst.base_template == 101:  # Document Library template
                    library_list.append({
                        'id': str(lst.id),
                        'title': lst.title,
                        'description': lst.description,
                        'item_count': lst.item_count,
                        'created': lst.created.isoformat() if lst.created else None,
                        'last_item_modified_date': lst.last_item_modified_date.isoformat() if lst.last_item_modified_date else None,
                        'server_relative_url': lst.root_folder.server_relative_url if hasattr(lst, 'root_folder') else None,
                    })
            
            logger.info(f"Retrieved {len(library_list)} document libraries for site {site_url}")
            return library_list
        
        except Exception as e:
            logger.error(f"Error getting document libraries for {site_url}: {str(e)}")
            return []
    
    def get_recycle_bin_items(self, site_url: str, stage: str = 'first') -> List[Dict[str, Any]]:
        """
        Get recycle bin items
        
        Args:
            site_url: SharePoint site URL
            stage: 'first' or 'second' stage recycle bin
        
        Returns:
            List of recycle bin item dictionaries
        """
        try:
            ctx = self._get_context(site_url)
            
            if stage == 'first':
                bin_items = ctx.web.recycle_bin
            else:
                bin_items = ctx.site.recycle_bin  # Second stage
            
            ctx.load(bin_items)
            ctx.execute_query()
            
            item_list = []
            for item in bin_items:
                item_list.append({
                    'id': str(item.id),
                    'title': item.title,
                    'deleted_by_email': item.deleted_by_email if hasattr(item, 'deleted_by_email') else None,
                    'deleted_date': item.deleted_date.isoformat() if item.deleted_date else None,
                    'item_type': str(item.item_type) if hasattr(item, 'item_type') else None,
                    'size': item.size if hasattr(item, 'size') else 0,
                    'dir_name': item.dir_name if hasattr(item, 'dir_name') else None,
                })
            
            logger.info(f"Retrieved {len(item_list)} items from {stage}-stage recycle bin for site {site_url}")
            return item_list
        
        except Exception as e:
            logger.error(f"Error getting recycle bin items for {site_url}: {str(e)}")
            return []
    
    def get_storage_metrics(self, site_url: str) -> Optional[Dict[str, Any]]:
        """
        Get storage usage metrics for a site
        
        Args:
            site_url: SharePoint site URL
        
        Returns:
            Storage metrics dictionary
        """
        try:
            ctx = self._get_context(site_url)
            site = ctx.site
            ctx.load(site)
            ctx.execute_query()
            
            # Note: Storage metrics may require admin permissions
            usage = site.usage if hasattr(site, 'usage') else None
            
            if usage:
                return {
                    'storage_used': usage.storage,
                    'storage_allocated': usage.storage_percentages_used if hasattr(usage, 'storage_percentages_used') else None,
                }
            
            return None
        
        except Exception as e:
            logger.warning(f"Could not retrieve storage metrics for {site_url}: {str(e)}")
            return None


# Global SharePoint service instance
sharepoint_service = SharePointService()

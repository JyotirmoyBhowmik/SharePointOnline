"""
Microsoft Graph API client for SharePoint and M365 integration
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

from msgraph.core import GraphClient
from azure.identity import ClientSecretCredential
from app.core.config import settings

logger = logging.getLogger(__name__)


class MicrosoftGraphService:
    """Microsoft Graph API client wrapper"""
    
    def __init__(self):
        """Initialize Graph client with app credentials"""
        self.credential = ClientSecretCredential(
            tenant_id=settings.TENANT_ID,
            client_id=settings.CLIENT_ID,
            client_secret=settings.CLIENT_SECRET
        )
        self.client = GraphClient(credential=self.credential)
    
    async def get_all_sites(self, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all SharePoint sites in the tenant
        
        Args:
            search: Optional search query to filter sites
        
        Returns:
            List of site objects
        """
        try:
            endpoint = "/sites?$select=id,name,displayName,webUrl,createdDateTime,lastModifiedDateTime,description"
            
            if search:
                endpoint += f"&$search=\"{search}\""
            
            response = self.client.get(endpoint)
            sites = response.json().get('value', [])
            
            # Handle pagination
            while '@odata.nextLink' in response.json():
                response = self.client.get(response.json()['@odata.nextLink'])
                sites.extend(response.json().get('value', []))
            
            logger.info(f"Retrieved {len(sites)} sites from Microsoft Graph")
            return sites
        
        except Exception as e:
            logger.error(f"Error retrieving sites: {str(e)}")
            raise
    
    async def get_site_by_url(self, site_url: str) -> Optional[Dict[str, Any]]:
        """
        Get site details by URL
        
        Args:
            site_url: SharePoint site URL
        
        Returns:
            Site object or None if not found
        """
        try:
            # Extract hostname and relative path
            # Example: https://tenant.sharepoint.com/sites/sitename
            # Becomes: tenant.sharepoint.com:/sites/sitename
            
            parts = site_url.replace('https://', '').split('/', 1)
            hostname = parts[0]
            path = '/' + parts[1] if len(parts) > 1 else ''
            
            endpoint = f"/sites/{hostname}:{path}"
            response = self.client.get(endpoint)
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error retrieving site {site_url}: {str(e)}")
            return None
    
    async def get_site_permissions(self, site_id: str) -> List[Dict[str, Any]]:
        """
        Get permissions for a site
        
        Args:
            site_id: Microsoft Graph site ID
        
        Returns:
            List of permission objects
        """
        try:
            endpoint = f"/sites/{site_id}/permissions"
            response = self.client.get(endpoint)
            permissions = response.json().get('value', [])
            
            logger.info(f"Retrieved {len(permissions)} permissions for site {site_id}")
            return permissions
        
        except Exception as e:
            logger.error(f"Error retrieving permissions for site {site_id}: {str(e)}")
            return []
    
    async def get_site_owners(self, site_id: str) -> List[Dict[str, Any]]:
        """
        Get site owners/administrators
        
        Args:
            site_id: Microsoft Graph site ID
        
        Returns:
            List of owner objects
        """
        try:
            # Get site owners via permissions with role filter
            permissions = await self.get_site_permissions(site_id)
            
            owners = [
                p for p in permissions
                if 'roles' in p and ('owner' in p['roles'] or 'write' in p['roles'])
            ]
            
            return owners
        
        except Exception as e:
            logger.error(f"Error retrieving owners for site {site_id}: {str(e)}")
            return []
    
    async def get_audit_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        operations: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get audit logs from Microsoft 365 Unified Audit Log
        
        Args:
            start_date: Start date for audit logs
            end_date: End date for audit logs
            operations: Optional list of operations to filter (e.g., FileAccessed, FileModified)
        
        Returns:
            List of audit log events
        """
        try:
            # Format dates for Graph API
            start_str = start_date.isoformat() + 'Z'
            end_str = end_date.isoformat() + 'Z'
            
            endpoint = f"/auditLogs/directoryAudits?$filter=activityDateTime ge {start_str} and activityDateTime le {end_str}"
            
            if operations:
                operations_filter = ' or '.join([f"operationType eq '{op}'" for op in operations])
                endpoint += f" and ({operations_filter})"
            
            response = self.client.get(endpoint)
            logs = response.json().get('value', [])
            
            # Handle pagination
            while '@odata.nextLink' in response.json():
                response = self.client.get(response.json()['@odata.nextLink'])
                logs.extend(response.json().get('value', []))
            
            logger.info(f"Retrieved {len(logs)} audit log entries")
            return logs
        
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {str(e)}")
            return []
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user details by email
        
        Args:
            email: User email address
        
        Returns:
            User object or None
        """
        try:
            endpoint = f"/users/{email}"
            response = self.client.get(endpoint)
            return response.json()
        
        except Exception as e:
            logger.warning(f"User not found: {email}")
            return None
    
    async def get_group_members(self, group_id: str) -> List[Dict[str, Any]]:
        """
        Get members of a group
        
        Args:
            group_id: Microsoft 365 group ID
        
        Returns:
            List of member objects
        """
        try:
            endpoint = f"/groups/{group_id}/members"
            response = self.client.get(endpoint)
            members = response.json().get('value', [])
            
            # Handle pagination
            while '@odata.nextLink' in response.json():
                response = self.client.get(response.json()['@odata.nextLink'])
                members.extend(response.json().get('value', []))
            
            return members
        
        except Exception as e:
            logger.error(f"Error retrieving group members for {group_id}: {str(e)}")
            return []
    
    async def get_retention_policies(self) -> List[Dict[str, Any]]:
        """
        Get retention policies from Microsoft Purview
        
        Returns:
            List of retention policy objects
        """
        try:
            endpoint = "/security/retentionPolicies"
            response = self.client.get(endpoint)
            policies = response.json().get('value', [])
            
            logger.info(f"Retrieved {len(policies)} retention policies")
            return policies
        
        except Exception as e:
            logger.error(f"Error retrieving retention policies: {str(e)}")
            return []
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = True
    ) -> bool:
        """
        Send email notification via Microsoft Graph
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            is_html: Whether body is HTML (default: True)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML" if is_html else "Text",
                        "content": body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ]
                }
            }
            
            # Send from configured email address
            endpoint = f"/users/{settings.EMAIL_FROM}/sendMail"
            self.client.post(endpoint, data=message)
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False


# Global Graph service instance
graph_service = MicrosoftGraphService()

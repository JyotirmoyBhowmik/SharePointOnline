"""
User service for AD synchronization
"""
from typing import Dict
from sqlalchemy.orm import Session
import logging
import ldap

from app.models.user import User, UserRole
from app.core.config import settings
from app.core.auth import determine_role_from_groups

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management and AD sync"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def sync_users_from_ad(self) -> Dict[str, int]:
        """
        Sync users from Active Directory to local database
        
        Returns:
            Statistics dictionary with counts
        """
        logger.info("Starting user synchronization from Active Directory")
        
        stats = {
            'total_found': 0,
            'new_users': 0,
            'updated_users': 0,
            'deactivated_users': 0,
        }
        
        try:
            # Initialize LDAP connection
            conn = ldap.initialize(settings.LDAP_SERVER)
            conn.set_option(ldap.OPT_REFERRALS, 0)
            conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
            
            # Bind with service account
            if settings.LDAP_BIND_DN and settings.LDAP_BIND_PASSWORD:
                conn.simple_bind_s(settings.LDAP_BIND_DN, settings.LDAP_BIND_PASSWORD)
            
            # Search for all users
            search_filter = "(objectClass=user)"
            search_base = settings.LDAP_USER_SEARCH_BASE or settings.LDAP_BASE_DN
            attrs = ['mail', 'displayName', 'department', 'sAMAccountName', 'memberOf', 'distinguishedName']
            
            result = conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter, attrs)
            
            stats['total_found'] = len(result)
            
            # Get existing users
            existing_users = {user.email: user for user in self.db.query(User).all()}
            synced_emails = set()
            
            for dn, attrs_dict in result:
                if not attrs_dict or 'mail' not in attrs_dict:
                    continue
                
                email = attrs_dict['mail'][0].decode('utf-8')
                synced_emails.add(email)
                
                name = attrs_dict.get('displayName', [b''])[0].decode('utf-8') if 'displayName' in attrs_dict else email
                department = attrs_dict.get('department', [b''])[0].decode('utf-8') if 'department' in attrs_dict else None
                username = attrs_dict.get('sAMAccountName', [b''])[0].decode('utf-8') if 'sAMAccountName' in attrs_dict else None
                
                # Get group memberships for role
                member_of = [g.decode('utf-8') for g in attrs_dict.get('memberOf', [])]
                role = determine_role_from_groups(member_of)
                
                if email in existing_users:
                    # Update existing user
                    user = existing_users[email]
                    if user.name != name or user.department != department or user.role != role:
                        user.name = name
                        user.department = department
                        user.role = role
                        user.ad_username = username
                        user.ad_distinguished_name = dn
                        stats['updated_users'] += 1
                else:
                    # Create new user
                    user = User(
                        email=email,
                        name=name,
                        department=department,
                        role=role,
                        ad_username=username,
                        ad_distinguished_name=dn,
                        is_active=True,
                    )
                    self.db.add(user)
                    stats['new_users'] += 1
            
            # Deactivate users not found in AD
            for email, user in existing_users.items():
                if email not in synced_emails and user.is_active:
                    user.is_active = False
                    stats['deactivated_users'] += 1
            
            self.db.commit()
            conn.unbind_s()
            
            logger.info(f"User sync completed: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Error syncing users from AD: {str(e)}")
            self.db.rollback()
            raise


def get_user_service(db: Session) -> UserService:
    """Dependency to get user service"""
    return UserService(db)

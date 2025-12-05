"""
Authentication module for AD/LDAP integration and JWT token management
"""
from datetime import datetime, timedelta
from typing import Optional
import ldap
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user import User, UserRole
import logging

logger = logging.getLogger(__name__)

# Password hashing context (if storing passwords locally)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def authenticate_with_ad(username: str, password: str) -> Optional[dict]:
    """
    Authenticate user against Active Directory via LDAP
    
    Args:
        username: User's username (can be email or sAMAccountName)
        password: User's password
    
    Returns:
        dict with user details if authentication successful, None otherwise
    """
    try:
        # Initialize LDAP connection
        conn = ldap.initialize(settings.LDAP_SERVER)
        conn.set_option(ldap.OPT_REFERRALS, 0)
        conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
        
        # Construct user DN (Distinguished Name)
        # Option 1: If username is email, search first
        if "@" in username:
            # Bind with service account to search
            if settings.LDAP_BIND_DN and settings.LDAP_BIND_PASSWORD:
                conn.simple_bind_s(settings.LDAP_BIND_DN, settings.LDAP_BIND_PASSWORD)
            
            # Search for user
            search_filter = f"(mail={username})"
            search_base = settings.LDAP_USER_SEARCH_BASE or settings.LDAP_BASE_DN
            result = conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter, ['distinguishedName', 'mail', 'displayName', 'department', 'memberOf'])
            
            if not result:
                logger.warning(f"User not found in AD: {username}")
                return None
            
            user_dn = result[0][0]
            user_attrs = result[0][1]
        else:
            # Construct DN from username (sAMAccountName)
            user_dn = f"cn={username},{settings.LDAP_USER_SEARCH_BASE or settings.LDAP_BASE_DN}"
            user_attrs = None
        
        # Attempt to bind with user credentials
        conn.simple_bind_s(user_dn, password)
        
        # If we didn't get attributes from search, get them now
        if not user_attrs:
            result = conn.search_s(user_dn, ldap.SCOPE_BASE, '(objectClass=*)', ['mail', 'displayName', 'department', 'memberOf'])
            user_attrs = result[0][1] if result else {}
        
        # Extract user details
        email = user_attrs.get('mail', [b''])[0].decode('utf-8') if 'mail' in user_attrs else username
        display_name = user_attrs.get('displayName', [b''])[0].decode('utf-8') if 'displayName' in user_attrs else username
        department = user_attrs.get('department', [b''])[0].decode('utf-8') if 'department' in user_attrs else None
        
        # Get group memberships for role determination
        member_of = [g.decode('utf-8') for g in user_attrs.get('memberOf', [])]
        role = determine_role_from_groups(member_of)
        
        conn.unbind_s()
        
        logger.info(f"AD authentication successful for user: {email}")
        
        return {
            'email': email,
            'name': display_name,
            'department': department,
            'role': role,
            'ad_username': username,
            'ad_distinguished_name': user_dn,
        }
    
    except ldap.INVALID_CREDENTIALS:
        logger.warning(f"Invalid credentials for user: {username}")
        return None
    except ldap.LDAPError as e:
        logger.error(f"LDAP error during authentication: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during AD authentication: {str(e)}")
        return None


def determine_role_from_groups(groups: list) -> UserRole:
    """
    Determine user role based on AD group memberships
    
    Args:
        groups: List of group DNs the user is member of
    
    Returns:
        UserRole enum value
    """
    # Define group name to role mapping (customize for your organization)
    role_mappings = {
        'SharePoint-Admins': UserRole.ADMIN,
        'Compliance-Officers': UserRole.COMPLIANCE_OFFICER,
        'IT-Auditors': UserRole.AUDITOR,
        'Executives': UserRole.EXECUTIVE,
    }
    
    # Check group memberships
    for group_dn in groups:
        # Extract CN from group DN
        for part in group_dn.split(','):
            if part.startswith('CN='):
                group_name = part[3:]  # Remove 'CN=' prefix
                if group_name in role_mappings:
                    return role_mappings[group_name]
    
    # Default to Site Owner
    return UserRole.SITE_OWNER


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Payload data to encode in token
        expires_delta: Token expiration time (default: from settings)
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token (longer expiration)
    
    Args:
        data: Payload data to encode in token
    
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hashed version (if using local storage)"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password (if using local storage)"""
    return pwd_context.hash(password)

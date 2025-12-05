"""
Two-Factor Authentication (2FA) core functionality
Implements TOTP (Time-based One-Time Password) using pyotp
"""
import secrets
import hashlib
import json
import io
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import pyotp
import qrcode
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.two_factor import UserTwoFactor, TrustedDevice


def generate_totp_secret() -> str:
    """
    Generate a random TOTP secret key
    
    Returns:
        Base32-encoded secret string (16 bytes = 26 char base32)
    """
    return pyotp.random_base32()


def generate_qr_code(secret: str, email: str, issuer_name: str = None) -> bytes:
    """
    Generate QR code image for TOTP setup
    
    Args:
        secret: TOTP secret key
        email: User's email (shown in authenticator app)
        issuer_name: Application name (defaults to settings.TOTP_ISSUER_NAME)
    
    Returns:
        PNG image bytes of QR code
    """
    if issuer_name is None:
        issuer_name = getattr(settings, 'TOTP_ISSUER_NAME', 'SharePoint Governance Platform')
    
    # Create TOTP URI
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=email,
        issuer_name=issuer_name
    )
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    # Create PNG image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes.getvalue()


def verify_totp_code(secret: str, code: str, valid_window: int = 1) -> bool:
    """
    Verify a TOTP code against the secret
    
    Args:
        secret: TOTP secret key
        code: 6-digit code from authenticator app
        valid_window: Number of time windows to check (default 1 = ±30 seconds)
    
    Returns:
        True if code is valid, False otherwise
    """
    if not code or not secret:
        return False
    
    # Remove any spaces or dashes from code
    code = code.replace(' ', '').replace('-', '')
    
    # Verify code length
    totp_digits = getattr(settings, 'TOTP_DIGITS', 6)
    if len(code) != totp_digits:
        return False
    
    # Create TOTP instance
    totp_interval = getattr(settings, 'TOTP_INTERVAL', 30)
    totp = pyotp.TOTP(secret, digits=totp_digits, interval=totp_interval)
    
    # Verify with time window
    return totp.verify(code, valid_window=valid_window)


def generate_backup_codes(count: int = 10) -> Tuple[List[str], List[str]]:
    """
    Generate backup codes for account recovery
    
    Args:
        count: Number of backup codes to generate
    
    Returns:
        Tuple of (plaintext_codes, hashed_codes)
        - plaintext_codes: List to show user (only time they see these)
        - hashed_codes: List to store in database
    """
    plaintext_codes = []
    hashed_codes = []
    
    for _ in range(count):
        # Generate 8-character alphanumeric code
        code = secrets.token_hex(4).upper()  # 8 hex chars
        plaintext_codes.append(code)
        
        # Hash the code for storage
        hashed = hashlib.sha256(code.encode()).hexdigest()
        hashed_codes.append(hashed)
    
    return plaintext_codes, hashed_codes


def verify_backup_code(code: str, stored_hashes: List[str]) -> bool:
    """
    Verify a backup code against stored hashes
    
    Args:
        code: Backup code entered by user
        stored_hashes: List of hashed backup codes from database
    
    Returns:
        True if code is valid and unused, False otherwise
    """
    if not code or not stored_hashes:
        return False
    
    # Remove spaces and convert to uppercase
    code = code.replace(' ', '').replace('-', '').upper()
    
    # Hash the provided code
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    
    # Check if hash exists in stored hashes
    return code_hash in stored_hashes


def mark_backup_code_used(code: str, user_2fa: UserTwoFactor, db: Session) -> bool:
    """
    Mark a backup code as used (remove from available codes)
    
    Args:
        code: Backup code that was used
        user_2fa: UserTwoFactor model instance
        db: Database session
    
    Returns:
        True if code was marked as used, False if invalid
    """
    code = code.replace(' ', '').replace('-', '').upper()
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    
    # Parse stored backup codes
    if not user_2fa.backup_codes_hash:
        return False
    
    try:
        stored_hashes = json.loads(user_2fa.backup_codes_hash)
    except json.JSONDecodeError:
        return False
    
    # Check if code exists and hasn't been used
    if code_hash not in stored_hashes:
        return False
    
    if code_hash in user_2fa.backup_codes_used:
        return False  # Already used
    
    # Mark as used
    user_2fa.backup_codes_used.append(code_hash)
    db.commit()
    
    return True


def create_trusted_device_token(user_id: str, device_info: dict) -> str:
    """
    Create a secure token for trusted device
    
    Args:
        user_id: User's UUID
        device_info: Dict with device_name, device_fingerprint, ip_address, user_agent
    
    Returns:
        Secure random token (32 bytes = 64 hex chars)
    """
    # Generate cryptographically secure random token
    token = secrets.token_urlsafe(32)
    return token


def hash_device_token(token: str) -> str:
    """
    Hash a device token for storage
    
    Args:
        token: Plaintext device token
    
    Returns:
        SHA-256 hash of token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_trusted_device(
    token: str,
    user_id: str,
    device_fingerprint: str,
    db: Session
) -> Optional[TrustedDevice]:
    """
    Verify a trusted device token
    
    Args:
        token: Device token from cookie/storage
        user_id: User's UUID
        device_fingerprint: Current device fingerprint
        db: Database session
    
    Returns:
        TrustedDevice instance if valid, None otherwise
    """
    token_hash = hash_device_token(token)
    
    # Find device by token hash and user
    device = db.query(TrustedDevice).filter(
        TrustedDevice.user_id == user_id,
        TrustedDevice.token_hash == token_hash,
        TrustedDevice.device_fingerprint == device_fingerprint,
        TrustedDevice.is_active == True
    ).first()
    
    if not device:
        return None
    
    # Check if expired
    if device.is_expired():
        return None
    
    # Update last used timestamp
    device.last_used_at = datetime.utcnow()
    db.commit()
    
    return device


def create_trusted_device(
    user_id: str,
    device_name: str,
    device_fingerprint: str,
    ip_address: str,
    user_agent: str,
    db: Session,
    expiry_days: int = None
) -> Tuple[TrustedDevice, str]:
    """
    Create a new trusted device entry
    
    Args:
        user_id: User's UUID
        device_name: User-friendly device name
        device_fingerprint: Browser fingerprint hash
        ip_address: IP address at creation
        user_agent: Full user agent string
        db: Database session
        expiry_days: Days until expiration (default from settings)
    
    Returns:
        Tuple of (TrustedDevice instance, plaintext token)
    """
    if expiry_days is None:
        expiry_days = getattr(settings, 'TRUSTED_DEVICE_EXPIRY_DAYS', 30)
    
    # Generate token
    token = create_trusted_device_token(
        user_id,
        {
            'device_name': device_name,
            'device_fingerprint': device_fingerprint,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
    )
    token_hash = hash_device_token(token)
    
    # Create device record
    device = TrustedDevice(
        user_id=user_id,
        device_name=device_name,
        device_fingerprint=device_fingerprint,
        token_hash=token_hash,
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.utcnow() + timedelta(days=expiry_days)
    )
    
    db.add(device)
    db.commit()
    db.refresh(device)
    
    return device, token


def revoke_trusted_device(device_id: str, db: Session) -> bool:
    """
    Revoke a trusted device
    
    Args:
        device_id: Device UUID
        db: Database session
    
    Returns:
        True if revoked, False if not found
    """
    device = db.query(TrustedDevice).filter(
        TrustedDevice.device_id == device_id
    ).first()
    
    if not device:
        return False
    
    device.is_active = False
    db.commit()
    
    return True


def get_remaining_backup_codes(user_2fa: UserTwoFactor) -> int:
    """
    Get count of remaining (unused) backup codes
    
    Args:
        user_2fa: UserTwoFactor instance
    
    Returns:
        Number of remaining backup codes
    """
    if not user_2fa.backup_codes_hash:
        return 0
    
    try:
        stored_hashes = json.loads(user_2fa.backup_codes_hash)
        total_codes = len(stored_hashes)
        used_codes = len(user_2fa.backup_codes_used)
        return total_codes - used_codes
    except json.JSONDecodeError:
        return 0

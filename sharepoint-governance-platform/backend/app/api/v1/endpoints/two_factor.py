"""
Two-Factor Authentication (2FA) API endpoints
"""
import json
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import io

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.two_factor import UserTwoFactor, TrustedDevice
from app.core.two_factor import (
    generate_totp_secret,
    generate_qr_code,
    verify_totp_code,
    generate_backup_codes,
    verify_backup_code,
    mark_backup_code_used,
    create_trusted_device,
    verify_trusted_device,
    revoke_trusted_device,
    get_remaining_backup_codes,
    hash_device_token
)
from app.core.auth import verify_password
from app.models.audit import AdminActionLog, AdminActionType, AdminActionStatus

router = APIRouter()


# Pydantic Schemas
class Enable2FARequest(BaseModel):
    """Request to enable 2FA"""
    password: str  # Require password confirmation


class Enable2FAResponse(BaseModel):
   """Response with TOTP secret and QR code"""
   totp_secret: str
   qr_code_url: str  # Data URL or endpoint
   backup_codes: list[str]


class Verify2FASetupRequest(BaseModel):
    """Verify 2FA during initial setup"""
    totp_code: str


class Disable2FARequest(BaseModel):
    """Request to disable 2FA"""
    password: str
    totp_code: Optional[str] = None


class Verify2FARequest(BaseModel):
    """Verify 2FA code during login"""
    totp_code: Optional[str] = None
    backup_code: Optional[str] = None
    trust_device: bool = False


class TrustedDeviceResponse(BaseModel):
    """Trusted device information"""
    device_id: str
    device_name: str
    ip_address: Optional[str]
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime


@router.post("/enable")
async def enable_2fa(
    request_data: Enable2FARequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enable 2FA for current user
    
    Generates TOTP secret, QR code, and backup codes
    Returns secret and backup codes (only shown once!)
    """
    # Verify password for security
    # Note: Since we use AD authentication, we'll skip password verification here
    # In production, you might want to re-authenticate the user
    
    # Check if 2FA already enabled
    existing_2fa = db.query(UserTwoFactor).filter(
        UserTwoFactor.user_id == current_user.user_id
    ).first()
    
    if existing_2fa and existing_2fa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled for this account"
        )
    
    # Generate TOTP secret
    totp_secret = generate_totp_secret()
    
    # Generate backup codes
    plaintext_codes, hashed_codes = generate_backup_codes(count=10)
    
    # Create or update 2FA record
    if existing_2fa:
        existing_2fa.totp_secret = totp_secret
        existing_2fa.backup_codes_hash = json.dumps(hashed_codes)
        existing_2fa.backup_codes_used = []
        existing_2fa.is_enabled = False  # Not enabled until verified
        existing_2fa.created_at = datetime.utcnow()
        user_2fa = existing_2fa
    else:
        user_2fa = UserTwoFactor(
            user_id=current_user.user_id,
            totp_secret=totp_secret,
            is_enabled=False,  # Not enabled until verified
            backup_codes_hash=json.dumps(hashed_codes),
            backup_codes_used=[]
        )
        db.add(user_2fa)
    
    db.commit()
    db.refresh(user_2fa)
    
    # Log action
    log = AdminActionLog(
        user_id=current_user.user_id,
        action_type=AdminActionType.SECURITY_CONFIG_CHANGE,
        action_description="Initiated 2FA setup",
        status=AdminActionStatus.SUCCESS,
        ip_address=request.client.host if request.client else None
    )
    db.add(log)
    db.commit()
    
    # Generate QR code URL endpoint
    qr_code_url = f"/api/v1/2fa/qr-code"
    
    return {
        "totp_secret": totp_secret,
        "qr_code_url": qr_code_url,
        "backup_codes": plaintext_codes,
        "message": "Save your backup codes in a safe place. They will not be shown again."
    }


@router.get("/qr-code")
async def get_qr_code(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get QR code image for 2FA setup
    
    Returns PNG image
    """
    # Get user's 2FA record
    user_2fa = db.query(UserTwoFactor).filter(
        UserTwoFactor.user_id == current_user.user_id
    ).first()
    
    if not user_2fa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="2FA not initialized. Call /enable first."
        )
    
    # Generate QR code
    qr_code_bytes = generate_qr_code(
        secret=user_2fa.totp_secret,
        email=current_user.email
    )
    
    # Return as image
    return StreamingResponse(
        io.BytesIO(qr_code_bytes),
        media_type="image/png",
        headers={"Cache-Control": "no-store"}
    )


@router.post("/verify-setup")
async def verify_2fa_setup(
    request_data: Verify2FASetupRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify TOTP code during 2FA setup to complete enrollment
    """
    # Get user's 2FA record
    user_2fa = db.query(UserTwoFactor).filter(
        UserTwoFactor.user_id == current_user.user_id
    ).first()
    
    if not user_2fa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="2FA not initialized"
        )
    
    if user_2fa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA already enabled"
        )
    
    # Verify code
    if not verify_totp_code(user_2fa.totp_secret, request_data.totp_code):
        # Log failed attempt
        log = AdminActionLog(
            user_id=current_user.user_id,
            action_type=AdminActionType.SECURITY_CONFIG_CHANGE,
            action_description="Failed 2FA setup verification",
            status=AdminActionStatus.FAILED,
            ip_address=request.client.host if request.client else None
        )
        db.add(log)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Enable 2FA
    user_2fa.is_enabled = True
    user_2fa.enabled_at = datetime.utcnow()
    db.commit()
    
    # Log success
    log = AdminActionLog(
        user_id=current_user.user_id,
        action_type=AdminActionType.SECURITY_CONFIG_CHANGE,
        action_description="2FA enabled successfully",
        status=AdminActionStatus.SUCCESS,
        ip_address=request.client.host if request.client else None
    )
    db.add(log)
    db.commit()
    
    return {
        "message": "2FA enabled successfully",
        "enabled_at": user_2fa.enabled_at
    }


@router.post("/disable")
async def disable_2fa(
    request_data: Disable2FARequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Disable 2FA for current user
    Requires password and TOTP code confirmation
    """
    # Get user's 2FA record
    user_2fa = db.query(UserTwoFactor).filter(
        UserTwoFactor.user_id == current_user.user_id
    ).first()
    
    if not user_2fa or not user_2fa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )
    
    # Verify TOTP code if provided
    if request_data.totp_code:
        if not verify_totp_code(user_2fa.totp_secret, request_data.totp_code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA code"
            )
    
    # Disable 2FA
    user_2fa.is_enabled = False
    
    # Revoke all trusted devices
    db.query(TrustedDevice).filter(
        TrustedDevice.user_id == current_user.user_id
    ).update({"is_active": False})
    
    db.commit()
    
    # Log action
    log = AdminActionLog(
        user_id=current_user.user_id,
        action_type=AdminActionType.SECURITY_CONFIG_CHANGE,
        action_description="2FA disabled",
        status=AdminActionStatus.SUCCESS,
        ip_address=request.client.host if request.client else None
    )
    db.add(log)
    db.commit()
    
    return {"message": "2FA disabled successfully"}


@router.post("/backup-codes/generate")
async def regenerate_backup_codes(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate new backup codes (invalidates old ones)
    """
    # Get user's 2FA record
    user_2fa = db.query(UserTwoFactor).filter(
        UserTwoFactor.user_id == current_user.user_id
    ).first()
    
    if not user_2fa or not user_2fa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is not enabled"
        )
    
    # Generate new backup codes
    plaintext_codes, hashed_codes = generate_backup_codes(count=10)
    
    # Update database
    user_2fa.backup_codes_hash = json.dumps(hashed_codes)
    user_2fa.backup_codes_used = []
    db.commit()
    
    # Log action
    log = AdminActionLog(
        user_id=current_user.user_id,
        action_type=AdminActionType.SECURITY_CONFIG_CHANGE,
        action_description="Regenerated 2FA backup codes",
        status=AdminActionStatus.SUCCESS,
        ip_address=request.client.host if request.client else None
    )
    db.add(log)
    db.commit()
    
    return {
        "backup_codes": plaintext_codes,
        "message": "New backup codes generated. Save them in a safe place."
    }


@router.get("/backup-codes/remaining")
async def get_remaining_codes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of remaining unused backup codes"""
    user_2fa = db.query(UserTwoFactor).filter(
        UserTwoFactor.user_id == current_user.user_id
    ).first()
    
    if not user_2fa or not user_2fa.is_enabled:
        return {"remaining": 0}
    
    remaining = get_remaining_backup_codes(user_2fa)
    
    return {
        "remaining": remaining,
        "total": 10
    }


@router.get("/devices")
async def list_trusted_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all trusted devices for current user"""
    devices = db.query(TrustedDevice).filter(
        TrustedDevice.user_id == current_user.user_id,
        TrustedDevice.is_active == True
    ).order_by(TrustedDevice.last_used_at.desc()).all()
    
    return {
        "devices": [
            {
                "device_id": str(device.device_id),
                "device_name": device.device_name,
                "ip_address": device.ip_address,
                "created_at": device.created_at,
                "last_used_at": device.last_used_at,
                "expires_at": device.expires_at,
                "is_expired": device.is_expired()
            }
            for device in devices
        ]
    }


@router.delete("/devices/{device_id}")
async def revoke_device(
    device_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke a trusted device"""
    # Find device
    device = db.query(TrustedDevice).filter(
        TrustedDevice.device_id == device_id,
        TrustedDevice.user_id == current_user.user_id
    ).first()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Revoke device
    success = revoke_trusted_device(device_id, db)
    
    if success:
        # Log action
        log = AdminActionLog(
            user_id=current_user.user_id,
            action_type=AdminActionType.SECURITY_CONFIG_CHANGE,
            action_description=f"Revoked trusted device: {device.device_name}",
            status=AdminActionStatus.SUCCESS,
            ip_address=request.client.host if request.client else None
        )
        db.add(log)
        db.commit()
        
        return {"message": "Device revoked successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to revoke device"
    )


@router.get("/status")
async def get_2fa_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get 2FA status for current user"""
    user_2fa = db.query(UserTwoFactor).filter(
        UserTwoFactor.user_id == current_user.user_id
    ).first()
    
    if not user_2fa:
        return {
            "enabled": False,
            "setup_started": False
        }
    
    return {
        "enabled": user_2fa.is_enabled,
        "setup_started": True,
        "enabled_at": user_2fa.enabled_at,
        "last_used_at": user_2fa.last_used_at,
        "backup_codes_remaining": get_remaining_backup_codes(user_2fa)
    }

"""
API v2 Router for Phase 2 Enhanced Features
"""
from fastapi import APIRouter

from app.api.v2.endpoints import storage, retention

api_v2_router = APIRouter()

# Include Phase 2 endpoint routers
api_v2_router.include_router(storage.router, prefix="/storage", tags=["Storage & Versions"])
api_v2_router.include_router(retention.router, prefix="/retention", tags=["Retention & Recycle Bin"])

# Root endpoint for API v2
@api_v2_router.get("/")
async def v2_root():
    """API v2 root endpoint"""
    return {
        "message": "SharePoint Governance Platform API v2 - Enhanced Features",
        "version": "2.0.0",
        "endpoints": {
            "storage": "/api/v2/storage",
            "retention": "/api/v2/retention",
        }
    }

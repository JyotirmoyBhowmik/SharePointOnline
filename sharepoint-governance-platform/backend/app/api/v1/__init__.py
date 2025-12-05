"""
API Router aggregating all endpoint modules
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, sites, access_reviews, audit, dashboard, two_factor

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(two_factor.router, prefix="/2fa", tags=["Two-Factor Authentication"])
api_router.include_router(sites.router, prefix="/sites", tags=["Sites"])
api_router.include_router(access_reviews.router, prefix="/access-reviews", tags=["Access Reviews"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit & Compliance"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

# Placeholder endpoint
@api_router.get("/")
async def root():
    """Root API endpoint"""
    return {
        "message": "SharePoint Governance Platform API",
        "version": "1.0.0",
        "docs": "/api/v1/docs",
        "endpoints": {
            "auth": "/api/v1/auth",
            "2fa": "/api/v1/2fa",
            "sites": "/api/v1/sites",
            "access_reviews": "/api/v1/access-reviews",
            "audit": "/api/v1/audit",
            "dashboard": "/api/v1/dashboard",
            "health": "/health"
        }
    }

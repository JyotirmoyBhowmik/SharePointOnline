"""
API v3 Router for Phase 3 Advanced Features
"""
from fastapi import APIRouter

from app.api.v3.endpoints import analytics, powerbi, tenants

api_v3_router = APIRouter()

# Include Phase 3 endpoint routers
api_v3_router.include_router(analytics.router, prefix="/analytics", tags=["AI Analytics & Compliance"])
api_v3_router.include_router(powerbi.router, prefix="/powerbi", tags=["Power BI Integration"])
api_v3_router.include_router(tenants.router, prefix="", tags=["Multi-Tenant Management"])

# Root endpoint for API v3
@api_v3_router.get("/")
async def v3_root():
    """API v3 root endpoint"""
    return {
        "message": "SharePoint Governance Platform API v3 - Advanced Features",
        "version": "3.0.0",
        "features": [
            "AI-Powered Anomaly Detection",
            "Risk Scoring Engine",
            "Advanced Compliance Reporting",
            "Executive Summary Generation",
            "Power BI Integration (5 Datasets)",
            "Multi-Tenant Support"
        ],
        "endpoints": {
            "analytics": "/api/v3/analytics",
            "powerbi": "/api/v3/powerbi",
            "tenants": "/api/v3/tenants",
        }
    }

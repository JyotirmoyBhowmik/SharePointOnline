"""
SharePoint Online Governance Platform - Main Application Entry Point
====================================================================

Author: Jyotirmoy Bhowmik
Email: jyotirmoy.bhowmik@company.com  
Version: 3.0.0
Created: 2025
Last Modified: December 5, 2025

Description:
    FastAPI application entry point for the SharePoint Governance Platform.
    Initializes the REST API, configures middleware, sets up background jobs,
    and exposes endpoints for governance, audit, and compliance operations.

Maintained by: Jyotirmoy Bhowmik
"""

# Standard library imports
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import logging

# Third-party imports - FastAPI framework and utilities
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import make_asgi_app
from sqlalchemy import text

# Application imports - Configuration and routing
from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import api_router
from app.api.v2 import api_v2_router
from app.api.v3 import api_v3_router
from app.tasks.scheduler import start_scheduler, stop_scheduler

# Setup structured logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    from app.core.cache import cache
    
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT if hasattr(settings, 'ENVIRONMENT') else 'production'}")
    
    # Initialize Redis connection
    await cache.connect()
    logger.info("Redis connection initialized")
    
    # Start background job scheduler
    if not settings.DEBUG:
        start_scheduler()
        logger.info("Background job scheduler started")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")
    stop_scheduler()
    
    # Cleanup resources
    await cache.close()


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_v2_router, prefix="/api/v2")
app.include_router(api_v3_router, prefix="/api/v3")

# [DEV MODULE] Conditionally include development router
if settings.DEBUG:
    from app.api.dev_router import router as dev_router
    app.include_router(dev_router, prefix="/api/dev", tags=["Development"])
    logger.info("Dev module enabled: /api/dev/seed")

# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Returns detailed status of all components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "components": {}
    }
    
    try:
        # Check database
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            health_status["components"]["database"] = "connected"
        finally:
            db.close()
        return health_status
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = "disconnected"
        health_status["error"] = str(e)
        return health_status


@app.get("/health/redis")
async def health_check_redis():
    """Redis health check"""
    from app.core.cache import cache
    
    try:
        is_healthy = await cache.ping()
        if is_healthy:
            return {"status": "healthy", "redis": "connected"}
        else:
            return {"status": "unhealthy", "redis": "disconnected"}
    except Exception as e:
        return {"status": "unhealthy", "redis": "disconnected", "error": str(e)}



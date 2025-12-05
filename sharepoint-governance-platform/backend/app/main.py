"""
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware # Added this import based on the instruction's context
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import api_router
from app.api.v2 import api_v2_router
from app.api.v3 import api_v3_router
from app.tasks.scheduler import start_scheduler, stop_scheduler
from prometheus_fastapi_instrumentator import Instrumentator, make_asgi_app # Added this import based on the instruction's context

# Setup structured logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Start background job scheduler
    if not settings.DEBUG:
        start_scheduler()
        logger.info("Background job scheduler started")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")
    stop_scheduler()
    
    # Cleanup resources
    from app.core.cache import redis_client
    await redis_client.close()


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
    allow_origins=settings.ALLOWED_ORIGINS,
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
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "components": {}
    }
    
    try:
        # Check database
        from app.db.session import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@app.get("/health/redis")
async def health_check_redis():
    """Redis health check"""
    from app.core.cache import redis_client
    
    try:
        await redis_client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "redis": "disconnected", "error": str(e)}


@app.on_event("startup")
async def startup_event():
    """Tasks to run on application startup"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Initialize background jobs
    if not settings.DEBUG:
        from app.tasks.scheduler import start_scheduler
        start_scheduler()
        logger.info("Background job scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    """Tasks to run on application shutdown"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Shutting down {settings.APP_NAME}")
    
    # Cleanup resources
    from app.core.cache import redis_client
    await redis_client.close()

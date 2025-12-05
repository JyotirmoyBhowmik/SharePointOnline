"""
Background job scheduler using APScheduler
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def site_discovery_job():
    """
    Background job for automated site discovery
    Runs daily at 2 AM
    """
    logger.info("Starting scheduled site discovery job")
    
    try:
        from app.services.site_discovery_service import SiteDiscoveryService
        
        db = SessionLocal()
        try:
            discovery_service = SiteDiscoveryService(db)
            stats = await discovery_service.discover_all_sites()
            
            logger.info(f"Site discovery job completed successfully: {stats}")
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Site discovery job failed: {str(e)}", exc_info=True)


async def audit_sync_job():
    """
    Background job for syncing audit logs from Microsoft 365
    Runs every 6 hours
    """
    logger.info("Starting scheduled audit log sync job")
    
    try:
        from app.services.audit_service import AuditService
        from datetime import timedelta
        
        db = SessionLocal()
        try:
            audit_service = AuditService(db)
            
            # Sync last 6 hours of audit logs
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=6)
            
            count = await audit_service.sync_audit_logs(start_date, end_date)
            
            logger.info(f"Audit sync job completed: {count} logs synced")
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Audit sync job failed: {str(e)}", exc_info=True)


async def user_sync_job():
    """
    Background job for syncing users from Active Directory
    Runs daily at 1 AM
    """
    logger.info("Starting scheduled user sync job")
    
    try:
        from app.services.user_service import UserService
        
        db = SessionLocal()
        try:
            user_service = UserService(db)
            stats = await user_service.sync_users_from_ad()
            
            logger.info(f"User sync job completed: {stats}")
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"User sync job failed: {str(e)}", exc_info=True)


async def access_review_initiation_job():
    """
    Background job for initiating quarterly access reviews
    Runs on the 1st of every quarter (Jan, Apr, Jul, Oct) at midnight
    """
    logger.info("Starting scheduled access review initiation job")
    
    try:
        from app.services.access_review_service import AccessReviewService
        
        db = SessionLocal()
        try:
            review_service = AccessReviewService(db)
            stats = await review_service.initiate_quarterly_reviews()
            
            logger.info(f"Access review initiation completed: {stats}")
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Access review initiation job failed: {str(e)}", exc_info=True)


def start_scheduler():
    """
    Initialize and start the background job scheduler
    """
    logger.info("Initializing background job scheduler")
    
    # Add site discovery job (daily at 2 AM)
    scheduler.add_job(
        site_discovery_job,
        trigger=CronTrigger.from_crontab(settings.SITE_DISCOVERY_SCHEDULE_CRON),
        id='site_discovery',
        name='Daily Site Discovery',
        replace_existing=True
    )
    logger.info(f"Scheduled: Site Discovery - {settings.SITE_DISCOVERY_SCHEDULE_CRON}")
    
    # Add audit sync job (every 6 hours)
    scheduler.add_job(
        audit_sync_job,
        trigger=CronTrigger.from_crontab(settings.AUDIT_SYNC_SCHEDULE_CRON),
        id='audit_sync',
        name='Audit Log Sync',
        replace_existing=True
    )
    logger.info(f"Scheduled: Audit Sync - {settings.AUDIT_SYNC_SCHEDULE_CRON}")
    
    # Add user sync job (daily at 1 AM)
    scheduler.add_job(
        user_sync_job,
        trigger=CronTrigger.from_crontab(settings.USER_SYNC_SCHEDULE_CRON),
        id='user_sync',
        name='User Sync from AD',
        replace_existing=True
    )
    logger.info(f"Scheduled: User Sync - {settings.USER_SYNC_SCHEDULE_CRON}")
    
    # Add access review initiation job (quarterly on 1st at midnight)
    scheduler.add_job(
        access_review_initiation_job,
        trigger=CronTrigger.from_crontab(settings.ACCESS_REVIEW_SCHEDULE_CRON),
        id='access_review_initiation',
        name='Quarterly Access Review Initiation',
        replace_existing=True
    )
    logger.info(f"Scheduled: Access Review - {settings.ACCESS_REVIEW_SCHEDULE_CRON}")
    
    # Start the scheduler
    scheduler.start()
    logger.info("Background job scheduler started successfully")


def stop_scheduler():
    """Stop the background job scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background job scheduler stopped")

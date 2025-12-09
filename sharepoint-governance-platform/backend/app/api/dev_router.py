from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.dev_utils.seeder import run_all_seeds
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/seed", status_code=status.HTTP_201_CREATED)
def seed_data(db: Session = Depends(get_db)):
    """
    [DEV ONLY] Seed the database with sample data.
    """
    logger.info("Triggering database seed...")
    try:
        results = run_all_seeds(db)
        return {"message": "Database seeded successfully", "details": results}
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        return {"error": str(e)}

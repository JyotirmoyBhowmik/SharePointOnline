from sqlalchemy.orm import Session
from faker import Faker
import random
from datetime import datetime, timedelta
import logging

from app.models.user import User
from app.models.site import Site
# Assuming these models exist based on file structure
# If not, I will use generic dictionaries or adjust imports
from app.core.auth import get_password_hash

logger = logging.getLogger(__name__)
fake = Faker()

def seed_users(db: Session, count: int = 5):
    """Seed random users"""
    created_users = []
    logger.info(f"Seeding {count} users...")
    
    # Create Admin
    admin_email = "admin@example.com"
    if not db.query(User).filter(User.email == admin_email).first():
        admin = User(
            email=admin_email,
            full_name="System Admin",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True,
            role="Global Admin"
        )
        db.add(admin)
        created_users.append(admin)

    for _ in range(count):
        user = User(
            email=fake.email(),
            full_name=fake.name(),
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_superuser=False,
            role=random.choice(["Site Owner", "User", "Compliance Officer"])
        )
        db.add(user)
        created_users.append(user)
    
    db.commit()
    logger.info("Users seeded.")
    return len(created_users)

def seed_sites(db: Session, count: int = 10):
    """Seed random SharePoint sites"""
    logger.info(f"Seeding {count} sites...")
    departments = ["HR", "Finance", "IT", "Legal", "Marketing"]
    
    for _ in range(count):
        dept = random.choice(departments)
        site = Site(
            site_name=f"{dept} - {fake.catch_phrase()}",
            site_url=fake.url(),
            owner_email=fake.email(),
            storage_used_gb=random.uniform(0.1, 50.0),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365)),
            sensitivity_label=random.choice(["General", "Confidential", "Highly Confidential"]),
            external_sharing_enabled=random.choice([True, False]),
            last_activity_date=datetime.utcnow() - timedelta(days=random.randint(0, 30))
        )
        db.add(site)
    
    db.commit()
    logger.info("Sites seeded.")
    return count

def run_all_seeds(db: Session):
    u_count = seed_users(db, 10)
    s_count = seed_sites(db, 20)
    return {"users_seeded": u_count, "sites_seeded": s_count}

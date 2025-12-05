"""
Phase 3 AI-Powered Anomaly Detection Service
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import numpy as np

from app.models.site import SharePointSite
from app.models.audit import AuditLog
from app.models.access_review import AccessReviewCycle

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    """Service for AI-powered anomaly detection"""
    
    def __init__(self, db: Session):
        self.db = db
        self.model = None
    
    async def detect_access_anomalies(
        self,
        site_id: Optional[str] = None,
        days: int = 30
    ) -> List[Dict]:
        """
        Detect anomalous access patterns using Isolation Forest
        
        Args:
            site_id: Optional site ID to filter
            days: Days of historical data to analyze
        
        Returns:
            List of detected anomalies
        """
        logger.info(f"Detecting access anomalies for last {days} days")
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(AuditLog).filter(
            AuditLog.event_datetime >= cutoff_date
        )
        
        if site_id:
            query = query.filter(AuditLog.site_id == site_id)
        
        audit_logs = query.all()
        
        if len(audit_logs) < 100:
            logger.warning("Insufficient data for anomaly detection")
            return []
        
        # Extract features for ML model
        features = self._extract_features(audit_logs)
        
        # Use Isolation Forest for anomaly detection
        try:
            from sklearn.ensemble import IsolationForest
            
            if self.model is None:
                self.model = IsolationFores(
                    contamination=0.05,  # 5% anomaly rate
                    random_state=42
                )
            
            # Train and predict
            predictions = self.model.fit_predict(features)
            
            # Extract anomalies
            anomalies = []
            for idx, prediction in enumerate(predictions):
                if prediction == -1:  # Anomaly
                    log = audit_logs[idx]
                    anomalies.append({
                        "audit_id": str(log.audit_id),
                        "event_type": log.event_type,
                        "operation": log.operation,
                        "user_email": log.user_email,
                        "site_url": log.site_url,
                        "event_datetime": log.event_datetime.isoformat(),
                        "anomaly_score": float(self.model.score_samples([features[idx]])[0]),
                        "reason": self._explain_anomaly(log, features[idx]),
                    })
            
            logger.info(f"Detected {len(anomalies)} anomalies")
            return anomalies
            
        except ImportError:
            logger.error("scikit-learn not installed, using rule-based detection")
            return self._rule_based_anomaly_detection(audit_logs)
    
    def _extract_features(self, logs: List[AuditLog]) -> np.ndarray:
        """Extract numerical features from audit logs"""
        features = []
        
        for log in logs:
            # Convert to numerical features
            hour_of_day = log.event_datetime.hour
            day_of_week = log.event_datetime.weekday()
            
            # Binary encoding for event types
            is_download = 1 if log.operation in ['FileDownloaded', 'FileAccessed'] else 0
            is_permission_change= 1 if 'Permission' in log.operation else 0
            is_deletion = 1 if 'Delete' in log.operation else 0
            
            features.append([
                hour_of_day,
                day_of_week,
                is_download,
                is_permission_change,
                is_deletion,
            ])
        
        return np.array(features)
    
    def _explain_anomaly(self, log: AuditLog, features: np.ndarray) -> str:
        """Generate human-readable explanation for anomaly"""
        hour = int(features[0])
        
        reasons = []
        
        if hour < 6 or hour > 22:
            reasons.append("Off-hours access")
        
        if log.operation in ['FileDownloaded', 'FileAccessed']:
            reasons.append("Unusual access pattern")
        
        if 'Permission' in log.operation:
            reasons.append("Permission modification")
        
        return "; ".join(reasons) if reasons else "Anomalous pattern detected"
    
    def _rule_based_anomaly_detection(self, logs: List[AuditLog]) -> List[Dict]:
        """Fallback rule-based anomaly detection"""
        anomalies = []
        
        for log in logs:
            is_anomaly = False
            reasons = []
            
            # Off-hours access (before 6 AM or after 10 PM)
            if log.event_datetime.hour < 6 or log.event_datetime.hour > 22:
                is_anomaly = True
                reasons.append("Off-hours access")
            
            # Weekend access for sensitive operations
            if log.event_datetime.weekday() >= 5 and 'Permission' in log.operation:
                is_anomaly = True
                reasons.append("Weekend permission change")
            
            if is_anomaly:
                anomalies.append({
                    "audit_id": str(log.audit_id),
                    "event_type": log.event_type,
                    "operation": log.operation,
                    "user_email": log.user_email,
                    "site_url": log.site_url,
                    "event_datetime": log.event_datetime.isoformat(),
                    "anomaly_score": -1.0,
                    "reason": "; ".join(reasons),
                })
        
        return anomalies
    
    async def calculate_site_risk_score(self, site_id: str) -> Dict:
        """
        Calculate risk score for a site
        
        Args:
            site_id: Site ID
        
        Returns:
            Risk score and breakdown
        """
        logger.info(f"Calculating risk score for site {site_id}")
        
        site = self.db.query(SharePointSite).filter(
            SharePointSite.site_id == site_id
        ).first()
        
        if not site:
            raise ValueError(f"Site {site_id} not found")
        
        risk_score = 0
        factors = []
        
        # Factor 1: Inactivity (max 20 points)
        if site.last_activity:
            days_inactive = (datetime.utcnow() - site.last_activity).days
            if days_inactive > 180:
                risk_score += 20
                factors.append(f"Inactive for {days_inactive} days")
            elif days_inactive > 90:
                risk_score += 10
                factors.append(f"Inactive for {days_inactive} days")
        
        # Factor 2: Storage usage (max 15 points)
        if site.storage_usage_percent > 90:
            risk_score += 15
            factors.append("Storage usage critical")
        elif site.storage_usage_percent > 75:
            risk_score += 8
            factors.append("Storage usage high")
        
        # Factor 3: External users (max 25 points)
        from app.models.site import AccessMatrix
        external_users = self.db.query(AccessMatrix).filter(
            AccessMatrix.site_id == site_id,
            AccessMatrix.is_external_user == True
        ).count()
        
        if external_users > 10:
            risk_score += 25
            factors.append(f"{external_users} external users")
        elif external_users > 0:
            risk_score += 15
            factors.append(f"{external_users} external users")
        
        # Factor 4: Overdue access reviews (max 20 points)
        overdue_reviews = self.db.query(AccessReviewCycle).filter(
            AccessReviewCycle.site_id == site_id,
            AccessReviewCycle.due_date < datetime.utcnow(),
            AccessReviewCycle.status.in_(['pending', 'in_progress'])
        ).count()
        
        if overdue_reviews > 0:
            risk_score += 20
            factors.append(f"{overdue_reviews} overdue reviews")
        
        # Factor 5: Recent anomalies (max 20 points)
        recent_anomalies = await self.detect_access_anomalies(site_id=site_id, days=7)
        if len(recent_anomalies) > 5:
            risk_score += 20
            factors.append(f"{len(recent_anomalies)} recent anomalies")
        elif len(recent_anomalies) > 0:
            risk_score += 10
            factors.append(f"{len(recent_anomalies)} recent anomalies")
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "site_id": str(site_id),
            "site_name": site.name,
            "risk_score": min(risk_score, 100),
            "risk_level": risk_level,
            "risk_factors": factors,
        }


def get_anomaly_detection_service(db: Session) -> AnomalyDetectionService:
    """Dependency to get anomaly detection service"""
    return AnomalyDetectionService(db)

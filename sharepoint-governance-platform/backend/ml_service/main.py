from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SharePoint Governance ML Service",
    description="ML Inference Service for predictive analytics and anomaly detection",
    version="1.0.0"
)

class PredictionRequest(BaseModel):
    site_id: str
    features: Dict[str, Any]

class PredictionResponse(BaseModel):
    site_id: str
    risk_score: float
    anomalies: List[str]
    confidence: float

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ml-service"}

@app.get("/")
async def root():
    return {"message": "SharePoint Governance ML Service is running"}

@app.post("/predict/risk", response_model=PredictionResponse)
async def predict_risk(request: PredictionRequest):
    """
    Predict risk score for a given site based on features.
    This is a stub implementation connecting to the model skeleton.
    """
    logger.info(f"Received prediction request for site: {request.site_id}")
    
    # Placeholder logic - to be replaced by actual model inference
    # In a real implementation, this would call model.predict(request.features)
    
    risk_score = 0.15  # Low risk default
    anomalies = []
    
    # Simple rule-based logic for demonstration
    if request.features.get("external_sharing_count", 0) > 10:
        risk_score += 0.4
        anomalies.append("High external sharing detected")
        
    if request.features.get("sensitive_files_count", 0) > 50:
        risk_score += 0.3
        anomalies.append("Large volume of sensitive data")
        
    return PredictionResponse(
        site_id=request.site_id,
        risk_score=min(risk_score, 1.0),
        anomalies=anomalies,
        confidence=0.85
    )

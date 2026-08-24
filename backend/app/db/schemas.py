"""
Pydantic models used for request validation and response serialization.
Mirrors the MongoDB document shapes described in the SolSight design doc:

Panel
 ├── panel_id
 ├── location
 ├── installation_date
 ├── rated_power
 └── inspections
      ├── date
      ├── image
      ├── voltage
      ├── current
      ├── temperature
      ├── detected_defect
      ├── confidence
      └── health_score
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Panels ----------
class PanelCreate(BaseModel):
    panel_id: str
    location: str
    installation_date: str
    rated_power: float = Field(..., description="Rated power in watts")


class PanelOut(PanelCreate):
    id: str
    latest_health_score: Optional[float] = None
    latest_status: Optional[str] = None
    created_at: datetime


# ---------- Inspections ----------
class OperationalData(BaseModel):
    voltage: float
    current: float
    temperature: float
    rated_power: Optional[float] = None


class DefectPrediction(BaseModel):
    label: str
    confidence: float
    all_probabilities: Dict[str, float]


class HealthPrediction(BaseModel):
    status: str  # Healthy | Warning | Critical
    health_score: float
    probabilities: Dict[str, float]


class DegradationPoint(BaseModel):
    day: int
    predicted_health: float


class InspectionResult(BaseModel):
    panel_id: str
    date: datetime
    voltage: float
    current: float
    temperature: float
    power_output: float
    power_loss_pct: float
    detected_defect: str
    confidence: float
    health_score: float
    status: str
    degradation_forecast: List[DegradationPoint]
    recommendation: str


class InspectionOut(InspectionResult):
    id: str
    image_url: Optional[str] = None
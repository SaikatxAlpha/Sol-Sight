from datetime import datetime
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.db.mongo import panels_collection, inspections_collection
from app.db.schemas import PanelCreate, PanelOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/panels", tags=["panels"])


def _serialize_panel(doc) -> dict:
    doc["id"] = str(doc["_id"])
    doc.pop("_id", None)
    return doc


@router.post("", response_model=PanelOut)
async def create_panel(payload: PanelCreate, current_user: dict = Depends(get_current_user)):
    existing = await panels_collection.find_one({"panel_id": payload.panel_id})
    if existing:
        raise HTTPException(status_code=400, detail="A panel with this panel_id already exists")

    doc = payload.model_dump()
    doc["owner_email"] = current_user["email"]
    doc["created_at"] = datetime.utcnow()
    result = await panels_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    out = _serialize_panel(doc)
    out["latest_health_score"] = None
    out["latest_status"] = None
    return out


@router.get("", response_model=List[PanelOut])
async def list_panels(current_user: dict = Depends(get_current_user)):
    panels = []
    cursor = panels_collection.find({"owner_email": current_user["email"]})
    async for doc in cursor:
        panel = _serialize_panel(doc)
        latest = await inspections_collection.find_one(
            {"panel_id": panel["panel_id"]}, sort=[("created_at", -1)]
        )
        panel["latest_health_score"] = latest["health_score"] if latest else None
        panel["latest_status"] = latest["status"] if latest else None
        panels.append(panel)
    return panels


@router.get("/{panel_id}", response_model=PanelOut)
async def get_panel(panel_id: str, current_user: dict = Depends(get_current_user)):
    doc = await panels_collection.find_one({"panel_id": panel_id, "owner_email": current_user["email"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Panel not found")
    panel = _serialize_panel(doc)
    latest = await inspections_collection.find_one({"panel_id": panel_id}, sort=[("created_at", -1)])
    panel["latest_health_score"] = latest["health_score"] if latest else None
    panel["latest_status"] = latest["status"] if latest else None
    return panel


@router.get("/{panel_id}/history")
async def get_panel_history(panel_id: str, current_user: dict = Depends(get_current_user)):
    owner_check = await panels_collection.find_one({"panel_id": panel_id, "owner_email": current_user["email"]})
    if not owner_check:
        raise HTTPException(status_code=404, detail="Panel not found")

    cursor = inspections_collection.find({"panel_id": panel_id}).sort("created_at", 1)
    history = []
    async for doc in cursor:
        history.append({
            "date": doc["created_at"],
            "health_score": doc["health_score"],
            "status": doc["status"],
            "detected_defect": doc["detected_defect"],
            "confidence": doc["confidence"],
        })
    return history


@router.get("/{panel_id}/prediction")
async def get_panel_prediction(panel_id: str, current_user: dict = Depends(get_current_user)):
    owner_check = await panels_collection.find_one({"panel_id": panel_id, "owner_email": current_user["email"]})
    if not owner_check:
        raise HTTPException(status_code=404, detail="Panel not found")

    latest = await inspections_collection.find_one({"panel_id": panel_id}, sort=[("created_at", -1)])
    if not latest:
        raise HTTPException(status_code=404, detail="No inspections yet for this panel")
    return {
        "current_health": latest["health_score"],
        "status": latest["status"],
        "degradation_forecast": latest["degradation_forecast"],
        "recommendation": latest["recommendation"],
    }
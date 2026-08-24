from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form

from app.db.mongo import panels_collection, inspections_collection
from app.routers.auth import get_current_user
from app.services.prediction_service import prediction_service

router = APIRouter(tags=["inspections"])


@router.post("/upload-inspection")
async def upload_inspection(
    panel_id: str = Form(...),
    voltage: float = Form(...),
    current: float = Form(...),
    temperature: float = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """Accepts an inspection image + operational readings, stores the raw record.
    Analysis (CNN/MLP/BiLSTM) happens in /predict-defect so the UI can show a
    separate 'ANALYZE' step, matching the design doc's workflow."""
    panel = await panels_collection.find_one({"panel_id": panel_id, "owner_email": current_user["email"]})
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    image_bytes = await image.read() if image else None

    doc = {
        "panel_id": panel_id,
        "owner_email": current_user["email"],
        "created_at": datetime.utcnow(),
        "voltage": voltage,
        "current": current,
        "temperature": temperature,
        "rated_power": panel["rated_power"],
        "image_bytes": image_bytes,  # small demo dataset; swap for object storage in production
        "analyzed": False,
    }
    result = await inspections_collection.insert_one(doc)
    return {"inspection_id": str(result.inserted_id), "status": "uploaded"}


@router.post("/predict-defect")
async def predict_defect(
    panel_id: str = Form(...),
    voltage: float = Form(...),
    current: float = Form(...),
    temperature: float = Form(...),
    image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
):
    """Runs the full CNN -> MLP -> Bi-LSTM pipeline and persists the result."""
    panel = await panels_collection.find_one({"panel_id": panel_id, "owner_email": current_user["email"]})
    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    image_bytes = await image.read() if image else None

    # Pull this panel's health-score history for the Bi-LSTM
    history_cursor = inspections_collection.find(
        {"panel_id": panel_id, "health_score": {"$exists": True}}
    ).sort("created_at", 1)
    history: List[float] = [doc["health_score"] async for doc in history_cursor]

    result = prediction_service.run_inspection(
        image_bytes=image_bytes,
        voltage=voltage,
        current=current,
        temperature=temperature,
        rated_power=panel["rated_power"],
        history=history,
    )

    inspection_doc = {
        "panel_id": panel_id,
        "owner_email": current_user["email"],
        "created_at": datetime.utcnow(),
        "voltage": voltage,
        "current": current,
        "temperature": temperature,
        "power_output": result["power_output"],
        "power_loss_pct": result["power_loss_pct"],
        "detected_defect": result["detected_defect"],
        "confidence": result["confidence"],
        "defect_probabilities": result["defect_probabilities"],
        "health_score": result["health_score"],
        "status": result["status"],
        "health_probabilities": result["health_probabilities"],
        "degradation_forecast": result["degradation_forecast"],
        "recommendation": result["recommendation"],
        "analyzed": True,
    }
    inserted = await inspections_collection.insert_one(inspection_doc)
    inspection_doc["id"] = str(inserted.inserted_id)
    inspection_doc.pop("_id", None)
    return inspection_doc
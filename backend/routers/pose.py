"""
Pose Router — Pose classification from uploaded images.
Route: POST /pose/classify-pose
"""
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db
from routers.users import get_current_user
from ai.pose_detector import classify_pose

router = APIRouter(prefix="/pose", tags=["Pose Detection"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("/classify-pose", response_model=schemas.PosePredictionOut)
async def classify_pose_endpoint(
    file: UploadFile = File(...),
    session_duration: float = Form(0.0),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload an image → returns classified pose with confidence and feedback.
    Also saves the result to the database.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=413, detail="Image too large. Max 10 MB.")

    result = classify_pose(image_bytes, user_weight_kg=current_user.weight_kg or 70.0)

    # Persist prediction
    prediction = models.PosePrediction(
        user_id=current_user.id,
        pose_label=result["pose_label"],
        confidence=result["confidence"],
        method=result["method"],
        image_filename=file.filename or "",
        feedback=result["feedback"],
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return prediction


@router.get("/history")
def get_pose_history(
    limit: int = 20,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get recent pose prediction history for the current user."""
    predictions = (
        db.query(models.PosePrediction)
        .filter(models.PosePrediction.user_id == current_user.id)
        .order_by(models.PosePrediction.created_at.desc())
        .limit(limit)
        .all()
    )
    return predictions


@router.get("/accuracy-trend")
def get_accuracy_trend(
    days: int = 30,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return daily average confidence for pose predictions."""
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(days=days)
    predictions = (
        db.query(models.PosePrediction)
        .filter(
            models.PosePrediction.user_id == current_user.id,
            models.PosePrediction.created_at >= since,
        )
        .all()
    )
    by_date = {}
    for p in predictions:
        d = p.created_at.strftime("%m/%d")
        by_date.setdefault(d, []).append(p.confidence * 100)

    import numpy as np
    return [{"date": d, "avg_confidence": round(float(np.mean(v)), 1)} for d, v in sorted(by_date.items())]

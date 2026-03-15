"""
Workout Router — NLP workout analysis + session management.
Routes: POST /workout/analyze-workout, GET/POST /workout/sessions, POST /workout/mood
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import models
import schemas
from database import get_db
from routers.users import get_current_user
from ai.nlp_analyzer import analyze_workout

router = APIRouter(prefix="/workout", tags=["Workout & NLP"])


@router.post("/analyze-workout", response_model=schemas.NLPAnalysisOut)
def analyze_workout_endpoint(
    payload: schemas.WorkoutCreate,
    save: bool = True,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyze a natural language workout description using NLP.
    Optionally saves the session to the database (save=true by default).
    """
    result = analyze_workout(payload.text, user_weight_kg=current_user.weight_kg or 70.0)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    session_id = None
    if save:
        session = models.WorkoutSession(
            user_id=current_user.id,
            workout_type=result["intent"],
            exercise_name=result["exercise_name"],
            duration_minutes=result["duration_minutes"],
            calories_burned=result["calories_estimate"],
            sets=result["sets"],
            reps=result["reps"],
            target_muscles=", ".join(result["target_muscles"]),
            raw_text=payload.text,
            pose_accuracy=0.0,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id

    return {**result, "session_id": session_id}


@router.get("/sessions")
def get_sessions(
    limit: int = 30,
    workout_type: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get workout session history, optionally filtered by type."""
    query = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == current_user.id
    )
    if workout_type:
        query = query.filter(models.WorkoutSession.workout_type == workout_type)
    return query.order_by(models.WorkoutSession.created_at.desc()).limit(limit).all()


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.id == session_id,
        models.WorkoutSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"message": "Session deleted"}


@router.post("/mood", response_model=schemas.MoodOut, status_code=201)
def log_mood(
    payload: schemas.MoodCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log mood, energy, and stress levels."""
    for field in ["mood_level", "energy_level", "stress_level"]:
        val = getattr(payload, field)
        if not 1 <= val <= 10:
            raise HTTPException(status_code=422, detail=f"{field} must be between 1 and 10")

    log = models.MoodLog(
        user_id=current_user.id,
        mood_level=payload.mood_level,
        energy_level=payload.energy_level,
        stress_level=payload.stress_level,
        sleep_hours=payload.sleep_hours or 0.0,
        notes=payload.notes or "",
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/mood/history")
def get_mood_history(
    limit: int = 30,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.MoodLog)
        .filter(models.MoodLog.user_id == current_user.id)
        .order_by(models.MoodLog.created_at.desc())
        .limit(limit)
        .all()
    )

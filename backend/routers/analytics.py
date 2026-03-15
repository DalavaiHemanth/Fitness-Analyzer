"""
Analytics Router — Progress, fitness scores, predictions.
Routes: GET /analytics/progress, GET /analytics/fitness-score,
        GET /analytics/predict, GET /analytics/muscle-heatmap
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import models
import schemas
from database import get_db
from routers.users import get_current_user
from ai.analytics_engine import (
    compute_fitness_score,
    get_full_progress_summary,
    predict_performance,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/progress", response_model=schemas.ProgressSummary)
def get_progress(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Full dashboard data: sessions, calories, streaks, weekly chart, mood trend."""
    return get_full_progress_summary(db, current_user.id)


@router.get("/fitness-score", response_model=schemas.FitnessScore)
def get_fitness_score(
    days: int = 7,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compute fitness score for recent N days."""
    return compute_fitness_score(db, current_user.id, days=days)


@router.get("/predict", response_model=schemas.PredictionOut)
def get_prediction(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Predict next week's workout sessions and calories using linear regression."""
    return predict_performance(db, current_user.id)


@router.get("/muscle-heatmap")
def get_muscle_heatmap(
    days: int = 30,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return muscle group frequency data for body heatmap visualization.
    Output: {"chest": 5, "back": 3, "legs": 8, ...}
    """
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(days=days)
    sessions = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == current_user.id,
        models.WorkoutSession.created_at >= since,
    ).all()

    muscle_counts = {}
    for s in sessions:
        muscles = [m.strip() for m in (s.target_muscles or "").split(",") if m.strip()]
        for muscle in muscles:
            muscle_counts[muscle] = muscle_counts.get(muscle, 0) + 1

    return muscle_counts


@router.get("/calorie-trend")
def get_calorie_trend(
    days: int = 30,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Daily calorie burn trend for the past N days."""
    from datetime import datetime, timedelta
    import numpy as np

    since = datetime.utcnow() - timedelta(days=days)
    sessions = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == current_user.id,
        models.WorkoutSession.created_at >= since,
    ).all()

    by_date = {}
    for s in sessions:
        d = s.created_at.strftime("%m/%d")
        by_date[d] = by_date.get(d, 0) + s.calories_burned

    return [{"date": d, "calories": round(v, 1)} for d, v in sorted(by_date.items())]

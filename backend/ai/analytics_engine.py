"""
Analytics Engine
================
Computes fitness scores, trends, predictions, and progress summaries.

Fitness Score formula:
  score = 0.4 × frequency_score + 0.3 × accuracy_score + 0.3 × duration_score
"""
import math
from datetime import datetime, timedelta
from typing import List, Optional
import numpy as np
from sqlalchemy.orm import Session
import models

GRADE_THRESHOLDS = [(90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D"), (0, "F")]
GRADE_MESSAGES = {
    "A+": "Outstanding! You're crushing your fitness goals! 🏆",
    "A":  "Excellent work! Keep pushing hard! 💪",
    "B":  "Great progress! A little more consistency will get you to A. 🔥",
    "C":  "Good effort! Aim for 4+ sessions per week. 📈",
    "D":  "Getting there! Even small steps count. 🚶",
    "F":  "Let's get moving! Start with 2 sessions this week. 🌱",
}


def _score_to_grade(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def compute_fitness_score(db: Session, user_id: int, days: int = 7) -> dict:
    """
    Compute fitness score for the past `days` days.
    Returns score (0-100), component scores, grade, and message.
    """
    since = datetime.utcnow() - timedelta(days=days)
    sessions = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == user_id,
        models.WorkoutSession.created_at >= since
    ).all()

    if not sessions:
        return {
            "score": 0.0, "frequency_score": 0.0, "accuracy_score": 0.0,
            "duration_score": 0.0, "grade": "F",
            "message": "No sessions found for this period. Time to start! 🌱"
        }

    # ── 1. Frequency Score (0-100) ────────────────────────────────────────────
    # Target: 5 sessions/week → 100 points
    target_sessions = days / 7 * 5
    frequency_score = min(len(sessions) / target_sessions * 100, 100)

    # ── 2. Accuracy Score (0-100) ─────────────────────────────────────────────
    # Include both manual accuracy from sessions and AI confidence from predictions
    session_accuracies = [s.pose_accuracy for s in sessions if s.pose_accuracy > 0]
    
    predictions = db.query(models.PosePrediction).filter(
        models.PosePrediction.user_id == user_id,
        models.PosePrediction.created_at >= since
    ).all()
    prediction_accuracies = [p.confidence * 100 for p in predictions if p.confidence > 0]
    
    all_accuracies = session_accuracies + prediction_accuracies
    accuracy_score = float(np.mean(all_accuracies)) if all_accuracies else 50.0  # neutral default

    # ── 3. Duration Score (0-100) ─────────────────────────────────────────────
    # Target: 45 min/session average
    avg_duration = float(np.mean([s.duration_minutes for s in sessions]))
    duration_score = min(avg_duration / 45.0 * 100, 100)

    # ── Composite score ───────────────────────────────────────────────────────
    score = (0.4 * frequency_score + 0.3 * accuracy_score + 0.3 * duration_score)
    grade = _score_to_grade(score)

    return {
        "score": round(score, 2),
        "frequency_score": round(frequency_score, 2),
        "accuracy_score": round(accuracy_score, 2),
        "duration_score": round(duration_score, 2),
        "grade": grade,
        "message": GRADE_MESSAGES.get(grade, ""),
    }


def compute_streak(db: Session, user_id: int) -> int:
    """Count consecutive days with at least one workout session."""
    sessions = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == user_id
    ).order_by(models.WorkoutSession.created_at.desc()).all()

    if not sessions:
        return 0

    streak = 0
    today = datetime.utcnow().date()
    check_date = today

    session_dates = set(s.created_at.date() for s in sessions)

    while check_date in session_dates:
        streak += 1
        check_date -= timedelta(days=1)

    return streak


def get_weekly_sessions(db: Session, user_id: int, weeks: int = 8) -> List[dict]:
    """Return weekly session count for the past N weeks."""
    result = []
    for i in range(weeks - 1, -1, -1):
        week_start = datetime.utcnow() - timedelta(weeks=i + 1)
        week_end = datetime.utcnow() - timedelta(weeks=i)
        count = db.query(models.WorkoutSession).filter(
            models.WorkoutSession.user_id == user_id,
            models.WorkoutSession.created_at >= week_start,
            models.WorkoutSession.created_at < week_end,
        ).count()
        result.append({
            "week": f"W{weeks - i}",
            "label": week_start.strftime("%b %d"),
            "sessions": count,
        })
    return result


def get_mood_trend(db: Session, user_id: int, days: int = 14) -> List[dict]:
    """Return daily mood/energy averages for the past N days."""
    since = datetime.utcnow() - timedelta(days=days)
    logs = db.query(models.MoodLog).filter(
        models.MoodLog.user_id == user_id,
        models.MoodLog.created_at >= since,
    ).order_by(models.MoodLog.created_at).all()

    # Group by date
    by_date = {}
    for log in logs:
        d = log.created_at.strftime("%m/%d")
        if d not in by_date:
            by_date[d] = {"mood": [], "energy": [], "stress": []}
        by_date[d]["mood"].append(log.mood_level)
        by_date[d]["energy"].append(log.energy_level)
        by_date[d]["stress"].append(log.stress_level)

    return [
        {
            "date": d,
            "mood": round(np.mean(v["mood"]), 1),
            "energy": round(np.mean(v["energy"]), 1),
            "stress": round(np.mean(v["stress"]), 1),
        }
        for d, v in by_date.items()
    ]


def get_top_exercises(db: Session, user_id: int, limit: int = 5) -> List[dict]:
    """Return most frequently logged exercises."""
    sessions = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == user_id,
        models.WorkoutSession.exercise_name != "",
    ).all()

    counts = {}
    for s in sessions:
        name = s.exercise_name or "general workout"
        if name not in counts:
            counts[name] = {"count": 0, "total_calories": 0.0}
        counts[name]["count"] += 1
        counts[name]["total_calories"] += s.calories_burned

    return sorted(
        [{"exercise": k, **v} for k, v in counts.items()],
        key=lambda x: -x["count"]
    )[:limit]


def predict_performance(db: Session, user_id: int) -> dict:
    """
    Linear regression prediction for next-week sessions and calories.
    Uses last 8 weeks of data.
    """
    weekly = get_weekly_sessions(db, user_id, weeks=8)
    session_counts = [w["sessions"] for w in weekly]

    if sum(session_counts) == 0:
        return {
            "next_week_sessions": 0.0,
            "next_week_calories": 0.0,
            "trend": "stable",
            "message": "Not enough data yet. Log more workouts to see predictions!",
        }

    X = np.arange(len(session_counts)).reshape(-1, 1)
    y = np.array(session_counts)

    # Simple linear regression
    x_mean, y_mean = X.mean(), y.mean()
    slope = float(np.sum((X.flatten() - x_mean) * (y - y_mean)) /
                  (np.sum((X.flatten() - x_mean) ** 2) + 1e-9))
    intercept = y_mean - slope * x_mean

    next_val = max(0, intercept + slope * len(session_counts))

    # Calorie estimate: avg calories per session × predicted sessions
    sessions = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == user_id
    ).all()
    avg_cals = float(np.mean([s.calories_burned for s in sessions])) if sessions else 200.0
    next_cals = round(next_val * avg_cals, 1)

    trend = "improving" if slope > 0.1 else ("declining" if slope < -0.1 else "stable")
    messages = {
        "improving": "You're on a roll! Keep the momentum going! 📈",
        "stable": "Consistent effort. Try adding one more session this week. 🎯",
        "declining": "Looks like things slowed down. Let's bounce back! 💪",
    }

    return {
        "next_week_sessions": round(next_val, 1),
        "next_week_calories": round(next_cals, 1),
        "trend": trend,
        "message": messages[trend],
    }


def get_full_progress_summary(db: Session, user_id: int) -> dict:
    """Aggregate all progress analytics for the dashboard."""
    since_30 = datetime.utcnow() - timedelta(days=30)
    sessions = db.query(models.WorkoutSession).filter(
        models.WorkoutSession.user_id == user_id,
        models.WorkoutSession.created_at >= since_30,
    ).all()

    fitness = compute_fitness_score(db, user_id)
    streak = compute_streak(db, user_id)

    total_duration = sum(s.duration_minutes for s in sessions)
    total_calories = sum(s.calories_burned for s in sessions)
    
    # Unified accuracy from both tables
    session_accuracies = [s.pose_accuracy for s in sessions if s.pose_accuracy > 0]
    predictions = db.query(models.PosePrediction).filter(
        models.PosePrediction.user_id == user_id,
        models.PosePrediction.created_at >= since_30,
    ).all()
    prediction_accuracies = [p.confidence * 100 for p in predictions if p.confidence > 0]
    
    all_accuracies = session_accuracies + prediction_accuracies
    avg_accuracy = float(np.mean(all_accuracies)) if all_accuracies else 0.0

    return {
        "total_sessions": len(sessions),
        "total_duration_minutes": round(total_duration, 1),
        "total_calories_burned": round(total_calories, 1),
        "avg_pose_accuracy": round(avg_accuracy, 1),
        "fitness_score": fitness["score"],
        "grade": fitness["grade"],
        "current_streak": streak,
        "weekly_sessions": get_weekly_sessions(db, user_id),
        "mood_trend": get_mood_trend(db, user_id),
        "top_exercises": get_top_exercises(db, user_id),
    }

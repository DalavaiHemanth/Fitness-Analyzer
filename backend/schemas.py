"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = ""
    age: Optional[int] = 0
    weight_kg: Optional[float] = 0.0
    height_cm: Optional[float] = 0.0
    fitness_goal: Optional[str] = "general"


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    fitness_goal: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    age: int
    weight_kg: float
    height_cm: float
    fitness_goal: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# ─── Workout Session Schemas ─────────────────────────────────────────────────

class WorkoutCreate(BaseModel):
    text: str  # Natural language description for NLP analysis


class WorkoutOut(BaseModel):
    id: int
    workout_type: str
    exercise_name: str
    duration_minutes: float
    calories_burned: float
    sets: int
    reps: int
    target_muscles: str
    notes: str
    pose_accuracy: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Pose Prediction Schemas ─────────────────────────────────────────────────

class PosePredictionOut(BaseModel):
    id: int
    pose_label: str
    confidence: float
    method: str
    feedback: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Mood Log Schemas ─────────────────────────────────────────────────────────

class MoodCreate(BaseModel):
    mood_level: int       # 1-10
    energy_level: int     # 1-10
    stress_level: int     # 1-10
    sleep_hours: Optional[float] = 0.0
    notes: Optional[str] = ""


class MoodOut(BaseModel):
    id: int
    mood_level: int
    energy_level: int
    stress_level: int
    sleep_hours: float
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Analytics / Progress Schemas ───────────────────────────────────────────

class FitnessScore(BaseModel):
    score: float
    frequency_score: float
    accuracy_score: float
    duration_score: float
    grade: str             # A, B, C, D, F
    message: str


class ProgressSummary(BaseModel):
    total_sessions: int
    total_duration_minutes: float
    total_calories_burned: float
    avg_pose_accuracy: float
    fitness_score: float
    grade: str
    current_streak: int
    weekly_sessions: List[dict]
    mood_trend: List[dict]
    top_exercises: List[dict]


class PredictionOut(BaseModel):
    next_week_sessions: float
    next_week_calories: float
    trend: str             # improving, declining, stable
    message: str


# ─── NLP Analysis Response ───────────────────────────────────────────────────

class NLPAnalysisOut(BaseModel):
    intent: str
    exercise_name: str
    duration_minutes: float
    sets: int
    reps: int
    target_muscles: List[str]
    calories_estimate: float
    confidence: float
    session_id: Optional[int] = None

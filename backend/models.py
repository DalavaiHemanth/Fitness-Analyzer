"""
SQLAlchemy ORM models for all database tables.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    age = Column(Integer, default=0)
    weight_kg = Column(Float, default=0.0)
    height_cm = Column(Float, default=0.0)
    fitness_goal = Column(String, default="general")  # weight_loss, muscle_gain, endurance, general
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workout_sessions = relationship("WorkoutSession", back_populates="user")
    pose_predictions = relationship("PosePrediction", back_populates="user")
    mood_logs = relationship("MoodLog", back_populates="user")


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workout_type = Column(String, nullable=False)  # strength, cardio, flexibility, recovery
    exercise_name = Column(String, default="")
    duration_minutes = Column(Float, default=0.0)
    calories_burned = Column(Float, default=0.0)
    sets = Column(Integer, default=0)
    reps = Column(Integer, default=0)
    target_muscles = Column(Text, default="")  # comma-separated
    notes = Column(Text, default="")
    raw_text = Column(Text, default="")  # original user input
    pose_accuracy = Column(Float, default=0.0)  # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workout_sessions")


class PosePrediction(Base):
    __tablename__ = "pose_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pose_label = Column(String, nullable=False)
    confidence = Column(Float, default=0.0)
    method = Column(String, default="mediapipe")  # mediapipe or trained_model
    image_filename = Column(String, default="")
    feedback = Column(Text, default="")  # pose correction tips
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="pose_predictions")


class MoodLog(Base):
    __tablename__ = "mood_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mood_level = Column(Integer, nullable=False)       # 1-10
    energy_level = Column(Integer, nullable=False)     # 1-10
    stress_level = Column(Integer, nullable=False)     # 1-10
    sleep_hours = Column(Float, default=0.0)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="mood_logs")

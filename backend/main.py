"""
FastAPI Application Entry Point
================================
Multi-Modal Fitness Pose, Activity & Mood Analyzer
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
import models  # ensure models are registered before create_all
from routers import users, pose, workout, analytics

# Create all DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fitness Analyzer API",
    description="""
## Multi-Modal Fitness Pose, Activity & Mood Analyzer

### Features
- 🏋️ **Pose Detection**: Upload workout images → AI classifies your exercise pose
- 💬 **NLP Analysis**: Describe your workout in plain text → Extracts exercises, sets, reps, muscles
- 📊 **Progress Analytics**: Fitness score, streak tracking, weekly trends
- 😊 **Mood Tracking**: Log mood/energy/stress and visualize trends
- 🔮 **Performance Prediction**: Linear regression predicts next-week workouts
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(users.router)
app.include_router(pose.router)
app.include_router(workout.router)
app.include_router(analytics.router)

# ── Serve uploaded images ──────────────────────────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Fitness Analyzer API is running!",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "database": "connected"}

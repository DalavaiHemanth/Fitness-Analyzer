"""
Backend Tests
=============
Run with: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app
from database import Base, engine, SessionLocal
import models

# Use in-memory SQLite for tests
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    """Create a test user and return auth headers."""
    # Register
    client.post("/users/register", json={
        "email": "test@fitai.com",
        "username": "testuser",
        "password": "testpass123",
        "fitness_goal": "general"
    })
    # Login
    res = client.post("/users/login", data={"username": "testuser", "password": "testpass123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self, client):
        res = client.post("/users/register", json={
            "email": "newuser@fitai.com",
            "username": "newuser",
            "password": "password123"
        })
        assert res.status_code == 201
        assert res.json()["username"] == "newuser"

    def test_register_duplicate_email(self, client):
        # Register first time
        client.post("/users/register", json={"email": "dup@fitai.com", "username": "dup1", "password": "pass"})
        # Duplicate
        res = client.post("/users/register", json={"email": "dup@fitai.com", "username": "dup2", "password": "pass"})
        assert res.status_code == 400

    def test_login_success(self, client):
        client.post("/users/register", json={"email": "login@fitai.com", "username": "loginuser", "password": "pass123"})
        res = client.post("/users/login", data={"username": "loginuser", "password": "pass123"})
        assert res.status_code == 200
        assert "access_token" in res.json()

    def test_login_wrong_password(self, client):
        res = client.post("/users/login", data={"username": "testuser", "password": "wrongpassword"})
        assert res.status_code == 401

    def test_get_me(self, client, auth_headers):
        res = client.get("/users/me", headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["username"] == "testuser"

    def test_unauthorized_access(self, client):
        res = client.get("/users/me")
        assert res.status_code == 401


# ── NLP Tests ────────────────────────────────────────────────────────────────

class TestNLP:
    def test_analyze_strength(self, client, auth_headers):
        res = client.post("/workout/analyze-workout?save=false",
            json={"text": "I did 3 sets of 10 pushups"},
            headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "strength"
        assert "pushup" in data["exercise_name"]
        assert data["sets"] == 3
        assert data["reps"] == 10

    def test_analyze_cardio(self, client, auth_headers):
        res = client.post("/workout/analyze-workout?save=false",
            json={"text": "Ran 5km in 30 minutes"},
            headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "cardio"
        assert data["duration_minutes"] == 30.0

    def test_analyze_flexibility(self, client, auth_headers):
        res = client.post("/workout/analyze-workout?save=false",
            json={"text": "Morning yoga session for 45 minutes"},
            headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["intent"] == "flexibility"

    def test_analyze_with_save(self, client, auth_headers):
        res = client.post("/workout/analyze-workout?save=true",
            json={"text": "4 sets of 8 bench press at 80kg"},
            headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["session_id"] is not None

    def test_analyze_empty_text(self, client, auth_headers):
        res = client.post("/workout/analyze-workout",
            json={"text": ""},
            headers=auth_headers)
        assert res.status_code == 400

    def test_get_sessions(self, client, auth_headers):
        res = client.get("/workout/sessions", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)


# ── Mood Tests ────────────────────────────────────────────────────────────────

class TestMood:
    def test_log_mood(self, client, auth_headers):
        res = client.post("/workout/mood",
            json={"mood_level": 7, "energy_level": 8, "stress_level": 3, "sleep_hours": 7.5},
            headers=auth_headers)
        assert res.status_code == 201
        data = res.json()
        assert data["mood_level"] == 7

    def test_invalid_mood_range(self, client, auth_headers):
        res = client.post("/workout/mood",
            json={"mood_level": 15, "energy_level": 5, "stress_level": 5},
            headers=auth_headers)
        assert res.status_code == 422

    def test_get_mood_history(self, client, auth_headers):
        res = client.get("/workout/mood/history", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)


# ── Analytics Tests ──────────────────────────────────────────────────────────

class TestAnalytics:
    def test_fitness_score(self, client, auth_headers):
        res = client.get("/analytics/fitness-score", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "score" in data
        assert "grade" in data
        assert 0 <= data["score"] <= 100

    def test_progress_summary(self, client, auth_headers):
        res = client.get("/analytics/progress", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "total_sessions" in data
        assert "fitness_score" in data

    def test_prediction(self, client, auth_headers):
        res = client.get("/analytics/predict", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "trend" in data
        assert data["trend"] in ["improving", "declining", "stable"]

    def test_muscle_heatmap(self, client, auth_headers):
        res = client.get("/analytics/muscle-heatmap", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), dict)

    def test_calorie_trend(self, client, auth_headers):
        res = client.get("/analytics/calorie-trend", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)


# ── NLP Unit Tests ────────────────────────────────────────────────────────────

class TestNLPUnit:
    def test_sets_reps_extraction(self):
        from ai.nlp_analyzer import _extract_sets_reps
        assert _extract_sets_reps("3 sets of 10") == (3, 10)
        assert _extract_sets_reps("3x10") == (3, 10)
        assert _extract_sets_reps("10 reps") == (1, 10)

    def test_duration_extraction(self):
        from ai.nlp_analyzer import _extract_duration
        assert _extract_duration("30 minutes") == 30.0
        assert _extract_duration("1 hour") == 60.0
        assert _extract_duration("45 min jog") == 45.0

    def test_exercise_extraction(self):
        from ai.nlp_analyzer import _extract_exercise
        name, info = _extract_exercise("I did pushups and some curls")
        assert name == "pushup"
        assert info["intent"] == "strength"

    def test_full_analysis(self):
        from ai.nlp_analyzer import analyze_workout
        result = analyze_workout("3 sets of 12 squats")
        assert result["intent"] == "strength"
        assert result["sets"] == 3
        assert result["reps"] == 12
        assert "squat" in result["exercise_name"]

# Multi-Modal Fitness Pose, Activity & Mood Analyzer

> AI-powered fitness tracker combining computer vision (pose detection), NLP (workout analysis), and analytics (progress tracking & prediction).

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy, SQLite |
| AI | MediaPipe, spaCy/NLTK, scikit-learn |
| Frontend | Vite + React 18, Recharts, Axios |
| Auth | JWT (python-jose, bcrypt) |

## Project Structure

```
Fitness Analyzer/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # SQLAlchemy + SQLite
│   ├── models.py               # ORM models
│   ├── schemas.py              # Pydantic schemas
│   ├── auth.py                 # JWT utilities
│   ├── ai/
│   │   ├── pose_detector.py    # MediaPipe + ML classifier
│   │   ├── nlp_analyzer.py     # Workout NLP (intent + entities)
│   │   └── analytics_engine.py # Fitness score + prediction
│   ├── routers/
│   │   ├── users.py            # Auth endpoints
│   │   ├── pose.py             # POST /pose/classify-pose
│   │   ├── workout.py          # POST /workout/analyze-workout
│   │   └── analytics.py       # GET /analytics/progress
│   ├── train_pose_model.py     # Train pose classifier
│   ├── train_nlp_model.py      # Train NLP intent classifier
│   └── tests/test_api.py       # pytest test suite
├── frontend/
│   └── src/
│       ├── pages/              # Dashboard, PoseUpload, WorkoutEntry, MoodTracker, Profile
│       └── components/         # Navbar
├── datasets/
│   ├── pose_images/            # Place training images here (subdir = label)
│   └── nlp_training_data.json  # Optional custom NLP examples
└── models/                     # Trained model files (auto-generated)
```

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Download spaCy English model
python -m spacy download en_core_web_sm

# Start the API server
uvicorn main:app --reload --port 8000
```

API docs available at: **http://localhost:8000/docs**

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend at: **http://localhost:5173**

---

## AI Model Training

### Pose Classifier (Computer Vision)

1. Create dataset directories:
```
datasets/pose_images/
├── squat/       ← add 50+ squat photos
├── pushup/      ← add 50+ pushup photos
├── plank/
├── deadlift/
├── bicep_curl/
├── lunge/
└── ...
```

2. Train:
```bash
cd backend
python train_pose_model.py
```

Results saved to `models/pose_classifier.pkl` and `models/training_report.json`.

> **Without training**: The app falls back to MediaPipe **angle-based analysis** — it still works perfectly, classifying poses using joint angle calculations.

### NLP Intent Classifier

```bash
cd backend
python train_nlp_model.py
```

Trains TF-IDF + Logistic Regression on 80+ built-in samples. Add custom samples in `datasets/nlp_training_data.json`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/users/register` | Create account |
| POST | `/users/login` | Get JWT token |
| GET | `/users/me` | Get profile |
| PUT | `/users/me` | Update profile |
| POST | `/pose/classify-pose` | Upload image → pose label |
| GET | `/pose/history` | Pose prediction history |
| POST | `/workout/analyze-workout` | NLP workout analysis |
| GET | `/workout/sessions` | Workout session history |
| POST | `/workout/mood` | Log mood/energy/stress |
| GET | `/analytics/progress` | Full dashboard data |
| GET | `/analytics/fitness-score` | Computed fitness grade |
| GET | `/analytics/predict` | Next-week predictions |
| GET | `/analytics/muscle-heatmap` | Muscle frequency data |

---

## Running Tests

```bash
cd backend
pip install pytest httpx
pytest tests/ -v
```

---

## Deployment

### Backend → Render

Create `backend/Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend → Vercel

```bash
cd frontend
npm run build
# Deploy dist/ folder to Vercel
```

---

## License

MIT — College Semester Project, 2024

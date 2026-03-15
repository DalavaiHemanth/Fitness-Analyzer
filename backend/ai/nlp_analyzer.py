"""
NLP Workout Analysis Module
===========================
Extracts structured fitness information from free-text workout descriptions.

Pipeline:
  1. Preprocessing: tokenize, lowercase, remove stopwords, lemmatize
  2. Intent classification: TF-IDF + Logistic Regression (strength/cardio/flexibility/recovery)
  3. Entity extraction: regex + keyword matching for exercise, duration, sets, reps, muscles

Example input:  "I did 3 sets of 10 pushups and 20 minutes of running"
Example output: intent=strength, exercise=pushup, sets=3, reps=10, duration=20
"""
import re
import os
import math
import joblib
import logging
import nltk
from typing import Optional

logger = logging.getLogger(__name__)

# Download NLTK data if not already present
for pkg in ["punkt", "punkt_tab", "stopwords", "wordnet", "averaged_perceptron_tagger", "averaged_perceptron_tagger_eng"]:
    try:
        nltk.download(pkg, quiet=True)
    except Exception:
        pass

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

_lemmatizer = WordNetLemmatizer()
_stop_words = set(stopwords.words("english")) - {"not", "no"}

# ── Exercise → intent + muscle mapping ────────────────────────────────────────
EXERCISE_DB = {
    # Strength
    "pushup": {"intent": "strength", "muscles": ["chest", "triceps", "shoulders"], "met": 5.0},
    "push-up": {"intent": "strength", "muscles": ["chest", "triceps", "shoulders"], "met": 5.0},
    "pullup": {"intent": "strength", "muscles": ["back", "biceps"], "met": 5.5},
    "pull-up": {"intent": "strength", "muscles": ["back", "biceps"], "met": 5.5},
    "squat": {"intent": "strength", "muscles": ["quads", "hamstrings", "glutes"], "met": 5.0},
    "deadlift": {"intent": "strength", "muscles": ["lower back", "glutes", "hamstrings"], "met": 6.0},
    "bench press": {"intent": "strength", "muscles": ["chest", "triceps", "shoulders"], "met": 5.0},
    "bicep curl": {"intent": "strength", "muscles": ["biceps"], "met": 3.5},
    "curl": {"intent": "strength", "muscles": ["biceps"], "met": 3.5},
    "shoulder press": {"intent": "strength", "muscles": ["shoulders", "triceps"], "met": 4.0},
    "overhead press": {"intent": "strength", "muscles": ["shoulders", "triceps"], "met": 4.0},
    "lunge": {"intent": "strength", "muscles": ["quads", "hamstrings", "glutes"], "met": 4.5},
    "plank": {"intent": "strength", "muscles": ["core", "abs"], "met": 4.0},
    "dip": {"intent": "strength", "muscles": ["triceps", "chest"], "met": 5.0},
    "row": {"intent": "strength", "muscles": ["back", "biceps"], "met": 5.0},
    "lat pulldown": {"intent": "strength", "muscles": ["back", "biceps"], "met": 4.5},
    "crunch": {"intent": "strength", "muscles": ["abs", "core"], "met": 4.0},
    "sit-up": {"intent": "strength", "muscles": ["abs", "core"], "met": 4.0},
    "situp": {"intent": "strength", "muscles": ["abs", "core"], "met": 4.0},
    "tricep extension": {"intent": "strength", "muscles": ["triceps"], "met": 3.0},
    "leg press": {"intent": "strength", "muscles": ["quads", "glutes", "hamstrings"], "met": 4.5},
    "flye": {"intent": "strength", "muscles": ["chest"], "met": 3.5},
    "fly": {"intent": "strength", "muscles": ["chest"], "met": 3.5},
    "shrug": {"intent": "strength", "muscles": ["shoulders", "back"], "met": 3.0},
    "calf raise": {"intent": "strength", "muscles": ["calves"], "met": 3.0},
    "leg curl": {"intent": "strength", "muscles": ["hamstrings"], "met": 3.5},
    "leg extension": {"intent": "strength", "muscles": ["quads"], "met": 3.5},
    "hip thrust": {"intent": "strength", "muscles": ["glutes"], "met": 4.0},
    # Cardio
    "run": {"intent": "cardio", "muscles": ["legs", "core"], "met": 9.0},
    "running": {"intent": "cardio", "muscles": ["legs", "core"], "met": 9.0},
    "jog": {"intent": "cardio", "muscles": ["legs", "core"], "met": 7.0},
    "jogging": {"intent": "cardio", "muscles": ["legs", "core"], "met": 7.0},
    "cycling": {"intent": "cardio", "muscles": ["legs"], "met": 8.0},
    "bike": {"intent": "cardio", "muscles": ["legs"], "met": 8.0},
    "swimming": {"intent": "cardio", "muscles": ["full body"], "met": 8.0},
    "jump rope": {"intent": "cardio", "muscles": ["legs", "core"], "met": 12.0},
    "skipping": {"intent": "cardio", "muscles": ["legs", "core"], "met": 12.0},
    "jumping jack": {"intent": "cardio", "muscles": ["full body"], "met": 8.0},
    "hiit": {"intent": "cardio", "muscles": ["full body"], "met": 10.0},
    "elliptical": {"intent": "cardio", "muscles": ["legs", "core"], "met": 7.0},
    "treadmill": {"intent": "cardio", "muscles": ["legs"], "met": 8.0},
    "walk": {"intent": "cardio", "muscles": ["legs"], "met": 3.5},
    "walking": {"intent": "cardio", "muscles": ["legs"], "met": 3.5},
    "burpee": {"intent": "cardio", "muscles": ["full body"], "met": 10.0},
    # Flexibility
    "yoga": {"intent": "flexibility", "muscles": ["full body"], "met": 2.5},
    "stretch": {"intent": "flexibility", "muscles": ["full body"], "met": 2.0},
    "stretching": {"intent": "flexibility", "muscles": ["full body"], "met": 2.0},
    "pilates": {"intent": "flexibility", "muscles": ["core", "full body"], "met": 3.0},
    "foam roll": {"intent": "flexibility", "muscles": ["full body"], "met": 2.0},
    "downward dog": {"intent": "flexibility", "muscles": ["back", "hamstrings"], "met": 2.5},
    "warrior": {"intent": "flexibility", "muscles": ["legs", "core"], "met": 2.5},
    # Recovery
    "rest": {"intent": "recovery", "muscles": [], "met": 1.0},
    "recovery": {"intent": "recovery", "muscles": [], "met": 1.0},
    "massage": {"intent": "recovery", "muscles": [], "met": 1.5},
    "ice bath": {"intent": "recovery", "muscles": [], "met": 1.0},
}

INTENT_KEYWORDS = {
    "strength": ["weight", "lift", "press", "pull", "push", "reps", "sets", "barbell", "dumbbell", "gym", "resistance"],
    "cardio": ["run", "jog", "cycle", "swim", "jump", "sprint", "minutes", "km", "mile", "heart", "breath", "aerobic"],
    "flexibility": ["stretch", "yoga", "pilates", "flex", "mobility", "relax", "breathe"],
    "recovery": ["rest", "sleep", "recover", "foam", "ice", "massage", "easy"],
}

MUSCLE_KEYWORDS = [
    "chest", "back", "shoulders", "biceps", "triceps", "legs", "quads",
    "hamstrings", "glutes", "abs", "core", "calves", "forearms", "full body", "lower back"
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "nlp_intent_classifier.pkl")
_intent_model = None
try:
    if os.path.exists(MODEL_PATH):
        _intent_model = joblib.load(MODEL_PATH)
        logger.info("✅ Loaded trained NLP intent classifier.")
except Exception as e:
    logger.warning("No trained NLP model found, using keyword rules: %s", e)


def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    tokens = word_tokenize(text)
    tokens = [_lemmatizer.lemmatize(t) for t in tokens if t not in _stop_words and len(t) > 1]
    return " ".join(tokens)


def _extract_numbers(text: str) -> list[int]:
    """Extract all numbers (including written ones) from text."""
    word_nums = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                 "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                 "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}
    text_lower = text.lower()
    nums = [int(m) for m in re.findall(r'\b\d+\b', text)]
    for word, val in word_nums.items():
        if word in text_lower:
            nums.append(val)
    return sorted(set(nums))


def _extract_sets_reps(text: str) -> tuple[int, int]:
    """Extract sets and reps from text like '3 sets of 10', '3x10', '10 reps'."""
    # Pattern: 3x10, 3X10
    m = re.search(r'(\d+)\s*[xX]\s*(\d+)', text)
    if m:
        return int(m.group(1)), int(m.group(2))
    # Pattern: 3 sets of 10, 3 sets 10 reps
    m = re.search(r'(\d+)\s*sets?\s*(of\s*)?(\d+)', text, re.I)
    if m:
        return int(m.group(1)), int(m.group(3))
    # Pattern: 10 reps only
    m = re.search(r'(\d+)\s*reps?', text, re.I)
    if m:
        return 1, int(m.group(1))
    return 0, 0


def _extract_duration(text: str) -> float:
    """Extract duration in minutes from text."""
    # Hours
    m = re.search(r'(\d+\.?\d*)\s*hour', text, re.I)
    if m:
        return float(m.group(1)) * 60
    # Minutes
    m = re.search(r'(\d+\.?\d*)\s*min', text, re.I)
    if m:
        return float(m.group(1))
    # Seconds
    m = re.search(r'(\d+)\s*sec', text, re.I)
    if m:
        return round(int(m.group(1)) / 60, 1)
    return 0.0


def _extract_exercise(text: str) -> tuple[str, dict]:
    """Find matching exercise from database using substring matching."""
    text_lower = text.lower()
    for name, info in sorted(EXERCISE_DB.items(), key=lambda x: -len(x[0])):
        if name in text_lower:
            return name, info
    return "", {}


def _keyword_intent(text: str) -> str:
    """Fallback: keyword-based intent classification."""
    text_lower = text.lower()
    scores = {intent: 0 for intent in INTENT_KEYWORDS}
    for intent, words in INTENT_KEYWORDS.items():
        scores[intent] = sum(1 for w in words if w in text_lower)
    return max(scores, key=scores.get)


def _extract_muscles_from_text(text: str) -> list[str]:
    """Find any directly mentioned muscle groups."""
    text_lower = text.lower()
    return [m for m in MUSCLE_KEYWORDS if m in text_lower]


def analyze_workout(text: str, user_weight_kg: float = 70.0) -> dict:
    """
    Main NLP analysis entry point.

    Args:
        text: Free-text workout description.
        user_weight_kg: Used for calorie estimation.

    Returns:
        Structured workout data dict.
    """
    if not text or not text.strip():
        return {"error": "Empty workout description"}

    # Exercise & muscles
    exercise_name, exercise_info = _extract_exercise(text)
    intent = exercise_info.get("intent", "")
    muscles = list(exercise_info.get("muscles", []))
    met = exercise_info.get("met", 4.0)

    # Extra muscles mentioned directly
    extra_muscles = _extract_muscles_from_text(text)
    muscles = list(dict.fromkeys(muscles + [m for m in extra_muscles if m not in muscles]))

    # Intent & Probability prediction
    model_prob = 0.0
    if not intent:
        if _intent_model:
            try:
                # Use the new calibrated model to get actual probabilities
                processed_text = preprocess(text)
                intent = _intent_model.predict([processed_text])[0]
                probs = _intent_model.predict_proba([processed_text])[0]
                model_prob = max(probs)
            except Exception as e:
                logger.error("Model prediction failed: %s", e)
                intent = _keyword_intent(text)
        else:
            intent = _keyword_intent(text)

    # Sets, reps, duration
    sets, reps = _extract_sets_reps(text)
    duration = _extract_duration(text)

    # Duration fallback: estimate from sets*reps
    if duration == 0.0 and sets > 0 and reps > 0:
        duration = round((sets * reps * 3) / 60, 1)  # ~3 sec/rep

    # Calorie estimate
    calories = 0.0
    if duration > 0:
        calories = round((met * user_weight_kg * 3.5 * duration) / 200.0, 1)
    elif sets > 0:
        calories = round(sets * reps * 0.1, 1)

    # Confidence calculation: heavily weight AI probability + database matching
    confidence = 0.0

    if model_prob > 0:
        # Base confidence starts with the ML model's mathematical certainty
        confidence = model_prob
        
        # If the ML model is confident AND we found a known exercise in our DB, boost it
        if exercise_name and confidence > 0.6:
            confidence = min(confidence + 0.15, 0.99)
            
        # Small penalty if it's missing key metrics (sets/reps/duration) to encourage detailed logging
        has_metrics = (sets > 0 and reps > 0) or duration > 0
        if not has_metrics:
            confidence *= 0.85
    else:
        # Fallback to pure extraction heuristic if ML model fails
        n_found = sum([bool(exercise_name), sets > 0, reps > 0, duration > 0, bool(muscles)])
        confidence = min(0.4 + n_found * 0.15, 0.95)

    # Cap at 99%
    confidence = min(confidence, 0.99)

    return {
        "intent": intent or "unknown",
        "exercise_name": exercise_name or "general workout",
        "duration_minutes": duration,
        "sets": sets,
        "reps": reps,
        "target_muscles": muscles,
        "calories_estimate": calories,
        "confidence": round(confidence, 3),
    }


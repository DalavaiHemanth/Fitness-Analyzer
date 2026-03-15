"""
Pose Detection AI Module
========================
Two-stage approach:
  1. MediaPipe: Extracts 33 body landmarks in real-time (no training needed)
  2. Custom Classifier: A trained MobileNetV2/EfficientNet model for pose label classification

Supported poses: squat, pushup, plank, deadlift, bicep_curl, shoulder_press,
                 lunge, jumping_jack, warrior_pose, downward_dog, unknown
"""
import os
import cv2
import numpy as np
from PIL import Image
import io
import joblib
import logging

logger = logging.getLogger(__name__)

# ── Pose labels the model can classify ────────────────────────────────────────
POSE_LABELS = [
    "squat", "pushup", "plank", "deadlift", "bicep_curl",
    "shoulder_press", "lunge", "jumping_jack", "warrior_pose",
    "downward_dog", "unknown"
]

# Pose-specific correction tips
POSE_FEEDBACK = {
    "squat": "Keep your back straight, knees behind toes, and chest up. Lower until thighs are parallel to the floor.",
    "pushup": "Keep core tight, elbows at 45°, and lower chest to the floor. Maintain straight body alignment.",
    "plank": "Engage core, keep hips level (not sagging or raised), and breathe steadily.",
    "deadlift": "Keep the bar close to your body, hinge at hips, and maintain a neutral spine throughout.",
    "bicep_curl": "Keep elbows fixed at sides, fully extend at bottom, and squeeze biceps at the top.",
    "shoulder_press": "Press overhead fully, keep core braced, and avoid arching your lower back.",
    "lunge": "Front knee should not pass the toe, maintain upright torso, and keep rear knee off the floor.",
    "jumping_jack": "Land softly with knees slightly bent and maintain a steady pace.",
    "warrior_pose": "Front knee should be at 90°, back leg straight, arms extended parallel to the floor.",
    "downward_dog": "Press heels toward the floor, straighten legs, and elongate the spine.",
    "unknown": "Pose could not be clearly identified. Ensure your full body is visible in the frame.",
}

# MET values for calorie estimation (per minute per kg)
POSE_MET = {
    "squat": 5.0, "pushup": 5.0, "plank": 4.0, "deadlift": 6.0,
    "bicep_curl": 3.5, "shoulder_press": 4.0, "lunge": 4.5,
    "jumping_jack": 8.0, "warrior_pose": 2.5, "downward_dog": 2.5, "unknown": 3.0
}

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "models", "pose_classifier.pkl")

# Try loading trained classifier (optional — falls back to MediaPipe angle analysis)
_classifier = None
try:
    if os.path.exists(MODEL_PATH):
        _classifier = joblib.load(MODEL_PATH)
        logger.info("✅ Loaded trained pose classifier from disk.")
    else:
        logger.warning("⚠️  No trained model found at %s. Using MediaPipe angle analysis.", MODEL_PATH)
except Exception as e:
    logger.warning("⚠️  Could not load trained model: %s", e)


def _extract_landmarks(image_array: np.ndarray) -> tuple[list, float]:
    """
    Run MediaPipe pose estimation and return normalized landmark array + visibility score.
    Returns (landmarks_flat, visibility) or ([], 0.0) if no pose detected.
    """
    try:
        import mediapipe as mp
        mp_pose = mp.solutions.pose
        with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
            rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb)
            if not results.pose_landmarks:
                return [], 0.0
            lm = results.pose_landmarks.landmark
            flat = []
            for l in lm:
                flat.extend([l.x, l.y, l.z, l.visibility])
            visibility = np.mean([l.visibility for l in lm])
            return flat, float(visibility)
    except Exception as e:
        logger.error("MediaPipe error: %s", e)
        return [], 0.0


def _get_angle(a, b, c) -> float:
    """Calculate angle at joint b given three 3D points (x, y, z)."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
    return float(angle)


def _extract_features(landmarks_flat: list) -> list:
    """
    Augment raw coordinates with geometric features (angles) to improve precision.
    Total features: 33*4 (raw) + 12 (angles) = 144
    """
    if not landmarks_flat:
        return []
    
    # Get 3D points
    def p3(idx):
        base = idx * 4
        return landmarks_flat[base:base+3]

    try:
        # Landmarks: 11=L Shld, 12=R Shld, 13=L Elb, 14=R Elb, 15=L Wrst, 16=R Wrst
        # 23=L Hip, 24=R Hip, 25=L Knee, 26=R Knee, 27=L Ankle, 28=R Ankle
        angles = [
            _get_angle(p3(11), p3(13), p3(15)), # L Elbow
            _get_angle(p3(12), p3(14), p3(16)), # R Elbow
            _get_angle(p3(13), p3(11), p3(23)), # L Shoulder
            _get_angle(p3(14), p3(12), p3(24)), # R Shoulder
            _get_angle(p3(11), p3(23), p3(25)), # L Hip
            _get_angle(p3(12), p3(24), p3(26)), # R Hip
            _get_angle(p3(23), p3(25), p3(27)), # L Knee
            _get_angle(p3(24), p3(26), p3(28)), # R Knee
            # Mid-body symmetry/alignment angles
            _get_angle(p3(11), p3(12), p3(24)), 
            _get_angle(p3(12), p3(11), p3(23)),
            _get_angle(p3(23), p3(24), p3(12)),
            _get_angle(p3(24), p3(23), p3(11)),
        ]
        return landmarks_flat + angles
    except Exception:
        return landmarks_flat + [0.0] * 12


def _angle(a, b, c) -> float:
    """Calculate angle at joint b given three 2D points (x, y). Used for rule-based fallback."""
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0))))


def _rule_based_classify(landmarks_flat: list) -> tuple[str, float]:
    """
    Heuristic angle-based pose classification using key joint angles.
    Used as fallback when no trained model is available.
    """
    if len(landmarks_flat) < 33 * 4:
        return "unknown", 0.3

    def pt(idx):
        base = idx * 4
        return landmarks_flat[base], landmarks_flat[base + 1]

    # MediaPipe landmark indices
    # 11=left shoulder, 12=right shoulder, 23=left hip, 24=right hip
    # 25=left knee, 26=right knee, 27=left ankle, 28=right ankle
    # 13=left elbow, 15=left wrist
    try:
        hip_l = pt(23); knee_l = pt(25); ankle_l = pt(27)
        hip_r = pt(24); knee_r = pt(26); ankle_r = pt(28)
        shoulder_l = pt(11); elbow_l = pt(13); wrist_l = pt(15)
        shoulder_r = pt(12)

        knee_angle = (_angle(hip_l, knee_l, ankle_l) + _angle(hip_r, knee_r, ankle_r)) / 2
        elbow_angle = _angle(shoulder_l, elbow_l, wrist_l)
        hip_angle = (_angle(shoulder_l, hip_l, knee_l) + _angle(shoulder_r, hip_r, knee_r)) / 2
        torso_height = abs(shoulder_l[1] - hip_l[1])
        leg_spread = abs(ankle_l[0] - ankle_r[0])

        # Classification rules
        if knee_angle < 110:
            return ("squat", 0.85) if hip_angle > 70 else ("lunge", 0.75)
        elif elbow_angle < 100 and torso_height < 0.15:
            return "pushup", 0.82
        elif torso_height < 0.12 and knee_angle > 150:
            return "plank", 0.80
        elif hip_angle < 70 and knee_angle > 150:
            return "deadlift", 0.75
        elif elbow_angle < 90 and torso_height > 0.2:
            return "bicep_curl", 0.78
        elif elbow_angle > 160 and torso_height > 0.25:
            return "shoulder_press", 0.78
        elif leg_spread > 0.3:
            return "jumping_jack", 0.72
        elif knee_angle > 150 and hip_angle > 150:
            return "downward_dog", 0.68
        else:
            return "warrior_pose", 0.60
    except Exception:
        return "unknown", 0.3


def classify_pose(image_bytes: bytes, user_weight_kg: float = 70.0) -> dict:
    """
    Main entry point: classifies the exercise pose in an image.

    Args:
        image_bytes: Raw bytes of the uploaded image.
        user_weight_kg: Used for calorie estimation.

    Returns:
        dict with pose_label, confidence, method, feedback, estimated_calories_per_min
    """
    # Decode image
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_array = np.array(image)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    except Exception as e:
        return {"pose_label": "unknown", "confidence": 0.0, "method": "error",
                "feedback": "Could not decode image.", "estimated_calories_per_min": 0.0}

    # Resize for uniform processing
    img_bgr = cv2.resize(img_bgr, (640, 480))

    # Step 1: Extract MediaPipe landmarks
    landmarks, visibility = _extract_landmarks(img_bgr)

    pose_label = "unknown"
    confidence = 0.0
    method = "mediapipe_angles"

    if landmarks:
        if _classifier is not None:
            # Step 2a: Use trained ML classifier on augmented features
            try:
                # Add geometric features (angles)
                features_aug = _extract_features(landmarks)
                features = np.array(features_aug).reshape(1, -1)
                proba = _classifier.predict_proba(features)[0]
                idx = int(np.argmax(proba))
                pose_label = POSE_LABELS[idx] if idx < len(POSE_LABELS) else "unknown"
                confidence = float(proba[idx])
                method = "trained_model_v2"
            except Exception as e:
                logger.warning("Classifier inference failed: %s. Falling back.", e)
                pose_label, confidence = _rule_based_classify(landmarks)
        else:
            # Step 2b: Rule-based angle analysis
            pose_label, confidence = _rule_based_classify(landmarks)

        # Adjust confidence by visibility
        confidence = min(confidence * (0.6 + 0.4 * visibility), 1.0)
    else:
        # No pose detected
        pose_label = "unknown"
        confidence = 0.0
        method = "no_pose_detected"

    met = POSE_MET.get(pose_label, 3.0)
    calories_per_min = (met * user_weight_kg * 3.5) / 200.0

    return {
        "pose_label": pose_label,
        "confidence": round(confidence, 4),
        "method": method,
        "feedback": POSE_FEEDBACK.get(pose_label, ""),
        "estimated_calories_per_min": round(calories_per_min, 2),
        "landmark_visibility": round(visibility, 3),
    }
